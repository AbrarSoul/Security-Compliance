"""HTTP client for GPT-Lab OpenAI-compatible endpoints."""

from __future__ import annotations

import httpx


class GptLabClientError(RuntimeError):
    """Raised when GPT-Lab API calls fail."""


class GptLabClient:
    def __init__(
        self,
        api_base: str,
        api_key: str,
        *,
        timeout_seconds: float = 30.0,
    ):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    async def fetch_model_ids(self) -> list[str]:
        url = f"{self.api_base}/models"
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(url, headers=self._headers())
        except httpx.RequestError as exc:
            raise GptLabClientError(f"Failed to reach GPT-Lab API: {exc}") from exc

        if response.status_code != 200:
            raise GptLabClientError(f"{response.status_code} - {response.text}")

        payload = response.json()
        data = payload.get("data", [])
        return [str(item.get("id", "")).strip() for item in data if item.get("id")]
