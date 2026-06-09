from __future__ import annotations

import logging
from typing import Any

import phoenix as px
from openinference.instrumentation.google_adk import GoogleADKInstrumentor

from nexus_ai.config import get_settings

logger = logging.getLogger(__name__)

_TRACING_STATE: dict[str, Any] = {
    "enabled": False,
}

def init_tracing() -> None:
    settings = get_settings()
    
    if not settings.arize_api_key:
        logger.warning("No ARIZE_API_KEY found in environment. Tracing disabled.")
        return

    try:
        # Initialize Arize Phoenix with project name
        px.launch_app()
        
        # We assume the user has set OTEL_EXPORTER_OTLP_HEADERS in .env for authentication
        # as per standard OpenInference documentation for Phoenix Cloud.
        # Auto-instrument Google ADK Agents
        GoogleADKInstrumentor().instrument()
        
        _TRACING_STATE["enabled"] = True
        logger.info(f"Arize Phoenix tracing enabled for project: {settings.arize_phoenix_project}")
    except Exception as e:
        logger.error(f"Failed to initialize Arize Phoenix tracing: {e}")

# The decorator is kept for compatibility with any custom spans outside of ADK
def trace_span(name: str, attributes: dict[str, Any] | None = None):
    # If using OpenTelemetry, this would typically map to a custom trace span.
    # For now, OpenInference auto-instruments ADK tools and LLM calls, so custom 
    # spans are a no-op fallback to prevent breaking scaffolded code.
    def decorator(func):
        return func
    return decorator

# Kept for compatibility, though OpenInference handles this automatically
def log_llm_call(_span: dict[str, Any], model: str, input_text: str, output_text: str, token_counts: dict[str, Any]) -> None:
    pass

def log_tool_call(_span: dict[str, Any], tool_name: str, input_args: dict[str, Any], output_result: Any) -> None:
    pass

def log_agent_routing(_span: dict[str, Any], from_agent: str, to_agent: str, reason: str) -> None:
    pass
