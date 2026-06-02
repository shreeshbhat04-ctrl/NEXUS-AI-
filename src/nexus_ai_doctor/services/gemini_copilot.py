import os
import json
import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an Agentic Medical Copilot specializing in medical data science.
You generate Python code for an E2B Code Interpreter sandbox (pandas, numpy, scikit-learn, scipy, matplotlib, seaborn, pydicom, nibabel).
IMPORTANT: Use the Google Search tool to find the latest documentation for libraries like nibabel or pydicom before writing code to avoid deprecated functions.
CRITICAL: If the user's prompt is ambiguous or lacks necessary specific details (e.g., "filter the data" without saying how), return status="AMBIGUOUS", a clarifying question, and a list of options. Otherwise, return status="EXECUTABLE" and the code.
Your code MUST print or display results. For plots, matplotlib plt.show() works automatically.

Respond strictly in JSON matching this schema:
{
  "status": "EXECUTABLE" | "AMBIGUOUS",
  "code": "Python code here", // if EXECUTABLE
  "question": "Clarifying question", // if AMBIGUOUS
  "options": ["Option A", "Option B"] // if AMBIGUOUS
}"""

class GeminiCopilot:
    def __init__(self):
        # google-genai client will automatically pick up GEMINI_API_KEY or GOOGLE_API_KEY from environment.
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            # Try default initialization
            try:
                self.client = genai.Client()
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")
                self.client = None

    async def generate_code_or_clarify(self, prompt: str) -> dict:
        if not self.client:
            return {
                "status": "EXECUTABLE",
                "code": "# Error: Gemini API client not initialized. Check GEMINI_API_KEY environment variable."
            }

        try:
            # We run synchronously via thread pool or just call the sync generate_content for simplicity,
            # or use client.aio for async if available in google-genai. 
            # The google-genai library supports client.aio for async.
            response = await self.client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.2,
                    response_mime_type="application/json",
                    tools=[{"google_search": {}}]
                )
            )
            
            text = response.text or "{}"
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"status": "EXECUTABLE", "code": text}
        except Exception as e:
            logger.error(f"Error in generate_code_or_clarify: {e}")
            return {
                "status": "EXECUTABLE",
                "code": f"# Error calling Gemini API: {str(e)}"
            }

    async def generate_mermaid_diagram(self, question: str, options: list) -> str:
        if not self.client:
            return "graph TD\n    A[Error: Gemini Client not initialized]"

        prompt = f"""The user was asked: "{question}" with options: {json.dumps(options)}. 
Please create a Mermaid diagram illustrating these options and their clinical/code consequences so the user can make an informed decision.
Return ONLY valid mermaid code starting with "graph TD" or similar. Do not use markdown blocks."""

        try:
            response = await self.client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.2)
            )
            
            text = response.text or ""
            # Strip markdown fence if present
            if "```mermaid" in text:
                import re
                match = re.search(r"```mermaid\n([\s\S]*?)```", text)
                if match:
                    return match.group(1).strip()
            return text.replace("```mermaid", "").replace("```", "").strip()
        except Exception as e:
            logger.error(f"Error in generate_mermaid_diagram: {e}")
            return f"graph TD\n    A[Error generating diagram: {str(e)}]"
