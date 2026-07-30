from pydantic import BaseModel, Field
from datetime import datetime


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(default="default")


class ChatResponse(BaseModel):
    response: str
    sources: list[str] = []
    blocked: bool = False
    reason: str | None = None
    booking_active: bool = False


class IngestRequest(BaseModel):
    docs_directory: str = "data/static_docs"


class IngestResponse(BaseModel):
    status: str
    chunks_ingested: int


class ReservationRequest(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    customer_email: str
    license_plate: str = Field(..., min_length=3, max_length=20)
    location_name: str
    vehicle_type: str = "standard"
    start_time: datetime
    end_time: datetime | None = None


class ReservationResponse(BaseModel):
    reservation_id: int
    status: str
    message: str


class HealthResponse(BaseModel):
    status: str
    version: str
    services: dict[str, str]
