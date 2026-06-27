# app/models/router.py
"""
Domain Router
Intelligently routes images to appropriate model (ViT-H/14 or MedCLIP)
"""
import numpy as np
from PIL import Image
from typing import Tuple, Literal
import logging

from .clip_vith14 import get_vith14_model
from .medclip_model import get_medclip_model

logger = logging.getLogger(__name__)

DomainType = Literal["medical", "fashion", "traffic", "satellite", "industrial", "natural"]

# Domain detection prompts - more distinctive keywords for better differentiation
DOMAIN_PROMPTS = {
    "medical": "x-ray scan radiograph ct mri ultrasound medical diagnosis hospital clinical anatomy organs tissue bone skeleton fracture disease pathology",
    "fashion": "clothing apparel dress shirt pants jacket shoes accessories fashion style model outfit",
    "traffic": "car truck bus motorcycle bicycle pedestrian traffic sign road highway street vehicle intersection",
    "satellite": "satellite aerial top view remote sensing Earth observation urban area vegetation water map overhead",
    "industrial": "factory warehouse machinery equipment industrial production manufacturing heavy metal construction assembly line workspace",
    "natural": "animal plant landscape outdoor nature person dog cat bird tree flower everyday scene scenery photo"
}

# Domain confidence thresholds
MEDICAL_THRESHOLD = 0.10  # Lowered so MedCLIP activates for fractures and standard x-rays reliably
TRAFFIC_THRESHOLD = 0.35  # Add minimum threshold for traffic detection

class DomainRouter:
    """Routes images to appropriate CLIP model based on domain (ViT-L-14 OpenAI)"""
    
    def __init__(self):
        self.vith14 = None
        self.medclip = None
        self._loaded = False
    
    def _ensure_loaded(self):
        """Lazy load models on first use"""
        if self._loaded:
            return
        
        try:
            logger.info("⚡ Initializing ViT-L-14 model (openai pretrained)...")
            self.vith14 = get_vith14_model()
            self.vith14._ensure_loaded()
            logger.info("✓ ViT-L-14 ready (768-dim embeddings, OpenAI pretrained)")
        except Exception as e:
            logger.error(f"Failed to initialize ViT-H/14: {e}", exc_info=True)
            raise
        
        try:
            logger.info("Initializing MedCLIP model...")
            self.medclip = get_medclip_model()
            self.medclip._ensure_loaded()
            logger.info("✓ MedCLIP model initialized")
        except Exception as e:
            logger.error(f"Failed to initialize MedCLIP: {e}", exc_info=True)
            raise
        
        self._loaded = True
    
    def estimate_domain(self, image: Image.Image) -> Tuple[DomainType, float, dict]:
        """
        🔍 DOMAIN DETECTION - CLIP SEMANTIC MATCHING LAYER
        
        Converts image to embedding and finds best-matching domain via cosine similarity.
        
        Mathematical Flow:
        [1] E_img = ViT-H/14_vision(Image)
            └─> Dense semantic vector (1024-dim), encodes visual concepts
        
        [2] For each domain (medical, fashion, traffic, satellite, industrial, natural):
            E_domain = ViT-H/14_text(domain_keywords)
            └─> Text embedding for domain description
        
        [3] Similarity = cos(E_img, E_domain)
            = (E_img · E_domain) / (||E_img|| × ||E_domain||)
            └─> Score range: 0.0 (no match) to 1.0 (perfect match)
        
        [4] best_domain = argmax(similarities)
            confidence = max(similarities)
        
        Returns highest similarity domain + all 6 scores for transparency.
        
        Args:
            image: PIL Image (any size, auto-resized to 224x224)
            
        Returns:
            Tuple of (domain, confidence, all_scores)
        """
        self._ensure_loaded()
        # Encode image with ViT-H/14
        image_emb = self.vith14.encode_image(image)
        
        # Encode domain prompts
        domain_labels = list(DOMAIN_PROMPTS.keys())
        domain_texts = [DOMAIN_PROMPTS[d] for d in domain_labels]
        text_embs = self.vith14.encode_text(domain_texts)
        
        # Compute similarities
        similarities = self.vith14.compute_similarity(image_emb, text_embs)
        
        # Get top domain
        top_idx = np.argmax(similarities)
        domain = domain_labels[top_idx]
        confidence = float(similarities[top_idx])
        
        # Create scores dict
        all_scores = {
            domain_labels[i]: float(similarities[i])
            for i in range(len(domain_labels))
        }
        
        logger.info(f"Domain estimation: {domain} (confidence: {confidence:.3f})")
        
        return domain, confidence, all_scores  # type: ignore
    
    def route(self, image: Image.Image) -> Tuple[str, DomainType, float, dict]:
        """
        Route image to appropriate model
        
        Args:
            image: PIL Image
            
        Returns:
            Tuple of (model_name, domain, confidence, domain_scores)
        """
        domain, confidence, domain_scores = self.estimate_domain(image)
        
        # Medical routing only if:
        # 1. Detected domain IS medical AND
        # 2. Medical score is high enough
        medical_score = domain_scores.get("medical", 0)
        
        # Use MedCLIP only if medical is clearly the best option
        if domain == "medical" and medical_score >= MEDICAL_THRESHOLD:
            model_name = "MedCLIP"
            logger.info(f"Using MedCLIP: medical={medical_score:.3f}")
        else:
            # Use ViT-H/14 for all other cases (more robust for non-medical)
            model_name = "ViT-H/14"
            logger.info(f"Using ViT-H/14: domain={domain}, confidence={confidence:.3f}")
        
        logger.info(f"Routing to {model_name} for {domain} domain (score: {confidence:.3f})")
        
        return model_name, domain, confidence, domain_scores
    
    def classify_with_routing(
        self,
        image: Image.Image,
        labels: list,
        top_k: int = 5,
        force_model: str = None
    ) -> dict:
        """
        Classify image with automatic model routing
        
        Args:
            image: PIL Image
            labels: List of possible class labels
            top_k: Number of top predictions
            force_model: "MedCLIP" or "ViT-H/14" to skip auto-detection
            
        Returns:
            Classification results with routing information
        """
        # Determine which model to use
        if force_model:
            model_name = force_model
            domain, domain_conf, domain_scores = self.estimate_domain(image)
        else:
            model_name, domain, domain_conf, domain_scores = self.route(image)
        
        logger.info(
            f"🎯 Routing Classification:"
            f"\n  Model: {model_name}"
            f"\n  Domain: {domain} (conf: {domain_conf:.3f})"
            f"\n  Labels: {len(labels)} candidates - {labels[:5]}..." if len(labels) > 5 else f"\n  Labels: {labels}"
        )
        
        # Classify with appropriate model
        if model_name == "MedCLIP":
            predictions, image_emb = self.medclip.classify(image, labels, top_k)
            logger.info(f"✅ MedCLIP classification complete - Top: {predictions[0]['label']} ({predictions[0]['score']:.3f})")
        else:
            predictions, image_emb = self.vith14.classify(image, labels, top_k)
            logger.info(f"✅ ViT-H/14 classification complete - Top: {predictions[0]['label']} ({predictions[0]['score']:.3f})")
        
        return {
            "model_used": model_name,
            "domain": domain,
            "domain_confidence": domain_conf,
            "domain_scores": domain_scores,
            "predictions": predictions,
            "image_embedding": image_emb
        }


# Global instance
_router = None

def get_router() -> DomainRouter:
    """Get or create global router instance"""
    global _router
    if _router is None:
        _router = DomainRouter()
    return _router
