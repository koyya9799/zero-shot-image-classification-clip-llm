# app/models/medclip_model.py
"""
MedCLIP Model
Specialized medical image understanding
"""
import torch
import numpy as np
from PIL import Image
from typing import List, Tuple, Optional
import logging
import time

from .model_cache import ModelLoader, DEVICE, log_memory_usage

logger = logging.getLogger(__name__)

class MedCLIPModel:
    """MedCLIP model for medical image classification"""
    
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
            logger.info("⚡ Loading MedCLIP model (fast cached loading)...")
            logger.info("=" * 60)
            
            start_time = time.time()
            self._cache_data = ModelLoader.load_medclip_fast()
            load_time = time.time() - start_time
            
            logger.info(f"✓ MedCLIP ready in {load_time:.2f}s")
            logger.info("=" * 60)
            self._loaded = True
            log_memory_usage()
            
        except Exception as e:
            logger.error(f"Failed to load Medical CLIP model: {e}", exc_info=True)
            self._loaded = False
            raise
    
    @property
    def model(self):
        """Get model with lazy loading"""
        self._ensure_loaded()
        return self._cache_data["model"]
    
    @property
    def processor(self):
        """Get processor with lazy loading"""
        self._ensure_loaded()
        return self._cache_data.get("processor")
    
    @property
    def preprocess(self):
        """Get preprocess with lazy loading (for fallback)"""
        self._ensure_loaded()
        return self._cache_data.get("preprocess")
    
    @property
    def tokenizer(self):
        """Get tokenizer with lazy loading (for fallback)"""
        self._ensure_loaded()
        return self._cache_data.get("tokenizer")
    
    def encode_image(self, image: Image.Image) -> np.ndarray:
        """
        Encode medical image to embedding vector
        
        Args:
            image: PIL Image (medical image)
            
        Returns:
            Normalized embedding vector [D]
        """
        self._ensure_loaded()
        with torch.no_grad():
            if self.processor is not None:
                # Using actual MedCLIP
                inputs = self.processor(images=image, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                image_features = self.model.encode_image(**inputs)
                image_features /= image_features.norm(dim=-1, keepdim=True)
            else:
                # Using OpenCLIP fallback
                image_input = self.preprocess(image).unsqueeze(0).to(self.device)
                image_features = self.model.encode_image(image_input)
                image_features /= image_features.norm(dim=-1, keepdim=True)
        
        return image_features.cpu().numpy()[0]
    
    def encode_text(self, texts: List[str]) -> np.ndarray:
        """
        Encode medical text prompts to embedding vectors
        
        Args:
            texts: List of medical term prompts
            
        Returns:
            Normalized embedding matrix [N, D]
        """
        self._ensure_loaded()
        # Add medical context to prompts
        medical_prompts = [self._format_medical_prompt(text) for text in texts]
        
        with torch.no_grad():
            if self.processor is not None:
                # Using actual MedCLIP
                inputs = self.processor(text=medical_prompts, return_tensors="pt", padding=True)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                text_features = self.model.encode_text(**inputs)
                text_features /= text_features.norm(dim=-1, keepdim=True)
            else:
                # Using OpenCLIP fallback
                text_tokens = self.tokenizer(medical_prompts).to(self.device)
                text_features = self.model.encode_text(text_tokens)
                text_features /= text_features.norm(dim=-1, keepdim=True)
        
        return text_features.cpu().numpy()
    
    def _format_medical_prompt(self, text: str) -> str:
        """Format text as medical prompt"""
        # Check if text already contains medical context
        medical_keywords = ["xray", "x-ray", "ct", "mri", "scan", "medical", "chest", "radiograph"]
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in medical_keywords):
            return text
        
        # Add medical context
        return f"a medical x-ray showing {text}"
    
    def compute_similarity(self, image_emb: np.ndarray, text_embs: np.ndarray) -> np.ndarray:
        """
        Compute cosine similarity between image and text embeddings
        
        Args:
            image_emb: Image embedding [D]
            text_embs: Text embeddings [N, D]
            
        Returns:
            Similarity scores [N]
        """
        similarities = text_embs @ image_emb
        return similarities
    
    def classify(
        self, 
        image: Image.Image, 
        labels: List[str], 
        top_k: int = 5
    ) -> Tuple[List[dict], np.ndarray]:
        """
        Classify medical image with given labels
        
        Args:
            image: PIL Image (medical image)
            labels: List of medical condition labels
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
_medclip_model = None

def get_medclip_model() -> MedCLIPModel:
    """Get or create global MedCLIP model instance"""
    global _medclip_model
    if _medclip_model is None:
        _medclip_model = MedCLIPModel()
    return _medclip_model
