from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from nexus_ai.patient_finance.arize_tracing import trace_span
from nexus_ai.patient_finance.mongodb import get_phi_mapping, save_phi_mapping


class PresidioAdapter(Protocol):
    def anonymize(self, text: str, session_id: str | None = None) -> tuple[str, dict[str, str]]:
        ...


@dataclass
class RegexPresidioAdapter:
    patterns: tuple[tuple[str, str], ...] = (
        ("EMAIL", r"\b[\w.\-]+@[\w.\-]+\.\w+\b"),
        ("PHONE", r"\b(?:\+?\d{1,3}[- ]?)?(?:\d{3}[- ]?){2}\d{4}\b"),
        ("DATE", r"\b\d{4}-\d{2}-\d{2}\b"),
        ("DATE", r"\b\d{2}/\d{2}/\d{4}\b"),
        ("MRN", r"\bMRN[:\s-]*\d+\b"),
        ("PLAN", r"\bPLAN[:\s-]*[A-Z0-9-]+\b"),
    )

    def anonymize(self, text: str, session_id: str | None = None) -> tuple[str, dict[str, str]]:
        counters: dict[str, int] = {}
        mapping: dict[str, str] = {}
        redacted = text

        def replace(match: re.Match[str], label: str) -> str:
            counters[label] = counters.get(label, 0) + 1
            token = f"<{label}_{counters[label]}>"
            mapping[token] = match.group(0)
            return token

        for label, pattern in self.patterns:
            redacted = re.sub(pattern, lambda match, lbl=label: replace(match, lbl), redacted)

        # Conservative fallback for obvious patient/provider names in title case.
        name_pattern = re.compile(r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b")
        redacted = name_pattern.sub(lambda match: replace(match, "PERSON"), redacted)

        if session_id:
            existing = get_phi_mapping(session_id)
            existing.update(mapping)
            save_phi_mapping(session_id, existing)

        return redacted, mapping


_ADAPTER: PresidioAdapter = RegexPresidioAdapter()


def get_active_adapter() -> PresidioAdapter:
    return _ADAPTER


@trace_span("patient_finance.redact_phi")
def redact_phi(text: str, session_id: str | None = None) -> str:
    redacted, _mapping = get_active_adapter().anonymize(text, session_id=session_id)
    return redacted


def restore_phi(redacted_text: str, session_id: str) -> str:
    restored = redacted_text
    mapping = get_phi_mapping(session_id)
    for token, original in mapping.items():
        restored = restored.replace(token, original)
    return restored


def _register_custom_recognizers(_analyzer: object) -> None:
    return None

