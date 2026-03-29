from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from persian_translator_bot.config import Config
from persian_translator_bot.database import get_connection, init_db
from persian_translator_bot.rate_limiter import RateLimiter
from persian_translator_bot.translator import TranslationError, Translator

if TYPE_CHECKING:
    from telegram import Update

logger = logging.getLogger(__name__)


def _extract_text(update: Update) -> str | None:
    """Extract translatable text from a message."""
    message = update.message
    if message is None:
        return None

    if message.text:
        return message.text

    if message.caption:
        return message.caption

    return None


def _is_unsupported_media(update: Update) -> bool:
    """Check if the message is a media type we don't handle."""
    message = update.message
    if message is None:
        return False
    return bool(message.voice or message.sticker)


def _is_media_without_caption(update: Update) -> bool:
    """Check if the message has media but no caption."""
    message = update.message
    if message is None:
        return False
    has_media = bool(message.photo or message.video or message.document)
    return has_media and not message.caption


async def handle_start(update: Update, context: object) -> None:
    """Handle the /start command."""
    if update.message is None:
        return
    await update.message.reply_text(
        "Welcome! Send me any message and I'll translate it to Persian (Farsi).\n\n"
        "I can translate text messages and photo/video captions."
    )


async def handle_message(
    update: Update,
    context: object,
    limiter: RateLimiter,
    translator: Translator,
) -> None:
    """Handle incoming messages and translate them."""
    if update.message is None or update.effective_user is None:
        return

    user_id = update.effective_user.id
    username = update.effective_user.username

    if _is_unsupported_media(update):
        await update.message.reply_text("Please send a text message to translate.")
        return

    if _is_media_without_caption(update):
        await update.message.reply_text("This message has no text to translate.")
        return

    text = _extract_text(update)
    if not text:
        await update.message.reply_text("Please send a text message to translate.")
        return

    if not limiter.is_allowed(user_id):
        await update.message.reply_text("You've reached the limit (10/min). Please wait a moment.")
        return

    try:
        result = await translator.translate(text)
    except TranslationError:
        logger.exception("Translation failed for user %d", user_id)
        await update.message.reply_text("Translation failed. Please try again.")
        return

    limiter.record(user_id=user_id, username=username)
    await update.message.reply_text(result)


def main() -> None:
    """Entry point for the bot."""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    config = Config.from_env()

    # Ensure data directory exists
    db_dir = Path(config.database_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)

    conn = get_connection(config.database_path)
    init_db(conn)

    limiter = RateLimiter(conn, max_per_minute=config.rate_limit_per_minute)
    translator = Translator(api_key=config.openrouter_api_key, model=config.openrouter_model)

    app = Application.builder().token(config.telegram_bot_token).build()

    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            lambda update, context: handle_message(update, context, limiter, translator),
        )
    )

    logger.info("Bot starting with model %s", config.openrouter_model)
    app.run_polling()


if __name__ == "__main__":
    main()
