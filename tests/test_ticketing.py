from nexus_ai.adapters.ticketing import MockTicketingAdapter


def test_mock_ticketing_adapter_creates_ticket() -> None:
    result = MockTicketingAdapter().create_review_ticket(
        patient_id=123,
        summary="Needs doctor review",
        case_type="doctor_review",
    )
    assert result.ticket_id.startswith("CQ-")
    assert result.status == "created"
