from __future__ import annotations

from decimal import Decimal

from nexus_ai.patient_finance.arize_tracing import trace_span
from nexus_ai.patient_finance.models import BillAuditResult, CoverageBreakdown, GapCalculationResult, as_money
from nexus_ai.patient_finance.mongodb import save_gap


@trace_span("patient_finance.calculate_gap")
def calculate_gap(
    audit_result: BillAuditResult,
    coverage_data: dict | None = None,
) -> GapCalculationResult:
    total_billed = as_money(audit_result.total_billed)
    verified_total = as_money(audit_result.total_verified)
    flagged_total = as_money(audit_result.total_flagged)

    if coverage_data is None:
        deductible_remaining = min(as_money("500.00"), as_money(verified_total * Decimal("0.10")))
        copay = as_money("50.00")
        covered_amount = as_money(verified_total * Decimal("0.72"))
        coinsurance_percent = 0.20
        coinsurance_amount = as_money(max(verified_total - covered_amount - deductible_remaining, Decimal("0.00")) * Decimal(str(coinsurance_percent)))
        out_of_pocket_max = as_money("6500.00")
        out_of_pocket_spent = as_money("3100.00")
        discounts = as_money("0.00")
    else:
        covered_amount = as_money(coverage_data.get("covered_amount", "0.00"))
        discounts = as_money(coverage_data.get("discounts", "0.00"))
        deductible_remaining = as_money(coverage_data.get("deductible_remaining", "0.00"))
        copay = as_money(coverage_data.get("copay", "0.00"))
        coinsurance_percent = float(coverage_data.get("co_insurance_pct", 0.0))
        coinsurance_amount = as_money(coverage_data.get("coinsurance_amount", "0.00"))
        out_of_pocket_max = as_money(coverage_data.get("oop_max_remaining", "0.00"))
        out_of_pocket_spent = as_money(coverage_data.get("oop_spent", "0.00"))

    patient_responsibility = as_money(flagged_total + deductible_remaining + copay + coinsurance_amount - discounts)
    if patient_responsibility > total_billed:
        patient_responsibility = total_billed
    if patient_responsibility < Decimal("0.00"):
        patient_responsibility = Decimal("0.00")

    breakdown = CoverageBreakdown(
        covered_amount=covered_amount,
        discounts=discounts,
        deductible_remaining=deductible_remaining,
        copay=copay,
        coinsurance_percent=coinsurance_percent,
        coinsurance_amount=coinsurance_amount,
        out_of_pocket_max=out_of_pocket_max,
        out_of_pocket_spent=out_of_pocket_spent,
        is_oop_max_reached=out_of_pocket_spent >= out_of_pocket_max if out_of_pocket_max > 0 else False,
    )
    result = GapCalculationResult(
        bill_id=audit_result.bill_id,
        patient_id=audit_result.patient_id,
        total_billed=total_billed,
        insurance_coverage=covered_amount,
        patient_responsibility=patient_responsibility,
        breakdown=breakdown,
    )
    save_gap(audit_result.bill_id, result)
    return result


def store_gap_result(patient_id: str, bill_id: str, gap_amount: Decimal) -> str:
    result = GapCalculationResult(
        bill_id=bill_id,
        patient_id=str(patient_id),
        total_billed=gap_amount,
        insurance_coverage=Decimal("0.00"),
        patient_responsibility=gap_amount,
        breakdown=CoverageBreakdown(covered_amount=Decimal("0.00")),
    )
    save_gap(bill_id, result)
    return bill_id

