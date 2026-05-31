"""Adapters to proxy Orchestrator agent calls to gRPC clients."""
import json
from types import SimpleNamespace
from datetime import datetime

class BrainAdapter:
    def __init__(self, client):
        self.client = client

    def get_patient_profile(self, patient_id):
        res = self.client.get_patient_profile(patient_id)
        if not res:
            return None
        # Return something that behaves like the PatientProfile model
        class MockProfile:
            def __init__(self, d):
                self.id = d.get("id")
                self.full_name = d.get("full_name")
                self.preferred_language = d.get("preferred_language")
                self.date_of_birth = d.get("date_of_birth")
                self.summary = d.get("summary")
                self._d = d
            def to_dict(self):
                return self._d
        return MockProfile(res)

    def get_relevant_conditions(self, patient_id):
        res = self.client.get_relevant_conditions(patient_id)
        class MockCondition:
            def __init__(self, d):
                self.id = d.get("id")
                self.name = d.get("name")
                self.condition_type = d.get("condition_type")
                self._d = d
            def to_dict(self):
                return self._d
        return [MockCondition(c) for c in res]


class ClinicalAdapter:
    def __init__(self, client):
        self.client = client

    def scan_prescription(self, db, patient_id, image_reference=None, raw_text_hint=None):
        res = self.client.scan_prescription(patient_id, image_reference, raw_text_hint)
        return SimpleNamespace(
            id=res.get("prescription_id"),
            medication_name=res.get("medication_name"),
            dosage=res.get("dosage"),
            instructions=res.get("instructions"),
            confidence_score=res.get("confidence_score"),
            review_status=res.get("review_status"),
            raw_text=raw_text_hint,
        )

    def check_alternatives(self, medication_name, conditions):
        conds = [c.to_dict() if hasattr(c, "to_dict") else c.__dict__ for c in conditions]
        res = self.client.check_alternatives(medication_name, conds)
        candidates = [SimpleNamespace(**a) for a in res.get("alternatives", [])]
        return candidates, res.get("formulary_checked", False), res.get("summary", "")

    def create_case(self, db, patient_id, case_type, summary, doctor_id=None, doctor_name=None, doctor_email=None, urgency=None):
        res = self.client.create_escalation_case(
            patient_id, case_type, summary, doctor_id or 0, doctor_name or "", doctor_email or "", urgency or ""
        )
        return SimpleNamespace(
            id=res.get("case_id"),
            status=res.get("status"),
            external_ticket_id=res.get("external_ticket_id"),
            external_ticket_url=res.get("external_ticket_url"),
        )

    def build_detailed_report(self, db, patient_id, context_summary=""):
        res = self.client.build_detailed_report(patient_id, context_summary)
        return res.get("report_text", "")

    def notify(self, db, patient_id, channel, message_type, message_body):
        res = self.client.notify(patient_id, channel, message_type, message_body)
        return SimpleNamespace(
            id=res.get("notification_id"),
            delivery_status=res.get("delivery_status"),
        )

    def compose_daily_checkin(self, profile, conditions, tasks):
        return "Daily check-in from your care team." # Simple mock for comms compose

    def build_conversation_plan(self, message, profile=None):
        res = self.client.build_conversation_plan(message, profile.id if profile else 0)
        return res.get("plan", {})

    def build_action_draft(self, db, patient_id, intent, message):
        res = self.client.build_action_draft(patient_id, intent, message)
        return res.get("draft", {})


class RoutineAdapter:
    def __init__(self, client):
        self.client = client

    def get_daily_routine(self):
        res = self.client.get_daily_routine()
        tasks = res.get("tasks", [])
        return [SimpleNamespace(**t) for t in tasks]

    def get_routine_snapshot(self):
        res = self.client.get_daily_routine()
        return res.get("snapshot", {})


class DietAdapter:
    def __init__(self, client):
        self.client = client

    def build_diet_support_plan(self, conditions, medication_name=None, pharmacy_summary=None):
        conds = [c.to_dict() if hasattr(c, "to_dict") else c.__dict__ for c in conditions]
        res = self.client.build_diet_plan(conds, medication_name or "", pharmacy_summary or "")
        return res.get("plan", {})

    def list_curated_recipes(self, meal_type=None, medication_name=None, conditions=None):
        conds = [c.to_dict() if hasattr(c, "to_dict") else c.__dict__ for c in (conditions or [])]
        return self.client.list_recipes(meal_type or "", medication_name or "", conds)

    def generate_recipes(self, conditions, medication_name=None, preferences=None):
        conds = [c.to_dict() if hasattr(c, "to_dict") else c.__dict__ for c in conditions]
        return self.client.generate_recipes(conds, medication_name or "", preferences or {})

    def scale_recipe(self, recipe_id, servings, conditions, medication_name=None):
        conds = [c.to_dict() if hasattr(c, "to_dict") else c.__dict__ for c in conditions]
        res = self.client.scale_recipe(recipe_id, servings, conds, medication_name or "")
        return res.get("recipe")

    def annotate_alternatives(self, candidates, conditions):
        return {} # Mock for diet support


class IntegrationAdapter:
    def __init__(self, client):
        self.client = client
        from nexus_ai.agents.integrations import IntegrationAgent
        self.fallback = IntegrationAgent()

    def create_calendar_event(self, db, patient_id, summary, minutes_from_now, duration_minutes, escalation_case_id=None):
        return self.client.create_calendar_event(
            patient_id, summary, duration_minutes, minutes_from_now
        )

    def list_health_emails(self, credentials, max_results=5):
        return self.fallback.list_health_emails(credentials, max_results)

    def send_care_email(self, to, subject, body_html, credentials=None):
        return self.client.send_care_email(to, subject, body_html)

    def list_drive_files(self, credentials, max_results=5):
        return self.fallback.list_drive_files(credentials, max_results)

    def upload_document(self, db, patient_id, file_path, mime_type, prescription_id=None):
        return self.client.upload_document(patient_id, file_path, mime_type, "", prescription_id or 0)

    def lookup_drug_label(self, medication_name):
        return self.client.lookup_drug_label(medication_name)

    def store_medical_memory(self, db, patient_id, source_type, query_text=None, file_path=None, drive_file_id=None, drive_file_url=None, use_live_embedding=False, metadata=None):
        content = query_text or file_path or "No content"
        return self.client.store_medical_memory(
            patient_id, source_type, "text", content, file_path or "", drive_file_id or "", drive_file_url or "", json.dumps(metadata or {})
        )

    def search_medical_memory(self, db, patient_id, query_text, modality=None, limit=5):
        return self.client.search_medical_memory(patient_id, query_text, modality or "", limit)

    def log_integration_event(self, event_type, payload):
        return self.client.log_integration_event(event_type, json.dumps(payload))


class DocumentAdapter:
    def __init__(self, integration_client):
        self.client = integration_client
    
    def build_document_intake_plan(self, patient_id, file_path, raw_text_hint=None, prescription_id=None):
        from nexus_ai.agents.documents import DocumentAgent
        return DocumentAgent().build_document_intake_plan(patient_id, file_path, raw_text_hint, prescription_id)

