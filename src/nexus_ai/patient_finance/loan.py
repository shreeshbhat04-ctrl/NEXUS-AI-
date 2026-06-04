from __future__ import annotations

import json
from abc import ABC, abstractmethod
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from nexus_ai.patient_finance.arize_tracing import trace_span
from nexus_ai.patient_finance.models import LoanOffer, LoanRankingInput, SubmissionResult, as_money
from nexus_ai.patient_finance.mongodb import save_offers, save_submission
from nexus_ai.patient_finance.privacy import redact_phi


FIXTURE_PATH = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "loans" / "sample_loan_offers.json"


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _emi(principal: Decimal, apr: float, months: int) -> Decimal:
    principal = as_money(principal)
    if apr <= 0:
        return as_money(principal / Decimal(months))
    monthly_rate = Decimal(str(apr / 100)) / Decimal("12")
    factor = (Decimal("1") + monthly_rate) ** months
    emi = principal * monthly_rate * factor / (factor - Decimal("1"))
    return as_money(emi)


class LoanProvider(ABC):
    provider_name: str

    @abstractmethod
    def discover_offers(self, gap_amount: Decimal, patient_profile: dict) -> list[LoanOffer]:
        raise NotImplementedError

    @abstractmethod
    def submit_application(self, prefill_payload: dict) -> dict:
        raise NotImplementedError


class FixtureLoanProvider(LoanProvider):
    def __init__(self, offer_payload: dict) -> None:
        self.offer_payload = offer_payload
        self.provider_name = offer_payload["provider_name"]

    def discover_offers(self, gap_amount: Decimal, patient_profile: dict) -> list[LoanOffer]:
        preferred_amount = as_money(gap_amount)
        minimum = as_money(self.offer_payload["min_amount"])
        maximum = as_money(self.offer_payload["max_amount"])
        if preferred_amount < minimum or preferred_amount > maximum:
            return []
        months = int(self.offer_payload["tenure_months"])
        apr = float(self.offer_payload["apr"])
        emi = _emi(preferred_amount, apr, months)
        return [
            LoanOffer(
                provider_name=self.provider_name,
                apr=apr,
                tenure_months=months,
                min_amount=minimum,
                max_amount=maximum,
                emi=emi,
                total_payable=as_money(emi * Decimal(months)),
                approval_probability=float(self.offer_payload["approval_probability"]),
                provider_reliability_score=float(self.offer_payload["provider_reliability"]),
            )
        ]

    def submit_application(self, prefill_payload: dict) -> dict:
        return {
            "status": "submitted",
            "provider_name": self.provider_name,
            "reference_id": f"loan-{uuid4().hex[:10]}",
            "requested_amount": prefill_payload["requested_amount"],
        }


def _providers() -> list[LoanProvider]:
    return [FixtureLoanProvider(offer) for offer in _load_fixture()["offers"]]


@trace_span("patient_finance.discover_offers")
def discover_offers(gap_amount: Decimal, patient_profile: dict) -> list[LoanOffer]:
    safe_profile = {
        key: redact_phi(str(value), session_id=str(patient_profile.get("patient_id", "finance")))
        for key, value in patient_profile.items()
        if isinstance(value, (str, int, float))
    }
    _ = safe_profile
    offers: list[LoanOffer] = []
    for provider in _providers():
        offers.extend(provider.discover_offers(as_money(gap_amount), patient_profile))
    return offers


@trace_span("patient_finance.rank_offers")
def rank_offers(gap_amount: Decimal, patient_profile: dict) -> list[LoanOffer]:
    offers = discover_offers(gap_amount, patient_profile)
    preferred_tenure = int(patient_profile.get("preferred_tenure", 12))

    def score(offer: LoanOffer) -> float:
        apr_component = max(0.0, 40.0 - offer.apr)
        tenure_component = max(0.0, 20.0 - abs(offer.tenure_months - preferred_tenure))
        approval_component = offer.approval_probability * 25.0
        reliability_component = offer.provider_reliability_score * 15.0
        return round(apr_component + tenure_component + approval_component + reliability_component, 3)

    ranked: list[LoanOffer] = []
    for offer in offers:
        ranked.append(offer.model_copy(update={"ranking_score": score(offer)}))

    ranked.sort(key=lambda offer: (-offer.ranking_score, offer.apr, -offer.approval_probability))
    if ranked:
        ranked[0].is_top_pick = True
    return ranked


def persist_ranked_offers(bill_id: str, patient_id: str, offers: list[LoanOffer]) -> None:
    save_offers(bill_id, patient_id, offers)


def build_prefill_payload(patient_profile: dict, selected_offer: LoanOffer) -> dict:
    patient_token = redact_phi(
        patient_profile.get("full_name", f"patient-{patient_profile.get('patient_id', 'unknown')}"),
        session_id=str(patient_profile.get("patient_id", "finance")),
    )
    return {
        "patient_token": patient_token,
        "patient_id": str(patient_profile.get("patient_id", "unknown")),
        "provider_name": selected_offer.provider_name,
        "requested_amount": f"{selected_offer.total_payable:.2f}",
        "tenure_months": selected_offer.tenure_months,
        "apr": selected_offer.apr,
        "application_metadata": {
            "preferred_language": patient_profile.get("preferred_language", "en"),
            "credit_tier": patient_profile.get("patient_credit_tier", "good"),
        },
    }


def submit_application(session_state: dict, prefill_payload: dict) -> dict:
    if not session_state.get("consent_flags", {}).get("loan_submission"):
        raise PermissionError("Loan submission requires explicit patient consent.")

    provider_name = prefill_payload["provider_name"]
    provider = next((candidate for candidate in _providers() if candidate.provider_name == provider_name), None)
    if provider is None:
        raise LookupError(f"No provider adapter registered for {provider_name}")

    provider_response = provider.submit_application(prefill_payload)
    result = SubmissionResult(
        provider_name=provider_name,
        requested_amount=Decimal(str(prefill_payload["requested_amount"])),
        reference_id=provider_response["reference_id"],
    )
    save_submission(result.submission_id, result)
    return result.model_dump(mode="json")

