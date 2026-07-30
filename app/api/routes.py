from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    ReservationRequest,
    ReservationResponse,
)
from app.api.admin_schemas import ReserveStatusResponse
from app.db.admin_repository import get_admin_request_by_id
from app.db.repository import (
    check_availability,
    create_reservation,
    get_location_by_name,
    get_zones_for_location,
)
from app.db.session import get_db
from app.graph.chat import get_or_create_session
from app.rag.chunker import load_documents
from app.rag.vector_store import ingest_chunks

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check():
    services = {}
    try:
        from app.rag.vector_store import get_qdrant_client
        client = get_qdrant_client()
        client.get_collections()
        services["qdrant"] = "healthy"
    except Exception:
        services["qdrant"] = "unavailable"

    try:
        from sqlalchemy import text
        from app.db.session import get_engine
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        services["postgres"] = "healthy"
    except Exception:
        services["postgres"] = "unavailable"

    try:
        import httpx
        from app.config import get_settings
        settings = get_settings()
        resp = httpx.get(f"{settings.mcp_base_url}/health", timeout=5.0)
        services["mcp_server"] = "healthy" if resp.status_code == 200 else "unavailable"
    except Exception:
        services["mcp_server"] = "unavailable"

    return HealthResponse(
        status="ok",
        version="2.0.0",
        services=services,
    )


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    session = get_or_create_session(request.session_id)
    result = session.process_message(request.message)
    return ChatResponse(
        response=result["response"],
        sources=result.get("sources", []),
        blocked=result.get("blocked", False),
        reason=result.get("reason"),
        booking_active=result.get("booking_active", False),
        admin_request_id=result.get("admin_request_id"),
    )


@router.post("/ingest", response_model=IngestResponse)
def ingest_documents(request: IngestRequest):
    docs_path = Path(request.docs_directory)
    if not docs_path.exists():
        raise HTTPException(status_code=400, detail=f"Directory not found: {request.docs_directory}")

    chunks = load_documents(docs_path)
    if not chunks:
        raise HTTPException(status_code=400, detail="No documents found to ingest")

    count = ingest_chunks(chunks)
    return IngestResponse(status="success", chunks_ingested=count)


@router.post("/reserve", response_model=ReservationResponse)
def make_reservation(request: ReservationRequest, db: Session = Depends(get_db)):
    location = get_location_by_name(db, request.location_name)
    if not location:
        raise HTTPException(status_code=404, detail=f"Location not found: {request.location_name}")

    zones = get_zones_for_location(db, location.id, request.vehicle_type)
    if not zones:
        raise HTTPException(
            status_code=404,
            detail=f"No {request.vehicle_type} zones at {location.name}",
        )

    zone = zones[0]
    available = check_availability(db, zone.id, request.start_time.date())
    if available <= 0:
        raise HTTPException(
            status_code=409,
            detail=f"No spaces available at {location.name} on {request.start_time.date()}",
        )

    reservation = create_reservation(
        db=db,
        location_id=location.id,
        zone_id=zone.id,
        customer_name=request.customer_name,
        customer_email=request.customer_email,
        license_plate=request.license_plate,
        vehicle_type=request.vehicle_type,
        start_time=request.start_time,
        end_time=request.end_time,
    )

    return ReservationResponse(
        reservation_id=reservation.id,
        status="confirmed",
        message=f"Reservation confirmed at {location.name}. Your spot is reserved!",
    )


@router.get("/reserve/status/{request_id}", response_model=ReserveStatusResponse)
def reservation_status(request_id: int, db: Session = Depends(get_db)):
    request = get_admin_request_by_id(db, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Reservation request not found")
    return ReserveStatusResponse(
        request_id=request.id,
        status=request.status,
        admin_note=request.admin_note,
        decided_at=request.decided_at,
    )
