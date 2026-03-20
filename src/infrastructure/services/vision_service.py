"""OpenAI-compatible vision service implementation."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
from decimal import Decimal
from io import BytesIO
from typing import Any, Optional

import requests
from PIL import Image

from src.domain.entities.analysis import VisionAnalysis


logger = logging.getLogger(__name__)


class OpenAICompatibleVisionService:
    """Analyze plan images via an OpenAI-compatible multimodal endpoint."""

    MAX_WIDTH = 1920
    MAX_HEIGHT = 1920
    JPEG_QUALITY = 85

    def __init__(
        self,
        api_key: str | None,
        base_url: str,
        model: str = "gpt-4o-mini",
        timeout_seconds: int = 120,
    ) -> None:
        normalized_base_url = base_url.strip()
        if not normalized_base_url:
            raise ValueError(
                "OPENAI_BASE_URL must be configured before enabling vision."
            )
        self.api_key = api_key or "chatmock-local"
        self.base_url = normalized_base_url.rstrip("/")
        self.model_name = model
        self.timeout_seconds = timeout_seconds
        logger.info(
            "OpenAI-compatible vision service initialized",
            extra={"model": model, "base_url": self.base_url},
        )

    def analyze_plan(
        self,
        plan_id: str,
        image_bytes: bytes,
        include_ocr: bool = True,
    ) -> Optional[VisionAnalysis]:
        """Analyze a plan image and return structured findings."""
        try:
            processed_image = self._preprocess_image(image_bytes)
            payload = self._request_analysis(processed_image, include_ocr=include_ocr)
            structured = self._parse_json(payload)
            if structured is None:
                logger.error("Vision response did not contain valid JSON")
                return None

            return VisionAnalysis(
                plan_id=plan_id,
                image_hash=self._calculate_hash(processed_image),
                description=str(structured.get("description") or "No description"),
                zones_identified=list(structured.get("zones_identified") or []),
                measurements=dict(structured.get("measurements") or {}),
                ocr_text=structured.get("ocr_text"),
                extracted_data=dict(structured.get("extracted_data") or {}),
                provider="openai-compatible",
                model=self.model_name,
                tokens_used=int(structured.get("tokens_used") or 0),
                cost_usd=Decimal("0"),
                confidence_scores=dict(structured.get("confidence_scores") or {}),
            )
        except Exception as exc:
            logger.error("Plan analysis failed: %s", exc)
            return None

    def analyze_pil_image(
        self,
        plan_id: str,
        image: Image.Image,
        include_ocr: bool = True,
    ) -> Optional[VisionAnalysis]:
        """Convenience wrapper for PIL images."""
        buf = BytesIO()
        prepared = image.convert("RGB") if image.mode != "RGB" else image
        prepared.save(buf, format="JPEG", quality=self.JPEG_QUALITY, optimize=True)
        return self.analyze_plan(
            plan_id=plan_id,
            image_bytes=buf.getvalue(),
            include_ocr=include_ocr,
        )

    def _request_analysis(self, image_bytes: bytes, *, include_ocr: bool) -> str:
        data_uri = self._to_data_uri(image_bytes)
        system_prompt = (
            "You are an expert planner reviewing Israeli planning documents. "
            "Return valid JSON only."
        )
        user_prompt = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Analyze this uploaded planning document and return a JSON object with keys: "
                        "description, zones_identified, measurements, ocr_text, extracted_data, "
                        "confidence_scores. "
                        f"OCR should be {'included' if include_ocr else 'null'}. "
                        "Keep zones_identified as an array of short strings. "
                        "Keep measurements/extracted_data/confidence_scores as JSON objects."
                    ),
                },
                {"type": "image_url", "image_url": {"url": data_uri}},
            ],
        }
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                user_prompt,
            ],
            "temperature": 0.1,
            "max_tokens": 1500,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        choices = body.get("choices") or []
        if not choices:
            raise ValueError("No choices returned by vision provider")
        content = choices[0].get("message", {}).get("content", "")
        if isinstance(content, list):
            return "\n".join(
                str(part.get("text", "")) for part in content if isinstance(part, dict)
            )
        return str(content)

    def _preprocess_image(self, image_bytes: bytes) -> bytes:
        """Resize and normalize images before sending them to the provider."""
        try:
            image = Image.open(BytesIO(image_bytes))
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
            if image.width > self.MAX_WIDTH or image.height > self.MAX_HEIGHT:
                image.thumbnail(
                    (self.MAX_WIDTH, self.MAX_HEIGHT),
                    Image.Resampling.LANCZOS,
                )
            output = BytesIO()
            image.save(
                output,
                format="JPEG",
                quality=self.JPEG_QUALITY,
                optimize=True,
            )
            return output.getvalue()
        except Exception as exc:
            logger.warning("Image preprocessing failed, using original bytes: %s", exc)
            return image_bytes

    @staticmethod
    def _calculate_hash(image_bytes: bytes) -> str:
        return hashlib.sha256(image_bytes).hexdigest()

    @staticmethod
    def _to_data_uri(image_bytes: bytes) -> str:
        encoded = base64.b64encode(image_bytes).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"

    @staticmethod
    def _parse_json(content: str) -> Optional[dict[str, Any]]:
        """Parse JSON from a model response that may include fenced code."""
        stripped = content.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if len(lines) >= 3:
                stripped = "\n".join(lines[1:-1]).strip()
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            start = stripped.find("{")
            end = stripped.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return None
            try:
                parsed = json.loads(stripped[start : end + 1])
            except json.JSONDecodeError:
                return None
        if not isinstance(parsed, dict):
            return None
        return parsed


# Backwards-compatible alias for modules that still import the legacy name.
GeminiVisionService = OpenAICompatibleVisionService
