# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import time

from api.routes import router
from models.clip_model import get_vith14_model
from models.medclip_model import get_medclip_model
from models.blip_model import get_blip_model

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Zero-Shot Classification Hybrid System",
    description="Dynamic multi-domain intelligent image understanding system.",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 80)
    logger.info("⚡ Dynamic Multi-Domain Image Understanding System")
    logger.info("=" * 80)
    
    # Preload models
    start = time.time()
    try:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(get_vith14_model()._ensure_loaded),
                executor.submit(get_medclip_model()._ensure_loaded),
                executor.submit(get_blip_model()._ensure_loaded)
            ]
            for future in concurrent.futures.as_completed(futures):
                future.result()
                
        logger.info(f"✅ Models loaded successfully in {time.time()-start:.2f}s")
    except Exception as e:
        logger.error(f"Failed to preload models: {e}")

@app.get("/health")
def health():
    return {
        "status": "ok",
        "system": "Dynamic Hybrid Image Understanding API",
        "version": "3.0.0"
    }
