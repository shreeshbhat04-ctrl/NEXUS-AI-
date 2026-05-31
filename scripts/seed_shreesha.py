"""Seed Shreesha (Patient 2) with Eczema + Epilepsy demo story.

Run with:
    .venv\\Scripts\\python.exe scripts/seed_shreesha.py
"""
from datetime import date, datetime, timedelta, UTC

from nexus_ai.db.bootstrap import init_database
from nexus_ai.db.models import ChronicCondition, Doctor, Patient, PatientDoctorMap, Prescription
from nexus_ai.db.session import SessionLocal


# ── Drive file references ──────────────────────────────────────────
# Replace these with the real Google Drive file IDs and URLs for your
# eczema / epilepsy document images once uploaded.
ECZEMA_DOC_DRIVE_FILE_ID = "1aQG7xEbVDFFkZOMrOTYsihooP51Yv_UY"          # e.g. "1aBcDeFgHiJkLmNoPqRsTuVwXyZ"
ECZEMA_DOC_DRIVE_FILE_URL = "https://drive.google.com/drive/folders/1aQG7xEbVDFFkZOMrOTYsihooP51Yv_UY"         # e.g. "https://drive.google.com/file/d/1aBc.../view"
EPILEPSY_DOC_DRIVE_FILE_ID = None        # e.g. "1zYxWvUtSrQpOnMlKjIhGfEdCbA"
EPILEPSY_DOC_DRIVE_FILE_URL = None       # e.g. "https://drive.google.com/file/d/1zYx.../view"


def main() -> None:
    init_database()

    with SessionLocal() as db:
        # Upsert patient 2
        patient = db.get(Patient, 2)
        if patient is None:
            patient = Patient(id=2)
            db.add(patient)

        patient.full_name = "Shreesha"
        patient.preferred_language = "en"
        patient.date_of_birth = date(2002, 4, 4)
        patient.google_email = "shreeshbhat04@gmail.com"
        patient.summary = (
            "22-year-old male managing chronic atopic eczema (moderate-severe, "
            "flare-prone on forearms and neck) and focal epilepsy (diagnosed age 19, "
            "currently controlled with anti-epileptic medication). Requires monitoring "
            "for drug interactions between dermatological corticosteroids and "
            "neurological treatments. Patient is tech-savvy and prefers digital "
            "communication for care coordination."
        )
        db.flush()

        # ── Conditions ──
        # Remove old conditions for patient 2 to avoid duplicates
        for old in patient.conditions:
            db.delete(old)
        db.flush()

        db.add(ChronicCondition(
            patient_id=2,
            name="Atopic Eczema",
            condition_type="chronic",
            last_updated=date.today(),
            notes=(
                "Moderate-severe atopic dermatitis. Recurrent flares on forearms, "
                "neck, and behind knees. Triggered by stress and weather changes. "
                "Currently managed with topical corticosteroids and emollients."
            ),
        ))
        db.add(ChronicCondition(
            patient_id=2,
            name="Focal Epilepsy",
            condition_type="chronic",
            last_updated=date.today(),
            notes=(
                "Focal onset seizures diagnosed at age 19. Last seizure 4 months ago. "
                "Well-controlled on Levetiracetam. EEG shows occasional focal "
                "epileptiform discharges in the left temporal lobe. No surgical "
                "intervention planned at this time."
            ),
        ))

        # ── Prescriptions ──
        for old in patient.prescriptions:
            db.delete(old)
        db.flush()

        db.add(Prescription(
            patient_id=2,
            source_reference="eczema_prescription_scan.jpg",
            raw_text="Apply Clobetasol Propionate 0.05% cream to affected areas twice daily for 14 days. Taper to once daily for 7 days. Use emollient liberally between applications.",
            medication_name="Clobetasol Propionate 0.05% Cream",
            dosage="Apply twice daily (tapering)",
            instructions="Apply thin layer to eczema flare areas on forearms and neck. Avoid face and groin. Use emollient 30 min before corticosteroid. Review after 3 weeks.",
            confidence_score=0.92,
            review_status="approved",
            document_drive_file_id=ECZEMA_DOC_DRIVE_FILE_ID,
            document_drive_file_url=ECZEMA_DOC_DRIVE_FILE_URL,
            created_at=datetime.now(UTC) - timedelta(days=14),
        ))
        db.add(Prescription(
            patient_id=2,
            source_reference="epilepsy_prescription_scan.jpg",
            raw_text="Divalproex 500mg tablets. Take one tablet twice daily (morning and evening). Do not stop abruptly — taper under medical supervision.",
            medication_name="Divalproex 500mg",
            dosage="500mg twice daily",
            instructions="Take with food to reduce GI side effects. Do not discontinue abruptly. Report mood changes, unusual bruising, or increased seizure frequency immediately.",
            confidence_score=0.95,
            review_status="approved",
            document_drive_file_id=EPILEPSY_DOC_DRIVE_FILE_ID,
            document_drive_file_url=EPILEPSY_DOC_DRIVE_FILE_URL,
            created_at=datetime.now(UTC) - timedelta(days=30),
        ))

        doctor = db.query(Doctor).filter(Doctor.asana_user_gid == "1214276322986923").one_or_none()
        if doctor is None:
            doctor = Doctor(asana_user_gid="1214276322986923")
            db.add(doctor)
        doctor.full_name = "Dr surgeon"
        doctor.specialty = "Gynacologist"
        doctor.email = "sreeshhb@gmail.com"
        doctor.asana_workspace_gid = "1213916290149152"
        doctor.profile_image_key = "surgeon"
        db.flush()

        for old_default in db.query(PatientDoctorMap).filter(
            PatientDoctorMap.patient_id == 2,
            PatientDoctorMap.is_default.is_(True),
            PatientDoctorMap.doctor_id != doctor.id,
        ):
            old_default.is_default = False

        mapping = db.query(PatientDoctorMap).filter(
            PatientDoctorMap.patient_id == 2,
            PatientDoctorMap.doctor_id == doctor.id,
        ).one_or_none()
        if mapping is None:
            mapping = PatientDoctorMap(patient_id=2, doctor_id=doctor.id)
            db.add(mapping)
        mapping.relationship_type = "primary"
        mapping.is_default = True
        mapping.notes = "Default doctor for Asana Care Approvals routing."

        db.commit()
        print(f"✓ Seeded Patient {patient.id}: {patient.full_name}")
        print(f"  Conditions: Atopic Eczema, Focal Epilepsy")
        print(f"  Prescriptions: Clobetasol Propionate, Levetiracetam 500mg")
        print(f"  Email: {patient.google_email}")
        print(f"  Default doctor: {doctor.full_name} ({doctor.asana_user_gid})")
        if ECZEMA_DOC_DRIVE_FILE_ID:
            print(f"  Eczema doc: {ECZEMA_DOC_DRIVE_FILE_URL}")
        else:
            print("  ⚠ Eczema doc Drive IDs not set — edit lines 17-18 in this file")
        if EPILEPSY_DOC_DRIVE_FILE_ID:
            print(f"  Epilepsy doc: {EPILEPSY_DOC_DRIVE_FILE_URL}")
        else:
            print("  ⚠ Epilepsy doc Drive IDs not set — edit lines 19-20 in this file")


if __name__ == "__main__":
    main()
