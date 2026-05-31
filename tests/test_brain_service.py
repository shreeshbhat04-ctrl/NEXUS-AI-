from datetime import date, timedelta

from nexus_ai.db.bootstrap import init_database
from nexus_ai.db.models import ChronicCondition, Patient
from nexus_ai.db.session import SessionLocal
from nexus_ai.services.brain import BrainService


def test_relevant_conditions_filter_keeps_chronic_and_recent_acute() -> None:
    init_database()
    with SessionLocal() as db:
        patient = Patient(full_name="Test Person", preferred_language="en", summary="summary")
        db.add(patient)
        db.flush()
        db.add(
            ChronicCondition(
                patient_id=patient.id,
                name="IBS",
                condition_type="chronic",
                last_updated=None,
            )
        )
        db.add(
            ChronicCondition(
                patient_id=patient.id,
                name="Recent Infection",
                condition_type="acute",
                last_updated=date.today() - timedelta(days=5),
            )
        )
        db.add(
            ChronicCondition(
                patient_id=patient.id,
                name="Old Acute",
                condition_type="acute",
                last_updated=date.today() - timedelta(days=365),
            )
        )
        db.commit()

        conditions = BrainService().get_relevant_conditions(db, patient.id)

    names = {condition.name for condition in conditions}
    assert "IBS" in names
    assert "Recent Infection" in names
    assert "Old Acute" not in names
