from nexus_ai.adapters.wikipedia import WikipediaAdapter
from nexus_ai.adapters.formulary import MockFormularyAdapter
from nexus_ai.api.models import AlternativeCandidate
from nexus_ai.services.brain import BrainCondition


class FormularyAgent:
    def __init__(
        self, 
        formulary_adapter: MockFormularyAdapter | None = None,
        wiki_adapter: WikipediaAdapter | None = None
    ) -> None:
        self.formulary_adapter = formulary_adapter or MockFormularyAdapter()
        self.wiki_adapter = wiki_adapter or WikipediaAdapter()

    def check_alternatives(self, medication_name: str, conditions: list[BrainCondition]) -> tuple[list[AlternativeCandidate], bool, str]:
        condition_names = {condition.name.lower() for condition in conditions}
        candidates: list[AlternativeCandidate] = []
        escalation_required = False

        # 1. Start with the clinical lookup (formulation details)
        formulation_records = self.formulary_adapter.find_alternatives(medication_name)
        
        # 2. Enrich with Wikipedia context
        wiki_result = self.wiki_adapter.lookup_drug_label(medication_name)
        
        for record in formulation_records:
            safety_note = "No known issue from demo context."
            if "ibs" in condition_names and "extended" in record.formulation_note.lower():
                safety_note = "Extended-release option may irritate active IBS. Doctor review required."
                escalation_required = True
            
            # Extract actual alternative labels from Wikipedia data if available
            display_name = record.name
            if wiki_result.get("found") and wiki_result.get("label"):
                label = wiki_result["label"]
                wiki_title = label.get("title")
                
                # If we found a Wikipedia page that matches the record name reasonably,
                # use the Wikipedia title for professional display.
                if wiki_title and display_name.lower() in wiki_title.lower():
                    display_name = wiki_title
            
            candidates.append(
                AlternativeCandidate(
                    name=display_name,
                    formulation_note=record.formulation_note,
                    safety_note=safety_note,
                )
            )

        summary = "Escalation required because a candidate needs clinician review." if escalation_required else "No blocking safety issues from demo context."
        return candidates, escalation_required, summary

