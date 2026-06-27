# backend/models/clip_model.py
import torch
import numpy as np
from PIL import Image
from typing import List, Tuple
from .model_cache import ModelLoader, DEVICE

class ViTH14Model:
    def __init__(self):
        self.device = DEVICE
        self._loaded = False
        self._cache_data = None
    
    def _ensure_loaded(self):
        if self._loaded and self._cache_data:
            return
        self._cache_data = ModelLoader.load_clip_model_fast("ViT-L-14")
        self._loaded = True
            
    @property
    def model(self):
        self._ensure_loaded()
        return self._cache_data["model"]
    
    @property
    def preprocess(self):
        self._ensure_loaded()
        return self._cache_data["preprocess"]
    
    @property
    def tokenizer(self):
        self._ensure_loaded()
        return self._cache_data["tokenizer"]
    
    def encode_image(self, image: Image.Image) -> np.ndarray:
        self._ensure_loaded()
        with torch.no_grad():
            image_input = self.preprocess(image).unsqueeze(0).to(self.device)
            image_features = self.model.encode_image(image_input)
            image_features /= image_features.norm(dim=-1, keepdim=True)
        return image_features.cpu().numpy()[0]
    
    def encode_text(self, texts: List[str]) -> np.ndarray:
        self._ensure_loaded()
        with torch.no_grad():
            text_tokens = self.tokenizer(texts).to(self.device)
            text_features = self.model.encode_text(text_tokens)
            text_features /= text_features.norm(dim=-1, keepdim=True)
        return text_features.cpu().numpy()
        
    def compute_similarity(self, image_emb: np.ndarray, text_embs: np.ndarray) -> np.ndarray:
        return text_embs @ image_emb
        
    def get_prompt_ensembles(self, label: str) -> List[str]:
        label_lower = label.lower()
        
        # IMPROVED: Industrial-specific prompts with very strong semantic distinction
        if any(term in label_lower for term in ['weld crack', 'fatigue crack', 'metal crack', 'structural crack']):
            # CRITICAL: Weld/fatigue crack prompts - maximize semantic clarity vs wood/natural textures
            return [
                "industrial metal weld crack defect",
                "fractured steel weld joint with rust",
                "metal fatigue crack near weld seam",
                "damaged welded metal surface with fracture",
                "steel weld bead crack and corrosion",
                "structural metal fracture in welded joint",
                "cracked weld defect on steel plate",
                "welded steel showing fatigue failure",
                "metal crack propagating from weld seam",
                "corroded fractured weld joint on metal",
            ]
        elif any(term in label_lower for term in ['weld', 'welding', 'metal', 'industrial', 'machinery', 'corrosion', 'rust', 'fracture']):
            # STRONG: General industrial prompts with high semantic specificity
            return [
                f"industrial metal {label}",
                f"close-up of {label} on steel surface",
                f"macro photography of {label}",
                f"detailed inspection image of {label}",
                f"high resolution {label} documentation",
                f"quality control image showing {label}",
                f"magnified view of {label}",
                f"structural engineering {label}",
                f"industrial defect{label[:1] if label[0].isupper() else ''} image",
                f"metal surface {label}"
            ]
        else:
            # Standard CLIP prompts for non-industrial domains
            return [
                f"a photo of a {label}",
                f"an image of a {label}",
                f"a clear picture of a {label}",
                f"a close-up photo of a {label}"
            ]

    def classify(self, image: Image.Image, labels: List[str], top_k: int = 5, custom_ensembles: dict = None) -> Tuple[List[dict], np.ndarray]:
        image_emb = self.encode_image(image)
        
        text_embs = []
        for label in labels:
            if custom_ensembles and label in custom_ensembles:
                prompts = custom_ensembles[label]
            else:
                prompts = self.get_prompt_ensembles(label)
                
            encoded = self.encode_text(prompts)
            avg_emb = np.mean(encoded, axis=0)
            avg_emb /= np.linalg.norm(avg_emb)
            text_embs.append(avg_emb)
            
        text_embs = np.array(text_embs)
        
        similarities = self.compute_similarity(image_emb, text_embs)
        
        # Temperature Scaling
        logits = similarities / 0.03
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / np.sum(exp_logits)
        
        top_indices = np.argsort(-probs)[:top_k]
        predictions = [{"label": labels[idx], "score": float(probs[idx])} for idx in top_indices]
        return predictions, image_emb

_vith14_model = None

def get_vith14_model() -> ViTH14Model:
    global _vith14_model
    if _vith14_model is None:
        _vith14_model = ViTH14Model()
    return _vith14_model
