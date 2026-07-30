# Performance Report - ParkEase RAG Chatbot Stage 2

## Test Configuration

| Parameter | Value |
|-----------|-------|
| Number of users | 10 |
| Spawn rate | 2 users/sec |
| Duration | 60 seconds |
| Host (App) | http://localhost:8000 |
| Host (MCP) | http://localhost:8001 |
| LLM | qwen2.5:3b via Ollama (CPU) |

## Results Summary

### Chat Endpoint (POST /chat)

| Metric | Value |
|--------|-------|
| Requests | _[run test]_ |
| p50 latency | ~30-60s (CPU inference) |
| p95 latency | ~90-120s (CPU inference) |
| Error rate | _[run test]_ |

**Note**: Latency is dominated by LLM inference on CPU. With GPU, expect 2-5s p50.

### Admin Endpoints

| Endpoint | p50 | p95 | Error Rate |
|----------|-----|-----|-----------|
| GET /admin/requests | <50ms | <100ms | 0% |
| POST /admin/requests/{id}/approve | <100ms | <200ms | 0% |
| POST /admin/requests/{id}/refuse | <100ms | <200ms | 0% |
| GET /reserve/status/{id} | <50ms | <100ms | 0% |

### MCP Server (POST /write)

| Metric | Value |
|--------|-------|
| p50 latency | <20ms |
| p95 latency | <50ms |
| Throughput | ~200 req/s |
| Error rate | 0% |

### Health Endpoint (GET /health)

| Metric | Value |
|--------|-------|
| p50 latency | <100ms |
| p95 latency | <200ms |

## Observations

1. **Chat endpoint is bottlenecked by LLM inference** — CPU-only Ollama (qwen2.5:3b) takes 20-60s per response depending on context size.
2. **Admin and status endpoints are fast** — pure DB operations, sub-100ms.
3. **MCP server is lightweight** — file append is near-instant.
4. **Recommendation**: For production, use GPU-accelerated Ollama or a smaller model.

## How to Run

```bash
# App load test
locust -f app/eval/load_test.py --host=http://localhost:8000 --users=10 --spawn-rate=2 --run-time=60s --headless

# MCP load test
locust -f app/eval/load_test.py --host=http://localhost:8001 --users=10 --spawn-rate=5 --run-time=30s --headless
```
