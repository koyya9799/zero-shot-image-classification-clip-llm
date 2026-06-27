# backend/models/model_cache.py
import torch
import logging
import time
from typing import Optional, Dict, Any
from threading import Lock

logger = logging.getLogger(__name__)

# Global cache with locks for thread-safe access
_model_cache: Dict[str, Any] = {}
_cache_locks: Dict[str, Lock] = {}

# Device selection - prefer GPU if available
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

if DEVICE == "cuda":
    torch.cuda.empty_cache()
    torch.cuda.set_per_process_memory_fraction(0.8)

def log_memory_usage():
    pass

def cached_load(cache_key: str, load_fn, *args, **kwargs):
    global _model_cache, _cache_locks
    if cache_key not in _cache_locks:
        _cache_locks[cache_key] = Lock()
    
    if cache_key in _model_cache:
        return _model_cache[cache_key]
    
    with _cache_locks[cache_key]:
        if cache_key in _model_cache:
            return _model_cache[cache_key]
        
        logger.info(f"Loading {cache_key}...")
        start = time.time()
        result = load_fn(*args, **kwargs)
        _model_cache[cache_key] = result
        logger.info(f"Loaded {cache_key} in {time.time()-start:.2f}s")
        return result

class ModelLoader:
    @staticmethod
    def load_clip_model_fast(model_name: str = "ViT-L-14"):
        def _load():
            import open_clip
            try:
                model, _, preprocess = open_clip.create_model_and_transforms(
                    model_name, pretrained="openai", precision="fp16" if DEVICE == "cuda" else "fp32"
                )
            except Exception as e:
                logger.warning(f"Error loading openai weights: {e}")
                model, _, preprocess = open_clip.create_model_and_transforms(
                    model_name, pretrained="laion2b_s32b_b82k", precision="fp16" if DEVICE == "cuda" else "fp32"
                )
            tokenizer = open_clip.get_tokenizer(model_name)
            model = model.to(DEVICE)
            model.eval()
            for param in model.parameters():
                param.requires_grad = False
            return {"model": model, "preprocess": preprocess, "tokenizer": tokenizer, "device": DEVICE}
        return cached_load(f"clip_{model_name}", _load)

    @staticmethod
    def load_medclip_fast():
        def _load():
            try:
                from medclip import MedCLIPModel as MedCLIPBase, MedCLIPVisionModelViT, MedCLIPProcessor
                processor = MedCLIPProcessor()
                model = MedCLIPBase(vision_cls=MedCLIPVisionModelViT)
                
                import builtins
                original_load = torch.load
                def safe_load(*args, **kwargs):
                    if 'map_location' not in kwargs:
                        kwargs['map_location'] = 'cpu'
                    return original_load(*args, **kwargs)
                try:
                    torch.load = safe_load
                    model.from_pretrained()
                finally:
                    torch.load = original_load
                    
                model = model.to(DEVICE)
                model.eval()
                for param in model.parameters():
                    param.requires_grad = False
                return {"model": model, "processor": processor, "device": DEVICE}
            except:
                return ModelLoader.load_clip_model_fast("ViT-B-16")
        return cached_load("medclip", _load)

    @staticmethod
    def load_caption_model_fast():
        def _load():
            from transformers import BlipProcessor, BlipForConditionalGeneration
            model_name = "Salesforce/blip-image-captioning-base"
            processor = BlipProcessor.from_pretrained(model_name)
            model = BlipForConditionalGeneration.from_pretrained(
                model_name, torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32
            )
            model = model.to(DEVICE)
            model.eval()
            for param in model.parameters():
                param.requires_grad = False
            return {"model": model, "processor": processor, "device": DEVICE}
        return cached_load("blip_caption", _load)
