# ParkEase RAG Chatbot - Stage 2 Presentation

## Slide 1: Title
- **ParkEase RAG Chatbot** - Stage 2: Admin Agent + MCP + LangGraph
- Multi-agent parking reservation system with human-in-the-loop approval
- [Screenshot: Full architecture diagram]

## Slide 2: Architecture Overview (Stage 2)
```
User ──→ [User Agent] ──→ [RAG Pipeline] ──→ Response
              │
              ▼ (if reservation)
        [Admin Approval Node]
              │
              ▼ (pending)
        [Admin REST API] ←── Administrator
              │
              ▼ (approved)
        [Record Node] ──→ [MCP Server] ──→ File
```

## Slide 3: LangGraph Orchestration
- **User Agent Node**: RAG Q&A + reservation detail collection
- **Admin Approval Node**: Creates pending request, human-in-the-loop wait
- **Record Node**: Calls MCP server to persist approved reservations
- State machine: chat → reserve → pending → approved/refused → recorded
- [Screenshot: Graph state transitions]

## Slide 4: LLM Integration (Qwen2.5:3B)
- LangChain + ChatOllama integration
- Model: qwen2.5:3b (local, free, no API key needed)
- Provider factory pattern (app/llm/provider.py)
- Configurable via .env: LLM_PROVIDER, OLLAMA_BASE_URL, OLLAMA_MODEL
- [Screenshot: Config + provider code]

## Slide 5: Admin Agent (Human-in-the-Loop)
- REST API for administrators:
  - GET /admin/requests (list pending)
  - GET /admin/requests/{id} (detail)
  - POST /admin/requests/{id}/approve
  - POST /admin/requests/{id}/refuse
- Persistent storage in PostgreSQL (admin_requests table)
- User polls via GET /reserve/status/{id}
- [Screenshot: Swagger admin endpoints + pending list]

## Slide 6: Reservation Flow
1. User says "I want to reserve" → agent collects details
2. Required: name, car_number, start/end datetime, location
3. Validation: format, time range, not in past, valid location
4. Submit → pending admin request
5. Admin approves/refuses → user notified via status endpoint
- [Screenshot: Multi-turn booking conversation]

## Slide 7: MCP Server (File Recording)
- Separate Docker service (mcp_server/)
- Bearer token authentication (MCP_API_TOKEN)
- Strict Pydantic validation
- Path traversal prevention
- Idempotency: [ID:N] marker prevents duplicate writes
- Format: `Name | Car Number | Period | Approval Time [ID:N]`
- [Screenshot: MCP write request + file content]

## Slide 8: Guardrails & Security
- Input: blocks prompt injection, credential extraction
- Output: redacts API keys, masks PII
- MCP: auth required, path traversal blocked, idempotent
- Admin: only pending requests can be decided
- No PII echoed beyond what's required for booking
- [Screenshot: Blocked request + MCP auth failure]

## Slide 9: Testing & Evaluation
- **78+ unit tests** across 10 test modules
- Covers: chunker, guardrails, API, chat, DB, eval, admin, orchestrator, MCP, LLM
- Integration tests: full flow (user → admin → approve → file)
- Load testing: Locust for chat, admin, MCP endpoints
- Retrieval metrics: Recall@K, Precision@K
- [Screenshot: pytest output green + CI pipeline]

## Slide 10: Docker Compose Architecture
```yaml
services:
  app         → FastAPI (port 8000)
  mcp-server  → MCP File Writer (port 8001)
  postgres    → PostgreSQL 16 (port 5432)
  qdrant      → Vector DB (port 6333)
  # Ollama runs on host (port 11434)
```
- [Screenshot: docker compose up output]

## Slide 11: Next Steps
- WebSocket for real-time admin notifications
- Slack/Telegram adapter for admin approval channel
- GPU-accelerated inference (NVIDIA + Ollama)
- Multi-tenant admin roles
- Monitoring with OpenTelemetry
- Production deployment (Kubernetes)

---

## Screenshots to Capture
1. docker compose up showing all 4 services
2. GET /health showing all services healthy
3. POST /ingest response
4. POST /chat with pricing question (with sources)
5. POST /chat triggering reservation flow
6. GET /admin/requests showing pending request
7. POST /admin/requests/1/approve
8. GET /reserve/status/1 showing "approved"
9. cat storage/approved_reservations.txt showing written line
10. Guardrails blocking prompt injection
11. MCP auth failure (wrong token)
12. pytest all passing
13. GitHub Actions CI green
