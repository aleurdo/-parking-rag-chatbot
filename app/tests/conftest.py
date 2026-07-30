import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "mcp_server"))


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5:3b")
    monkeypatch.setenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    monkeypatch.setenv("LLM_TEMPERATURE", "0.2")
    monkeypatch.setenv("LLM_TIMEOUT", "300")
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    monkeypatch.setenv("QDRANT_PORT", "6333")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "parking_booking")
    monkeypatch.setenv("POSTGRES_USER", "parking")
    monkeypatch.setenv("POSTGRES_PASSWORD", "parking_secret")
    monkeypatch.setenv("GUARDRAILS_ENABLED", "true")
    monkeypatch.setenv("MCP_BASE_URL", "http://localhost:8001")
    monkeypatch.setenv("MCP_API_TOKEN", "mcp-secret-token")
    monkeypatch.setenv("MCP_OUTPUT_FILE", "/data/approved_reservations.txt")

    from app.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
