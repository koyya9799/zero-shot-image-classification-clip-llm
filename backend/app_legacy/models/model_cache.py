# app/models/model_cache.py
"""
Model Cache Manager
Fast model loading with intelligent caching and memory optimization
"""
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

# Enable memory optimization
if DEVICE == "cuda":
    torch.cuda.empty_cache()
    torch.cuda.set_per_process_memory_fraction(0.8)  # Use max 80% GPU memory


def get_device():
    """Get computation device (cuda or cpu)"""
    return DEVICE


def clear_gpu_cache():
    """Clear GPU cache to free memory"""
    if DEVICE == "cuda":
        torch.cuda.empty_cache()
        logger.info("GPU cache cleared")


def log_memory_usage():
    """Log current memory usage"""
    try:
        if DEVICE == "cuda":
            allocated = torch.cuda.memory_allocated() / 1024 / 1024 / 1024
            reserved = torch.cuda.memory_reserved() / 1024 / 1024 / 1024
            logger.info(f"GPU Memory - Allocated: {allocated:.2f}GB, Reserved: {reserved:.2f}GB")
        else:
            try:
                import psutil
                process = psutil.Process()
                mem_info = process.memory_info()
                rss_gb = mem_info.rss / 1024 / 1024 / 1024
                logger.info(f"CPU Memory - Used: {rss_gb:.2f}GB")
            except ImportError:
                logger.debug("psutil not available for memory logging")
    except Exception as e:
        logger.debug(f"Memory logging failed: {e}")


def cached_load(cache_key: str, load_fn, *args, **kwargs):
    """
    Load and cache a model/resource
    
    Args:
        cache_key: Unique identifier for the cached item
        load_fn: Function that loads the model
        *args, **kwargs: Arguments to pass to load_fn
        
    Returns:
        Loaded and cached model/resource
    """
    global _model_cache, _cache_locks
    
    # Create lock for this key if it doesn't exist
    if cache_key not in _cache_locks:
        _cache_locks[cache_key] = Lock()
    
    # Check cache first (fast path)
    if cache_key in _model_cache:
        logger.debug(f"✓ Cache hit for {cache_key}")
        return _model_cache[cache_key]
    
    # Lock and load (slow path)
    with _cache_locks[cache_key]:
        # Double-check after acquiring lock
        if cache_key in _model_cache:
            return _model_cache[cache_key]
        
        logger.info(f"Loading {cache_key}...")
        start_time = time.time()
        
        try:
            result = load_fn(*args, **kwargs)
            load_time = time.time() - start_time
            
            # Cache the result
            _model_cache[cache_key] = result
            
            logger.info(f"✓ {cache_key} loaded in {load_time:.2f}s")
            log_memory_usage()
            
            return result
        except Exception as e:
            logger.error(f"Failed to load {cache_key}: {e}", exc_info=True)
            raise


def get_cached_model(cache_key: str) -> Optional[Any]:
    """Get cached model if it exists"""
    return _model_cache.get(cache_key)


def clear_cache(cache_key: Optional[str] = None):
    """Clear cache entry or entire cache"""
    global _model_cache
    
    if cache_key is None:
        _model_cache.clear()
        logger.info("✓ All models cleared from cache")
    else:
        if cache_key in _model_cache:
            del _model_cache[cache_key]
            logger.info(f"✓ {cache_key} cleared from cache")
        clear_gpu_cache()


def cache_stats():
    """Get cache statistics"""
    return {
        "cached_models": list(_model_cache.keys()),
        "cache_size": len(_model_cache),
        "device": DEVICE,
    }


# Model-specific cache utilities

class ModelLoader:
    """Utility class for fast model loading"""
    
    @staticmethod
    def load_clip_model_fast(model_name: str = "ViT-L-14"):
        """Load CLIP model with optimization - uses best available pretrained weights"""
        def _load():
            import open_clip
            logger.info(f"Creating {model_name}...")
            
            # Try to load with openai pretrained weights (best quality)
            try:
                model, _, preprocess = open_clip.create_model_and_transforms(
                    model_name,
                    pretrained="openai",
                    precision="fp16" if DEVICE == "cuda" else "fp32"
                )
            except (RuntimeError, ValueError):
                # Fallback to laion2b if openai not available
                logger.warning(f"OpenAI weights not available for {model_name}, using laion2b...")
                model, _, preprocess = open_clip.create_model_and_transforms(
                    model_name,
                    pretrained="laion2b_s32b_b79k",
                    precision="fp16" if DEVICE == "cuda" else "fp32"
                )
            
            tokenizer = open_clip.get_tokenizer(model_name)
            model = model.to(DEVICE)
            model.eval()
            
            # Disable gradients for inference
            for param in model.parameters():
                param.requires_grad = False
            
            return {
                "model": model,
                "preprocess": preprocess,
                "tokenizer": tokenizer,
                "device": DEVICE
            }
        
        return cached_load(f"clip_{model_name}", _load)
    
    @staticmethod
    def load_medclip_fast():
        """Load MedCLIP model with optimization"""
        def _load():
            try:
                from medclip import MedCLIPModel as MedCLIPBase, MedCLIPVisionModelViT
                from medclip import MedCLIPProcessor
                
                logger.info("Creating MedCLIP...")
                processor = MedCLIPProcessor()
                model = MedCLIPBase(vision_cls=MedCLIPVisionModelViT)
                
                # Patch torch.load temporarily to fix MedCLIP serialization issue on CPU
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
                
                # Disable gradients for inference
                for param in model.parameters():
                    param.requires_grad = False
                
                return {
                    "model": model,
                    "processor": processor,
                    "device": DEVICE
                }
            except ImportError:
                # Fallback to lightweight model
                logger.warning("MedCLIP not available, using CLIP ViT-B-16 fallback")
                return ModelLoader.load_clip_model_fast("ViT-B-16")
            except Exception as e:
                # Fallback on any exception (like download failure, CUDA errors, etc)
                logger.warning(f"Failed to load MedCLIP ({e}), using CLIP ViT-B-16 fallback")
                return ModelLoader.load_clip_model_fast("ViT-B-16")
        
        return cached_load("medclip", _load)
    
    @staticmethod
    def load_caption_model_fast():
        """Load BLIP caption model with optimization"""
        def _load():
            from transformers import BlipProcessor, BlipForConditionalGeneration
            
            logger.info("Creating BLIP caption model...")
            model_name = "Salesforce/blip-image-captioning-base"
            processor = BlipProcessor.from_pretrained(model_name)
            model = BlipForConditionalGeneration.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32
            )
            model = model.to(DEVICE)
            model.eval()
            
            # Disable gradients for inference
            for param in model.parameters():
                param.requires_grad = False
            
            return {
                "model": model,
                "processor": processor,
                "device": DEVICE
            }
        
        return cached_load("blip_caption", _load)
