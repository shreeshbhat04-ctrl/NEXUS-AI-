from dataclasses import dataclass


@dataclass
class OCRResult:
    medication_name: str
    dosage: str | None
    instructions: str | None
    raw_text: str
    confidence_score: float


class MockOCRAdapter:
    def scan(self, image_reference: str | None = None, raw_text_hint: str | None = None) -> OCRResult:
        text = raw_text_hint or "Metformin 500 mg twice daily with meals"
        confidence = 0.92 if raw_text_hint else 0.88
        return OCRResult(
            medication_name="Metformin",
            dosage="500 mg",
            instructions="Twice daily with meals",
            raw_text=text,
            confidence_score=confidence,
        )
