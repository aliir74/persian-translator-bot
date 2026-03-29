from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = (
    "You are a translator. Translate the following text to Persian (Farsi). "
    "Only output the translation, nothing else. No explanations, no notes. "
    "If the text is already in Persian, reply with the exact same text. "
    "Preserve the original formatting (line breaks, bullet points, etc.)."
)


class TranslationError(Exception):
    pass


class Translator:
    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model
        self._client = httpx.AsyncClient(timeout=30.0)

    async def translate(self, text: str) -> str:
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = await self._client.post(OPENROUTER_URL, json=payload, headers=headers)
        except httpx.HTTPError as e:
            logger.error("OpenRouter request failed: %s", e)
            raise TranslationError(f"Request failed: {e}") from e

        if response.status_code == 429:
            logger.warning("OpenRouter rate limit hit")
            raise TranslationError("OpenRouter rate limit reached")

        if response.status_code != 200:
            logger.error("OpenRouter returned %d: %s", response.status_code, response.text)
            raise TranslationError(f"API error: {response.status_code}")

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            logger.error("Malformed OpenRouter response: %s", response.text)
            raise TranslationError(f"Malformed response: {e}") from e

        if not content or not content.strip():
            raise TranslationError("OpenRouter returned empty translation")

        return content.strip()

    async def close(self) -> None:
        await self._client.aclose()
