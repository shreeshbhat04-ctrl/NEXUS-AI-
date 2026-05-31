from typing import Any
import json
import logging
from google.adk.agents import LlmAgent
from google.genai import types
from nexus_ai.config import get_settings
from nexus_ai.services.brain import BrainService

logger = logging.getLogger(__name__)

MEDICAL_ANALYST_INSTRUCTION = """
    You are a strictly clinical dietitian. You analyze the patient's medical history 
    (allergies, chronic conditions, current medications) and translate it into dietary constraints.
    
    Output a STRICT JSON object in this format:
    {
      "ingredients_to_avoid": ["list", "of", "ingredients", "to", "avoid"],
      "general_dietary_rules": ["rule 1", "rule 2"]
    }
    
    No other text or markdown block. ONLY valid JSON.
    Use generic ingredient names. Include known contraindications 
    (e.g. grapefruit for statins).
"""

def get_medical_analyst() -> LlmAgent:
    settings = get_settings()
    return LlmAgent(
        name="diet_medical_analyst",
        model=settings.gemini_fast_model_id,
        description="Clinical dietitian agent that extracts dietary constraints from medical history.",
        instruction=MEDICAL_ANALYST_INSTRUCTION,
        tools=[],
        sub_agents=[],
    )

def analyze_patient_dietary_needs(patient_id: int) -> dict[str, Any]:
    """Runs the Medical Analyst agent given a patient ID."""
    from nexus_ai.adapters.brain import build_brain_gateway
    brain = build_brain_gateway()
    profile = brain.get_patient_profile(patient_id)
    conditions = brain.get_relevant_conditions(patient_id)
    
    history_summary = f"Patient Profile: {profile.summary if profile else 'Unknown'}\n"
    history_summary += "Conditions:\n" + "\n".join([f"- {c.name}" for c in conditions])
    
    agent = get_medical_analyst()
    
    from google.genai.client import Client
    client = Client(api_key=get_settings().gemini_api_key)
    
    try:
        config = types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
            system_instruction=agent.instruction,
        )
        response = client.models.generate_content(
            model=agent.model,
            contents=[
                types.Content(role="user", parts=[
                    types.Part.from_text(text=f"Analyze this medical history and output dietary constraints:\n{history_summary}")
                ])
            ],
            config=config
        )
        
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Medical Analyst failed: {e}")
        return {
            "ingredients_to_avoid": [],
            "general_dietary_rules": ["Error fetching dietary constraints."]
        }
