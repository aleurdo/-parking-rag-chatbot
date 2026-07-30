"""
Evaluation metrics for retrieval quality: Recall@K and Precision@K.
"""

from app.eval.dataset import EVAL_DATASET
from app.rag.vector_store import search_similar


def recall_at_k(retrieved_sources: list[str], relevant_sources: list[str], k: int) -> float:
    retrieved_set = set(retrieved_sources[:k])
    relevant_set = set(relevant_sources)
    if not relevant_set:
        return 0.0
    return len(retrieved_set & relevant_set) / len(relevant_set)


def precision_at_k(retrieved_sources: list[str], relevant_sources: list[str], k: int) -> float:
    retrieved_set = set(retrieved_sources[:k])
    relevant_set = set(relevant_sources)
    if not retrieved_set:
        return 0.0
    return len(retrieved_set & relevant_set) / len(retrieved_set)


def evaluate_retrieval(top_k: int = 5) -> dict:
    results = []

    for item in EVAL_DATASET:
        try:
            hits = search_similar(item["query"], top_k=top_k)
            retrieved_sources = [hit["source"] for hit in hits]

            r_at_k = recall_at_k(retrieved_sources, item["relevant_sources"], top_k)
            p_at_k = precision_at_k(retrieved_sources, item["relevant_sources"], top_k)

            results.append({
                "query_id": item["id"],
                "query": item["query"],
                "relevant_sources": item["relevant_sources"],
                "retrieved_sources": retrieved_sources,
                "recall_at_k": r_at_k,
                "precision_at_k": p_at_k,
            })
        except Exception as e:
            results.append({
                "query_id": item["id"],
                "query": item["query"],
                "error": str(e),
                "recall_at_k": 0.0,
                "precision_at_k": 0.0,
            })

    avg_recall = sum(r["recall_at_k"] for r in results) / len(results) if results else 0
    avg_precision = sum(r["precision_at_k"] for r in results) / len(results) if results else 0

    return {
        "top_k": top_k,
        "num_queries": len(results),
        "avg_recall_at_k": round(avg_recall, 4),
        "avg_precision_at_k": round(avg_precision, 4),
        "per_query_results": results,
    }


if __name__ == "__main__":
    import json
    report = evaluate_retrieval(top_k=5)
    print(json.dumps(report, indent=2))
