"""
Chat session management: ties together the LangGraph orchestrator with session state.
"""

from app.graph.orchestrator import run_graph
from app.graph.state import GraphState, ReservationDraft


class ChatSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history: list[dict] = []
        self.state: GraphState = GraphState(session_id=session_id)

    def process_message(self, user_message: str) -> dict:
        self.state.user_message = user_message
        self.state.final_response = ""
        self.state.current_node = "user_agent"

        if self.state.intent != "reserve":
            self.state.intent = "chat"

        self.state = run_graph(self.state)

        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": self.state.final_response})

        result = {
            "response": self.state.final_response,
            "blocked": False,
            "sources": [],
        }

        if self.state.admin_request_id:
            result["admin_request_id"] = self.state.admin_request_id
            result["booking_active"] = True

        return result


_sessions: dict[str, ChatSession] = {}


def get_or_create_session(session_id: str) -> ChatSession:
    if session_id not in _sessions:
        _sessions[session_id] = ChatSession(session_id)
    return _sessions[session_id]
