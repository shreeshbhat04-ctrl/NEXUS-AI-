from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from nexus_ai.patient_finance.orchestrator import PatientFinanceOrchestrator


finance_router = APIRouter(prefix="/api/finance", tags=["patient-finance"])
orchestrator = PatientFinanceOrchestrator()


class ConsentRequest(BaseModel):
    patient_id: int
    bill_id: str
    offer_id: str


class SubmitRequest(BaseModel):
    patient_id: int
    bill_id: str
    offer_id: str
    consent_id: str


@finance_router.post("/upload-bill")
async def upload_bill(
    patient_id: int = Form(...),
    file: UploadFile = File(...),
) -> dict[str, Any]:
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Only PDF bill uploads are supported in this flow.")

    raw_bytes = await file.read()
    snapshot = orchestrator.start_workflow(
        patient_id=patient_id,
        filename=file.filename or "medical-bill.pdf",
        content_type=file.content_type or "application/pdf",
        raw_bytes=raw_bytes,
    )
    return {
        "bill_id": snapshot.bill_id,
        "session_id": snapshot.session_id,
        "status": "processing",
        "summary": snapshot.model_dump(mode="json", by_alias=True),
    }


@finance_router.get("/summary/{bill_id}")
def get_finance_summary(bill_id: str) -> dict[str, Any]:
    snapshot = orchestrator.get_snapshot_by_bill(bill_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="No finance workflow found for that bill.")
    return snapshot.model_dump(mode="json", by_alias=True)


@finance_router.get("/audit/{bill_id}")
def get_audit(bill_id: str) -> dict[str, Any]:
    audit = orchestrator.get_audit(bill_id)
    if audit is None:
        raise HTTPException(status_code=404, detail="Audit result not found.")
    return audit.model_dump(mode="json", by_alias=True) if hasattr(audit, "model_dump") else audit


@finance_router.get("/gap/{bill_id}")
def get_gap(bill_id: str) -> dict[str, Any]:
    gap = orchestrator.get_gap(bill_id)
    if gap is None:
        raise HTTPException(status_code=404, detail="Gap result not found.")
    return gap.model_dump(mode="json", by_alias=True) if hasattr(gap, "model_dump") else gap


@finance_router.get("/loans/{bill_id}")
def get_loans(bill_id: str) -> dict[str, Any]:
    offers = orchestrator.get_ranked_offers(bill_id)
    return {
        "offers": [offer.model_dump(mode="json", by_alias=True) if hasattr(offer, "model_dump") else offer for offer in offers]
    }


@finance_router.get("/policy-citations/{bill_id}")
def get_policy_citations(bill_id: str) -> dict[str, Any]:
    citations = orchestrator.get_policy_citations(bill_id)
    snapshot = orchestrator.get_snapshot_by_bill(bill_id)
    viewer_ready = snapshot.viewer_ready_format if snapshot else {}
    return {
        "citations": [citation.model_dump(mode="json", by_alias=True) for citation in citations],
        "viewer_ready_format": viewer_ready,
    }


@finance_router.post("/consent")
def record_consent(payload: ConsentRequest) -> dict[str, Any]:
    consent = orchestrator.record_consent(payload.patient_id, payload.bill_id, payload.offer_id)
    return consent.model_dump(mode="json", by_alias=True)


@finance_router.post("/submit")
def submit_application(payload: SubmitRequest) -> dict[str, Any]:
    try:
        return orchestrator.submit_offer(
            patient_id=payload.patient_id,
            bill_id=payload.bill_id,
            offer_id=payload.offer_id,
            consent_id=payload.consent_id,
        )
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@finance_router.get("/workflow-status/{session_id}")
async def workflow_status(session_id: str) -> StreamingResponse:
    snapshot = orchestrator.get_snapshot_by_session(session_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Workflow session not found.")

    async def event_stream():
        for event in snapshot.events:
            yield f"data: {json.dumps(event.model_dump(mode='json', by_alias=True))}\n\n"
            await asyncio.sleep(0.05)

    return StreamingResponse(event_stream(), media_type="text/event-stream")

