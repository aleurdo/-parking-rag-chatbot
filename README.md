# ParkEase RAG Chatbot

A production-oriented Retrieval-Augmented Generation (RAG) chatbot for parking reservation and information services. Built with FastAPI, Qdrant vector database, PostgreSQL, and OpenAI.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      FastAPI Server                       │
├─────────────┬──────────────┬──────────────┬─────────────┤
│   /chat     │   /ingest    │   /reserve   │   /health   │
└──────┬──────┴──────┬───────┴──────┬───────┴─────────────┘
       │             │              │
       ▼             ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│  Guardrails  │ │ Chunker  │ │  Repository  │
│  (Input/Out) │ │& Embedder│ │   (SQL)      │
└──────┬───────┘ └────┬─────┘ └──────┬───────┘
       │              │               │
       ▼              ▼               ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│  LLM (GPT)  │ │  Qdrant  │ │  PostgreSQL  │
│  Generation  │ │ VectorDB │ │  (Bookings)  │
└──────────────┘ └──────────┘ └──────────────┘
```

### Data Flow
1. **Static Knowledge** → Markdown docs → Chunked & embedded → Qdrant
2. **Dynamic Data** (availability, reservations) → PostgreSQL
3. **User Query** → Guardrails check → Vector search → LLM generation → Output filter → Response

## Features

- **RAG-based Q&A**: Answers parking questions using retrieved document context with source citations
- **Reservation Flow**: Multi-turn conversation to collect booking details and create reservations
- **Guardrails**: Input/output filtering for prompt injection, PII, secrets, and credentials
- **Evaluation**: Retrieval quality metrics (Recall@K, Precision@K) and load testing
- **Dockerized**: One-command setup with Docker Compose

## Project Structure

```
parking-rag-chatbot/
├── app/
│   ├── api/            # FastAPI routes & schemas
│   ├── rag/            # Chunking, embeddings, vector store
│   ├── graph/          # LLM orchestration & chat session logic
│   ├── guardrails/     # Input/output filtering & policy
│   ├── db/             # SQLAlchemy models & repository
│   ├── eval/           # Evaluation dataset & metrics
│   ├── tests/          # Unit & integration tests
│   ├── config.py       # Settings (from env vars)
│   └── main.py         # FastAPI app entry point
├── data/
│   ├── static_docs/    # Knowledge base (Markdown)
│   ├── schema.sql      # PostgreSQL schema
│   └── seed.sql        # Sample data
├── .github/workflows/  # CI/CD pipeline
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key

### Setup

1. **Clone and configure:**
   ```bash
   git clone <repo-url>
   cd parking-rag-chatbot
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

2. **Start all services:**
   ```bash
   docker compose up --build
   ```

3. **Ingest documents:**
   ```bash
   curl -X POST http://localhost:8000/ingest \
     -H "Content-Type: application/json" \
     -d '{"docs_directory": "data/static_docs"}'
   ```

4. **Start chatting:**
   ```bash
   curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "What are the parking rates?", "session_id": "user1"}'
   ```

### Local Development (without Docker)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start Qdrant and PostgreSQL separately, then:
uvicorn app.main:app --reload
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health check |
| POST | `/chat` | Send a chat message |
| POST | `/ingest` | Ingest documents into vector DB |
| POST | `/reserve` | Create a parking reservation |

### POST /chat
```json
{
  "message": "What are the parking rates at Downtown Garage?",
  "session_id": "user-123"
}
```

Response:
```json
{
  "response": "Downtown Garage rates are $3.00 for the first hour...",
  "sources": ["pricing.md"],
  "blocked": false,
  "booking_active": false
}
```

### POST /reserve
```json
{
  "customer_name": "John Doe",
  "customer_email": "john@example.com",
  "license_plate": "ABC-1234",
  "location_name": "Downtown Garage",
  "vehicle_type": "standard",
  "start_time": "2025-01-15T09:00:00"
}
```

## Running Tests

```bash
# Unit tests (no external services needed)
pytest app/tests/ -v --ignore=app/tests/test_integration.py

# With coverage
pytest app/tests/ --cov=app --cov-report=term-missing --ignore=app/tests/test_integration.py

# Integration tests (requires running services)
pytest app/tests/test_integration.py -v
```

## Evaluation

### Retrieval Quality
```bash
# After ingesting documents:
python -m app.eval.metrics
```

Outputs Recall@K and Precision@K for a labeled evaluation dataset (12 queries).

### Load Testing
```bash
locust -f app/eval/load_test.py --host=http://localhost:8000
```

## CI/CD

GitHub Actions pipeline (`.github/workflows/ci.yml`):
1. **Lint** → ruff check
2. **Unit Tests** → pytest (mocked external deps)
3. **Integration Tests** → with Postgres & Qdrant services

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Vector DB | Qdrant | Excellent Docker support, simple API, cosine similarity |
| SQL DB | PostgreSQL | Mature, widely supported, handles availability/reservations |
| Embeddings | OpenAI text-embedding-3-small | High quality, cost-effective, 1536 dimensions |
| LLM | GPT-4o-mini | Fast, affordable, good instruction following |
| Guardrails | Regex + heuristic | Lightweight, no extra model dependencies for PII |
| Framework | FastAPI | Async-ready, auto-docs, Pydantic validation |
| Chunking | Header-based + size limit | Preserves semantic coherence of parking info sections |

## Guardrails Policy

The system implements layered protection:
- **Input**: Blocks prompt injection, credential extraction attempts
- **Output**: Redacts API keys, masks PII (emails, phones, cards, SSNs)
- **Scope**: Bot refuses off-topic or harmful requests

See `app/guardrails/policy.py` for the full policy specification.
