# app/domain_service.py
from typing import Literal, Optional

Domain = Literal["natural", "medical", "anime", "sketch", "satellite", "unknown"]

KEYWORDS = {
    "medical": [
        "xray", "x-ray", "ct", "mri", "scan", "radiograph", "chest", "lung", "lungs",
        "rib", "ribs", "opacity", "pulmonary", "cardiac", "heart", "bone", "fracture",
        "medical", "clinical", "diagnostic", "anatomy", "radiology", "imaging",
        "patient", "thorax", "abdomen", "skull", "spine", "vertebra",
        "alzheimer", "retinopathy", "cyst", "glaucoma", "glioma", "leukemia", 
        "osteoarthritis", "tuberculosis", "brain", "eye", "skin", "blood", "tumor"
    ],
    "anime": ["anime", "manga", "cartoon", "illustration", "character", "animated"],
    "satellite": ["satellite", "aerial", "top view", "remote sensing", "overhead", "bird's eye"],
    "sketch": ["sketch", "line art", "line-art", "drawing", "pencil", "hand-drawn"],
}

def infer_domain_from_hint(hint: Optional[str]) -> Domain:
    """Infer domain from user hint text."""
    if not hint:
        return "unknown"
    h = hint.lower()
    for dom, words in KEYWORDS.items():
        if any(w in h for w in words):
            return dom  # type: ignore
    return "natural"

def infer_domain_from_caption(caption: str) -> Domain:
    """Infer domain from image caption."""
    if not caption:
        return "unknown"
    c = caption.lower()
    
    # Check for medical imaging indicators
    medical_indicators = [
        "chest", "lung", "lungs", "xray", "x-ray", "rib", "ribs",
        "medical", "radiograph", "scan", "ct", "mri", "opacity",
        "pulmonary", "cardiac", "bone", "anatomy", "radiology",
        "alzheimer", "retinopathy", "cyst", "glaucoma", "glioma", "leukemia", 
        "osteoarthritis", "tuberculosis", "brain", "eye", "skin", "blood", "tumor"
    ]
    if any(word in c for word in medical_indicators):
        return "medical"
    
    # Check for anime/cartoon indicators  
    anime_indicators = ["anime", "manga", "cartoon", "animated", "character"]
    if any(word in c for word in anime_indicators):
        return "anime"
    
    # Check for sketch/drawing indicators
    sketch_indicators = ["sketch", "drawing", "line art", "pencil", "hand-drawn"]
    if any(word in c for word in sketch_indicators):
        return "sketch"
    
    # Check for satellite/aerial indicators
    satellite_indicators = ["satellite", "aerial", "overhead", "bird's eye", "top view"]
    if any(word in c for word in satellite_indicators):
        return "satellite"
    
    return "natural"

def infer_domain(caption: str = "", user_hint: str = "") -> Domain:
    """
    Infer domain from both caption and user hint.
    User hint takes precedence, then caption analysis.
    """
    # First try user hint
    if user_hint:
        hint_domain = infer_domain_from_hint(user_hint)
        if hint_domain != "unknown" and hint_domain != "natural":
            return hint_domain
    
    # Then try caption
    caption_domain = infer_domain_from_caption(caption)
    if caption_domain != "unknown":
        return caption_domain
    
    # Default to natural
    return "natural"
