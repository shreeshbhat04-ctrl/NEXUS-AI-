import httpx

from nexus_ai.adapters.openfda import OpenFDAAdapter


class DummyResponse:
    def __init__(self, status_code: int, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.request = httpx.Request("GET", "https://api.fda.gov/drug/label.json")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=self.request,
                response=httpx.Response(self.status_code, request=self.request),
            )

    def json(self) -> dict:
        return self._payload


def test_lookup_drug_label_returns_not_found_on_404(monkeypatch) -> None:
    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url: str, params: dict) -> DummyResponse:
            return DummyResponse(404)

    monkeypatch.setattr(httpx, "Client", DummyClient)

    adapter = OpenFDAAdapter()
    result = adapter.lookup_drug_label("Clobetasol Propionate 0.05% Cream")

    assert result == {
        "medication_name": "Clobetasol Propionate 0.05% Cream",
        "found": False,
        "label": None,
    }


def test_lookup_drug_label_falls_back_to_normalized_name(monkeypatch) -> None:
    captured_queries: list[str] = []

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url: str, params: dict) -> DummyResponse:
            captured_queries.append(params["search"])
            if "0.05% Cream" in params["search"]:
                return DummyResponse(404)
            return DummyResponse(
                200,
                {
                    "results": [
                        {
                            "openfda": {
                                "brand_name": ["Temovate"],
                                "generic_name": ["Clobetasol Propionate"],
                                "manufacturer_name": ["Example Pharma"],
                            },
                            "warnings": ["For external use only."],
                            "boxed_warning": ["Serious warning text."],
                            "contraindications": ["Do not use with example condition."],
                            "adverse_reactions": ["Skin irritation."],
                            "dosage_and_administration": ["Apply as directed."],
                            "dosage_forms_and_strengths": ["Cream 0.05%."],
                            "drug_interactions": ["Example interaction."],
                            "warnings_and_cautions": ["Avoid contact with eyes."],
                        }
                    ]
                },
            )

    monkeypatch.setattr(httpx, "Client", DummyClient)

    adapter = OpenFDAAdapter()
    result = adapter.lookup_drug_label("Clobetasol Propionate 0.05% Cream")

    assert result["found"] is True
    assert result["label"]["generic_name"] == ["Clobetasol Propionate"]
    assert result["label"]["boxed_warning"] == ["Serious warning text."]
    assert result["label"]["contraindications"] == ["Do not use with example condition."]
    assert result["label"]["adverse_reactions"] == ["Skin irritation."]
    assert result["label"]["dosage_and_administration"] == ["Apply as directed."]
    assert result["label"]["dosage_forms_and_strengths"] == ["Cream 0.05%."]
    assert result["label"]["drug_interactions"] == ["Example interaction."]
    assert result["label"]["warnings_and_cautions"] == ["Avoid contact with eyes."]
    assert len(captured_queries) == 2
    assert captured_queries[0] == 'openfda.brand_name:"Clobetasol Propionate 0.05% Cream" OR openfda.generic_name:"Clobetasol Propionate 0.05% Cream"'
    assert captured_queries[1] == 'openfda.brand_name:"Clobetasol Propionate" OR openfda.generic_name:"Clobetasol Propionate"'
