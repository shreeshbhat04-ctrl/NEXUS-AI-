from __future__ import annotations

from decimal import Decimal
from typing import Any, Callable
from uuid import uuid4

from nexus_ai.config import get_settings
from nexus_ai.grpc_clients.brain_client import BrainClient
from nexus_ai.patient_finance.billing import audit_bill, parse_itemized_bill
from nexus_ai.patient_finance.gap import calculate_gap
from nexus_ai.patient_finance.loan import build_prefill_payload, persist_ranked_offers, rank_offers, submit_application
from nexus_ai.patient_finance.models import ConsentRecord, PolicyCitation, WorkflowEvent, WorkflowSnapshot
from nexus_ai.patient_finance.mongodb import (
    create_bill,
    get_audit,
    get_consent,
    get_document,
    get_gap,
    get_offers,
    save_consent,
)
from nexus_ai.patient_finance.policy import build_citation_payload, parse_policy_chunks, retrieve_relevant_chunks
from nexus_ai.patient_finance.state import clear_session, initialize_session, persist_snapshot, update_state


ProfileLoader = Callable[[int], dict[str, Any] | None]


class PatientFinanceOrchestrator:
    def __init__(self, profile_loader: ProfileLoader | None = None) -> None:
        self.profile_loader = profile_loader or self._load_profile_from_brain
        self._sessions_by_bill: dict[str, WorkflowSnapshot] = {}
        self._sessions_by_id: dict[str, WorkflowSnapshot] = {}

    def _load_profile_from_brain(self, patient_id: int) -> dict[str, Any] | None:
        settings = get_settings()
        try:
            with BrainClient(host=settings.grpc_brain_host, port=settings.grpc_brain_port) as client:
                profile = client.get_patient_profile(patient_id)
                return profile
        except Exception:
            return None

    def _build_patient_profile(self, patient_id: int) -> dict[str, Any]:
        profile = self.profile_loader(patient_id) or {}
        return {
            "patient_id": str(patient_id),
            "full_name": profile.get("full_name", f"Patient {patient_id}"),
            "preferred_language": profile.get("preferred_language", "en"),
            "patient_credit_tier": profile.get("patient_credit_tier", "good"),
            "preferred_tenure": int(profile.get("preferred_tenure", 12)),
            "conditions": profile.get("conditions", []),
        }

    def _event(self, step: WorkflowSnapshot.model_fields["current_step"].annotation, message: str, data: dict | None = None) -> WorkflowEvent:
        return WorkflowEvent(step=step, message=message, data=data or {})

    def _store_snapshot(self, snapshot: WorkflowSnapshot) -> WorkflowSnapshot:
        self._sessions_by_bill[snapshot.bill_id] = snapshot
        self._sessions_by_id[snapshot.session_id] = snapshot
        return snapshot

    def get_snapshot_by_session(self, session_id: str) -> WorkflowSnapshot | None:
        return self._sessions_by_id.get(session_id)

    def get_snapshot_by_bill(self, bill_id: str) -> WorkflowSnapshot | None:
        return self._sessions_by_bill.get(bill_id)

    def start_workflow(self, patient_id: int, filename: str, content_type: str, raw_bytes: bytes) -> WorkflowSnapshot:
        patient_profile = self._build_patient_profile(patient_id)
        bill_id = create_bill(
            patient_id=str(patient_id),
            filename=filename,
            content_type=content_type,
            raw_bytes=raw_bytes,
        )
        session_id = f"finance-session-{uuid4().hex[:12]}"
        session_state = initialize_session(str(patient_id), bill_id, patient_profile)
        snapshot = WorkflowSnapshot(
            session_id=session_id,
            patient_id=str(patient_id),
            patient_name=patient_profile["full_name"],
            bill_id=bill_id,
            current_step="uploading",
            status_message="Bill received. Preparing the finance workflow.",
            pdf_filename=filename,
        )
        snapshot.events.append(self._event("uploading", snapshot.status_message, {"bill_id": bill_id}))

        parsed_items = parse_itemized_bill(bill_id)
        snapshot.current_step = "parsing"
        snapshot.status_message = f"Parsed {len(parsed_items)} line items from the uploaded bill."
        snapshot.events.append(self._event("parsing", snapshot.status_message, {"item_count": len(parsed_items)}))

        audit_result = audit_bill(parsed_items, bill_id)
        session_state = update_state(session_state, "audit_result", audit_result)
        snapshot.current_step = "auditing"
        snapshot.audit_result = audit_result
        snapshot.status_message = audit_result.summary or "Audit complete."
        snapshot.events.append(
            self._event(
                "auditing",
                snapshot.status_message,
                {"flag_count": len(audit_result.flags), "total_billed": f"{audit_result.total_billed:.2f}"},
            )
        )

        policy_chunks = parse_policy_chunks()
        source_doc_id = policy_chunks[0].source_doc_id if policy_chunks else "POLICY-HMO-2026-SAMPLE"
        citation_query = " ".join(flag.reason for flag in audit_result.flags) or "deductible coverage"
        citations = build_citation_payload(retrieve_relevant_chunks(citation_query, source_doc_id)).citations
        session_state = update_state(session_state, "policy_citations", citations)
        snapshot.policy_citations = citations

        for index, flag in enumerate(snapshot.audit_result.flags):
            linked = [citation.id for citation in citations[index:index + 2]]
            snapshot.audit_result.flags[index].policy_citation_ids = linked

        gap_result = calculate_gap(audit_result)
        session_state = update_state(session_state, "gap_result", gap_result)
        snapshot.current_step = "gap_calculating"
        snapshot.gap_result = gap_result
        snapshot.status_message = "Computed the patient responsibility and coverage breakdown."
        snapshot.events.append(
            self._event(
                "gap_calculating",
                snapshot.status_message,
                {"patient_responsibility": f"{gap_result.patient_responsibility:.2f}"},
            )
        )

        offers = rank_offers(Decimal(gap_result.patient_responsibility), patient_profile)
        persist_ranked_offers(bill_id, str(patient_id), offers)
        session_state = update_state(session_state, "ranked_offers", offers)
        snapshot.current_step = "loan_discovery"
        snapshot.loan_offers = offers
        snapshot.status_message = f"Ranked {len(offers)} financing options for the uncovered balance."
        snapshot.events.append(
            self._event(
                "loan_discovery",
                snapshot.status_message,
                {"offer_count": len(offers)},
            )
        )

        snapshot.current_step = "awaiting_consent"
        snapshot.status_message = "Choose an offer to review the consent terms."
        snapshot.events.append(self._event("awaiting_consent", snapshot.status_message))
        persist_snapshot(session_state)
        return self._store_snapshot(snapshot)

    def get_audit(self, bill_id: str):
        snapshot = self.get_snapshot_by_bill(bill_id)
        if snapshot and snapshot.audit_result:
            return snapshot.audit_result
        stored = get_audit(bill_id)
        return stored

    def get_gap(self, bill_id: str):
        snapshot = self.get_snapshot_by_bill(bill_id)
        if snapshot and snapshot.gap_result:
            return snapshot.gap_result
        return get_gap(bill_id)

    def get_policy_citations(self, bill_id: str) -> list[PolicyCitation]:
        snapshot = self.get_snapshot_by_bill(bill_id)
        return snapshot.policy_citations if snapshot else []

    def get_ranked_offers(self, bill_id: str) -> list[Any]:
        snapshot = self.get_snapshot_by_bill(bill_id)
        if snapshot and snapshot.loan_offers:
            return snapshot.loan_offers
        return get_offers(bill_id)

    def record_consent(self, patient_id: int, bill_id: str, offer_id: str) -> ConsentRecord:
        consent = ConsentRecord(patient_id=str(patient_id), bill_id=bill_id, offer_id=offer_id)
        save_consent(consent, consent_id=consent.consent_id)
        snapshot = self.get_snapshot_by_bill(bill_id)
        if snapshot is not None:
            snapshot.consent_status = "granted"
            snapshot.selected_offer_id = offer_id
            snapshot.events.append(self._event("awaiting_consent", "Patient consent recorded.", {"offer_id": offer_id}))
        return consent

    def submit_offer(self, patient_id: int, bill_id: str, offer_id: str, consent_id: str) -> dict[str, Any]:
        consent = get_consent(consent_id)
        if consent is None:
            raise PermissionError("Missing consent record for loan submission.")
        snapshot = self.get_snapshot_by_bill(bill_id)
        if snapshot is None:
            raise LookupError("No workflow snapshot found for this bill.")
        selected_offer = next((offer for offer in snapshot.loan_offers if offer.id == offer_id), None)
        if selected_offer is None:
            raise LookupError("Selected loan offer was not found.")
        session_state = {
            "consent_flags": {"loan_submission": True},
        }
        patient_profile = self._build_patient_profile(patient_id)
        payload = build_prefill_payload(patient_profile, selected_offer)
        submission = submit_application(session_state, payload)
        snapshot.current_step = "submitted"
        snapshot.application_id = submission["submission_id"]
        snapshot.selected_offer_id = offer_id
        snapshot.status_message = "Loan application submitted successfully."
        snapshot.events.append(self._event("submitted", snapshot.status_message, submission))
        clear_session(str(patient_id))
        return submission

