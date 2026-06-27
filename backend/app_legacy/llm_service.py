# app/llm_service.py
import os
import json
from typing import Dict, List
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
_api_key = os.getenv("GEMINI_API_KEY")
if _api_key:
    genai.configure(api_key=_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None


def expand_prompts_with_llm(class_names: List[str], domain: str) -> Dict[str, List[str]]:
    """Optional: use LLM to generate extra prompts. Returns {label: [prompt,...]}"""
    if model is None:
        return {}

    prompt = f"""
You help build prompts for CLIP in a domain-aware way.

Domain: {domain}
Class names: {class_names}

For each class, generate 3 very short descriptive English prompts suitable as image captions.
Respond as JSON: {{"class_name": ["prompt1", "prompt2", "prompt3"], ...}}
"""

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
            )
        )
        return json.loads(response.text)
    except Exception:
        return {}


def llm_reason_and_label(
    caption: str,
    candidates: List[Dict],
    user_hint: str,
    domain: str,
) -> Dict[str, str]:
    """Choose final label + explanation using LLM with high accuracy focus."""
    if model is None:
        # fallback – just take top candidate
        top = candidates[0]
        return {
            "label": top["label"],
            "reason": "Selected highest-similarity CLIP class (LLM disabled).",
        }

    prompt = f"""
You are an EXPERT visual recognition specialist with 20+ years of experience.
Your task: IDENTIFY THE MOST ACCURATE PRIMARY LABEL from candidates.

📸 IMAGE INFORMATION:
Caption: "{caption}"
Domain: {domain}

🎯 CANDIDATE LABELS (with confidence scores):
"""
    for i, candidate in enumerate(candidates[:5], 1):
        prompt += f"\n{i}. {candidate['label']}: {candidate['score']:.3f}"
    
    prompt += f"""

❓ User's hint/context: "{user_hint}"

🔬 YOUR TASK:
1. Analyze the caption and candidates carefully
2. Consider semantic alignment between caption and each candidate
3. Choose the SINGLE MOST ACCURATE label that best describes the primary subject
4. Determine the infinite/custom Domain (e.g. vintage vehicles, modern art, broken bones, architecture) based on the image subject.
5. Provide a detailed, evidence-based explanation that is APPROXIMATELY 100 WORDS LONG. Describe why this label is correct and what visual features support it.

⚠️ ACCURACY IS CRITICAL - Choose conservatively if uncertain.

Respond ONLY as valid JSON (no markdown blocks):
{{
  "domain": "<newly_identified_highly_specific_domain>",
  "label": "<most_accurate_label>",
  "reason": "<100-word explanation>",
  "confidence_multiplier": <0.8_to_1.2_adjustment_factor>
}}
"""

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.05,  # ULTRA-LOW for maximum accuracy
                top_p=0.9,         # Reduce sampling diversity
                max_output_tokens=350,
            )
        )
        
        # Clean response text - remove markdown code blocks if present
        response_text = response.text.strip()
        if response_text.startswith("```"):
            # Remove markdown code blocks
            lines = response_text.split("\n")
            response_text = "\n".join([line for line in lines if not line.startswith("```")])
            response_text = response_text.strip()
        
        # Try to parse JSON
        parsed = json.loads(response_text)
        return parsed
        
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Response text: {response.text}")
        top = candidates[0]
        return {
            "label": top["label"],
            "reason": "Fallback to top CLIP candidate due to JSON parse error.",
            "confidence_multiplier": 0.95
        }
    except Exception as e:
        print(f"LLM error: {e}")
        top = candidates[0]
        return {
            "label": top["label"],
            "reason": "Fallback to top CLIP candidate due to LLM error.",
            "confidence_multiplier": 0.95
        }


def llm_narrative(
    caption: str,
    candidates: List[Dict],
    user_hint: str,
    domain: str,
) -> str:
    """Generate detailed, accurate narrative description with focus on truth."""
    if model is None:
        return caption  # fallback: just caption

    prompt = f"""
You are an EXPERT image analyst describing images with ABSOLUTE ACCURACY.

Caption: "{caption}"
Domain: {domain}
Detected classes: {[c['label'] for c in candidates[:5]]}

📝 TASK: Write a 6-9 sentence narrative that:
1. Describes ONLY what is clearly visible in the caption
2. Includes main subjects, key objects, and visual elements
3. Mentions colors, textures, composition, and spatial relationships
4. Notes the environment/setting and atmosphere
5. Describes any identified actions or states

⚠️ ACCURACY CRITICAL:
- Do NOT fabricate details
- Only include facts supported by the caption
- Be specific and precise
- Avoid speculation beyond what is clear

Respond ONLY with the narrative text (no introduction, no conclusion):
"""

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.15,  # LOWERED from 0.5 for accuracy
                top_p=0.9,
                max_output_tokens=400,
            )
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Narrative generation error: {e}")
        return caption  # Safe fallback


def extract_objects(
    caption: str,
    candidates: List[Dict],
    domain: str,
) -> List[Dict]:
    """Extract a list of objects/entities present in the image with confidence scores."""
    if model is None:
        # Fallback: use top candidates as objects
        return [
            {"name": c["label"], "score": round(c.get("score", 0), 2)}
            for c in candidates[:5] if c.get("score", 0) > 0.1
        ]
    
    prompt = f"""
You are an expert visual object detection specialist.

Image caption: "{caption}"
Domain: {domain}
Detected classes with scores: {candidates}

Identify and list the main objects, entities, and significant visual elements present in the image.
For each object, estimate a confidence score between 0.0 and 1.0 based on how clearly identifiable it is in the image.

Respond ONLY as a JSON array of objects with "name" and "score" fields:
[
  {{"name": "object1", "score": 0.95}},
  {{"name": "object2", "score": 0.88}},
  {{"name": "object3", "score": 0.82}}
]

Rules:
- Use 3-8 objects
- Use simple noun phrases for object names
- Scores should reflect confidence (higher for clear/prominent objects)
- For medical images, focus on anatomical structures and abnormalities
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
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join([line for line in lines if not line.startswith("```")])
            response_text = response_text.strip()
        
        parsed = json.loads(response_text)
        if isinstance(parsed, list) and len(parsed) > 0:
            # Validate and clean objects
            objects = []
            for obj in parsed[:10]:  # Max 10 objects
                if isinstance(obj, dict) and "name" in obj and "score" in obj:
                    objects.append({
                        "name": str(obj["name"]).strip(),
                        "score": round(float(obj["score"]), 2)
                    })
            return objects if objects else [
                {"name": c["label"], "score": round(c.get("score", 0), 2)}
                for c in candidates[:5] if c.get("score", 0) > 0.1
            ]
        else:
            # Fallback to candidates
            return [
                {"name": c["label"], "score": round(c.get("score", 0), 2)}
                for c in candidates[:5] if c.get("score", 0) > 0.1
            ]
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error extracting objects: {e}")
        # Fallback to candidates
        return [
            {"name": c["label"], "score": round(c.get("score", 0), 2)}
            for c in candidates[:5] if c.get("score", 0) > 0.1
        ]

def extract_domain_and_classes(caption: str) -> dict:
    """Dynamically determine the domain and suggest 5-8 relevant classes for classification."""
    if model is None:
        return {"domain": "General", "classes": ["object", "person", "animal", "vehicle", "nature"]}
    
    prompt = f"""
Given this image caption: "{caption}"

1. What is the specific domain of this image? (e.g. Vehicles, Medical Images, Animals, Interior Design, Fashion, etc.)
2. List 5 to 8 specific candidate object classes that might be in this image to use for image classification classification.

Respond ONLY with valid JSON:
{{
  "domain": "Domain Name",
  "classes": ["class1", "class2", "class3", "class4", "class5"]
}}
"""
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=150,
            )
        )
        text = response.text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join([line for line in lines if not line.startswith("```")]).strip()
        
        parsed = json.loads(text)
        return parsed
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error extracting domain/classes: {e}")
        return {"domain": "General", "classes": ["object", "person", "animal", "vehicle", "nature"]}
