from pathlib import Path

from nexus_ai.config import get_settings
from nexus_ai.services.model_routing import ModelRoutingService


class DocumentAgent:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model_routing = ModelRoutingService()

    def build_document_intake_plan(
        self,
        patient_id: int,
        file_path: str,
        raw_text_hint: str | None = None,
        prescription_id: int | None = None,
    ) -> dict:
        path = Path(file_path)
        route = self.model_routing.route_medical_input(query_text=raw_text_hint, file_path=file_path)
        return {
            "patient_id": patient_id,
            "prescription_id": prescription_id,
            "file_name": path.name,
            "file_path": str(path),
            "ocr_model": route["primary_model"],
            "reasoning_model": route.get("secondary_model") or self.settings.gemini_fast_model_id,
            "support_model": route.get("support_model"),
            "storage_target": "google_drive",
            "ocr_strategy": "vision_first_then_structured_medical_reasoning" if route["route_type"] == "medical_image" else "text_first_then_structured_medical_reasoning",
            "raw_text_hint": raw_text_hint,
            "route_type": route["route_type"],
            "route_reason": route["reason"],
            "execution_plan": route["execution_plan"],
        }
