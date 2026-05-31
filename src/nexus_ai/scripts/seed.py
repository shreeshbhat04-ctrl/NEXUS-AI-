import csv
import logging
from datetime import date
from pathlib import Path

from nexus_ai.agents.intake import IntakeAgent
from nexus_ai.agents.communications import CommunicationsAgent
from nexus_ai.agents.hitl import HITLAgent
from nexus_ai.agents.integrations import IntegrationAgent
from nexus_ai.api.models import PatientIntakeRequest, ConditionInput
from nexus_ai.db.bootstrap import init_database
from nexus_ai.db.session import SessionLocal, Base, engine

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def seed_database():
    logger.info("Drop all tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("Init schema...")
    init_database()
    
    db = SessionLocal()
    
    logger.info("Create demo patient...")
    intake = IntakeAgent()
    comms = CommunicationsAgent()
    hitl = HITLAgent()
    integrations = IntegrationAgent()
    
    payload = PatientIntakeRequest(
        full_name="Shreesha",
        preferred_language="en",
        date_of_birth=date(1990, 1, 1),
        active_conditions=[
            ConditionInput(name="Eczema", condition_type="chronic", notes="Severe skin irritation"),
            ConditionInput(name="Epilepsy", condition_type="chronic", notes="Occasional seizures"),
        ]
    )
    patient = intake.intake_patient(db=db, payload=payload)
    logger.info(f"Created patient {patient.full_name} (ID: {patient.id})")
    
    project_root = Path(__file__).parent.parent.parent.parent
    dataset_dir = project_root / "Datasets"
    indian_medicine_csv = dataset_dir / "Indian_medicine_sample_100.csv"
    
    if indian_medicine_csv.exists():
        logger.info(f"Read {indian_medicine_csv.name}...")
        with open(indian_medicine_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                if count >= 3:
                    break
                med_name = row.get("medicineName", "Unknown Med")
                try:
                    intake.scan_prescription(
                        db=db,
                        patient_id=patient.id,
                        image_reference=None,
                        raw_text_hint=f"Prescription for {med_name}"
                    )
                    count += 1
                except Exception as e:
                    logger.warning(f"Skip prescription {med_name}: {e}")
    else:
        logger.warning(f"File {indian_medicine_csv} not found.")

    try:
        logger.info("Create HITL case...")
        hitl.create_case(
            db=db,
            patient_id=patient.id,
            case_type="doctor_review",
            summary="Review recent eczema flare-up and epilepsy medication interactions.",
            urgency="high"
        )
    except Exception as e:
        logger.warning(f"HITL case fail: {e}")
        
    try:
        logger.info("Send welcome notification...")
        comms.notify(
            db=db,
            patient_id=patient.id,
            channel="mock_email",
            message_type="welcome",
            message_body="Welcome to nexus_ai demo workspace."
        )
    except Exception as e:
        logger.warning(f"Notify fail: {e}")
        
    try:
        logger.info("Store medical memory...")
        integrations.store_medical_memory(
            db=db,
            patient_id=patient.id,
            source_type="manual_upload",
            metadata={"note": "Initial patient setup notes"}
        )
    except Exception as e:
        logger.warning(f"Medical memory fail: {e}")
        
    db.close()
    logger.info("Seed complete.")

if __name__ == "__main__":
    seed_database()
