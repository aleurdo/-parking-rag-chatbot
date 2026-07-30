from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.admin_schemas import (
    AdminDecisionRequest,
    AdminRequestListResponse,
    AdminRequestOut,
    ReserveStatusResponse,
)
from app.db.admin_repository import (
    approve_request,
    get_admin_request_by_id,
    get_pending_requests,
    refuse_request,
)
from app.db.session import get_db
from app.mcp.client import record_approved_reservation

admin_router = APIRouter(prefix="/admin", tags=["admin"])


@admin_router.get("/requests", response_model=AdminRequestListResponse)
def list_pending_requests(db: Session = Depends(get_db)):
    requests = get_pending_requests(db)
    return AdminRequestListResponse(
        requests=[AdminRequestOut.model_validate(r) for r in requests],
        total=len(requests),
    )


@admin_router.get("/requests/{request_id}", response_model=AdminRequestOut)
def get_request_detail(request_id: int, db: Session = Depends(get_db)):
    request = get_admin_request_by_id(db, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Admin request not found")
    return AdminRequestOut.model_validate(request)


@admin_router.post("/requests/{request_id}/approve", response_model=AdminRequestOut)
def approve_admin_request(
    request_id: int,
    body: AdminDecisionRequest = AdminDecisionRequest(),
    db: Session = Depends(get_db),
):
    request = approve_request(db, request_id, admin_note=body.note)
    if not request:
        raise HTTPException(
            status_code=400,
            detail="Request not found or not in pending status",
        )
    try:
        record_approved_reservation(request)
    except Exception:
        pass
    return AdminRequestOut.model_validate(request)


@admin_router.post("/requests/{request_id}/refuse", response_model=AdminRequestOut)
def refuse_admin_request(
    request_id: int,
    body: AdminDecisionRequest = AdminDecisionRequest(),
    db: Session = Depends(get_db),
):
    request = refuse_request(db, request_id, admin_note=body.note)
    if not request:
        raise HTTPException(
            status_code=400,
            detail="Request not found or not in pending status",
        )
    return AdminRequestOut.model_validate(request)
