import json

import httpx
import pytest
import respx  # noqa: F401 – respx.mock decorator is used via @respx.mock

from persian_translator_bot.translator import TranslationError, Translator

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class TestTranslator:
    @respx.mock
    @pytest.mark.asyncio
    async def test_translates_text(self) -> None:
        respx.post(OPENROUTER_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "choices": [
                        {"message": {"content": "سلام دنیا"}}
                    ]
                },
            )
        )

        translator = Translator(
            api_key="test-key",
            model="google/gemini-2.0-flash-001",
        )
        result = await translator.translate("Hello world")

        assert result == "سلام دنیا"

    @respx.mock
    @pytest.mark.asyncio
    async def test_sends_correct_prompt(self) -> None:
        route = respx.post(OPENROUTER_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "choices": [
                        {"message": {"content": "ترجمه"}}
                    ]
                },
            )
        )

        translator = Translator(api_key="test-key", model="test-model")
        await translator.translate("Some text")

        request = route.calls[0].request
        body = request.content.decode()
        payload = json.loads(body)

        assert payload["model"] == "test-model"
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert "Persian" in payload["messages"][0]["content"]
        assert payload["messages"][1]["role"] == "user"
        assert payload["messages"][1]["content"] == "Some text"

    @respx.mock
    @pytest.mark.asyncio
    async def test_sends_auth_header(self) -> None:
        route = respx.post(OPENROUTER_URL).mock(
            return_value=httpx.Response(
                200,
                json={"choices": [{"message": {"content": "ok"}}]},
            )
        )

        translator = Translator(api_key="sk-test-123", model="test-model")
        await translator.translate("text")

        request = route.calls[0].request
        assert request.headers["Authorization"] == "Bearer sk-test-123"

    @respx.mock
    @pytest.mark.asyncio
    async def test_api_error_raises_translation_error(self) -> None:
        respx.post(OPENROUTER_URL).mock(
            return_value=httpx.Response(500, json={"error": "Internal server error"})
        )

        translator = Translator(api_key="test-key", model="test-model")
        with pytest.raises(TranslationError):
            await translator.translate("text")

    @respx.mock
    @pytest.mark.asyncio
    async def test_rate_limit_429_raises_translation_error(self) -> None:
        respx.post(OPENROUTER_URL).mock(
            return_value=httpx.Response(429, json={"error": "Rate limited"})
        )

        translator = Translator(api_key="test-key", model="test-model")
        with pytest.raises(TranslationError, match="rate limit"):
            await translator.translate("text")

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_response_raises_translation_error(self) -> None:
        respx.post(OPENROUTER_URL).mock(
            return_value=httpx.Response(
                200,
                json={"choices": [{"message": {"content": ""}}]},
            )
        )

        translator = Translator(api_key="test-key", model="test-model")
        with pytest.raises(TranslationError, match="empty"):
            await translator.translate("text")

    @respx.mock
    @pytest.mark.asyncio
    async def test_malformed_response_raises_translation_error(self) -> None:
        respx.post(OPENROUTER_URL).mock(
            return_value=httpx.Response(200, json={"unexpected": "format"})
        )

        translator = Translator(api_key="test-key", model="test-model")
        with pytest.raises(TranslationError):
            await translator.translate("text")

    @respx.mock
    @pytest.mark.asyncio
    async def test_network_error_raises_translation_error(self) -> None:
        respx.post(OPENROUTER_URL).mock(side_effect=httpx.ConnectError("connection refused"))

        translator = Translator(api_key="test-key", model="test-model")
        with pytest.raises(TranslationError):
            await translator.translate("text")
