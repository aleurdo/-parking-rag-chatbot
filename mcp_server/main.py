import os
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Header
from pydantic import BaseModel, Field

app = FastAPI(title="MCP File Writer", version="1.0.0")

MCP_API_TOKEN = os.getenv("MCP_API_TOKEN", "mcp-secret-token")
MCP_OUTPUT_FILE = os.getenv("MCP_OUTPUT_FILE", "/data/approved_reservations.txt")


class WriteRequest(BaseModel):
    reservation_id: int = Field(..., gt=0)
    customer_name: str = Field(..., min_length=1, max_length=100)
    car_number: str = Field(..., min_length=1, max_length=20)
    start_time: str
    end_time: str
    approval_time: str | None = None


def verify_token(authorization: str = Header(...)) -> None:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization[7:]
    import mcp_server.main as _self
    if token != _self.MCP_API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")


def _safe_path(file_path: str) -> Path:
    path = Path(file_path).resolve()
    allowed_dir = Path(file_path).resolve().parent
    if ".." in str(file_path):
        raise HTTPException(status_code=403, detail="Path traversal not allowed")
    return path


def _is_duplicate(path: Path, reservation_id: int) -> bool:
    if not path.exists():
        return False
    marker = f"[ID:{reservation_id}]"
    return marker in path.read_text(encoding="utf-8")


@app.post("/write")
def write_reservation(request: WriteRequest, _: None = Depends(verify_token)):
    import mcp_server.main as _self
    path = _safe_path(_self.MCP_OUTPUT_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)

    if _is_duplicate(path, request.reservation_id):
        return {"status": "skipped", "reason": "duplicate", "reservation_id": request.reservation_id}

    approval_time = request.approval_time or datetime.utcnow().isoformat() + "Z"
    period = f"{request.start_time} - {request.end_time}"
    line = f"{request.customer_name} | {request.car_number} | {period} | {approval_time} [ID:{request.reservation_id}]\n"

    with open(path, "a", encoding="utf-8") as f:
        f.write(line)

    return {"status": "written", "reservation_id": request.reservation_id}


@app.get("/health")
def health():
    return {"status": "ok", "service": "mcp-server"}
