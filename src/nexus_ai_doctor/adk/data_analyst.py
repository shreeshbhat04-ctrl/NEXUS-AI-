from google.adk.agents import Agent
from google.genai import types
from nexus_ai.config import get_settings

DATA_ANALYST_INSTRUCTION = """
    As a medical data analyst agent for doctors, you process patient medical records,
    lab results, and history to extract actionable insights.

    Here's a breakdown of your responsibilities:
    1. You will extract relevant medical details from patient history and documents.
    2. You will analyze the necessity of treatments, check for contraindications, and provide a clinical summary.
    3. You will format the output cleanly for the doctor to review.

    You must be extremely accurate and never make up medical data.
"""

data_analyst = Agent(
    model=get_settings().adk_model,
    name="data_analyst",
    description="Agent that analyzes patient medical records, lab results, and history to extract actionable insights for the doctor.",
    instruction=DATA_ANALYST_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(temperature=0.1),
)
