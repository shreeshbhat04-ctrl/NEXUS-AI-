from nexus_ai.services.emergency import detect_emergency


def test_detects_red_flag_phrase() -> None:
    assert detect_emergency("Patient reports chest pain and dizziness.")


def test_ignores_non_emergency_text() -> None:
    assert not detect_emergency("Patient would like a refill reminder.")
