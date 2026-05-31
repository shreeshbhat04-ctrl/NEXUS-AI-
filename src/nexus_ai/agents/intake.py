from sqlalchemy.orm import Session

from nexus_ai.adapters.ocr import MockOCRAdapter, OCRResult
from nexus_ai.api.models import PatientIntakeRequest
from nexus_ai.config import get_settings
from nexus_ai.db.models import ChronicCondition, Patient, Prescription


class IntakeAgent:
    def __init__(self, ocr_adapter: MockOCRAdapter | None = None) -> None:
        self.ocr_adapter = ocr_adapter or MockOCRAdapter()
        self.settings = get_settings()

    def intake_patient(self, db: Session, payload: PatientIntakeRequest) -> Patient:
        summary = f"{payload.full_name} prefers {payload.preferred_language} and has {len(payload.active_conditions)} recorded conditions."
        patient = Patient(
            full_name=payload.full_name,
            preferred_language=payload.preferred_language,
            date_of_birth=payload.date_of_birth,
            summary=summary,
        )
        db.add(patient)
        db.flush()
        for condition in payload.active_conditions:
            db.add(
                ChronicCondition(
                    patient_id=patient.id,
                    name=condition.name,
                    condition_type=condition.condition_type,
                    last_updated=condition.last_updated,
                    notes=condition.notes,
                )
            )
        db.commit()
        db.refresh(patient)
        return patient

    def scan_prescription(self, db: Session, patient_id: int, image_reference: str | None, raw_text_hint: str | None) -> Prescription:
        result: OCRResult = self.ocr_adapter.scan(image_reference=image_reference, raw_text_hint=raw_text_hint)
        review_status = "manual_review_required" if result.confidence_score < self.settings.ocr_confidence_threshold else "structured"
        prescription = Prescription(
            patient_id=patient_id,
            source_reference=image_reference,
            raw_text=result.raw_text,
            medication_name=result.medication_name,
            dosage=result.dosage,
            instructions=result.instructions,
            confidence_score=result.confidence_score,
            review_status=review_status,
        )
        db.add(prescription)
        db.commit()
        db.refresh(prescription)
        return prescription
