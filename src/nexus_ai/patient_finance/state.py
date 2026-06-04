from __future__ import annotations

from copy import deepcopy
from typing import Any

from nexus_ai.patient_finance.mongodb import (
    clear_session_snapshot,
    get_session_snapshot,
    save_session_snapshot,
)


def initialize_session(patient_id: str, bill_source: str, loan_profile: dict | None = None) -> dict[str, Any]:
    existing = restore_snapshot(patient_id)
    if existing is not None:
        return existing

    state = {
        "patient_id": str(patient_id),
        "bill_source": bill_source,
        "loan_profile": dict(loan_profile or {}),
        "consent_flags": {
            "data_sharing": False,
            "loan_submission": False,
            "phi_release": False,
        },
        "audit_result": None,
        "gap_result": None,
        "ranked_offers": [],
        "selected_offer": None,
        "policy_citations": [],
    }
    persist_snapshot(state)
    return state


def update_state(session_state: dict[str, Any], key: str, value: Any) -> dict[str, Any]:
    next_state = deepcopy(session_state)
    next_state[key] = value
    persist_snapshot(next_state)
    return next_state


def get_state(session_state: dict[str, Any], key: str) -> Any:
    return session_state.get(key)


def persist_snapshot(session_state: dict[str, Any]) -> None:
    save_session_snapshot(str(session_state["patient_id"]), deepcopy(session_state))


def restore_snapshot(patient_id: str) -> dict[str, Any] | None:
    snapshot = get_session_snapshot(str(patient_id))
    if snapshot is None:
        return None
    return deepcopy(snapshot)


def clear_session(patient_id: str) -> None:
    clear_session_snapshot(str(patient_id))

