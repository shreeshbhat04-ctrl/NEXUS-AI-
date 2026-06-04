from __future__ import annotations

from collections.abc import Iterable
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


KNOWN_COLLECTIONS = {
    "bills",
    "bill_audits",
    "loan_offers",
    "patient_gaps",
    "policy_chunks",
    "consent_logs",
    "finance_sessions",
    "phi_mappings",
    "submissions",
}


_STORE: dict[str, dict[str, Any]] = {name: {} for name in KNOWN_COLLECTIONS}


async def init_mongodb() -> None:
    return None


async def close_mongodb() -> None:
    return None


async def ensure_indexes() -> None:
    return None


def get_database() -> dict[str, dict[str, Any]]:
    return _STORE


def get_collection(name: str) -> dict[str, Any]:
    if name not in KNOWN_COLLECTIONS:
        raise KeyError(f"Unknown patient finance collection: {name}")
    return _STORE[name]


def _clone(value: Any) -> Any:
    return deepcopy(value)


def upsert_document(collection: str, document_id: str, payload: Any) -> str:
    get_collection(collection)[document_id] = _clone(payload)
    return document_id


def insert_document(collection: str, payload: Any, *, document_id: str | None = None) -> str:
    target_id = document_id or f"{collection[:-1]}-{uuid4().hex[:12]}"
    get_collection(collection)[target_id] = _clone(payload)
    return target_id


def get_document(collection: str, document_id: str) -> Any | None:
    value = get_collection(collection).get(document_id)
    return _clone(value) if value is not None else None


def delete_document(collection: str, document_id: str) -> None:
    get_collection(collection).pop(document_id, None)


def list_documents(collection: str) -> list[Any]:
    return [_clone(value) for value in get_collection(collection).values()]


def filter_documents(collection: str, predicate: Any) -> list[Any]:
    return [_clone(value) for value in get_collection(collection).values() if predicate(value)]


def create_bill(
    *,
    patient_id: str,
    filename: str,
    content_type: str,
    raw_bytes: bytes,
    parsed_data: dict | None = None,
) -> str:
    bill_id = f"bill-{uuid4().hex[:12]}"
    payload = {
        "bill_id": bill_id,
        "patient_id": str(patient_id),
        "filename": filename,
        "content_type": content_type,
        "raw_size": len(raw_bytes),
        "parsed_data": _clone(parsed_data),
        "status": "uploaded",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    insert_document("bills", payload, document_id=bill_id)
    return bill_id


def save_audit(bill_id: str, payload: Any) -> str:
    return upsert_document("bill_audits", bill_id, payload)


def get_audit(bill_id: str) -> Any | None:
    return get_document("bill_audits", bill_id)


def save_gap(bill_id: str, payload: Any) -> str:
    return upsert_document("patient_gaps", bill_id, payload)


def get_gap(bill_id: str) -> Any | None:
    return get_document("patient_gaps", bill_id)


def save_policy_chunks(source_doc_id: str, payload: Iterable[Any]) -> None:
    collection = get_collection("policy_chunks")
    for chunk in payload:
        chunk_id = getattr(chunk, "chunk_id", None)
        if chunk_id is None and isinstance(chunk, dict):
            chunk_id = chunk["chunk_id"]
        if chunk_id is None:
            raise KeyError("Policy chunk is missing a chunk_id.")
        collection[f"{source_doc_id}:{chunk_id}"] = _clone(chunk)


def get_policy_chunks(source_doc_id: str) -> list[Any]:
    prefix = f"{source_doc_id}:"
    return [_clone(value) for key, value in get_collection("policy_chunks").items() if key.startswith(prefix)]


def save_offers(bill_id: str, patient_id: str, offers: list[Any]) -> None:
    upsert_document(
        "loan_offers",
        bill_id,
        {
            "bill_id": bill_id,
            "patient_id": str(patient_id),
            "offers": _clone(offers),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    )


def get_offers(bill_id: str) -> list[Any]:
    payload = get_document("loan_offers", bill_id)
    if not payload:
        return []
    return payload.get("offers", [])


def save_consent(payload: Any, *, consent_id: str) -> str:
    return upsert_document("consent_logs", consent_id, payload)


def get_consent(consent_id: str) -> Any | None:
    return get_document("consent_logs", consent_id)


def save_submission(submission_id: str, payload: Any) -> str:
    return upsert_document("submissions", submission_id, payload)


def save_phi_mapping(session_id: str, mapping: dict[str, str]) -> None:
    upsert_document(
        "phi_mappings",
        session_id,
        {
            "session_id": session_id,
            "mapping": _clone(mapping),
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )


def get_phi_mapping(session_id: str) -> dict[str, str]:
    payload = get_document("phi_mappings", session_id)
    if not payload:
        return {}
    return payload.get("mapping", {})


def save_session_snapshot(patient_id: str, payload: Any) -> None:
    upsert_document("finance_sessions", str(patient_id), payload)


def get_session_snapshot(patient_id: str) -> Any | None:
    return get_document("finance_sessions", str(patient_id))


def clear_session_snapshot(patient_id: str) -> None:
    delete_document("finance_sessions", str(patient_id))
