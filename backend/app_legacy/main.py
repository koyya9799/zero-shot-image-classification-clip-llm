# app/main.py
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from PIL import Image
import io
import logging
import numpy as np
import json
import time

from .clip_service import (
    classify_image,
    create_class_prototype,
    list_classes,
    encode_image,
    compute_text_similarity,
    CLASS_PROTOTYPES,
)
from .caption_service import generate_caption
from .domain_service import infer_domain_from_hint, infer_domain
from .llm_service import llm_reason_and_label, llm_narrative, extract_objects, extract_domain_and_classes
from .evaluation_service import evaluate_dataset
from .config_performance import PRELOAD_MODELS, PARALLEL_MODEL_LOADING
from .models.router import get_router
from .models.model_cache import log_memory_usage

# Import hybrid classification routes
from .routes.classify import router as classify_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Custom JSON encoder to handle numpy types
class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles numpy data types"""
    def default(self, obj):
        if isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


app = FastAPI(
    title="Zero-Shot Classification with ViT-H/14",
    description="High-accuracy zero-shot image classification using ViT-H/14 CLIP model",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include hybrid classification routes (disabled as we use the unified /api/classify)
# app.include_router(classify_router)


@app.on_event("startup")
async def startup_event():
    """Server startup event"""
    logger.info("=" * 80)
    logger.info("⚡ Zero-Shot Classification System (ViT-L-14 OpenAI)")
    logger.info("=" * 80)
    logger.info("Model: OpenCLIP ViT-L-14 (768-dim, OpenAI pretrained, high-accuracy)")
    
    if PRELOAD_MODELS:
        logger.info("Status: Preloading models on startup...")
        
        try:
            # Preload all models
            start_time = time.time()
            
            if PARALLEL_MODEL_LOADING:
                logger.info("\n📦 Loading models in parallel...")
                import concurrent.futures
                from .models.clip_vith14 import get_vith14_model
                from .models.medclip_model import get_medclip_model
                from .caption_service import _load_caption_model
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    futures = [
                        executor.submit(get_vith14_model()._ensure_loaded),
                        executor.submit(get_medclip_model()._ensure_loaded),
                        executor.submit(_load_caption_model)
                    ]
                    for future in concurrent.futures.as_completed(futures):
                        future.result()
                        
                router = get_router()
                router._ensure_loaded()
            else:
                logger.info("\n📦 Loading ViT-H/14 and MedCLIP models sequentially...")
                router = get_router()
                router._ensure_loaded()
                
                logger.info("📦 Loading BLIP caption model...")
                _ = generate_caption(Image.new('RGB', (224, 224)))
            
            load_time = time.time() - start_time
            log_memory_usage()
            
            logger.info(f"\n✅ All models loaded successfully in {load_time:.2f}s")
            logger.info("Status: Ready (all models in memory)")
            logger.info("First classification: < 2 seconds (models cached)")
            logger.info("Subsequent classifications: < 2 seconds (cached)")
            
        except Exception as e:
            logger.error(f"Failed to preload models: {e}", exc_info=True)
            logger.warning("System will use lazy loading fallback")
    else:
        logger.info("Status: Lazy loading - models load on first request")
        logger.info("First classification: 1-2 minutes (model loading)")
        logger.info("Subsequent classifications: < 2 seconds (cached)")
    
    logger.info("=" * 80)
    logger.info("✓ Server ready for inference")
    logger.info("=" * 80)


@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "system": "Hybrid ViT-H/14 + MedCLIP",
        "version": "2.0.0"
    }


@app.get("/api/classes")
def api_classes():
    return {"classes": list_classes()}


@app.post("/api/init-default-classes")
def api_init_default_classes(domain: str = Form(default="animal")):
    """Initialize default classes for a given domain."""
    try:
        default_classes = {
            "medical": [
                "chest x-ray", "ct scan", "mri", "ultrasound",
                "normal chest x-ray", "pneumonia", "radiology image"
            ],
            "industry": [
                "factory", "machinery", "assembly line", "warehouse", 
                "industrial equipment", "manufacturing plant"
            ],
            "vegetable": [
                "carrot", "broccoli", "tomato", "potato", 
                "leafy green", "root vegetable"
            ],
            "animal": [
                "dog", "cat", "bird", "wildlife", 
                "mammal", "reptile"
            ]
        }
        
        classes = default_classes.get(domain, default_classes["animal"])
        
        # Clear existing classes
        CLASS_PROTOTYPES.clear()
        
        # Create prototypes for each class
        for label in classes:
            create_class_prototype(label=label, domain=domain, images=None)
        
        return {
            "status": "ok",
            "message": f"Initialized {len(classes)} {domain} classes",
            "classes": classes
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/add-class")
async def api_add_class(
    label: str = Form(...),
    domain: Optional[str] = Form(default="natural"),
    files: Optional[List[UploadFile]] = File(default=None),
):
    try:
        label = label.strip()
        if not label:
            return JSONResponse(status_code=400, content={"error": "Label must not be empty."})

        pil_images: List[Image.Image] = []
        if files:
            for f in files:
                data = await f.read()
                img = Image.open(io.BytesIO(data)).convert("RGB")
                pil_images.append(img)

        info = create_class_prototype(
            label=label,
            domain=domain or "natural",
            images=pil_images if pil_images else None,
        )

        return {
            "status": "ok",
            "label": label,
            "domain": domain,
            "num_images_used": info["num_images"],
            "embedding_norm": info["norm"],
            "message": f"class '{label}' added/updated successfully",
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/classify")
async def api_classify(
    file: UploadFile = File(...),
):
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # 1) Generate caption first
        caption = generate_caption(img)
        
        # 2) Dynamically extract possible candidate classes from caption to feed into CLIP
        llm_metadata = extract_domain_and_classes(caption)
        classes = llm_metadata.get("classes", ["object", "background feature"])
        
        # 3) Let the router estimate the domain visually
        domain_router = get_router()
        model_used, visual_domain, confidence, _ = domain_router.route(img)
        
        # 4) Setup dynamically generated classes for CLIP
        CLASS_PROTOTYPES.clear()
        for label in classes:
            create_class_prototype(label=str(label), domain=visual_domain, images=None)
            
        # 5) Perform pure visual classification First
        classification_result = domain_router.classify_with_routing(
            image=img,
            labels=classes,
            top_k=3
        )
        
        predictions = classification_result["predictions"]
        model_used = classification_result["model_used"]  # May have dynamically switched
        top_prediction = predictions[0]
        prediction_label = str(top_prediction["label"]).title()
        
        # 6) LLM determines accurate explanations and final Domain name based on objects detected
        reasoning = llm_reason_and_label(
            caption=caption,
            candidates=predictions,
            user_hint="",
            domain=visual_domain,
        )
        
        # 7) Try to grab domain from reasoning if it generated one, fallback to the initial LLM guess
        final_domain = reasoning.get("domain", llm_metadata.get("domain", "General Objects"))
        final_domain_clean = str(final_domain).title()
        if "Medical" in final_domain_clean and "Image" not in final_domain_clean:
            final_domain_clean += " Images"
            
        # 8) Construct JSON Output exactly as requested
        return {
            "domain": final_domain_clean,
            "model_used": model_used,
            "prediction": prediction_label,
            "confidence": float(round(top_prediction["score"], 2)),
            "top_predictions": [
                {
                    "label": str(pred["label"]).title(),
                    "score": float(round(pred["score"], 2))
                }
                for pred in predictions[:3]
            ],
            "caption": caption,
            "explanation": reasoning.get("reason", f"The image features characteristic properties of a {prediction_label.lower()}.")
        }

    except Exception as e:
        logger.error(f"Classification error: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/evaluate")
async def api_evaluate(
    files: List[UploadFile] = File(...),
    labels: List[str] = Form(...),
):
    """
    Evaluate the model on a test dataset.
    
    Expects:
    - files: List of image files
    - labels: Corresponding ground truth labels (comma-separated or list)
    
    Returns comprehensive metrics including accuracy, precision, recall, F1, mAP, etc.
    """
    try:
        # Parse labels if they come as a single comma-separated string
        if len(labels) == 1 and ',' in labels[0]:
            labels = [l.strip() for l in labels[0].split(',')]
        
        if len(files) != len(labels):
            return JSONResponse(
                status_code=400, 
                content={"error": f"Number of files ({len(files)}) must match number of labels ({len(labels)})"}
            )
        
        # Read all files
        file_data = []
        for f in files:
            contents = await f.read()
            file_data.append((contents, f.filename or "unknown"))
        
        # Evaluate
        metrics = await evaluate_dataset(file_data, labels)
        
        return {
            "status": "ok",
            "metrics": metrics
        }
        
    except ValueError as ve:
        return JSONResponse(status_code=400, content={"error": str(ve)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
