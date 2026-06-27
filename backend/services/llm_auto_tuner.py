import json
import logging
import os
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional
from PIL import Image

from models.llm_model import get_llm_model

logger = logging.getLogger(__name__)

DOMAIN_ALIASES: Dict[str, str] = {
    "medical image": "medical",
    "medical": "medical",
    "industrial object": "industrial",
    "industrial": "industrial",
}


class LLMAutoTuner:
    """Handles lightweight self-learning state and optional LLM prompt tuning."""

    def __init__(self):
        self.enabled = os.getenv("ENABLE_LLM_AUTO_TUNING", "true").lower() == "true"
        self.self_learning_enabled = os.getenv("ENABLE_SELF_LEARNING", "true").lower() == "true"
        self.auto_reinforce_enabled = os.getenv("ENABLE_AUTO_SELF_LEARNING", "true").lower() == "true"
        self.auto_reinforce_threshold = float(os.getenv("AUTO_SELF_LEARNING_THRESHOLD", "0.65"))
        self.min_feedback_support = int(os.getenv("SELF_LEARNING_MIN_SUPPORT", "2"))
        self.file_path = Path(__file__).resolve().parent.parent / "auto_learning_feedback.json"
        self._lock = Lock()

    def normalize_domain(self, domain: str) -> str:
        domain_key = (domain or "").strip().lower()
        return DOMAIN_ALIASES.get(domain_key, domain_key)

    def _default_state(self) -> Dict:
        return {
            "by_domain": {},
            "corrections": {},
        }

    def _load_state(self) -> Dict:
        if not self.file_path.exists():
            return self._default_state()
        try:
            with self.file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return self._default_state()
            data.setdefault("by_domain", {})
            data.setdefault("corrections", {})
            return data
        except Exception as exc:
            logger.warning("Failed to load auto-learning state: %s", exc)
            return self._default_state()

    def _save_state(self, state: Dict) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with self.file_path.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def get_learned_labels(self, domain: str) -> List[str]:
        if not self.self_learning_enabled:
            return []

        normalized_domain = self.normalize_domain(domain)
        state = self._load_state()
        domain_bucket = state.get("by_domain", {}).get(normalized_domain, {})

        learned = []
        for label, meta in domain_bucket.items():
            support = int(meta.get("support", 0))
            if support >= self.min_feedback_support:
                learned.append(label)

        return sorted(set(learned))

    def get_correction_boost(self, domain: str, predicted_label: str, candidate_label: str) -> float:
        if not self.self_learning_enabled:
            return 0.0

        normalized_domain = self.normalize_domain(domain)
        state = self._load_state()
        domain_map = state.get("corrections", {}).get(normalized_domain, {})
        key = f"{(predicted_label or '').strip().lower()}->{(candidate_label or '').strip().lower()}"
        count = int(domain_map.get(key, 0))

        # Enhanced score boost based on repeated user corrections.
        if count >= 5:
            return 0.08
        if count >= 3:
            return 0.05
        if count >= 2:
            return 0.03
        if count >= 1:
            return 0.015
        return 0.0

    def auto_reinforce_prediction(self, domain: str, predicted_label: str, confidence: float, caption: Optional[str] = None) -> Dict:
        """Automatically reinforce a confident prediction as pseudo-label learning."""
        if not self.self_learning_enabled or not self.auto_reinforce_enabled:
            return {"saved": False, "message": "Auto self-learning is disabled."}

        if confidence < self.auto_reinforce_threshold:
            return {
                "saved": False,
                "message": f"Confidence {confidence:.2f} below auto threshold {self.auto_reinforce_threshold:.2f}.",
            }

        return self.record_feedback(
            domain=domain,
            predicted_label=predicted_label,
            true_label=predicted_label,
            caption=caption,
        )

    def record_feedback(
        self,
        domain: str,
        predicted_label: str,
        true_label: str,
        caption: Optional[str] = None,
    ) -> Dict:
        if not self.self_learning_enabled:
            return {
                "saved": False,
                "message": "Self-learning is disabled by configuration.",
            }

        normalized_domain = self.normalize_domain(domain)
        predicted = (predicted_label or "").strip().lower()
        truth = (true_label or "").strip().lower()

        if not normalized_domain or not truth:
            return {
                "saved": False,
                "message": "Domain and true_label are required.",
            }

        with self._lock:
            state = self._load_state()
            by_domain = state.setdefault("by_domain", {})
            corrections = state.setdefault("corrections", {})

            domain_bucket = by_domain.setdefault(normalized_domain, {})
            label_meta = domain_bucket.setdefault(truth, {"support": 0, "captions": []})
            label_meta["support"] = int(label_meta.get("support", 0)) + 1

            if caption:
                captions = label_meta.setdefault("captions", [])
                captions.append(caption.strip())
                # Keep file bounded.
                if len(captions) > 20:
                    label_meta["captions"] = captions[-20:]

            if predicted and predicted != truth:
                correction_key = f"{predicted}->{truth}"
                domain_corr = corrections.setdefault(normalized_domain, {})
                domain_corr[correction_key] = int(domain_corr.get(correction_key, 0)) + 1

            self._save_state(state)

        learned = self.get_learned_labels(normalized_domain)
        return {
            "saved": True,
            "domain": normalized_domain,
            "true_label": truth,
            "learned_labels": learned,
        }

    def validate_prompts_with_clip(
        self,
        image: Image.Image,
        label: str,
        prompts: List[str],
    ) -> List[str]:
        """Use CLIP to validate and rank LLM-generated prompts by similarity"""
        try:
            from models.clip_model import get_vith14_model
            
            clip = get_vith14_model()
            image_emb = clip.encode_image(image)
            
            # Test all prompts
            prompt_scores = []
            for prompt in prompts:
                text_emb = clip.encode_text([prompt])
                similarity = clip.compute_similarity(image_emb, text_emb)[0]
                prompt_scores.append((prompt, float(similarity)))
            
            # Sort by similarity (best first)
            prompt_scores.sort(key=lambda x: x[1], reverse=True)
            validated = [p[0] for p in prompt_scores]
            
            logger.info(f"CLIP-validated prompts for '{label}': {validated[:2]} (scores: {[f'{s:.3f}' for _, s in prompt_scores[:2]]})")
            return validated
        except Exception as e:
            logger.warning(f"CLIP validation failed: {e}")
            return prompts

    def build_llm_prompt_ensembles(
        self,
        domain: str,
        caption: str,
        candidate_labels: List[str],
        image: Optional[Image.Image] = None,
    ) -> Dict[str, List[str]]:
        if not self.enabled or not caption or not candidate_labels:
            return {}

        prompt = f"""
You optimize CLIP prompts for image classification.

Domain: {self.normalize_domain(domain)}
Caption: {caption}
Candidate labels: {candidate_labels}

Return ONLY valid JSON as an object:
{{
  "label": ["prompt 1", "prompt 2", "prompt 3", "prompt 4"]
}}

Rules:
- Include exactly the provided labels as keys.
- Each label must have 4 concise prompts.
- Keep prompts factual and caption-grounded.
- Do not include markdown code fences.
"""

        try:
            llm = get_llm_model()
            raw = llm.generate(prompt=prompt, temperature=0.2, max_tokens=300)
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                return {}

            valid: Dict[str, List[str]] = {}
            for label in candidate_labels:
                prompts = parsed.get(label)
                if isinstance(prompts, list):
                    cleaned = [str(p).strip() for p in prompts if str(p).strip()]
                    if cleaned:
                        # Optionally validate with CLIP if image provided
                        if image is not None:
                            cleaned = self.validate_prompts_with_clip(image, label, cleaned[:4])
                        valid[label] = cleaned[:4]
            return valid
        except Exception as exc:
            logger.info("LLM auto-tuning skipped: %s", exc)
            return {}


_auto_tuner = None


def get_llm_auto_tuner() -> LLMAutoTuner:
    global _auto_tuner
    if _auto_tuner is None:
        _auto_tuner = LLMAutoTuner()
    return _auto_tuner
