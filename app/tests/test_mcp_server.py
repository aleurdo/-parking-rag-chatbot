"""Tests for the MCP server (file writer with auth + idempotency)."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "mcp_server"))
import mcp_server.main as mcp_module


@pytest.fixture
def mcp_client():
    return TestClient(mcp_module.app)


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {mcp_module.MCP_API_TOKEN}"}


@pytest.fixture(autouse=True)
def set_output_file(tmp_path, monkeypatch):
    output_file = str(tmp_path / "reservations.txt")
    monkeypatch.setattr(mcp_module, "MCP_OUTPUT_FILE", output_file)
    return output_file


class TestMCPAuthentication:
    def test_requires_auth_header(self, mcp_client):
        response = mcp_client.post("/write", json={
            "reservation_id": 1,
            "customer_name": "Alice",
            "car_number": "34-AB-123",
            "start_time": "2026-08-01T10:00:00Z",
            "end_time": "2026-08-01T12:00:00Z",
        })
        assert response.status_code == 422

    def test_rejects_invalid_token(self, mcp_client):
        response = mcp_client.post(
            "/write",
            json={
                "reservation_id": 1,
                "customer_name": "Alice",
                "car_number": "34-AB-123",
                "start_time": "2026-08-01T10:00:00Z",
                "end_time": "2026-08-01T12:00:00Z",
            },
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert response.status_code == 403

    def test_accepts_valid_token(self, mcp_client, auth_headers):
        response = mcp_client.post(
            "/write",
            json={
                "reservation_id": 1,
                "customer_name": "Alice",
                "car_number": "34-AB-123",
                "start_time": "2026-08-01T10:00:00Z",
                "end_time": "2026-08-01T12:00:00Z",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestMCPFileWrite:
    def test_writes_correct_format(self, mcp_client, auth_headers, set_output_file):
        response = mcp_client.post(
            "/write",
            json={
                "reservation_id": 1,
                "customer_name": "Alice Smith",
                "car_number": "34-AB-123",
                "start_time": "2026-08-01T10:00:00Z",
                "end_time": "2026-08-01T12:00:00Z",
                "approval_time": "2026-07-30T14:15:00Z",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "written"

        content = Path(set_output_file).read_text()
        assert "Alice Smith" in content
        assert "34-AB-123" in content
        assert "2026-08-01T10:00:00Z - 2026-08-01T12:00:00Z" in content
        assert "[ID:1]" in content

    def test_idempotency_prevents_duplicate(self, mcp_client, auth_headers, set_output_file):
        payload = {
            "reservation_id": 42,
            "customer_name": "Bob",
            "car_number": "XY-999",
            "start_time": "2026-08-02T08:00:00Z",
            "end_time": "2026-08-02T10:00:00Z",
        }
        mcp_client.post("/write", json=payload, headers=auth_headers)
        response = mcp_client.post("/write", json=payload, headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["status"] == "skipped"
        assert response.json()["reason"] == "duplicate"

        content = Path(set_output_file).read_text()
        assert content.count("[ID:42]") == 1


class TestMCPValidation:
    def test_rejects_invalid_reservation_id(self, mcp_client, auth_headers):
        response = mcp_client.post(
            "/write",
            json={
                "reservation_id": -1,
                "customer_name": "Alice",
                "car_number": "34-AB-123",
                "start_time": "2026-08-01T10:00:00Z",
                "end_time": "2026-08-01T12:00:00Z",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_rejects_empty_name(self, mcp_client, auth_headers):
        response = mcp_client.post(
            "/write",
            json={
                "reservation_id": 1,
                "customer_name": "",
                "car_number": "34-AB-123",
                "start_time": "2026-08-01T10:00:00Z",
                "end_time": "2026-08-01T12:00:00Z",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestMCPHealth:
    def test_health_endpoint(self, mcp_client):
        response = mcp_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
