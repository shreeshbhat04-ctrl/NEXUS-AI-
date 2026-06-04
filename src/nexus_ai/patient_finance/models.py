from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_money(value: Decimal | float | int | str) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class FinanceBaseModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={
            Decimal: lambda value: f"{value:.2f}",
            datetime: lambda value: value.isoformat(),
        },
    )


class BoundingBox(FinanceBaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    page_number: int = Field(alias="pageNumber")

    @computed_field
    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @computed_field
    @property
    def height(self) -> float:
        return self.y2 - self.y1


class BillItem(FinanceBaseModel):
    description: str
    code: str
    category: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    bbox: BoundingBox | None = None

    @model_validator(mode="after")
    def normalize_money(self) -> "BillItem":
        self.description = self.description.strip()
        self.code = self.code.strip().upper()
        self.category = self.category.strip()
        self.unit_price = as_money(self.unit_price)
        expected_total = as_money(Decimal(self.quantity) * self.unit_price)
        self.line_total = as_money(self.line_total or expected_total)
        return self


class AuditFlag(FinanceBaseModel):
    id: str = Field(default_factory=lambda: f"flag-{uuid4().hex[:10]}")
    type: Literal["duplicate", "unknown_code", "pricing_outlier", "math_error", "verified"]
    severity: Literal["info", "warning", "error"]
    item_index: int
    reason: str
    suggested_action: str
    line_item_description: str
    billed_amount: Decimal
    verified_amount: Decimal | None = None
    bbox: BoundingBox | None = None
    policy_citation_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def normalize_money(self) -> "AuditFlag":
        self.billed_amount = as_money(self.billed_amount)
        if self.verified_amount is not None:
            self.verified_amount = as_money(self.verified_amount)
        return self


class BillAuditResult(FinanceBaseModel):
    bill_id: str
    patient_id: str
    items: list[BillItem]
    total_billed: Decimal
    total_flagged: Decimal
    total_verified: Decimal
    flags: list[AuditFlag] = Field(default_factory=list)
    status: Literal["in_progress", "completed"] = "completed"
    summary: str | None = None
    audit_timestamp: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def normalize_totals(self) -> "BillAuditResult":
        self.total_billed = as_money(self.total_billed)
        self.total_flagged = as_money(self.total_flagged)
        self.total_verified = as_money(self.total_verified)
        return self


class CoverageBreakdown(FinanceBaseModel):
    covered_amount: Decimal
    discounts: Decimal = Decimal("0.00")
    deductible_remaining: Decimal = Decimal("0.00")
    copay: Decimal = Decimal("0.00")
    coinsurance_percent: float = 0.0
    coinsurance_amount: Decimal = Decimal("0.00")
    out_of_pocket_max: Decimal = Decimal("0.00")
    out_of_pocket_spent: Decimal = Decimal("0.00")
    is_oop_max_reached: bool = False

    @model_validator(mode="after")
    def normalize_money(self) -> "CoverageBreakdown":
        self.covered_amount = as_money(self.covered_amount)
        self.discounts = as_money(self.discounts)
        self.deductible_remaining = as_money(self.deductible_remaining)
        self.copay = as_money(self.copay)
        self.coinsurance_amount = as_money(self.coinsurance_amount)
        self.out_of_pocket_max = as_money(self.out_of_pocket_max)
        self.out_of_pocket_spent = as_money(self.out_of_pocket_spent)
        return self


class GapCalculationResult(FinanceBaseModel):
    bill_id: str
    patient_id: str
    total_billed: Decimal
    insurance_coverage: Decimal
    patient_responsibility: Decimal
    breakdown: CoverageBreakdown
    status: Literal["in_progress", "completed"] = "completed"
    computed_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def normalize_totals(self) -> "GapCalculationResult":
        self.total_billed = as_money(self.total_billed)
        self.insurance_coverage = as_money(self.insurance_coverage)
        self.patient_responsibility = as_money(self.patient_responsibility)
        return self


class LoanOffer(FinanceBaseModel):
    id: str = Field(default_factory=lambda: f"offer-{uuid4().hex[:10]}")
    provider_name: str
    apr: float
    tenure_months: int
    min_amount: Decimal
    max_amount: Decimal
    emi: Decimal
    total_payable: Decimal
    approval_probability: float
    provider_reliability_score: float
    ranking_score: float = 0.0
    is_top_pick: bool = False

    @model_validator(mode="after")
    def normalize_money(self) -> "LoanOffer":
        self.min_amount = as_money(self.min_amount)
        self.max_amount = as_money(self.max_amount)
        self.emi = as_money(self.emi)
        self.total_payable = as_money(self.total_payable)
        return self


class LoanRankingInput(FinanceBaseModel):
    gap_amount: Decimal
    patient_credit_tier: str = "good"
    preferred_tenure: int = 12
    offers: list[LoanOffer] = Field(default_factory=list)

    @model_validator(mode="after")
    def normalize_money(self) -> "LoanRankingInput":
        self.gap_amount = as_money(self.gap_amount)
        return self


class PolicyChunk(FinanceBaseModel):
    chunk_id: str
    page: int
    bbox: BoundingBox
    text: str
    section_title: str
    source_doc_id: str
    relevance_score: float = 0.0


class PolicyCitation(FinanceBaseModel):
    id: str
    section_title: str
    page_number: int
    excerpt: str
    relevance_tag: Literal["coverage", "exclusion", "limitation", "general"] = "general"
    related_audit_flag_ids: list[str] = Field(default_factory=list)
    bbox: BoundingBox | None = None


class CitationPayload(FinanceBaseModel):
    chunk_ids: list[str]
    citations: list[PolicyCitation]
    viewer_ready_format: dict


class ConsentRecord(FinanceBaseModel):
    consent_id: str = Field(default_factory=lambda: f"consent-{uuid4().hex[:12]}")
    patient_id: str
    bill_id: str
    offer_id: str
    consent_type: str = "loan_submission"
    created_at: datetime = Field(default_factory=utc_now)


class SubmissionResult(FinanceBaseModel):
    submission_id: str = Field(default_factory=lambda: f"submission-{uuid4().hex[:12]}")
    reference_id: str = Field(default_factory=lambda: f"ref-{uuid4().hex[:10]}")
    provider_name: str
    requested_amount: Decimal
    status: Literal["submitted", "failed"] = "submitted"
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def normalize_money(self) -> "SubmissionResult":
        self.requested_amount = as_money(self.requested_amount)
        return self


WorkflowStep = Literal[
    "idle",
    "uploading",
    "parsing",
    "auditing",
    "gap_calculating",
    "loan_discovery",
    "awaiting_consent",
    "submitted",
]


class WorkflowEvent(FinanceBaseModel):
    event: str = "step_change"
    step: WorkflowStep
    message: str
    data: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)


class WorkflowSnapshot(FinanceBaseModel):
    session_id: str
    patient_id: str
    patient_name: str
    bill_id: str
    current_step: WorkflowStep
    status_message: str
    pdf_filename: str | None = None
    pdf_url: str | None = None
    audit_result: BillAuditResult | None = None
    gap_result: GapCalculationResult | None = None
    loan_offers: list[LoanOffer] = Field(default_factory=list)
    policy_citations: list[PolicyCitation] = Field(default_factory=list)
    selected_offer_id: str | None = None
    consent_status: Literal["pending", "granted", "denied"] = "pending"
    application_id: str | None = None
    updated_at: datetime = Field(default_factory=utc_now)
    events: list[WorkflowEvent] = Field(default_factory=list)

