"""gRPC client for the Clinical service (Intake, Formulary, HITL, Comms, Questioner, Routine)."""
import json
import logging
from typing import Optional

import grpc

from nexus_ai.generated import clinical_pb2, clinical_pb2_grpc

logger = logging.getLogger(__name__)


class ClinicalClient:
    """Client wrapper for ClinicalService gRPC calls."""

    def __init__(self, host: str = "localhost", port: int = 50053) -> None:
        self.target = f"{host}:{port}"
        self.channel = grpc.insecure_channel(self.target)
        self.stub = clinical_pb2_grpc.ClinicalServiceStub(self.channel)
        logger.info("ClinicalClient connected to %s", self.target)

    # ─── Intake ─────────────────────────────────────────────────────

    def intake_patient(
        self,
        full_name: str,
        preferred_language: str = "en",
        date_of_birth: str = "",
        summary: str = "",
        condition_names: list[str] | None = None,
    ) -> dict:
        try:
            response = self.stub.IntakePatient(clinical_pb2.IntakeRequest(
                full_name=full_name,
                preferred_language=preferred_language,
                date_of_birth=date_of_birth,
                summary=summary,
                condition_names=condition_names or [],
            ))
            return {
                "success": response.success,
                "patient_id": response.patient_id,
                "full_name": response.full_name,
                "conditions_created": response.conditions_created,
                "message": response.message,
            }
        except grpc.RpcError as e:
            logger.error("ClinicalClient.intake_patient failed: %s", e.details())
            raise

    # ─── Prescription Scan ──────────────────────────────────────────

    def scan_prescription(
        self,
        patient_id: int,
        image_reference: str = "",
        raw_text_hint: str = "",
    ) -> dict:
        try:
            response = self.stub.ScanPrescription(clinical_pb2.PrescriptionScanRequest(
                patient_id=patient_id,
                image_reference=image_reference,
                raw_text_hint=raw_text_hint,
            ))
            return {
                "success": response.success,
                "prescription_id": response.prescription_id,
                "medication_name": response.medication_name,
                "dosage": response.dosage,
                "instructions": response.instructions,
                "confidence_score": response.confidence_score,
                "review_status": response.review_status,
                "message": response.message,
            }
        except grpc.RpcError as e:
            logger.error("ClinicalClient.scan_prescription failed: %s", e.details())
            raise

    # ─── Formulary / Alternatives ───────────────────────────────────

    def check_alternatives(
        self,
        medication_name: str,
        conditions: list[dict] | None = None,
    ) -> dict:
        cond_refs = [
            clinical_pb2.ConditionRef(
                name=c.get("name", ""),
                condition_type=c.get("condition_type", ""),
            )
            for c in (conditions or [])
        ]
        try:
            response = self.stub.CheckAlternatives(clinical_pb2.AlternativeCheckRequest(
                medication_name=medication_name,
                conditions=cond_refs,
            ))
            alternatives = [
                {
                    "medication_name": a.medication_name,
                    "rationale": a.rationale,
                    "is_generic": a.is_generic,
                    "fit_score": a.fit_score,
                }
                for a in response.alternatives
            ]
            return {
                "found": response.found,
                "alternatives": alternatives,
                "formulary_checked": response.formulary_checked,
                "summary": response.summary,
            }
        except grpc.RpcError as e:
            logger.error("ClinicalClient.check_alternatives failed: %s", e.details())
            raise

    # ─── HITL Escalation ────────────────────────────────────────────

    def create_escalation_case(
        self,
        patient_id: int,
        case_type: str,
        summary: str,
        doctor_id: int = 0,
        doctor_name: str = "",
        doctor_email: str = "",
        urgency: str = "",
    ) -> dict:
        try:
            response = self.stub.CreateEscalationCase(clinical_pb2.EscalationRequest(
                patient_id=patient_id, case_type=case_type, summary=summary,
                doctor_id=doctor_id, doctor_name=doctor_name,
                doctor_email=doctor_email, urgency=urgency,
            ))
            return {
                "success": response.success,
                "case_id": response.case_id,
                "status": response.status,
                "external_ticket_id": response.external_ticket_id,
                "external_ticket_url": response.external_ticket_url,
                "message": response.message,
            }
        except grpc.RpcError as e:
            logger.error("ClinicalClient.create_escalation_case failed: %s", e.details())
            raise

    # ─── Reports ────────────────────────────────────────────────────

    def build_detailed_report(self, patient_id: int, context_summary: str = "") -> dict:
        try:
            response = self.stub.BuildDetailedReport(clinical_pb2.ReportRequest(
                patient_id=patient_id, context_summary=context_summary,
            ))
            return {"success": response.success, "report_text": response.report_text}
        except grpc.RpcError as e:
            logger.error("ClinicalClient.build_detailed_report failed: %s", e.details())
            raise

    def build_ai_comprehension(
        self,
        patient_id: int,
        patient_name: str = "",
        patient_summary: str = "",
    ) -> dict:
        try:
            response = self.stub.BuildAIComprehension(clinical_pb2.ComprehensionRequest(
                patient_id=patient_id, patient_name=patient_name,
                patient_summary=patient_summary,
            ))
            return {
                "success": response.success,
                "patient_name": response.patient_name,
                "patient_dob": response.patient_dob,
                "patient_summary": response.patient_summary,
                "ai_analysis": response.ai_analysis,
                "conditions_json": response.conditions_json,
                "medications_json": response.medications_json,
            }
        except grpc.RpcError as e:
            logger.error("ClinicalClient.build_ai_comprehension failed: %s", e.details())
            raise

    # ─── Notification ───────────────────────────────────────────────

    def notify(
        self,
        patient_id: int,
        channel: str,
        message_type: str,
        message_body: str,
    ) -> dict:
        try:
            response = self.stub.Notify(clinical_pb2.NotifyRequest(
                patient_id=patient_id, channel=channel,
                message_type=message_type, message_body=message_body,
            ))
            return {
                "success": response.success,
                "notification_id": response.notification_id,
                "delivery_status": response.delivery_status,
                "message": response.message,
            }
        except grpc.RpcError as e:
            logger.error("ClinicalClient.notify failed: %s", e.details())
            raise

    # ─── Conversation Plan ──────────────────────────────────────────

    def build_conversation_plan(self, message: str, patient_id: int = 0) -> dict:
        try:
            response = self.stub.BuildConversationPlan(clinical_pb2.ConversationPlanRequest(
                message=message, patient_id=patient_id,
            ))
            return {
                "success": response.success,
                "plan": json.loads(response.plan_json) if response.plan_json else {},
                "message": response.message,
            }
        except grpc.RpcError as e:
            logger.error("ClinicalClient.build_conversation_plan failed: %s", e.details())
            raise

    # ─── Action Draft ───────────────────────────────────────────────

    def build_action_draft(self, patient_id: int, intent: str, message: str) -> dict:
        try:
            response = self.stub.BuildActionDraft(clinical_pb2.ActionDraftRequest(
                patient_id=patient_id, intent=intent, message=message,
            ))
            return {
                "success": response.success,
                "draft": json.loads(response.draft_json) if response.draft_json else {},
                "message": response.message,
            }
        except grpc.RpcError as e:
            logger.error("ClinicalClient.build_action_draft failed: %s", e.details())
            raise

    # ─── Daily Routine ──────────────────────────────────────────────

    def get_daily_routine(self) -> dict:
        try:
            response = self.stub.GetDailyRoutine(clinical_pb2.RoutineRequest())
            tasks = [
                {
                    "task_id": t.task_id,
                    "name": t.name,
                    "completed": t.completed,
                    "source": t.source,
                    "title": t.title,
                    "short_summary": t.short_summary,
                    "full_details": t.full_details,
                    "due_at": t.due_at,
                    "due_on": t.due_on,
                    "notes": t.notes,
                }
                for t in response.tasks
            ]
            snapshot = json.loads(response.snapshot_json) if response.snapshot_json else {}
            return {"success": response.success, "tasks": tasks, "snapshot": snapshot}
        except grpc.RpcError as e:
            logger.error("ClinicalClient.get_daily_routine failed: %s", e.details())
            raise

    # ─── Lifecycle ──────────────────────────────────────────────────

    def close(self) -> None:
        self.channel.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
