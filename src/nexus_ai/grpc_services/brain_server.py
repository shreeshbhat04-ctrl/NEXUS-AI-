"""Brain gRPC server — patient profiles and conditions."""
import logging
import os
from concurrent import futures

import grpc

from nexus_ai.config import get_settings
from nexus_ai.db.session import SessionLocal
from nexus_ai.services.brain import BrainService
from nexus_ai.generated import brain_pb2, brain_pb2_grpc

logger = logging.getLogger(__name__)


class BrainServiceServicer(brain_pb2_grpc.BrainServiceServicer):
    """gRPC servicer that wraps the existing BrainService."""

    def __init__(self) -> None:
        self.brain = BrainService()

    def Healthcheck(self, request, context):
        db = SessionLocal()
        try:
            result = self.brain.healthcheck(db)
            return brain_pb2.HealthResponse(
                healthy=result.get("healthy", True),
                message=result.get("message", "ok"),
                version="1.0.0",
            )
        except Exception as e:
            logger.exception("Healthcheck failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
        finally:
            db.close()

    def GetPatientProfile(self, request, context):
        db = SessionLocal()
        try:
            profile = self.brain.get_patient_profile(db, request.patient_id)
            if profile is None:
                return brain_pb2.PatientProfileResponse(found=False)

            conditions = []
            if hasattr(profile, "conditions") and profile.conditions:
                for c in profile.conditions:
                    conditions.append(brain_pb2.Condition(
                        id=getattr(c, "id", 0),
                        name=getattr(c, "name", ""),
                        condition_type=getattr(c, "condition_type", ""),
                        last_updated=str(getattr(c, "last_updated", "") or ""),
                        notes=getattr(c, "notes", "") or "",
                    ))

            return brain_pb2.PatientProfileResponse(
                found=True,
                id=profile.id,
                full_name=profile.full_name or "",
                preferred_language=profile.preferred_language or "en",
                date_of_birth=str(profile.date_of_birth or ""),
                summary=profile.summary or "",
                google_email=profile.google_email or "",
                conditions=conditions,
            )
        except Exception as e:
            logger.exception("GetPatientProfile failed for patient_id=%s", request.patient_id)
            context.abort(grpc.StatusCode.INTERNAL, str(e))
        finally:
            db.close()

    def GetRelevantConditions(self, request, context):
        db = SessionLocal()
        try:
            results = self.brain.get_relevant_conditions(db, request.patient_id)
            conditions = []
            for c in results:
                conditions.append(brain_pb2.Condition(
                    id=getattr(c, "id", 0),
                    name=getattr(c, "name", ""),
                    condition_type=getattr(c, "condition_type", ""),
                ))
            return brain_pb2.ConditionsResponse(
                patient_id=request.patient_id,
                conditions=conditions,
            )
        except Exception as e:
            logger.exception("GetRelevantConditions failed for patient_id=%s", request.patient_id)
            context.abort(grpc.StatusCode.INTERNAL, str(e))
        finally:
            db.close()


def serve() -> None:
    settings = get_settings()
    port = os.getenv("GRPC_PORT", str(settings.grpc_brain_port))
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    brain_pb2_grpc.add_BrainServiceServicer_to_server(BrainServiceServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"Brain gRPC service running on port {port}")
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()
