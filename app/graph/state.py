from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ReservationDraft:
    customer_name: str | None = None
    car_number: str | None = None
    location: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    vehicle_type: str = "standard"

    def is_complete(self) -> bool:
        return all([self.customer_name, self.car_number, self.location, self.start_time, self.end_time])

    def missing_fields(self) -> list[str]:
        labels = {
            "customer_name": "your full name",
            "car_number": "your car/license plate number",
            "location": "preferred parking location",
            "start_time": "reservation start date/time (YYYY-MM-DDTHH:MM)",
            "end_time": "reservation end date/time (YYYY-MM-DDTHH:MM)",
        }
        return [labels[k] for k in ["customer_name", "car_number", "location", "start_time", "end_time"]
                if getattr(self, k) is None]


@dataclass
class GraphState:
    session_id: str = ""
    user_message: str = ""
    reservation_draft: ReservationDraft = field(default_factory=ReservationDraft)
    admin_request_id: int | None = None
    admin_status: str | None = None
    final_response: str = ""
    current_node: str = "user_agent"
    intent: Literal["chat", "reserve", "status"] = "chat"
