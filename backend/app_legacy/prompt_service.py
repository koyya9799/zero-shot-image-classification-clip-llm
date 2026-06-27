# app/prompt_service.py
from typing import List
from .llm_service import expand_prompts_with_llm

TEMPLATES = {
    "natural": [
        "a photo of a {}",
        "an image of a {}",
        "a realistic picture of a {}",
        "a clear photo of a {}",
        "a high quality image of a {}",
        "a detailed view of a {}",
        "{} in a natural setting",
        "{} in the wild",
    ],
    "medical": [
        "a medical X-ray image showing {}",
        "a radiology scan of {}",
        "a grayscale chest X-ray depicting {}",
        "a clinical image of {}",
        "a diagnostic scan showing {}",
        "medical imaging of {}",
    ],
    "vegetable": [
        "a fresh {} vegetable",
        "raw {} used for cooking",
        "a {} from a grocery market",
        "a fresh farm {}",
        "organic {} produce",
        "harvested {}",
        "a {} on display in supermarket",
        "fresh {} on retail shelves",
    ],
    "food": [
        "fresh {} ingredients",
        "a food ingredient {}",
        "a plated {} dish",
        "a close-up photo of {} on a plate",
        "a high resolution food photo of {}",
        "a cooked {} meal",
        "{} served as food",
        "a {} in a kitchen setting",
    ],
    "anime": [
        "an anime-style illustration of a {}",
        "a colorful cartoon drawing of a {}",
        "manga art of a {}",
        "Japanese animation style {}",
        "anime character {}",
    ],
    "sketch": [
        "a black and white line drawing of a {}",
        "a pencil sketch of a {}",
        "a detailed sketch of a {}",
        "line art of a {}",
        "hand-drawn illustration of a {}",
    ],
    "satellite": [
        "a top-down satellite image of {}",
        "an aerial photograph of {}",
        "satellite view of {}",
        "bird's eye view of {}",
        "overhead image of {}",
    ],
    "unknown": [
        "an image of a {}",
        "a photo of a {}",
        "{} in an image",
    ],
}

def build_prompts_for_label(label: str, domain: str) -> List[str]:
    base = [t.format(label) for t in TEMPLATES.get(domain, TEMPLATES["unknown"])]
    # optional: LLM expansion (if no API key, this returns {})
    extra = expand_prompts_with_llm([label], domain).get(label, [])
    # de-duplicate while preserving order
    seen = set()
    all_prompts: List[str] = []
    for p in base + extra:
        if p not in seen:
            seen.add(p)
            all_prompts.append(p)
    return all_prompts
