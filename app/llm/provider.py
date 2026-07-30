from langchain_ollama import ChatOllama

from app.config import get_settings


def get_llm() -> ChatOllama:
    settings = get_settings()
    if settings.llm_provider == "ollama":
        return ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=settings.llm_temperature,
            timeout=settings.llm_timeout,
        )
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
