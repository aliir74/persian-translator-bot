import sqlite3
from unittest.mock import AsyncMock, MagicMock

import pytest

from persian_translator_bot.bot import handle_message, handle_start
from persian_translator_bot.rate_limiter import RateLimiter
from persian_translator_bot.translator import TranslationError, Translator


def make_update(
    text: str | None = None,
    caption: str | None = None,
    user_id: int = 123,
    username: str = "testuser",
    content_type: str = "text",
) -> MagicMock:
    """Create a mock Telegram Update object."""
    update = MagicMock()
    update.effective_user.id = user_id
    update.effective_user.username = username
    update.message.reply_text = AsyncMock()

    if content_type == "text":
        update.message.text = text
        update.message.caption = None
        update.message.photo = None
        update.message.video = None
        update.message.document = None
        update.message.voice = None
        update.message.sticker = None
    elif content_type == "photo":
        update.message.text = None
        update.message.caption = caption
        update.message.photo = [MagicMock()]
        update.message.video = None
        update.message.document = None
        update.message.voice = None
        update.message.sticker = None
    elif content_type == "voice":
        update.message.text = None
        update.message.caption = None
        update.message.photo = None
        update.message.video = None
        update.message.document = None
        update.message.voice = MagicMock()
        update.message.sticker = None
    elif content_type == "sticker":
        update.message.text = None
        update.message.caption = None
        update.message.photo = None
        update.message.video = None
        update.message.document = None
        update.message.voice = None
        update.message.sticker = MagicMock()

    return update


@pytest.fixture
def bot_deps(db_conn: sqlite3.Connection) -> dict:
    limiter = RateLimiter(db_conn, max_per_minute=10)
    translator = MagicMock(spec=Translator)
    translator.translate = AsyncMock(return_value="ترجمه تست")
    return {"limiter": limiter, "translator": translator}


class TestHandleStart:
    @pytest.mark.asyncio
    async def test_sends_welcome_message(self) -> None:
        update = make_update()
        context = MagicMock()

        await handle_start(update, context)

        update.message.reply_text.assert_called_once()
        call_text = update.message.reply_text.call_args[0][0]
        assert "translate" in call_text.lower() or "Persian" in call_text


class TestHandleMessage:
    @pytest.mark.asyncio
    async def test_translates_text_message(self, bot_deps: dict) -> None:
        update = make_update(text="Hello world")
        context = MagicMock()

        await handle_message(update, context, bot_deps["limiter"], bot_deps["translator"])

        bot_deps["translator"].translate.assert_called_once_with("Hello world")
        update.message.reply_text.assert_called_once_with("ترجمه تست")

    @pytest.mark.asyncio
    async def test_translates_photo_caption(self, bot_deps: dict) -> None:
        update = make_update(caption="Photo description", content_type="photo")
        context = MagicMock()

        await handle_message(update, context, bot_deps["limiter"], bot_deps["translator"])

        bot_deps["translator"].translate.assert_called_once_with("Photo description")
        update.message.reply_text.assert_called_once_with("ترجمه تست")

    @pytest.mark.asyncio
    async def test_rejects_photo_without_caption(self, bot_deps: dict) -> None:
        update = make_update(content_type="photo")
        context = MagicMock()

        await handle_message(update, context, bot_deps["limiter"], bot_deps["translator"])

        bot_deps["translator"].translate.assert_not_called()
        call_text = update.message.reply_text.call_args[0][0]
        assert "no text" in call_text.lower()

    @pytest.mark.asyncio
    async def test_rejects_voice_message(self, bot_deps: dict) -> None:
        update = make_update(content_type="voice")
        context = MagicMock()

        await handle_message(update, context, bot_deps["limiter"], bot_deps["translator"])

        bot_deps["translator"].translate.assert_not_called()
        call_text = update.message.reply_text.call_args[0][0]
        assert "text message" in call_text.lower()

    @pytest.mark.asyncio
    async def test_rejects_sticker(self, bot_deps: dict) -> None:
        update = make_update(content_type="sticker")
        context = MagicMock()

        await handle_message(update, context, bot_deps["limiter"], bot_deps["translator"])

        bot_deps["translator"].translate.assert_not_called()

    @pytest.mark.asyncio
    async def test_rate_limited_user_gets_error(self, db_conn: sqlite3.Connection) -> None:
        limiter = RateLimiter(db_conn, max_per_minute=1)
        translator = MagicMock(spec=Translator)
        translator.translate = AsyncMock(return_value="ترجمه")

        # First request fills the limit
        limiter.record(user_id=123, username="testuser")

        update = make_update(text="Hello")
        context = MagicMock()

        await handle_message(update, context, limiter, translator)

        translator.translate.assert_not_called()
        call_text = update.message.reply_text.call_args[0][0]
        assert "limit" in call_text.lower()

    @pytest.mark.asyncio
    async def test_translation_error_sends_friendly_message(self, bot_deps: dict) -> None:
        bot_deps["translator"].translate = AsyncMock(side_effect=TranslationError("API error"))
        update = make_update(text="Hello")
        context = MagicMock()

        await handle_message(update, context, bot_deps["limiter"], bot_deps["translator"])

        call_text = update.message.reply_text.call_args[0][0]
        assert "failed" in call_text.lower() or "try again" in call_text.lower()

    @pytest.mark.asyncio
    async def test_records_usage_on_success(
        self, db_conn: sqlite3.Connection, bot_deps: dict
    ) -> None:
        update = make_update(text="Hello")
        context = MagicMock()

        await handle_message(update, context, bot_deps["limiter"], bot_deps["translator"])

        cursor = db_conn.execute("SELECT COUNT(*) FROM usage WHERE user_id = 123")
        assert cursor.fetchone()[0] == 1
