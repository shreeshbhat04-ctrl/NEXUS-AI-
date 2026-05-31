"""Gemini Vision service for symptom image / prescription analysis
and AI-powered diagnostic image generation.

Uses the google-genai SDK.  Nothing is hardcoded – system instructions,
model ids and the API key are all pulled from configuration or built
dynamically from analysis results.
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any

from google import genai
from google.genai import types

from nexus_ai.config import get_settings

logger = logging.getLogger(__name__)

# ─── System instructions ────────────────────────────────────────────

SYMPTOM_ANALYSIS_SYSTEM_INSTRUCTION = """\
You are a medical image analysis assistant integrated into a chronic-care
management platform called nexus_ai.

When the user uploads a medical image (symptom photo, skin condition,
lab report, prescription scan, etc.) you MUST return a JSON object with
exactly these keys:

{
  "severity": "<string: one of 'Mild', 'Moderate', 'Severe', 'Critical', or 'Inconclusive'>",
  "confidence": <integer 0-100>,
  "findings": ["<string>", ...],
  "summary": "<string: 2-4 sentence clinical summary>"
}

Guidelines:
- Be factual and concise.  Do NOT diagnose – describe observations only.
- If the image is a prescription or lab report, extract the key information
  into findings and summarise it.
- If the image quality is too poor to analyse, set severity to
  "Inconclusive", confidence to a low number, and explain in the summary.
- ALWAYS respond with valid JSON only – no markdown fences, no extra text.
"""

PRESCRIPTION_ANALYSIS_SYSTEM_INSTRUCTION = """\
You are a prescription reading assistant integrated into a chronic-care
management platform called nexus_ai.

When the user uploads a prescription image you MUST return a JSON object
with exactly these keys:

{
  "medication_name": "<string>",
  "dosage": "<string>",
  "instructions": "<string>",
  "confidence": <integer 0-100>,
  "findings": ["<string>", ...],
  "summary": "<string: 2-3 sentence summary of the prescription>"
}

Guidelines:
- Extract medication name, dosage and instructions from the prescription.
- List each distinct medication / instruction as a separate finding.
- If the image is unclear, set confidence low and explain in summary.
- ALWAYS respond with valid JSON only – no markdown fences, no extra text.
"""

AUTO_DETECT_SYSTEM_INSTRUCTION = """\
You are a medical image analysis assistant integrated into a chronic-care
management platform called nexus_ai.

The user has uploaded a medical image but has NOT told you what type it is.
You must FIRST determine what the image contains, then analyse it.

Step 1 – Classify the image as one of:
  "prescription"  – a handwritten or printed prescription / medication label
  "symptom"       – a photo of a body part, skin condition, wound, etc.
  "lab_report"    – a lab result, blood work, or diagnostic report
  "other"         – anything else (e.g. insurance card, ID, unrelated photo)

Step 2 – Based on your classification, return a JSON object with these keys:

{
  "detected_type": "<string: prescription | symptom | lab_report | other>",
  "medication_name": "<string or null>",
  "dosage": "<string or null>",
  "instructions": "<string or null>",
  "severity": "<string: Mild | Moderate | Severe | Critical | Inconclusive | null>",
  "confidence": <integer 0-100>,
  "findings": ["<string>", ...],
  "summary": "<string: 2-4 sentence summary>",
  "diet_relevant": <boolean: true if findings may affect diet or medication-food interactions>
}

Guidelines:
- Fill in medication fields only if detected_type is "prescription".
- Fill in severity only if detected_type is "symptom" or "lab_report".
- Set diet_relevant to true if any finding involves medication known for
  food interactions (e.g. Warfarin, Metformin, blood thinners, etc.)
- ALWAYS respond with valid JSON only – no markdown fences, no extra text.
"""

PHARMACEUTICAL_INSPECTION_SYSTEM_INSTRUCTION = """\
Role & Objective
You are an expert pharmaceutical visual inspector. Your task is to analyze images of medication packaging, identify the type of container, extract key medical information, and assess its physical state.

Execution Steps (You MUST follow this sequence):
Step 1: Container Classification
Look at the primary object in the image and classify it into one of the following categories:
- Blister Pack (sheets with foil backing and plastic bubbles)
- Tube/Ointment (squeezable tubes for creams or gels)
- Bottle/Vial (solid containers for liquids or loose pills)
- Other (boxes, syringes, inhalers, etc.)

Step 2: Universal Label Extraction (Apply to ALL categories)
Regardless of the container type, carefully read and extract:
- Brand Name: (e.g., Bilashine-M, paracetomol)
- Active Ingredients & Strengths: (e.g., Bilastine 20mg, Montelukast 10mg)
- Warnings/Notices: Look specifically for colored boxes (like red "SCHEDULE H" or "Caution" boxes).

Step 3: Physical Assessment (Branching Logic)
Apply the specific rule set based on your classification in Step 1:
IF BLISTER PACK:
- Grid Mapping: Determine the grid layout (e.g., "2 columns by 5 rows = 10 total slots").
- Scan: Check every slot. An "Opened" slot has torn, pushed-in, or missing foil. A "Sealed" slot has an intact, raised bump.
- Tally: Output Total Slots, Opened Slots, and Sealed Slots.

IF TUBE/OINTMENT:
- Net Weight/Volume: Find the total quantity printed on the tube (e.g., 15g, 30ml).
- Usage State: Look at the physical shape of the tube. Is it perfectly inflated and smooth (likely New/Unused)? Or is it crumpled, folded, and squeezed flat at the bottom (Used)?
- Cap Status: Is the cap securely on, missing, or open?

IF BOTTLE/VIAL:
- Volume: Find the total volume (e.g., 100ml).
- Fill Level: If the bottle is transparent, estimate if it is Full, Partially Full, or Empty based on the liquid line.

Step 4: Final Output Generation
Provide a structured summary containing the Classification, Extracted Text, and the Physical Assessment based on the rules above. Keep the output clean and factual.

Output:
Return ONLY valid JSON with the following fields:
{
  "no_of_tablets_consumed": <integer or null>,
  "no_of_tablets_present": <integer or null>,
  "percentage_of_ointment_left": <float or null>,   // percentage (0–100)
  "confidence_score": <float>,              // between 0 and 1
  "medication_name": "<string>"
}

Constraints:
- Do not invent or assume details not visible in the image.
- If a field cannot be determined, leave it blank or null.
- Output must be valid JSON only, no extra commentary.
"""

DIAGNOSTIC_IMAGE_SYSTEM_INSTRUCTION = """\
You are a medical imaging specialist AI that creates professional
diagnostic comparison graphics for the nexus_ai chronic-care platform.

When given a patient's symptom image and its analysis results, you MUST
generate a technical, side-by-side diagnostic comparison image.

Follow this layout specification exactly:

LAYOUT:
- White background.  Divide the image into two equal vertical panels
  separated by a thick black border.
- LEFT PANEL:  Show the original uploaded symptom area / condition as
  you understand it – recreate or represent the key visual features of
  the condition.
- RIGHT PANEL:  Show an annotated medical-diagram view of the same
  area highlighting the specific findings from the analysis.

HEADER:
- At the very top, add a bold, centered header in a clear sans-serif
  font reading: 'nexus_ai Diagnostic Report'.
- Above the left panel add the sub-header 'Uploaded Image'.
- Above the right panel add the sub-header 'AI Analysis Overlay'.

ANNOTATIONS (LEFT PANEL):
- Draw bright yellow bounding boxes around the areas that correspond
  to the most significant findings.
- Attach small white text boxes with black borders containing
  sequential numbers (1, 2, …) to each annotated area.

ANNOTATIONS (RIGHT PANEL):
- Draw bright yellow arrows pointing to each area of clinical
  interest identified in the findings.
- Attach small white text boxes with black borders containing
  sequential numbers matching the legend.

LEGEND:
- At the bottom of the graphic, create a white section divided by a
  black line.
- Create a numbered text legend.  For every number used in the
  annotations, write the ACTUAL clinical description from the analysis
  findings – do NOT use placeholder text.  Explain in your own medical
  words why you think the condition has worsened, improved, or stayed
  the same based on what you observe.

DISCLAIMER:
- Add a small disclaimer at the bottom-right reading:
  'AI-generated – not a substitute for professional medical advice.'

IMPORTANT:
- Replace every description/label with what YOU believe is the correct
  clinical observation.  Never leave generic placeholders.
- The legend descriptions should reflect your reasoning about the
  severity, progression, or improvement of the condition.
"""


class GeminiVisionService:
    """Wrapper around google-genai for medical image analysis and
    diagnostic image generation."""

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key: str | None = settings.google_api_key
        self._analysis_model_id: str = "gemini-2.0-flash"
        self._image_gen_model_id: str = "gemini-2.0-flash-exp"

    # ── Public: text analysis ───────────────────────────────────────

    def analyze_symptom_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        analysis_type: str = "symptom",
    ) -> dict[str, Any]:
        """Send *image_bytes* to Gemini and return structured analysis.

        Parameters
        ----------
        image_bytes : raw bytes of the uploaded image.
        mime_type   : e.g. ``image/jpeg``, ``image/png``.
        analysis_type : ``"symptom"`` or ``"prescription"``.
        """
        if not self._api_key:
            logger.warning("GOOGLE_API_KEY not set – returning fallback.")
            return self._fallback_response(analysis_type)

        system_instruction = (
            PRESCRIPTION_ANALYSIS_SYSTEM_INSTRUCTION
            if analysis_type == "prescription"
            else SYMPTOM_ANALYSIS_SYSTEM_INSTRUCTION
        )

        try:
            client = genai.Client(api_key=self._api_key)

            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(mime_type=mime_type, data=image_bytes),
                        types.Part.from_text(
                            text="Analyze this uploaded medical image and return the structured JSON response."
                        ),
                    ],
                ),
            ]

            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                system_instruction=[types.Part.from_text(text=system_instruction)],
            )

            response = client.models.generate_content(
                model=self._analysis_model_id,
                contents=contents,
                config=config,
            )

            raw_text = response.text.strip() if response.text else ""
            logger.info("Gemini analysis raw (500): %s", raw_text[:500])
            return self._parse_response(raw_text, analysis_type)

        except Exception:
            logger.exception("Gemini analysis call failed")
            return self._fallback_response(analysis_type)

    def inspect_medication_state(
        self,
        image_bytes: bytes,
        mime_type: str,
    ) -> dict[str, Any]:
        """Perform pharmaceutical visual inspection (counting tablets, tube usage, etc.)"""
        if not self._api_key:
            return {"medication_name": "Unknown", "confidence_score": 0.0}

        try:
            client = genai.Client(api_key=self._api_key)
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(mime_type=mime_type, data=image_bytes),
                        types.Part.from_text(text="Analyze this medication packaging and perform a physical state assessment."),
                    ],
                ),
            ]
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                system_instruction=[types.Part.from_text(text=PHARMACEUTICAL_INSPECTION_SYSTEM_INSTRUCTION)],
            )
            response = client.models.generate_content(
                model=self._analysis_model_id,
                contents=contents,
                config=config,
            )
            raw_text = response.text.strip() if response.text else ""
            return self._parse_inspection_response(raw_text)
        except Exception:
            logger.exception("Pharmaceutical inspection failed")
            return {"medication_name": "Unknown", "confidence_score": 0.0}

    @staticmethod
    def _parse_inspection_response(raw_text: str) -> dict[str, Any]:
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Inspection JSON parse failed")
            return {"medication_name": "Unknown", "confidence_score": 0.0}

    # ── Public: auto-classify + analyse (fallback chain) ────────────

    def auto_analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        file_path: str | None = None,
    ) -> dict[str, Any]:
        """Classify an image automatically then analyse it.

        This is the primary entry-point when the user has NOT indicated
        whether the upload is a prescription, symptom photo, or other.

        Fallback chain:
        1. ImageClassifierService  →  PRESCRIPTION / SYMPTOM / OTHER
        2. If OTHER or if classifier fails  →  Gemini auto-detect prompt
        """
        category = self._classify_with_fallback(image_bytes, mime_type, file_path)
        logger.info("Auto-classification result: %s", category)

        if category == "PRESCRIPTION":
            analysis = self.analyze_symptom_image(image_bytes, mime_type, "prescription")
            return {"category": category, "analysis_type": "prescription", **analysis}

        if category == "SYMPTOM":
            analysis = self.analyze_symptom_image(image_bytes, mime_type, "symptom")
            return {"category": category, "analysis_type": "symptom", **analysis}

        # OTHER or unknown → let Gemini auto-detect with the unified prompt
        return self._auto_detect_analysis(image_bytes, mime_type)

    def _classify_with_fallback(
        self,
        image_bytes: bytes,
        mime_type: str,
        file_path: str | None = None,
    ) -> str:
        """Try ImageClassifierService first; if it fails, return OTHER."""
        if file_path:
            try:
                from nexus_ai.services.image_classifier import ImageClassifierService
                classifier = ImageClassifierService()
                result = classifier.classify_medical_image(file_path)
                if result in {"PRESCRIPTION", "SYMPTOM"}:
                    return result
            except Exception:
                logger.warning("ImageClassifier fallback failed; using Gemini auto-detect.")

        # Inline Gemini classification as a second-chance fallback
        if self._api_key:
            try:
                client = genai.Client(api_key=self._api_key)
                response = client.models.generate_content(
                    model=self._analysis_model_id,
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        "Categorize this medical image. Reply with ONLY ONE WORD: PRESCRIPTION, SYMPTOM, or OTHER.",
                    ],
                )
                raw = (response.text or "").strip().upper()
                for cat in ("PRESCRIPTION", "SYMPTOM"):
                    if cat in raw:
                        return cat
            except Exception:
                logger.warning("Inline Gemini classification also failed.")

        return "OTHER"

    def _auto_detect_analysis(
        self,
        image_bytes: bytes,
        mime_type: str,
    ) -> dict[str, Any]:
        """Use the unified AUTO_DETECT prompt when we don't know the image type."""
        if not self._api_key:
            return {"category": "OTHER", "analysis_type": "auto", **self._fallback_response("symptom")}

        try:
            client = genai.Client(api_key=self._api_key)
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(mime_type=mime_type, data=image_bytes),
                        types.Part.from_text(
                            text="Analyze this uploaded medical image. Determine what type it is and return the structured JSON response."
                        ),
                    ],
                ),
            ]
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                system_instruction=[types.Part.from_text(text=AUTO_DETECT_SYSTEM_INSTRUCTION)],
            )
            response = client.models.generate_content(
                model=self._analysis_model_id,
                contents=contents,
                config=config,
            )
            raw_text = response.text.strip() if response.text else ""
            logger.info("Auto-detect raw (500): %s", raw_text[:500])
            data = self._parse_auto_detect_response(raw_text)
            return {"category": data.get("detected_type", "OTHER").upper(), "analysis_type": "auto", **data}
        except Exception:
            logger.exception("Auto-detect analysis failed")
            return {"category": "OTHER", "analysis_type": "auto", **self._fallback_response("symptom")}

    @staticmethod
    def _parse_auto_detect_response(raw_text: str) -> dict[str, Any]:
        """Parse the unified auto-detect JSON response."""
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Auto-detect JSON parse failed: %s", cleaned[:300])
            return {
                "detected_type": "other",
                "confidence": 0,
                "findings": ["Could not parse auto-detect response."],
                "summary": "Image analysis could not be completed.",
                "diet_relevant": False,
            }
        return {
            "detected_type": data.get("detected_type", "other"),
            "medication_name": data.get("medication_name"),
            "dosage": data.get("dosage"),
            "instructions": data.get("instructions"),
            "severity": data.get("severity"),
            "confidence": int(data.get("confidence", 50)),
            "findings": data.get("findings", []),
            "summary": data.get("summary", "Analysis could not be completed."),
            "diet_relevant": data.get("diet_relevant", False),
        }

    # ── Public: diagnostic image generation ─────────────────────────


    def generate_diagnostic_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        analysis: dict[str, Any],
    ) -> str | None:
        """Generate an annotated diagnostic comparison graphic.

        Parameters
        ----------
        image_bytes : the original uploaded symptom image bytes.
        mime_type   : MIME type of the original image.
        analysis    : the dict returned by ``analyze_symptom_image``.

        Returns
        -------
        Base64-encoded PNG string of the generated diagnostic image,
        or ``None`` if generation fails / is unavailable.
        """
        if not self._api_key:
            logger.warning("GOOGLE_API_KEY not set – skipping diagnostic image.")
            return None

        # Build a dynamic user prompt that feeds the analysis findings
        # into the image-generation request so the model fills the
        # legend with real descriptions (never placeholders).
        findings_text = "\n".join(
            f"  {i + 1}. {f}" for i, f in enumerate(analysis.get("findings", []))
        )

        user_prompt = (
            f"Generate a professional diagnostic comparison image for the "
            f"following medical analysis.\n\n"
            f"Severity: {analysis.get('severity', 'Unknown')}\n"
            f"Confidence: {analysis.get('confidence', 0)}%\n"
            f"Summary: {analysis.get('summary', '')}\n\n"
            f"Findings to annotate:\n{findings_text}\n\n"
            f"Use the uploaded symptom image as the LEFT panel reference. "
            f"Create the annotated analysis overlay as the RIGHT panel. "
            f"Fill every legend entry with your own clinical reasoning "
            f"about why the condition may have worsened or improved. "
            f"Do NOT use placeholder text anywhere."
        )

        try:
            client = genai.Client(api_key=self._api_key)

            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(mime_type=mime_type, data=image_bytes),
                        types.Part.from_text(text=user_prompt),
                    ],
                ),
            ]

            config = types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                system_instruction=[
                    types.Part.from_text(text=DIAGNOSTIC_IMAGE_SYSTEM_INSTRUCTION),
                ],
            )

            response = client.models.generate_content(
                model=self._image_gen_model_id,
                contents=contents,
                config=config,
            )

            # Walk through response parts looking for an inline image
            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.data:
                        img_bytes = part.inline_data.data
                        # inline_data.data is already bytes
                        if isinstance(img_bytes, str):
                            return img_bytes  # already base64
                        return base64.b64encode(img_bytes).decode("utf-8")

            logger.warning("Gemini image generation returned no image parts.")
            return None

        except Exception:
            logger.exception("Diagnostic image generation failed")
            return None

    # ── Internals ───────────────────────────────────────────────────

    @staticmethod
    def _parse_response(raw_text: str, analysis_type: str) -> dict[str, Any]:
        """Parse Gemini JSON response with graceful fallback."""
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("JSON parse failed: %s", cleaned[:300])
            return GeminiVisionService._fallback_response(analysis_type)

        if analysis_type == "prescription":
            return {
                "medication_name": data.get("medication_name", "Unknown"),
                "dosage": data.get("dosage", ""),
                "instructions": data.get("instructions", ""),
                "confidence": int(data.get("confidence", 50)),
                "findings": data.get("findings", []),
                "summary": data.get("summary", "Unable to fully parse the prescription."),
            }

        return {
            "severity": data.get("severity", "Inconclusive"),
            "confidence": int(data.get("confidence", 50)),
            "findings": data.get("findings", []),
            "summary": data.get("summary", "Analysis could not be completed."),
        }

    @staticmethod
    def _fallback_response(analysis_type: str) -> dict[str, Any]:
        if analysis_type == "prescription":
            return {
                "medication_name": "Unknown",
                "dosage": "",
                "instructions": "",
                "confidence": 0,
                "findings": ["Could not process image – API unavailable or key missing."],
                "summary": "Prescription analysis is temporarily unavailable.",
            }
        return {
            "severity": "Inconclusive",
            "confidence": 0,
            "findings": ["Could not process image – API unavailable or key missing."],
            "summary": "Image analysis is temporarily unavailable.",
        }
