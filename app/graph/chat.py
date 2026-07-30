"""
Chat orchestration: ties together retrieval, generation, guardrails, and booking detection.
"""

import re
from datetime import datetime

from app.config import get_settings
from app.guardrails.filters import apply_guardrails, check_input_blocked, FilterResult
from app.rag.vector_store import search_similar
from app.graph.llm import generate_response


BOOKING_KEYWORDS = [
    "reserve", "book", "reservation", "booking", "park my car",
    "i want to park", "need a spot", "need parking",
]


class ChatSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history: list[dict] = []
        self.booking_state: dict | None = None

    def process_message(self, user_message: str) -> dict:
        settings = get_settings()

        if settings.guardrails_enabled:
            input_check = check_input_blocked(user_message)
            if input_check.is_blocked:
                return {
                    "response": (
                        "I'm sorry, but I can't process that request. "
                        "I can only help with ParkEase parking services, "
                        "booking, and general information."
                    ),
                    "blocked": True,
                    "reason": input_check.reason,
                    "sources": [],
                }

        if self.booking_state:
            return self._handle_booking_flow(user_message)

        if self._is_booking_intent(user_message):
            return self._start_booking(user_message)

        context_chunks = search_similar(user_message, top_k=5)

        raw_response = generate_response(
            query=user_message,
            context_chunks=context_chunks,
            conversation_history=self.history[-10:],
        )

        if settings.guardrails_enabled:
            filter_result, final_response = apply_guardrails(user_message, raw_response)
        else:
            final_response = raw_response

        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": final_response})

        sources = list({chunk["source"] for chunk in context_chunks[:3]})

        return {
            "response": final_response,
            "blocked": False,
            "sources": sources,
        }

    def _is_booking_intent(self, message: str) -> bool:
        msg_lower = message.lower()
        return any(kw in msg_lower for kw in BOOKING_KEYWORDS)

    def _start_booking(self, message: str) -> dict:
        self.booking_state = {
            "step": "collect_info",
            "data": {
                "customer_name": None,
                "customer_email": None,
                "license_plate": None,
                "location": None,
                "date": None,
                "time": None,
                "vehicle_type": "standard",
            },
        }
        response = (
            "I'd be happy to help you reserve a parking spot! "
            "I'll need a few details.\n\n"
            "Which location would you prefer?\n"
            "- Downtown Garage (123 Main Street)\n"
            "- Riverside Lot (45 River Road)\n"
            "- Airport Express Park (789 Terminal Way)\n\n"
            "Also, please provide:\n"
            "- Your name\n"
            "- Email address\n"
            "- License plate number\n"
            "- Date and time\n"
            "- Vehicle type (standard, EV, motorcycle)"
        )
        self.history.append({"role": "user", "content": message})
        self.history.append({"role": "assistant", "content": response})
        return {"response": response, "blocked": False, "sources": [], "booking_active": True}

    def _handle_booking_flow(self, message: str) -> dict:
        data = self.booking_state["data"]
        msg_lower = message.lower()

        if "cancel" in msg_lower or "nevermind" in msg_lower:
            self.booking_state = None
            response = "No problem! Reservation cancelled. How else can I help?"
            self.history.append({"role": "user", "content": message})
            self.history.append({"role": "assistant", "content": response})
            return {"response": response, "blocked": False, "sources": []}

        self._extract_booking_info(message)

        missing = [k for k, v in data.items() if v is None and k != "vehicle_type"]
        if not missing:
            return self._confirm_booking()

        missing_labels = {
            "customer_name": "your name",
            "customer_email": "your email address",
            "license_plate": "your license plate number",
            "location": "preferred location",
            "date": "parking date",
            "time": "arrival time",
        }
        needed = [missing_labels.get(k, k) for k in missing[:2]]
        response = f"Thanks! I still need: {', '.join(needed)}. Please provide those."

        self.history.append({"role": "user", "content": message})
        self.history.append({"role": "assistant", "content": response})
        return {"response": response, "blocked": False, "sources": [], "booking_active": True}

    def _extract_booking_info(self, message: str) -> None:
        data = self.booking_state["data"]
        msg_lower = message.lower()

        if not data["location"]:
            if "downtown" in msg_lower:
                data["location"] = "Downtown Garage"
            elif "riverside" in msg_lower:
                data["location"] = "Riverside Lot"
            elif "airport" in msg_lower:
                data["location"] = "Airport Express Park"

        if not data["vehicle_type"] or data["vehicle_type"] == "standard":
            if "ev" in msg_lower or "electric" in msg_lower:
                data["vehicle_type"] = "ev"
            elif "motorcycle" in msg_lower or "bike" in msg_lower:
                data["vehicle_type"] = "motorcycle"

        email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}", message)
        if email_match and not data["customer_email"]:
            data["customer_email"] = email_match.group()

        plate_match = re.search(r"\b[A-Z]{2,3}[-\s]?\d{3,4}\b", message.upper())
        if plate_match and not data["license_plate"]:
            data["license_plate"] = plate_match.group()

        date_match = re.search(r"\d{4}-\d{2}-\d{2}", message)
        if date_match and not data["date"]:
            data["date"] = date_match.group()

        time_match = re.search(r"\d{1,2}:\d{2}\s*(AM|PM|am|pm)?", message)
        if time_match and not data["time"]:
            data["time"] = time_match.group()

        words = message.split()
        if not data["customer_name"] and len(words) >= 2:
            potential_name = []
            for word in words:
                clean = word.strip(",.!?")
                if clean.isalpha() and clean[0].isupper() and len(clean) > 1:
                    if clean.lower() not in {"downtown", "riverside", "airport", "ev", "standard", "motorcycle", "am", "pm"}:
                        potential_name.append(clean)
                if len(potential_name) == 2:
                    break
            if len(potential_name) == 2:
                data["customer_name"] = " ".join(potential_name)

    def _confirm_booking(self) -> dict:
        data = self.booking_state["data"]
        response = (
            f"Here's your reservation summary:\n\n"
            f"- **Name**: {data['customer_name']}\n"
            f"- **Email**: {data['customer_email']}\n"
            f"- **License Plate**: {data['license_plate']}\n"
            f"- **Location**: {data['location']}\n"
            f"- **Date**: {data['date']}\n"
            f"- **Time**: {data['time']}\n"
            f"- **Vehicle Type**: {data['vehicle_type']}\n\n"
            f"Would you like me to confirm this reservation? (yes/no)"
        )
        self.booking_state["step"] = "confirm"
        self.history.append({"role": "assistant", "content": response})
        return {"response": response, "blocked": False, "sources": [], "booking_active": True}


_sessions: dict[str, ChatSession] = {}


def get_or_create_session(session_id: str) -> ChatSession:
    if session_id not in _sessions:
        _sessions[session_id] = ChatSession(session_id)
    return _sessions[session_id]
