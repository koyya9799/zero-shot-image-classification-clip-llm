# backend/api/routes.py
from fastapi import APIRouter, UploadFile, File, HTTPException
import logging

from utils.image_preprocessor import process_image_bytes
from services.prediction_engine import get_prediction_engine
from services.caption_generator import generate_caption
from services.explanation_generator import generate_explanation
from services.llm_auto_tuner import get_llm_auto_tuner
from schemas.response_schema import (
    ClassificationResponse,
    FeedbackRequest,
    FeedbackResponse,
    PredictionMatch,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

@router.post("/classify", response_model=ClassificationResponse)
async def classify_image(file: UploadFile = File(...)):
    """
    Classify an uploaded image across dynamic domains using a modular 
    pipeline of domain detection, classification, captioning, and explanation.
    """
    try:
        # Preprocess Image
        contents = await file.read()
        image = process_image_bytes(contents)

        # IMPROVED: First detect domain for better caption generation
        domain_detector = get_prediction_engine().domain_detector  # Get quick domain detection
        domain, domain_conf, _ = domain_detector.detect_domain(image)
        
        # Generate caption with DOMAIN CONDITIONING to prevent cross-domain confusion
        caption = generate_caption(image, domain=domain)

        # Predict Domain and Classes with full pipeline
        engine = get_prediction_engine()
        predictions, model_used, final_domain, domain_conf = engine.predict(image, top_k=3, caption=caption)

        top_pred_label = str(predictions[0]["label"]).title()
        top_pred_score = float(predictions[0]["score"])

        # Generate LLM Explanation with CLIP verification
        explanation = generate_explanation(
            domain=final_domain,
            model_used=model_used,
            prediction=top_pred_label,
            confidence=top_pred_score,
            caption=caption,
            top_matches=predictions,
            image=image
        )

        formatted_predictions = [
            PredictionMatch(label=str(p["label"]).title(), score=float(p["score"]))
            for p in predictions
        ]

        # Format and return strict JSON response
        return ClassificationResponse(
            domain=final_domain.title(),
            model_used=model_used,
            prediction=top_pred_label,
            confidence=top_pred_score,
            top_predictions=formatted_predictions,
            caption=caption,
            explanation=explanation
        )

    except Exception as e:
        logger.error(f"Error in image classification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(payload: FeedbackRequest):
    """Capture user correction to support self-learning label adaptation."""
    try:
        tuner = get_llm_auto_tuner()
        result = tuner.record_feedback(
            domain=payload.domain,
            predicted_label=payload.predicted_label,
            true_label=payload.true_label,
            caption=payload.caption,
        )

        return FeedbackResponse(
            saved=bool(result.get("saved", False)),
            message=result.get("message"),
            domain=result.get("domain"),
            true_label=result.get("true_label"),
            learned_labels=result.get("learned_labels", []),
        )
    except Exception as e:
        logger.error(f"Error in feedback submission: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
