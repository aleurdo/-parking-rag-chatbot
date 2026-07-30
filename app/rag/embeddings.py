import httpx

from app.config import get_settings


def embed_texts(texts: list[str]) -> list[list[float]]:
    settings = get_settings()
    embeddings = []
    for text in texts:
        response = httpx.post(
            f"{settings.ollama_base_url}/api/embed",
            json={"model": settings.ollama_embedding_model, "input": text},
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        embeddings.append(data["embeddings"][0])
    return embeddings


def embed_query(query: str) -> list[float]:
    return embed_texts([query])[0]
