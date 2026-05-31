from nexus_ai.api.models import (
    ConversationRoutingRequest,
    EscalateRequest,
    MedGemmaRequest,
    MedSigLIPClassificationRequest,
    MedicalMemoryStoreRequest,
    MedicalRoutingRequest,
)


def test_escalate_request_defaults() -> None:
    payload = EscalateRequest(patient_id=1, summary="Needs review")
    assert payload.create_calendar_event is False
    assert payload.calendar_minutes_from_now == 30
    assert payload.calendar_duration_minutes == 30


def test_escalate_request_accepts_doctor_routing() -> None:
    payload = EscalateRequest(patient_id=2, summary="Needs review", doctor_id=7, urgency="high")
    assert payload.doctor_id == 7
    assert payload.urgency == "high"


def test_conversation_routing_request_requires_message() -> None:
    payload = ConversationRoutingRequest(patient_id=7, message="How was my day going?")
    assert payload.patient_id == 7


def test_medical_routing_request_accepts_query_or_file() -> None:
    payload = MedicalRoutingRequest(patient_id=7, query_text="I have a rash", file_path="rash.jpg")
    assert payload.query_text == "I have a rash"
    assert payload.file_path == "rash.jpg"


def test_medical_memory_store_request_defaults() -> None:
    payload = MedicalMemoryStoreRequest(patient_id=3)
    assert payload.use_live_embedding is False


def test_medgemma_request_shape() -> None:
    payload = MedGemmaRequest(patient_id=3, prompt="What do you see?", image_path="test.png")
    assert payload.max_new_tokens == 128


def test_medsiglip_request_shape() -> None:
    payload = MedSigLIPClassificationRequest(patient_id=3, image_path="test.png", candidate_labels=["rash", "burn"])
    assert len(payload.candidate_labels) == 2
