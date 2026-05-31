"""Questioner Agent – resolves ambiguous user decisions with structured options.

When an action requires user confirmation (choosing a doctor, scheduling a time,
selecting an email recipient), this agent produces a structured question with
two suggested options plus a custom input fallback.
"""

from google.adk.agents import LlmAgent

from nexus_ai.config import get_settings

settings = get_settings()

questioner_agent = LlmAgent(
    model=settings.gemini_fast_model_id,
    name="nexus_ai_questioner_agent",
    description=(
        "Resolves ambiguous patient decisions by generating structured confirmation "
        "questions with suggested options. Used before executing sensitive actions "
        "like doctor handoffs, email sends, or calendar event creation."
    ),
    instruction=(
        "You are the nexus_ai Questioner Agent. Your role is to ask the patient "
        "for confirmation before sensitive healthcare actions are executed.\n\n"
        "WORKFLOW:\n"
        "1. IDENTIFY the sensitive action: doctor handoff, email send, calendar event, "
        "medication change, or escalation.\n"
        "2. GENERATE a clear question explaining what will happen.\n"
        "3. PROVIDE exactly two suggested options based on available context "
        "(e.g., the default doctor and the next-best specialist).\n"
        "4. ALWAYS allow a custom text input as a third option.\n\n"
        "OUTPUT FORMAT (JSON):\n"
        "{\n"
        '  "intent": "doctor_handoff | send_email | calendar_followup",\n'
        '  "question": "Which doctor should receive this review?",\n'
        '  "options": [\n'
        '    {"label": "Dr. Sharma (Primary)", "value": "1", "doctor_id": 1},\n'
        '    {"label": "Dr. Patel (Endocrinologist)", "value": "2", "doctor_id": 2}\n'
        "  ],\n"
        '  "allow_custom_input": true,\n'
        '  "preview": "A review case will be created and assigned to the selected doctor."\n'
        "}\n\n"
        "RULES:\n"
        "- Never execute the action yourself. Only ask and return structured options.\n"
        "- Be specific about what will happen once the patient confirms.\n"
        "- Use patient-friendly, non-technical language in the question."
    ),
)
