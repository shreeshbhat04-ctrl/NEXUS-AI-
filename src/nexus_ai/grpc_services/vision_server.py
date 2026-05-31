"""Vision gRPC server — Gemini Vision and Image Classification."""
import json
import logging
import os
from concurrent import futures

import grpc

from nexus_ai.config import get_settings
from nexus_ai.services.gemini_vision import GeminiVisionService
from nexus_ai.services.image_classifier import ImageClassifierService
from nexus_ai.generated import vision_pb2, vision_pb2_grpc

logger = logging.getLogger(__name__)


class VisionServiceServicer(vision_pb2_grpc.VisionServiceServicer):
    """gRPC servicer wrapping Vision services."""

    def __init__(self) -> None:
        self.gemini_vision = GeminiVisionService()
        self.image_classifier = ImageClassifierService()

    def AnalyzeSymptomImage(self, request, context):
        try:
            result = self.gemini_vision.analyze_symptom_image(
                image_bytes=request.image_bytes,
                mime_type=request.mime_type,
                analysis_type=request.analysis_type,
            )
            return vision_pb2.ImageAnalysisResponse(
                success=result.get("success", True),
                analysis=result.get("analysis", ""),
                classification=result.get("classification", ""),
                message=result.get("message", ""),
            )
        except Exception as e:
            logger.exception("AnalyzeSymptomImage failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def ClassifyMedicalImage(self, request, context):
        try:
            classification = self.image_classifier.classify_medical_image(
                file_path=request.file_path,
            )
            return vision_pb2.ImageClassifyResponse(
                classification=classification,
            )
        except Exception as e:
            logger.exception("ClassifyMedicalImage failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def AutoAnalyzeImage(self, request, context):
        try:
            result = self.gemini_vision.auto_analyze_image(
                image_bytes=request.image_bytes,
                mime_type=request.mime_type,
                file_path=None, # In-memory
            )
            return vision_pb2.ImageAnalysisResponse(
                success=result.get("success", True),
                analysis=result.get("analysis", ""),
                classification=result.get("classification", ""),
                message=result.get("message", ""),
            )
        except Exception as e:
            logger.exception("AutoAnalyzeImage failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def GenerateDiagnosticImage(self, request, context):
        try:
            analysis_dict = json.loads(request.analysis_dict_json) if request.analysis_dict_json else {}
            image_base64 = self.gemini_vision.generate_diagnostic_image(
                image_bytes=request.image_bytes,
                mime_type=request.mime_type,
                analysis=analysis_dict,
            )
            return vision_pb2.DiagnosticImageResponse(
                success=True if image_base64 else False,
                image_base64=image_base64 or "",
                message="Image generated" if image_base64 else "Failed to generate image",
            )
        except Exception as e:
            logger.exception("GenerateDiagnosticImage failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))


def serve() -> None:
    settings = get_settings()
    port = os.getenv("GRPC_PORT", str(settings.grpc_vision_port))
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    vision_pb2_grpc.add_VisionServiceServicer_to_server(VisionServiceServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"Vision gRPC service running on port {port}")
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()
