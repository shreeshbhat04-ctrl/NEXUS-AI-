"""gRPC client for the Brain service (patient profiles & conditions)."""
import logging
from typing import Optional

import grpc

from nexus_ai.generated import brain_pb2, brain_pb2_grpc

logger = logging.getLogger(__name__)


class BrainClient:
    """Client wrapper for BrainService gRPC calls."""

    def __init__(self, host: str = "localhost", port: int = 50051) -> None:
        self.target = f"{host}:{port}"
        self.channel = grpc.insecure_channel(self.target)
        self.stub = brain_pb2_grpc.BrainServiceStub(self.channel)
        logger.info("BrainClient connected to %s", self.target)

    def healthcheck(self) -> dict:
        """Check brain service health."""
        try:
            response = self.stub.Healthcheck(brain_pb2.Empty())
            return {
                "healthy": response.healthy,
                "message": response.message,
                "version": response.version,
            }
        except grpc.RpcError as e:
            logger.error("BrainClient.healthcheck failed: %s", e.details())
            return {"healthy": False, "message": f"gRPC error: {e.details()}"}

    def get_patient_profile(self, patient_id: int) -> Optional[dict]:
        """Fetch a patient profile by ID. Returns None if not found."""
        try:
            response = self.stub.GetPatientProfile(
                brain_pb2.PatientProfileRequest(patient_id=patient_id)
            )
            if not response.found:
                return None
            conditions = [
                {
                    "id": c.id,
                    "name": c.name,
                    "condition_type": c.condition_type,
                    "last_updated": c.last_updated or None,
                    "notes": c.notes or None,
                }
                for c in response.conditions
            ]
            return {
                "id": response.id,
                "full_name": response.full_name,
                "preferred_language": response.preferred_language,
                "date_of_birth": response.date_of_birth or None,
                "summary": response.summary or None,
                "google_email": response.google_email or None,
                "conditions": conditions,
            }
        except grpc.RpcError as e:
            logger.error("BrainClient.get_patient_profile failed: %s", e.details())
            raise

    def get_relevant_conditions(self, patient_id: int) -> list[dict]:
        """Fetch relevant conditions for a patient."""
        try:
            response = self.stub.GetRelevantConditions(
                brain_pb2.ConditionsRequest(patient_id=patient_id)
            )
            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "condition_type": c.condition_type,
                }
                for c in response.conditions
            ]
        except grpc.RpcError as e:
            logger.error("BrainClient.get_relevant_conditions failed: %s", e.details())
            raise

    def close(self) -> None:
        """Close the gRPC channel."""
        self.channel.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
