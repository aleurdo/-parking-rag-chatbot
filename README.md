# ParkEase RAG Chatbot (Stage 2)

A production-oriented multi-agent parking reservation system with RAG, human-in-the-loop admin approval, MCP file recording, and LangGraph orchestration. Uses **Qwen2.5:3B** via Ollama (local, free).

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         FastAPI Server                             │
├───────────┬──────────┬───────────┬──────────┬────────────────────┤
│  /chat    │ /ingest  │ /reserve  │ /health  │ /admin/*           │
└─────┬─────┴────┬─────┴─────┬────┴──────────┴─────────┬──────────┘
      │          │           │                          │
      ▼          ▼           ▼                          ▼
┌───────────┐ ┌────────┐ ┌───────────┐          ┌─────────────┐
│ LangGraph │ │Chunker │ │Repository │          │ Admin Agent │
│Orchestratr│ │+Embed  │ │  (SQL)    │          │ (Approve/   │
│           │ │        │ │           │          │  Refuse)    │
├───────────┤ └───┬────┘ └─────┬─────┘          └──────┬──────┘
│User Agent │     │            │                        │
│Admin Node │     ▼            ▼                        ▼
│Record Node│ ┌────────┐ ┌──────────┐           ┌──────────────┐
└─────┬─────┘ │ Qdrant │ │PostgreSQL│           │  MCP Server  │
      │       └────────┘ └──────────┘           │(File Writer) │
      ▼                                         └──────────────┘
┌───────────┐
│  Ollama   │
│qwen2.5:3b │
└───────────┘
```

### LangGraph Flow
```
User Message → [User Agent Node]
                    │
          ┌─────────┼──────────┐
          ▼         ▼          ▼
      [RAG Q&A] [Reserve]  [Status]
                    │          │
                    ▼          ▼
            [Admin Approval] [Check DB]
                    │
            ┌───────┴───────┐
            ▼               ▼
        [Pending]      [Approved]
                           │
                           ▼
                    [Record Node]
                           │
                           ▼
                    [MCP Write File]
```

## Features

- **RAG Q&A**: Answers parking questions with source citations (Qdrant + Ollama embeddings)
- **Reservation Flow**: Multi-turn collection of name, car number, period, location
- **Admin Approval**: Human-in-the-loop via REST API; persistent in PostgreSQL
- **MCP Recording**: Approved reservations written to file via authenticated MCP server
- **LangGraph Orchestration**: State machine connecting user, admin, and recording nodes
- **Guardrails**: Input/output filtering (prompt injection, PII, secrets)
- **LLM**: Qwen2.5:3B via LangChain + ChatOllama (local, no API key)
- **Evaluation**: Recall@K, Precision@K metrics + Locust load testing

## Project Structure

```
parking-rag-chatbot/
├── app/
│   ├── api/            # FastAPI routes (user + admin)
│   ├── llm/            # LangChain provider factory (Ollama)
│   ├── graph/          # LangGraph orchestrator, state, LLM generation
│   ├── rag/            # Chunking, embeddings, Qdrant vector store
│   ├── guardrails/     # Input/output filtering & policy
│   ├── db/             # SQLAlchemy models + repositories
│   ├── mcp/            # MCP client (calls file writer)
│   ├── eval/           # Evaluation dataset, metrics, load tests
│   ├── tests/          # Unit + integration tests (78+ tests)
│   ├── config.py       # Settings from .env
│   └── main.py         # FastAPI app entry point
├── mcp_server/         # Standalone MCP file writer service
├── data/
│   ├── static_docs/    # Knowledge base (Markdown)
│   ├── schema.sql      # PostgreSQL schema (incl. admin_requests)
│   └── seed.sql        # Sample data
├── storage/            # MCP output directory (shared volume)
├── docs/               # Performance report
├── slides/             # Presentation outline
├── .github/workflows/  # CI/CD pipeline
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Ollama installed (`curl -fsSL https://ollama.com/install.sh | sh`)

### Setup

```bash
# 1. Pull required models
ollama pull qwen2.5:3b
ollama pull nomic-embed-text

# 2. Clone and configure
git clone https://github.com/aleurdo/-parking-rag-chatbot.git
cd parking-rag-chatbot
cp .env.example .env

# 3. Start all services
docker compose up --build

# 4. Ingest documents
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"docs_directory": "data/static_docs"}'
```

## API Endpoints

### User Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health check |
| POST | `/chat` | Send a chat message |
| POST | `/ingest` | Ingest documents into vector DB |
| POST | `/reserve` | Create a reservation directly |
| GET | `/reserve/status/{id}` | Check admin approval status |

### Admin Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/requests` | List pending admin requests |
| GET | `/admin/requests/{id}` | Get request detail |
| POST | `/admin/requests/{id}/approve` | Approve a reservation |
| POST | `/admin/requests/{id}/refuse` | Refuse a reservation |

### MCP Server (port 8001)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/write` | Write approved reservation to file |
| GET | `/health` | MCP server health |

## Usage Examples

### Chat (FAQ)
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the parking rates?", "session_id": "user1"}'
```

### Make a Reservation (via chat)
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to reserve at Downtown Garage. Alice Smith, car 34-AB-123, from 2026-08-01T10:00 to 2026-08-01T14:00",
    "session_id": "user1"
  }'
```

### Admin Approval
```bash
# List pending
curl http://localhost:8000/admin/requests

# Approve
curl -X POST http://localhost:8000/admin/requests/1/approve \
  -H "Content-Type: application/json" \
  -d '{"note": "Approved - space available"}'

# Check status
curl http://localhost:8000/reserve/status/1
```

### Check recorded file
```bash
cat storage/approved_reservations.txt
# Output: Alice Smith | 34-AB-123 | 2026-08-01T10:00:00Z - 2026-08-01T14:00:00Z | 2026-07-30T14:15:00Z [ID:1]
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| LLM_PROVIDER | ollama | LLM backend (ollama) |
| OLLAMA_BASE_URL | http://localhost:11434 | Ollama API URL |
| OLLAMA_MODEL | qwen2.5:3b | Chat model |
| OLLAMA_EMBEDDING_MODEL | nomic-embed-text | Embedding model |
| LLM_TEMPERATURE | 0.2 | Generation temperature |
| LLM_TIMEOUT | 300 | Request timeout (seconds) |
| QDRANT_HOST | localhost | Qdrant host |
| POSTGRES_HOST | localhost | PostgreSQL host |
| MCP_BASE_URL | http://localhost:8001 | MCP server URL |
| MCP_API_TOKEN | mcp-secret-token | MCP auth token |
| GUARDRAILS_ENABLED | true | Enable input/output filtering |

## Running Tests

```bash
# All unit tests (no external services needed)
pytest app/tests/ -v --ignore=app/tests/test_integration.py --ignore=app/tests/test_integration_flow.py

# With coverage
pytest app/tests/ --cov=app --cov-report=term-missing \
  --ignore=app/tests/test_integration.py --ignore=app/tests/test_integration_flow.py

# Integration tests (requires running services)
pytest app/tests/test_integration_flow.py -v
```

## Evaluation

```bash
# Retrieval quality (after ingest)
python -m app.eval.metrics

# Load testing
locust -f app/eval/load_test.py --host=http://localhost:8000
```

## CI/CD

GitHub Actions pipeline (`.github/workflows/ci.yml`):
1. **Lint** → ruff check
2. **Unit Tests** → pytest (mocked LLM + DB)
3. **Integration Tests** → with Postgres & Qdrant services

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LLM | Qwen2.5:3B via Ollama | Local, free, fast enough on CPU |
| LLM Framework | LangChain (ChatOllama) | Standard interface, easy to swap |
| Orchestration | LangGraph-style state machine | Deterministic flow, testable nodes |
| Admin Channel | REST API | Simple, testable, no external deps |
| MCP Server | Separate FastAPI service | Isolation, shared volume for file |
| Auth | Bearer token | Simple, effective for service-to-service |
| Idempotency | [ID:N] marker in file | Prevents duplicate writes on retry |
