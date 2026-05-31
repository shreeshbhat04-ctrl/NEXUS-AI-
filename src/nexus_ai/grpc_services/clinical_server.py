"""Clinical gRPC server — Intake, Formulary, HITL, Communications, Questioner, Routine."""
import json
import logging
import os
from concurrent import futures

import grpc

from nexus_ai.config import get_settings
from nexus_ai.db.session import SessionLocal
from nexus_ai.agents.intake import IntakeAgent
from nexus_ai.agents.formulary import FormularyAgent
from nexus_ai.agents.hitl import HITLAgent
from nexus_ai.agents.communications import CommunicationsAgent
from nexus_ai.agents.questioner import QuestionerAgent
from nexus_ai.agents.routine import RoutineAgent
from nexus_ai.generated import clinical_pb2, clinical_pb2_grpc

logger = logging.getLogger(__name__)


class ClinicalServiceServicer(clinical_pb2_grpc.ClinicalServiceServicer):
    """gRPC servicer wrapping clinical workflow agents."""

    def __init__(self) -> None:
        self.intake = IntakeAgent()
        self.formulary = FormularyAgent()
        self.hitl = HITLAgent()
        self.communications = CommunicationsAgent()
        self.questioner = QuestionerAgent()
        self.routine = RoutineAgent()

    # ─── Intake ─────────────────────────────────────────────────────

    def IntakePatient(self, request, context):
        db = SessionLocal()
        try:
            from nexus_ai.api.models import PatientIntakeRequest
            payload = PatientIntakeRequest(
                full_name=request.full_name,
                preferred_language=request.preferred_language or "en",
                date_of_birth=request.date_of_birth or None,
                summary=request.summary or None,
                conditions=list(request.condition_names) if request.condition_names else [],
            )
            patient = self.intake.intake_patient(db, payload)
            return clinical_pb2.IntakeResponse(
                success=True,
                patient_id=patient.id,
                full_name=patient.full_name,
                conditions_created=len(request.condition_names),
                message="Patient intake completed.",
            )
        except Exception as e:
            logger.exception("IntakePatient failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
        finally:
            db.close()

    # ─── Prescription Scan ──────────────────────────────────────────

    def ScanPrescription(self, request, context):
        db = SessionLocal()
        try:
            prescription = self.intake.scan_prescription(
                db=db,
                patient_id=request.patient_id,
                image_reference=request.image_reference or None,
                raw_text_hint=request.raw_text_hint or None,
            )
            return clinical_pb2.PrescriptionScanResponse(
                success=True,
                prescription_id=prescription.id,
                medication_name=prescription.medication_name or "",
                dosage=prescription.dosage or "",
                instructions=prescription.instructions or "",
                confidence_score=prescription.confidence_score or 0.0,
                review_status=prescription.review_status or "pending",
                message="Prescription scanned.",
            )
        except Exception as e:
            logger.exception("ScanPrescription failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
        finally:
            db.close()

    # ─── Formulary / Alternatives ───────────────────────────────────

    def CheckAlternatives(self, request, context):
        try:
            # Build BrainCondition-like objects from the request
            from types import SimpleNamespace
            conditions = [
                SimpleNamespace(name=c.name, condition_type=c.condition_type)
                for c in request.conditions
            ]
            alternatives, formulary_checked, summary = self.formulary.check_alternatives(
                medication_name=request.medication_name,
                conditions=conditions,
            )
            alt_protos = []
            for alt in alternatives:
                alt_protos.append(clinical_pb2.AlternativeCandidate(
                    medication_name=getattr(alt, "medication_name", ""),
                    rationale=getattr(alt, "rationale", ""),
                    is_generic=getattr(alt, "is_generic", False),
                    fit_score=getattr(alt, "fit_score", 0.0),
                ))
            return clinical_pb2.AlternativeCheckResponse(
                found=len(alternatives) > 0,
                alternatives=alt_protos,
                formulary_checked=formulary_checked,
                summary=summary,
            )
        except Exception as e:
            logger.exception("CheckAlternatives failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    # ─── HITL Escalation ────────────────────────────────────────────

    def CreateEscalationCase(self, request, context):
        db = SessionLocal()
        try:
            case = self.hitl.create_case(
                db=db,
                patient_id=request.patient_id,
                case_type=request.case_type,
                summary=request.summary,
                doctor_id=request.doctor_id or None,
                doctor_name=request.doctor_name or None,
                doctor_email=request.doctor_email or None,
                urgency=request.urgency or None,
            )
            return clinical_pb2.EscalationResponse(
                success=True,
                case_id=case.id,
                status=case.status or "open",
                external_ticket_id=case.external_ticket_id or "",
                external_ticket_url=case.external_ticket_url or "",
                message="Escalation case created.",
            )
        except Exception as e:
            logger.exception("CreateEscalationCase failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
        finally:
            db.close()

    # ─── Detailed Report ────────────────────────────────────────────

    def BuildDetailedReport(self, request, context):
        db = SessionLocal()
        try:
            report_text = self.hitl.build_detailed_report(
                db=db,
                patient_id=request.patient_id,
                context_summary=request.context_summary or None,
            )
            return clinical_pb2.ReportResponse(
                success=True,
                report_text=report_text,
            )
        except Exception as e:
            logger.exception("BuildDetailedReport failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
        finally:
            db.close()

    # ─── AI Comprehension ───────────────────────────────────────────

    def BuildAIComprehension(self, request, context):
        db = SessionLocal()
        try:
            result = self.hitl.build_ai_comprehension(
                db=db,
                patient_id=request.patient_id,
                patient_name=request.patient_name or None,
                patient_summary=request.patient_summary or None,
            )
            return clinical_pb2.ComprehensionResponse(
                success=True,
                patient_name=result.get("patient", {}).get("name", ""),
                patient_dob=result.get("patient", {}).get("dob", ""),
                patient_summary=result.get("patient", {}).get("summary", ""),
                ai_analysis=result.get("ai_analysis", ""),
                conditions_json=json.dumps(result.get("conditions", [])),
                medications_json=json.dumps(result.get("medications", [])),
            )
        except Exception as e:
            logger.exception("BuildAIComprehension failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
        finally:
            db.close()

    # ─── Notification ───────────────────────────────────────────────

    def Notify(self, request, context):
        db = SessionLocal()
        try:
            notification = self.communications.notify(
                db=db,
                patient_id=request.patient_id,
                channel=request.channel,
                message_type=request.message_type,
                message_body=request.message_body,
            )
            return clinical_pb2.NotifyResponse(
                success=True,
                notification_id=notification.id,
                delivery_status=notification.delivery_status or "queued",
                message="Notification sent.",
            )
        except Exception as e:
            logger.exception("Notify failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
        finally:
            db.close()

    # ─── Conversation Plan ──────────────────────────────────────────

    def BuildConversationPlan(self, request, context):
        try:
            result = self.communications.build_conversation_plan(
                message=request.message,
                profile=None,  # Profile can be fetched via brain service if needed
            )
            return clinical_pb2.ConversationPlanResponse(
                success=True,
                plan_json=json.dumps(result),
                message="Conversation plan built.",
            )
        except Exception as e:
            logger.exception("BuildConversationPlan failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    # ─── Action Draft ───────────────────────────────────────────────

    def BuildActionDraft(self, request, context):
        db = SessionLocal()
        try:
            result = self.questioner.build_action_draft(
                db=db,
                patient_id=request.patient_id,
                intent=request.intent,
                message=request.message,
            )
            return clinical_pb2.ActionDraftResponse(
                success=True,
                draft_json=json.dumps(result),
                message="Action draft built.",
            )
        except Exception as e:
            logger.exception("BuildActionDraft failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
        finally:
            db.close()

    # ─── Daily Routine ──────────────────────────────────────────────

    def GetDailyRoutine(self, request, context):
        try:
            tasks = self.routine.get_daily_routine()
            task_protos = []
            for t in tasks:
                task_protos.append(clinical_pb2.RoutineTask(
                    task_id=getattr(t, "task_id", ""),
                    name=getattr(t, "name", ""),
                    completed=getattr(t, "completed", False),
                    source=getattr(t, "source", "Internal"),
                    title=getattr(t, "title", "") or "",
                    short_summary=getattr(t, "short_summary", "") or "",
                    full_details=getattr(t, "full_details", "") or "",
                    due_at=getattr(t, "due_at", "") or "",
                    due_on=getattr(t, "due_on", "") or "",
                    notes=getattr(t, "notes", "") or "",
                ))
            snapshot = self.routine.get_routine_snapshot()
            return clinical_pb2.RoutineResponse(
                success=True,
                tasks=task_protos,
                snapshot_json=json.dumps(snapshot),
            )
        except Exception as e:
            logger.exception("GetDailyRoutine failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))


def serve() -> None:
    settings = get_settings()
    port = os.getenv("GRPC_PORT", str(settings.grpc_clinical_port))
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    clinical_pb2_grpc.add_ClinicalServiceServicer_to_server(
        ClinicalServiceServicer(), server
    )
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"Clinical gRPC service running on port {port}")
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()
