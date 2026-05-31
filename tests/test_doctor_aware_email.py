from nexus_ai.agents.orchestrator import Orchestrator
from nexus_ai.api.routes import send_gmail_care_summary
from nexus_ai.db.bootstrap import init_database
from nexus_ai.db.models import Doctor, Notification, PatientDoctorMap
from nexus_ai.db.session import SessionLocal
from nexus_ai.api.models import PatientIntakeRequest
from tests.test_orchestrator import StubBrainGateway, StubIntegrations


def _seed_patient_and_doctor() -> tuple[Orchestrator, int, int]:
    init_database()
    orchestrator = Orchestrator(brain_gateway=StubBrainGateway())
    orchestrator.integrations = StubIntegrations()

    with SessionLocal() as db:
        patient = orchestrator.intake.intake_patient(
            db,
            PatientIntakeRequest(full_name="Asha Rao", preferred_language="en", active_conditions=[]),
        )
        patient.summary = "Recurring abdominal pain with intermittent nausea."
        patient.google_access_token = "token"
        patient.google_refresh_token = "refresh"
        doctor = Doctor(
            full_name="Dr surgeon",
            specialty="Gynaecologist",
            email="doctor@example.com",
            asana_user_gid="asana-test-user-1",
            asana_workspace_gid="asana-test-workspace-1",
        )
        db.add(doctor)
        db.commit()
        db.refresh(doctor)
        db.add(
            PatientDoctorMap(
                patient_id=patient.id,
                doctor_id=doctor.id,
                relationship_type="primary",
                is_default=True,
            )
        )
        orchestrator.intake.scan_prescription(
            db=db,
            patient_id=patient.id,
            image_reference=None,
            raw_text_hint="Metformin 500 mg twice daily with meals",
        )
        db.commit()
        return orchestrator, patient.id, doctor.id


def test_confirm_action_send_email_resolves_doctor_and_persists_notification() -> None:
    orchestrator, patient_id, doctor_id = _seed_patient_and_doctor()

    with SessionLocal() as db:
        draft = orchestrator.draft_action(
            db=db,
            patient_id=patient_id,
            intent="send_email",
            message="Please send this to my doctor.",
        )
        result = orchestrator.confirm_action(
            db=db,
            action_id=draft["action_id"],
            selected_option="doctor@example.com",
            custom_input=None,
        )
        notifications = db.query(Notification).filter(Notification.patient_id == patient_id).all()

    assert result["status"] == "confirmed"
    assert result["result"]["doctor_id"] == doctor_id
    assert result["result"]["doctor_name"] == "Dr surgeon"
    assert result["result"]["recipient"] == "doctor@example.com"
    assert result["result"]["message_id"] == "msg-for-doctor@example.com"
    assert len(notifications) == 1
    assert notifications[0].delivery_status == "sent"
    assert "Dr surgeon" in notifications[0].body
    sent_email = orchestrator.integrations.last_sent_email
    assert sent_email is not None
    assert sent_email["to"] == "doctor@example.com"
    assert "Respected Dr surgeon" in sent_email["body_html"]
    assert "Asha Rao" in sent_email["body_html"]


def test_send_gmail_care_summary_resolves_doctor_id_and_persists_notification(monkeypatch) -> None:
    orchestrator, patient_id, doctor_id = _seed_patient_and_doctor()

    with SessionLocal() as db:
        from nexus_ai.api import routes

        monkeypatch.setattr(routes, "orchestrator", orchestrator)
        result = send_gmail_care_summary(
            patient_id=patient_id,
            to_email=None,
            doctor_id=doctor_id,
            subject=None,
            body_html=None,
            db=db,
        )
        notifications = db.query(Notification).filter(Notification.patient_id == patient_id).all()

    assert result["recipient"] == "doctor@example.com"
    assert result["doctor_id"] == doctor_id
    assert result["doctor_name"] == "Dr surgeon"
    assert result["message_id"] == "msg-for-doctor@example.com"
    assert len(notifications) == 1
    assert notifications[0].delivery_status == "sent"
    assert "doctor@example.com" in notifications[0].body
