import json
import logging
from typing import Any
from google.adk.agents import LlmAgent
from google.genai import types
from nexus_ai.config import get_settings

logger = logging.getLogger(__name__)

CULINARY_GENERATOR_INSTRUCTION = """
    You are the Culinary Generator Agent. You generate personalized recipes.
    
    Inputs provided:
    1. A list of strictly SAFE available ingredients the user has selected.
    2. A target Cuisine Style (e.g., South Indian, Mediterranean).
    3. A maximum cooking Duration (e.g., Under 30 minutes).
    4. General dietary rules to follow.
    
    Output a STRICT JSON object representing a single recipe in this format:
    {
      "recipe": {
        "title": "Recipe Name",
        "description": "Short description",
        "cook_time": "20 minutes",
        "meal_type": "dinner",
        "cuisine": "South Indian",
        "ingredients": [
          {"name": "ingredient", "quantity": 1, "unit": "cup"}
        ],
        "instructions": ["Step 1", "Step 2"],
        "why_it_fits": "Brief explanation of why it fits the medical constraints and cuisine."
      }
    }
    
    No other text or markdown block. ONLY valid JSON.
"""

def get_culinary_generator() -> LlmAgent:
    settings = get_settings()
    return LlmAgent(
        name="diet_culinary_generator",
        model=settings.gemini_fast_model_id,
        description="Generates personalized recipes based on strict safe ingredients and user preferences.",
        instruction=CULINARY_GENERATOR_INSTRUCTION,
        tools=[],
        sub_agents=[]
    )

def generate_recipe(
    safe_ingredients: list[str], 
    cuisine_style: str, 
    duration: str, 
    dietary_rules: list[str]
) -> dict[str, Any]:
    """Runs the Culinary Generator agent to create a recipe."""
    agent = get_culinary_generator()
    
    prompt = f"""
    Selected Safe Ingredients: {', '.join(safe_ingredients)}
    Desired Cuisine: {cuisine_style}
    Max Duration: {duration}
    Dietary Rules to Follow: {', '.join(dietary_rules)}
    
    Generate the recipe now.
    """
    
    from google.genai.client import Client
    client = Client(api_key=get_settings().gemini_api_key)
    
    try:
        config = types.GenerateContentConfig(
            temperature=0.3,
            response_mime_type="application/json",
            system_instruction=agent.instruction,
        )
        response = client.models.generate_content(
            model=agent.model,
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
            config=config
        )
        
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Culinary Generator failed: {e}")
        return {"recipe": None}
