# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import time

from api.routes import router

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
    logger.info("Server started successfully.")
    
    # Preload models


@app.get("/health")
def health():
    return {
        "status": "ok",
        "system": "Dynamic Hybrid Image Understanding API",
        "version": "3.0.0"
    }
