import json
import logging
import copy
from typing import Any, Optional
from google.adk.agents import LlmAgent
from google.genai import types
from google.genai.client import Client

from nexus_ai.config import get_settings
from nexus_ai.services.brain import BrainService
from nexus_ai.services.recipe_store import RecipeStore
from nexus_ai.adk.recipe_agent import recipe_agent

logger = logging.getLogger(__name__)


# ── Diet Medical Aggregator (Original class) ─────────────────────────

DIET_AGGREGATOR_INSTRUCTION = """
    You are the Medical Diet Aggregator Agent. Your job is to create a complete medical-dietary profile 
    for a patient based on their conditions, pharmacy summaries, and active medications.

    If the provided data includes explicit dietary restrictions, expand on them with culinary context.
    If the data lacks specific food recommendations for the listed medicines, use your search tools 
    (GoogleSearchTool, url_context) to look up contraindicated foods and recommended nutrients online 
    for those specific drugs or conditions (e.g. Grapefruit interactions with Statins).

    Output a STRICT JSON object in this format:
    {
      "recommendations": ["list", "of", "recommended", "foods/nutrients"],
      "restrictions": ["list", "of", "foods", "to", "avoid"],
      "reasoning": "Detailed explanation of why these were chosen based on the medicines and conditions."
    }

    No other text or markdown block. ONLY valid JSON.
"""

class DietMedicalAggregator:
    def __init__(self):
        from nexus_ai.adapters.brain import build_brain_gateway
        self.brain = build_brain_gateway()
        self.settings = get_settings()

    def _get_agent(self) -> LlmAgent:
        tools_list = []
        try:
            from google.adk.tools.google_search_tool import GoogleSearchTool
            from google.adk.tools import url_context
            tools_list.extend([GoogleSearchTool(), url_context])
        except ImportError as e:
            logger.warning(f"ADK native tools not found: {e}. Aggregator will run without search capabilities.")
            
        return LlmAgent(
            name="diet_medical_aggregator",
            model=self.settings.gemini_pro_model_id, # Using Pro since it needs to think & search
            description="Aggregates and researches patient medical data to form dietary constraints.",
            instruction=DIET_AGGREGATOR_INSTRUCTION,
            tools=tools_list,
            sub_agents=[]
        )

    def get_patient_diet_profile(
        self, 
        patient_id: int, 
        medication_name: Optional[str] = None,
        pharmacy_summary: Optional[str] = None
    ) -> dict[str, Any]:
        """Fetches patient profile and uses LLM to generate the enriched dietary profile."""
        profile = self.brain.get_patient_profile(patient_id)
        conditions = self.brain.get_relevant_conditions(patient_id)
        
        history_summary = f"Patient Profile: {profile.summary if profile else 'Unknown'}\n"
        history_summary += "Conditions:\n" + "\n".join([f"- {c.name}" for c in conditions]) + "\n"
        
        if medication_name:
            history_summary += f"Active Medication Focus: {medication_name}\n"
        if pharmacy_summary:
            history_summary += f"Pharmacy Notes: {pharmacy_summary}\n"

        agent = self._get_agent()
        
        client = Client(api_key=self.settings.gemini_api_key)
        
        prompt = f"Analyze this medical history and output the enriched dietary constraints:\n{history_summary}"
        
        try:
            config = types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
            )
            response = client.models.generate_content(
                model=agent.model,
                contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
                config=config
            )
            
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Medical Aggregator failed: {e}")
            return {
                "recommendations": [],
                "restrictions": [],
                "reasoning": f"Error fetching dietary constraints: {e}"
            }


# ── DietAgent (Restored class matching test & service interface) ──────

class DietAgent:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.recipe_store = RecipeStore()
        self._recipe_agent = recipe_agent

    def build_diet_support_plan(self, conditions: list[Any], medication_name: str | None = None, pharmacy_summary: str | None = None) -> dict:
        meal_rules = []
        cond_names = {c.name.lower() for c in conditions if hasattr(c, "name") and c.name}
        
        # Condition rules
        if "ibs" in cond_names:
            meal_rules.append("Prefer low-FODMAP ingredients. Limit garlic, onions, and wheat.")
        if "epilepsy" in cond_names:
            meal_rules.append("Focus on a high-fat, low-carbohydrate diet to support seizure control.")
        if "atopic eczema" in cond_names or "eczema" in cond_names:
            meal_rules.append("Avoid common triggers such as dairy, nuts, and highly processed foods.")
            
        # Medication rules
        if medication_name:
            med_lower = medication_name.lower()
            if "statin" in med_lower or "atorvastatin" in med_lower or "simvastatin" in med_lower:
                meal_rules.append("Do NOT consume grapefruit or grapefruit juice, as it increases statin levels.")
            if "metformin" in med_lower:
                meal_rules.append("Monitor vitamin B12 levels. Limit alcohol consumption.")
            if "levetiracetam" in med_lower:
                meal_rules.append("Limit caffeine intake. Take medication consistently with or without food.")

        # Default rules if empty
        if not meal_rules:
            meal_rules.append("Focus on whole grains, fresh vegetables, and lean proteins.")
            
        plan_summary = f"Dietary guidance tailored to conditions: {', '.join(c.name for c in conditions if hasattr(c, 'name'))}."
        
        return {
            "medication_name": medication_name,
            "meal_rules": meal_rules,
            "pharmacy_summary": pharmacy_summary,
            "plan_summary": plan_summary,
        }

    def list_curated_recipes(self, meal_type: str | None = None, medication_name: str | None = None, conditions: list[Any] | None = None) -> list[dict]:
        recipes = self.recipe_store.list_recipes(meal_type)
        safe_recipes = []
        for recipe in recipes:
            if not self._recipe_contains_blocked(recipe, medication_name, conditions or []):
                safe_recipes.append(self.apply_safety_rules(recipe, medication_name, conditions or []))
        return safe_recipes

    def get_recipe(self, recipe_id: str) -> dict | None:
        return self.recipe_store.get_recipe(recipe_id)

    def scale_recipe(self, recipe_id: str, servings: int, conditions: list[Any], medication_name: str | None = None) -> dict | None:
        recipe = self.recipe_store.get_recipe(recipe_id)
        if not recipe:
            return None
        scaled = self.recipe_store.scale_recipe(recipe, servings)
        return self.apply_safety_rules(scaled, medication_name, conditions)

    def _recipe_contains_blocked(self, recipe: dict, medication_name: str | None, conditions: list[Any]) -> bool:
        ingredients = {str(i.get("name", "")).lower().strip() for i in recipe.get("ingredients", [])}
        
        # Block rules
        if medication_name:
            med_lower = medication_name.lower()
            if "statin" in med_lower or "atorvastatin" in med_lower or "simvastatin" in med_lower:
                if "grapefruit" in ingredients or any("grapefruit" in ing for ing in ingredients):
                    return True
        return False

    def apply_safety_rules(self, recipe: dict, medication_name: str | None, conditions: list[Any]) -> dict:
        adjusted = copy.deepcopy(recipe)
        adjusted.setdefault("safety_notes", [])
        adjusted.setdefault("medication_fit", [])
        adjusted.setdefault("condition_fit", [])
        adjusted.setdefault("avoid_flags", [])
        
        cond_names = {c.name.lower() for c in conditions if hasattr(c, "name") and c.name}
        ingredients = {str(i.get("name", "")).lower().strip() for i in adjusted.get("ingredients", [])}
        
        if "ibs" in cond_names:
            adjusted["condition_fit"].append("IBS-safe")
            if any(x in ingredients for x in ["garlic", "onion", "wheat"]):
                adjusted["safety_notes"].append({"severity": "caution", "message": "Contains garlic/onion which may trigger IBS symptoms.", "related_to": "IBS"})
                adjusted["avoid_flags"].append("high-fodmap")
        
        if "epilepsy" in cond_names:
            adjusted["condition_fit"].append("Epilepsy-safe")
            if any(x in ingredients for x in ["sugar", "syrup", "honey"]):
                adjusted["safety_notes"].append({"severity": "caution", "message": "High sugar contents should be monitored for epilepsy keto-management.", "related_to": "Epilepsy"})
                
        if medication_name:
            med_lower = medication_name.lower()
            if "statin" in med_lower or "atorvastatin" in med_lower or "simvastatin" in med_lower:
                adjusted["medication_fit"].append("Statin-compatible")
                if "grapefruit" in ingredients:
                    adjusted["avoid_flags"].append("grapefruit")
            if "metformin" in med_lower:
                adjusted["medication_fit"].append("Metformin-compatible")
                
        return adjusted

    def generate_recipes(self, conditions: list[Any], medication_name: str | None = None, preferences: dict | None = None) -> dict:
        prefs = preferences or {}
        meal_type = prefs.get("meal_type", "any")
        servings = prefs.get("servings", 4)
        
        # Attempt ADK generation
        recipes = []
        fallback_used = True
        safety_summary = "Generating diet recipes tailored to your conditions."
        
        if self._recipe_agent:
            try:
                recipes = self._generate_with_adk(conditions, medication_name, prefs)
                if recipes:
                    fallback_used = False
                    safety_summary = "Generated safe recipes based on ingredients and medical profile."
            except Exception as e:
                logger.error(f"ADK generation failed, falling back to curated: {e}")
                
        if fallback_used:
            curated = self.list_curated_recipes(meal_type, medication_name, conditions)
            scaled = []
            for r in curated[:2]:
                scaled.append(self.scale_recipe(r["recipe_id"], servings, conditions, medication_name))
            recipes = scaled
            safety_summary = "Curated recipes provided as a safe fallback."
            
        return {
            "patient_id": prefs.get("patient_id", 1),
            "conditions": [c.to_dict() if hasattr(c, "to_dict") else c.__dict__ for c in conditions],
            "medication_name": medication_name,
            "recipes": recipes,
            "fallback_used": fallback_used,
            "safety_summary": safety_summary,
        }

    def _generate_with_adk(self, conditions: list[Any], medication_name: str | None, preferences: dict) -> list[dict]:
        prompt = self._build_generation_prompt(conditions, medication_name, preferences)
        raw_res = self._run_adk_generation(prompt)
        return self._parse_generated_response(raw_res)

    def _run_adk_generation(self, prompt: str) -> str:
        if not self.settings.google_api_key:
            return ""
        try:
            client = Client(api_key=self.settings.google_api_key)
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
            )
            response = client.models.generate_content(
                model=self._recipe_agent.model,
                contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
                config=config
            )
            return response.text or ""
        except Exception as e:
            logger.error(f"ADK Recipe execution failed: {e}")
            return ""

    def _build_generation_prompt(self, conditions: list[Any], medication_name: str | None, preferences: dict) -> str:
        return f"Generate safe recipe for conditions: {conditions}, medication: {medication_name}, preferences: {preferences}"

    def _parse_generated_response(self, raw_text: str) -> list[dict]:
        if not raw_text:
            return []
        try:
            data = json.loads(raw_text)
            recipes = data.get("recipes", [])
            return [self._normalize_generated_recipe(r) for r in recipes]
        except Exception:
            return []

    def _normalize_generated_recipe(self, recipe: dict) -> dict:
        return recipe
