# app/routes/classify.py
"""
Hybrid Classification Route
Main endpoint for ViT-H/14 + MedCLIP classification system
"""
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from PIL import Image
import io
import time
import logging
from typing import Optional, List
import numpy as np

from ..models.router import get_router
from ..models.clip_vith14 import get_vith14_model
from ..models.medclip_model import get_medclip_model
from ..models.similarity import (
    compute_confidence_score,
    get_confidence_explanation,
    compute_cosine_similarity,
    validate_semantic_consistency
)
from ..models.llm_hybrid import (
    generate_hybrid_explanation,
    generate_detailed_narrative,
    extract_objects_hybrid
)
from ..caption_service import generate_caption

logger = logging.getLogger(__name__)


def ensure_json_serializable(obj):
    """Recursively convert numpy types to Python native types"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: ensure_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [ensure_json_serializable(item) for item in obj]
    return obj

router = APIRouter(prefix="/api", tags=["classification"])

# Default class labels for different domains
DEFAULT_LABELS = {
    "medical": [
        # Anatomical structures
        "chest x-ray",
        "lung",
        "heart",
        "rib cage",
        "spine",
        "diaphragm",
        # Common findings/diseases
        "pneumonia",
        "pulmonary opacity",
        "consolidation",
        "pleural effusion",
        "atelectasis",
        "cardiomegaly",
        "pulmonary edema",
        "pneumothorax",
        "lung nodule",
        "lung mass",
        "infiltrate",
        "interstitial marking",
        "alzheimer's disease",
        "diabetic retinopathy",
        "epidermoid cyst",
        "bone fracture",
        "glaucoma",
        "glioma",
        "leukemia",
        "osteoarthritis",
        "tuberculosis",
        # Status
        "normal chest x-ray",
        "abnormal chest x-ray",
        "clear lung fields",
        "lung infection",
        "pulmonary disease"
    ],
    "fashion": [
        "dress",
        "shirt",
        "pants",
        "jacket",
        "shoes",
        "accessories",
        "formal wear",
        "casual wear"
    ],
    "traffic": [
        "car",
        "truck",
        "bus",
        "motorcycle",
        "bicycle",
        "pedestrian",
        "traffic sign",
        "road"
    ],
    "satellite": [
        "urban area",
        "vegetation",
        "water",
        "road network",
        "agricultural land",
        "forest",
        "buildings"
    ],
    "industrial": [
        "machinery",
        "factory",
        "assembly line",
        "warehouse",
        "industrial equipment",
        "manufacturing"
    ],
    "natural": [
        "dog",
        "cat",
        "bird",
        "tree",
        "flower",
        "person",
        "building",
        "landscape",
        "vehicle",
        "food"
    ]
}


@router.post("/classify-hybrid")
async def classify_hybrid(
    file: UploadFile = File(...),
    custom_labels: Optional[str] = Form(default=None),
    top_k: int = Form(default=5)
):
    """
    Hybrid classification endpoint with automatic model routing
    
    - Automatically detects domain using ViT-H/14
    - Routes to MedCLIP for medical images, ViT-H/14 for others
    - Generates LLM-based explanations
    - Returns comprehensive analysis
    """
    start_time = time.time()
    
    try:
        # Read and process image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Get router instance
        domain_router = get_router()
        
        # Parse custom labels or use defaults
        if custom_labels:
            labels = [label.strip() for label in custom_labels.split(",")]
            logger.info(f"Using {len(labels)} custom labels")
        else:
            # Detect domain first for default labels
            _, domain, domain_conf, domain_scores = domain_router.route(image)
            labels = DEFAULT_LABELS.get(domain, DEFAULT_LABELS["natural"])
            logger.info(
                f"Domain detected: {domain} (confidence: {domain_conf:.3f})"
                f" - Using {len(labels)} domain-specific labels"
            )
        
        # Classify with automatic routing
        classification_result = domain_router.classify_with_routing(
            image=image,
            labels=labels,
            top_k=top_k
        )
        
        # Extract results
        model_used = classification_result["model_used"]
        domain = classification_result["domain"]
        domain_confidence = float(classification_result["domain_confidence"])
        domain_scores = {k: float(v) for k, v in classification_result["domain_scores"].items()}
        predictions = classification_result["predictions"]
        image_emb = classification_result["image_embedding"]
        
        # Get top prediction
        top_prediction = predictions[0]
        prediction_label = str(top_prediction["label"])
        prediction_score = float(top_prediction["score"])
        
        # Generate caption
        caption = generate_caption(image)
        
        # Get appropriate model for caption embedding
        if model_used == "MedCLIP":
            model = get_medclip_model()
        else:
            model = get_vith14_model()
        
        # Encode caption for confidence calculation
        caption_emb = model.encode_text([caption])[0]
        
        # Compute final confidence score
        confidence_score = compute_confidence_score(
            domain=domain,
            model_used=model_used,
            prediction_score=float(prediction_score),
            image_emb=image_emb,
            caption_emb=caption_emb,
            domain_similarity=float(domain_confidence)
        )
        
        # Ensure confidence_score is native Python float
        confidence_score = float(confidence_score)
        
        # Generate LLM explanation
        llm_result = generate_hybrid_explanation(
            domain=domain,
            model_used=model_used,
            prediction=prediction_label,
            confidence=confidence_score,
            caption=caption,
            top_matches=predictions,
            domain_scores=domain_scores
        )
        
        # Generate detailed narrative with short and detailed versions
        narrative_result = generate_detailed_narrative(
            domain=domain,
            model_used=model_used,
            prediction=prediction_label,
            caption=llm_result["caption"],
            top_matches=predictions
        )
        
        # Determine narrative confidence based on classification score
        if confidence_score >= 0.7:
            narrative_confidence = "High"
        elif confidence_score >= 0.4:
            narrative_confidence = "Medium"
        else:
            narrative_confidence = "Low"
        
        # Extract objects
        objects = extract_objects_hybrid(
            domain=domain,
            caption=llm_result["caption"],
            top_matches=predictions
        )
        
        # Compute inference time
        inference_time = time.time() - start_time
        
        # Format domain name for display (e.g., "medical_image" -> "Medical Imaging")
        domain_display = domain.replace("_", " ").title()
        
        # Format model name for display
        model_display = model_used.replace("_", " ").title() if "_" in model_used else model_used
        
        # Format prediction for display
        prediction_display = prediction_label.replace("_", " ").title()
        
        # Prepare structured response in user's desired format
        response = {
            "domain": domain_display,
            "model_used": model_display,
            "prediction": prediction_display,
            "confidence": float(round(confidence_score, 2)),  # Ensure native Python float
            "top_predictions": [
                {
                    "label": str(pred["label"]).replace("_", " ").title(),
                    "score": float(pred["score"])
                }
                for pred in predictions[:5]  # Return top 5
            ],
            "caption": llm_result["caption"],
            "explanation": llm_result["explanation"],
            "narrative": {
                "short": narrative_result.get("short", ""),
                "detailed": narrative_result.get("detailed", ""),
                "confidence": narrative_confidence
            },
            "risk_notes": llm_result.get("risk_notes", ""),
            "objects": [
                {
                    "name": obj.get("name", "").replace("_", " ").title(),
                    "score": float(obj.get("score", 0))
                }
                for obj in objects
            ],
            "metadata": {
                "raw_domain": domain,
                "domain_confidence": float(round(domain_confidence, 4)),
                "raw_prediction_score": float(round(prediction_score, 4)),
                "total_labels_evaluated": len(labels),
                "inference_time_seconds": float(round(inference_time, 3)),
                "model_details": {
                    "name": model_used,
                    "routing": "Automatic domain detection with model selection",
                    "medical_detected": domain.lower() in ["medical", "medical_image"]
                },
                "confidence_explanation": get_confidence_explanation(
                    confidence_score, domain, model_used
                )
            }
        }
        
        logger.info(
            f"Classification complete: {prediction_label} ({confidence_score:.2%}) "
            f"using {model_used} in {inference_time:.2f}s"
        )
        
        # Ensure all values are JSON serializable
        response = ensure_json_serializable(response)
        return response
        
    except Exception as e:
        logger.error(f"Classification error: {e}", exc_info=True)
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Full traceback:\n{error_detail}")
        
        # Return error response with safe types
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "detail": "Internal server error during classification",
                "traceback": error_detail
            }
        )


@router.post("/classify")
async def classify_open_ended(
    file: UploadFile = File(...),
    user_text: Optional[str] = Form(default=None),
    top_k: int = Form(default=10)
):
    """
    Open-ended classification endpoint - detects ALL objects without predefined labels
    
    - Generates image caption using state-of-the-art model
    - Extracts objects dynamically from the caption using LLM
    - Classifies against detected objects (100% custom, no predefined classes)
    - Works across any domain, any objects, any scenarios
    """
    start_time = time.time()
    
    try:
        # Read and process image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Get router instance
        domain_router = get_router()
        
        # Step 1: Generate caption (describes what's in the image)
        caption = generate_caption(image)
        logger.info(f"Generated caption: {caption[:100]}...")
        
        # Step 2: Determine domain for better context
        _, domain, _, domain_scores = domain_router.route(image)
        logger.info(f"Detected domain: {domain}")
        
        # Step 3: Use custom user labels if provided, otherwise extract objects
        if user_text:
            # User provided specific labels to classify
            labels = [label.strip() for label in user_text.split(",")]
            logger.info(f"Using user-provided labels: {labels}")
        else:
            # Fully open-ended: extract objects from caption
            logger.info("Performing open-ended detection...")
            # First, get some initial candidates to help guide object extraction
            temp_labels = ["object", "item", "entity", "person", "thing"]
            temp_result = domain_router.classify_with_routing(
                image=image,
                labels=temp_labels,
                top_k=1
            )
            
            # Extract objects from the caption
            extracted = extract_objects_hybrid(
                domain=domain,
                caption=caption,
                top_matches=temp_result["predictions"]
            )
            
            # Use extracted objects as labels
            labels = [obj["name"] for obj in extracted]
            logger.info(f"Extracted {len(labels)} objects: {labels}")
        
        # Step 4: Classify with detected/provided labels
        classification_result = domain_router.classify_with_routing(
            image=image,
            labels=labels,
            top_k=min(top_k, len(labels))
        )
        
        # Extract results
        model_used = classification_result["model_used"]
        domain_confidence = float(classification_result["domain_confidence"])
        domain_scores_full = {k: float(v) for k, v in classification_result["domain_scores"].items()}
        predictions = classification_result["predictions"]
        image_emb = classification_result["image_embedding"]
        
        # Get top prediction
        top_prediction = predictions[0]
        prediction_label = str(top_prediction["label"])
        prediction_score = float(top_prediction["score"])
        
        # Get appropriate model for caption embedding
        if model_used == "MedCLIP":
            model = get_medclip_model()
        else:
            model = get_vith14_model()
        
        # Encode caption for confidence calculation
        caption_emb = model.encode_text([caption])[0]
        
        # 🛡️ SEMANTIC VALIDATION - Check consistency
        validation_result = validate_semantic_consistency(
            prediction_label=prediction_label,
            caption=caption,
            image_emb=image_emb,
            model_instance=model
        )
        logger.info(f"Semantic validation: {validation_result['verdict']}")
        
        # Compute final confidence score with validation adjustment
        confidence_score = compute_confidence_score(
            domain=domain,
            model_used=model_used,
            prediction_score=prediction_score,
            image_emb=image_emb,
            caption_emb=caption_emb,
            domain_similarity=domain_confidence,
            confidence_multiplier=validation_result["confidence_adjustment"]
        )
        
        # Generate LLM explanation
        llm_result = generate_hybrid_explanation(
            domain=domain,
            model_used=model_used,
            prediction=prediction_label,
            confidence=confidence_score,
            caption=caption,
            top_matches=predictions,
            domain_scores=domain_scores_full
        )
        
        # Generate detailed narrative with short and detailed versions
        narrative_result = generate_detailed_narrative(
            domain=domain,
            model_used=model_used,
            prediction=prediction_label,
            caption=llm_result["caption"],
            top_matches=predictions
        )
        
        # Determine narrative confidence based on classification score
        if confidence_score >= 0.7:
            narrative_confidence = "High"
        elif confidence_score >= 0.4:
            narrative_confidence = "Medium"
        else:
            narrative_confidence = "Low"
        
        # Extract objects (again for final response)
        objects = extract_objects_hybrid(
            domain=domain,
            caption=llm_result["caption"],
            top_matches=predictions
        )
        
        inference_time = time.time() - start_time
        
        # Format domain name for display
        domain_display = domain.replace("_", " ").title()
        model_display = model_used.replace("_", " ").title() if "_" in model_used else model_used
        prediction_display = prediction_label.replace("_", " ").title()
        
        # Build response in structured format
        response = {
            "domain": domain_display,
            "model_used": model_display,
            "prediction": prediction_display,
            "confidence": float(round(confidence_score, 2)),
            "top_predictions": [
                {
                    "label": str(pred["label"]).replace("_", " ").title(),
                    "score": float(pred["score"])
                }
                for pred in predictions[:5]
            ],
            "caption": caption,
            "explanation": llm_result["explanation"],
            "narrative": {
                "short": narrative_result.get("short", ""),
                "detailed": narrative_result.get("detailed", ""),
                "confidence": narrative_confidence
            },
            "risk_notes": llm_result.get("risk_notes", ""),
            "objects": [
                {
                    "name": obj.get("name", "").replace("_", " ").title(),
                    "score": float(obj.get("score", 0))
                }
                for obj in objects
            ],
            "metadata": {
                "raw_domain": domain,
                "domain_confidence": float(round(domain_confidence, 4)),
                "raw_prediction_score": float(round(prediction_score, 4)),
                "total_labels_evaluated": len(labels),
                "inference_time_seconds": float(round(inference_time, 3)),
                "model_details": {
                    "name": model_used,
                    "mode": "open-ended" if user_text is None else "guided",
                    "labels_evaluated": labels if user_text is not None else []
                },
                "semantic_validation": {
                    "is_consistent": validation_result["is_consistent"],
                    "alignment_score": float(validation_result["alignment_score"]),
                    "verdict": validation_result["verdict"],
                    "confidence_adjustment_factor": float(validation_result["confidence_adjustment"])
                }
            }
        }
        
        logger.info(
            f"Open-ended classification complete: {prediction_label} ({confidence_score:.2%}) "
            f"using {model_used}. Detected {len(objects)} objects in {inference_time:.2f}s"
        )
        
        # Ensure all values are JSON serializable
        response = ensure_json_serializable(response)
        return response
        
    except Exception as e:
        logger.error(f"Open-ended classification error: {e}", exc_info=True)
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Full traceback:\n{error_detail}")
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "detail": "Internal server error during classification",
                "traceback": error_detail if True else None  # Set to False in production
            }
        )


@router.get("/models/status")
async def get_models_status():
    """Get status of loaded models"""
    try:
        router_instance = get_router()
        
        return {
            "status": "ready",
            "models": {
                "vit_h14": {
                    "loaded": router_instance.vith14.model is not None,
                    "device": str(router_instance.vith14.device)
                },
                "medclip": {
                    "loaded": router_instance.medclip.model is not None,
                    "device": str(router_instance.medclip.device)
                }
            },
            "default_labels": DEFAULT_LABELS
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@router.get("/domains")
async def get_supported_domains():
    """Get list of supported domains"""
    return {
        "domains": list(DEFAULT_LABELS.keys()),
        "domain_descriptions": {
            "medical": "Medical imaging (X-rays, CT, MRI scans)",
            "fashion": "Fashion and apparel images",
            "traffic": "Traffic scenes and road images",
            "satellite": "Satellite and aerial imagery",
            "industrial": "Industrial and manufacturing scenes",
            "natural": "General natural and everyday scenes"
        }
    }
