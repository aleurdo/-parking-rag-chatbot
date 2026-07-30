from datetime import datetime
from unittest.mock import MagicMock

import pytest

from app.db.admin_repository import (
    approve_request,
    create_admin_request,
    get_admin_request_by_id,
    get_pending_requests,
    mark_as_recorded,
    refuse_request,
)
from app.db.models import AdminRequest


class TestCreateAdminRequest:
    def test_creates_request_with_correct_fields(self):
        mock_db = MagicMock()
        result = create_admin_request(
            db=mock_db,
            session_id="sess-1",
            customer_name="Alice Smith",
            car_number="34-AB-123",
            location="Downtown Garage",
            start_time=datetime(2026, 8, 1, 10, 0),
            end_time=datetime(2026, 8, 1, 12, 0),
            vehicle_type="standard",
        )
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_defaults_to_pending_status(self):
        mock_db = MagicMock()
        create_admin_request(
            db=mock_db,
            session_id="sess-1",
            customer_name="Bob",
            car_number="XY-999",
            location="Riverside Lot",
            start_time=datetime(2026, 8, 1, 10, 0),
            end_time=datetime(2026, 8, 1, 12, 0),
        )
        added_obj = mock_db.add.call_args[0][0]
        assert added_obj.status == "pending"


class TestGetPendingRequests:
    def test_returns_only_pending(self):
        mock_db = MagicMock()
        pending = [AdminRequest(id=1, status="pending"), AdminRequest(id=2, status="pending")]
        mock_db.query.return_value.filter.return_value.all.return_value = pending
        result = get_pending_requests(mock_db)
        assert len(result) == 2

    def test_returns_empty_list(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = get_pending_requests(mock_db)
        assert result == []


class TestApproveRequest:
    def test_approves_pending_request(self):
        mock_db = MagicMock()
        req = AdminRequest(id=1, status="pending")
        mock_db.query.return_value.filter.return_value.first.return_value = req
        result = approve_request(mock_db, 1, admin_note="Looks good")
        assert result.status == "approved"
        assert result.admin_note == "Looks good"
        assert result.decided_at is not None
        mock_db.commit.assert_called_once()

    def test_returns_none_for_already_decided(self):
        mock_db = MagicMock()
        req = AdminRequest(id=1, status="approved")
        mock_db.query.return_value.filter.return_value.first.return_value = req
        result = approve_request(mock_db, 1)
        assert result is None

    def test_returns_none_for_missing_request(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = approve_request(mock_db, 999)
        assert result is None


class TestRefuseRequest:
    def test_refuses_pending_request(self):
        mock_db = MagicMock()
        req = AdminRequest(id=1, status="pending")
        mock_db.query.return_value.filter.return_value.first.return_value = req
        result = refuse_request(mock_db, 1, admin_note="No availability")
        assert result.status == "refused"
        assert result.admin_note == "No availability"

    def test_returns_none_for_non_pending(self):
        mock_db = MagicMock()
        req = AdminRequest(id=1, status="refused")
        mock_db.query.return_value.filter.return_value.first.return_value = req
        result = refuse_request(mock_db, 1)
        assert result is None


class TestMarkAsRecorded:
    def test_marks_recorded(self):
        mock_db = MagicMock()
        req = AdminRequest(id=1, status="approved", recorded=False)
        mock_db.query.return_value.filter.return_value.first.return_value = req
        result = mark_as_recorded(mock_db, 1)
        assert result.recorded is True
        mock_db.commit.assert_called_once()
