# app/models/llm_hybrid.py
"""
LLM Service for Hybrid System
Generates explanations and captions for multi-model predictions
"""
import os
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)

load_dotenv()
_api_key = os.getenv("GEMINI_API_KEY")
if _api_key:
    try:
        genai.configure(api_key=_api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("✓ Gemini API configured successfully")
    except Exception as e:
        logger.warning(f"Failed to configure Gemini API: {e}")
        model = None
else:
    model = None
    logger.warning("GEMINI_API_KEY not found - LLM features will use fallbacks")


def generate_hybrid_explanation(
    domain: str,
    model_used: str,
    prediction: str,
    confidence: float,
    caption: str,
    top_matches: List[Dict],
    domain_scores: Dict[str, float]
) -> Dict[str, str]:
    """
    Generate comprehensive explanation for hybrid model prediction
    
    Args:
        domain: Detected domain
        model_used: Model name (ViT-H/14 or MedCLIP)
        prediction: Top prediction label
        confidence: Confidence score
        caption: Image caption
        top_matches: Top prediction matches
        domain_scores: Domain similarity scores
        
    Returns:
        Dict with explanation, caption, and risk_notes
    """
    if model is None:
        return _generate_explanation_fallback(
            domain, model_used, prediction, confidence, caption, top_matches
        )
    
    # Build structured prompt for LLM
    prompt = f"""You are an expert image analyst specializing in visual domain classification.

IMAGE ANALYSIS DETAILS:
- Detected Domain: {domain}
- Primary Classification: {prediction}
- Confidence Score: {confidence:.1%}
- Image Caption: "{caption}"
- Analysis Model: {model_used}
- Top Alternative Classifications: {', '.join([m['label'] for m in top_matches[1:4]]) if len(top_matches) > 1 else 'N/A'}

Generate a professional analysis explanation that:
1. Describes the visual characteristics that led to this classification
2. Identifies key structural/compositional elements
3. Explains the confidence level
4. Notes any notable features or patterns

IMPORTANT: Write a single, cohesive explanation (2-4 sentences) that reads naturally, describing what makes this image fit the "{prediction}" classification based on its visual properties.

Example format (for medical X-ray): "The grayscale radiographic structure with visible rib cage, lung fields, and cardiac silhouette indicates a chest X-ray image."

Respond ONLY with the explanation text, nothing else."""

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=300
            )
        )
        
        explanation_text = response.text.strip()
        
        return {
            "caption": caption,
            "explanation": explanation_text,
            "risk_notes": _generate_risk_notes(domain, prediction)
        }
        
    except Exception as e:
        logger.error(f"LLM explanation error: {e}", exc_info=True)
        return _generate_explanation_fallback(
            domain, model_used, prediction, confidence, caption, top_matches
        )


def _generate_explanation_fallback(
    domain: str,
    model_used: str,
    prediction: str,
    confidence: float,
    caption: str,
    top_matches: List[Dict]
) -> Dict[str, str]:
    """Generate detailed explanation when LLM is unavailable"""
    
    # Domain-specific visual characteristic descriptions
    visual_characteristics = {
        "medical_image": {
            "chest_x_ray": "grayscale radiographic structure with visible rib cage, lung fields, and cardiac silhouette",
            "ct_scan": "cross-sectional computed tomography image with detailed tissue contrast and anatomical planes",
            "mri": "high-resolution magnetic resonance imaging with detailed soft tissue differentiation",
            "lung": "pulmonary imaging demonstrating respiratory structure and tissue patterns",
            "x_ray": "radiographic image showing bone density and anatomical alignment",
            "medical": "clinical imaging modality with diagnostic-grade visualization and technical annotation"
        },
        "natural_image": {
            "landscape": "photographic composition with natural scenery and environmental context",
            "portrait": "photographic representation of human subject with facial features and expression",
            "object": "product or object photography with clear subject isolation and lighting",
        },
        "sketch": {
            "drawing": "artistic line-based rendering with pen or pencil medium and detailed strokes",
            "sketch": "hand-drawn artwork with characteristic sketch patterns and artistic composition",
        },
        "artistic_image": {
            "painting": "artistic oil or acrylic painting with visible brushstrokes and color blending",
            "illustration": "artistic illustration with stylized elements and creative visual design",
            "artwork": "artistic creation demonstrating compositional and color theory principles",
        },
        "anime": {
            "anime": "anime-style artwork with characteristic cel-shading and Japanese animation aesthetics",
            "manga": "manga illustration with ink-based drawing style and sequential art composition",
        }
    }
    
    # Normalize strings: convert to lowercase, replace spaces/hyphens/multiple underscores with single underscore
    def normalize_str(s: str) -> str:
        return s.lower().replace(" ", "_").replace("-", "_")
    
    pred_clean = normalize_str(prediction)
    domain_clean = normalize_str(domain)
    
    visual_desc = "detailed image"
    
    # Try to find matching visual description
    if domain_clean in visual_characteristics:
        if pred_clean in visual_characteristics[domain_clean]:
            visual_desc = visual_characteristics[domain_clean][pred_clean]
        else:
            # Try partial matching - check if any key is contained in or contains the prediction
            for key in visual_characteristics[domain_clean].keys():
                # Exact normalize match
                key_normalized = normalize_str(key)
                if key_normalized == pred_clean:
                    visual_desc = visual_characteristics[domain_clean][key]
                    break
            else:
                # Use generic description
                visual_desc = f"{domain_clean.replace('_', ' ')}-type image with distinctive visual characteristics"
    
    # Build explanation
    explanation = (
        f"The {visual_desc} indicates a {prediction.lower()} classification. "
        f"With {confidence:.0%} confidence, the {model_used.replace('_', ' ')} model identified this based on "
        f"distinctive structural and visual patterns characteristic of this image category."
    )
    
    return {
        "caption": caption,
        "explanation": explanation,
        "risk_notes": _generate_risk_notes(domain, prediction)
    }


def _generate_risk_notes(domain: str, prediction: str) -> str:
    """Generate appropriate risk notes based on domain"""
    domain_lower = domain.lower()
    
    if "medical" in domain_lower:
        return (
            "⚠️ MEDICAL DISCLAIMER: This AI analysis is for reference only and not a substitute for "
            "professional medical diagnosis. Always consult qualified healthcare professionals for clinical decisions."
        )
    else:
        return "N/A - Not a medical image"


def generate_detailed_narrative(
    domain: str,
    model_used: str,
    prediction: str,
    caption: str,
    top_matches: List[Dict]
) -> Dict[str, str]:
    """
    Generate detailed narrative description with both short and detailed versions
    
    Args:
        domain: Image domain
        model_used: Model name
        prediction: Top prediction
        caption: Image caption
        top_matches: Top predictions
        
    Returns:
        Dict with 'short' and 'detailed' narrative texts
    """
    # Generate short summary
    short_narrative = caption
    
    # Try LLM first if available
    if model is not None:
        detailed_narrative = _generate_narrative_with_llm(
            domain, model_used, prediction, caption, top_matches
        )
    else:
        # Fallback: Generate detailed narrative programmatically
        detailed_narrative = _generate_narrative_fallback(
            domain, model_used, prediction, caption, top_matches
        )
    
    return {
        "short": short_narrative,
        "detailed": detailed_narrative
    }


def _generate_narrative_with_llm(
    domain: str,
    model_used: str,
    prediction: str,
    caption: str,
    top_matches: List[Dict]
) -> str:
    """Generate narrative using LLM API"""
    
    # Generate comprehensive prompt for detailed narrative
    prompt = f"""
You are an expert image analyst with deep domain knowledge. Write a detailed, flowing narrative analysis (minimum 200 words).

IMAGE CONTEXT:
- Domain: {domain}
- Classification: {prediction}
- Image Caption: "{caption}"
- Analysis Model: {model_used}
- Alternative predictions: {', '.join([m['label'] for m in top_matches[:3]])}

DETAILED ANALYSIS (MINIMUM 200 WORDS):
Write a comprehensive, flowing paragraph covering:

1. Overall composition and spatial arrangement
2. Detailed description of the main subject/classification
3. Visual characteristics (colors, textures, lighting, contrast)
4. Supporting details and context clues
5. Technical observations (quality, resolution, processing)

For MEDICAL images: Include anatomical structures, findings, and clinical significance.
For NON-MEDICAL images: Include scene context, environment, and visual elements.

MANDATORY: Write at least 200 words. Return ONLY the narrative text as a continuous paragraph.
"""
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.5,
                max_output_tokens=1200,
            )
        )
        
        detailed_narrative = response.text.strip()
        
        # Verify word count
        word_count = len(detailed_narrative.split())
        if word_count >= 200:
            logger.info(f"Generated detailed narrative with {word_count} words")
            return detailed_narrative
        else:
            logger.warning(f"LLM narrative has only {word_count} words, using fallback")
            return _generate_narrative_fallback(domain, model_used, prediction, caption, top_matches)
        
    except Exception as e:
        logger.error(f"LLM narrative generation error: {e}", exc_info=True)
        return _generate_narrative_fallback(domain, model_used, prediction, caption, top_matches)


def _generate_narrative_fallback(
    domain: str,
    model_used: str,
    prediction: str,
    caption: str,
    top_matches: List[Dict]
) -> str:
    """
    Generate detailed narrative without LLM (guaranteed 200+ words)
    Programmatic detailed description based on domain and prediction
    """
    
    # Get alternative predictions
    alternatives = [m.get('label', 'Unknown') for m in top_matches[1:4]] if len(top_matches) > 1 else []
    
    # Domain-specific context
    domain_context = {
        "medical_image": "This is a medical imaging examination that represents a specialized radiological study.",
        "chest x-ray": "This is a chest radiograph, a standard diagnostic imaging technique used in medical practice.",
        "sketch": "This is a sketch or line drawing, created with hand-drawn techniques.",
        "anime": "This is anime or manga-style artwork, featuring characteristic animation and illustration styles.",
        "natural_image": "This is a natural photograph capturing real-world subject matter.",
        "satellite": "This is satellite or aerial imagery, captured from an elevated perspective.",
        "medical": "This medical image represents clinical diagnostic imaging.",
    }
    
    # Get appropriate context based on domain
    domain_desc = ""
    for key, value in domain_context.items():
        if key.lower() in domain.lower():
            domain_desc = value
            break
    
    if not domain_desc:
        domain_desc = f"This image falls within the {domain} category of visual content."
    
    # Build detailed narrative with guaranteed 200+ words
    narrative_parts = [
        # Part 1: Introduction and overall composition (30-40 words)
        f"Classification Analysis: {domain_desc} The primary classification identifies this imagery as '{prediction}', which represents a significant categorization within visual analysis frameworks. ",
        
        # Part 2: Primary subject and classification reasoning (50-60 words)
        f"The subject matter classified as '{prediction}' displays characteristic features consistent with this categorization. This classification was determined through comprehensive visual analysis using {model_used} model technology. The imaging demonstrates distinctive patterns, morphological characteristics, and visual attributes that strongly support this identification within the {domain} domain. ",
        
        # Part 3: Visual characteristics and technical aspects (50-70 words)
        f"Visual examination reveals important characteristics including composition, arrangement, and presentation. The image displays technical qualities related to resolution, clarity, and visual fidelity. Color information, spatial distribution, lighting conditions, and contrast characteristics all contribute to the overall visual presentation. The technical parameters of this imagery reflect standard practices in {domain} imaging and presentation methodologies. ",
        
        # Part 4: Context and supporting evidence (40-50 words)
        f"Supporting contextual information includes consideration of alternative classifications such as {', '.join(alternatives) if alternatives else 'similar categories'}. Comparative analysis with these alternatives reinforces the primary classification with '{prediction}' showing the highest confidence score. The confidence in this classification is substantiated through multiple analytical approaches. ",
        
        # Part 5: Domain-specific observations (30-50 words)
        f"Within the {domain} imaging context, this example demonstrates typical characteristics observed in this category. The analysis considers domain-specific variables, technical parameters, and visual markers that are meaningful within this specialized classification framework. This representation provides valuable information for understanding {prediction} within its appropriate visual context. ",
        
        # Part 6: Summary and assessment (20-30 words)
        f"Overall, this analysis synthesizes multiple dimensions of visual information to support the classification of '{prediction}'. The comprehensive evaluation reflects systematic analysis of visual features, contextual information, and domain-specific characteristics.",
    ]
    
    detailed_narrative = "".join(narrative_parts)
    
    # Ensure we have at least 200 words
    word_count = len(detailed_narrative.split())
    if word_count >= 200:
        logger.info(f"Generated fallback narrative with {word_count} words")
        return detailed_narrative
    
    # If still short, add more detailed context
    if word_count < 200:
        additional_context = (
            f"\n\nAdditional Analysis: The classification '{prediction}' within the {domain} domain represents an important categorization in visual analysis. "
            f"The confidence in this determination is based on multiple complementary analysis methods. This categorization has implications for understanding the visual content and its relationship to other potential classifications. "
            f"The thorough examination of all visual, compositional, and technical aspects supports the validity of this classification determination. "
            f"Future analysis or verification may involve cross-referencing with domain expert knowledge or additional computational verification methods."
        )
        detailed_narrative += additional_context
    
    return detailed_narrative


def extract_objects_hybrid(
    domain: str,
    caption: str,
    top_matches: List[Dict]
) -> List[Dict]:
    """
    Extract objects/entities from image analysis
    
    Args:
        domain: Image domain
        caption: Image caption
        top_matches: Top classification matches
        
    Returns:
        List of objects with confidence scores
    """
    if model is None:
        # Fallback: use top matches
        return [
            {"name": m["label"], "score": round(m["score"], 2)}
            for m in top_matches[:5]
        ]
    
    prompt = f"""
Extract key objects/entities from this image analysis.

Domain: {domain}
Caption: "{caption}"
Detected classes: {[m['label'] for m in top_matches]}

List 3-8 main objects/entities with confidence scores (0.0-1.0).
For medical images: anatomical structures and abnormalities
For other images: main objects and scene elements

Respond ONLY as JSON array:
[
  {{"name": "object1", "score": 0.95}},
  {{"name": "object2", "score": 0.88}}
]
"""
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=200,
            )
        )
        
        response_text = response.text.strip()
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join([line for line in lines if not line.startswith("```")])
            response_text = response_text.strip()
        
        parsed = json.loads(response_text)
        
        if isinstance(parsed, list):
            return [
                {"name": str(obj.get("name", "")), "score": round(float(obj.get("score", 0)), 2)}
                for obj in parsed[:8]
                if "name" in obj and "score" in obj
            ]
    except Exception as e:
        logger.error(f"Object extraction error: {e}")
    
    # Fallback
    return [
        {"name": m["label"], "score": round(m["score"], 2)}
        for m in top_matches[:5]
    ]
