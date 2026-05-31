"""Integration gRPC server — Drive, Calendar, Gmail, Maps, Memory, Speech."""
import json
import logging
import os
from concurrent import futures

import grpc

from nexus_ai.config import get_settings
from nexus_ai.db.session import SessionLocal
from nexus_ai.agents.integrations import IntegrationAgent
from nexus_ai.generated import integration_pb2, integration_pb2_grpc

logger = logging.getLogger(__name__)


class IntegrationServiceServicer(integration_pb2_grpc.IntegrationServiceServicer):
    """gRPC servicer wrapping IntegrationAgent."""

    def __init__(self) -> None:
        self.agent = IntegrationAgent()

    # ─── Document Upload ────────────────────────────────────────────

    def UploadDocument(self, request, context):
        db = SessionLocal()
        try:
            result = self.agent.upload_document(
                db=db,
                patient_id=request.patient_id,
                file_path=request.file_path,
                mime_type=request.mime_type,
                document_category=request.document_category or None,
                prescription_id=request.prescription_id or None,
            )
            return integration_pb2.DocumentUploadResponse(
                success=result.get("success", True),
                drive_file_id=result.get("drive_file_id", ""),
                drive_file_url=result.get("drive_file_url", ""),
                drive_path=result.get("drive_path", ""),
                classification=result.get("classification", ""),
                message=result.get("message", "uploaded"),
            )
        except Exception as e:
            logger.exception("UploadDocument failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
        finally:
            db.close()

    # ─── Calendar ───────────────────────────────────────────────────

    def CreateCalendarEvent(self, request, context):
        db = SessionLocal()
        try:
            result = self.agent.create_calendar_event(
                db=db,
                patient_id=request.patient_id,
                summary=request.summary,
                duration_minutes=request.duration_minutes,
                offset_minutes=request.offset_minutes,
                offset_days=request.offset_days or None,
            )
            return integration_pb2.CalendarEventResponse(
                success=result.get("success", True),
                event_id=result.get("event_id", ""),
                event_url=result.get("event_url", ""),
                message=result.get("message", "created"),
            )
        except Exception as e:
            logger.exception("CreateCalendarEvent failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
        finally:
            db.close()

    # ─── Email ──────────────────────────────────────────────────────

    def SendCareEmail(self, request, context):
        try:
            result = self.agent.send_care_email(
                to=request.to,
                subject=request.subject,
                body_html=request.body_html,
            )
            return integration_pb2.EmailResponse(
                success=result.get("success", True),
                message_id=result.get("message_id", ""),
                message=result.get("message", "sent"),
            )
        except Exception as e:
            logger.exception("SendCareEmail failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    # ─── Drug Label ─────────────────────────────────────────────────

    def LookupDrugLabel(self, request, context):
        try:
            result = self.agent.lookup_drug_label(request.medication_name)
            return integration_pb2.DrugLabelResponse(
                found=result.get("found", False),
                medication_name=result.get("medication_name", request.medication_name),
                summary=result.get("summary", ""),
                url=result.get("url", ""),
                raw_text=result.get("raw_text", ""),
            )
        except Exception as e:
            logger.exception("LookupDrugLabel failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    # ─── Pharmacy Search ────────────────────────────────────────────

    def SearchPharmacies(self, request, context):
        try:
            result = self.agent.search_nearby_pharmacies(
                location_query=request.location_query,
                medication_name=request.medication_name or None,
                latitude=request.latitude or None,
                longitude=request.longitude or None,
                radius_meters=request.radius_meters or 5000,
                max_results=request.max_results or 5,
            )
            pharmacies = []
            for p in result.get("results", []):
                pharmacies.append(integration_pb2.PharmacyResult(
                    name=p.get("name", ""),
                    address=p.get("address", ""),
                    latitude=p.get("latitude", 0.0),
                    longitude=p.get("longitude", 0.0),
                    rating=p.get("rating", 0.0),
                    open_now=p.get("open_now", False),
                    place_id=p.get("place_id", ""),
                ))
            return integration_pb2.PharmacySearchResponse(
                success=result.get("success", True),
                results=pharmacies,
                message=result.get("message", ""),
            )
        except Exception as e:
            logger.exception("SearchPharmacies failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    # ─── Care Route ─────────────────────────────────────────────────

    def BuildCareRoute(self, request, context):
        try:
            result = self.agent.build_care_route(
                origin=request.origin,
                destination=request.destination,
                travel_mode=request.travel_mode or "driving",
                origin_lat=request.origin_lat or None,
                origin_lng=request.origin_lng or None,
            )
            return integration_pb2.CareRouteResponse(
                success=result.get("success", True),
                distance=result.get("distance", ""),
                duration=result.get("duration", ""),
                summary=result.get("summary", ""),
                message=result.get("message", ""),
            )
        except Exception as e:
            logger.exception("BuildCareRoute failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    # ─── Medical Memory ─────────────────────────────────────────────

    def StoreMedicalMemory(self, request, context):
        db = SessionLocal()
        try:
            result = self.agent.store_medical_memory(
                db=db,
                patient_id=request.patient_id,
                source_type=request.source_type,
                modality=request.modality,
                content=request.content,
                source_reference=request.source_reference or None,
                drive_file_id=request.drive_file_id or None,
                drive_file_url=request.drive_file_url or None,
                drive_path=request.drive_path or None,
                metadata=json.loads(request.metadata_json) if request.metadata_json else None,
            )
            return integration_pb2.StoreMemoryResponse(
                success=result.get("success", True),
                memory_id=result.get("memory_id", 0),
                vector_synced=result.get("vector_synced", False),
                message=result.get("message", "stored"),
            )
        except Exception as e:
            logger.exception("StoreMedicalMemory failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
        finally:
            db.close()

    def SearchMedicalMemory(self, request, context):
        db = SessionLocal()
        try:
            result = self.agent.search_medical_memory(
                db=db,
                patient_id=request.patient_id,
                query_text=request.query_text,
                modality=request.modality or None,
                limit=request.limit or 5,
            )
            memories = []
            for m in result.get("results", []):
                memories.append(integration_pb2.MemoryResult(
                    memory_id=m.get("memory_id", 0),
                    source_type=m.get("source_type", ""),
                    source_reference=m.get("source_reference", ""),
                    modality=m.get("modality", ""),
                    embedding_model=m.get("embedding_model", ""),
                    summary_text=m.get("summary_text", ""),
                    drive_file_id=m.get("drive_file_id", ""),
                    drive_file_url=m.get("drive_file_url", ""),
                    similarity=m.get("similarity", 0.0),
                ))
            return integration_pb2.SearchMemoryResponse(
                success=result.get("success", True),
                results=memories,
                message=result.get("message", ""),
            )
        except Exception as e:
            logger.exception("SearchMedicalMemory failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
        finally:
            db.close()

    # ─── Audio / Speech ─────────────────────────────────────────────

    def TranscribeAudio(self, request, context):
        try:
            result = self.agent.transcribe_audio(request.audio_bytes)
            return integration_pb2.TranscriptionResponse(
                success=result.get("success", True),
                transcript=result.get("transcript", ""),
                confidence=result.get("confidence", 0.0),
                message=result.get("message", ""),
            )
        except Exception as e:
            logger.exception("TranscribeAudio failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def SynthesizeSpeech(self, request, context):
        try:
            result = self.agent.synthesize_speech(request.text)
            return integration_pb2.SpeechResponse(
                success=result.get("success", True),
                audio_content=result.get("audio_content", b""),
                content_type=result.get("content_type", "audio/wav"),
                message=result.get("message", ""),
            )
        except Exception as e:
            logger.exception("SynthesizeSpeech failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    # ─── Integration Event Logging ──────────────────────────────────

    def LogIntegrationEvent(self, request, context):
        try:
            payload = json.loads(request.payload_json) if request.payload_json else {}
            result = self.agent.log_integration_event(request.event_type, payload)
            return integration_pb2.IntegrationEventResponse(
                success=result.get("success", True),
                message=result.get("message", "logged"),
            )
        except Exception as e:
            logger.exception("LogIntegrationEvent failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))


def serve() -> None:
    settings = get_settings()
    port = os.getenv("GRPC_PORT", str(settings.grpc_integration_port))
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    integration_pb2_grpc.add_IntegrationServiceServicer_to_server(
        IntegrationServiceServicer(), server
    )
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"Integration gRPC service running on port {port}")
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()
