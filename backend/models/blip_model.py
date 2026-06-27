# backend/models/blip_model.py
import torch
from .model_cache import ModelLoader, DEVICE

class BlipModel:
    def __init__(self):
        self._loaded = False
        self._cache_data = None

    def _ensure_loaded(self):
        if self._loaded and self._cache_data:
            return
        self._cache_data = ModelLoader.load_caption_model_fast()
        self._loaded = True

    @property
    def model(self):
        self._ensure_loaded()
        return self._cache_data["model"]

    @property
    def processor(self):
        self._ensure_loaded()
        return self._cache_data["processor"]

_blip_model = None
def get_blip_model() -> BlipModel:
    global _blip_model
    if _blip_model is None:
        _blip_model = BlipModel()
    return _blip_model
