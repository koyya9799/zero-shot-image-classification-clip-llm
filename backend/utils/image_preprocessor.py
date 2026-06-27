# backend/utils/image_preprocessor.py
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

def process_image_bytes(image_bytes: bytes) -> Image.Image:
    """Read bytes into a standard RGB PIL Image."""
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return img
    except Exception as e:
        logger.error(f"Image preprocessing failed: {e}")
        raise ValueError("Invalid image file format")
