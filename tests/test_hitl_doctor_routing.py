from nexus_ai.agents.hitl import HITLAgent
from nexus_ai.db.bootstrap import init_database
from nexus_ai.db.session import SessionLocal


class CapturingTicketingAdapter:
    def __init__(self) -> None:
        self.last_request: dict | None = None

    def create_review_ticket(self, **kwargs):
        self.last_request = kwargs

        class Result:
            ticket_id = "task-456"
            status = "created"
            external_url = "https://app.asana.com/0/project/task-456"

        return Result()

    def list_routine_tasks(self):
        return []


def test_hitl_case_stores_selected_doctor_context_and_routes_ticket() -> None:
    init_database()
    ticketing = CapturingTicketingAdapter()
    agent = HITLAgent(ticketing_adapter=ticketing)

    with SessionLocal() as db:
        case = agent.create_case(
            db=db,
            patient_id=2,
            case_type="doctor_review",
            summary="Review care plan",
            doctor_id=3,
            doctor_name="Dr surgeon",
            doctor_email="sreeshhb@gmail.com",
            doctor_asana_gid="1214276322986923",
            urgency="high",
        )

    assert ticketing.last_request is not None
    assert ticketing.last_request["doctor_asana_gid"] == "1214276322986923"
    assert ticketing.last_request["doctor_name"] == "Dr surgeon"
    assert ticketing.last_request["urgency"] == "high"
    assert case.doctor_id == 3
    assert case.doctor_name == "Dr surgeon"
    assert case.doctor_email == "sreeshhb@gmail.com"
    assert case.doctor_asana_gid == "1214276322986923"
