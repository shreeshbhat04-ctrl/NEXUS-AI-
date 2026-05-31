from types import SimpleNamespace

from nexus_ai.agents.communications import CommunicationsAgent
from nexus_ai.services.brain import BrainPatientProfile


def test_medical_conversation_uses_medgemma_proxy_and_keeps_medgemma_label(monkeypatch) -> None:
    agent = CommunicationsAgent()
    agent.medical_generation.medgemma_generate = lambda **kwargs: {  # type: ignore[method-assign]
        "provider": "gemini-proxy",
        "model": "google/medgemma-1.5-4b-it",
        "result": {"text": "Clinical Impression\nThis needs a doctor visit soon."},
    }

    result = agent.build_conversation_plan(
        message="I have dizziness and sharp stomach pain.",
        profile=BrainPatientProfile(id=1, full_name="Asha Rao", preferred_language="en", summary="IBS history"),
    )

    assert result["primary_model"] == agent.model_routing.settings.medgemma_model_id
    assert result["route_type"] == "medical_text"
    assert "doctor visit" in result["message"]


def test_general_conversation_falls_back_across_gemini_models(monkeypatch) -> None:
    attempts: list[str] = []

    class DummyModels:
        def generate_content(self, *, model, contents, config):
            _ = contents, config
            attempts.append(model)
            if model == "gemini-2.5-flash-lite":
                raise RuntimeError("404 Not Found")
            return SimpleNamespace(text="You're doing okay — let's take this one step at a time.")

    class DummyClient:
        def __init__(self, api_key: str) -> None:
            _ = api_key
            self.models = DummyModels()

    monkeypatch.setattr("google.genai.Client", DummyClient)

    agent = CommunicationsAgent()
    settings = agent.model_routing.settings
    settings.gemini_fast_model_id = "gemini-2.5-flash-lite"
    settings.gemini_fast_fallback_model_ids = "gemini-2.5-flash,gemini-2.0-flash"
    result = agent.build_conversation_plan(message="I've been stressed lately.")

    assert attempts[:2] == ["gemini-2.5-flash-lite", "gemini-2.5-flash"]
    assert "one step at a time" in result["message"]
