# app/models/similarity.py
"""
Similarity Computation Module
Handles confidence scoring with domain-specific formulas
"""
import numpy as np
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def compute_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score (0-1)
    """
    # Normalize vectors
    vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-8)
    vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-8)
    
    # Compute dot product
    similarity = np.dot(vec1_norm, vec2_norm)
    
    # Clamp to [0, 1]
    return float(np.clip(similarity, 0, 1))


def compute_confidence_score(
    domain: str,
    model_used: str,
    prediction_score: float,
    image_emb: np.ndarray,
    caption_emb: np.ndarray = None,
    domain_similarity: float = None,
    confidence_multiplier: float = 1.0
) -> float:
    """
    🎯 CONFIDENCE COMPUTATION - MULTI-FACTOR ACCURACY SCORING
    
    Computes final confidence with validation layers.
    
    For medical (MedCLIP):
        base_confidence = 0.7 * disease_sim + 0.3 * caption_sim
        final = base * confidence_multiplier * domain_boost
    
    For general (ViT-H/14):
        base = prediction_score
        final = base * confidence_multiplier * semantic_boost
    
    Factors:
    - prediction_score: CLIP similarity (0-1)
    - confidence_multiplier: LLM validation factor (0.8-1.2)
    - domain_similarity: Image-domain alignment (0-1)
    - caption_emb: LLM caption semantic consistency
    
    Args:
        domain: Image domain
        model_used: Model name (ViT-H/14 or MedCLIP)
        prediction_score: Score from model
        image_emb: Image embedding
        caption_emb: Optional caption embedding
        domain_similarity: Optional domain similarity
        confidence_multiplier: LLM confidence adjustment (default 1.0)
        
    Returns:
        Final confidence score (0-1)
    """
    if domain == "medical" and model_used == "MedCLIP":
        # Medical formula with validation
        disease_sim = prediction_score
        
        if caption_emb is not None:
            caption_sim = compute_cosine_similarity(image_emb, caption_emb)
            base_confidence = 0.7 * disease_sim + 0.3 * caption_sim
        else:
            base_confidence = disease_sim
        
        # Apply domain boost if domain is medical
        domain_boost = 1.0 + (domain_similarity * 0.2) if domain_similarity else 1.0
        
        # Apply LLM confidence multiplier
        final_confidence = base_confidence * confidence_multiplier * domain_boost
        
        logger.debug(
            f"Medical confidence: disease={disease_sim:.3f}, "
            f"caption={caption_sim if caption_emb is not None else 0:.3f}, "
            f"domain_boost={domain_boost:.3f}, llm_mult={confidence_multiplier:.3f}, "
            f"final={final_confidence:.3f}"
        )
    else:
        # General formula with semantic validation
        base_confidence = prediction_score
        
        # Apply domain and LLM validation factors
        domain_boost = 1.0 + (domain_similarity * 0.15) if domain_similarity else 1.0
        final_confidence = base_confidence * confidence_multiplier * domain_boost
        
        logger.debug(
            f"General confidence: base={base_confidence:.3f}, "
            f"llm_mult={confidence_multiplier:.3f}, "
            f"domain_boost={domain_boost:.3f}, "
            f"final={final_confidence:.3f}"
        )
    
    return float(np.clip(final_confidence, 0, 1))


def rank_predictions(
    predictions: List[Dict],
    image_emb: np.ndarray,
    model,
    top_k: int = 5
) -> List[Dict]:
    """
    Re-rank predictions with additional similarity computations
    
    Args:
        predictions: Initial predictions
        image_emb: Image embedding
        model: CLIP model instance
        top_k: Number of top results
        
    Returns:
        Re-ranked predictions with enhanced scores
    """
    enhanced_predictions = []
    
    for pred in predictions[:top_k]:
        label = pred["label"]
        base_score = pred["score"]
        
        # Compute text embedding for label
        text_emb = model.encode_text([label])[0]
        
        # Compute direct similarity
        direct_sim = compute_cosine_similarity(image_emb, text_emb)
        
        # Combine scores (weighted average)
        enhanced_score = 0.6 * base_score + 0.4 * direct_sim
        
        enhanced_predictions.append({
            "label": label,
            "score": float(enhanced_score),
            "base_score": float(base_score),
            "direct_similarity": float(direct_sim)
        })
    
    # Re-sort by enhanced score
    enhanced_predictions.sort(key=lambda x: x["score"], reverse=True)
    
    return enhanced_predictions


def compute_batch_similarities(
    image_embs: np.ndarray,
    text_embs: np.ndarray
) -> np.ndarray:
    """
    Compute pairwise similarities for batch processing
    
    Args:
        image_embs: Image embeddings [N, D]
        text_embs: Text embeddings [M, D]
        
    Returns:
        Similarity matrix [N, M]
    """
    # Normalize embeddings
    image_embs_norm = image_embs / (np.linalg.norm(image_embs, axis=1, keepdims=True) + 1e-8)
    text_embs_norm = text_embs / (np.linalg.norm(text_embs, axis=1, keepdims=True) + 1e-8)
    
    # Compute similarity matrix
    similarities = image_embs_norm @ text_embs_norm.T
    
    return np.clip(similarities, 0, 1)


def get_confidence_explanation(
    confidence: float,
    domain: str,
    model_used: str
) -> str:
    """
    Generate human-readable confidence explanation
    
    Args:
        confidence: Confidence score
        domain: Image domain
        model_used: Model name
        
    Returns:
        Explanation string
    """
    if confidence >= 0.8:
        level = "Very High"
        desc = "strong visual match and clear features"
    elif confidence >= 0.6:
        level = "High"
        desc = "good visual match with recognizable features"
    elif confidence >= 0.4:
        level = "Moderate"
        desc = "reasonable visual match but some ambiguity"
    elif confidence >= 0.2:
        level = "Low"
        desc = "weak visual match with significant uncertainty"
    else:
        level = "Very Low"
        desc = "very weak visual match, highly uncertain"
    
    return f"{level} confidence ({confidence:.1%}) - {desc} detected by {model_used} in {domain} domain"


def validate_semantic_consistency(
    prediction_label: str,
    caption: str,
    image_emb: np.ndarray,
    model_instance
) -> Dict:
    """
    🛡️ SEMANTIC VALIDATION - Cross-check prediction consistency
    
    Validates that the predicted label is semantically aligned with:
    1. The generated caption
    2. The image embedding
    
    High inconsistency indicates potential hallucination or error.
    
    Args:
        prediction_label: Predicted class label
        caption: Generated image caption
        image_emb: Image embedding
        model_instance: CLIP model instance
        
    Returns:
        Dict with:
        - is_consistent: bool (True if alignment > 0.4)
        - alignment_score: float (0-1)
        - verdict: str (description)
        - confidence_adjustment: float (0.8-1.2 multiplier)
    """
    try:
        # Encode prediction and caption
        pred_emb = model_instance.encode_text([prediction_label])[0]
        caption_emb = model_instance.encode_text([caption])[0]
        
        # Compute alignments
        pred_caption_sim = compute_cosine_similarity(pred_emb, caption_emb)
        pred_image_sim = compute_cosine_similarity(image_emb, pred_emb)
        caption_image_sim = compute_cosine_similarity(image_emb, caption_emb)
        
        # Average alignment score
        alignment_score = (pred_caption_sim + pred_image_sim) / 2.0
        
        # Determine consistency
        if alignment_score >= 0.6:
            verdict = "Highly consistent - prediction aligns well with image and caption"
            confidence_adj = 1.1  # Boost confidence
            is_consistent = True
        elif alignment_score >= 0.4:
            verdict = "Consistent - reasonable alignment with image and caption"
            confidence_adj = 1.0  # No adjustment\n            is_consistent = True
        elif alignment_score >= 0.25:
            verdict = "Weakly consistent - some alignment but with moderate uncertainty"
            confidence_adj = 0.85  # Reduce confidence
            is_consistent = False
        else:
            verdict = "Inconsistent - poor alignment between prediction, image, and caption"
            confidence_adj = 0.75  # Significantly reduce confidence
            is_consistent = False
        
        logger.debug(
            f"Semantic validation: pred={pred_caption_sim:.3f}, "
            f"img={pred_image_sim:.3f}, caption={caption_image_sim:.3f}, "
            f"avg={alignment_score:.3f}, adj={confidence_adj:.2f}"
        )
        
        return {
            "is_consistent": is_consistent,
            "alignment_score": float(alignment_score),
            "verdict": verdict,
            "confidence_adjustment": float(confidence_adj),
            "scores": {
                "prediction_caption_similarity": float(pred_caption_sim),
                "prediction_image_similarity": float(pred_image_sim),
                "caption_image_similarity": float(caption_image_sim)
            }
        }
        
    except Exception as e:
        logger.error(f"Semantic validation error: {e}")
        return {
            "is_consistent": True,
            "alignment_score": 0.5,
            "verdict": "Validation skipped due to error",
            "confidence_adjustment": 1.0,
            "scores": {}
        }

