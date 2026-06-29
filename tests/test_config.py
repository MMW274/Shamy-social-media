import os
from pipeline.config import Settings, load_settings


def test_load_settings_from_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g-key")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t-tok")
    monkeypatch.setenv("TELEGRAM_CHAT_ID_SNEHA", "111")
    monkeypatch.setenv("TELEGRAM_CHAT_ID_MEHUL", "222")
    monkeypatch.setenv("DRIVE_ROOT_FOLDER_ID", "abc")
    monkeypatch.setenv("DRY_RUN", "true")

    s = load_settings()
    assert isinstance(s, Settings)
    assert s.gemini_api_key == "g-key"
    assert s.telegram_bot_token == "t-tok"
    assert s.dry_run is True
    assert s.timezone == "Europe/Berlin"


def test_missing_required_raises(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    import pytest
    with pytest.raises(RuntimeError) as exc:
        load_settings()
    assert "GEMINI_API_KEY" in str(exc.value)
