from unittest.mock import patch

import pytest

from app.llm.provider import get_llm


class TestLLMProvider:
    def test_returns_chat_ollama_instance(self):
        llm = get_llm()
        from langchain_ollama import ChatOllama
        assert isinstance(llm, ChatOllama)

    def test_uses_correct_model(self):
        llm = get_llm()
        assert llm.model == "qwen2.5:3b"

    def test_uses_correct_temperature(self):
        llm = get_llm()
        assert llm.temperature == 0.2

    @patch("app.llm.provider.get_settings")
    def test_raises_for_unsupported_provider(self, mock_settings):
        mock_settings.return_value.llm_provider = "unsupported"
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            get_llm()
