from datetime import datetime

from pydantic import BaseModel, Field


class AdminRequestOut(BaseModel):
    id: int
    session_id: str
    status: str
    customer_name: str
    car_number: str
    location: str
    start_time: datetime
    end_time: datetime
    vehicle_type: str
    admin_note: str | None = None
    recorded: bool = False
    created_at: datetime
    decided_at: datetime | None = None

    class Config:
        from_attributes = True


class AdminDecisionRequest(BaseModel):
    note: str | None = Field(default=None, max_length=500)


class AdminRequestListResponse(BaseModel):
    requests: list[AdminRequestOut]
    total: int


class ReserveStatusResponse(BaseModel):
    request_id: int
    status: str
    admin_note: str | None = None
    decided_at: datetime | None = None
