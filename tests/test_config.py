import pytest

from persian_translator_bot.config import Config, ConfigError


class TestConfig:
    def test_loads_required_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        config = Config.from_env()

        assert config.telegram_bot_token == "test-token"
        assert config.openrouter_api_key == "test-key"

    def test_defaults_for_optional_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
        monkeypatch.delenv("RATE_LIMIT_PER_MINUTE", raising=False)
        monkeypatch.delenv("DATABASE_PATH", raising=False)

        config = Config.from_env()

        assert config.openrouter_model == "google/gemini-2.0-flash-001"
        assert config.rate_limit_per_minute == 10
        assert config.database_path == "data/bot.db"

    def test_custom_optional_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        monkeypatch.setenv("OPENROUTER_MODEL", "anthropic/claude-3-haiku")
        monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "20")
        monkeypatch.setenv("DATABASE_PATH", "/tmp/test.db")

        config = Config.from_env()

        assert config.openrouter_model == "anthropic/claude-3-haiku"
        assert config.rate_limit_per_minute == 20
        assert config.database_path == "/tmp/test.db"

    def test_missing_telegram_token_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        with pytest.raises(ConfigError, match="TELEGRAM_BOT_TOKEN"):
            Config.from_env()

    def test_missing_openrouter_key_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        with pytest.raises(ConfigError, match="OPENROUTER_API_KEY"):
            Config.from_env()
