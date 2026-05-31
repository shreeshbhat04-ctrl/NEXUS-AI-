import json
import logging
from typing import Any, Optional
from google.adk.agents import LlmAgent
from google.genai import types
from nexus_ai.config import get_settings

logger = logging.getLogger(__name__)

VISION_EXTRACTOR_INSTRUCTION = """
    You are the Vision Extractor Agent. Your job is to identify every ingredient present
    in the source material provided by the user (which could be an image, a URL, or text).
    
    If the user provides a URL, use the url_context tool to retrieve its content, or GoogleSearchTool 
    if you need to look up a generic recipe or ingredient list online.
    
    Output a STRICT JSON object in this format:
    {
      "detected_ingredients": ["list", "of", "ingredients", "found"]
    }
    
    No other text or markdown block. ONLY valid JSON.
"""

def get_vision_extractor() -> LlmAgent:
    settings = get_settings()
    
    # Attempt to import ADK native tools; if unavailable, fallback to empty list
    tools_list = []
    try:
        from google.adk.tools.google_search_tool import GoogleSearchTool
        from google.adk.tools import url_context
        tools_list.extend([GoogleSearchTool(), url_context])
    except ImportError as e:
        logger.warning(f"ADK native tools not found: {e}. Vision extractor will run without them.")
        
    return LlmAgent(
        name="diet_vision_extractor",
        model=settings.gemini_fast_model_id,
        description="Multimodal agent that identifies ingredients from images or URLs using native tools.",
        instruction=VISION_EXTRACTOR_INSTRUCTION,
        tools=tools_list,
        sub_agents=[],
    )

def extract_ingredients(url: Optional[str] = None, image_bytes: Optional[bytes] = None, mime_type: str = "image/jpeg") -> dict[str, Any]:
    """Runs the Vision Extractor agent given a URL or image bytes."""
    agent = get_vision_extractor()
    
    from google.genai.client import Client
    client = Client(api_key=get_settings().gemini_api_key)
    
    parts = []
    if url:
        parts.append(types.Part.from_text(text=f"Extract ingredients from this URL: {url}"))
    if image_bytes:
        parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))
        parts.append(types.Part.from_text(text="Extract ingredients from this image."))
        
    if not parts:
        return {"detected_ingredients": []}
        
    try:
        config = types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
            system_instruction=agent.instruction,
        )
        
        # Note: If ADK has a native runner for LlmAgent (e.g. runner.run(agent)), 
        # we would use it here to natively handle the tool loop. 
        # For now, we pass the prompt directly via GenAI client.
        response = client.models.generate_content(
            model=agent.model,
            contents=[types.Content(role="user", parts=parts)],
            config=config
        )
        
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Vision Extractor failed: {e}")
        return {"detected_ingredients": []}

