from types import SimpleNamespace

from nexus_ai.adapters.ticketing import MockTicketingAdapter
from nexus_ai.agents.orchestrator import Orchestrator
from nexus_ai.api.models import PatientIntakeRequest
from nexus_ai.services.brain import BrainCondition, BrainPatientProfile
from nexus_ai.db.bootstrap import init_database
from nexus_ai.db.session import SessionLocal


class StubBrainGateway:
    def healthcheck(self):
        return {"status": "ok"}

    def get_patient_profile(self, patient_id: int):
        return BrainPatientProfile(
            id=patient_id,
            full_name="Asha Rao",
            preferred_language="en",
            summary="summary",
        )

    def get_relevant_conditions(self, patient_id: int):
        _ = patient_id
        return [BrainCondition(id=1, patient_id=1, name="IBS", condition_type="chronic", last_updated=None, notes=None)]


class StubIntegrations:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict]] = []
        self.last_sent_email: dict | None = None

    def upload_document(self, **kwargs):
        _ = kwargs
        return {"id": "drive-1", "webViewLink": "https://drive.example/doc"}

    def store_medical_memory(self, **kwargs):
        _ = kwargs
        return {"memory_id": 1, "patient_id": 1, "source_type": "document_intake_flow", "modality": "text", "embedding_model": "mock", "summary_text": "summary", "live_embedding_used": False, "vector_store_synced": False}

    def search_nearby_pharmacies(self, location_query: str):
        return {"provider": "mock", "pharmacies": [{"name": f"{location_query} Pharmacy"}]}

    def create_calendar_event(self, **kwargs):
        _ = kwargs
        return {"id": "cal-1", "htmlLink": "https://calendar.example/event"}

    def log_integration_event(self, event_type: str, payload: dict):
        self.events.append((event_type, payload))
        return {"logged": True, "event_id": "evt-1", "provider": "mock"}

    def list_health_emails(self, credentials=None, max_results: int = 5):
        _ = credentials, max_results
        return [{"subject": "Lab report ready"}, {"subject": "Prescription update"}]

    def send_care_email(self, to: str, subject: str, body_html: str, credentials=None):
        _ = credentials
        self.last_sent_email = {
            "to": to,
            "subject": subject,
            "body_html": body_html,
        }
        return {"sent": True, "message_id": f"msg-for-{to}", "error": None}

    def list_drive_files(self, credentials=None, max_results: int = 5):
        _ = credentials, max_results
        return [
            {"name": "Prescription-April.pdf", "webViewLink": "https://drive.example/prescription-april"},
            {"name": "Lab-Results.pdf", "webViewLink": "https://drive.example/lab-results"},
        ]


def test_build_daily_checkin_returns_message_and_tasks() -> None:
    orchestrator = Orchestrator(brain_gateway=StubBrainGateway())
    orchestrator.routine.ticketing_adapter = MockTicketingAdapter()
    result = orchestrator.build_daily_checkin(patient_id=1)
    assert "Asha Rao" in result["message"]
    assert result["routine_tasks"]


def test_orchestration_manifest_exposes_agent_roles() -> None:
    orchestrator = Orchestrator(brain_gateway=StubBrainGateway())
    orchestrator.routine.ticketing_adapter = MockTicketingAdapter()
    manifest = orchestrator.get_orchestration_manifest(patient_id=1)
    assert "communication_agent" in manifest["agent_manifest"]
    assert "document_agent" in manifest["agent_manifest"]
    assert "medical_text_query" in manifest["trigger_manifest"]


def test_route_conversation_uses_gemini_for_general_support() -> None:
    orchestrator = Orchestrator(brain_gateway=StubBrainGateway())
    result = orchestrator.route_conversation(patient_id=1, message="I feel a bit stressed today and just need some support.")
    assert result["primary_model"] == orchestrator.model_routing.settings.gemini_fast_model_id
    assert result["route_type"] == "supportive_conversation"


def test_route_conversation_uses_medgemma_for_medical_text() -> None:
    orchestrator = Orchestrator(brain_gateway=StubBrainGateway())
    result = orchestrator.route_conversation(patient_id=1, message="I have fever and stomach pain after taking my medicine.")
    assert result["primary_model"] == orchestrator.model_routing.settings.medgemma_model_id
    assert result["route_type"] == "medical_text"


def test_route_conversation_can_create_calendar_follow_up() -> None:
    init_database()
    orchestrator = Orchestrator(brain_gateway=StubBrainGateway())
    orchestrator.integrations = StubIntegrations()
    orchestrator.communications.build_conversation_plan = lambda message, profile=None: {  # type: ignore[method-assign]
        "message": "I’m with you.",
        "route_type": "medical_text",
        "primary_model": orchestrator.model_routing.settings.medgemma_model_id,
        "support_model": orchestrator.model_routing.settings.gemini_fast_model_id,
        "reason": "Medical request detected.",
        "suggested_response_style": "calm",
        "execution_plan": ["Respond to the patient."],
    }

    with SessionLocal() as db:
        result = orchestrator.route_conversation(
            patient_id=1,
            message="Can you book a doctor appointment for me?",
            db=db,
        )

    assert "follow-up appointment" in result["message"]
    assert "calendar.example" in result["message"]


def test_route_conversation_can_read_health_emails() -> None:
    init_database()
    orchestrator = Orchestrator(brain_gateway=StubBrainGateway())
    orchestrator.integrations = StubIntegrations()
    orchestrator.communications.build_conversation_plan = lambda message, profile=None: {  # type: ignore[method-assign]
        "message": "I checked for you.",
        "route_type": "general_conversation",
        "primary_model": orchestrator.model_routing.settings.gemini_fast_model_id,
        "support_model": None,
        "reason": "General request detected.",
        "suggested_response_style": "calm",
        "execution_plan": ["Respond to the patient."],
    }

    with SessionLocal() as db:
        patient = orchestrator.intake.intake_patient(
            db,
            PatientIntakeRequest(full_name="Asha Rao", preferred_language="en", active_conditions=[]),
        )
        patient.google_access_token = "token"
        patient.google_refresh_token = "refresh"
        db.commit()
        result = orchestrator.route_conversation(
            patient_id=patient.id,
            message="Can you check my recent health emails?",
            db=db,
        )

    assert "Lab report ready" in result["message"]


def test_route_conversation_returns_prescription_list_from_workspace() -> None:
    init_database()
    orchestrator = Orchestrator(brain_gateway=StubBrainGateway())
    orchestrator.communications.build_conversation_plan = lambda message, profile=None: {  # type: ignore[method-assign]
        "message": "Let me check that.",
        "route_type": "medical_text",
        "primary_model": orchestrator.model_routing.settings.medgemma_model_id,
        "support_model": orchestrator.model_routing.settings.gemini_fast_model_id,
        "reason": "Medical request detected.",
        "suggested_response_style": "calm",
        "execution_plan": ["Respond to the patient."],
    }

    with SessionLocal() as db:
        patient = orchestrator.intake.intake_patient(
            db,
            PatientIntakeRequest(full_name="Asha Rao", preferred_language="en", active_conditions=[]),
        )
        orchestrator.intake.scan_prescription(
            db=db,
            patient_id=patient.id,
            image_reference=None,
            raw_text_hint="Metformin 500 mg twice daily with meals",
        )
        result = orchestrator.route_conversation(
            patient_id=patient.id,
            message="Can you show my current prescriptions?",
            db=db,
        )

    assert result["message"].startswith("Here are the latest stored prescriptions:")
    assert "Metformin" in result["message"]


def test_route_conversation_can_read_drive_files_and_prescription_docs() -> None:
    init_database()
    orchestrator = Orchestrator(brain_gateway=StubBrainGateway())
    orchestrator.integrations = StubIntegrations()
    orchestrator.communications.build_conversation_plan = lambda message, profile=None: {  # type: ignore[method-assign]
        "message": "I’ll check Drive.",
        "route_type": "general_conversation",
        "primary_model": orchestrator.model_routing.settings.gemini_fast_model_id,
        "support_model": None,
        "reason": "General request detected.",
        "suggested_response_style": "calm",
        "execution_plan": ["Respond to the patient."],
    }

    with SessionLocal() as db:
        patient = orchestrator.intake.intake_patient(
            db,
            PatientIntakeRequest(full_name="Asha Rao", preferred_language="en", active_conditions=[]),
        )
        patient.google_access_token = "token"
        patient.google_refresh_token = "refresh"
        prescription = orchestrator.intake.scan_prescription(
            db=db,
            patient_id=patient.id,
            image_reference=None,
            raw_text_hint="Metformin 500 mg twice daily with meals",
        )
        prescription.document_drive_file_url = "https://drive.example/prescription-linked"
        db.commit()

        result = orchestrator.route_conversation(
            patient_id=patient.id,
            message="Can you check my Google Drive prescription documents?",
            db=db,
        )

    assert "Recent Drive files" in result["message"]
    assert "Prescription docs" in result["message"]
    assert "Prescription-April.pdf" in result["message"]


def test_route_conversation_send_email_uses_professional_contextual_body() -> None:
    init_database()
    orchestrator = Orchestrator(brain_gateway=StubBrainGateway())
    orchestrator.integrations = StubIntegrations()
    orchestrator.communications.build_conversation_plan = lambda message, profile=None: {  # type: ignore[method-assign]
        "message": "I can handle that.",
        "route_type": "general_conversation",
        "primary_model": orchestrator.model_routing.settings.gemini_fast_model_id,
        "support_model": None,
        "reason": "General request detected.",
        "suggested_response_style": "calm",
        "execution_plan": ["Respond to the patient."],
    }

    with SessionLocal() as db:
        patient = orchestrator.intake.intake_patient(
            db,
            PatientIntakeRequest(full_name="Asha Rao", preferred_language="en", active_conditions=["IBS"]),
        )
        patient.summary = "Recurring abdominal pain with intermittent nausea."
        patient.google_access_token = "token"
        patient.google_refresh_token = "refresh"
        orchestrator.intake.scan_prescription(
            db=db,
            patient_id=patient.id,
            image_reference=None,
            raw_text_hint="Metformin 500 mg twice daily with meals",
        )
        db.commit()

        result = orchestrator.route_conversation(
            patient_id=patient.id,
            message="Please send care summary to doctor@example.com about my current status",
            db=db,
        )

    assert "I sent the care summary email" in result["message"]
    sent_email = orchestrator.integrations.last_sent_email
    assert sent_email is not None
    assert sent_email["to"] == "doctor@example.com"
    assert "Dear Care Team" in sent_email["body_html"]
    assert "Patient Summary:" in sent_email["body_html"]
    assert "Relevant Conditions:" in sent_email["body_html"]
    assert "Recent Prescription History:" in sent_email["body_html"]
    assert "Patient Request:" in sent_email["body_html"]


def test_route_medical_input_uses_medsiglip_for_images() -> None:
    orchestrator = Orchestrator(brain_gateway=StubBrainGateway())
    result = orchestrator.route_medical_input(patient_id=1, query_text="Photo of a skin rash", file_path="rash-photo.jpg")
    assert result["primary_model"] == orchestrator.model_routing.settings.medsiglip_model_id
    assert result["secondary_model"] == orchestrator.model_routing.settings.medgemma_model_id
    assert result["route_type"] == "medical_image"


def test_store_and_search_medical_memory() -> None:
    init_database()
    orchestrator = Orchestrator(brain_gateway=StubBrainGateway())
    with SessionLocal() as db:
        stored = orchestrator.store_medical_memory(
            db=db,
            patient_id=1,
            source_type="manual_upload",
            query_text="Patient has recurring IBS flare with stomach pain.",
            file_path="flare-note.png",
        )
        assert stored["route_type"] == "medical_image"
        search = orchestrator.search_medical_memory(
            db=db,
            patient_id=1,
            query_text="stomach pain with IBS flare",
            limit=3,
        )
        assert search["results"]


def test_run_document_intake_flow_creates_case_when_escalation_needed() -> None:
    init_database()
    orchestrator = Orchestrator(brain_gateway=StubBrainGateway())
    orchestrator.integrations = StubIntegrations()
    orchestrator.hitl.create_case = lambda db, patient_id, case_type, summary: SimpleNamespace(  # type: ignore[method-assign]
        id=99,
        status="created",
        external_ticket_id="ASANA-99",
        external_ticket_url="https://asana.example/task/99",
    )
    with SessionLocal() as db:
        patient = orchestrator.intake.intake_patient(
            db,
            PatientIntakeRequest(full_name="Asha Rao", preferred_language="en", active_conditions=[]),
        )
        result = orchestrator.run_document_intake_flow(
            db=db,
            patient_id=patient.id,
            raw_text_hint="Metformin 500 mg twice daily with meals",
            document_file_path="sample-note.png",
            pharmacy_location_query="Koramangala",
        )
        assert result["prescription"]["medication_name"] == "Metformin"
        assert result["memory_result"]["memory_id"] == 1
        assert result["escalation_required"] is True
        assert result["case"]["case_id"] == 99


def test_run_routine_automation_creates_case_for_high_risk() -> None:
    orchestrator = Orchestrator(brain_gateway=StubBrainGateway())
    orchestrator.routine.get_routine_snapshot = lambda: {  # type: ignore[method-assign]
        "tasks": [
            SimpleNamespace(task_id="1", name="Task 1", completed=False, due_on="2020-01-01", notes=None, assignee_name=None, permalink_url=None),
            SimpleNamespace(task_id="2", name="Task 2", completed=False, due_on="2020-01-02", notes=None, assignee_name=None, permalink_url=None),
        ],
        "open_count": 2,
        "overdue_count": 2,
        "due_today_count": 0,
        "risk_level": "high",
        "routine_summary": "2 overdue tasks.",
    }
    orchestrator.hitl.create_case = lambda db, patient_id, case_type, summary: SimpleNamespace(  # type: ignore[method-assign]
        id=7,
        status="created",
        external_ticket_id="ASANA-7",
        external_ticket_url="https://asana.example/task/7",
    )
    orchestrator.integrations = StubIntegrations()
    with SessionLocal() as db:
        result = orchestrator.run_routine_automation(db=db, patient_id=1)
        assert result["risk_level"] == "high"
        assert result["case"]["case_id"] == 7
