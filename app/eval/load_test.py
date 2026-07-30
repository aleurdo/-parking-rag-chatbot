"""
Load test using Locust for performance evaluation.
Run with: locust -f app/eval/load_test.py --host=http://localhost:8000
"""

from locust import HttpUser, between, task


class ParkEaseChatUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def chat_faq(self):
        self.client.post(
            "/chat",
            json={
                "message": "What are your parking rates?",
                "session_id": f"load_test_{self.environment.runner.user_count}",
            },
        )

    @task(2)
    def chat_location(self):
        self.client.post(
            "/chat",
            json={
                "message": "Where is the Downtown Garage?",
                "session_id": f"load_test_loc_{self.environment.runner.user_count}",
            },
        )

    @task(1)
    def health_check(self):
        self.client.get("/health")

    @task(1)
    def admin_list(self):
        self.client.get("/admin/requests")

    @task(1)
    def reserve_status(self):
        self.client.get("/reserve/status/1")


class MCPUser(HttpUser):
    wait_time = between(0.5, 1)

    @task
    def write_reservation(self):
        self.client.post(
            "/write",
            json={
                "reservation_id": 99999,
                "customer_name": "Load Test",
                "car_number": "LT-000",
                "start_time": "2026-08-01T10:00:00Z",
                "end_time": "2026-08-01T12:00:00Z",
            },
            headers={"Authorization": "Bearer mcp-secret-token"},
        )
