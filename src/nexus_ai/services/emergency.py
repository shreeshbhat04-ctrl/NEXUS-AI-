EMERGENCY_PHRASES = (
    "chest pain",
    "can't breathe",
    "cannot breathe",
    "shortness of breath",
    "passed out",
)


def detect_emergency(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in EMERGENCY_PHRASES)
