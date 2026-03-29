# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Telegram bot that translates any message to Persian (Farsi) using OpenRouter LLM API. Built with `python-telegram-bot` and `httpx`.

## Commands

```bash
make dev          # install all deps (including dev) via uv
make test         # run full test suite (pytest -v)
make lint         # ruff check src/ tests/
make format       # ruff format src/ tests/
make typecheck    # ty check src/
make check        # lint + typecheck + test
make run          # run bot locally (requires .env)

# single test
uv run pytest tests/test_bot.py -v
uv run pytest tests/test_bot.py::TestHandleMessage::test_translates_text_message -v
```

## Architecture

```
src/persian_translator_bot/
  bot.py          — Telegram handlers (start, message routing), Application setup, entry point (main())
  translator.py   — Translator class: async httpx client → OpenRouter chat completions API
  rate_limiter.py — RateLimiter: per-user sliding window (60s) backed by SQLite usage table
  database.py     — SQLite connection (WAL mode) and schema init (usage table)
  config.py       — Config dataclass loaded from env vars
  __main__.py     — Calls bot.main()
```

**Flow:** Telegram message → `bot.handle_message` → rate limit check → `Translator.translate` (OpenRouter API) → reply with Persian text. Usage recorded to SQLite after successful translation.

## Environment Variables

| Variable | Required | Default |
|----------|----------|---------|
| `TELEGRAM_BOT_TOKEN` | yes | — |
| `OPENROUTER_API_KEY` | yes | — |
| `OPENROUTER_MODEL` | no | `google/gemini-2.0-flash-001` |
| `RATE_LIMIT_PER_MINUTE` | no | `10` |
| `DATABASE_PATH` | no | `data/bot.db` |

## Testing

- Tests use `pytest-asyncio` with `asyncio_mode = "auto"` (no `@pytest.mark.asyncio` needed on new tests)
- `conftest.py` provides a `db_conn` fixture using in-memory SQLite
- `Translator` is mocked in bot tests; translator tests use `respx` to mock httpx
- `make_update()` helper in `test_bot.py` creates mock Telegram Update objects

## Deployment

Docker-based deployment to VPS via `make deploy` (runs `deploy.sh`). Requires `VPS_SSH=user@host` in `.env`. Data directory is volume-mounted at `./data`.
