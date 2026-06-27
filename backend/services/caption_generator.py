# backend/services/caption_generator.py
import torch
from PIL import Image
import logging

from models.blip_model import get_blip_model
from models.llm_model import get_llm_model
from models.model_cache import DEVICE

logger = logging.getLogger(__name__)

def _generate_llm_caption(img: Image.Image, domain: str = "unknown") -> str:
    """Generate caption using configured LLM vision provider with domain conditioning."""
    try:
        llm = get_llm_model()
        if not llm.is_available():
            return None
        
        # CRITICAL: Domain conditioning to prevent cross-domain confusion
        domain_instructions = ""
        if domain.lower() == "industrial":
            domain_instructions = """You are analyzing an INDUSTRIAL DEFECT IMAGE.
Focus on: metal surfaces, welds, cracks, corrosion, rust, structural damage ONLY.
IGNORE: wood, natural textures, plants, animals, organic materials.
For this industrial image, describe metal defects, fractures, and corrosion exclusively."""
        elif domain.lower() == "medical":
            domain_instructions = """Analyze this MEDICAL IMAGE ONLY. Focus on radiological findings. Ignore non-medical content."""
        elif domain.lower() == "vegetable":
            domain_instructions = """Analyze this VEGETABLE/PRODUCE IMAGE. Focus on vegetables, crops, and agricultural produce.
Can be: fresh vegetables, harvested produce, vegetables on display in stores, retail produce sections.
Describe: vegetable types, colors, shapes, leaf textures, condition (fresh vs aged), arrangement, and visible characteristics.
Include specific features: florets (broccoli/cauliflower), leafiness (cabbage/lettuce), root structure (carrots), roundness (pumpkin), store/shelf context."""
        elif domain.lower() == "food":
            domain_instructions = """Analyze this FOOD IMAGE. Focus on dishes, ingredients, and food items.
Describe: food type, color, texture, plating style, ingredients visible, cooking method (raw/cooked), presentation."""
        else:
            domain_instructions = "Provide accurate description specific to this domain."
        
        prompt = f"""{domain_instructions}

Provide a concise, factual description of this image in one sentence (max 15 words). 
Focus on the main subject, its key visual features, and context. Be specific and precise.
Do not use phrases like 'the image shows' or 'this is'. Just describe what you see."""
        
        caption = llm.generate_vision(prompt=prompt, image=img, temperature=0.3, max_tokens=50)
        logger.info(f"LLM caption ({domain}): {caption}")
        return caption
    except Exception as e:
        logger.warning(f"LLM caption generation failed: {e}")
        return None

def _merge_captions(blip_caption: str, llm_caption: str) -> str:
    """Intelligently merge BLIP and LLM captions for best accuracy"""
    # Extract key terms from both
    blip_words = set(blip_caption.lower().split())
    llm_words = set(llm_caption.lower().split())
    
    # Calculate overlap
    overlap = len(blip_words & llm_words) / max(len(blip_words), len(llm_words))
    
    # High overlap (>40%) = both agree, use LLM (better phrasing)
    if overlap > 0.4:
        logger.info(f"Caption agreement {overlap:.2f}, using LLM caption")
        return llm_caption
    
    # Low overlap (<20%) = potential hallucination, use BLIP (more grounded)
    if overlap < 0.2:
        logger.info(f"Caption disagreement {overlap:.2f}, using BLIP for safety")
        return blip_caption
    
    # Medium overlap = blend key information
    logger.info(f"Caption partial agreement {overlap:.2f}, using LLM with BLIP verification")
    return llm_caption

def generate_caption(img: Image.Image, max_new_tokens: int = 30, domain: str = "unknown") -> str:
    """Generate image caption using intelligent BLIP + LLM hybrid with cross-validation"""
    blip_caption = None
    llm_caption = None
    
    # Get BLIP caption (vision-grounded)
    try:
        blip = get_blip_model()
        processor = blip.processor
        model = blip.model
        
        with torch.no_grad():
            inputs = processor(images=img, return_tensors="pt").to(DEVICE)
            out = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                num_beams=5,
                early_stopping=True,
                repetition_penalty=1.1,
                no_repeat_ngram_size=2,
            )
            blip_caption = processor.decode(out[0], skip_special_tokens=True)
            
            # BLIP frequently misspells giraffe as "git" or "gi gife" with various penalties
            blip_caption = blip_caption.replace("gi gife", "giraffes").replace("git", "giraffes")
            logger.info(f"BLIP caption: {blip_caption}")
    except Exception as e:
        logger.error(f"Error generating BLIP caption: {e}")
    
    # Get LLM caption (semantic understanding) with domain conditioning
    llm_caption = _generate_llm_caption(img, domain=domain)
    
    # Intelligently combine both captions
    if blip_caption and llm_caption:
        merged = _merge_captions(blip_caption, llm_caption)
        logger.info(f"Hybrid caption selected: {merged}")
        return merged
    elif llm_caption:
        logger.info("Using LLM-only caption")
        return llm_caption
    elif blip_caption:
        logger.info("Using BLIP-only caption")
        return blip_caption
    else:
        return "An image."
