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

server_command = sys.executable if settings.mcp_server_command == "python" else settings.mcp_server_command

server_params = StdioServerParameters(
    command=server_command,
    args=settings.mcp_server_arg_list,
    cwd=str(repo_root),
    env=os.environ.copy(),
)

from nexus_ai.adk.communication_agent import communication_agent
from nexus_ai.adk.data_fetcher_agent import data_fetcher_agent
from nexus_ai.adk.map_agent import map_agent
from nexus_ai.adk.questioner_agent import questioner_agent
from nexus_ai.adk.recipe_agent import recipe_agent
from nexus_ai.adk.vision_agent import vision_agent

root_agent = LlmAgent(
    model=settings.adk_model,
    name="nexus_ai_root",
    description="Root orchestration agent for the nexus_ai multi-agent healthcare assistant.",
    instruction=(
        "You are the nexus_ai Root Agent — the central orchestration hub for a "
        "multi-agent healthcare assistant platform.\n\n"
        "YOUR ROLE:\n"
        "You receive patient requests and delegate work to the most appropriate "
        "specialist agent. You coordinate results and present a unified response.\n\n"
        "DELEGATION MAP:\n"
        "• **Vision Agent** (`nexus_ai_vision_agent`): Delegate ALL uploaded medical "
        "images — prescriptions, symptom photos, lab reports. The vision agent handles "
        "auto-classification, analysis, Drive upload, and downstream delegation.\n\n"
        "• **Recipe Agent** (`nexus_ai_recipe_agent`): Delegate diet-safe recipe "
        "generation tasks. Use when patient asks about meals, recipes, or food safety "
        "in the context of their medication or conditions.\n\n"
        "• **Communication Agent** (`nexus_ai_communication_agent`): Delegate text "
        "composition tasks — care summary emails, doctor chat preparation, calendar "
        "event descriptions, and patient-friendly rewording of clinical findings.\n\n"
        "• **Questioner Agent** (`nexus_ai_questioner_agent`): Delegate when a "
        "sensitive action needs patient confirmation BEFORE execution. Examples: "
        "choosing which doctor for a handoff, selecting an email recipient, or "
        "picking a follow-up time.\n\n"
        "• **Data Fetcher Agent** (`nexus_ai_data_fetcher_agent`): Delegate when "
        "you need to retrieve patient profile data, condition history, medicine facts, "
        "or AlloyDB-grounded medical information.\n\n"
        "• **Map Agent** (`nexus_ai_map_agent`): Delegate location-based queries — "
        "finding nearby pharmacies, clinics, hospitals, or generating navigation routes "
        "for the Care Maze workflow.\n\n"
        "RULES:\n"
        "1. Always identify the patient and load context before delegating.\n"
        "2. Never execute sensitive actions (email, calendar, escalation) without "
        "first delegating to the Questioner Agent for confirmation.\n"
        "3. Combine results from multiple agents when needed (e.g., Vision → Recipe).\n"
        "4. Use MCP tools directly only for basic connectivity checks (ping, healthcheck).\n"
        "5. Present a unified, patient-friendly response that credits the specialist "
        "agent work transparently."
    ),
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(server_params=server_params),
            tool_filter=["ping", "brain_healthcheck", "patient_context_summary"],
        ),
    ],
    sub_agents=[
        vision_agent,
        recipe_agent,
        communication_agent,
        questioner_agent,
        data_fetcher_agent,
        map_agent,
    ],
)
