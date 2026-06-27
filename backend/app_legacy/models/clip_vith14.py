# app/models/clip_vith14.py
"""
OpenCLIP ViT-H/14 Model
Universal zero-shot image understanding
"""
import torch
import open_clip
from PIL import Image
from typing import List, Tuple
import numpy as np
import logging
import time

from .model_cache import ModelLoader, DEVICE, log_memory_usage

logger = logging.getLogger(__name__)

class ViTH14Model:
    """ViT-H/14 model for universal image classification"""
    
    def __init__(self):
        self.device = DEVICE
        self._loaded = False
        self._cache_data = None
    
    def _ensure_loaded(self):
        """Lazy load model on first use with intelligent caching"""
        if self._loaded and self._cache_data:
            return
        
        try:
            logger.info("=" * 60)
            logger.info("⚡ Loading ViT-L-14 model (openai weights, fast cached)...")
            logger.info("=" * 60)
            
            # Use fast loader with caching
            start_time = time.time()
            self._cache_data = ModelLoader.load_clip_model_fast("ViT-L-14")
            load_time = time.time() - start_time
            
            logger.info(f"✓ ViT-L-14 ready in {load_time:.2f}s")
            logger.info("=" * 60)
            self._loaded = True
            log_memory_usage()
            
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}", exc_info=True)
            self._loaded = False
            raise
    
    @property
    def model(self):
        """Get model with lazy loading"""
        self._ensure_loaded()
        return self._cache_data["model"]
    
    @property
    def preprocess(self):
        """Get preprocessor with lazy loading"""
        self._ensure_loaded()
        return self._cache_data["preprocess"]
    
    @property
    def tokenizer(self):
        """Get tokenizer with lazy loading"""
        self._ensure_loaded()
        return self._cache_data["tokenizer"]
    
    def encode_image(self, image: Image.Image) -> np.ndarray:
        """
        Encode image to embedding vector
        
        Args:
            image: PIL Image
            
        Returns:
            Normalized embedding vector [D]
        """
        self._ensure_loaded()
        with torch.no_grad():
            image_input = self.preprocess(image).unsqueeze(0).to(self.device)
            image_features = self.model.encode_image(image_input)
            image_features /= image_features.norm(dim=-1, keepdim=True)
        return image_features.cpu().numpy()[0]
    
    def encode_text(self, texts: List[str]) -> np.ndarray:
        """
        Encode text prompts to embedding vectors
        
        Args:
            texts: List of text prompts
            
        Returns:
            Normalized embedding matrix [N, D]
        """
        self._ensure_loaded()
        with torch.no_grad():
            text_tokens = self.tokenizer(texts).to(self.device)
            text_features = self.model.encode_text(text_tokens)
            text_features /= text_features.norm(dim=-1, keepdim=True)
        return text_features.cpu().numpy()
    
    def compute_similarity(self, image_emb: np.ndarray, text_embs: np.ndarray) -> np.ndarray:
        """
        Compute cosine similarity between image and text embeddings
        
        Args:
            image_emb: Image embedding [D]
            text_embs: Text embeddings [N, D]
            
        Returns:
            Similarity scores [N]
        """
        # Both are already normalized, so dot product = cosine similarity
        similarities = text_embs @ image_emb
        return similarities
    
    def classify(
        self, 
        image: Image.Image, 
        labels: List[str], 
        top_k: int = 5
    ) -> Tuple[List[dict], np.ndarray]:
        """
        Classify image with given labels
        
        Args:
            image: PIL Image
            labels: List of class labels
            top_k: Number of top predictions to return
            
        Returns:
            Tuple of (top predictions, image embedding)
        """
        # Encode image
        image_emb = self.encode_image(image)
        
        # Encode labels
        text_embs = self.encode_text(labels)
        
        # Compute similarities
        similarities = self.compute_similarity(image_emb, text_embs)
        
        # Get top-k predictions
        top_indices = np.argsort(-similarities)[:top_k]
        
        predictions = [
            {
                "label": labels[idx],
                "score": float(similarities[idx])
            }
            for idx in top_indices
        ]
        
        return predictions, image_emb


# Global instance
_vith14_model = None

def get_vith14_model() -> ViTH14Model:
    """Get or create global ViT-H/14 model instance"""
    global _vith14_model
    if _vith14_model is None:
        _vith14_model = ViTH14Model()
    return _vith14_model
