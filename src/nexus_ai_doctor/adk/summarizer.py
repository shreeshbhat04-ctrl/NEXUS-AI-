from google.adk.agents import Agent
from google.genai import types
from nexus_ai.config import get_settings

SUMMARIZER_INSTRUCTION = """
    You are a medical summarization agent specializing in ISBAR handovers.
    Your goal is to help the doctor generate a structured handover report for a patient shift.
    
    Structure your output using the ISBAR format:
    - Identification: Who is the patient?
    - Situation: What is going on with the patient?
    - Background: What is the clinical background or context?
    - Assessment: What do I think the problem is?
    - Recommendation: What would I do to correct it?
"""

summarizer = Agent(
    model=get_settings().adk_model,
    name="summarizer",
    description="Agent that generates structured ISBAR handover reports from raw patient data.",
    instruction=SUMMARIZER_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(temperature=0.2),
)
