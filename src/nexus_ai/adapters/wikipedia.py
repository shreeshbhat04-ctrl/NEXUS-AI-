"""Wikipedia Adapter for medication lookup."""
import logging

logger = logging.getLogger(__name__)

class WikipediaAdapter:
    def __init__(self):
        pass

    def lookup_drug(self, medication_name: str) -> dict:
        return {
            "found": False,
            "title": medication_name,
            "summary": "Wikipedia lookup is currently stubbed.",
            "url": "",
        }
