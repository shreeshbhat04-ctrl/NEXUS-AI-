"""gRPC client for the Integration service (Drive, Calendar, Gmail, Maps, Memory, Speech)."""
import json
import logging
from typing import Optional

import grpc

from nexus_ai.generated import integration_pb2, integration_pb2_grpc

logger = logging.getLogger(__name__)


class IntegrationClient:
    """Client wrapper for IntegrationService gRPC calls."""

    def __init__(self, host: str = "localhost", port: int = 50052) -> None:
        self.target = f"{host}:{port}"
        self.channel = grpc.insecure_channel(self.target)
        self.stub = integration_pb2_grpc.IntegrationServiceStub(self.channel)
        logger.info("IntegrationClient connected to %s", self.target)

    # ─── Document Upload ────────────────────────────────────────────

    def upload_document(
        self,
        patient_id: int,
        file_path: str,
        mime_type: str,
        document_category: str = "",
        prescription_id: int = 0,
    ) -> dict:
        try:
            response = self.stub.UploadDocument(integration_pb2.DocumentUploadRequest(
                patient_id=patient_id,
                file_path=file_path,
                mime_type=mime_type,
                document_category=document_category,
                prescription_id=prescription_id,
            ))
            return {
                "success": response.success,
                "drive_file_id": response.drive_file_id,
                "drive_file_url": response.drive_file_url,
                "drive_path": response.drive_path,
                "classification": response.classification,
                "message": response.message,
            }
        except grpc.RpcError as e:
            logger.error("IntegrationClient.upload_document failed: %s", e.details())
            raise

    # ─── Calendar ───────────────────────────────────────────────────

    def create_calendar_event(
        self,
        patient_id: int,
        summary: str,
        duration_minutes: int,
        offset_minutes: int,
        offset_days: int = 0,
        description: str = "",
    ) -> dict:
        try:
            response = self.stub.CreateCalendarEvent(integration_pb2.CalendarEventRequest(
                patient_id=patient_id,
                summary=summary,
                duration_minutes=duration_minutes,
                offset_minutes=offset_minutes,
                offset_days=offset_days,
                description=description,
            ))
            return {
                "success": response.success,
                "event_id": response.event_id,
                "event_url": response.event_url,
                "message": response.message,
            }
        except grpc.RpcError as e:
            logger.error("IntegrationClient.create_calendar_event failed: %s", e.details())
            raise

    # ─── Email ──────────────────────────────────────────────────────

    def send_care_email(self, to: str, subject: str, body_html: str) -> dict:
        try:
            response = self.stub.SendCareEmail(integration_pb2.EmailRequest(
                to=to, subject=subject, body_html=body_html,
            ))
            return {
                "success": response.success,
                "message_id": response.message_id,
                "message": response.message,
            }
        except grpc.RpcError as e:
            logger.error("IntegrationClient.send_care_email failed: %s", e.details())
            raise

    # ─── Drug Label ─────────────────────────────────────────────────

    def lookup_drug_label(self, medication_name: str) -> dict:
        try:
            response = self.stub.LookupDrugLabel(
                integration_pb2.DrugLabelRequest(medication_name=medication_name)
            )
            return {
                "found": response.found,
                "medication_name": response.medication_name,
                "summary": response.summary,
                "url": response.url,
                "raw_text": response.raw_text,
            }
        except grpc.RpcError as e:
            logger.error("IntegrationClient.lookup_drug_label failed: %s", e.details())
            raise

    # ─── Pharmacy Search ────────────────────────────────────────────

    def search_pharmacies(
        self,
        location_query: str,
        medication_name: str = "",
        latitude: float = 0.0,
        longitude: float = 0.0,
        radius_meters: int = 5000,
        max_results: int = 5,
    ) -> dict:
        try:
            response = self.stub.SearchPharmacies(integration_pb2.PharmacySearchRequest(
                location_query=location_query,
                medication_name=medication_name,
                latitude=latitude,
                longitude=longitude,
                radius_meters=radius_meters,
                max_results=max_results,
            ))
            results = [
                {
                    "name": p.name,
                    "address": p.address,
                    "latitude": p.latitude,
                    "longitude": p.longitude,
                    "rating": p.rating,
                    "open_now": p.open_now,
                    "place_id": p.place_id,
                }
                for p in response.results
            ]
            return {"success": response.success, "results": results, "message": response.message}
        except grpc.RpcError as e:
            logger.error("IntegrationClient.search_pharmacies failed: %s", e.details())
            raise

    # ─── Care Route ─────────────────────────────────────────────────

    def build_care_route(
        self,
        origin: str,
        destination: str,
        travel_mode: str = "driving",
        origin_lat: float = 0.0,
        origin_lng: float = 0.0,
    ) -> dict:
        try:
            response = self.stub.BuildCareRoute(integration_pb2.CareRouteRequest(
                origin=origin, destination=destination, travel_mode=travel_mode,
                origin_lat=origin_lat, origin_lng=origin_lng,
            ))
            return {
                "success": response.success,
                "distance": response.distance,
                "duration": response.duration,
                "summary": response.summary,
                "message": response.message,
            }
        except grpc.RpcError as e:
            logger.error("IntegrationClient.build_care_route failed: %s", e.details())
            raise

    # ─── Medical Memory ─────────────────────────────────────────────

    def store_medical_memory(
        self,
        patient_id: int,
        source_type: str,
        modality: str,
        content: str,
        source_reference: str = "",
        drive_file_id: str = "",
        drive_file_url: str = "",
        drive_path: str = "",
        metadata_json: str = "{}",
    ) -> dict:
        try:
            response = self.stub.StoreMedicalMemory(integration_pb2.StoreMemoryRequest(
                patient_id=patient_id, source_type=source_type, modality=modality,
                content=content, source_reference=source_reference,
                drive_file_id=drive_file_id, drive_file_url=drive_file_url,
                drive_path=drive_path, metadata_json=metadata_json,
            ))
            return {
                "success": response.success,
                "memory_id": response.memory_id,
                "vector_synced": response.vector_synced,
                "message": response.message,
            }
        except grpc.RpcError as e:
            logger.error("IntegrationClient.store_medical_memory failed: %s", e.details())
            raise

    def search_medical_memory(
        self,
        patient_id: int,
        query_text: str,
        modality: str = "",
        limit: int = 5,
    ) -> dict:
        try:
            response = self.stub.SearchMedicalMemory(integration_pb2.SearchMemoryRequest(
                patient_id=patient_id, query_text=query_text,
                modality=modality, limit=limit,
            ))
            results = [
                {
                    "memory_id": m.memory_id,
                    "source_type": m.source_type,
                    "source_reference": m.source_reference,
                    "modality": m.modality,
                    "embedding_model": m.embedding_model,
                    "summary_text": m.summary_text,
                    "drive_file_id": m.drive_file_id,
                    "drive_file_url": m.drive_file_url,
                    "similarity": m.similarity,
                }
                for m in response.results
            ]
            return {"success": response.success, "results": results, "message": response.message}
        except grpc.RpcError as e:
            logger.error("IntegrationClient.search_medical_memory failed: %s", e.details())
            raise

    # ─── Audio / Speech ─────────────────────────────────────────────

    def transcribe_audio(
        self,
        audio_bytes: bytes,
        encoding: str = "LINEAR16",
        sample_rate_hertz: int = 16000,
    ) -> dict:
        try:
            response = self.stub.TranscribeAudio(integration_pb2.AudioRequest(
                audio_bytes=audio_bytes, encoding=encoding,
                sample_rate_hertz=sample_rate_hertz,
            ))
            return {
                "success": response.success,
                "transcript": response.transcript,
                "confidence": response.confidence,
                "message": response.message,
            }
        except grpc.RpcError as e:
            logger.error("IntegrationClient.transcribe_audio failed: %s", e.details())
            raise

    def synthesize_speech(
        self,
        text: str,
        language_code: str = "en-US",
        voice_name: str = "",
    ) -> dict:
        try:
            response = self.stub.SynthesizeSpeech(integration_pb2.SpeechRequest(
                text=text, language_code=language_code, voice_name=voice_name,
            ))
            return {
                "success": response.success,
                "audio_content": response.audio_content,
                "content_type": response.content_type,
                "message": response.message,
            }
        except grpc.RpcError as e:
            logger.error("IntegrationClient.synthesize_speech failed: %s", e.details())
            raise

    # ─── Integration Event Logging ──────────────────────────────────

    def log_integration_event(self, event_type: str, payload_json: str = "{}") -> dict:
        try:
            response = self.stub.LogIntegrationEvent(integration_pb2.IntegrationEventRequest(
                event_type=event_type, payload_json=payload_json,
            ))
            return {"success": response.success, "message": response.message}
        except grpc.RpcError as e:
            logger.error("IntegrationClient.log_integration_event failed: %s", e.details())
            raise

    # ─── Lifecycle ──────────────────────────────────────────────────

    def close(self) -> None:
        self.channel.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
