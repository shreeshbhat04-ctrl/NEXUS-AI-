"""Doctor gRPC server — ADK Agent module."""
import logging
import os
import asyncio
from concurrent import futures

import grpc

from nexus_ai.config import get_settings
from nexus_ai.generated import doctor_pb2, doctor_pb2_grpc

# Note: since doctor module uses ADK (which is async), we need to handle the event loop.
from nexus_ai_doctor.adk.agent import root_doctor_agent

logger = logging.getLogger(__name__)


class DoctorAgentServiceServicer(doctor_pb2_grpc.DoctorAgentServiceServicer):
    """gRPC servicer wrapping Doctor ADK Agent."""

    def __init__(self) -> None:
        pass

    def Healthcheck(self, request, context):
        return doctor_pb2.HealthResponse(
            healthy=True,
            message="Doctor agent is ready",
            version="1.0.0",
        )

    def Chat(self, request, context):
        try:
            # We must run the async generate_response in a new event loop
            # since gRPC servicer threads don't have an event loop by default.
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response_text = loop.run_until_complete(
                root_doctor_agent.generate_response(request.message)
            )
            loop.close()

            return doctor_pb2.DoctorChatResponse(
                success=True,
                response=response_text,
                message="Chat generated.",
            )
        except Exception as e:
            logger.exception("Chat failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))


def serve() -> None:
    settings = get_settings()
    port = os.getenv("GRPC_PORT", str(settings.grpc_doctor_port))
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    doctor_pb2_grpc.add_DoctorAgentServiceServicer_to_server(DoctorAgentServiceServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"Doctor gRPC service running on port {port}")
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()
