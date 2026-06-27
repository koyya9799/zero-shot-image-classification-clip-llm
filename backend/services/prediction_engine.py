# backend/services/prediction_engine.py
import logging
from typing import List, Dict, Tuple
from PIL import Image

from config import (
    MEDICAL_THRESHOLD,
    BASE_CLASSES,
    BASE_PROMPT_TEMPLATES,
    DOMAIN_PROMPT_TEMPLATES,
    EXACT_LABEL_PROMPTS,
    KEYWORD_LABEL_PROMPTS,
)
from services.domain_detector import get_domain_detector
from services.llm_auto_tuner import get_llm_auto_tuner
from models.clip_model import get_vith14_model
from models.medclip_model import get_medclip_model
from models.llm_model import get_llm_model
import json
import re

logger = logging.getLogger(__name__)

class PredictionEngine:
    def __init__(self):
        self.domain_detector = get_domain_detector()
        self.auto_tuner = get_llm_auto_tuner()
        self.clip = get_vith14_model()
        self.medclip = get_medclip_model()
        self.llm = get_llm_model()
        self._llm_retry_after_ts = 0.0
        self._llm_cooldown_seconds = 300

    def _get_llm_prediction_validation(self, image: Image.Image, top_predictions: List[Dict], caption: str, domain: str) -> Dict[str, float]:
        """Use LLM vision to validate and boost CLIP predictions for higher confidence"""
        import time
        now = time.time()
        if now < self._llm_retry_after_ts or not self.llm.is_available():
            return {}
        
        try:
            # Get top candidate labels
            candidates = [p['label'] for p in top_predictions[:5]]
            candidates_str = ", ".join(candidates)
            
            prompt = f"""You are validating an image classification system's predictions.

Image Caption: "{caption}"
Domain: {domain}
Candidate Classifications: {candidates_str}

For each candidate, assess how well it matches the visual evidence in the image.
Provide confidence adjustments as JSON:

{{
    "label1": 0.15,  // boost by 0.15 if very confident match
    "label2": -0.10, // reduce by 0.10 if poor match
    "label3": 0.0    // no change if uncertain
}}

Only adjust by -0.20 to +0.20. Base on visual features you can see."""

            result_text = self.llm.generate_vision(
                prompt=prompt,
                image=image,
                temperature=0.2,
                max_tokens=150,
            ).strip()
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(0)
            
            boosts = json.loads(result_text)
            logger.info(f"LLM validation boosts: {boosts}")
            return {k.lower(): float(v) for k, v in boosts.items()}
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                self._llm_retry_after_ts = time.time() + self._llm_cooldown_seconds
                logger.warning("LLM prediction validation rate-limited")
            else:
                logger.warning(f"LLM prediction validation failed: {e}")
            return {}

    def get_dynamic_labels_for_domain(self, domain: str) -> List[str]:
        # Base labels are centrally configured in backend/config.py
        return BASE_CLASSES.get(domain, ["object", "natural scene", "item"])

    def _dedupe_prompts(self, prompts: List[str]) -> List[str]:
        seen = set()
        cleaned: List[str] = []
        for prompt in prompts:
            text = str(prompt).strip()
            if not text:
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(text)
        return cleaned

    def _build_prompt_ensembles(self, labels: List[str], domain: str) -> Dict[str, List[str]]:
        """Build strong CLIP prompt ensembles for each label in a domain-aware way."""
        domain = (domain or "").strip().lower()
        ensembles: Dict[str, List[str]] = {}
        domain_templates = DOMAIN_PROMPT_TEMPLATES.get(domain, [])
        exact_rules = EXACT_LABEL_PROMPTS.get(domain, {})
        keyword_rules = KEYWORD_LABEL_PROMPTS.get(domain, {})

        for label in labels:
            label_text = str(label).strip().lower()
            if not label_text:
                continue

            prompts = [template.format(label=label_text) for template in BASE_PROMPT_TEMPLATES]
            prompts.extend(template.format(label=label_text) for template in domain_templates)

            prompts.extend(exact_rules.get(label_text, []))

            for keyword, keyword_prompts in keyword_rules.items():
                if keyword in label_text:
                    prompts.extend(keyword_prompts)

            ensembles[label_text] = self._dedupe_prompts(prompts)

        return ensembles

    def _fuse_predictions(
        self,
        med_predictions: List[Dict],
        clip_predictions: List[Dict],
        top_k: int,
        med_weight: float = 0.6,
        clip_weight: float = 0.4,
    ) -> List[Dict]:
        """Fuse two probability distributions by weighted averaging on shared labels."""
        med_map = {str(p.get("label", "")).lower(): float(p.get("score", 0.0)) for p in med_predictions}
        clip_map = {str(p.get("label", "")).lower(): float(p.get("score", 0.0)) for p in clip_predictions}
        labels = sorted(set(med_map.keys()) | set(clip_map.keys()))

        fused: List[Dict] = []
        for label in labels:
            score = (med_weight * med_map.get(label, 0.0)) + (clip_weight * clip_map.get(label, 0.0))
            fused.append({"label": label, "score": float(score)})

        total = sum(item["score"] for item in fused) or 1.0
        for item in fused:
            item["score"] = float(item["score"] / total)

        fused.sort(key=lambda item: item["score"], reverse=True)
        return fused[:top_k]

    def _classify_with_optional_fusion(
        self,
        image: Image.Image,
        labels: List[str],
        top_k: int,
        custom_ensembles: Dict[str, List[str]],
        use_medical_fusion: bool,
    ) -> List[Dict]:
        if use_medical_fusion:
            full_k = max(len(labels), top_k)
            med_preds, _ = self.medclip.classify(image, labels, top_k=full_k, custom_ensembles=custom_ensembles)
            clip_preds, _ = self.clip.classify(image, labels, top_k=full_k, custom_ensembles=custom_ensembles)
            return self._fuse_predictions(med_preds, clip_preds, top_k=top_k, med_weight=0.6, clip_weight=0.4)

        preds, _ = self.clip.classify(image, labels, top_k=top_k, custom_ensembles=custom_ensembles)
        return preds

    def _merge_labels(self, domain: str) -> List[str]:
        base_labels = self.get_dynamic_labels_for_domain(domain)
        learned_labels = self.auto_tuner.get_learned_labels(domain)
        merged = []
        for label in base_labels + learned_labels:
            key = str(label).strip().lower()
            if key and key not in merged:
                merged.append(key)
        return merged

    def _apply_self_learning_boosts(self, predictions: List[Dict], domain: str) -> List[Dict]:
        if not predictions:
            return predictions

        top_label = str(predictions[0].get("label", "")).lower()
        boosted = []
        max_boost = 0.0
        for pred in predictions:
            label = str(pred.get("label", "")).lower()
            score = float(pred.get("score", 0.0))
            boost = self.auto_tuner.get_correction_boost(domain, top_label, label)
            max_boost = max(max_boost, boost)
            boosted.append({"label": label, "score": score + boost})

        # Normalize more conservatively to preserve confidence gains
        if max_boost > 0:
            # Apply softer normalization when boosts are present
            total = sum(p["score"] for p in boosted)
            if total > 1.0:
                # Only normalize if sum exceeds 1.0
                for pred in boosted:
                    pred["score"] = float(pred["score"] / total)
        else:
            # Standard normalization when no boosts
            total = sum(p["score"] for p in boosted) or 1.0
            for pred in boosted:
                pred["score"] = float(pred["score"] / total)

        boosted.sort(key=lambda item: item["score"], reverse=True)
        return boosted

    def predict(
        self,
        image: Image.Image,
        top_k: int = 3,
        force_domain: str = None,
        caption: str = "",
    ) -> Tuple[List[Dict], str, str, float]:
        """
        Detects domain and runs classification.
        Returns: (predictions, model_used, domain, domain_confidence)
        """
        # 1. Detect Domain
        if force_domain:
            domain = self.auto_tuner.normalize_domain(force_domain)
            domain_conf = 1.0
            all_scores = {domain: 1.0}
        else:
            domain, domain_conf, all_scores = self.domain_detector.detect_domain(image)
            domain = self.auto_tuner.normalize_domain(domain)

        # 2. Select Model based on exact configured logic
        medical_score = all_scores.get("medical", all_scores.get("medical image", 0.0))
        
        use_medical_fusion = domain == "medical" and medical_score >= MEDICAL_THRESHOLD
        if use_medical_fusion:
            model_name = "MedCLIP+ViT-H/14 (fusion)"
            logger.info(
                "Routing to medical fusion (MedCLIP 0.6 + ViT-H/14 0.4) for %s (score: %.3f)",
                domain,
                medical_score,
            )
        else:
            model_name = "ViT-H/14"
            logger.info(f"Routing to {model_name} for {domain} (score: {domain_conf:.3f})")

        # 3. Get labels dynamically
        labels = self._merge_labels(domain)

        # 4. Classify using strong prompt ensembles for every label.
        custom_ensembles = self._build_prompt_ensembles(labels, domain)
        if use_medical_fusion:
            predictions = self._classify_with_optional_fusion(
                image=image,
                labels=labels,
                top_k=top_k,
                custom_ensembles=custom_ensembles,
                use_medical_fusion=True,
            )
        else:
            predictions, _ = self.clip.classify(image, labels, top_k=top_k, custom_ensembles=custom_ensembles)
        
        # 5. Confidence Filtering Fallback
        if predictions and predictions[0]['score'] < 0.55:
            logger.info(f"Confidence {predictions[0]['score']:.2f} < 0.55. Applying fallback logic with expanded prompts.")
            
            top_candidate_labels = [p['label'] for p in predictions[:3]]
            custom_ensembles = self._build_prompt_ensembles(top_candidate_labels, domain)

            llm_ensembles = self.auto_tuner.build_llm_prompt_ensembles(
                domain=domain,
                caption=caption,
                candidate_labels=top_candidate_labels,
            )
            for label, llm_prompts in llm_ensembles.items():
                key = str(label).strip().lower()
                base_prompts = custom_ensembles.get(key, [])
                custom_ensembles[key] = self._dedupe_prompts(base_prompts + list(llm_prompts))

            if use_medical_fusion:
                fallback_predictions = self._classify_with_optional_fusion(
                    image=image,
                    labels=top_candidate_labels,
                    top_k=top_k,
                    custom_ensembles=custom_ensembles,
                    use_medical_fusion=True,
                )
            else:
                fallback_predictions, _ = self.clip.classify(
                    image,
                    top_candidate_labels,
                    top_k=top_k,
                    custom_ensembles=custom_ensembles,
                )
            logger.info(f"Fallback improved score to {fallback_predictions[0]['score']:.2f} for {fallback_predictions[0]['label']}")
            predictions = fallback_predictions

        # 5.5 Apply LLM visual validation for extra confidence
        if predictions and caption:
            llm_boosts = self._get_llm_prediction_validation(image, predictions, caption, domain)
            if llm_boosts:
                for pred in predictions:
                    label = pred['label'].lower()
                    if label in llm_boosts:
                        old_score = pred['score']
                        pred['score'] = max(0.0, min(1.0, pred['score'] + llm_boosts[label]))
                        logger.info(f"LLM adjusted {label}: {old_score:.3f} -> {pred['score']:.3f}")
                
                # Re-sort and normalize
                predictions.sort(key=lambda x: x['score'], reverse=True)
                total = sum(p['score'] for p in predictions) or 1.0
                for pred in predictions:
                    pred['score'] = float(pred['score'] / total)
        
        predictions = self._apply_self_learning_boosts(predictions, domain)

        # 6. Automatic self-learning from confident predictions.
        if predictions:
            top_label = str(predictions[0].get("label", "")).strip().lower()
            top_score = float(predictions[0].get("score", 0.0))
            self.auto_tuner.auto_reinforce_prediction(
                domain=domain,
                predicted_label=top_label,
                confidence=top_score,
                caption=caption,
            )
        
        return predictions, model_name, domain, domain_conf

_engine = None
def get_prediction_engine() -> PredictionEngine:
    global _engine
    if _engine is None:
        _engine = PredictionEngine()
    return _engine
