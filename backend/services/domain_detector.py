# backend/services/domain_detector.py
import numpy as np
from PIL import Image
from typing import Tuple, Dict, Optional
import logging
import json
import time
import re

from config import DOMAINS, DOMAIN_PROMPTS
from models.clip_model import get_vith14_model
from models.llm_model import get_llm_model

logger = logging.getLogger(__name__)

class DomainDetector:
    def __init__(self):
        self.clip = get_vith14_model()
        self.llm = get_llm_model()
        self._llm_retry_after_ts = 0.0
        self._llm_cooldown_seconds = 300

    @staticmethod
    def _is_quota_or_rate_limit_error(error: Exception) -> bool:
        message = str(error).lower()
        code = getattr(error, "code", None)
        return (
            code == 429
            or "429" in message
            or "resource_exhausted" in message
            or "rate limit" in message
            or "quota" in message
        )

    def _get_llm_domain_prediction(self, image: Image.Image) -> Optional[Tuple[str, float]]:
        """
        Use LLM with vision to predict domain.
        Returns: (predicted_domain, confidence) or None if LLM not available
        """
        try:
            if not self.llm.is_available():
                return None

            now = time.time()
            if now < self._llm_retry_after_ts:
                return None
            
            # Create prompt for domain detection
            domain_list = ", ".join(DOMAINS)
            prompt = f"""Analyze this image and determine which domain it belongs to.

Available domains: {domain_list}

Provide your answer in JSON format with exactly this structure:
{{
    "domain": "the most appropriate domain from the list",
    "confidence": 0.85,
    "reasoning": "brief explanation of why this domain was chosen"
}}

Be precise and choose only from the available domains."""

            # Parse JSON response with robust handling
            result_text = self.llm.generate_vision(
                prompt=prompt,
                image=image,
                temperature=0.2,
                max_tokens=200,
            ).strip()
            
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(1)
            elif result_text.startswith("```"):
                # Fallback: remove code block markers manually
                parts = result_text.split("```")
                if len(parts) >= 2:
                    result_text = parts[1]
                    if result_text.startswith("json"):
                        result_text = result_text[4:]
                result_text = result_text.strip()
            
            # Extract JSON if wrapped in extra text
            if not result_text.startswith("{"):
                brace_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if brace_match:
                    result_text = brace_match.group(0)
            
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError as je:
                logger.warning(f"Failed to parse LLM JSON response. Error: {je}. Raw response: {result_text[:200]}")
                return None
            
            predicted_domain = result.get("domain", "").lower()
            llm_confidence = float(result.get("confidence", 0.5))
            reasoning = result.get("reasoning", "")
            
            # Validate predicted domain
            if predicted_domain in DOMAIN_PROMPTS:
                logger.info(f"LLM domain prediction: {predicted_domain} (confidence: {llm_confidence:.3f}) - {reasoning}")
                return predicted_domain, llm_confidence
            else:
                logger.warning(f"LLM predicted invalid domain: {predicted_domain}")
                return None
                
        except Exception as e:
            if self._is_quota_or_rate_limit_error(e):
                self._llm_retry_after_ts = time.time() + self._llm_cooldown_seconds
                logger.warning(
                    "LLM domain prediction rate-limited/quota-exhausted. "
                    "Using CLIP-only detection for %.0f seconds.",
                    self._llm_cooldown_seconds,
                )
                return None

            logger.warning(f"LLM domain prediction failed: {e}")
            return None

    def detect_domain(self, image: Image.Image) -> Tuple[str, float, Dict[str, float]]:
        """
        Dynamically detects the domain of the image using both CLIP and LLM.
        Combines both predictions for better accuracy.
        Returns: (best_domain, confidence_score, all_domain_scores)
        """
        # === CLIP-based Detection ===
        image_emb = self.clip.encode_image(image)
        
        # Prepare configured domains
        domain_labels = list(DOMAIN_PROMPTS.keys())
        domain_texts = [DOMAIN_PROMPTS[d] for d in domain_labels]
        
        # Encode domains
        text_embs = self.clip.encode_text(domain_texts)
        
        # Compute similarity
        clip_similarities = self.clip.compute_similarity(image_emb, text_embs)
        
        # Normalize CLIP scores
        clip_scores = {
            domain_labels[i]: float(clip_similarities[i])
            for i in range(len(domain_labels))
        }
        
        # === LLM-based Detection ===
        llm_prediction = self._get_llm_domain_prediction(image)
        
        # === Combine Predictions ===
        if llm_prediction:
            llm_domain, llm_confidence = llm_prediction
            
            # Hybrid scoring: weighted combination
            # CLIP: 40%, LLM: 60% (LLM has better semantic understanding)
            combined_scores = {}
            for domain in domain_labels:
                clip_score = clip_scores[domain]
                # Boost LLM's predicted domain, dampen others
                llm_boost = llm_confidence if domain == llm_domain else (1 - llm_confidence) / (len(domain_labels) - 1)
                combined_scores[domain] = 0.4 * clip_score + 0.6 * llm_boost
            
            # Get best combined domain
            best_domain = max(combined_scores, key=combined_scores.get)
            confidence = combined_scores[best_domain]
            
            logger.info(f"Hybrid domain detection: {best_domain} (confidence: {confidence:.3f}, CLIP: {clip_scores[best_domain]:.3f}, LLM: {llm_domain})")
            return best_domain, confidence, combined_scores
        else:
            # Fallback to CLIP-only if LLM fails
            top_idx = np.argmax(clip_similarities)
            best_domain = domain_labels[top_idx]
            confidence = float(clip_similarities[top_idx])
            
            logger.info(f"CLIP-only domain detection: {best_domain} (confidence: {confidence:.3f})")
            return best_domain, confidence, clip_scores

_detector = None
def get_domain_detector() -> DomainDetector:
    global _detector
    if _detector is None:
        _detector = DomainDetector()
    return _detector
