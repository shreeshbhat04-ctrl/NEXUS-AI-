"""gRPC client for the Vision service."""
import json
import logging

import grpc

from nexus_ai.generated import vision_pb2, vision_pb2_grpc

logger = logging.getLogger(__name__)


class VisionClient:
    """Client wrapper for VisionService gRPC calls."""

    def __init__(self, host: str = "localhost", port: int = 50054) -> None:
        self.target = f"{host}:{port}"
        self.channel = grpc.insecure_channel(self.target)
        self.stub = vision_pb2_grpc.VisionServiceStub(self.channel)
        logger.info("VisionClient connected to %s", self.target)

    def analyze_symptom_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        analysis_type: str,
    ) -> dict:
        try:
            response = self.stub.AnalyzeSymptomImage(vision_pb2.ImageAnalysisRequest(
                image_bytes=image_bytes,
                mime_type=mime_type,
                analysis_type=analysis_type,
            ))
            return {
                "success": response.success,
                "analysis": response.analysis,
                "classification": response.classification,
                "message": response.message,
            }
        except grpc.RpcError as e:
            logger.error("VisionClient.analyze_symptom_image failed: %s", e.details())
            raise

    def classify_medical_image(self, file_path: str) -> str:
        try:
            response = self.stub.ClassifyMedicalImage(vision_pb2.ImageClassifyRequest(
                file_path=file_path,
            ))
            return response.classification
        except grpc.RpcError as e:
            logger.error("VisionClient.classify_medical_image failed: %s", e.details())
            raise

    def auto_analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
    ) -> dict:
        try:
            response = self.stub.AutoAnalyzeImage(vision_pb2.ImageAnalysisRequest(
                image_bytes=image_bytes,
                mime_type=mime_type,
                analysis_type="",
            ))
            return {
                "success": response.success,
                "analysis": response.analysis,
                "classification": response.classification,
                "message": response.message,
            }
        except grpc.RpcError as e:
            logger.error("VisionClient.auto_analyze_image failed: %s", e.details())
            raise

    def generate_diagnostic_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        analysis_dict: dict,
    ) -> str:
        try:
            response = self.stub.GenerateDiagnosticImage(vision_pb2.DiagnosticImageRequest(
                image_bytes=image_bytes,
                mime_type=mime_type,
                analysis_dict_json=json.dumps(analysis_dict),
            ))
            return response.image_base64 if response.success else ""
        except grpc.RpcError as e:
            logger.error("VisionClient.generate_diagnostic_image failed: %s", e.details())
            raise

    def close(self) -> None:
        self.channel.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
