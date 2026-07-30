from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import AdminRequest


def create_admin_request(
    db: Session,
    session_id: str,
    customer_name: str,
    car_number: str,
    location: str,
    start_time: datetime,
    end_time: datetime,
    vehicle_type: str = "standard",
) -> AdminRequest:
    request = AdminRequest(
        session_id=session_id,
        customer_name=customer_name,
        car_number=car_number,
        location=location,
        start_time=start_time,
        end_time=end_time,
        vehicle_type=vehicle_type,
        status="pending",
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def get_pending_requests(db: Session) -> list[AdminRequest]:
    return db.query(AdminRequest).filter(AdminRequest.status == "pending").all()


def get_admin_request_by_id(db: Session, request_id: int) -> AdminRequest | None:
    return db.query(AdminRequest).filter(AdminRequest.id == request_id).first()


def approve_request(db: Session, request_id: int, admin_note: str | None = None) -> AdminRequest | None:
    request = get_admin_request_by_id(db, request_id)
    if not request or request.status != "pending":
        return None
    request.status = "approved"
    request.decided_at = datetime.utcnow()
    request.admin_note = admin_note
    db.commit()
    db.refresh(request)
    return request


def refuse_request(db: Session, request_id: int, admin_note: str | None = None) -> AdminRequest | None:
    request = get_admin_request_by_id(db, request_id)
    if not request or request.status != "pending":
        return None
    request.status = "refused"
    request.decided_at = datetime.utcnow()
    request.admin_note = admin_note
    db.commit()
    db.refresh(request)
    return request


def mark_as_recorded(db: Session, request_id: int) -> AdminRequest | None:
    request = get_admin_request_by_id(db, request_id)
    if not request:
        return None
    request.recorded = True
    db.commit()
    db.refresh(request)
    return request
