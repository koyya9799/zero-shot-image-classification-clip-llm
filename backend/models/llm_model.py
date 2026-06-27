# backend/models/llm_model.py
import io
import os
import base64
import logging
import re
import time
from typing import List, Optional

from dotenv import load_dotenv
from PIL import Image

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover
    genai = None

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None

logger = logging.getLogger(__name__)

class LLMModel:
    def __init__(self):
        # Keep `model` for backward compatibility with older call sites.
        self.model = None
        self.model_name = None
        self.provider = "none"

        self._gemini_model = None
        self._gemini_model_name = None
        self._openai_client = None
        self._openai_model_name = None

        self._available_providers: List[str] = []
        self._provider_retry_after = {"openai": 0.0, "gemini": 0.0}
        self._configure()

    def is_available(self) -> bool:
        return bool(self._available_providers)

    def _provider_order(self) -> List[str]:
        preferred = os.getenv("LLM_PROVIDER", "auto").strip().lower()
        if preferred == "gemini":
            return ["gemini", "openai"]
        if preferred == "openai":
            return ["openai", "gemini"]
        return ["openai", "gemini"]

    @staticmethod
    def _candidate_models() -> List[str]:
        preferred = os.getenv("GEMINI_MODEL", "").strip()
        ordered = [
            preferred,
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-flash-latest",
            "gemini-1.5-flash",
        ]
        # Deduplicate while preserving order and dropping empty values
        return [name for i, name in enumerate(ordered) if name and name not in ordered[:i]]

    def _resolve_supported_model(self) -> str:
        candidates = self._candidate_models()

        if genai is None:
            return candidates[0]

        try:
            available = set()
            for model in genai.list_models():
                methods = getattr(model, "supported_generation_methods", []) or []
                if "generateContent" in methods:
                    # model.name is usually like "models/gemini-2.0-flash"
                    short_name = model.name.replace("models/", "")
                    available.add(short_name)

            for name in candidates:
                if name in available:
                    return name

            for name in sorted(available):
                if name.startswith("gemini"):
                    logger.warning(
                        "No preferred GEMINI_MODEL available. Falling back to available model: %s",
                        name,
                    )
                    return name
        except Exception as e:
            logger.warning("Failed to enumerate Gemini models, using static fallback list: %s", e)

        return candidates[0]

    @staticmethod
    def _openai_candidate_models() -> List[str]:
        preferred = os.getenv("OPENAI_MODEL", "").strip()
        ordered = [
            preferred,
            "gpt-4.1-mini",
            "gpt-4o-mini",
        ]
        return [name for i, name in enumerate(ordered) if name and name not in ordered[:i]]

    def _configure_gemini(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return
        if genai is None:
            logger.warning("google-generativeai package not available, skipping Gemini provider")
            return

        try:
            genai.configure(api_key=api_key)
            model_name = self._resolve_supported_model()
            self._gemini_model = genai.GenerativeModel(model_name)
            self._gemini_model_name = model_name
            self._available_providers.append("gemini")
            logger.info("Gemini provider configured with model: %s", model_name)
        except Exception as e:
            logger.warning("Failed to configure Gemini API: %s", e)

    def _configure_openai(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return
        if OpenAI is None:
            logger.warning("openai package not available, skipping OpenAI provider")
            return

        try:
            # Disable SDK retries so fallback to other providers is immediate.
            self._openai_client = OpenAI(api_key=api_key, max_retries=0)
            self._openai_model_name = self._openai_candidate_models()[0]
            self._available_providers.append("openai")
            logger.info("OpenAI provider configured with model: %s", self._openai_model_name)
        except Exception as e:
            logger.warning("Failed to configure OpenAI API: %s", e)

    @staticmethod
    def _is_rate_limited_error(exc: Exception) -> bool:
        message = str(exc).lower()
        status_code = getattr(exc, "status_code", None)
        return (
            status_code == 429
            or "429" in message
            or "rate limit" in message
            or "quota" in message
            or "resource_exhausted" in message
        )

    @staticmethod
    def _extract_retry_seconds(exc: Exception, default_seconds: float = 60.0) -> float:
        message = str(exc)

        # Examples seen in providers:
        # - "Please retry in 387.798442ms"
        # - "Please retry in 37.11s"
        retry_match = re.search(r"retry\s+in\s+([0-9]+(?:\.[0-9]+)?)\s*(ms|s)?", message, re.IGNORECASE)
        if retry_match:
            value = float(retry_match.group(1))
            unit = (retry_match.group(2) or "s").lower()
            seconds = value / 1000.0 if unit == "ms" else value
            return max(1.0, min(seconds, 600.0))

        # OpenAI errors may include: "Please try again in 20s"
        try_again_match = re.search(r"try again in\s+([0-9]+(?:\.[0-9]+)?)\s*(ms|s)?", message, re.IGNORECASE)
        if try_again_match:
            value = float(try_again_match.group(1))
            unit = (try_again_match.group(2) or "s").lower()
            seconds = value / 1000.0 if unit == "ms" else value
            return max(1.0, min(seconds, 600.0))

        return default_seconds

    def _configure(self):
        load_dotenv()
        self._configure_openai()
        self._configure_gemini()

        for provider in self._provider_order():
            if provider in self._available_providers:
                self.provider = provider
                if provider == "openai":
                    self.model = self._openai_client
                    self.model_name = self._openai_model_name
                elif provider == "gemini":
                    self.model = self._gemini_model
                    self.model_name = self._gemini_model_name
                break

        if not self._available_providers:
            logger.warning(
                "No LLM provider configured. Set OPENAI_API_KEY and/or GEMINI_API_KEY to enable LLM features."
            )

    def _generate_text_openai(self, prompt: str, temperature: float, max_tokens: int) -> str:
        response = self._openai_client.chat.completions.create(
            model=self._openai_model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (response.choices[0].message.content or "").strip()

    def _generate_text_gemini(self, prompt: str, temperature: float, max_tokens: int) -> str:
        response = self._gemini_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text.strip()

    def _generate_vision_openai(self, prompt: str, image: Image.Image, temperature: float, max_tokens: int) -> str:
        image_bytes = io.BytesIO()
        image.save(image_bytes, format="PNG")
        image_b64 = base64.b64encode(image_bytes.getvalue()).decode("utf-8")

        response = self._openai_client.chat.completions.create(
            model=self._openai_model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                    ],
                }
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (response.choices[0].message.content or "").strip()

    def _generate_vision_gemini(self, prompt: str, image: Image.Image, temperature: float, max_tokens: int) -> str:
        response = self._gemini_model.generate_content(
            [prompt, image],
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text.strip()

    def _execute_with_fallback(self, mode: str, prompt: str, image: Optional[Image.Image], temperature: float, max_tokens: int) -> str:
        if not self._available_providers:
            raise ValueError("LLM is not configured")

        now = time.time()
        errors = []
        for provider in self._provider_order():
            if provider not in self._available_providers:
                continue

            retry_after = float(self._provider_retry_after.get(provider, 0.0))
            if now < retry_after:
                remaining = int(retry_after - now)
                errors.append(f"{provider}: cooling down ({remaining}s)")
                continue

            try:
                if mode == "text":
                    if provider == "openai":
                        return self._generate_text_openai(prompt, temperature, max_tokens)
                    if provider == "gemini":
                        return self._generate_text_gemini(prompt, temperature, max_tokens)
                else:
                    if provider == "openai":
                        return self._generate_vision_openai(prompt, image, temperature, max_tokens)
                    if provider == "gemini":
                        return self._generate_vision_gemini(prompt, image, temperature, max_tokens)
            except Exception as exc:
                errors.append(f"{provider}: {exc}")
                if self._is_rate_limited_error(exc):
                    cooldown = self._extract_retry_seconds(exc)
                    self._provider_retry_after[provider] = time.time() + cooldown
                    logger.warning(
                        "LLM %s generation rate-limited on %s; cooling down for %.1fs",
                        mode,
                        provider,
                        cooldown,
                    )
                else:
                    self._provider_retry_after[provider] = time.time() + 5.0
                logger.warning("LLM %s generation failed on %s, trying fallback", mode, provider)

        raise ValueError("All configured LLM providers failed: " + " | ".join(errors))

    def generate(self, prompt: str, temperature: float = 0.3, max_tokens: int = 300) -> str:
        return self._execute_with_fallback(
            mode="text",
            prompt=prompt,
            image=None,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def generate_vision(self, prompt: str, image: Image.Image, temperature: float = 0.3, max_tokens: int = 200) -> str:
        return self._execute_with_fallback(
            mode="vision",
            prompt=prompt,
            image=image,
            temperature=temperature,
            max_tokens=max_tokens,
        )

_llm_model = None
def get_llm_model() -> LLMModel:
    global _llm_model
    if _llm_model is None:
        _llm_model = LLMModel()
    return _llm_model
