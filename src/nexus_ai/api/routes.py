import json
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Response
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_ai.agents.orchestrator import Orchestrator
from nexus_ai.utils.url_router import ProductUrlRouter
from nexus_ai.api.models import (
    ActionConfirmRequest,
    ActionConfirmResponse,
    ActionDraftRequest,
    ActionDraftResponse,
    CareDestinationResponse,
    CareDestinationSearchRequest,
    CareDestinationSearchResponse,
    CareMapRouteRequest,
    CareMapRouteResponse,
    CaseResponse,
    CalendarEventRequest,
    CalendarEventResponse,
    CheckAlternativesRequest,
    CheckAlternativesResponse,
    ConversationRoutingRequest,
    ConversationRoutingResponse,
    DailyCheckInResponse,
    DietSupportRequest,
    DietSupportResponse,
    DoctorCreateRequest,
    DoctorResponse,
    DocumentFlowRequest,
    DocumentFlowResponse,
    DrugLabelRequest,
    DrugLabelResponse,
    DocumentPipelineRequest,
    DocumentPipelineResponse,
    DriveUploadRequest,
    DriveUploadResponse,
    EscalateRequest,
    EscalateResponse,
    GenerateDietRecipesRequest,
    GenerateDietRecipesResponse,
    HitlReportRequest,
    HitlReportResponse,
    MedicalRoutingRequest,
    MedicalRoutingResponse,
    MedicalMemorySearchRequest,
    MedicalMemorySearchResponse,
    MedicalMemoryStoreRequest,
    MedicalMemoryStoreResponse,
    MedicineGroundedAnswerRequest,
    ChatThreadCreateRequest,
    ChatMessageCreateRequest,
    ChatThreadResponse,
    ChatThreadListResponse,
    ChatMessageResponse,
    ChatMessageListResponse,
    MedicineGroundedAnswerResponse,
    DietRecipeTutorialResponse,
    SaveDietRecipeResponse,
    SavedDietRecipesResponse,
    MarketIngredientResponse,
    NotifyRequest,
    NotifyResponse,
    OrchestrationManifestResponse,
    PendingActionResponse,
    PatientIntakeRequest,
    PatientIntakeResponse,
    PatientDoctorMapRequest,
    PatientProfileResponse,
    PatientProfileUpdateRequest,
    PatientConditionSnapshotCreateRequest,
    PatientConditionSnapshotResponse,
    PatientHistoryQueryRequest,
    PatientVitalCreateRequest,
    PatientVitalResponse,
    PharmacySearchRequest,
    PharmacySearchResponse,
    PrescriptionAnalysisResponse,
    PrescriptionScanRequest,
    PrescriptionScanResponse,
    RoutineSnapshotResponse,
    RoutineTaskResponse,
    RoutineAutomationResponse,
    ScaleDietRecipeRequest,
    ScaleDietRecipeResponse,
    SymptomAnalysisResponse,
    VisionSuggestedAction,
    VisionUploadAnalyzeResponse,
    CartItemCreateRequest,
    CartItemResponse,
    CartCheckoutResponse,
)
from fastapi import WebSocket, WebSocketDisconnect
from nexus_ai.adapters.gemini_live import GeminiLive
import asyncio
from nexus_ai.db.models import EscalationCase
from nexus_ai.db.models import (
    ChronicCondition,
    Doctor,
    MedicalMemory,
    Notification,
    Patient,
    PatientConditionSnapshot,
    PatientDoctorMap,
    PatientProfileDetail,
    PatientVital,
    PendingAction,
    Prescription,
    SavedDietRecipe,
    CartItem,
)
from nexus_ai.db.session import get_db

router = APIRouter()
orchestrator = Orchestrator()


def _safe_json_load(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except json.JSONDecodeError:
        return []
    return []


def _profile_response(patient: Patient, detail: PatientProfileDetail | None) -> PatientProfileResponse:
    return PatientProfileResponse(
        patient_id=patient.id,
        full_name=patient.full_name,
        preferred_language=patient.preferred_language,
        date_of_birth=None if patient.date_of_birth is None else patient.date_of_birth.isoformat(),
        summary=patient.summary,
        height_cm=None if detail is None else detail.height_cm,
        weight_kg=None if detail is None else detail.weight_kg,
        blood_group=None if detail is None else detail.blood_group,
        allergies=[] if detail is None else _safe_json_load(detail.allergies_json),
        emergency_contact_name=None if detail is None else detail.emergency_contact_name,
        emergency_contact_phone=None if detail is None else detail.emergency_contact_phone,
        primary_language=None if detail is None else detail.primary_language,
        notes=None if detail is None else detail.notes,
        updated_at=None if detail is None or detail.updated_at is None else detail.updated_at.isoformat(),
    )


def _vital_response(vital: PatientVital) -> PatientVitalResponse:
    return PatientVitalResponse(
        id=vital.id,
        patient_id=vital.patient_id,
        blood_pressure=vital.blood_pressure,
        heart_rate_bpm=vital.heart_rate_bpm,
        blood_glucose_mg_dl=vital.blood_glucose_mg_dl,
        temperature_c=vital.temperature_c,
        weight_kg=vital.weight_kg,
        source=vital.source,
        recorded_at=vital.recorded_at.isoformat(),
    )


def _snapshot_response(snapshot: PatientConditionSnapshot) -> PatientConditionSnapshotResponse:
    def load_dict(raw: str | None) -> dict | None:
        if not raw:
            return None
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None

    def load_list(raw: str | None) -> list[dict]:
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [item for item in parsed if isinstance(item, dict)]
        except json.JSONDecodeError:
            return []
        return []

    return PatientConditionSnapshotResponse(
        id=snapshot.id,
        patient_id=snapshot.patient_id,
        snapshot_type=snapshot.snapshot_type,
        summary=snapshot.summary,
        profile=load_dict(snapshot.profile_json),
        conditions=load_list(snapshot.conditions_json),
        prescriptions=load_list(snapshot.prescriptions_json),
        vitals=load_list(snapshot.vitals_json),
        source_event_type=snapshot.source_event_type,
        source_event_id=snapshot.source_event_id,
        created_at=snapshot.created_at.isoformat(),
    )


def _create_profile_snapshot(
    db: Session,
    patient: Patient,
    detail: PatientProfileDetail | None,
    source_event_type: str,
    source_event_id: str | None = None,
    snapshot_type: str | None = None,
    summary: str | None = None,
) -> PatientConditionSnapshot:
    conditions = db.scalars(
        select(ChronicCondition).where(ChronicCondition.patient_id == patient.id).order_by(ChronicCondition.id.desc())
    ).all()
    prescriptions = db.scalars(
        select(Prescription).where(Prescription.patient_id == patient.id).order_by(Prescription.created_at.desc())
    ).all()
    latest_vitals = db.scalars(
        select(PatientVital).where(PatientVital.patient_id == patient.id).order_by(PatientVital.recorded_at.desc())
    ).all()[:5]

    profile_payload = _profile_response(patient, detail).model_dump()
    snapshot = PatientConditionSnapshot(
        patient_id=patient.id,
        snapshot_type=snapshot_type or source_event_type,
        summary=summary or f"Profile snapshot captured for {patient.full_name}.",
        profile_json=json.dumps(profile_payload, ensure_ascii=True),
        conditions_json=json.dumps(
            [
                {
                    "id": item.id,
                    "name": item.name,
                    "condition_type": item.condition_type,
                    "last_updated": None if item.last_updated is None else item.last_updated.isoformat(),
                    "notes": item.notes,
                }
                for item in conditions
            ],
            ensure_ascii=True,
        ),
        prescriptions_json=json.dumps(
            [
                {
                    "id": item.id,
                    "medication_name": item.medication_name,
                    "dosage": item.dosage,
                    "instructions": item.instructions,
                    "review_status": item.review_status,
                    "created_at": item.created_at.isoformat(),
                }
                for item in prescriptions
            ],
            ensure_ascii=True,
        ),
        vitals_json=json.dumps([_vital_response(item).model_dump() for item in latest_vitals], ensure_ascii=True),
        source_event_type=source_event_type,
        source_event_id=source_event_id,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def _create_manual_snapshot(
    db: Session,
    patient_id: int,
    payload: PatientConditionSnapshotCreateRequest,
) -> PatientConditionSnapshot:
    snapshot = PatientConditionSnapshot(
        patient_id=patient_id,
        snapshot_type=payload.snapshot_type,
        summary=payload.summary,
        profile_json=None if payload.profile is None else json.dumps(payload.profile, ensure_ascii=True),
        conditions_json=json.dumps(payload.conditions, ensure_ascii=True),
        prescriptions_json=json.dumps(payload.prescriptions, ensure_ascii=True),
        vitals_json=json.dumps(payload.vitals, ensure_ascii=True),
        source_event_type=payload.source_event_type,
        source_event_id=payload.source_event_id,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def _doctor_response(doctor: Doctor, mapping: PatientDoctorMap | None = None) -> DoctorResponse:
    return DoctorResponse(
        id=doctor.id,
        full_name=doctor.full_name,
        specialty=doctor.specialty,
        email=doctor.email,
        phone=doctor.phone,
        profile_image_key=doctor.profile_image_key,
        is_default=bool(mapping.is_default) if mapping is not None else False,
        relationship_type=mapping.relationship_type if mapping is not None else None,
    )


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def root() -> HTMLResponse:
    return HTMLResponse(
        """
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>nexus_ai API</title>
            <style>
              body { font-family: Arial, sans-serif; margin: 0; padding: 40px; background: #fcfaee; color: #1b1c15; }
              .card { max-width: 720px; margin: 0 auto; padding: 32px; background: white; border-radius: 24px; box-shadow: 0 12px 32px rgba(27,28,21,0.08); }
              h1 { margin-top: 0; }
              a { color: #536431; text-decoration: none; font-weight: 600; }
              ul { line-height: 1.8; }
            </style>
          </head>
          <body>
            <main class="card">
              <h1>nexus_ai API</h1>
              <p>The backend service is running on Cloud Run.</p>
              <ul>
                <li><a href="/docs">Open API docs</a></li>
                <li><a href="/health">Health check</a></li>
              </ul>
            </main>
          </body>
        </html>
        """
    )


@router.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/auth/google")
def google_auth_exchange(
    code: str = Form(...),
    db: Session = Depends(get_db),
):
    """Exchange a Google authorization code for tokens, match to a patient."""
    import google_auth_oauthlib.flow as oauthflow
    from nexus_ai.config import get_settings

    settings = get_settings()
    if not settings.google_oauth_client_id or not settings.google_oauth_client_secret:
        raise HTTPException(status_code=500, detail="OAuth client not configured on server.")

    # Build client config for web application flow
    client_config = {
        "web": {
            "client_id": settings.google_oauth_client_id,
            "client_secret": settings.google_oauth_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["postmessage"],
        }
    }
    scopes = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
    ]
    flow = oauthflow.Flow.from_client_config(client_config, scopes=scopes)
    flow.redirect_uri = "postmessage"

    try:
        flow.fetch_token(code=code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {e}")

    creds = flow.credentials
    # Extract user info from ID token
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
    try:
        id_info = id_token.verify_oauth2_token(
            creds.id_token, google_requests.Request(), settings.google_oauth_client_id
        )
        user_email = id_info.get("email", "")
        user_name = id_info.get("name", "")
    except Exception:
        user_email = ""
        user_name = ""

    # Try to match to existing patient by email, or by ID 2 as fallback
    patient = None
    if user_email:
        patient = db.scalar(select(Patient).where(Patient.google_email == user_email))
    if patient is None:
        # Fallback: assign to patient 2 (Shreesha) and set their email
        patient = db.scalar(select(Patient).where(Patient.id == 2))
        if patient is None:
            raise HTTPException(status_code=404, detail="No matching patient found.")
        patient.google_email = user_email

    # Save tokens
    patient.google_access_token = creds.token
    patient.google_refresh_token = creds.refresh_token
    patient.google_token_expiry = creds.expiry
    db.commit()

    return {
        "patient_id": patient.id,
        "name": patient.full_name,
        "email": user_email or patient.google_email,
        "google_connected": True,
    }


@router.get("/auth/google/status/{patient_id}")
def google_auth_status(patient_id: int, db: Session = Depends(get_db)):
    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    has_tokens = bool(patient.google_access_token)
    return {
        "patient_id": patient_id,
        "google_connected": has_tokens,
        "email": patient.google_email,
        "services": {
            "drive": has_tokens,
            "calendar": has_tokens,
            "gmail": has_tokens,
        },
    }


@router.get("/gmail/{patient_id}/health-emails")
def list_gmail_health_emails(patient_id: int, db: Session = Depends(get_db)):
    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    if not patient or not patient.google_access_token:
        return {"patient_id": patient_id, "emails": [], "error": "Gmail not connected."}

    from nexus_ai.services.google_workspace import credentials_from_tokens
    creds = credentials_from_tokens(
        access_token=patient.google_access_token,
        refresh_token=patient.google_refresh_token,
    )
    emails = orchestrator.integrations.list_health_emails(credentials=creds, max_results=5)
    return {"patient_id": patient_id, "emails": emails}


@router.post("/gmail/send-care-summary")
def send_gmail_care_summary(
    patient_id: int = Form(...),
    to_email: str | None = Form(None),
    doctor_id: int | None = Form(None),
    subject: str | None = Form(None),
    body_html: str | None = Form(None),
    db: Session = Depends(get_db),
):
    if not to_email and doctor_id is None:
        raise HTTPException(status_code=400, detail="Provide either to_email or doctor_id.")

    try:
        result = orchestrator.send_doctor_aware_care_email(
            db=db,
            patient_id=patient_id,
            message="Care summary requested from Gmail route.",
            doctor_id=doctor_id,
            to_email=to_email,
            subject=subject,
            body_html=body_html,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if not result.get("sent"):
        raise HTTPException(
            status_code=502,
            detail=result.get("error") or "Failed to send care summary email via Gmail."
        )

    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    detail = db.scalar(select(PatientProfileDetail).where(PatientProfileDetail.patient_id == patient_id))
    if patient is not None:
        _create_profile_snapshot(
            db=db,
            patient=patient,
            detail=detail,
            source_event_type="email_sent",
            source_event_id=None if result.get("message_id") is None else str(result["message_id"]),
        )
    return {"patient_id": patient_id, **result}


@router.get("/demo/patient/{patient_id}/workspace")
def patient_workspace(patient_id: int, db: Session = Depends(get_db)) -> dict:
    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    profile_detail = db.scalar(select(PatientProfileDetail).where(PatientProfileDetail.patient_id == patient_id))
    vitals = db.scalars(
        select(PatientVital).where(PatientVital.patient_id == patient_id).order_by(PatientVital.recorded_at.desc())
    ).all()
    snapshots = db.scalars(
        select(PatientConditionSnapshot)
        .where(PatientConditionSnapshot.patient_id == patient_id)
        .order_by(PatientConditionSnapshot.created_at.desc())
    ).all()

    conditions = db.scalars(
        select(ChronicCondition).where(ChronicCondition.patient_id == patient_id).order_by(ChronicCondition.id.desc())
    ).all()
    prescriptions = db.scalars(
        select(Prescription).where(Prescription.patient_id == patient_id).order_by(Prescription.created_at.desc())
    ).all()
    notifications = db.scalars(
        select(Notification).where(Notification.patient_id == patient_id).order_by(Notification.created_at.desc())
    ).all()
    cases = db.scalars(
        select(EscalationCase).where(EscalationCase.patient_id == patient_id).order_by(EscalationCase.created_at.desc())
    ).all()
    memories = db.scalars(
        select(MedicalMemory).where(MedicalMemory.patient_id == patient_id).order_by(MedicalMemory.created_at.desc())
    ).all()
    doctor_rows = db.execute(
        select(Doctor, PatientDoctorMap)
        .join(PatientDoctorMap, PatientDoctorMap.doctor_id == Doctor.id)
        .where(PatientDoctorMap.patient_id == patient_id)
        .order_by(PatientDoctorMap.is_default.desc(), Doctor.full_name)
    ).all()

    checkin = orchestrator.build_daily_checkin(patient_id)
    manifest = orchestrator.get_orchestration_manifest(patient_id)

    return {
        "patient": {
            "id": patient.id,
            "full_name": patient.full_name,
            "preferred_language": patient.preferred_language,
            "summary": patient.summary,
            "date_of_birth": None if patient.date_of_birth is None else patient.date_of_birth.isoformat(),
        },
        "profile": _profile_response(patient, profile_detail).model_dump(),
        "vitals": [_vital_response(item).model_dump() for item in vitals[:10]],
        "condition_snapshots": [_snapshot_response(item).model_dump() for item in snapshots[:12]],
        "conditions": [
            {
                "id": item.id,
                "name": item.name,
                "condition_type": item.condition_type,
                "last_updated": None if item.last_updated is None else item.last_updated.isoformat(),
                "notes": item.notes,
            }
            for item in conditions
        ],
        "prescriptions": [
            {
                "id": item.id,
                "medication_name": item.medication_name,
                "dosage": item.dosage,
                "instructions": item.instructions,
                "review_status": item.review_status,
                "confidence_score": item.confidence_score,
                "document_drive_file_url": item.document_drive_file_url,
                "created_at": item.created_at.isoformat(),
            }
            for item in prescriptions
        ],
        "notifications": [
            {
                "id": item.id,
                "channel": item.channel,
                "message_type": item.message_type,
                "body": item.body,
                "delivery_status": item.delivery_status,
                "created_at": item.created_at.isoformat(),
            }
            for item in notifications
        ],
        "cases": [
            {
                "id": item.id,
                "case_type": item.case_type,
                "status": item.status,
                "summary": item.summary,
                "doctor_id": item.doctor_id,
                "doctor_name": item.doctor_name,
                "doctor_email": item.doctor_email,
                "urgency": item.urgency,
                "external_ticket_id": item.external_ticket_id,
                "external_ticket_url": item.external_ticket_url,
                "drive_file_url": item.drive_file_url,
                "calendar_event_url": item.calendar_event_url,
                "pharmacy_search_summary": item.pharmacy_search_summary,
                "created_at": item.created_at.isoformat(),
            }
            for item in cases
        ],
        "memories": [
            {
                "id": item.id,
                "source_type": item.source_type,
                "modality": item.modality,
                "embedding_model": item.embedding_model,
                "summary_text": item.summary_text,
                "drive_file_url": item.drive_file_url,
                "created_at": item.created_at.isoformat(),
            }
            for item in memories
        ],
        "doctors": [
            _doctor_response(doctor, mapping).model_dump()
            for doctor, mapping in doctor_rows
        ],
        "checkin": checkin,
        "manifest": manifest,
    }


@router.get("/doctors", response_model=list[DoctorResponse])
def list_doctors(patient_id: int | None = None, db: Session = Depends(get_db)) -> list[DoctorResponse]:
    if patient_id is None:
        doctors = db.scalars(select(Doctor).order_by(Doctor.full_name)).all()
        return [_doctor_response(doctor) for doctor in doctors]

    rows = db.execute(
        select(Doctor, PatientDoctorMap)
        .join(PatientDoctorMap, PatientDoctorMap.doctor_id == Doctor.id)
        .where(PatientDoctorMap.patient_id == patient_id)
        .order_by(PatientDoctorMap.is_default.desc(), Doctor.full_name)
    ).all()
    return [_doctor_response(doctor, mapping) for doctor, mapping in rows]


@router.get("/patients/{patient_id}/profile", response_model=PatientProfileResponse)
def get_patient_profile(patient_id: int, db: Session = Depends(get_db)) -> PatientProfileResponse:
    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found.")
    detail = db.scalar(select(PatientProfileDetail).where(PatientProfileDetail.patient_id == patient_id))
    return _profile_response(patient, detail)


@router.post("/patients/{patient_id}/condition-snapshots", response_model=PatientConditionSnapshotResponse)
def create_patient_condition_snapshot(
    patient_id: int,
    payload: PatientConditionSnapshotCreateRequest,
    db: Session = Depends(get_db),
) -> PatientConditionSnapshotResponse:
    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found.")
    snapshot = _create_manual_snapshot(db=db, patient_id=patient_id, payload=payload)
    return _snapshot_response(snapshot)


@router.get("/patients/{patient_id}/condition-snapshots", response_model=list[PatientConditionSnapshotResponse])
def list_patient_condition_snapshots(
    patient_id: int,
    db: Session = Depends(get_db),
) -> list[PatientConditionSnapshotResponse]:
    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found.")
    snapshots = db.scalars(
        select(PatientConditionSnapshot)
        .where(PatientConditionSnapshot.patient_id == patient_id)
        .order_by(PatientConditionSnapshot.created_at.desc())
    ).all()
    return [_snapshot_response(item) for item in snapshots]


@router.post("/patients/{patient_id}/history/query", response_model=list[PatientConditionSnapshotResponse])
def query_patient_history(
    patient_id: int,
    payload: PatientHistoryQueryRequest,
    db: Session = Depends(get_db),
) -> list[PatientConditionSnapshotResponse]:
    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found.")
    query_text = payload.query_text.lower().strip()
    snapshots = db.scalars(
        select(PatientConditionSnapshot)
        .where(PatientConditionSnapshot.patient_id == patient_id)
        .order_by(PatientConditionSnapshot.created_at.desc())
    ).all()
    if not query_text:
        return [_snapshot_response(item) for item in snapshots]

    matches: list[PatientConditionSnapshotResponse] = []
    for item in snapshots:
        haystack = " ".join(
            part
            for part in [
                item.summary,
                item.snapshot_type,
                item.source_event_type or "",
                item.profile_json or "",
                item.conditions_json or "",
                item.prescriptions_json or "",
                item.vitals_json or "",
            ]
            if part
        ).lower()
        if query_text in haystack:
            matches.append(_snapshot_response(item))
    return matches


@router.patch("/patients/{patient_id}/profile", response_model=PatientProfileResponse)
def update_patient_profile(
    patient_id: int,
    payload: PatientProfileUpdateRequest,
    db: Session = Depends(get_db),
) -> PatientProfileResponse:
    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found.")

    detail = db.scalar(select(PatientProfileDetail).where(PatientProfileDetail.patient_id == patient_id))
    if detail is None:
        detail = PatientProfileDetail(patient_id=patient_id)
        db.add(detail)

    updates = payload.model_dump(exclude_unset=True)
    if "full_name" in updates:
        patient.full_name = updates["full_name"] or patient.full_name
    if "preferred_language" in updates:
        patient.preferred_language = updates["preferred_language"] or patient.preferred_language
    if "date_of_birth" in updates:
        patient.date_of_birth = updates["date_of_birth"]
    if "summary" in updates:
        patient.summary = updates["summary"]

    if "height_cm" in updates:
        detail.height_cm = updates["height_cm"]
    if "weight_kg" in updates:
        detail.weight_kg = updates["weight_kg"]
    if "blood_group" in updates:
        detail.blood_group = updates["blood_group"]
    if "allergies" in updates:
        detail.allergies_json = json.dumps(updates["allergies"] or [], ensure_ascii=True)
    if "emergency_contact_name" in updates:
        detail.emergency_contact_name = updates["emergency_contact_name"]
    if "emergency_contact_phone" in updates:
        detail.emergency_contact_phone = updates["emergency_contact_phone"]
    if "primary_language" in updates:
        detail.primary_language = updates["primary_language"]
    if "notes" in updates:
        detail.notes = updates["notes"]

    db.commit()
    db.refresh(patient)
    db.refresh(detail)
    _create_profile_snapshot(db=db, patient=patient, detail=detail, source_event_type="profile_update")
    return _profile_response(patient, detail)


@router.post("/patients/{patient_id}/vitals", response_model=PatientVitalResponse)
def create_patient_vital(
    patient_id: int,
    payload: PatientVitalCreateRequest,
    db: Session = Depends(get_db),
) -> PatientVitalResponse:
    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found.")

    vital = PatientVital(
        patient_id=patient_id,
        blood_pressure=payload.blood_pressure,
        heart_rate_bpm=payload.heart_rate_bpm,
        blood_glucose_mg_dl=payload.blood_glucose_mg_dl,
        temperature_c=payload.temperature_c,
        weight_kg=payload.weight_kg,
        source=payload.source,
    )
    db.add(vital)
    db.commit()
    db.refresh(vital)
    detail = db.scalar(select(PatientProfileDetail).where(PatientProfileDetail.patient_id == patient_id))
    _create_profile_snapshot(
        db=db,
        patient=patient,
        detail=detail,
        source_event_type="vital_added",
        source_event_id=str(vital.id),
    )
    return _vital_response(vital)


def _resolve_doctor_for_patient(
    db: Session,
    patient_id: int,
    doctor_id: int | None = None,
) -> Doctor | None:
    if doctor_id is not None:
        return db.scalar(
            select(Doctor)
            .join(PatientDoctorMap, PatientDoctorMap.doctor_id == Doctor.id)
            .where(
                Doctor.id == doctor_id,
                PatientDoctorMap.patient_id == patient_id,
            )
        )

    mapping = db.scalar(
        select(PatientDoctorMap)
        .where(PatientDoctorMap.patient_id == patient_id)
        .order_by(PatientDoctorMap.is_default.desc(), PatientDoctorMap.created_at.asc())
    )
    if mapping is None:
        return None
    return db.scalar(select(Doctor).where(Doctor.id == mapping.doctor_id))


def _vision_suggested_actions(category: str, diet_relevant: bool) -> list[VisionSuggestedAction]:
    actions = [
        VisionSuggestedAction(
            action_id="ask_follow_up",
            label="Ask follow-up",
            description="Turn this upload into a guided follow-up question through the assistant.",
        ),
        VisionSuggestedAction(
            action_id="send_doctor_handoff",
            label="Send doctor handoff",
            description="Escalate the result to the mapped doctor with the current care context.",
        ),
        VisionSuggestedAction(
            action_id="chat_with_doctor",
            label="Chat with doctor",
            description="Use this upload as context for the next doctor-facing conversation step.",
        ),
    ]
    if category == "PRESCRIPTION":
        actions.append(
            VisionSuggestedAction(
                action_id="review_medication",
                label="Review medication",
                description="Use the extracted prescription details in Medication Hub.",
            )
        )
    elif diet_relevant:
        actions.append(
            VisionSuggestedAction(
                action_id="review_diet_support",
                label="Review diet support",
                description="Open medication-aware food guidance linked to this upload.",
            )
        )
    return actions

@router.get("/patients/{patient_id}/vitals", response_model=list[PatientVitalResponse])
def list_patient_vitals(patient_id: int, db: Session = Depends(get_db)) -> list[PatientVitalResponse]:
    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found.")
    vitals = db.scalars(
        select(PatientVital).where(PatientVital.patient_id == patient_id).order_by(PatientVital.recorded_at.desc())
    ).all()
    return [_vital_response(item) for item in vitals]


@router.post("/doctors", response_model=DoctorResponse)
def create_doctor(payload: DoctorCreateRequest, db: Session = Depends(get_db)) -> DoctorResponse:
    doctor = Doctor(
        full_name=payload.full_name,
        specialty=payload.specialty,
        email=payload.email,
        phone=payload.phone,
        profile_image_key=payload.profile_image_key,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return _doctor_response(doctor)


@router.post("/patients/{patient_id}/doctor-map", response_model=DoctorResponse)
def create_patient_doctor_map(
    patient_id: int,
    payload: PatientDoctorMapRequest,
    db: Session = Depends(get_db),
) -> DoctorResponse:
    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found.")
    doctor = db.scalar(select(Doctor).where(Doctor.id == payload.doctor_id))
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found.")

    if payload.is_default:
        existing_defaults = db.scalars(
            select(PatientDoctorMap).where(
                PatientDoctorMap.patient_id == patient_id,
                PatientDoctorMap.is_default.is_(True),
            )
        ).all()
        for item in existing_defaults:
            item.is_default = False

    mapping = db.scalar(
        select(PatientDoctorMap).where(
            PatientDoctorMap.patient_id == patient_id,
            PatientDoctorMap.doctor_id == payload.doctor_id,
        )
    )
    if mapping is None:
        mapping = PatientDoctorMap(patient_id=patient_id, doctor_id=payload.doctor_id)
        db.add(mapping)

    mapping.relationship_type = payload.relationship_type
    mapping.is_default = payload.is_default
    mapping.notes = payload.notes
    db.commit()
    db.refresh(mapping)
    return _doctor_response(doctor, mapping)


@router.get("/doctor-workspace/{doctor_id}/tasks", response_model=list[RoutineTaskResponse])
def doctor_workspace_tasks(doctor_id: int, db: Session = Depends(get_db)) -> list[RoutineTaskResponse]:
    doctor = db.scalar(select(Doctor).where(Doctor.id == doctor_id))
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found.")
    # Tasks functionality has been simplified and removed external dependencies
    tasks = []
    return [RoutineTaskResponse(**task.__dict__) for task in tasks]


@router.get("/patients/{patient_id}/pending-actions", response_model=list[PendingActionResponse])
def list_pending_actions(patient_id: int, db: Session = Depends(get_db)) -> list[PendingActionResponse]:
    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found.")
    actions = orchestrator.list_pending_actions(db=db, patient_id=patient_id)
    return [PendingActionResponse(**item) for item in actions]


@router.post("/patient/intake", response_model=PatientIntakeResponse)
def patient_intake(payload: PatientIntakeRequest, db: Session = Depends(get_db)) -> PatientIntakeResponse:
    patient = orchestrator.intake.intake_patient(db, payload)
    return PatientIntakeResponse(patient_id=patient.id, summary=patient.summary or "")


@router.post("/prescription/scan", response_model=PrescriptionScanResponse)
def prescription_scan(payload: PrescriptionScanRequest, db: Session = Depends(get_db)) -> PrescriptionScanResponse:
    prescription = orchestrator.intake.scan_prescription(
        db=db,
        patient_id=payload.patient_id,
        image_reference=payload.image_reference,
        raw_text_hint=payload.raw_text_hint,
    )
    patient = db.scalar(select(Patient).where(Patient.id == payload.patient_id))
    detail = db.scalar(select(PatientProfileDetail).where(PatientProfileDetail.patient_id == payload.patient_id))
    if patient is not None:
        _create_profile_snapshot(
            db=db,
            patient=patient,
            detail=detail,
            source_event_type="prescription_upload",
            source_event_id=str(prescription.id),
        )
    return PrescriptionScanResponse(
        prescription_id=prescription.id,
        medication_name=prescription.medication_name,
        dosage=prescription.dosage,
        instructions=prescription.instructions,
        confidence_score=prescription.confidence_score,
        review_status=prescription.review_status,
    )


@router.post("/patient/check-alternatives", response_model=CheckAlternativesResponse)
def check_alternatives(payload: CheckAlternativesRequest) -> CheckAlternativesResponse:
    candidates, escalation_required, safety_summary = orchestrator.evaluate_alternatives(
        patient_id=payload.patient_id,
        unavailable_medication=payload.unavailable_medication,
    )
    return CheckAlternativesResponse(
        patient_id=payload.patient_id,
        candidates=candidates,
        escalation_required=escalation_required,
        safety_summary=safety_summary,
    )


@router.post("/patient/escalate", response_model=EscalateResponse)
def escalate(payload: EscalateRequest, db: Session = Depends(get_db)) -> EscalateResponse:
    case = orchestrator.hitl.create_case(
        db,
        payload.patient_id,
        payload.case_type,
        payload.summary,
        doctor_id=payload.doctor_id,
        urgency=payload.urgency,
    )
    drive_result = None
    if payload.document_file_path:
        drive_result = orchestrator.integrations.upload_document(
            db=db,
            patient_id=payload.patient_id,
            file_path=payload.document_file_path,
            mime_type="application/pdf" if payload.document_file_path.lower().endswith(".pdf") else "application/octet-stream",
        )
        case.drive_file_id = drive_result.get("id")
        case.drive_file_url = drive_result.get("webViewLink")
        case.drive_path = drive_result.get("drive_path")

    calendar_result = None
    if payload.create_calendar_event:
        calendar_result = orchestrator.integrations.create_calendar_event(
            db=db,
            patient_id=payload.patient_id,
            summary=payload.calendar_summary or f"nexus_ai follow-up for patient {payload.patient_id}",
            minutes_from_now=payload.calendar_minutes_from_now,
            duration_minutes=payload.calendar_duration_minutes,
            escalation_case_id=case.id,
        )

    pharmacy_result = None
    if payload.pharmacy_location_query:
        pharmacy_result = orchestrator.integrations.search_nearby_pharmacies(payload.pharmacy_location_query)
        pharmacy_names = [item["name"] for item in pharmacy_result.get("pharmacies", [])[:3] if item.get("name")]
        case.pharmacy_search_summary = ", ".join(pharmacy_names) if pharmacy_names else "No pharmacies found"

    db.add(case)
    db.commit()
    db.refresh(case)
    patient = db.scalar(select(Patient).where(Patient.id == payload.patient_id))
    detail = db.scalar(select(PatientProfileDetail).where(PatientProfileDetail.patient_id == payload.patient_id))
    if patient is not None:
        _create_profile_snapshot(
            db=db,
            patient=patient,
            detail=detail,
            source_event_type="doctor_handoff",
            source_event_id=str(case.id),
        )

    orchestrator.integrations.log_integration_event(
        "escalation_case_created",
        {
            "case_id": case.id,
            "patient_id": payload.patient_id,
            "external_ticket_id": case.external_ticket_id,
            "drive_file_id": case.drive_file_id,
            "calendar_event_id": case.calendar_event_id,
            "pharmacy_search_summary": case.pharmacy_search_summary,
        },
    )

    return EscalateResponse(
        case_id=case.id,
        external_ticket_id=case.external_ticket_id,
        status=case.status,
        external_ticket_url=case.external_ticket_url,
        doctor_id=case.doctor_id,
        doctor_name=case.doctor_name,
        doctor_email=case.doctor_email,
        urgency=case.urgency,
        drive_file_id=case.drive_file_id,
        drive_file_url=case.drive_file_url,
        calendar_event_id=case.calendar_event_id,
        calendar_event_url=case.calendar_event_url,
        pharmacy_search_summary=case.pharmacy_search_summary,
    )


@router.post("/patient/notify", response_model=NotifyResponse)
def notify(payload: NotifyRequest, db: Session = Depends(get_db)) -> NotifyResponse:
    notification = orchestrator.communications.notify(
        db,
        patient_id=payload.patient_id,
        channel=payload.channel,
        message_type=payload.message_type,
        message_body=payload.message_body,
    )
    return NotifyResponse(notification_id=notification.id, delivery_status=notification.delivery_status)


@router.get("/cases/{case_id}", response_model=CaseResponse)
def get_case(case_id: int, db: Session = Depends(get_db)) -> CaseResponse:
    case = db.scalar(select(EscalationCase).where(EscalationCase.id == case_id))
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return CaseResponse(
        case_id=case.id,
        patient_id=case.patient_id,
        case_type=case.case_type,
        status=case.status,
        summary=case.summary,
        doctor_id=case.doctor_id,
        doctor_name=case.doctor_name,
        doctor_email=case.doctor_email,
        urgency=case.urgency,
        external_ticket_id=case.external_ticket_id,
        external_ticket_url=case.external_ticket_url,
        drive_file_id=case.drive_file_id,
        drive_file_url=case.drive_file_url,
        calendar_event_id=case.calendar_event_id,
        calendar_event_url=case.calendar_event_url,
        pharmacy_search_summary=case.pharmacy_search_summary,
    )


@router.post("/documents/upload", response_model=DriveUploadResponse)
def upload_document(payload: DriveUploadRequest, db: Session = Depends(get_db)) -> DriveUploadResponse:
    result = orchestrator.integrations.upload_document(
        db=db,
        patient_id=payload.patient_id,
        file_path=payload.file_path,
        mime_type=payload.mime_type,
        prescription_id=payload.prescription_id,
        doctor_name=payload.doctor_name,
        patient_name=payload.patient_name,
        document_type=payload.document_type,
        disease_name=payload.disease_name,
        capture_date=payload.capture_date,
        image_category=payload.image_category,
    )
    return DriveUploadResponse(
        patient_id=payload.patient_id,
        file_id=result["id"],
        file_name=result["name"],
        web_view_link=result.get("webViewLink"),
        prescription_id=payload.prescription_id,
        image_category=result.get("image_category"),
        doctor_name=result.get("doctor_name"),
        patient_name=result.get("patient_name"),
        document_type=result.get("document_type"),
        disease_name=result.get("disease_name"),
        capture_date=result.get("capture_date"),
        drive_path=result.get("drive_path"),
    )


@router.post("/documents/upload-file", response_model=DriveUploadResponse)
def upload_document_file(
    patient_id: int = Form(...),
    file: UploadFile = File(...),
    prescription_id: int | None = Form(None),
    doctor_name: str | None = Form(None),
    patient_name: str | None = Form(None),
    document_type: str | None = Form(None),
    disease_name: str | None = Form(None),
    capture_date: str | None = Form(None),
    image_category: str | None = Form(None),
    db: Session = Depends(get_db),
) -> DriveUploadResponse:
    import tempfile, os
    suffix = os.path.splitext(file.filename or "upload")[1] or ""
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    try:
        result = orchestrator.integrations.upload_document(
            db=db,
            patient_id=patient_id,
            file_path=tmp_path,
            mime_type=file.content_type or "application/octet-stream",
            prescription_id=prescription_id,
            doctor_name=doctor_name,
            patient_name=patient_name,
            document_type=document_type,
            disease_name=disease_name,
            capture_date=capture_date,
            image_category=image_category,
        )
    finally:
        os.unlink(tmp_path)

    return DriveUploadResponse(
        patient_id=patient_id,
        file_id=result["id"],
        file_name=result["name"],
        web_view_link=result.get("webViewLink"),
        prescription_id=prescription_id,
        image_category=result.get("image_category"),
        doctor_name=result.get("doctor_name"),
        patient_name=result.get("patient_name"),
        document_type=result.get("document_type"),
        disease_name=result.get("disease_name"),
        capture_date=result.get("capture_date"),
        drive_path=result.get("drive_path"),
    )


@router.post("/vision/upload-analyze", response_model=VisionUploadAnalyzeResponse)
def vision_upload_analyze(
    patient_id: int = Form(...),
    file: UploadFile = File(...),
    doctor_id: int | None = Form(None),
    disease_name: str | None = Form(None),
    capture_date: str | None = Form(None),
    create_handoff: bool = Form(False),
    db: Session = Depends(get_db),
) -> VisionUploadAnalyzeResponse:
    import os
    import tempfile

    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found.")

    detail = db.scalar(select(PatientProfileDetail).where(PatientProfileDetail.patient_id == patient_id))
    doctor = _resolve_doctor_for_patient(db=db, patient_id=patient_id, doctor_id=doctor_id)

    original_name = file.filename or "medical-upload"
    suffix = os.path.splitext(original_name)[1] or ""
    image_bytes = file.file.read()
    mime_type = file.content_type or "application/octet-stream"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        analysis = _gemini_vision.auto_analyze_image(
            image_bytes=image_bytes,
            mime_type=mime_type,
            file_path=tmp_path,
        )
        category = str(analysis.get("category", "OTHER")).upper()
        upload_result = orchestrator.integrations.upload_document(
            db=db,
            patient_id=patient_id,
            file_path=tmp_path,
            mime_type=mime_type,
            doctor_name=None if doctor is None else doctor.full_name,
            patient_name=patient.full_name,
            disease_name=disease_name or patient.summary or "general-condition",
            capture_date=capture_date,
            image_category=category,
        )
    finally:
        os.unlink(tmp_path)

    diagnostic_image_base64 = None
    if category == "SYMPTOM":
        diagnostic_image_base64 = _gemini_vision.generate_diagnostic_image(
            image_bytes=image_bytes,
            mime_type=mime_type,
            analysis=analysis,
        )

    prescription = None
    if category == "PRESCRIPTION":
        raw_text_hint = "\n".join(
            [
                item
                for item in [
                    str(analysis.get("summary") or "").strip(),
                    *[str(entry).strip() for entry in analysis.get("findings", []) if str(entry).strip()],
                ]
                if item
            ]
        )
        prescription = orchestrator.intake.scan_prescription(
            db=db,
            patient_id=patient_id,
            image_reference=upload_result.get("webViewLink") or upload_result.get("name") or original_name,
            raw_text_hint=raw_text_hint or None,
        )
        prescription.document_drive_file_id = upload_result.get("id")
        prescription.document_drive_file_url = upload_result.get("webViewLink")
        prescription.drive_path = upload_result.get("drive_path")
        db.add(prescription)
        db.commit()
        db.refresh(prescription)

    created_case_id = None
    snapshot_event_type = "vision_upload"
    snapshot_event_id = str(upload_result.get("id") or upload_result.get("name") or original_name)
    if create_handoff:
        case = orchestrator.hitl.create_case(
            db,
            patient_id,
            "doctor_review",
            (
                f"Vision upload review requested for {patient.full_name}. "
                f"Category: {category}. Summary: {analysis.get('summary') or 'No summary available.'}"
            ),
            doctor_id=None if doctor is None else doctor.id,
            urgency="high" if category in {"PRESCRIPTION", "SYMPTOM"} else "medium",
        )
        created_case_id = case.id
        snapshot_event_type = "vision_handoff"
        snapshot_event_id = str(case.id)

    snapshot = _create_profile_snapshot(
        db=db,
        patient=patient,
        detail=detail,
        source_event_type=snapshot_event_type,
        source_event_id=snapshot_event_id,
        snapshot_type="vision_upload",
        summary=(
            f"{original_name} analyzed as {category.lower()}. "
            f"{analysis.get('summary') or 'Vision workflow completed.'}"
        ),
    )

    drive_upload = DriveUploadResponse(
        patient_id=patient_id,
        file_id=upload_result["id"],
        file_name=upload_result["name"],
        web_view_link=upload_result.get("webViewLink"),
        prescription_id=None if prescription is None else prescription.id,
        image_category=upload_result.get("image_category"),
        doctor_name=upload_result.get("doctor_name"),
        patient_name=upload_result.get("patient_name"),
        document_type=upload_result.get("document_type"),
        disease_name=upload_result.get("disease_name"),
        capture_date=upload_result.get("capture_date"),
        drive_path=upload_result.get("drive_path"),
    )

    detected_type = analysis.get("detected_type")
    if detected_type is None:
        detected_type = category.lower()

    return VisionUploadAnalyzeResponse(
        patient_id=patient_id,
        category=category,
        analysis_type=str(analysis.get("analysis_type", "auto")),
        detected_type=str(detected_type),
        medication_name=analysis.get("medication_name") or (None if prescription is None else prescription.medication_name),
        dosage=analysis.get("dosage") or (None if prescription is None else prescription.dosage),
        instructions=analysis.get("instructions") or (None if prescription is None else prescription.instructions),
        severity=analysis.get("severity"),
        confidence=int(analysis.get("confidence", 0)),
        findings=[str(item) for item in analysis.get("findings", [])],
        summary=str(analysis.get("summary") or "Vision upload processed."),
        diet_relevant=bool(analysis.get("diet_relevant", False)),
        model_used=_gemini_vision._analysis_model_id,
        diagnostic_image_base64=diagnostic_image_base64,
        drive_upload=drive_upload,
        prescription_id=None if prescription is None else prescription.id,
        snapshot_id=snapshot.id,
        created_case_id=created_case_id,
        suggested_actions=_vision_suggested_actions(
            category=category,
            diet_relevant=bool(analysis.get("diet_relevant", False)),
        ),
    )


@router.post("/calendar/events", response_model=CalendarEventResponse)
def create_calendar_event(payload: CalendarEventRequest, db: Session = Depends(get_db)) -> CalendarEventResponse:
    result = orchestrator.integrations.create_calendar_event(
        db=db,
        patient_id=payload.patient_id,
        summary=payload.summary,
        minutes_from_now=payload.minutes_from_now,
        duration_minutes=payload.duration_minutes,
        escalation_case_id=payload.escalation_case_id,
    )
    return CalendarEventResponse(
        patient_id=payload.patient_id,
        event_id=result["id"],
        html_link=result.get("htmlLink"),
        escalation_case_id=payload.escalation_case_id,
    )


@router.post("/drug/label", response_model=DrugLabelResponse)
def lookup_drug_label(payload: DrugLabelRequest) -> DrugLabelResponse:
    result = orchestrator.integrations.lookup_drug_label(payload.medication_name)
    return DrugLabelResponse(**result)


@router.post("/medicine/grounded-answer", response_model=MedicineGroundedAnswerResponse)
def medicine_grounded_answer(payload: MedicineGroundedAnswerRequest) -> MedicineGroundedAnswerResponse:
    result = orchestrator.get_medicine_grounded_answer(
        patient_id=payload.patient_id,
        medication_name=payload.medication_name,
    )
    return MedicineGroundedAnswerResponse(**result)


@router.post("/pharmacy/search", response_model=PharmacySearchResponse)
def pharmacy_search(payload: PharmacySearchRequest) -> PharmacySearchResponse:
    result = orchestrator.integrations.search_nearby_pharmacies(payload.location_query)
    return PharmacySearchResponse(**result)


@router.post("/caremaze/nearby-care-destinations", response_model=CareDestinationSearchResponse)
def nearby_care_destinations(
    payload: CareDestinationSearchRequest,
    db: Session = Depends(get_db),
) -> CareDestinationSearchResponse:
    patient = db.scalar(select(Patient).where(Patient.id == payload.patient_id))
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found.")

    primary_condition = db.scalar(
        select(ChronicCondition)
        .where(ChronicCondition.patient_id == payload.patient_id)
        .order_by(ChronicCondition.id.asc())
    )
    result = orchestrator.integrations.search_nearby_care_destinations(
        destination_type=payload.destination_type,
        location_query=payload.location_query,
        latitude=payload.latitude,
        longitude=payload.longitude,
        medication_name=payload.medication_name,
        condition_name=payload.condition_name or (None if primary_condition is None else primary_condition.name),
    )
    return CareDestinationSearchResponse(
        patient_id=payload.patient_id,
        searched_location=result["searched_location"],
        destination_type=result["destination_type"],
        source_used=result["source_used"],
        summary=result["summary"],
        destinations=[CareDestinationResponse(**item) for item in result["destinations"]],
    )


@router.post("/caremaze/map-route", response_model=CareMapRouteResponse)
def caremaze_map_route(
    payload: CareMapRouteRequest,
    db: Session = Depends(get_db),
) -> CareMapRouteResponse:
    patient = db.scalar(select(Patient).where(Patient.id == payload.patient_id))
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found.")

    primary_condition = db.scalar(
        select(ChronicCondition)
        .where(ChronicCondition.patient_id == payload.patient_id)
        .order_by(ChronicCondition.id.asc())
    )
    result = orchestrator.integrations.build_care_route(
        destination_name=payload.destination_name,
        destination_type=payload.destination_type,
        location_query=payload.location_query,
        latitude=payload.latitude,
        longitude=payload.longitude,
        destination_address=payload.destination_address,
        medication_name=payload.medication_name,
        condition_name=payload.condition_name or (None if primary_condition is None else primary_condition.name),
    )
    return CareMapRouteResponse(patient_id=payload.patient_id, **result)


@router.get("/orchestration/check-in/{patient_id}", response_model=DailyCheckInResponse)
def orchestration_checkin(patient_id: int) -> DailyCheckInResponse:
    result = orchestrator.build_daily_checkin(patient_id)
    return DailyCheckInResponse(
        patient_id=patient_id,
        profile=result["profile"],
        conditions=result["conditions"],
        routine_tasks=result["routine_tasks"],
        message=result["message"],
    )


@router.get("/orchestration/routine/{patient_id}", response_model=RoutineSnapshotResponse)
def orchestration_routine(patient_id: int) -> RoutineSnapshotResponse:
    _ = patient_id
    tasks = orchestrator.routine.get_daily_routine()
    return RoutineSnapshotResponse(patient_id=patient_id, tasks=[task.__dict__ for task in tasks])


@router.post("/orchestration/hitl-report", response_model=HitlReportResponse)
def orchestration_hitl_report(payload: HitlReportRequest, db: Session = Depends(get_db)) -> HitlReportResponse:
    report = orchestrator.hitl.build_detailed_report(db, payload.patient_id, payload.context_summary)
    case_id = None
    external_ticket_id = None
    external_ticket_url = None
    if payload.create_case:
        case = orchestrator.hitl.create_case(
            db,
            payload.patient_id,
            payload.case_type,
            report,
            doctor_id=payload.doctor_id,
            urgency=payload.urgency,
        )
        case_id = case.id
        external_ticket_id = case.external_ticket_id
        external_ticket_url = case.external_ticket_url

    return HitlReportResponse(
        patient_id=payload.patient_id,
        report=report,
        case_id=case_id,
        external_ticket_id=external_ticket_id,
        external_ticket_url=external_ticket_url,
    )


@router.post("/orchestration/hitl-comprehension")
def orchestration_hitl_comprehension(payload: HitlReportRequest, db: Session = Depends(get_db)):
    result = orchestrator.hitl.build_ai_comprehension(db, payload.patient_id)
    return {"patient_id": payload.patient_id, **result}


@router.post("/patient/reminders")
def save_reminder(
    patient_id: int = Form(...),
    medication_name: str = Form(...),
    reminder_time: str = Form(...),
    db: Session = Depends(get_db),
):
    """Store a medication reminder. Using MedicationEvent as lightweight storage."""
    from nexus_ai.db.models import MedicationEvent
    event = MedicationEvent(
        patient_id=patient_id,
        event_type="reminder_set",
        medication_name=medication_name,
        details=reminder_time,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return {
        "id": event.id,
        "patient_id": patient_id,
        "medication_name": medication_name,
        "reminder_time": reminder_time,
        "status": "saved",
    }


@router.get("/patient/{patient_id}/reminders")
def get_reminders(patient_id: int, db: Session = Depends(get_db)):
    from nexus_ai.db.models import MedicationEvent
    events = db.scalars(
        select(MedicationEvent)
        .where(MedicationEvent.patient_id == patient_id, MedicationEvent.event_type == "reminder_set")
        .order_by(MedicationEvent.created_at.desc())
    ).all()
    return {
        "patient_id": patient_id,
        "reminders": [
            {
                "id": e.id,
                "medication_name": e.medication_name,
                "reminder_time": e.details,
                "created_at": str(e.created_at),
            }
            for e in events
        ],
    }


@router.post("/orchestration/diet-support", response_model=DietSupportResponse)
def orchestration_diet_support(payload: DietSupportRequest) -> DietSupportResponse:
    result = orchestrator.build_diet_and_pharmacy_support(
        patient_id=payload.patient_id,
        medication_name=payload.medication_name,
        location_query=payload.location_query,
    )
    return DietSupportResponse(
        patient_id=payload.patient_id,
        conditions=result["conditions"],
        diet_plan=result["diet_plan"],
        pharmacy_result=result["pharmacy_result"],
    )


@router.get("/diet/recipes")
def list_diet_recipes(
    patient_id: int = 2,
    medication_name: str | None = None,
    meal_type: str | None = None,
) -> dict:
    result = orchestrator.list_diet_recipes(
        patient_id=patient_id,
        medication_name=medication_name,
        meal_type=meal_type,
    )
    return {
        "patient_id": result["patient_id"],
        "conditions": result["conditions"],
        "recipes": result["recipes"],
    }


@router.post("/diet/recipes/generate", response_model=GenerateDietRecipesResponse)
def generate_diet_recipes(payload: GenerateDietRecipesRequest) -> GenerateDietRecipesResponse:
    result = orchestrator.generate_diet_recipes(payload.model_dump())
    return GenerateDietRecipesResponse(**result)


@router.get("/diet/recipes/recent", response_model=SavedDietRecipesResponse)
def list_recent_saved_recipes(patient_id: int, db: Session = Depends(get_db)) -> SavedDietRecipesResponse:
    """
    Return the most recently saved diet recipes for a patient.

    This is used by the Medication Hub "recent recipes" UI.
    """
    # Get saved IDs (most recent first)
    saved_rows = db.execute(
        select(SavedDietRecipe)
        .where(SavedDietRecipe.patient_id == patient_id)
        .order_by(SavedDietRecipe.created_at.desc())
        .limit(12)
    ).scalars().all()

    saved_ids = [row.recipe_id for row in saved_rows]
    if not saved_ids:
        return SavedDietRecipesResponse(patient_id=patient_id, recipes=[])

    # Hydrate recipes using existing curated list.
    # NOTE: Saved recipes are curated/generated IDs; for now we hydrate from curated store only.
    all_recipes = orchestrator.list_diet_recipes(patient_id=patient_id).get("recipes", [])
    by_id = {str(item.get("recipe_id")): item for item in all_recipes if isinstance(item, dict)}
    hydrated = [by_id[rid] for rid in saved_ids if rid in by_id]
    return SavedDietRecipesResponse(patient_id=patient_id, recipes=hydrated)


@router.post("/diet/recipes/{recipe_id}/save", response_model=SaveDietRecipeResponse)
def save_diet_recipe(recipe_id: str, patient_id: int, db: Session = Depends(get_db)) -> SaveDietRecipeResponse:
    """
    Persist a saved recipe ID for "recent recipes".
    """
    existing = db.scalar(
        select(SavedDietRecipe).where(
            SavedDietRecipe.patient_id == patient_id,
            SavedDietRecipe.recipe_id == recipe_id,
        )
    )
    if existing is None:
        db.add(SavedDietRecipe(patient_id=patient_id, recipe_id=recipe_id))
        db.commit()
    return SaveDietRecipeResponse(patient_id=patient_id, recipe_id=recipe_id, saved=True)


@router.post("/diet/recipes/{recipe_id}/scale", response_model=ScaleDietRecipeResponse)
def scale_diet_recipe(
    recipe_id: str,
    payload: ScaleDietRecipeRequest,
    patient_id: int,
    medication_name: str | None = None,
) -> ScaleDietRecipeResponse:
    recipe = orchestrator.scale_diet_recipe(
        patient_id=patient_id,
        recipe_id=recipe_id,
        servings=payload.servings,
        medication_name=medication_name,
    )
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return ScaleDietRecipeResponse(recipe=recipe)


@router.get("/diet/recipes/{recipe_id}/tutorials", response_model=DietRecipeTutorialResponse)
def get_recipe_tutorials(recipe_id: str) -> DietRecipeTutorialResponse:
    """Fetch a real YouTube tutorial for a given recipe using the YouTube Data API v3."""
    import httpx
    from nexus_ai.config import get_settings

    search_query = recipe_id.replace("_", " ").replace("-", " ").title() + " recipe"
    fallback_url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"

    settings = get_settings()
    api_key = settings.google_api_key
    if not api_key:
        return DietRecipeTutorialResponse(
            recipe_id=recipe_id,
            search_query=search_query,
            youtube_url=fallback_url,
        )

    try:
        resp = httpx.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "q": search_query,
                "type": "video",
                "maxResults": 1,
                "key": api_key,
            },
            timeout=8,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if items:
            video_id = items[0]["id"]["videoId"]
            return DietRecipeTutorialResponse(
                recipe_id=recipe_id,
                search_query=search_query,
                youtube_url=f"https://www.youtube.com/watch?v={video_id}",
            )
    except Exception:
        pass

    return DietRecipeTutorialResponse(
        recipe_id=recipe_id,
        search_query=search_query,
        youtube_url=fallback_url,
    )


@router.get("/market/ingredients", response_model=MarketIngredientResponse)
def get_market_ingredients(
    patient_id: int,
    recipe_id: str | None = None,
    db: Session = Depends(get_db),
) -> MarketIngredientResponse:
    """Return shopping search links for ingredients of a given recipe."""
    ingredients: list[dict] = []

    if recipe_id:
        try:
            result = orchestrator.list_diet_recipes(patient_id=patient_id)
            recipes = result.get("recipes", [])
            matched = next((r for r in recipes if r.get("recipe_id") == recipe_id), None)
            if matched:
                for ing in matched.get("ingredients", []):
                    name = ing.get("name", "") if isinstance(ing, dict) else str(ing)
                    if name:
                        ingredients.append({
                            "name": name,
                            "search_url": ProductUrlRouter.get_search_url(name, "ingredient"),
                        })
        except Exception:
            pass

    if not ingredients:
        fallback_items = ["rice", "dal", "turmeric", "ghee", "salt"]
        ingredients = [
            {"name": item, "search_url": ProductUrlRouter.get_search_url(item, "ingredient")}
            for item in fallback_items
        ]

    return MarketIngredientResponse(
        patient_id=patient_id,
        recipe_id=recipe_id,
        ingredients=ingredients,
    )


@router.post("/orchestration/document-pipeline", response_model=DocumentPipelineResponse)
def orchestration_document_pipeline(payload: DocumentPipelineRequest) -> DocumentPipelineResponse:
    result = orchestrator.build_document_pipeline(
        patient_id=payload.patient_id,
        file_path=payload.file_path,
        raw_text_hint=payload.raw_text_hint,
        prescription_id=payload.prescription_id,
    )
    return DocumentPipelineResponse(**result)


@router.post("/orchestration/run-document-flow", response_model=DocumentFlowResponse)
def orchestration_run_document_flow(payload: DocumentFlowRequest, db: Session = Depends(get_db)) -> DocumentFlowResponse:
    result = orchestrator.run_document_intake_flow(
        db=db,
        patient_id=payload.patient_id,
        image_reference=payload.image_reference,
        raw_text_hint=payload.raw_text_hint,
        document_file_path=payload.document_file_path,
        pharmacy_location_query=payload.pharmacy_location_query,
        create_calendar_event=payload.create_calendar_event,
    )
    return DocumentFlowResponse(**result)


@router.post("/orchestration/conversation-route", response_model=ConversationRoutingResponse)
def orchestration_conversation_route(payload: ConversationRoutingRequest, db: Session = Depends(get_db)) -> ConversationRoutingResponse:
    result = orchestrator.route_conversation(patient_id=payload.patient_id, message=payload.message, db=db)
    return ConversationRoutingResponse(**result)


@router.post("/orchestration/action-draft", response_model=ActionDraftResponse)
def orchestration_action_draft(payload: ActionDraftRequest, db: Session = Depends(get_db)) -> ActionDraftResponse:
    result = orchestrator.draft_action(
        db=db,
        patient_id=payload.patient_id,
        intent=payload.intent,
        message=payload.message,
    )
    return ActionDraftResponse(**result)


@router.post("/orchestration/action-confirm", response_model=ActionConfirmResponse)
def orchestration_action_confirm(payload: ActionConfirmRequest, db: Session = Depends(get_db)) -> ActionConfirmResponse:
    result = orchestrator.confirm_action(
        db=db,
        action_id=payload.action_id,
        selected_option=payload.selected_option,
        custom_input=payload.custom_input,
    )
    return ActionConfirmResponse(**result)


import base64

@router.post("/orchestration/voice-route", response_model=ConversationRoutingResponse)
def orchestration_voice_route(
    patient_id: int = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ConversationRoutingResponse:
    audio_bytes = audio.file.read()
    stt_result = orchestrator.integrations.transcribe_audio(audio_bytes)
    
    transcript = stt_result.get("transcript")
    if not transcript:
        raise HTTPException(status_code=400, detail=f"Audio transcription failed: {stt_result.get('error')}")
        
    result = orchestrator.route_conversation(patient_id=patient_id, message=transcript, db=db)
    
    # Text-to-Speech logic for voice-route (cleaning URLs/paths)
    clean_message = re.sub(r'https?://\S+', '', result["message"])
    clean_message = re.sub(r'[a-zA-Z]:\\[\\\S]+', '', clean_message)
    clean_message = clean_message.strip()
    
    tts_result = orchestrator.integrations.synthesize_speech(clean_message)
    if tts_result.get("audio_bytes"):
        result["audio_base64"] = base64.b64encode(tts_result["audio_bytes"]).decode("utf-8")
        
    return ConversationRoutingResponse(**result)


from fastapi.responses import StreamingResponse
import re

@router.post("/orchestration/voice-route-stream")
async def orchestration_voice_route_stream(
    patient_id: int = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Streaming version of voice-route to reduce perceived latency."""
    audio_bytes = audio.file.read()
    stt_result = orchestrator.integrations.transcribe_audio(audio_bytes)
    
    transcript = stt_result.get("transcript")
    if not transcript:
        async def error_gen():
            yield json.dumps({"type": "error", "message": "Transcription failed"}) + "\n"
        return StreamingResponse(error_gen(), media_type="application/x-ndjson")
        
    result = orchestrator.route_conversation(patient_id=patient_id, message=transcript, db=db)
    full_message = result["message"]
    
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', full_message) if s.strip()]
    
    async def audio_generator():
        import asyncio
        
        yield json.dumps({
            "type": "metadata",
            "transcript": transcript,
            "full_message": full_message,
            "route_type": result.get("route_type"),
            "primary_model": result.get("primary_model"),
            "action_id": result.get("action_id"),
            "options": result.get("options") or [],
            "allow_custom_input": bool(result.get("allow_custom_input", False)),
        }) + "\n"
        
        tasks = []
        for sentence in sentences:
            # Clean technical noise (URLs, paths) from the spoken text
            clean_sentence = re.sub(r'https?://\S+', '', sentence) # Remove URLs
            clean_sentence = re.sub(r'[a-zA-Z]:\\[\\\S]+', '', clean_sentence) # Remove Windows paths
            clean_sentence = re.sub(r'/\S+/\S+', '', clean_sentence) # Remove Unix-like paths
            clean_sentence = clean_sentence.strip()
            
            if not clean_sentence or len(clean_sentence) < 2:
                continue

            # Schedule synchronous TTS call in background thread concurrently
            task = asyncio.to_thread(orchestrator.integrations.synthesize_speech, clean_sentence)
            tasks.append(task)
            
        # Await tasks in original order so playback is sequential
        for task in tasks:
            tts_result = await task
            if tts_result and tts_result.get("audio_bytes"):
                audio_b64 = base64.b64encode(tts_result["audio_bytes"]).decode("utf-8")
                yield json.dumps({"type": "audio", "chunk": audio_b64}) + "\n"
            
    return StreamingResponse(audio_generator(), media_type="application/x-ndjson")

@router.websocket("/orchestration/voice-live-stream/{patient_id}")
async def orchestration_voice_live_stream(
    websocket: WebSocket,
    patient_id: int,
    db: Session = Depends(get_db),
):
    """WebSocket endpoint for Gemini Live."""
    await websocket.accept()
    
    from nexus_ai.config import get_settings
    settings = get_settings()

    audio_input_queue = asyncio.Queue()
    video_input_queue = asyncio.Queue()
    text_input_queue = asyncio.Queue()

    async def audio_output_callback(data):
        await websocket.send_bytes(data)

    async def audio_interrupt_callback():
        pass

    gemini_client = GeminiLive(
        api_key=settings.google_api_key,
        model="gemini-2.5-flash-native-audio-latest",
        input_sample_rate=16000
    )

    async def receive_from_client():
        import logging
        ws_logger = logging.getLogger("uvicorn.error")
        try:
            while True:
                message = await websocket.receive()
                if message.get("bytes"):
                    ws_logger.info(f"WS client sent {len(message['bytes'])} bytes")
                    await audio_input_queue.put(message["bytes"])
                elif message.get("text"):
                    text = message["text"]
                    ws_logger.info(f"WS client sent text: {text}")
                    try:
                        payload = json.loads(text)
                        if isinstance(payload, dict) and payload.get("type") == "image":
                            image_data = base64.b64decode(payload["data"])
                            await video_input_queue.put(image_data)
                            continue
                    except json.JSONDecodeError:
                        pass
                    await text_input_queue.put(text)
        except WebSocketDisconnect:
            ws_logger.info("WS client disconnected cleanly")
            pass

    receive_task = asyncio.create_task(receive_from_client())

    try:
        async for event in gemini_client.start_session(
            audio_input_queue=audio_input_queue,
            video_input_queue=video_input_queue,
            text_input_queue=text_input_queue,
            audio_output_callback=audio_output_callback,
            audio_interrupt_callback=audio_interrupt_callback,
        ):
            if event:
                await websocket.send_json(event)
    except Exception as e:
        import traceback
        print(f"Error in Gemini session: {e}\n{traceback.format_exc()}")
    finally:
        receive_task.cancel()
        try:
            await websocket.close()
        except:
            pass

@router.post("/orchestration/medical-route", response_model=MedicalRoutingResponse)
def orchestration_medical_route(payload: MedicalRoutingRequest) -> MedicalRoutingResponse:
    result = orchestrator.route_medical_input(
        patient_id=payload.patient_id,
        query_text=payload.query_text,
        file_path=payload.file_path,
    )
    return MedicalRoutingResponse(**result)


@router.post("/medical-memory/store", response_model=MedicalMemoryStoreResponse)
def medical_memory_store(payload: MedicalMemoryStoreRequest, db: Session = Depends(get_db)) -> MedicalMemoryStoreResponse:
    result = orchestrator.store_medical_memory(
        db=db,
        patient_id=payload.patient_id,
        source_type=payload.source_type,
        query_text=payload.query_text,
        file_path=payload.file_path,
        drive_file_id=payload.drive_file_id,
        drive_file_url=payload.drive_file_url,
        drive_path=payload.drive_path,
        use_live_embedding=payload.use_live_embedding,
        metadata=payload.metadata,
    )
    return MedicalMemoryStoreResponse(**result)


@router.post("/medical-memory/search", response_model=MedicalMemorySearchResponse)
def medical_memory_search(payload: MedicalMemorySearchRequest, db: Session = Depends(get_db)) -> MedicalMemorySearchResponse:
    result = orchestrator.search_medical_memory(
        db=db,
        patient_id=payload.patient_id,
        query_text=payload.query_text,
        modality=payload.modality,
        limit=payload.limit,
    )
    return MedicalMemorySearchResponse(**result)


@router.get("/orchestration/routine-automation/{patient_id}", response_model=RoutineAutomationResponse)
def orchestration_routine_automation(patient_id: int, db: Session = Depends(get_db)) -> RoutineAutomationResponse:
    result = orchestrator.run_routine_automation(db=db, patient_id=patient_id)
    return RoutineAutomationResponse(**result)



@router.get("/orchestration/manifest/{patient_id}", response_model=OrchestrationManifestResponse)
def orchestration_manifest(patient_id: int) -> OrchestrationManifestResponse:
    result = orchestrator.get_orchestration_manifest(patient_id)
    return OrchestrationManifestResponse(**result)


# ── Care Maze: AI-powered image analysis endpoints ───────────────

from nexus_ai.services.gemini_vision import GeminiVisionService

_gemini_vision = GeminiVisionService()


@router.post("/caremaze/analyze-symptom", response_model=SymptomAnalysisResponse)
def caremaze_analyze_symptom(
    patient_id: int = Form(...),
    file: UploadFile = File(...),
) -> SymptomAnalysisResponse:
    """Analyze an uploaded symptom image (skin condition, lab report, etc.)
    using Gemini vision and return structured findings plus an
    AI-generated annotated diagnostic comparison graphic."""
    image_bytes = file.file.read()
    mime = file.content_type or "image/jpeg"

    # Step 1 – text analysis
    result = _gemini_vision.analyze_symptom_image(
        image_bytes=image_bytes,
        mime_type=mime,
        analysis_type="symptom",
    )

    # Step 2 – generate annotated diagnostic comparison image
    diagnostic_b64 = _gemini_vision.generate_diagnostic_image(
        image_bytes=image_bytes,
        mime_type=mime,
        analysis=result,
    )

    return SymptomAnalysisResponse(
        patient_id=patient_id,
        severity=result["severity"],
        confidence=result["confidence"],
        findings=result["findings"],
        summary=result["summary"],
        model_used=_gemini_vision._analysis_model_id,
        diagnostic_image_base64=diagnostic_b64,
    )


@router.post("/caremaze/analyze-prescription", response_model=PrescriptionAnalysisResponse)
def caremaze_analyze_prescription(
    patient_id: int = Form(...),
    file: UploadFile = File(...),
) -> PrescriptionAnalysisResponse:
    """Analyze an uploaded prescription image using Gemini vision
    and return extracted medication details."""
    image_bytes = file.file.read()
    mime = file.content_type or "image/jpeg"

    result = _gemini_vision.analyze_symptom_image(
        image_bytes=image_bytes,
        mime_type=mime,
        analysis_type="prescription",
    )

    return PrescriptionAnalysisResponse(
        patient_id=patient_id,
        medication_name=result.get("medication_name", "Unknown"),
        dosage=result.get("dosage"),
        instructions=result.get("instructions"),
        confidence=result["confidence"],
        findings=result["findings"],
        summary=result["summary"],
        model_used=_gemini_vision._analysis_model_id,
    )

# ── Doctor-Patient Chat ──────────────────────────────────────


@router.get("/chat/threads", response_model=ChatThreadListResponse)
def list_chat_threads(patient_id: int | None = None, doctor_id: int | None = None, db: Session = Depends(get_db)):
    from nexus_ai.db.models import ChatThread, ChatMessage
    from sqlalchemy import func

    query = db.query(ChatThread)
    if patient_id is not None:
        query = query.filter(ChatThread.patient_id == patient_id)
    if doctor_id is not None:
        query = query.filter(ChatThread.doctor_id == doctor_id)

    threads = query.order_by(ChatThread.updated_at.desc()).all()
    result = []
    for thread in threads:
        msg_count = db.query(func.count(ChatMessage.id)).filter(ChatMessage.thread_id == thread.id).scalar() or 0
        last_msg = db.query(ChatMessage).filter(ChatMessage.thread_id == thread.id).order_by(ChatMessage.created_at.desc()).first()
        last_msg_resp = None
        if last_msg:
            last_msg_resp = ChatMessageResponse(
                id=last_msg.id,
                thread_id=last_msg.thread_id,
                sender_role=last_msg.sender_role,
                sender_display_name=last_msg.sender_display_name,
                body=last_msg.body,
                created_at=last_msg.created_at.isoformat(),
            )
        result.append(ChatThreadResponse(
            id=thread.id,
            patient_id=thread.patient_id,
            doctor_id=thread.doctor_id,
            subject=thread.subject,
            status=thread.status,
            created_at=thread.created_at.isoformat(),
            updated_at=thread.updated_at.isoformat(),
            last_message=last_msg_resp,
            message_count=msg_count,
        ))
    return ChatThreadListResponse(threads=result)


@router.post("/chat/threads", response_model=ChatThreadResponse, status_code=201)
def create_chat_thread(payload: ChatThreadCreateRequest, db: Session = Depends(get_db)):
    from nexus_ai.db.models import ChatThread

    thread = ChatThread(
        patient_id=payload.patient_id,
        doctor_id=payload.doctor_id,
        subject=payload.subject,
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return ChatThreadResponse(
        id=thread.id,
        patient_id=thread.patient_id,
        doctor_id=thread.doctor_id,
        subject=thread.subject,
        status=thread.status,
        created_at=thread.created_at.isoformat(),
        updated_at=thread.updated_at.isoformat(),
    )


@router.get("/chat/threads/{thread_id}/messages", response_model=ChatMessageListResponse)
def list_chat_messages(thread_id: int, db: Session = Depends(get_db)):
    from nexus_ai.db.models import ChatMessage

    messages = db.query(ChatMessage).filter(
        ChatMessage.thread_id == thread_id
    ).order_by(ChatMessage.created_at.asc()).all()

    return ChatMessageListResponse(
        thread_id=thread_id,
        messages=[
            ChatMessageResponse(
                id=msg.id,
                thread_id=msg.thread_id,
                sender_role=msg.sender_role,
                sender_display_name=msg.sender_display_name,
                body=msg.body,
                created_at=msg.created_at.isoformat(),
            )
            for msg in messages
        ],
    )


@router.post("/chat/threads/{thread_id}/messages", response_model=ChatMessageResponse, status_code=201)
def create_chat_message(thread_id: int, payload: ChatMessageCreateRequest, db: Session = Depends(get_db)):
    from nexus_ai.db.models import ChatThread, ChatMessage
    from datetime import datetime, UTC

    thread = db.query(ChatThread).filter(ChatThread.id == thread_id).first()
    if thread is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Chat thread not found")

    message = ChatMessage(
        thread_id=thread_id,
        sender_role=payload.sender_role,
        sender_display_name=payload.sender_display_name,
        body=payload.body,
    )
    db.add(message)
    thread.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(message)

    return ChatMessageResponse(
        id=message.id,
        thread_id=message.thread_id,
        sender_role=message.sender_role,
        sender_display_name=message.sender_display_name,
        body=message.body,
        created_at=message.created_at.isoformat(),
    )

class ExtractSafeIngredientsRequest(BaseModel):
    patient_id: int
    url: str | None = None
    image_base64: str | None = None

class ExtractSafeIngredientsResponse(BaseModel):
    safe_ingredients: list[dict]

@router.post("/diet/multiagent/extract-safe-ingredients", response_model=ExtractSafeIngredientsResponse)
def multiagent_extract_safe_ingredients(payload: ExtractSafeIngredientsRequest):
    from nexus_ai.agents.diet_multiagent.medical_analyst import analyze_patient_dietary_needs
    from nexus_ai.agents.diet_multiagent.vision_extractor import extract_ingredients
    from nexus_ai.services.diet.filter import generate_safe_ingredients
    import base64
    
    # 1. Medical Analyst
    dietary_needs = analyze_patient_dietary_needs(payload.patient_id)
    ingredients_to_avoid = dietary_needs.get("ingredients_to_avoid", [])
    
    # 2. Vision Extractor
    image_bytes = None
    if payload.image_base64:
        image_bytes = base64.b64decode(payload.image_base64)
    extracted = extract_ingredients(url=payload.url, image_bytes=image_bytes)
    detected_ingredients = extracted.get("detected_ingredients", [])
    
    # 3. Filter
    safe_ingredients = generate_safe_ingredients(detected_ingredients, ingredients_to_avoid)
    
    return ExtractSafeIngredientsResponse(safe_ingredients=safe_ingredients)

from fastapi.responses import StreamingResponse

@router.post("/diet/multiagent/extract-safe-ingredients-stream")
async def multiagent_extract_safe_ingredients_stream(payload: ExtractSafeIngredientsRequest):
    async def event_generator():
        import json
        for resp in orchestrator.diet_client.stream_extract_safe_ingredients(
            patient_id=payload.patient_id,
            url=payload.url,
            image_base64=payload.image_base64
        ):
            if resp.success:
                yield json.dumps({"type": "ingredient", "data": json.loads(resp.ingredient_json)}) + "\n"
    
    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

class GenerateCulinaryRecipeRequest(BaseModel):
    safe_ingredients: list[str]
    cuisine_style: str
    duration: str
    patient_id: int

@router.post("/diet/multiagent/generate-recipe")
def multiagent_generate_recipe(payload: GenerateCulinaryRecipeRequest):
    from nexus_ai.agents.diet_multiagent.medical_analyst import analyze_patient_dietary_needs
    from nexus_ai.agents.diet_multiagent.culinary_generator import generate_recipe
    
    dietary_needs = analyze_patient_dietary_needs(payload.patient_id)
    rules = dietary_needs.get("general_dietary_rules", [])
    
    recipe_data = generate_recipe(
        safe_ingredients=payload.safe_ingredients,
        cuisine_style=payload.cuisine_style,
        duration=payload.duration,
        dietary_rules=rules
    )
    
    return recipe_data


# ── Cart routes ──────────────────────────────────────────────────────

from nexus_ai.services.shopping_service import ShoppingService
shopping_service = ShoppingService()

@router.get("/patient/{patient_id}/cart", response_model=list[CartItemResponse])
def get_cart(patient_id: int, db: Session = Depends(get_db)) -> list[CartItemResponse]:
    items = db.scalars(select(CartItem).where(CartItem.patient_id == patient_id).order_by(CartItem.created_at.desc())).all()
    return [
        CartItemResponse(
            id=item.id,
            patient_id=item.patient_id,
            item_name=item.item_name,
            item_type=item.item_type,
            price=item.price,
            status=item.status,
            source_url=item.source_url,
            original_price=item.original_price,
            coupon_code=item.coupon_code,
            last_checked=item.last_checked.isoformat() if item.last_checked else None,
            created_at=item.created_at.isoformat(),
        )
        for item in items
    ]

@router.post("/patient/{patient_id}/cart", response_model=CartItemResponse)
def add_to_cart(patient_id: int, payload: CartItemCreateRequest, db: Session = Depends(get_db)) -> CartItemResponse:
    # Check if item already exists in cart with non-purchased status
    existing = db.scalar(
        select(CartItem).where(
            CartItem.patient_id == patient_id,
            CartItem.item_name == payload.item_name,
            CartItem.status != "purchased"
        )
    )
    if existing:
        return CartItemResponse(
            id=existing.id,
            patient_id=existing.patient_id,
            item_name=existing.item_name,
            item_type=existing.item_type,
            price=existing.price,
            status=existing.status,
            source_url=existing.source_url,
            original_price=existing.original_price,
            coupon_code=existing.coupon_code,
            last_checked=existing.last_checked.isoformat() if existing.last_checked else None,
            created_at=existing.created_at.isoformat(),
        )
        
    item = CartItem(
        patient_id=patient_id,
        item_name=payload.item_name,
        item_type=payload.item_type,
        price=payload.price,
        source_url=payload.source_url or ProductUrlRouter.get_search_url(payload.item_name, payload.item_type),
        status="checking",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    
    return CartItemResponse(
        id=item.id,
        patient_id=item.patient_id,
        item_name=item.item_name,
        item_type=item.item_type,
        price=item.price,
        status=item.status,
        source_url=item.source_url,
        original_price=item.original_price,
        coupon_code=item.coupon_code,
        last_checked=item.last_checked.isoformat() if item.last_checked else None,
        created_at=item.created_at.isoformat(),
    )

@router.delete("/patient/{patient_id}/cart/{item_id}")
def delete_from_cart(patient_id: int, item_id: int, db: Session = Depends(get_db)):
    item = db.scalar(select(CartItem).where(CartItem.id == item_id, CartItem.patient_id == patient_id))
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(item)
    db.commit()
    return {"success": True, "message": "Item deleted from cart"}

@router.post("/patient/{patient_id}/cart/check-availability", response_model=list[CartItemResponse])
def trigger_availability_check(patient_id: int, db: Session = Depends(get_db)) -> list[CartItemResponse]:
    items = shopping_service.check_cart_availability(db, patient_id)
    return [
        CartItemResponse(
            id=item.id,
            patient_id=item.patient_id,
            item_name=item.item_name,
            item_type=item.item_type,
            price=item.price,
            status=item.status,
            source_url=item.source_url,
            original_price=item.original_price,
            coupon_code=item.coupon_code,
            last_checked=item.last_checked.isoformat() if item.last_checked else None,
            created_at=item.created_at.isoformat(),
        )
        for item in items
    ]

@router.post("/patient/{patient_id}/cart/{item_id}/checkout", response_model=CartCheckoutResponse)
def checkout_cart_item(patient_id: int, item_id: int, db: Session = Depends(get_db)) -> CartCheckoutResponse:
    res = shopping_service.checkout_item(db, patient_id, item_id)
    return CartCheckoutResponse(**res)



