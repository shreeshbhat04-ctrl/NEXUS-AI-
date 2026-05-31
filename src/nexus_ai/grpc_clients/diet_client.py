"""gRPC client for the Diet service."""
import json
import logging
from typing import Optional

import grpc

from nexus_ai.generated import diet_pb2, diet_pb2_grpc

logger = logging.getLogger(__name__)


class DietClient:
    """Client wrapper for DietService gRPC calls."""

    def __init__(self, host: str = "localhost", port: int = 50055) -> None:
        self.target = f"{host}:{port}"
        self.channel = grpc.insecure_channel(self.target)
        self.stub = diet_pb2_grpc.DietServiceStub(self.channel)
        logger.info("DietClient connected to %s", self.target)

    def _convert_conditions(self, conditions):
        return [
            diet_pb2.DietCondition(
                name=c.get("name", ""),
                condition_type=c.get("condition_type", ""),
            )
            for c in (conditions or [])
        ]

    def build_diet_plan(
        self,
        conditions: list[dict],
        medication_name: str = "",
        pharmacy_summary: str = "",
    ) -> dict:
        try:
            response = self.stub.BuildDietPlan(diet_pb2.DietPlanRequest(
                conditions=self._convert_conditions(conditions),
                medication_name=medication_name,
                pharmacy_summary=pharmacy_summary,
            ))
            return {
                "success": response.success,
                "plan": json.loads(response.plan_json) if response.plan_json else {},
                "message": response.message,
            }
        except grpc.RpcError as e:
            logger.error("DietClient.build_diet_plan failed: %s", e.details())
            raise

    def list_recipes(
        self,
        meal_type: str = "",
        medication_name: str = "",
        conditions: list[dict] = None,
    ) -> list[dict]:
        try:
            response = self.stub.ListRecipes(diet_pb2.RecipeListRequest(
                meal_type=meal_type,
                medication_name=medication_name,
                conditions=self._convert_conditions(conditions),
            ))
            return [
                {
                    "recipe_id": r.recipe_id,
                    "title": r.title,
                    "summary": r.summary,
                }
                for r in response.recipes
            ]
        except grpc.RpcError as e:
            logger.error("DietClient.list_recipes failed: %s", e.details())
            raise

    def generate_recipes(
        self,
        conditions: list[dict],
        medication_name: str = "",
        preferences: dict = None,
    ) -> dict:
        try:
            response = self.stub.GenerateRecipes(diet_pb2.RecipeGenerateRequest(
                conditions=self._convert_conditions(conditions),
                medication_name=medication_name,
                preferences_json=json.dumps(preferences or {}),
            ))
            return {
                "success": response.success,
                "recipes": json.loads(response.recipes_json) if response.recipes_json else [],
                "message": response.message,
            }
        except grpc.RpcError as e:
            logger.error("DietClient.generate_recipes failed: %s", e.details())
            raise

    def scale_recipe(
        self,
        recipe_id: str,
        servings: int,
        conditions: list[dict],
        medication_name: str = "",
    ) -> dict:
        try:
            response = self.stub.ScaleRecipe(diet_pb2.RecipeScaleRequest(
                recipe_id=recipe_id,
                servings=servings,
                conditions=self._convert_conditions(conditions),
                medication_name=medication_name,
            ))
            return {
                "success": response.success,
                "recipe": json.loads(response.recipe_json) if response.recipe_json else {},
                "message": response.message,
            }
        except grpc.RpcError as e:
            logger.error("DietClient.scale_recipe failed: %s", e.details())
            raise

    def get_recipe(self, recipe_id: str) -> Optional[dict]:
        try:
            response = self.stub.GetRecipe(diet_pb2.RecipeGetRequest(
                recipe_id=recipe_id,
            ))
            if not response.found:
                return None
            return json.loads(response.recipe_json) if response.recipe_json else {}
        except grpc.RpcError as e:
            logger.error("DietClient.get_recipe failed: %s", e.details())
            raise

    def close(self) -> None:
        self.channel.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
