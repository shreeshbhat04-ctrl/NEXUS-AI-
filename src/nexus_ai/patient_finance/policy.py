from __future__ import annotations

import json
import re
from pathlib import Path

from nexus_ai.patient_finance.arize_tracing import trace_span
from nexus_ai.patient_finance.models import BoundingBox, CitationPayload, PolicyChunk, PolicyCitation
from nexus_ai.patient_finance.mongodb import get_policy_chunks, save_policy_chunks


FIXTURE_PATH = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "policies" / "sample_policy_chunks.json"


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@trace_span("patient_finance.parse_policy_chunks")
def parse_policy_chunks(doc_path: str | None = None) -> list[PolicyChunk]:
    _ = doc_path
    payload = _load_fixture()
    source_doc_id = payload["source_doc_id"]
    chunks = [
        PolicyChunk(
            chunk_id=raw_chunk["chunk_id"],
            page=int(raw_chunk["page"]),
            bbox=BoundingBox(
                x1=float(raw_chunk["bbox"]["x"]),
                y1=float(raw_chunk["bbox"]["y"]),
                x2=float(raw_chunk["bbox"]["x"] + raw_chunk["bbox"]["w"]),
                y2=float(raw_chunk["bbox"]["y"] + raw_chunk["bbox"]["h"]),
                pageNumber=int(raw_chunk["page"]),
            ),
            text=raw_chunk["text"],
            section_title=raw_chunk["section_title"],
            source_doc_id=source_doc_id,
        )
        for raw_chunk in payload["chunks"]
    ]
    save_policy_chunks(source_doc_id, chunks)
    return chunks


def _tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2}


@trace_span("patient_finance.policy_lookup")
def retrieve_relevant_chunks(query: str, source_doc_id: str, top_k: int = 5) -> list[PolicyChunk]:
    stored = get_policy_chunks(source_doc_id)
    chunks = [PolicyChunk.model_validate(chunk) for chunk in stored] if stored else parse_policy_chunks()
    query_tokens = _tokenize(query)
    ranked: list[PolicyChunk] = []
    for chunk in chunks:
        text_tokens = _tokenize(f"{chunk.section_title} {chunk.text}")
        overlap = len(query_tokens & text_tokens)
        ranked.append(chunk.model_copy(update={"relevance_score": float(overlap)}))
    ranked.sort(key=lambda item: item.relevance_score, reverse=True)
    top = [chunk for chunk in ranked[:top_k] if chunk.relevance_score > 0]
    return top or ranked[:top_k]


def _relevance_tag(chunk: PolicyChunk) -> str:
    title = chunk.section_title.lower()
    if "exclusion" in title:
        return "exclusion"
    if "limit" in title or "deductible" in title:
        return "limitation"
    if "copay" in title or "coverage" in title:
        return "coverage"
    return "general"


def build_citation_payload(chunks: list[PolicyChunk], query_result: dict | None = None) -> CitationPayload:
    highlights: list[dict] = []
    citations: list[PolicyCitation] = []
    for chunk in chunks:
        excerpt = chunk.text[:220].strip()
        position = {
            "boundingRect": {
                "x1": chunk.bbox.x1,
                "y1": chunk.bbox.y1,
                "x2": chunk.bbox.x2,
                "y2": chunk.bbox.y2,
                "width": chunk.bbox.width,
                "height": chunk.bbox.height,
                "pageNumber": chunk.page,
            },
            "rects": [
                {
                    "x1": chunk.bbox.x1,
                    "y1": chunk.bbox.y1,
                    "x2": chunk.bbox.x2,
                    "y2": chunk.bbox.y2,
                    "width": chunk.bbox.width,
                    "height": chunk.bbox.height,
                    "pageNumber": chunk.page,
                }
            ],
            "pageNumber": chunk.page,
        }
        highlights.append(
            {
                "id": chunk.chunk_id,
                "position": position,
                "comment": {
                    "text": excerpt,
                    "query": query_result.get("query") if query_result else None,
                },
            }
        )
        citations.append(
            PolicyCitation(
                id=chunk.chunk_id,
                section_title=chunk.section_title,
                page_number=chunk.page,
                excerpt=excerpt,
                relevance_tag=_relevance_tag(chunk),  # type: ignore[arg-type]
                bbox=chunk.bbox,
            )
        )
    return CitationPayload(
        chunk_ids=[chunk.chunk_id for chunk in chunks],
        citations=citations,
        viewer_ready_format={"highlights": highlights},
    )

