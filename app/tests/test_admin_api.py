from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.db.models import AdminRequest
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def _make_admin_request(id=1, status="pending", **kwargs):
    defaults = {
        "session_id": "sess-1",
        "customer_name": "Alice Smith",
        "car_number": "34-AB-123",
        "location": "Downtown Garage",
        "start_time": datetime(2026, 8, 1, 10, 0),
        "end_time": datetime(2026, 8, 1, 12, 0),
        "vehicle_type": "standard",
        "admin_note": None,
        "recorded": False,
        "created_at": datetime(2026, 7, 30, 10, 0),
        "decided_at": None,
    }
    defaults.update(kwargs)
    req = AdminRequest(id=id, status=status, **defaults)
    return req


class TestListPendingRequests:
    @patch("app.api.admin_routes.get_pending_requests")
    @patch("app.api.admin_routes.get_db")
    def test_returns_pending_list(self, mock_db_dep, mock_get_pending, client):
        mock_db = MagicMock()
        mock_db_dep.return_value = iter([mock_db])
        mock_get_pending.return_value = [_make_admin_request(id=1), _make_admin_request(id=2)]

        response = client.get("/admin/requests")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["requests"]) == 2

    @patch("app.api.admin_routes.get_pending_requests")
    @patch("app.api.admin_routes.get_db")
    def test_returns_empty_list(self, mock_db_dep, mock_get_pending, client):
        mock_db = MagicMock()
        mock_db_dep.return_value = iter([mock_db])
        mock_get_pending.return_value = []

        response = client.get("/admin/requests")
        assert response.status_code == 200
        assert response.json()["total"] == 0


class TestApproveEndpoint:
    @patch("app.api.admin_routes.record_approved_reservation")
    @patch("app.api.admin_routes.approve_request")
    @patch("app.api.admin_routes.get_db")
    def test_approve_success(self, mock_db_dep, mock_approve, mock_record, client):
        mock_db = MagicMock()
        mock_db_dep.return_value = iter([mock_db])
        approved = _make_admin_request(id=1, status="approved", decided_at=datetime.utcnow())
        mock_approve.return_value = approved
        mock_record.return_value = True

        response = client.post("/admin/requests/1/approve", json={"note": "OK"})
        assert response.status_code == 200
        assert response.json()["status"] == "approved"

    @patch("app.api.admin_routes.approve_request")
    @patch("app.api.admin_routes.get_db")
    def test_approve_not_found(self, mock_db_dep, mock_approve, client):
        mock_db = MagicMock()
        mock_db_dep.return_value = iter([mock_db])
        mock_approve.return_value = None

        response = client.post("/admin/requests/999/approve", json={})
        assert response.status_code == 400


class TestRefuseEndpoint:
    @patch("app.api.admin_routes.refuse_request")
    @patch("app.api.admin_routes.get_db")
    def test_refuse_success(self, mock_db_dep, mock_refuse, client):
        mock_db = MagicMock()
        mock_db_dep.return_value = iter([mock_db])
        refused = _make_admin_request(id=1, status="refused", decided_at=datetime.utcnow(), admin_note="No space")
        mock_refuse.return_value = refused

        response = client.post("/admin/requests/1/refuse", json={"note": "No space"})
        assert response.status_code == 200
        assert response.json()["status"] == "refused"
        assert response.json()["admin_note"] == "No space"

    @patch("app.api.admin_routes.refuse_request")
    @patch("app.api.admin_routes.get_db")
    def test_refuse_not_found(self, mock_db_dep, mock_refuse, client):
        mock_db = MagicMock()
        mock_db_dep.return_value = iter([mock_db])
        mock_refuse.return_value = None

        response = client.post("/admin/requests/999/refuse", json={})
        assert response.status_code == 400
