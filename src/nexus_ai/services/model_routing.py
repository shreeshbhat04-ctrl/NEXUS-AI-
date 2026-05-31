from nexus_ai.config import get_settings


class ModelRoutingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._medical_keywords = {
            "pain",
            "fever",
            "cough",
            "disease",
            "rash",
            "swelling",
            "vomiting",
            "diarrhea",
            "infection",
            "diabetes",
            "ibs",
            "thyroid",
            "bp",
            "pressure",
            "sugar",
            "tablet",
            "medicine",
            "medication",
            "dose",
            "dosage",
            "prescription",
            "symptom",
            "dizzy",
            "headache",
            "nausea",
            "ulcer",
            "skin",
            "lesion",
            "mole",
            "eczema",
            "psoriasis",
        }
        self._supportive_keywords = {
            "sad",
            "worried",
            "anxious",
            "stressed",
            "lonely",
            "scared",
            "down",
            "tired",
            "overwhelmed",
            "check in",
            "how are you",
            "how was your day",
        }
        self._image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".heic"}

    def get_model_manifest(self) -> dict[str, dict[str, str]]:
        return {
            "communication_agent": {
                "primary_model": self.settings.gemini_fast_model_id,
                "reason": "Fast conversational check-ins and patient-facing summaries.",
            },
            "hitl_agent": {
                "primary_model": self.settings.gemini_fast_model_id,
                "reason": "Medical-detail report drafting and clinical summarization.",
            },
            "routine_agent": {
                "primary_model": self.settings.gemini_fast_model_id,
                "reason": "Lightweight planning over reminders and routines.",
            },
            "diet_pharmacy_agent": {
                "primary_model": self.settings.gemini_fast_model_id,
                "reason": "Medication-aware diet logic and safe alternative reasoning.",
            },
            "document_agent": {
                "primary_model": self.settings.adk_model,
                "reason": "Document OCR and visual intake before downstream storage/reasoning.",
            },
        }

    def route_general_conversation(self, message: str) -> dict[str, object]:
        normalized = message.lower().strip()
        supportive = any(keyword in normalized for keyword in self._supportive_keywords)
        medical = self._contains_medical_signal(normalized)
        if medical:
            return {
                "route_type": "medical_text",
                "primary_model": self.settings.gemini_fast_model_id,
                "support_model": None,
                "reason": "Medical symptoms, medicine, or disease terms were detected in the conversation.",
                "execution_plan": [
                    "Use Gemini 3.1 Flash for medical interpretation, safety-aware response drafting, and patient-friendly tone.",
                ],
            }

        tone = "supportive" if supportive else "general"
        return {
            "route_type": f"{tone}_conversation",
            "primary_model": self.settings.gemini_fast_model_id,
            "support_model": None,
            "reason": "General conversation and reassuring language should stay on Gemini 3.1 Flash.",
            "execution_plan": [
                "Use Gemini 3.1 Flash for conversational support, empathy, and daily check-ins.",
            ],
        }

    def route_medical_input(self, query_text: str | None = None, file_path: str | None = None) -> dict[str, object]:
        normalized = (query_text or "").lower().strip()
        is_image = self._is_image_file(file_path)
        has_medical_text = self._contains_medical_signal(normalized)

        if is_image:
            return {
                "route_type": "medical_image",
                "primary_model": self.settings.adk_model,
                "secondary_model": self.settings.gemini_fast_model_id,
                "support_model": None,
                "reason": "Uploaded image should go through ADK model first, then Gemini 3.1 Flash for medical reasoning.",
                "execution_plan": [
                    "Use ADK model for visual understanding and OCR-style intake from the uploaded image.",
                    "Pass extracted findings to Gemini 3.1 Flash for disease-oriented medical reasoning and patient-friendly wording.",
                ],
            }

        if has_medical_text:
            return {
                "route_type": "medical_text",
                "primary_model": self.settings.gemini_fast_model_id,
                "secondary_model": None,
                "support_model": None,
                "reason": "Medical query text should be handled by Gemini 3.1 Flash.",
                "execution_plan": [
                    "Use Gemini 3.1 Flash for clinical-style interpretation of the medical query and patient-friendly restatement.",
                ],
            }

        return {
            "route_type": "general_text",
            "primary_model": self.settings.gemini_fast_model_id,
            "secondary_model": None,
            "support_model": None,
            "reason": "No clear medical signal was detected, so Gemini 3.1 Flash should handle the interaction.",
            "execution_plan": [
                "Use Gemini 3.1 Flash for the response.",
            ],
        }

    def _contains_medical_signal(self, normalized_text: str) -> bool:
        return any(keyword in normalized_text for keyword in self._medical_keywords)

    def _is_image_file(self, file_path: str | None) -> bool:
        if not file_path:
            return False
        lowered = file_path.lower().strip()
        return any(lowered.endswith(extension) for extension in self._image_extensions)
