from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy import select

from nexus_ai.adapters.ticketing import TicketingAdapter, build_ticketing_adapter
from nexus_ai.db.models import ChronicCondition, Doctor, EscalationCase, Notification, Prescription


class HITLAgent:
    def __init__(self, ticketing_adapter: TicketingAdapter | None = None) -> None:
        self.ticketing_adapter = ticketing_adapter or build_ticketing_adapter()

    def create_case(
        self,
        db: Session,
        patient_id: int,
        case_type: str,
        summary: str,
        doctor_id: int | None = None,
        doctor_name: str | None = None,
        doctor_email: str | None = None,
        urgency: str | None = None,
    ) -> EscalationCase:
        if doctor_id is not None:
            doctor = db.scalar(select(Doctor).where(Doctor.id == doctor_id))
            if doctor is not None:
                doctor_name = doctor_name or doctor.full_name
                doctor_email = doctor_email or doctor.email

        # Simplified ticketing adapter usage
        ticket = self.ticketing_adapter.create_review_ticket(
            patient_id=patient_id,
            summary=summary,
            case_type=case_type,
            doctor_name=doctor_name,
            urgency=urgency,
        )
        case = EscalationCase(
            patient_id=patient_id,
            case_type=case_type,
            status=ticket.status,
            summary=summary,
            doctor_id=doctor_id,
            doctor_name=doctor_name,
            doctor_email=doctor_email,
            urgency=urgency,
            external_ticket_id=ticket.ticket_id,
            external_ticket_url=ticket.external_url,
        )
        db.add(case)
        db.commit()
        db.refresh(case)
        return case

    def build_detailed_report(self, db: Session, patient_id: int, context_summary: str | None = None) -> str:
        conditions = db.scalars(select(ChronicCondition).where(ChronicCondition.patient_id == patient_id)).all()
        prescriptions = db.scalars(select(Prescription).where(Prescription.patient_id == patient_id)).all()
        notifications = db.scalars(select(Notification).where(Notification.patient_id == patient_id)).all()

        condition_lines = ", ".join(f"{item.name} ({item.condition_type})" for item in conditions) or "No conditions recorded."
        prescription_lines = (
            "; ".join(
                f"{item.medication_name} {item.dosage or ''} [{item.review_status}]".strip()
                for item in prescriptions
            )
            or "No prescriptions recorded."
        )
        notification_lines = (
            "; ".join(f"{item.message_type}:{item.delivery_status}" for item in notifications[-5:])
            or "No recent patient communications."
        )

        sections = [
            f"Patient ID: {patient_id}",
            f"Clinical context: {condition_lines}",
            f"Medication history: {prescription_lines}",
            f"Communication history: {notification_lines}",
        ]
        if context_summary:
            sections.append(f"Latest concern: {context_summary}")
        return "\n".join(sections)

    def build_ai_comprehension(self, db: Session, patient_id: int, patient_name: str | None = None, patient_summary: str | None = None) -> dict:
        """Generate a comprehensive AI-powered HITL review using Gemini."""
        from nexus_ai.db.models import Patient
        
        # Gather all data
        patient = db.scalar(select(Patient).where(Patient.id == patient_id))
        conditions = list(db.scalars(select(ChronicCondition).where(ChronicCondition.patient_id == patient_id)).all())
        prescriptions = list(db.scalars(select(Prescription).where(Prescription.patient_id == patient_id)).all())
        
        # Build structured patient data
        today = date.today()
        
        patient_info = {
            "name": patient.full_name if patient else (patient_name or "Unknown"),
            "dob": str(patient.date_of_birth) if patient and patient.date_of_birth else None,
            "summary": patient.summary if patient else patient_summary,
        }
        
        condition_data = []
        for c in conditions:
            condition_data.append({
                "name": c.name,
                "type": c.condition_type,
                "last_updated": str(c.last_updated) if c.last_updated else None,
                "notes": c.notes,
            })
        
        medication_data = []
        for p in prescriptions:
            days_on_med = (today - p.created_at.date()).days if p.created_at else None
            medication_data.append({
                "name": p.medication_name,
                "dosage": p.dosage,
                "instructions": p.instructions,
                "review_status": p.review_status,
                "days_on_medication": days_on_med,
                "confidence_score": p.confidence_score,
            })
        
        # Build prompt for Gemini
        prompt = f"""You are a medical AI assistant performing a Human-in-the-Loop (HITL) comprehensive patient review.

PATIENT PROFILE:
- Name: {patient_info['name']}
- Date of Birth: {patient_info['dob'] or 'Not recorded'}
- Clinical Summary: {patient_info['summary'] or 'No summary available'}

ACTIVE CONDITIONS:
{chr(10).join(f"- {c['name']} ({c['type']}), Last updated: {c['last_updated'] or 'N/A'}, Notes: {c['notes'] or 'None'}" for c in condition_data) if condition_data else '- No conditions recorded'}

CURRENT MEDICATIONS:
{chr(10).join(f"- {m['name']} {m['dosage'] or ''}, Status: {m['review_status']}, Days on medication: {m['days_on_medication'] or 'Unknown'}, Instructions: {m['instructions'] or 'None'}" for m in medication_data) if medication_data else '- No medications recorded'}

Please provide a structured HITL review with:
1. **Patient Comprehension**: A clear, human-readable summary of who this patient is and their current health state.
2. **Symptom & Condition Analysis**: What conditions they have, how they interact, and any concerns.
3. **Medication Review**: Each medication, how long they've been on it, and whether the duration/dosage seems appropriate.
4. **Recommended Actions**: What should happen next (continue, adjust, escalate to doctor, schedule follow-up).
5. **Reasoning**: Why you recommend each action, grounded in the patient data.
6. **dont use key words like ** ## or any special symbols ,tone your response from point to pointin a professional but caring manner, and be concise yet thorough in your analysis.

Keep the tone professional but caring. Be concise but thorough."""

        # Call Gemini
        try:
            from google import genai
            from nexus_ai.config import get_settings
            settings = get_settings()
            client = genai.Client(api_key=settings.google_api_key)
            response = client.models.generate_content(
                model=settings.gemini_fast_model_id,
                contents=prompt,
                config=genai.types.GenerateContentConfig(temperature=0.3),
            )
            ai_analysis = response.text.strip()
        except Exception as e:
            ai_analysis = f"AI analysis unavailable: {e}"

        return {
            "patient": patient_info,
            "conditions": condition_data,
            "medications": medication_data,
            "ai_analysis": ai_analysis,
        }
