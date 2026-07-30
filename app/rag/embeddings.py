from openai import OpenAI

from app.config import get_settings


def get_embedding_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(api_key=settings.openai_api_key)


def embed_texts(texts: list[str]) -> list[list[float]]:
    settings = get_settings()
    client = get_embedding_client()
    response = client.embeddings.create(
        input=texts,
        model=settings.openai_embedding_model,
    )
    return [item.embedding for item in response.data]


def embed_query(query: str) -> list[float]:
    return embed_texts([query])[0]
