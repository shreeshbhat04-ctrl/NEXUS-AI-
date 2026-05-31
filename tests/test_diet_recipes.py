from nexus_ai.agents.diet import DietAgent
from nexus_ai.services.brain import BrainCondition
from nexus_ai.services.recipe_store import RecipeStore


def _condition(name: str) -> BrainCondition:
    return BrainCondition(
        id=1,
        patient_id=2,
        name=name,
        condition_type="chronic",
        last_updated=None,
        notes=None,
    )


def test_recipe_store_loads_seed_data() -> None:
    store = RecipeStore()
    recipes = store.list_recipes()
    assert recipes
    assert any(recipe["recipe_id"] == "gentle_upma_bowl" for recipe in recipes)


def test_recipe_store_scales_measurable_and_countable_units() -> None:
    store = RecipeStore()
    recipe = {
        "recipe_id": "scale_test",
        "default_servings": 2,
        "ingredients": [
            {"name": "Salmon", "quantity": 1.5, "unit": "lb"},
            {"name": "Egg", "quantity": 1, "unit": "piece"},
        ],
    }

    scaled = store.scale_recipe(recipe, target_servings=4)
    assert scaled["ingredients"][0]["quantity"] == 3.0
    assert scaled["ingredients"][1]["quantity"] == 2.0


def test_generate_recipes_falls_back_to_curated_when_adk_unavailable() -> None:
    agent = DietAgent()
    agent._recipe_agent = None

    result = agent.generate_recipes(
        conditions=[_condition("IBS")],
        medication_name="Metformin",
        preferences={
            "patient_id": 2,
            "meal_type": "breakfast",
            "available_ingredients": ["semolina", "carrot"],
            "avoid_ingredients": [],
            "servings": 2,
            "count": 2,
        },
    )

    assert result["fallback_used"] is True
    assert result["recipes"]
    assert len(result["recipes"]) <= 2


def test_generate_recipes_filters_blocked_statin_ingredient() -> None:
    agent = DietAgent()
    recipe = {
        "recipe_id": "bad_recipe",
        "source": "generated",
        "title": "Citrus Bowl",
        "description": "Contains grapefruit.",
        "default_servings": 2,
        "cook_time": "10 minutes",
        "meal_type": "breakfast",
        "ingredients": [{"name": "Grapefruit", "quantity": 1, "unit": "piece"}],
        "instructions": ["Serve."],
        "safety_notes": [],
        "condition_fit": [],
        "medication_fit": [],
        "avoid_flags": [],
        "why_it_fits": "test",
        "dietary_pattern": None,
        "cuisine_preference": None,
        "image_url": None,
        "image_status": "unavailable",
    }

    assert agent._recipe_contains_blocked(recipe, "statin", []) is True
