"""gRPC client wrappers for inter-service communication."""
from nexus_ai.grpc_clients.brain_client import BrainClient
from nexus_ai.grpc_clients.integration_client import IntegrationClient
from nexus_ai.grpc_clients.clinical_client import ClinicalClient
from nexus_ai.grpc_clients.vision_client import VisionClient
from nexus_ai.grpc_clients.diet_client import DietClient
from nexus_ai.grpc_clients.doctor_client import DoctorClient

__all__ = ["BrainClient", "IntegrationClient", "ClinicalClient", "VisionClient", "DietClient", "DoctorClient"]
