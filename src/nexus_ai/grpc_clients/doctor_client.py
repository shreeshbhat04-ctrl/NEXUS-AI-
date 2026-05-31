"""gRPC client for the Doctor service."""
import logging
from typing import Optional

import grpc

from nexus_ai.generated import doctor_pb2, doctor_pb2_grpc

logger = logging.getLogger(__name__)


class DoctorClient:
    """Client wrapper for DoctorAgentService gRPC calls."""

    def __init__(self, host: str = "localhost", port: int = 50056) -> None:
        self.target = f"{host}:{port}"
        self.channel = grpc.insecure_channel(self.target)
        self.stub = doctor_pb2_grpc.DoctorAgentServiceStub(self.channel)
        logger.info("DoctorClient connected to %s", self.target)

    def healthcheck(self) -> dict:
        """Check doctor service health."""
        try:
            response = self.stub.Healthcheck(doctor_pb2.Empty())
            return {
                "healthy": response.healthy,
                "message": response.message,
                "version": response.version,
            }
        except grpc.RpcError as e:
            logger.error("DoctorClient.healthcheck failed: %s", e.details())
            return {"healthy": False, "message": f"gRPC error: {e.details()}"}

    def chat(self, message: str) -> dict:
        """Chat with the Doctor ADK agent."""
        try:
            response = self.stub.Chat(doctor_pb2.DoctorChatRequest(
                message=message,
            ))
            return {
                "success": response.success,
                "response": response.response,
                "message": response.message,
            }
        except grpc.RpcError as e:
            logger.error("DoctorClient.chat failed: %s", e.details())
            raise

    def close(self) -> None:
        """Close the gRPC channel."""
        self.channel.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
