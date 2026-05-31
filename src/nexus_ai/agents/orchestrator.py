import re
import json
from html import escape
from datetime import datetime
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_ai.agents.communications import CommunicationsAgent
from nexus_ai.agents.diet import DietAgent
from nexus_ai.agents.documents import DocumentAgent
from nexus_ai.agents.formulary import FormularyAgent
from nexus_ai.agents.hitl import HITLAgent
from nexus_ai.agents.integrations import IntegrationAgent
from nexus_ai.agents.intake import IntakeAgent
from nexus_ai.agents.questioner import QuestionerAgent
from nexus_ai.agents.routine import RoutineAgent
from nexus_ai.agents.temporal_memory import TemporalMemoryAgent
from nexus_ai.adapters.brain import BrainGateway, build_brain_gateway
from nexus_ai.db.models import Doctor, Notification, Patient, PatientDoctorMap, PendingAction, Prescription
from nexus_ai.services.google_workspace import credentials_from_tokens
from nexus_ai.services.model_routing import ModelRoutingService


class Orchestrator:
    def __init__(self, brain_gateway: BrainGateway | None = None) -> None:
        from nexus_ai.config import get_settings
        from nexus_ai.grpc_clients import BrainClient, ClinicalClient, DietClient, IntegrationClient, VisionClient
        from nexus_ai.grpc_clients.adapters import (
            BrainAdapter, ClinicalAdapter, RoutineAdapter, DietAdapter, IntegrationAdapter, DocumentAdapter
        )
        settings = get_settings()
        
        self.brain_client = BrainClient(settings.grpc_brain_host, settings.grpc_brain_port)
        self.clinical_client = ClinicalClient(settings.grpc_clinical_host, settings.grpc_clinical_port)
        self.diet_client = DietClient(settings.grpc_diet_host, settings.grpc_diet_port)
        self.integration_client = IntegrationClient(settings.grpc_integration_host, settings.grpc_integration_port)
        
        self.brain_gateway = BrainAdapter(self.brain_client)
        self.temporal_memory = BrainAdapter(self.brain_client)
        
        clinical_adapter = ClinicalAdapter(self.clinical_client)
        self.intake = clinical_adapter
        self.formulary = clinical_adapter
        self.hitl = clinical_adapter
        self.communications = clinical_adapter
        self.questioner = clinical_adapter
        
        self.routine = RoutineAdapter(self.clinical_client)
        self.diet = DietAdapter(self.diet_client)
        self.integrations = IntegrationAdapter(self.integration_client)
        self.documents = DocumentAdapter(self.integration_client)
        
        self.model_routing = ModelRoutingService()

    def evaluate_alternatives(self, patient_id: int, unavailable_medication: str):
        conditions = self.temporal_memory.get_relevant_conditions(patient_id)
        return self.formulary.check_alternatives(unavailable_medication, conditions)

    def build_daily_checkin(self, patient_id: int) -> dict:
        import re
        profile = self.brain_gateway.get_patient_profile(patient_id)
        conditions = self.temporal_memory.get_relevant_conditions(patient_id)
        all_tasks = self.routine.get_daily_routine()
        
        # Filter tasks using exact word boundaries so "Patient 1" doesn't match "Patient 12"
        patient_pattern = re.compile(rf"Patient {patient_id}\b", re.IGNORECASE)
        any_patient_pattern = re.compile(r"Patient \d+", re.IGNORECASE)
        
        routine_tasks = [
            task for task in all_tasks
            if patient_pattern.search(task.name)
            or not any_patient_pattern.search(task.name)
        ]
        
        message = self.communications.compose_daily_checkin(profile, conditions, routine_tasks)
        return {
            "profile": None if profile is None else profile.to_dict(),
            "conditions": [item.to_dict() for item in conditions],
            "routine_tasks": [task.__dict__ for task in routine_tasks],
            "message": message,
        }

    def build_diet_and_pharmacy_support(self, patient_id: int, medication_name: str | None, location_query: str | None) -> dict:
        conditions = self.temporal_memory.get_relevant_conditions(patient_id)
        diet_plan = self.diet.build_diet_support_plan(conditions, medication_name=medication_name, pharmacy_summary=None)
        return {
            "conditions": [item.to_dict() for item in conditions],
            "diet_plan": diet_plan,
            "pharmacy_result": {"provider": "disabled", "pharmacies": []},
        }

    def list_diet_recipes(
        self,
        patient_id: int,
        medication_name: str | None = None,
        meal_type: str | None = None,
    ) -> dict:
        conditions = self.temporal_memory.get_relevant_conditions(patient_id)
        recipes = self.diet.list_curated_recipes(
            meal_type=meal_type,
            medication_name=medication_name,
            conditions=conditions,
        )
        return {
            "patient_id": patient_id,
            "conditions": [item.to_dict() for item in conditions],
            "recipes": recipes,
        }

    def generate_diet_recipes(self, payload: dict) -> dict:
        patient_id = int(payload["patient_id"])
        conditions = self.temporal_memory.get_relevant_conditions(patient_id)
        recipe_result = self.diet.generate_recipes(
            conditions=conditions,
            medication_name=payload.get("medication_name"),
            preferences=payload,
        )
        return {
            "patient_id": patient_id,
            **recipe_result,
        }

    def scale_diet_recipe(
        self,
        patient_id: int,
        recipe_id: str,
        servings: int,
        medication_name: str | None = None,
    ) -> dict | None:
        conditions = self.temporal_memory.get_relevant_conditions(patient_id)
        return self.diet.scale_recipe(
            recipe_id=recipe_id,
            servings=servings,
            conditions=conditions,
            medication_name=medication_name,
        )

    def get_medicine_grounded_answer(self, patient_id: int, medication_name: str) -> dict:
        """
        Minimal grounded medicine answer for the frontend.

        Current grounding source is the existing Wikipedia/OpenFDA adapter used by `/drug/label`.
        This unblocks the Medication Hub flow until AlloyDB-grounded medicine lookup is implemented.
        """
        label = self.integrations.lookup_drug_label(medication_name)
        found = bool(label.get("found"))
        payload = label.get("label") or {}
        wiki_link = payload.get("url") or payload.get("page_url") or payload.get("link")

        # Keep this intentionally conservative: "safety_summary" is for UI display, not clinical advice.
        if found:
            summary_bits: list[str] = []
            title = payload.get("title") or medication_name
            if title:
                summary_bits.append(f"Found reference information for {title}.")
            snippet = payload.get("summary") or payload.get("extract") or payload.get("description")
            if isinstance(snippet, str) and snippet.strip():
                summary_bits.append(snippet.strip())
            safety_summary = " ".join(summary_bits).strip() or "Reference information was found."
            source_used = "wikipedia"
        else:
            safety_summary = (
                "I couldn't find a reliable reference entry for this medication name yet. "
                "Double-check spelling or try the generic name."
            )
            source_used = "unavailable"

        return {
            "patient_id": patient_id,
            "medication_name": medication_name,
            "safety_summary": safety_summary,
            "source_used": source_used,
            "wiki_link": wiki_link if isinstance(wiki_link, str) else None,
        }

    def build_document_pipeline(self, patient_id: int, file_path: str, raw_text_hint: str | None = None, prescription_id: int | None = None) -> dict:
        return self.documents.build_document_intake_plan(
            patient_id=patient_id,
            file_path=file_path,
            raw_text_hint=raw_text_hint,
            prescription_id=prescription_id,
        )

    def route_conversation(self, patient_id: int, message: str, db: Session | None = None) -> dict:
        profile = self.brain_gateway.get_patient_profile(patient_id)
        plan = self.communications.build_conversation_plan(message, profile=profile)

        draft_action = self._maybe_draft_conversation_action(
            db=db,
            patient_id=patient_id,
            message=message,
        )
        if draft_action is not None:
            plan["message"] = draft_action["question"]
            plan["execution_plan"] = [
                *plan["execution_plan"],
                "Collect explicit confirmation before executing a sensitive action.",
            ]
            plan["reason"] = f"{plan['reason']} Sensitive action requires confirmation.".strip()
            return {
                "patient_id": patient_id,
                "profile": None if profile is None else profile.to_dict(),
                **plan,
                **draft_action,
            }

        tool_outcome = self._maybe_execute_conversation_tool(
            db=db,
            patient_id=patient_id,
            message=message,
            patient_name=None if profile is None else profile.full_name,
        )
        if tool_outcome is not None:
            plan["message"] = tool_outcome["message"]
            plan["execution_plan"] = [*plan["execution_plan"], *tool_outcome["execution_plan"]]
            plan["reason"] = f"{plan['reason']} {tool_outcome['reason']}".strip()
        return {
            "patient_id": patient_id,
            "profile": None if profile is None else profile.to_dict(),
            **plan,
        }

    def _maybe_draft_conversation_action(
        self,
        db: Session | None,
        patient_id: int,
        message: str,
    ) -> dict | None:
        if db is None:
            return None

        normalized = message.lower().strip()
        intent: str | None = None
        if self._is_escalation_request(normalized):
            intent = "doctor_handoff"
        elif self._is_send_email_request(normalized):
            intent = "send_email"
        elif self._is_calendar_request(normalized):
            intent = "calendar_followup"

        if intent is None:
            return None

        return self.draft_action(db=db, patient_id=patient_id, intent=intent, message=message)

    def draft_action(self, db: Session, patient_id: int, intent: str, message: str) -> dict:
        draft = self.questioner.build_action_draft(
            db=db,
            patient_id=patient_id,
            intent=intent,
            message=message,
        )
        pending = PendingAction(
            patient_id=patient_id,
            action_type=draft["intent"],
            status="draft",
            draft_payload_json=json.dumps({"message": message}, ensure_ascii=True),
            options_json=json.dumps(draft.get("options", []), ensure_ascii=True),
            selected_option_json=None,
            result_json=None,
        )
        db.add(pending)
        db.commit()
        db.refresh(pending)
        return {
            "action_id": pending.id,
            "intent": draft["intent"],
            "question": draft["question"],
            "options": draft.get("options", []),
            "allow_custom_input": bool(draft.get("allow_custom_input", True)),
            "preview": draft.get("preview"),
        }

    def confirm_action(
        self,
        db: Session,
        action_id: int,
        selected_option: str | None,
        custom_input: str | None,
    ) -> dict:
        pending = db.scalar(select(PendingAction).where(PendingAction.id == action_id))
        if pending is None:
            raise ValueError("Pending action not found.")
        if pending.status != "draft":
            return {
                "action_id": pending.id,
                "status": pending.status,
                "result": self._json_load(pending.result_json),
            }

        options = self._json_load(pending.options_json)
        payload = self._json_load(pending.draft_payload_json)
        chosen_value = (custom_input or "").strip() or (selected_option or "").strip()
        chosen_option = next((item for item in options if str(item.get("value")) == selected_option), None)

        result: dict
        try:
            if pending.action_type == "doctor_handoff":
                doctor_id = None
                if chosen_option and chosen_option.get("doctor_id"):
                    doctor_id = int(chosen_option["doctor_id"])
                elif chosen_value.isdigit():
                    doctor_id = int(chosen_value)

                case = self.hitl.create_case(
                    db,
                    pending.patient_id,
                    "doctor_review",
                    payload.get("message") or "Doctor handoff requested from conversation.",
                    doctor_id=doctor_id,
                    urgency="high",
                )
                result = {
                    "message": "Doctor handoff created successfully.",
                    "case_id": case.id,
                    "external_ticket_id": case.external_ticket_id,
                    "external_ticket_url": case.external_ticket_url,
                }
            elif pending.action_type == "send_email":
                target_email = chosen_value
                doctor_id = None
                if chosen_option and chosen_option.get("doctor_id"):
                    doctor_id = int(chosen_option["doctor_id"])
                if chosen_option and chosen_option.get("value") not in (None, "custom"):
                    target_email = str(chosen_option["value"])

                email_result = self.send_doctor_aware_care_email(
                    db=db,
                    patient_id=pending.patient_id,
                    message=payload.get("message") or "Care summary requested from conversation.",
                    doctor_id=doctor_id,
                    to_email=target_email,
                )
                if not email_result.get("sent"):
                    raise ValueError(email_result.get("error") or "Email send failed")
                result = {
                    "message": f"Care summary email sent to {email_result['recipient']}.",
                    **email_result,
                }
            elif pending.action_type == "calendar_followup":
                minutes_from_now = 45
                if chosen_value == "tomorrow_morning":
                    now = datetime.now()
                    tomorrow = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
                    delta = tomorrow - now
                    minutes_from_now = max(30, int(delta.total_seconds() // 60))
                elif chosen_value.isdigit():
                    minutes_from_now = max(15, int(chosen_value))

                event = self.integrations.create_calendar_event(
                    db=db,
                    patient_id=pending.patient_id,
                    summary=f"Doctor follow-up for patient {pending.patient_id}",
                    minutes_from_now=minutes_from_now,
                    duration_minutes=30,
                )
                result = {
                    "message": "Follow-up calendar event created.",
                    "event_id": event.get("id"),
                    "html_link": event.get("htmlLink"),
                }
            else:
                result = {"message": "Action confirmed."}

            pending.status = "confirmed"
            pending.selected_option_json = json.dumps(
                {
                    "selected_option": selected_option,
                    "custom_input": custom_input,
                    "resolved": chosen_option,
                },
                ensure_ascii=True,
            )
            pending.result_json = json.dumps(result, ensure_ascii=True)
            pending.confirmed_at = datetime.utcnow()
            db.add(pending)
            db.commit()
            db.refresh(pending)
            return {
                "action_id": pending.id,
                "status": pending.status,
                "result": result,
            }
        except Exception as error:
            pending.status = "failed"
            pending.result_json = json.dumps({"message": str(error)}, ensure_ascii=True)
            pending.confirmed_at = datetime.utcnow()
            db.add(pending)
            db.commit()
            db.refresh(pending)
            return {
                "action_id": pending.id,
                "status": pending.status,
                "result": {"message": str(error)},
            }

    def list_pending_actions(self, db: Session, patient_id: int) -> list[dict]:
        rows = db.scalars(
            select(PendingAction)
            .where(PendingAction.patient_id == patient_id)
            .order_by(PendingAction.created_at.desc())
        ).all()
        return [
            {
                "action_id": item.id,
                "patient_id": item.patient_id,
                "action_type": item.action_type,
                "status": item.status,
                "options": self._json_load(item.options_json),
                "selected_option": self._json_load(item.selected_option_json),
                "result": self._json_load(item.result_json),
                "created_at": item.created_at.isoformat(),
                "confirmed_at": None if item.confirmed_at is None else item.confirmed_at.isoformat(),
            }
            for item in rows
        ]

    @staticmethod
    def _json_load(raw: str | None) -> dict | list:
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, (dict, list)):
                return parsed
        except json.JSONDecodeError:
            return {}
        return {}

    def _maybe_execute_conversation_tool(
        self,
        db: Session | None,
        patient_id: int,
        message: str,
        patient_name: str | None,
    ) -> dict | None:
        if db is None:
            return None

        normalized = message.lower().strip()

        if self._is_calendar_request(normalized):
            return self._execute_calendar_request(db=db, patient_id=patient_id, patient_name=patient_name)

        if self._is_health_email_list_request(normalized):
            return self._execute_health_email_list(db=db, patient_id=patient_id)

        if self._is_send_email_request(normalized):
            return self._execute_send_email(db=db, patient_id=patient_id, message=message, patient_name=patient_name)

        if self._is_escalation_request(normalized):
            return self._execute_escalation(db=db, patient_id=patient_id, message=message)

        if self._is_drive_request(normalized):
            return self._execute_drive_request(db=db, patient_id=patient_id, normalized=normalized)

        if self._is_prescription_lookup_request(normalized):
            return self._execute_prescription_lookup(db=db, patient_id=patient_id)

        return None

    def _execute_calendar_request(self, db: Session, patient_id: int, patient_name: str | None) -> dict:
        summary = f"Doctor follow-up for {patient_name or f'patient {patient_id}'}"
        result = self.integrations.create_calendar_event(
            db=db,
            patient_id=patient_id,
            summary=summary,
            minutes_from_now=45,
            duration_minutes=30,
        )
        return {
            "message": (
                "I created a follow-up appointment on the connected calendar. "
                + (
                    f"Open it here: {result.get('htmlLink')}"
                    if result.get("htmlLink")
                    else "It was created with the default follow-up window."
                )
            ),
            "reason": "The message requested booking or scheduling a doctor follow-up.",
            "execution_plan": [
                "Create a calendar follow-up event through the connected calendar integration.",
            ],
        }

    def _execute_health_email_list(self, db: Session, patient_id: int) -> dict:
        patient = db.scalar(select(Patient).where(Patient.id == patient_id))
        if not patient or not patient.google_access_token:
            return {
                "message": "I can check health emails after Google Gmail is connected for this patient.",
                "reason": "Email lookup requires stored Google OAuth tokens.",
                "execution_plan": [
                    "Ask the user to connect Google Gmail before reading inbox messages.",
                ],
            }

        creds = credentials_from_tokens(
            access_token=patient.google_access_token,
            refresh_token=patient.google_refresh_token,
        )
        emails = self.integrations.list_health_emails(credentials=creds, max_results=5)
        if not emails:
            return {
                "message": "I checked the connected Gmail account and didn’t find recent health-related emails.",
                "reason": "The message asked to inspect recent health emails.",
                "execution_plan": [
                    "Query recent health-related Gmail messages for the connected patient account.",
                ],
            }

        preview = "; ".join(email.get("subject", "(no subject)") for email in emails[:3])
        return {
            "message": f"I checked the connected Gmail account. Recent health-related emails include: {preview}.",
            "reason": "The message asked to inspect recent health emails.",
            "execution_plan": [
                "Query recent health-related Gmail messages for the connected patient account.",
            ],
        }

    def _execute_send_email(self, db: Session, patient_id: int, message: str, patient_name: str | None) -> dict:
        patient = db.scalar(select(Patient).where(Patient.id == patient_id))
        target_email_match = re.search(r"[\w.\-+]+@[\w.\-]+\.\w+", message)
        if target_email_match is None:
            return {
                "message": "I can send an email, but I need the recipient email address in the message.",
                "reason": "Email sending requires an explicit recipient address.",
                "execution_plan": [
                    "Ask for a concrete recipient email address before sending care summary mail.",
                ],
            }
        if not patient or not patient.google_access_token:
            return {
                "message": "I can send email after Google Gmail is connected for this patient.",
                "reason": "Email sending requires stored Google OAuth tokens.",
                "execution_plan": [
                    "Ask the user to connect Google Gmail before sending mail.",
                ],
            }

        email_result = self.send_doctor_aware_care_email(
            db=db,
            patient_id=patient_id,
            message=message,
            to_email=target_email_match.group(0),
        )
        if email_result.get("sent"):
            return {
                "message": f"I sent the care summary email to {email_result['recipient']}.",
                "reason": "The message requested sending a care summary email.",
                "execution_plan": [
                    "Send the care summary through the connected Gmail integration.",
                ],
            }
        return {
            "message": (
                f"I tried to send the email to {email_result['recipient']}, "
                f"but it failed: {email_result.get('error') or 'unknown error'}."
            ),
            "reason": "The message requested sending a care summary email.",
            "execution_plan": [
                "Attempt to send the care summary through the connected Gmail integration.",
            ],
        }

    def send_doctor_aware_care_email(
        self,
        db: Session,
        patient_id: int,
        message: str,
        doctor_id: int | None = None,
        to_email: str | None = None,
        subject: str | None = None,
        body_html: str | None = None,
    ) -> dict:
        patient = db.scalar(select(Patient).where(Patient.id == patient_id))
        if not patient or not patient.google_access_token:
            raise ValueError("Gmail is not connected for this patient.")

        doctor = None
        if doctor_id is not None:
            # Verify the doctor is mapped to this patient
            mapping = db.scalar(
                select(PatientDoctorMap).where(
                    PatientDoctorMap.patient_id == patient_id,
                    PatientDoctorMap.doctor_id == doctor_id
                )
            )
            if mapping is None:
                raise ValueError("Selected doctor is not associated with this patient.")

            doctor = db.scalar(select(Doctor).where(Doctor.id == doctor_id))
            if doctor is None:
                raise ValueError("Selected doctor was not found.")
            if not to_email:
                to_email = doctor.email
            if not to_email:
                raise ValueError("Selected doctor does not have an email address.")

        resolved_email = (to_email or "").strip()
        if "@" not in resolved_email:
            raise ValueError("Please provide a valid email address.")

        patient_name = patient.full_name or f"patient {patient_id}"
        creds = credentials_from_tokens(
            access_token=patient.google_access_token,
            refresh_token=patient.google_refresh_token,
        )
        resolved_subject = subject or f"nexus_ai care summary for {patient_name}"
        resolved_body_html = body_html or self._build_professional_care_email(
            db=db,
            patient_id=patient_id,
            patient_name=patient_name,
            patient_summary=patient.summary,
            message=message,
            doctor_name=None if doctor is None else doctor.full_name,
        )
        email_result = self.integrations.send_care_email(
            to=resolved_email,
            subject=resolved_subject,
            body_html=resolved_body_html,
            credentials=creds,
        )

        notification_status = "sent" if email_result.get("sent") else "failed"
        recipient_summary = resolved_email
        if doctor is not None:
            recipient_summary = f"{doctor.full_name} <{resolved_email}>"
        notification = Notification(
            patient_id=patient_id,
            channel="gmail",
            message_type="care_summary_email",
            body=(
                f"Care summary email to {recipient_summary}. "
                f"Message ID: {email_result.get('message_id') or 'unavailable'}."
            ),
            delivery_status=notification_status,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        return {
            "sent": bool(email_result.get("sent")),
            "message_id": email_result.get("message_id"),
            "error": email_result.get("error"),
            "recipient": resolved_email,
            "doctor_id": None if doctor is None else doctor.id,
            "doctor_name": None if doctor is None else doctor.full_name,
            "doctor_email": None if doctor is None else doctor.email,
            "notification_id": notification.id,
        }

    def _build_professional_care_email(
        self,
        db: Session,
        patient_id: int,
        patient_name: str | None,
        patient_summary: str | None,
        message: str,
        doctor_name: str | None = None,
    ) -> str:
        conditions = self.temporal_memory.get_relevant_conditions(patient_id)
        condition_names = [escape(item.name) for item in conditions if item.name][:3]
        recent_prescriptions = db.scalars(
            select(Prescription)
            .where(Prescription.patient_id == patient_id)
            .order_by(Prescription.created_at.desc())
        ).all()[:3]

        clean_request = escape(re.sub(r"[\w.\-+]+@[\w.\-]+\.\w+", "[recipient]", message).strip())
        patient_display_name = escape(patient_name or f"patient {patient_id}")
        doctor_display_name = escape(doctor_name or "Doctor")
        escaped_patient_summary = escape(patient_summary) if patient_summary else None
        sent_on = datetime.now().strftime("%Y-%m-%d")

        sections: list[str] = [
            f"<p>Respected {doctor_display_name},</p>",
            (
                f"<p>Please find a brief care update for <strong>{patient_display_name}</strong> "
                f"as of {sent_on}.</p>"
            ),
        ]

        if escaped_patient_summary:
            sections.append(f"<p><strong>Patient Summary:</strong> {escaped_patient_summary}</p>")

        if condition_names:
            sections.append(
                "<p><strong>Relevant Conditions:</strong> "
                + ", ".join(condition_names)
                + "</p>"
            )

        if recent_prescriptions:
            medication_summary = ", ".join(
                f"{escape(item.medication_name)}{f' {escape(item.dosage)}' if item.dosage else ''}".strip()
                for item in recent_prescriptions
                if item.medication_name
            )
            if medication_summary:
                sections.append(f"<p><strong>Recent Prescription History:</strong> {medication_summary}</p>")

        sections.append(f"<p><strong>Patient Request:</strong> {clean_request}</p>")
        sections.extend(
            [
                "<p>Please review and advise if any clinical follow-up is recommended.</p>",
                "<p>Regards,<br>nexus_ai Assistant</p>",
                "<p><em>This message is generated from the patient support workflow for care coordination.</em></p>",
            ]
        )
        return "".join(sections)

    def _execute_escalation(self, db: Session, patient_id: int, message: str) -> dict:
        case = self.hitl.create_case(db, patient_id, "doctor_review", message)
        return {
            "message": (
                "I created a doctor handoff for review."
                + (
                    f" Open it here: {case.external_ticket_url}"
                    if case.external_ticket_url
                    else ""
                )
            ),
            "reason": "The message requested escalation or doctor handoff.",
            "execution_plan": [
                "Create a doctor-review case through the escalation workflow.",
            ],
        }

    def _execute_prescription_lookup(self, db: Session, patient_id: int) -> dict:
        prescriptions = db.scalars(
            select(Prescription)
            .where(Prescription.patient_id == patient_id)
            .order_by(Prescription.created_at.desc())
        ).all()

        if not prescriptions:
            return {
                "message": "I don’t see any stored prescriptions for this patient yet.",
                "reason": "The message asked for the current prescription list.",
                "execution_plan": [
                    "Look up stored prescriptions from the patient workspace.",
                ],
            }

        recent = prescriptions[:3]
        summary = "; ".join(
            f"{item.medication_name}{f' {item.dosage}' if item.dosage else ''}".strip()
            for item in recent
        )
        return {
            "message": f"Here are the latest stored prescriptions: {summary}.",
            "reason": "The message asked for the current prescription list.",
            "execution_plan": [
                "Look up stored prescriptions from the patient workspace.",
            ],
        }

    def _execute_drive_request(self, db: Session, patient_id: int, normalized: str) -> dict:
        if self._is_drive_upload_request(normalized):
            return {
                "message": "I can upload to Drive when a file is attached, but chat and voice requests do not include a document payload yet.",
                "reason": "Drive upload from conversation needs an attached file or explicit file path.",
                "execution_plan": [
                    "Explain that Drive upload needs an attached file or explicit document reference.",
                ],
            }

        patient = db.scalar(select(Patient).where(Patient.id == patient_id))
        if not patient or not patient.google_access_token:
            return {
                "message": "I can check Drive after Google Drive is connected for this patient.",
                "reason": "Drive listing requires stored Google OAuth tokens.",
                "execution_plan": [
                    "Ask the user to connect Google Drive before browsing files.",
                ],
            }

        creds = credentials_from_tokens(
            access_token=patient.google_access_token,
            refresh_token=patient.google_refresh_token,
        )
        files = self.integrations.list_drive_files(credentials=creds, max_results=5)
        prescription_links = db.scalars(
            select(Prescription)
            .where(Prescription.patient_id == patient_id, Prescription.document_drive_file_url.is_not(None))
            .order_by(Prescription.created_at.desc())
        ).all()

        details: list[str] = []
        if files:
            file_summary = "; ".join(item.get("name", "Unnamed file") for item in files[:3])
            details.append(f"Recent Drive files: {file_summary}.")
        if prescription_links:
            prescription_summary = "; ".join(
                f"{item.medication_name}: {item.document_drive_file_url}"
                for item in prescription_links[:2]
            )
            details.append(f"Prescription docs: {prescription_summary}.")

        if not details:
            details.append("I checked Drive, but I didn’t find recent accessible files or stored prescription documents.")

        return {
            "message": " ".join(details),
            "reason": "The message requested Drive access or Drive-backed prescription references.",
            "execution_plan": [
                "Query recent accessible files from the connected Google Drive account.",
                "Cross-reference stored prescription documents with Drive links in the patient workspace.",
            ],
        }

    @staticmethod
    def _is_calendar_request(normalized: str) -> bool:
        schedule_terms = ("book", "schedule", "set up", "create")
        appointment_terms = ("appointment", "follow-up", "doctor visit", "calendar event", "meeting")
        return any(term in normalized for term in schedule_terms) and any(term in normalized for term in appointment_terms)

    @staticmethod
    def _is_health_email_list_request(normalized: str) -> bool:
        email_terms = ("email", "emails", "gmail", "inbox", "mail")
        lookup_terms = ("check", "show", "list", "read", "recent", "latest")
        return any(term in normalized for term in email_terms) and any(term in normalized for term in lookup_terms)

    @staticmethod
    def _is_send_email_request(normalized: str) -> bool:
        return ("send" in normalized or "email" in normalized) and (
            "@"
            in normalized
            or "mail to" in normalized
            or "doctor" in normalized
        )

    @staticmethod
    def _is_escalation_request(normalized: str) -> bool:
        escalation_terms = ("escalate", "handoff", "send to doctor", "doctor review", "send doctor")
        return any(term in normalized for term in escalation_terms)

    @staticmethod
    def _is_drive_request(normalized: str) -> bool:
        drive_terms = ("drive", "upload", "save file", "save to google drive", "google drive", "drive files", "drive documents")
        return any(term in normalized for term in drive_terms)

    @staticmethod
    def _is_drive_upload_request(normalized: str) -> bool:
        upload_terms = ("upload", "save file", "save to google drive")
        return any(term in normalized for term in upload_terms)

    @staticmethod
    def _is_prescription_lookup_request(normalized: str) -> bool:
        prescription_terms = ("prescription", "prescriptions", "medication list", "medicine list", "current meds", "current medication")
        lookup_terms = ("what", "show", "list", "check", "review", "current")
        return any(term in normalized for term in prescription_terms) and any(term in normalized for term in lookup_terms)

    def route_medical_input(self, patient_id: int, query_text: str | None = None, file_path: str | None = None) -> dict:
        profile = self.brain_gateway.get_patient_profile(patient_id)
        route = self.model_routing.route_medical_input(query_text=query_text, file_path=file_path)
        return {
            "patient_id": patient_id,
            "profile": None if profile is None else profile.to_dict(),
            "query_text": query_text,
            "file_path": file_path,
            **route,
        }

    def store_medical_memory(
        self,
        db,
        patient_id: int,
        source_type: str,
        query_text: str | None = None,
        file_path: str | None = None,
        drive_file_id: str | None = None,
        drive_file_url: str | None = None,
        metadata: dict | None = None,
        use_live_embedding: bool = False,
    ) -> dict:
        route = self.model_routing.route_medical_input(query_text=query_text, file_path=file_path)
        result = self.integrations.store_medical_memory(
            db=db,
            patient_id=patient_id,
            source_type=source_type,
            query_text=query_text,
            file_path=file_path,
            drive_file_id=drive_file_id,
            drive_file_url=drive_file_url,
            use_live_embedding=use_live_embedding,
            metadata={
                "route_type": route["route_type"],
                "route_reason": route["reason"],
                **(metadata or {}),
            },
        )
        return {
            **result,
            "route_type": route["route_type"],
            "route_reason": route["reason"],
        }

    def search_medical_memory(self, db, patient_id: int, query_text: str, modality: str | None = None, limit: int = 5) -> dict:
        profile = self.brain_gateway.get_patient_profile(patient_id)
        results = self.integrations.search_medical_memory(
            db=db,
            patient_id=patient_id,
            query_text=query_text,
            modality=modality,
            limit=limit,
        )
        return {
            "patient_id": patient_id,
            "profile": None if profile is None else profile.to_dict(),
            **results,
        }


    def get_orchestration_manifest(self, patient_id: int) -> dict:
        profile = self.brain_gateway.get_patient_profile(patient_id)
        conditions = self.temporal_memory.get_relevant_conditions(patient_id)
        routine_tasks = self.routine.get_daily_routine()
        return {
            "patient_id": patient_id,
            "profile": None if profile is None else profile.to_dict(),
            "conditions": [item.to_dict() for item in conditions],
            "routine_tasks": [task.__dict__ for task in routine_tasks],
            "agent_manifest": self.model_routing.get_model_manifest(),
            "trigger_manifest": {
                "general_conversation": "Gemini 3.1 Flash handles supportive and everyday conversation.",
                "medical_text_query": "Gemini 3.1 Flash handles symptom, disease, medicine, and clinical text queries.",
                "medical_image_upload": "Gemini 3.1 Flash handles the uploaded image directly to generate insights.",
            },
        }

    def run_document_intake_flow(
        self,
        db: Session,
        patient_id: int,
        image_reference: str | None = None,
        raw_text_hint: str | None = None,
        document_file_path: str | None = None,
        pharmacy_location_query: str | None = None,
        create_calendar_event: bool = True,
    ) -> dict:
        self.integrations.log_integration_event("workflow_started", {"patient_id": patient_id, "flow": "document_intake"})
        prescription = self.intake.scan_prescription(
            db=db,
            patient_id=patient_id,
            image_reference=image_reference,
            raw_text_hint=raw_text_hint,
        )

        drive_result = None
        if document_file_path:
            try:
                drive_result = self.integrations.upload_document(
                    db=db,
                    patient_id=patient_id,
                    file_path=document_file_path,
                    mime_type="application/pdf" if document_file_path.lower().endswith(".pdf") else "application/octet-stream",
                    prescription_id=prescription.id,
                )
            except Exception as error:
                drive_result = {"error": str(error)}

        memory_result = self.store_medical_memory(
            db=db,
            patient_id=patient_id,
            source_type="document_intake_flow",
            query_text=prescription.raw_text,
            file_path=document_file_path or image_reference,
            drive_file_id=None if not drive_result else drive_result.get("id"),
            drive_file_url=None if not drive_result else drive_result.get("webViewLink"),
            use_live_embedding=True,
            metadata={"prescription_id": prescription.id},
        )

        conditions = self.temporal_memory.get_relevant_conditions(patient_id)
        candidates, escalation_required, safety_summary = self.formulary.check_alternatives(prescription.medication_name, conditions)
        diet_support = self.diet.annotate_alternatives(candidates, conditions)
        pharmacy_result = {"provider": "disabled", "pharmacies": []} if pharmacy_location_query else None

        case = None
        calendar_result = None
        flow_notes: list[str] = []
        if prescription.review_status == "manual_review_required":
            flow_notes.append("OCR confidence below threshold. Manual review required.")
            escalation_required = True
        if escalation_required:
            report = self.hitl.build_detailed_report(db, patient_id, f"{safety_summary}\nMedication: {prescription.medication_name}")
            case = self.hitl.create_case(db, patient_id, "doctor_review", report)
            flow_notes.append("HITL case created.")
            if create_calendar_event:
                try:
                    calendar_result = self.integrations.create_calendar_event(
                        db=db,
                        patient_id=patient_id,
                        summary=f"Doctor follow-up for {prescription.medication_name}",
                        minutes_from_now=45,
                        duration_minutes=30,
                        escalation_case_id=case.id,
                    )
                except Exception as error:
                    calendar_result = {"error": str(error)}

        notification = self.communications.notify(
            db=db,
            patient_id=patient_id,
            channel="mock_email",
            message_type="workflow_update",
            message_body=(
                "We reviewed your uploaded medication details. "
                + ("A doctor follow-up has been prepared." if escalation_required else "No urgent review is needed right now.")
            ),
        )

        self.integrations.log_integration_event(
            "document_intake_flow_completed",
            {
                "patient_id": patient_id,
                "prescription_id": prescription.id,
                "escalation_required": escalation_required,
                "case_id": None if case is None else case.id,
                "calendar_event_id": None if not calendar_result else calendar_result.get("id"),
                "memory_id": memory_result["memory_id"],
            },
        )

        return {
            "patient_id": patient_id,
            "prescription": {
                "id": prescription.id,
                "medication_name": prescription.medication_name,
                "dosage": prescription.dosage,
                "instructions": prescription.instructions,
                "confidence_score": prescription.confidence_score,
                "review_status": prescription.review_status,
            },
            "document_pipeline": self.build_document_pipeline(
                patient_id=patient_id,
                file_path=document_file_path or image_reference or "inline-input",
                raw_text_hint=raw_text_hint,
                prescription_id=prescription.id,
            ),
            "drive_result": drive_result,
            "memory_result": memory_result,
            "alternatives": [candidate.model_dump() for candidate in candidates],
            "diet_support": diet_support,
            "pharmacy_result": pharmacy_result,
            "escalation_required": escalation_required,
            "safety_summary": safety_summary,
            "case": None
            if case is None
            else {
                "case_id": case.id,
                "status": case.status,
                "external_ticket_id": case.external_ticket_id,
                "external_ticket_url": case.external_ticket_url,
            },
            "calendar_result": calendar_result,
            "notification": {
                "notification_id": notification.id,
                "delivery_status": notification.delivery_status,
            },
            "flow_notes": flow_notes,
        }

    def run_routine_automation(self, db: Session, patient_id: int) -> dict:
        profile = self.brain_gateway.get_patient_profile(patient_id)
        conditions = self.temporal_memory.get_relevant_conditions(patient_id)
        snapshot = self.routine.get_routine_snapshot()
        message = self.communications.compose_daily_checkin(profile, conditions, snapshot["tasks"])
        case = None
        if snapshot["risk_level"] == "high":
            report = self.hitl.build_detailed_report(db, patient_id, snapshot["routine_summary"])
            case = self.hitl.create_case(db, patient_id, "routine_nonadherence", report)

        self.integrations.log_integration_event(
            "routine_automation_evaluated",
            {
                "patient_id": patient_id,
                "risk_level": snapshot["risk_level"],
                "overdue_count": snapshot["overdue_count"],
                "case_id": None if case is None else case.id,
            },
        )
        return {
            "patient_id": patient_id,
            "profile": None if profile is None else profile.to_dict(),
            "routine_tasks": [task.__dict__ for task in snapshot["tasks"]],
            "routine_summary": snapshot["routine_summary"],
            "risk_level": snapshot["risk_level"],
            "overdue_count": snapshot["overdue_count"],
            "due_today_count": snapshot["due_today_count"],
            "message": message,
            "case": None
            if case is None
            else {
                "case_id": case.id,
                "status": case.status,
                "external_ticket_id": case.external_ticket_id,
                "external_ticket_url": case.external_ticket_url,
            },
        }
