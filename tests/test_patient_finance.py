from decimal import Decimal

import pytest

from nexus_ai.patient_finance import (
    PatientFinanceOrchestrator,
    audit_bill_tool,
    calculate_gap_tool,
    lookup_policy_tool,
    parse_bill_tool,
    rank_loans_tool,
    search_loan_offers_tool,
    submit_loan_application_tool,
)
from nexus_ai.patient_finance.gap import calculate_gap
from nexus_ai.patient_finance.loan import build_prefill_payload, submit_application
from nexus_ai.patient_finance.models import BillAuditResult, BillItem


def test_parse_bill_tool_returns_fixture_backed_line_items() -> None:
    result = parse_bill_tool("test-bill")

    assert result["item_count"] == 8
    assert Decimal(result["total"]) == Decimal("1980.00")


def test_audit_bill_tool_flags_duplicates_and_unknown_codes() -> None:
    audit = audit_bill_tool("test-bill")

    reasons = {flag["reason"] for flag in audit["flags"]}
    assert any("duplicate" in reason.lower() for reason in reasons)
    assert any("unknown" in reason.lower() for reason in reasons)
    assert Decimal(audit["total_billed"]) == Decimal("1980.00")


def test_gap_calculation_returns_non_negative_breakdown() -> None:
    audit_result = BillAuditResult(
        bill_id="bill-1",
        patient_id="1",
        items=[
            BillItem(
                description="Office visit",
                code="99203",
                category="E/M",
                quantity=1,
                unit_price=Decimal("250.00"),
                line_total=Decimal("250.00"),
            )
        ],
        total_billed=Decimal("250.00"),
        total_flagged=Decimal("0.00"),
        total_verified=Decimal("250.00"),
        flags=[],
    )

    result = calculate_gap(audit_result)

    assert result.patient_responsibility >= Decimal("0.00")
    assert result.breakdown.covered_amount >= Decimal("0.00")


def test_policy_lookup_tool_returns_viewer_ready_citations() -> None:
    citation_payload = lookup_policy_tool("deductible and coinsurance")

    assert citation_payload["citations"]
    assert citation_payload["viewer_ready_format"]["highlights"]


def test_rank_loans_tool_prefers_hospital_zero_apr_offer() -> None:
    ranked = rank_loans_tool(
        {
            "gap_amount": "2200.00",
            "loan_profile": {"preferred_tenure": 12, "patient_id": "PAT-TEST-001"},
        }
    )

    assert ranked["ranked_offers"][0]["provider_name"] == "Citywide General Hospital Payment Plan"


def test_submit_application_requires_explicit_consent() -> None:
    with pytest.raises(PermissionError):
        submit_application(
            {"consent_flags": {"loan_submission": False}},
            {"provider_name": "Citywide General Hospital Payment Plan"},
        )


def test_orchestrator_runs_finance_workflow_end_to_end() -> None:
    orchestrator = PatientFinanceOrchestrator(
        profile_loader=lambda patient_id: {
            "id": patient_id,
            "full_name": "Asha Rao",
            "preferred_language": "en",
            "conditions": [{"name": "IBS"}],
        }
    )

    snapshot = orchestrator.start_workflow(
        patient_id=1,
        filename="bill.pdf",
        content_type="application/pdf",
        raw_bytes=b"%PDF-1.4 demo",
    )

    assert snapshot.current_step == "awaiting_consent"
    assert snapshot.audit_result is not None
    assert snapshot.gap_result is not None
    assert snapshot.loan_offers
    assert snapshot.patient_name == "Asha Rao"
