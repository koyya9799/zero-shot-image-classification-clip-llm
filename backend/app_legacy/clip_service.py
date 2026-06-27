# app/clip_service.py
import numpy as np
import torch
import open_clip
from PIL import Image
from typing import Dict, List, Optional, Tuple
import logging

from .prompt_service import build_prompts_for_label

logger = logging.getLogger(__name__)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Lazy loading for CLIP model
_model = None
_preprocess = None
_tokenizer = None

def _load_clip_model():
    """Load CLIP model lazily to save memory"""
    global _model, _preprocess, _tokenizer
    
    if _model is not None:
        return _model, _preprocess, _tokenizer
    
    try:
        logger.info("⚡ Loading CLIP ViT-L-14 model (openai weights)...")
        _model, _, _preprocess = open_clip.create_model_and_transforms(
            "ViT-L-14",
            pretrained="openai",
        )
        _tokenizer = open_clip.get_tokenizer("ViT-L-14")
        _model = _model.to(DEVICE)
        _model.eval()
        logger.info("✓ ViT-H/14 CLIP model loaded successfully")
        return _model, _preprocess, _tokenizer
    except Exception as e:
        logger.error(f"Failed to load CLIP model: {e}")
        raise

# adaptive state (in-memory)
CLASS_PROTOTYPES: Dict[str, np.ndarray] = {}
CLASS_COUNTS: Dict[str, int] = {}   # how many times we've updated
CONFIDENCE_THRESHOLD = 0.15         # min cosine sim to trust prediction (lowered for better learning)
TEMPERATURE = 0.01                  # temperature scaling for confidence calibration


def encode_texts(texts: List[str]) -> torch.Tensor:
    model, _, _ = _load_clip_model()
    tokenizer = _tokenizer
    with torch.no_grad():
        tokens = tokenizer(texts).to(DEVICE)
        feats = model.encode_text(tokens)
        feats /= feats.norm(dim=-1, keepdim=True)
    return feats  # [N, D]


def encode_image(img: Image.Image) -> np.ndarray:
    model, preprocess, _ = _load_clip_model()
    tensor = preprocess(img).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        feats = model.encode_image(tensor)
        feats /= feats.norm(dim=-1, keepdim=True)
    return feats.cpu().numpy()[0]  # [D]


def create_class_prototype(
    label: str,
    domain: str = "natural",
    images: Optional[List[Image.Image]] = None,
    w_text: float = 0.7,
    w_image: float = 0.3,
) -> Dict:
    """Create/replace prototype for a label using prompts (+ optional images)."""
    prompts = build_prompts_for_label(label, domain)
    text_embs = encode_texts(prompts).cpu().numpy()  # [n, D]
    # Use weighted average with more weight on diverse prompts
    t_proto = text_embs.mean(axis=0)
    t_proto /= np.linalg.norm(t_proto) + 1e-8

    if images:
        img_vecs = [encode_image(im) for im in images]
        i_proto = np.stack(img_vecs, axis=0).mean(axis=0)
        i_proto /= np.linalg.norm(i_proto) + 1e-8
        vec = w_text * t_proto + w_image * i_proto
        num_images = len(images)
    else:
        vec = t_proto
        num_images = 0

    norm = np.linalg.norm(vec) + 1e-8
    vec /= norm

    CLASS_PROTOTYPES[label] = vec
    # initialize count with at least 1 to keep alpha small
    CLASS_COUNTS[label] = CLASS_COUNTS.get(label, 1) + max(1, num_images)

    return {"num_images": num_images, "norm": float(norm)}


def _update_prototype_after_prediction(label: str, img_vec: np.ndarray) -> None:
    """Automatic online learning via EMA update."""
    if label not in CLASS_PROTOTYPES:
        return
    old = CLASS_PROTOTYPES[label]
    n = CLASS_COUNTS.get(label, 1)
    # smaller learning rate for more stable updates
    alpha = 0.05  # fixed small learning rate for stability
    new = (1 - alpha) * old + alpha * img_vec
    new /= np.linalg.norm(new) + 1e-8
    CLASS_PROTOTYPES[label] = new
    CLASS_COUNTS[label] = n + 1


def classify_image(
    img: Image.Image,
    top_k: int = 5,
) -> Dict:
    if not CLASS_PROTOTYPES:
        raise RuntimeError("No classes defined. Add classes first using /api/add-class.")

    img_vec = encode_image(img)
    labels = list(CLASS_PROTOTYPES.keys())
    mat = np.stack([CLASS_PROTOTYPES[l] for l in labels])  # [N, D]

    sims = mat @ img_vec
    # Apply temperature scaling for better confidence calibration
    sims = sims / TEMPERATURE
    # Apply softmax for normalized probabilities
    exp_sims = np.exp(sims - np.max(sims))
    probs = exp_sims / exp_sims.sum()
    
    idx = np.argsort(-probs)
    idx_top = idx[:top_k]

    candidates = [
        {"label": labels[i], "score": float(probs[i])}
        for i in idx_top
    ]
    best = candidates[0]
    best_label, best_score = best["label"], best["score"]

    if best_score >= CONFIDENCE_THRESHOLD:
        _update_prototype_after_prediction(best_label, img_vec)

    return {
        "label": best_label,
        "confidence": best_score,
        "candidates": candidates,
    }


def list_classes() -> List[str]:
    return sorted(CLASS_PROTOTYPES.keys())


def compute_text_similarity(img_vec: np.ndarray, text: str) -> float:
    """
    Compute cosine similarity between image embedding and text embedding.
    Returns a float between 0 and 1 representing the similarity.
    """
    text_tokens = _tokenizer([text]).to(DEVICE)
    with torch.no_grad():
        text_feats = _model.encode_text(text_tokens)
        text_feats /= text_feats.norm(dim=-1, keepdim=True)
    text_vec = text_feats.cpu().numpy()[0]
    
    # Compute cosine similarity (both vectors are already normalized)
    similarity = np.dot(img_vec, text_vec)
    # Clamp to [0, 1] range
    return float(np.clip(similarity, 0, 1))
