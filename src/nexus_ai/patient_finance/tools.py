from __future__ import annotations

from decimal import Decimal
from typing import Any

from nexus_ai.patient_finance.billing import audit_bill, parse_itemized_bill
from nexus_ai.patient_finance.gap import calculate_gap
from nexus_ai.patient_finance.loan import build_prefill_payload, rank_offers, submit_application
from nexus_ai.patient_finance.policy import build_citation_payload, parse_policy_chunks, retrieve_relevant_chunks


def parse_bill_tool(bill_id: str) -> dict[str, Any]:
    items = parse_itemized_bill(bill_id)
    total = sum(item.line_total for item in items)
    return {
        "item_count": len(items),
        "total": f"{total:.2f}",
        "items": [item.model_dump(mode="json", by_alias=True) for item in items],
    }


def audit_bill_tool(bill_id: str) -> dict[str, Any]:
    items = parse_itemized_bill(bill_id)
    result = audit_bill(items, bill_id)
    return result.model_dump(mode="json", by_alias=True)


def calculate_gap_tool(audit_payload: dict[str, Any]) -> dict[str, Any]:
    from nexus_ai.patient_finance.models import BillAuditResult

    audit_result = BillAuditResult.model_validate(audit_payload)
    gap_result = calculate_gap(audit_result)
    return gap_result.model_dump(mode="json", by_alias=True)


def search_loan_offers_tool(session_state: dict[str, Any]) -> dict[str, Any]:
    gap_amount = Decimal(str(session_state["gap_amount"]))
    offers = rank_offers(gap_amount, session_state.get("loan_profile", {}))
    return {"offer_count": len(offers), "offers": [offer.model_dump(mode="json") for offer in offers]}


def rank_loans_tool(session_state: dict[str, Any]) -> dict[str, Any]:
    gap_amount = Decimal(str(session_state["gap_amount"]))
    ranked = rank_offers(gap_amount, session_state.get("loan_profile", {}))
    return {"ranked_offers": [offer.model_dump(mode="json") for offer in ranked]}


def submit_loan_application_tool(offer_index: int, session_state: dict[str, Any]) -> dict[str, Any]:
    if not session_state.get("consent_flags", {}).get("loan_submission"):
        return {"error": "Patient consent not granted. Cannot submit application."}
    selected = session_state["ranked_offers"][offer_index]
    selected_offer = selected if hasattr(selected, "provider_name") else None
    if selected_offer is None:
        from nexus_ai.patient_finance.models import LoanOffer

        selected_offer = LoanOffer.model_validate(selected)
    payload = build_prefill_payload(session_state.get("loan_profile", {}), selected_offer)
    return submit_application(session_state, payload)


def lookup_policy_tool(query: str, doc_path: str | None = None) -> dict[str, Any]:
    chunks = parse_policy_chunks(doc_path)
    source_doc_id = chunks[0].source_doc_id if chunks else "POLICY-HMO-2026-SAMPLE"
    relevant = retrieve_relevant_chunks(query, source_doc_id)
    payload = build_citation_payload(relevant, {"query": query})
    return payload.model_dump(mode="json", by_alias=True)

