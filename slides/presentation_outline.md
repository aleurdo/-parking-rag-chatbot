# ParkEase RAG Chatbot - Presentation Outline

## Slide 1: Title
- **ParkEase RAG Chatbot** - Stage 1
- Intelligent Parking Assistant with Retrieval-Augmented Generation
- [Screenshot: Chat interaction example]

## Slide 2: Architecture Overview
- High-level system diagram
- Components: FastAPI → Guardrails → RAG Pipeline → LLM
- Data stores: Qdrant (static) + PostgreSQL (dynamic)
- [Screenshot: Architecture diagram from README]

## Slide 3: Data Pipeline
- Document ingestion flow:
  - Markdown docs → Parse → Chunk by headers → Embed → Store in Qdrant
- Dynamic data in PostgreSQL:
  - Locations, zones, availability, reservations
- [Screenshot: Ingestion API call + Qdrant dashboard]

## Slide 4: RAG Flow
- User query → Embed → Vector search (top-5) → Context assembly → LLM prompt → Response
- Source citations included in answers
- Multi-turn conversation support via session state
- [Screenshot: /chat request/response with sources]

## Slide 5: Reservation Flow
- Multi-turn booking conversation
- Information extraction: name, email, plate, location, date, vehicle type
- Availability check against PostgreSQL
- Confirmation and booking creation
- [Screenshot: Booking conversation flow]

## Slide 6: Guardrails & Data Protection
- Input filtering: prompt injection, credential extraction attempts
- Output sanitization: API keys, PII masking (email, phone, cards)
- Policy-based blocking with clear refusal messages
- [Screenshot: Blocked request + redacted output examples]

## Slide 7: Evaluation Results
- Retrieval quality: Recall@5 and Precision@5 metrics
- 12-query labeled evaluation dataset
- Performance: Latency benchmarks (p50, p95, p99)
- Load testing results (Locust)
- [Screenshot: Evaluation metrics output]

## Slide 8: Testing & CI/CD
- Unit tests: 6 test modules, 30+ test cases
- Integration tests with live services
- GitHub Actions pipeline: lint → test → integration
- Docker Compose for one-command deployment
- [Screenshot: CI pipeline passing + test coverage]

## Slide 9: Technology Stack
| Layer | Technology |
|-------|-----------|
| API | FastAPI + Pydantic |
| Vector DB | Qdrant |
| SQL DB | PostgreSQL |
| Embeddings | OpenAI text-embedding-3-small |
| LLM | GPT-4o-mini |
| Guardrails | Regex + heuristic filters |
| Tests | pytest + httpx |
| CI/CD | GitHub Actions |
| Infra | Docker Compose |

## Slide 10: Next Steps (Stage 2)
- Presidio NLP-based PII detection (upgrade from regex)
- LangGraph for complex multi-step workflows
- Conversation memory persistence (Redis)
- Admin dashboard for knowledge base management
- Production deployment (Kubernetes / Cloud Run)
- Monitoring & observability (OpenTelemetry)

---

## Screenshots to Capture

1. `docker compose up` output showing all services starting
2. Health check response showing all services healthy
3. Ingest API call response
4. Chat interaction: pricing question with source citation
5. Chat interaction: booking flow (multi-turn)
6. Guardrails: blocked prompt injection attempt
7. Guardrails: redacted PII in output
8. pytest output with all tests passing
9. GitHub Actions CI pipeline (green)
10. Qdrant dashboard showing collection (localhost:6333/dashboard)
