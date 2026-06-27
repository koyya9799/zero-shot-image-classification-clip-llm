# app/caption_service.py
import torch
from PIL import Image
import logging

from .models.model_cache import ModelLoader, DEVICE

logger = logging.getLogger(__name__)

_processor = None
_model = None
_load_error = None

def _load_caption_model():
    """Load BLIP model lazily with fast caching"""
    global _processor, _model, _load_error
    
    if _model is not None:
        return True
    
    if _load_error is not None:
        logger.error(f"Previous BLIP model load failed: {_load_error}")
        return False
    
    try:
        logger.info("⚡ Loading BLIP caption model (fast cached)...")
        cache_data = ModelLoader.load_caption_model_fast()
        _processor = cache_data["processor"]
        _model = cache_data["model"]
        logger.info("✓ BLIP model ready")
        return True
    except Exception as e:
        _load_error = str(e)
        logger.error(f"Failed to load BLIP model: {e}", exc_info=True)
        return False


def generate_caption(img: Image.Image, max_new_tokens: int = 30) -> str:
    """Generate image caption with fallback handling"""
    global _processor, _model
    
    # Try to load model if not already loaded
    if _processor is None or _model is None:
        if not _load_caption_model():
            logger.warning("BLIP model unavailable, returning generic caption")
            return "Image of unspecified content"
    
    try:
        with torch.no_grad():
            inputs = _processor(images=img, return_tensors="pt").to(DEVICE)
            out = _model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                num_beams=5,
                early_stopping=True,
            )
            caption = _processor.decode(out[0], skip_special_tokens=True)
        return caption
    except Exception as e:
        logger.error(f"Error generating caption: {e}", exc_info=True)
        return "Image content detected"
