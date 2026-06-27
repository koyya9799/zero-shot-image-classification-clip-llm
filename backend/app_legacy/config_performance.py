# app/config_performance.py
"""
Performance Optimization Configuration
"""
import os

# GPU/CUDA Configuration
ENABLE_GPU = True  # Set to False to force CPU
USE_GPU_MEMORY_FRACTION = 0.8  # Use max 80% of GPU VRAM
ENABLE_MIXED_PRECISION = True  # Use fp16 for faster inference on GPU

# Model Loading Configuration
ENABLE_MODEL_CACHING = True  # Cache loaded models in memory
CACHE_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", ".cache")
PARALLEL_MODEL_LOADING = True  # Load models sequentially (True for async, needs refactor)

# Inference Optimization
BATCH_SIZE = 1  # Adjust for throughput vs latency
ENABLE_GRADIENT_CHECKPOINTING = False  # Save memory at cost of speed
ENABLE_INFERENCE_OPTIMIZATION = True  # Use torch optimizations

# Startup Configuration
PRELOAD_MODELS = True  # Preload all models on startup (True = eager load, False = lazy load)
LOG_MEMORY_USAGE = True  # Log GPU/CPU memory usage
LOG_LOAD_TIMES = True  # Log model loading times

# Performance Monitoring
ENABLE_PROFILING = False  # Enable detailed profiling (slower)
PROFILE_OUTPUT = "inference_profile.txt"

# Feature Flags
ENABLE_QUANTIZATION = False  # Model quantization (experimental, can reduce accuracy)
ENABLE_PRUNING = False  # Model pruning (experimental)
ENABLE_KNOWLEDGE_DISTILLATION = False  # Use smaller models (experimental)
