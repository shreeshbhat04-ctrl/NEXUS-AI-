from dataclasses import dataclass
from datetime import date
from uuid import uuid4

import logging

from nexus_ai.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class TicketResult:
    ticket_id: str
    status: str
    external_url: str | None = None


@dataclass
class RoutineTask:
    task_id: str
    name: str
    completed: bool
    source: str = "Internal"
    title: str | None = None
    short_summary: str | None = None
    full_details: str | None = None
    due_at: str | None = None
    due_on: str | None = None
    notes: str | None = None


class TicketingAdapter:
    def create_review_ticket(
        self,
        patient_id: int,
        summary: str,
        case_type: str,
        doctor_name: str | None = None,
        urgency: str | None = None,
    ) -> TicketResult:
        raise NotImplementedError

    def list_routine_tasks(self) -> list[RoutineTask]:
        raise NotImplementedError

    def list_workspace_users(self) -> list[dict[str, str | None]]:
        raise NotImplementedError


class MockTicketingAdapter(TicketingAdapter):
    def create_review_ticket(
        self,
        patient_id: int,
        summary: str,
        case_type: str,
        doctor_name: str | None = None,
        urgency: str | None = None,
    ) -> TicketResult:
        _ = (patient_id, summary, case_type, doctor_name, urgency)
        ticket_id = f"CQ-{str(uuid4())[:8].upper()}"
        return TicketResult(ticket_id=ticket_id, status="created")

    def list_routine_tasks(self) -> list[RoutineTask]:
        return [
            RoutineTask(
                task_id="mock-1",
                name="Morning medication reminder",
                completed=False,
                title="Morning medication reminder",
                short_summary="Morning dose check-in.",
                full_details="Check whether the patient took the morning dose.",
                due_at=date.today().isoformat(),
                due_on=date.today().isoformat(),
                notes="Check whether the patient took the morning dose.",
            ),
            RoutineTask(
                task_id="mock-2",
                name="Follow-up symptom check",
                completed=False,
                title="Follow-up symptom check",
                short_summary="Brief symptom follow-up is due today.",
                full_details="Ask how the patient is feeling today.",
                due_at=date.today().isoformat(),
                due_on=date.today().isoformat(),
                notes="Ask how the patient is feeling today.",
            ),
        ]

    def list_workspace_users(self) -> list[dict[str, str | None]]:
        return [
            {
                "gid": "mock-doctor-1",
                "name": "Dr surgeon",
                "email": "doctor@example.com",
            }
        ]


def build_ticketing_adapter() -> TicketingAdapter:
    return MockTicketingAdapter()


def _short_summary(notes: str | None, fallback: str, max_length: int = 96) -> str:
    if notes:
        normalized = " ".join(notes.split())
        if len(normalized) <= max_length:
            return normalized
        return normalized[: max_length - 3].rstrip() + "..."
    return fallback
