from google.adk.agents import LlmAgent
from nexus_ai.config import get_settings

from nexus_ai_doctor.adk.data_analyst import data_analyst
from nexus_ai_doctor.adk.summarizer import summarizer
from nexus_ai_doctor.adk.sandbox_agent import sandbox_agent

root_doctor_agent = LlmAgent(
    model=get_settings().adk_model,
    name="nexus_ai_doctor_root",
    description="Root orchestration agent for the nexus_ai Doctor module.",
    instruction=(
        "You are the nexus_ai Doctor Root Agent — the central orchestration hub for a "
        "multi-agent clinical assistant platform designed to aid doctors.\n\n"
        "YOUR ROLE:\n"
        "You receive requests from doctors and delegate work to the most appropriate "
        "specialist agent. You coordinate results and present a unified response.\n\n"
        "DELEGATION MAP:\n"
        "• **Data Analyst Agent** (`data_analyst`): Delegate when the doctor needs medical records analyzed, "
        "lab results interpreted, or clinical insights extracted.\n\n"
        "• **Summarizer Agent** (`summarizer`): Delegate when the doctor needs an ISBAR handover report "
        "or a patient shift summary generated.\n\n"
        "• **Sandbox Agent** (`nexus_ai_sandbox_agent`): Delegate when programmatic action is required, "
        "such as analyzing data files with pandas, writing automation scripts, or using the Workspace CLI "
        "to manage calendar events and send emails.\n\n"
    ),
    sub_agents=[
        data_analyst,
        summarizer,
        sandbox_agent,
    ],
)
