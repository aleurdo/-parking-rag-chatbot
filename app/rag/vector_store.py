from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)

from app.config import get_settings
from app.rag.chunker import DocumentChunk
from app.rag.embeddings import embed_query, embed_texts


def get_qdrant_client() -> QdrantClient:
    settings = get_settings()
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def ensure_collection(client: QdrantClient, dimension: int = 1536) -> None:
    settings = get_settings()
    collections = [c.name for c in client.get_collections().collections]
    if settings.qdrant_collection not in collections:
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
        )


def ingest_chunks(chunks: list[DocumentChunk]) -> int:
    settings = get_settings()
    client = get_qdrant_client()
    ensure_collection(client)

    texts = [c.content for c in chunks]
    batch_size = 50
    total_ingested = 0

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        batch_chunks = chunks[i : i + batch_size]
        embeddings = embed_texts(batch_texts)

        points = [
            PointStruct(
                id=i + j,
                vector=emb,
                payload={
                    "content": chunk.content,
                    "source": chunk.source,
                    "chunk_id": chunk.chunk_id,
                    "metadata": chunk.metadata,
                },
            )
            for j, (emb, chunk) in enumerate(zip(embeddings, batch_chunks))
        ]

        client.upsert(collection_name=settings.qdrant_collection, points=points)
        total_ingested += len(points)

    return total_ingested


def search_similar(query: str, top_k: int = 5) -> list[dict]:
    settings = get_settings()
    client = get_qdrant_client()
    query_vector = embed_query(query)

    results = client.search(
        collection_name=settings.qdrant_collection,
        query_vector=query_vector,
        limit=top_k,
    )

    return [
        {
            "content": hit.payload["content"],
            "source": hit.payload["source"],
            "chunk_id": hit.payload["chunk_id"],
            "score": hit.score,
            "metadata": hit.payload.get("metadata", {}),
        }
        for hit in results
    ]
