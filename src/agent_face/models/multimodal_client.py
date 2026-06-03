"""
HTTP client for the multimodal model service (port 8001).

The multimodal model takes an image + optional text prompt
and returns a structured analysis of the person's features,
skin condition, and suggested beautification parameters.
"""

import httpx
from typing import Optional
from agent_face.config import settings
from agent_face.langgraph_brain.state import AnalysisResult, BeautifyParams


class MultimodalModelClient:
    """
    Async HTTP client wrapping the multimodal model's FastAPI service.

    The service is expected to expose:
        POST /analyze
        {
            "image_b64": "<base64>",
            "prompt": "Analyze this face for beautification",
            "preferences": {...}  // optional user preferences as hints
        }
        Returns: AnalysisResult schema
    """

    def __init__(self):
        self._base_url = settings.multimodal_model_url.rstrip("/")
        self._timeout = settings.model_request_timeout

    async def analyze(
        self,
        image_b64: str,
        prompt: Optional[str] = None,
        preferences: Optional[BeautifyParams] = None,
    ) -> AnalysisResult:
        """
        Send an image to the multimodal model for analysis.

        Args:
            image_b64: Base64-encoded input image.
            prompt: Optional natural language instruction for the analysis.
            preferences: Optional user preference parameters as hints.

        Returns:
            AnalysisResult with skin analysis, detected issues, and suggested params.

        Raises:
            httpx.HTTPError: On connection or timeout errors.
        """
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            payload = {
                "image_b64": image_b64,
                "prompt": prompt or "Analyze this face photo and suggest beautification parameters. "
                "Describe skin tone, skin condition, detected facial features, "
                "and any skin issues (acne, dark circles, spots, etc.). "
                "For each beautification parameter, give a value from 0.0 to 5.0.",
            }
            if preferences:
                payload["preferences"] = preferences

            response = await client.post(
                f"{self._base_url}/analyze",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return AnalysisResult(
                skin_tone=data["skin_tone"],
                skin_condition=data["skin_condition"],
                detected_features=data.get("detected_features", []),
                detected_issues=data.get("detected_issues", []),
                suggested_params=BeautifyParams(
                    skin_smoothing=data["suggested_params"].get("skin_smoothing", 2.0),
                    whitening=data["suggested_params"].get("whitening", 1.0),
                    eye_enlargement=data["suggested_params"].get("eye_enlargement", 1.5),
                    face_slimming=data["suggested_params"].get("face_slimming", 1.0),
                    blush=data["suggested_params"].get("blush", 1.0),
                    lip_color_adjustment=data["suggested_params"].get("lip_color_adjustment", 1.0),
                    blemish_removal=data["suggested_params"].get("blemish_removal", 3.0),
                    nose_reshaping=data["suggested_params"].get("nose_reshaping", 0.5),
                    eyebrow_adjustment=data["suggested_params"].get("eyebrow_adjustment", 1.0),
                ),
                reasoning=data.get("reasoning", ""),
                confidence=data.get("confidence", 0.5),
            )

    async def health_check(self) -> dict:
        """Check if the multimodal model service is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._base_url}/health")
                return {"status": "ok", "latency_ms": resp.elapsed.total_seconds() * 1000}
        except Exception as e:
            return {"status": "error", "error": str(e)}
