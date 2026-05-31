from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_ai.db.models import Doctor, PatientDoctorMap


class QuestionerAgent:
    def build_action_draft(
        self,
        db: Session,
        patient_id: int,
        intent: str,
        message: str,
    ) -> dict:
        normalized_intent = intent.strip().lower()
        if normalized_intent == "doctor_handoff":
            return self._doctor_handoff_draft(db=db, patient_id=patient_id, message=message)
        if normalized_intent == "send_email":
            return self._send_email_draft(db=db, patient_id=patient_id, message=message)
        if normalized_intent == "calendar_followup":
            return self._calendar_draft(message=message)

        return {
            "intent": normalized_intent,
            "question": "Please choose how you want to proceed.",
            "options": [
                {"label": "Proceed with suggested action", "value": "suggested"},
                {"label": "Review details first", "value": "review"},
            ],
            "allow_custom_input": True,
            "preview": message,
        }

    def _doctor_handoff_draft(self, db: Session, patient_id: int, message: str) -> dict:
        rows = db.execute(
            select(Doctor, PatientDoctorMap)
            .join(PatientDoctorMap, PatientDoctorMap.doctor_id == Doctor.id)
            .where(PatientDoctorMap.patient_id == patient_id)
            .order_by(PatientDoctorMap.is_default.desc(), Doctor.full_name)
        ).all()

        options: list[dict] = []
        for doctor, mapping in rows[:2]:
            options.append(
                {
                    "label": f"{doctor.full_name} ({doctor.specialty or 'Doctor'})",
                    "value": str(doctor.id),
                    "doctor_id": doctor.id,
                    "is_default": bool(mapping.is_default),
                }
            )

        if not options:
            options = [
                {"label": "Use default care team doctor", "value": "default"},
                {"label": "Type doctor email manually", "value": "custom"},
            ]

        return {
            "intent": "doctor_handoff",
            "question": "Which doctor should receive this review?",
            "options": options,
            "allow_custom_input": True,
            "preview": message,
        }

    def _send_email_draft(self, db: Session, patient_id: int, message: str) -> dict:
        rows = db.execute(
            select(Doctor, PatientDoctorMap)
            .join(PatientDoctorMap, PatientDoctorMap.doctor_id == Doctor.id)
            .where(PatientDoctorMap.patient_id == patient_id, Doctor.email.is_not(None))
            .order_by(PatientDoctorMap.is_default.desc(), Doctor.full_name)
        ).all()

        options = [
            {
                "label": f"{doctor.full_name} <{doctor.email}>",
                "value": doctor.email,
                "doctor_id": doctor.id,
            }
            for doctor, _ in rows[:2]
            if doctor.email
        ]

        if len(options) < 2:
            options.append({"label": "Use custom email address", "value": "custom"})

        return {
            "intent": "send_email",
            "question": "Who should receive this care summary email?",
            "options": options,
            "allow_custom_input": True,
            "preview": message,
        }

    @staticmethod
    def _calendar_draft(message: str) -> dict:
        return {
            "intent": "calendar_followup",
            "question": "When should I create the follow-up?",
            "options": [
                {"label": "Today, 45 minutes from now", "value": "today_45"},
                {"label": "Tomorrow morning", "value": "tomorrow_morning"},
            ],
            "allow_custom_input": True,
            "preview": message,
        }
