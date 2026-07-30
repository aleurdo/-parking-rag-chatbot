import pytest

from app.eval.metrics import precision_at_k, recall_at_k


class TestRecallAtK:
    def test_perfect_recall(self):
        retrieved = ["pricing.md", "faq.md", "general_info.md"]
        relevant = ["pricing.md", "faq.md"]
        assert recall_at_k(retrieved, relevant, k=3) == 1.0

    def test_partial_recall(self):
        retrieved = ["pricing.md", "location_access.md"]
        relevant = ["pricing.md", "faq.md"]
        assert recall_at_k(retrieved, relevant, k=2) == 0.5

    def test_zero_recall(self):
        retrieved = ["location_access.md", "booking_process.md"]
        relevant = ["pricing.md", "faq.md"]
        assert recall_at_k(retrieved, relevant, k=2) == 0.0

    def test_empty_relevant_returns_zero(self):
        retrieved = ["pricing.md"]
        assert recall_at_k(retrieved, [], k=1) == 0.0

    def test_k_limits_retrieved(self):
        retrieved = ["a.md", "b.md", "pricing.md"]
        relevant = ["pricing.md"]
        assert recall_at_k(retrieved, relevant, k=2) == 0.0
        assert recall_at_k(retrieved, relevant, k=3) == 1.0


class TestPrecisionAtK:
    def test_perfect_precision(self):
        retrieved = ["pricing.md", "faq.md"]
        relevant = ["pricing.md", "faq.md"]
        assert precision_at_k(retrieved, relevant, k=2) == 1.0

    def test_half_precision(self):
        retrieved = ["pricing.md", "location_access.md"]
        relevant = ["pricing.md", "faq.md"]
        assert precision_at_k(retrieved, relevant, k=2) == 0.5

    def test_zero_precision(self):
        retrieved = ["location_access.md", "booking_process.md"]
        relevant = ["pricing.md"]
        assert precision_at_k(retrieved, relevant, k=2) == 0.0

    def test_empty_retrieved_returns_zero(self):
        assert precision_at_k([], ["pricing.md"], k=5) == 0.0
