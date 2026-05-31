from dataclasses import dataclass


@dataclass
class AlternativeRecord:
    name: str
    formulation_note: str
    stock_status: str


class MockFormularyAdapter:
    def find_alternatives(self, medication_name: str) -> list[AlternativeRecord]:
        return [
            AlternativeRecord(
                name=f"{medication_name} XR",
                formulation_note="Extended-release alternative available nearby.",
                stock_status="in_stock",
            ),
            AlternativeRecord(
                name=f"{medication_name} Generic",
                formulation_note="Generic standard-release option.",
                stock_status="in_stock",
            ),
        ]
