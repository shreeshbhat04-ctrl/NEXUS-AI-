"""Diet gRPC server — Diet plans, recipes, ADK generation."""
import json
import logging
import os
from concurrent import futures
from types import SimpleNamespace

import grpc

from nexus_ai.config import get_settings
from nexus_ai.agents.diet import DietAgent
from nexus_ai.services.recipe_store import RecipeStore
from nexus_ai.generated import diet_pb2, diet_pb2_grpc

logger = logging.getLogger(__name__)


class DietServiceServicer(diet_pb2_grpc.DietServiceServicer):
    """gRPC servicer wrapping Diet services."""

    def __init__(self) -> None:
        self.diet_agent = DietAgent()
        self.recipe_store = RecipeStore()

    def _convert_conditions(self, conditions_proto):
        return [
            SimpleNamespace(name=c.name, condition_type=c.condition_type)
            for c in conditions_proto
        ]

    def BuildDietPlan(self, request, context):
        try:
            conditions = self._convert_conditions(request.conditions)
            result = self.diet_agent.build_diet_support_plan(
                conditions=conditions,
                medication_name=request.medication_name or None,
                pharmacy_summary=request.pharmacy_summary or None,
            )
            return diet_pb2.DietPlanResponse(
                success=True,
                plan_json=json.dumps(result),
                message="Diet plan built.",
            )
        except Exception as e:
            logger.exception("BuildDietPlan failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def ListRecipes(self, request, context):
        try:
            conditions = self._convert_conditions(request.conditions)
            recipes = self.diet_agent.list_curated_recipes(
                meal_type=request.meal_type or None,
                medication_name=request.medication_name or None,
                conditions=conditions if conditions else None,
            )
            results = [
                diet_pb2.RecipeResult(
                    recipe_id=r.get("recipe_id", ""),
                    title=r.get("title", ""),
                    summary=r.get("summary", ""),
                )
                for r in recipes
            ]
            return diet_pb2.RecipeListResponse(
                success=True,
                recipes=results,
                message="Recipes listed.",
            )
        except Exception as e:
            logger.exception("ListRecipes failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def GenerateRecipes(self, request, context):
        try:
            conditions = self._convert_conditions(request.conditions)
            preferences = json.loads(request.preferences_json) if request.preferences_json else {}
            
            result = self.diet_agent.generate_recipes(
                conditions=conditions,
                medication_name=request.medication_name or None,
                preferences=preferences,
            )
            return diet_pb2.RecipeGenerateResponse(
                success=result.get("success", True),
                recipes_json=json.dumps(result.get("recipes", [])),
                message=result.get("message", "Recipes generated."),
            )
        except Exception as e:
            logger.exception("GenerateRecipes failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def ScaleRecipe(self, request, context):
        try:
            conditions = self._convert_conditions(request.conditions)
            scaled_recipe = self.diet_agent.scale_recipe(
                recipe_id=request.recipe_id,
                servings=request.servings,
                conditions=conditions,
                medication_name=request.medication_name or None,
            )
            return diet_pb2.RecipeScaleResponse(
                success=scaled_recipe is not None,
                recipe_json=json.dumps(scaled_recipe) if scaled_recipe else "{}",
                message="Recipe scaled." if scaled_recipe else "Recipe not found or scaling failed.",
            )
        except Exception as e:
            logger.exception("ScaleRecipe failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
            
    def GetRecipe(self, request, context):
        try:
            recipe = self.recipe_store.get_recipe(request.recipe_id)
            return diet_pb2.RecipeGetResponse(
                found=recipe is not None,
                recipe_json=json.dumps(recipe) if recipe else "{}",
            )
        except Exception as e:
            logger.exception("GetRecipe failed")
            context.abort(grpc.StatusCode.INTERNAL, str(e))


def serve() -> None:
    settings = get_settings()
    port = os.getenv("GRPC_PORT", str(settings.grpc_diet_port))
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    diet_pb2_grpc.add_DietServiceServicer_to_server(DietServiceServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"Diet gRPC service running on port {port}")
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()
