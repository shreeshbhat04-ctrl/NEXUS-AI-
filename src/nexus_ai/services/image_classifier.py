"""Gemini-powered medical image classifier.

Sends an image to Gemini's multimodal API and asks it to categorize the image
as PRESCRIPTION, SYMPTOM, or OTHER.  The returned category is used by the
integration layer to route Drive uploads into the correct subfolder.
"""

from __future__ import annotations

import logging
from pathlib import Path

from google import genai
from google.genai import types

from nexus_ai.config import get_settings

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {"PRESCRIPTION", "SYMPTOM", "OTHER"}

CLASSIFICATION_PROMPT = (
    "Categorize this medical image. "
    "Reply with ONLY ONE WORD: either 'PRESCRIPTION', 'SYMPTOM', or 'OTHER'."
)

# Map categories to human-friendly Drive subfolder names.
CATEGORY_FOLDER_MAP: dict[str, str] = {
    "PRESCRIPTION": "Prescriptions",
    "SYMPTOM": "Symptoms",
    "OTHER": "Other",
}

# Image extensions that the classifier will attempt to process.
_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".heic", ".gif"}


def _is_image_file(file_path: str) -> bool:
    """Return True if the file path looks like an image based on its extension."""
    return Path(file_path).suffix.lower() in _IMAGE_EXTENSIONS


class ImageClassifierService:
    """Uses Gemini multimodal to classify medical images."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def classify_medical_image(self, file_path: str) -> str:
        """Classify *file_path* and return one of PRESCRIPTION / SYMPTOM / OTHER.

        Non-image files are returned as OTHER without calling the API.
        Any API or parsing errors also fall back to OTHER.
        """
        if not _is_image_file(file_path):
            logger.info("Skipping classification for non-image file: %s", file_path)
            return "OTHER"

        path = Path(file_path)
        if not path.exists():
            logger.warning("Image file not found for classification: %s", file_path)
            return "OTHER"

        try:
            return self._call_gemini(path)
        except Exception:
            logger.exception("Gemini classification failed for %s — defaulting to OTHER", file_path)
            return "OTHER"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _call_gemini(self, image_path: Path) -> str:
        """Send the image to Gemini and parse the one-word response."""
        client = genai.Client(api_key=self.settings.google_api_key)

        # Read the image bytes and determine MIME type.
        image_bytes = image_path.read_bytes()
        mime_type = self._mime_for_extension(image_path.suffix.lower())

        response = client.models.generate_content(
            model=self.settings.gemini_fast_model_id,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                CLASSIFICATION_PROMPT,
            ],
        )

        raw = (response.text or "").strip().upper()
        logger.info("Gemini classification raw response: %r", raw)

        if raw in VALID_CATEGORIES:
            return raw

        # Attempt to find a valid category anywhere in the response.
        for category in VALID_CATEGORIES:
            if category in raw:
                logger.info("Extracted category %s from noisy response", category)
                return category

        logger.warning("Unexpected Gemini response %r — defaulting to OTHER", raw)
        return "OTHER"

    @staticmethod
    def _mime_for_extension(ext: str) -> str:
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
            ".tiff": "image/tiff",
            ".heic": "image/heic",
            ".gif": "image/gif",
        }
        return mime_map.get(ext, "application/octet-stream")
