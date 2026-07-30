"""
LangGraph-style orchestration pipeline.
Connects: User Agent → Admin Approval → MCP Recording
"""

import re
from datetime import datetime

from app.config import get_settings
from app.db.admin_repository import (
    create_admin_request,
    get_admin_request_by_id,
    mark_as_recorded,
)
from app.db.session import get_session_factory
from app.graph.state import GraphState, ReservationDraft
from app.guardrails.filters import check_input_blocked, apply_guardrails
from app.mcp.client import record_approved_reservation
from app.rag.vector_store import search_similar
from app.graph.llm import generate_response


BOOKING_KEYWORDS = [
    "reserve", "book", "reservation", "booking", "park my car",
    "i want to park", "need a spot", "need parking",
]

VALID_LOCATIONS = ["Downtown Garage", "Riverside Lot", "Airport Express Park"]


def user_agent_node(state: GraphState) -> GraphState:
    settings = get_settings()

    if settings.guardrails_enabled:
        input_check = check_input_blocked(state.user_message)
        if input_check.is_blocked:
            state.final_response = (
                "I'm sorry, but I can't process that request. "
                "I can only help with ParkEase parking services."
            )
            return state

    if _is_booking_intent(state.user_message):
        state.intent = "reserve"
        _extract_reservation_info(state)

        if state.reservation_draft.is_complete():
            validation_error = _validate_reservation(state.reservation_draft)
            if validation_error:
                state.final_response = validation_error
                return state
            state.current_node = "admin_approval"
            return admin_approval_node(state)

        missing = state.reservation_draft.missing_fields()
        state.final_response = (
            "I'd be happy to help you reserve a parking spot! "
            f"I still need the following:\n- " + "\n- ".join(missing[:3]) +
            "\n\nAvailable locations: Downtown Garage, Riverside Lot, Airport Express Park"
        )
        return state

    context_chunks = search_similar(state.user_message, top_k=3)
    raw_response = generate_response(
        query=state.user_message,
        context_chunks=context_chunks,
    )

    if settings.guardrails_enabled:
        _, final_response = apply_guardrails(state.user_message, raw_response)
    else:
        final_response = raw_response

    state.final_response = final_response
    return state


def admin_approval_node(state: GraphState) -> GraphState:
    draft = state.reservation_draft
    factory = get_session_factory()
    db = factory()
    try:
        admin_req = create_admin_request(
            db=db,
            session_id=state.session_id,
            customer_name=draft.customer_name,
            car_number=draft.car_number,
            location=draft.location,
            start_time=datetime.fromisoformat(draft.start_time),
            end_time=datetime.fromisoformat(draft.end_time),
            vehicle_type=draft.vehicle_type,
        )
        state.admin_request_id = admin_req.id
        state.admin_status = "pending"
        state.final_response = (
            f"Your reservation request has been submitted for admin approval.\n\n"
            f"**Request ID**: {admin_req.id}\n"
            f"**Name**: {draft.customer_name}\n"
            f"**Car**: {draft.car_number}\n"
            f"**Location**: {draft.location}\n"
            f"**Period**: {draft.start_time} to {draft.end_time}\n\n"
            f"You can check the status with: GET /reserve/status/{admin_req.id}"
        )
    finally:
        db.close()
    return state


def record_node(state: GraphState) -> GraphState:
    if not state.admin_request_id:
        state.final_response = "No reservation to record."
        return state

    factory = get_session_factory()
    db = factory()
    try:
        request = get_admin_request_by_id(db, state.admin_request_id)
        if not request or request.status != "approved":
            state.final_response = "Reservation is not approved yet."
            return state

        if request.recorded:
            state.final_response = "Reservation already recorded."
            return state

        try:
            record_approved_reservation(request)
            mark_as_recorded(db, request.id)
            state.final_response = (
                f"Reservation #{request.id} has been approved and recorded. "
                f"Your spot at {request.location} is confirmed!"
            )
        except Exception as e:
            state.final_response = (
                f"Reservation #{request.id} is approved but recording failed. "
                f"Please contact support."
            )
    finally:
        db.close()
    return state


def run_graph(state: GraphState) -> GraphState:
    if state.intent == "status" and state.admin_request_id:
        return _check_status(state)
    state = user_agent_node(state)
    if state.current_node == "admin_approval" and state.admin_status == "pending":
        pass
    return state


def _check_status(state: GraphState) -> GraphState:
    factory = get_session_factory()
    db = factory()
    try:
        request = get_admin_request_by_id(db, state.admin_request_id)
        if not request:
            state.final_response = "Request not found."
            return state
        if request.status == "pending":
            state.final_response = f"Request #{request.id} is still pending admin approval."
        elif request.status == "approved":
            if not request.recorded:
                state = record_node(state)
            else:
                state.final_response = (
                    f"Request #{request.id} is APPROVED and recorded. "
                    f"Your parking at {request.location} is confirmed!"
                )
        elif request.status == "refused":
            note = f" Reason: {request.admin_note}" if request.admin_note else ""
            state.final_response = f"Request #{request.id} was REFUSED.{note}"
    finally:
        db.close()
    return state


def _is_booking_intent(message: str) -> bool:
    msg_lower = message.lower()
    return any(kw in msg_lower for kw in BOOKING_KEYWORDS)


def _extract_reservation_info(state: GraphState) -> None:
    message = state.user_message
    draft = state.reservation_draft
    msg_lower = message.lower()

    if not draft.location:
        if "downtown" in msg_lower:
            draft.location = "Downtown Garage"
        elif "riverside" in msg_lower:
            draft.location = "Riverside Lot"
        elif "airport" in msg_lower:
            draft.location = "Airport Express Park"

    if "ev" in msg_lower or "electric" in msg_lower:
        draft.vehicle_type = "ev"
    elif "motorcycle" in msg_lower or "bike" in msg_lower:
        draft.vehicle_type = "motorcycle"

    plate_match = re.search(r"\b\d{2,3}[-\s]?[A-Z]{2,3}[-\s]?\d{2,4}\b", message.upper())
    if plate_match and not draft.car_number:
        draft.car_number = plate_match.group()

    datetime_matches = re.findall(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", message)
    if len(datetime_matches) >= 2:
        draft.start_time = datetime_matches[0]
        draft.end_time = datetime_matches[1]
    elif len(datetime_matches) == 1 and not draft.start_time:
        draft.start_time = datetime_matches[0]

    words = message.split()
    if not draft.customer_name:
        potential_name = []
        for word in words:
            clean = word.strip(",.!?")
            if clean.isalpha() and clean[0].isupper() and len(clean) > 1:
                if clean.lower() not in {
                    "downtown", "riverside", "airport", "ev", "standard",
                    "motorcycle", "am", "pm", "reserve", "book", "parking",
                    "i", "the", "my", "need",
                }:
                    potential_name.append(clean)
            if len(potential_name) == 2:
                break
        if len(potential_name) >= 2:
            draft.customer_name = " ".join(potential_name[:2])


def _validate_reservation(draft: ReservationDraft) -> str | None:
    if draft.location not in VALID_LOCATIONS:
        return f"Invalid location. Choose from: {', '.join(VALID_LOCATIONS)}"
    try:
        start = datetime.fromisoformat(draft.start_time)
        end = datetime.fromisoformat(draft.end_time)
    except (ValueError, TypeError):
        return "Invalid date/time format. Use YYYY-MM-DDTHH:MM format."
    if end <= start:
        return "End time must be after start time."
    if start < datetime.utcnow():
        return "Start time cannot be in the past."
    return None
