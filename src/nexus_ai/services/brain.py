from dataclasses import asdict, dataclass
from datetime import date, timedelta

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from nexus_ai.config import get_settings
from nexus_ai.db.models import ChronicCondition, Patient


@dataclass
class BrainCondition:
    id: int
    patient_id: int
    name: str
    condition_type: str
    last_updated: date | None
    notes: str | None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class BrainPatientProfile:
    id: int
    full_name: str
    preferred_language: str
    summary: str | None

    def to_dict(self) -> dict:
        return asdict(self)


class BrainService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def healthcheck(self, db: Session) -> dict[str, str]:
        db.execute(text("SELECT 1"))
        provider = "alloydb_or_postgres" if self.settings.resolved_database_url.startswith("postgresql") else "sqlite"
        return {
            "status": "ok",
            "provider": provider,
            "gateway_mode": self.settings.brain_gateway_mode,
            "database_url_hint": self.settings.database_backend_hint,
        }

    def get_patient_profile(self, db: Session, patient_id: int) -> BrainPatientProfile | None:
        patient = db.scalar(select(Patient).where(Patient.id == patient_id))
        if patient is None:
            return None
        return BrainPatientProfile(
            id=patient.id,
            full_name=patient.full_name,
            preferred_language=patient.preferred_language,
            summary=patient.summary,
        )

    def get_relevant_conditions(self, db: Session, patient_id: int) -> list[BrainCondition]:
        conditions = db.scalars(select(ChronicCondition).where(ChronicCondition.patient_id == patient_id)).all()
        cutoff = date.today() - timedelta(days=self.settings.acute_condition_lookback_days)
        return [
            BrainCondition(
                id=condition.id,
                patient_id=condition.patient_id,
                name=condition.name,
                condition_type=condition.condition_type,
                last_updated=condition.last_updated,
                notes=condition.notes,
            )
            for condition in conditions
            if condition.condition_type == "chronic"
            or condition.last_updated is None
            or condition.last_updated >= cutoff
        ]
