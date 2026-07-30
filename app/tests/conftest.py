import os

import pytest


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-real-key-for-testing")
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    monkeypatch.setenv("QDRANT_PORT", "6333")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "parking_booking")
    monkeypatch.setenv("POSTGRES_USER", "parking")
    monkeypatch.setenv("POSTGRES_PASSWORD", "parking_secret")
    monkeypatch.setenv("GUARDRAILS_ENABLED", "true")

    from app.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
