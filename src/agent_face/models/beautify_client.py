"""
HTTP client for the beautification model service (port 8002).

The beautification model takes an image + natural language description
and returns the beautified/enhanced image.
"""

import httpx
from agent_face.config import settings
from agent_face.langgraph_brain.state import BeautifyParams, BEAUTIFY_PARAM_LABELS


class BeautifyModelClient:
    """
    Async HTTP client wrapping the beautification model's FastAPI service.

    The service is expected to expose:
        POST /beautify
        {
            "image_b64": "<base64>",
            "description": "Apply skin smoothing level 3, whitening level 2..."
        }
        Returns: {"image_b64": "<base64>"}
    """

    def __init__(self):
        self._base_url = settings.beautify_model_url.rstrip("/")
        self._timeout = settings.model_request_timeout

    @staticmethod
    def params_to_description(params: BeautifyParams) -> str:
        """
        Convert structured beautification parameters to a natural language
        description that the beautification model can understand.

        This is the key translation: BeautifyParams → natural language.
        """
        parts = []
        for key, label in BEAUTIFY_PARAM_LABELS.items():
            value = params.get(key, 0)
            if value > 0:
                if value <= 1.0:
                    level = "轻微"
                elif value <= 2.0:
                    level = "轻度"
                elif value <= 3.0:
                    level = "中度"
                elif value <= 4.0:
                    level = "较明显"
                else:
                    level = "明显"

                parts.append(f"{label}{level}(程度{value:.1f}/5.0)")

        description = (
            "请对人像进行以下美颜处理："
            + "；".join(parts)
            + "。保持自然真实感，不要过度处理，确保面部特征可辨识。"
        )
        return description

    async def beautify(self, image_b64: str, params: BeautifyParams) -> str:
        """
        Send an image and beautification instructions to the beautification model.

        Args:
            image_b64: Base64-encoded input image.
            params: Beautification parameters to apply.

        Returns:
            Base64-encoded beautified image.

        Raises:
            httpx.HTTPError: On connection or timeout errors.
        """
        description = self.params_to_description(params)

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            payload = {
                "image_b64": image_b64,
                "description": description,
            }
            response = await client.post(
                f"{self._base_url}/beautify",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["image_b64"]

    async def health_check(self) -> dict:
        """Check if the beautification model service is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._base_url}/health")
                return {"status": "ok", "latency_ms": resp.elapsed.total_seconds() * 1000}
        except Exception as e:
            return {"status": "error", "error": str(e)}
