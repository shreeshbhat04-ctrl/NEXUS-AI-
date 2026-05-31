"""Data Fetcher Agent - retrieves patient data and medicine facts from AlloyDB.

Provides grounded lookup for medicine information, patient profile snapshots,
and historical condition context via the Nexus_ai MCP server tools.
"""

import os
from pathlib import Path
import sys

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from nexus_ai.config import get_settings

settings = get_settings()

repo_root = Path(__file__).resolve().parents[3]

_server_command = (
    sys.executable
    if settings.mcp_server_command == "python"
    else settings.mcp_server_command
)

_server_params = StdioServerParameters(
    command=_server_command,
    args=settings.mcp_server_arg_list,
    cwd=str(repo_root),
    env=os.environ.copy(),
)

data_fetcher_agent = LlmAgent(
    model=settings.gemini_fast_model_id,
    name="nexus_ai_data_fetcher_agent",
    description=(
        "Fetches and summarizes patient data, medicine facts, and historical "
        "condition context from the nexus_ai database via MCP tools. "
        "Provides grounded lookup for AlloyDB-backed medical information."
    ),
    instruction=(
        "You are the nexus_ai Data Fetcher Agent. Your role is to retrieve "
        "and summarize structured patient data from the shared brain store.\n\n"
        "CAPABILITIES:\n"
        "1. PATIENT PROFILES: Fetch patient demographics, conditions, and prescriptions "
        "using the brain_get_patient_profile and brain_get_relevant_conditions tools.\n"
        "2. MEDICINE FACTS: Look up medication safety information. When AlloyDB "
        "medicine grounding is available, use it for Indian-market medication data.\n"
        "3. HISTORICAL CONTEXT: Retrieve past condition snapshots to provide "
        "temporal medical context for agent reasoning.\n"
        "4. HEALTH CHECK: Verify database connectivity via brain_healthcheck.\n\n"
        "RULES:\n"
        "- Always return structured, factual data without embellishment.\n"
        "- Clearly state when data is unavailable or incomplete.\n"
        "- Never invent medical facts — only return what the database provides.\n"
        "- Include source attribution (e.g., 'from patient profile' or 'from AlloyDB')."
    ),
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(server_params=_server_params),
        ),
    ],
)
