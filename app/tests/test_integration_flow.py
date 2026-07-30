"""
Integration test: full flow user -> admin pending -> approve -> file written.
Uses mocks for LLM and real test fixtures for DB/MCP logic.
"""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.db.admin_repository import (
    approve_request,
    create_admin_request,
    get_admin_request_by_id,
    mark_as_recorded,
)
from app.db.models import AdminRequest
from app.graph.orchestrator import admin_approval_node, record_node, user_agent_node
from app.graph.state import GraphState, ReservationDraft


class TestFullReservationFlow:
    @patch("app.graph.orchestrator.get_session_factory")
    @patch("app.graph.orchestrator.check_input_blocked")
    def test_user_submits_complete_reservation(self, mock_check, mock_factory):
        from app.guardrails.filters import FilterResult
        mock_check.return_value = FilterResult(is_blocked=False)

        mock_db = MagicMock()
        mock_factory.return_value = MagicMock(return_value=mock_db)

        mock_db.refresh = MagicMock(side_effect=lambda x: setattr(x, 'id', 7))

        future = datetime.utcnow() + timedelta(days=2)
        start = future.strftime("%Y-%m-%dT%H:%M")
        end = (future + timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M")

        state = GraphState(
            session_id="flow-test",
            user_message=(
                f"I want to reserve at Downtown Garage. "
                f"Alice Smith, car 34-AB-123, from {start} to {end}"
            ),
        )
        result = user_agent_node(state)

        assert result.admin_status == "pending"
        assert "submitted" in result.final_response.lower()
        mock_db.add.assert_called_once()

    @patch("app.graph.orchestrator.mark_as_recorded")
    @patch("app.graph.orchestrator.record_approved_reservation")
    @patch("app.graph.orchestrator.get_session_factory")
    def test_approved_request_gets_recorded(self, mock_factory, mock_record_mcp, mock_mark):
        mock_db = MagicMock()
        mock_factory.return_value = MagicMock(return_value=mock_db)

        approved_req = MagicMock()
        approved_req.id = 7
        approved_req.status = "approved"
        approved_req.recorded = False
        approved_req.location = "Downtown Garage"
        mock_db.query.return_value.filter.return_value.first.return_value = approved_req
        mock_record_mcp.return_value = True
        mock_mark.return_value = approved_req

        state = GraphState(admin_request_id=7)
        result = record_node(state)

        assert "approved and recorded" in result.final_response
        mock_record_mcp.assert_called_once_with(approved_req)
        mock_mark.assert_called_once()

    @patch("app.graph.orchestrator.get_session_factory")
    def test_refused_request_notifies_user(self, mock_factory):
        mock_db = MagicMock()
        mock_factory.return_value = MagicMock(return_value=mock_db)

        refused_req = MagicMock()
        refused_req.id = 8
        refused_req.status = "refused"
        refused_req.recorded = False
        refused_req.admin_note = "Lot full"
        refused_req.location = "Riverside Lot"
        mock_db.query.return_value.filter.return_value.first.return_value = refused_req

        state = GraphState(admin_request_id=8, intent="status")
        from app.graph.orchestrator import _check_status
        result = _check_status(state)

        assert "REFUSED" in result.final_response
        assert "Lot full" in result.final_response
