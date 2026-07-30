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
