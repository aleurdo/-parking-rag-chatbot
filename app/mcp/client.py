import httpx

from app.config import get_settings
from app.db.models import AdminRequest


def record_approved_reservation(request: AdminRequest) -> bool:
    settings = get_settings()
    payload = {
        "reservation_id": request.id,
        "customer_name": request.customer_name,
        "car_number": request.car_number,
        "start_time": request.start_time.isoformat() + "Z",
        "end_time": request.end_time.isoformat() + "Z",
        "approval_time": request.decided_at.isoformat() + "Z" if request.decided_at else None,
    }
    response = httpx.post(
        f"{settings.mcp_base_url}/write",
        json=payload,
        headers={"Authorization": f"Bearer {settings.mcp_api_token}"},
        timeout=30.0,
    )
    response.raise_for_status()
    return True
