from __future__ import annotations

import json
import re
from pathlib import Path
from statistics import median

from nexus_ai.patient_finance.arize_tracing import trace_span
from nexus_ai.patient_finance.models import AuditFlag, BillAuditResult, BillItem, BoundingBox, as_money
from nexus_ai.patient_finance.mongodb import get_document, save_audit


FIXTURE_PATH = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "bills" / "sample_itemized_bill.json"
_CODE_PATTERN = re.compile(r"^(?:\d{5}|[A-Z]\d{4})$")


def _make_bbox(index: int) -> BoundingBox:
    top = 720 - (index * 38)
    return BoundingBox(x1=72, y1=float(top), x2=540, y2=float(top - 26), pageNumber=1)


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _load_cpt_reference() -> dict[str, dict[str, object]]:
    return {
        "99203": {"description": "Office visit, new patient, level 3", "category": "E/M", "median_price": 240.0},
        "80053": {"description": "Comprehensive metabolic panel", "category": "Lab", "median_price": 110.0},
        "99214": {"description": "Office visit, established patient, level 4", "category": "E/M", "median_price": 190.0},
        "71046": {"description": "Chest X-ray, 2 views", "category": "Imaging", "median_price": 320.0},
        "80061": {"description": "Lipid panel", "category": "Lab", "median_price": 80.0},
        "96365": {"description": "IV infusion, first hour", "category": "Procedures", "median_price": 290.0},
    }


@trace_span("patient_finance.parse_bill")
def parse_itemized_bill(bill_id: str) -> list[BillItem]:
    bill_document = get_document("bills", bill_id)
    payload = bill_document.get("parsed_data") if bill_document else None
    if not payload:
        payload = _load_fixture()

    items: list[BillItem] = []
    for index, raw_item in enumerate(payload["items"]):
        items.append(
            BillItem(
                description=raw_item["description"],
                code=raw_item["code"],
                category=raw_item["category"],
                quantity=int(raw_item.get("qty", raw_item.get("quantity", 1))),
                unit_price=as_money(raw_item["unit_price"]),
                line_total=as_money(raw_item["line_total"]),
                bbox=_make_bbox(index),
            )
        )
    return items


@trace_span("patient_finance.audit_bill")
def audit_bill(items: list[BillItem], bill_id: str) -> BillAuditResult:
    bill_document = get_document("bills", bill_id) or _load_fixture()
    patient_id = str(bill_document.get("patient_id", "PAT-TEST-001"))
    cpt_reference = _load_cpt_reference()
    prices_by_category: dict[str, list[float]] = {}
    for item in items:
        prices_by_category.setdefault(item.category, []).append(float(item.unit_price))

    flags: list[AuditFlag] = []
    flagged_indexes: set[int] = set()
    code_counts: dict[str, int] = {}

    for index, item in enumerate(items):
        code_counts[item.code] = code_counts.get(item.code, 0) + 1
        if code_counts[item.code] > 1:
            flags.append(
                AuditFlag(
                    type="duplicate",
                    severity="warning",
                    item_index=index,
                    reason=f"Potential duplicate billing for code {item.code}.",
                    suggested_action="Ask the provider to justify why the same code appears multiple times.",
                    line_item_description=item.description,
                    billed_amount=item.line_total,
                    verified_amount=item.line_total,
                    bbox=item.bbox,
                )
            )
            flagged_indexes.add(index)

        if not _CODE_PATTERN.match(item.code) or item.code not in cpt_reference:
            flags.append(
                AuditFlag(
                    type="unknown_code",
                    severity="error",
                    item_index=index,
                    reason=f"Unknown billing code {item.code}.",
                    suggested_action="Request the billing office to provide a valid CPT/HCPCS code.",
                    line_item_description=item.description,
                    billed_amount=item.line_total,
                    bbox=item.bbox,
                )
            )
            flagged_indexes.add(index)
            continue

        benchmark = float(cpt_reference[item.code]["median_price"])
        if float(item.unit_price) > benchmark * 1.5:
            flags.append(
                AuditFlag(
                    type="pricing_outlier",
                    severity="warning",
                    item_index=index,
                    reason=f"Price for code {item.code} is well above the fixture benchmark.",
                    suggested_action="Compare this charge against the provider's contracted rate schedule.",
                    line_item_description=item.description,
                    billed_amount=item.line_total,
                    verified_amount=as_money(benchmark * item.quantity),
                    bbox=item.bbox,
                )
            )
            flagged_indexes.add(index)

        expected_total = as_money(item.quantity * item.unit_price)
        if item.line_total != expected_total:
            flags.append(
                AuditFlag(
                    type="math_error",
                    severity="error",
                    item_index=index,
                    reason="Line total does not match quantity multiplied by unit price.",
                    suggested_action="Request a corrected itemized bill.",
                    line_item_description=item.description,
                    billed_amount=item.line_total,
                    verified_amount=expected_total,
                    bbox=item.bbox,
                )
            )
            flagged_indexes.add(index)

    total_billed = as_money(sum(item.line_total for item in items))
    total_flagged = as_money(sum(items[index].line_total for index in flagged_indexes))
    total_verified = as_money(total_billed - total_flagged)

    if not flags:
        for index, item in enumerate(items):
            flags.append(
                AuditFlag(
                    type="verified",
                    severity="info",
                    item_index=index,
                    reason="Charge validated against the current reference fixture.",
                    suggested_action="No action needed.",
                    line_item_description=item.description,
                    billed_amount=item.line_total,
                    verified_amount=item.line_total,
                    bbox=item.bbox,
                )
            )

    result = BillAuditResult(
        bill_id=bill_id,
        patient_id=patient_id,
        items=items,
        total_billed=total_billed,
        total_flagged=total_flagged,
        total_verified=total_verified,
        flags=flags,
        summary=f"Audited {len(items)} line items and flagged {len(flagged_indexes)} potentially problematic charges.",
    )
    save_audit(bill_id, result)
    return result

