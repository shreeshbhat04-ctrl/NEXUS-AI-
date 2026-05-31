from __future__ import annotations

import copy
import json
from pathlib import Path


COUNTABLE_UNITS = {
    "piece",
    "pieces",
    "clove",
    "cloves",
    "egg",
    "eggs",
    "leaf",
    "leaves",
    "packet",
    "packets",
    "medium",
    "large",
    "small",
    "stalk",
    "stalks",
}


class RecipeStore:
    """JSON-backed recipe storage for curated recipe experiences."""

    def __init__(self, data_file: str | None = None) -> None:
        default_path = Path(__file__).resolve().parents[1] / "data" / "diet_recipes.json"
        self.data_file = Path(data_file) if data_file else default_path
        self._recipes = self._load_recipes()

    def _load_recipes(self) -> list[dict]:
        if not self.data_file.exists():
            return []

        try:
            payload = json.loads(self.data_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

        recipes = payload.get("recipes")
        if not isinstance(recipes, list):
            return []
        return [item for item in recipes if isinstance(item, dict)]

    def list_recipes(self, meal_type: str | None = None) -> list[dict]:
        recipes = [copy.deepcopy(item) for item in self._recipes]
        if not meal_type or meal_type == "any":
            return recipes
        normalized = meal_type.strip().lower()
        return [item for item in recipes if str(item.get("meal_type", "")).lower() == normalized]

    def get_recipe(self, recipe_id: str) -> dict | None:
        for recipe in self._recipes:
            if recipe.get("recipe_id") == recipe_id:
                return copy.deepcopy(recipe)
        return None

    def scale_recipe(self, recipe: dict, target_servings: int) -> dict:
        scaled = copy.deepcopy(recipe)
        default_servings = int(scaled.get("default_servings") or 1)
        if default_servings <= 0:
            default_servings = 1

        factor = target_servings / default_servings
        ingredients = scaled.get("ingredients", [])
        for ingredient in ingredients:
            quantity = float(ingredient.get("quantity", 0))
            unit = str(ingredient.get("unit", "")).lower().strip()
            scaled_quantity = quantity * factor
            if unit in COUNTABLE_UNITS:
                ingredient["quantity"] = float(max(1, round(scaled_quantity)))
            else:
                ingredient["quantity"] = round(scaled_quantity, 1)

        scaled["default_servings"] = target_servings
        return scaled
