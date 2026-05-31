from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field


class ConditionInput(BaseModel):
    name: str
    condition_type: str = "chronic"
    last_updated: date | None = None
    notes: str | None = None


class PatientIntakeRequest(BaseModel):
    full_name: str
    preferred_language: str = "en"
    date_of_birth: date | None = None
    active_conditions: list[ConditionInput] = Field(default_factory=list)


class PatientIntakeResponse(BaseModel):
    patient_id: int
    summary: str


class PrescriptionScanRequest(BaseModel):
    patient_id: int
    image_reference: str | None = None
    raw_text_hint: str | None = None


class PrescriptionScanResponse(BaseModel):
    prescription_id: int
    medication_name: str
    dosage: str | None = None
    instructions: str | None = None
    confidence_score: float
    review_status: str


class CheckAlternativesRequest(BaseModel):
    patient_id: int
    unavailable_medication: str


class AlternativeCandidate(BaseModel):
    name: str
    formulation_note: str
    safety_note: str



class CheckAlternativesResponse(BaseModel):
    patient_id: int
    candidates: list[AlternativeCandidate]
    escalation_required: bool
    safety_summary: str


class EscalateRequest(BaseModel):
    patient_id: int
    case_type: str = "doctor_review"
    summary: str
    doctor_id: int | None = None
    urgency: str | None = None
    document_file_path: str | None = None
    calendar_summary: str | None = None
    create_calendar_event: bool = False
    calendar_minutes_from_now: int = 30
    calendar_duration_minutes: int = 30
    pharmacy_location_query: str | None = None


class EscalateResponse(BaseModel):
    case_id: int
    external_ticket_id: str | None
    status: str
    external_ticket_url: str | None = None
    doctor_id: int | None = None
    doctor_name: str | None = None
    doctor_email: str | None = None
    urgency: str | None = None
    drive_file_id: str | None = None
    drive_file_url: str | None = None
    calendar_event_id: str | None = None
    calendar_event_url: str | None = None
    pharmacy_search_summary: str | None = None


class NotifyRequest(BaseModel):
    patient_id: int
    message_type: str
    message_body: str
    channel: str = "mock_email"


class NotifyResponse(BaseModel):
    notification_id: int
    delivery_status: str


class CaseResponse(BaseModel):
    case_id: int
    patient_id: int
    case_type: str
    status: str
    summary: str
    doctor_id: int | None = None
    doctor_name: str | None = None
    doctor_email: str | None = None
    urgency: str | None = None
    external_ticket_id: str | None = None
    external_ticket_url: str | None = None
    drive_file_id: str | None = None
    drive_file_url: str | None = None
    calendar_event_id: str | None = None
    calendar_event_url: str | None = None
    pharmacy_search_summary: str | None = None


class DriveUploadRequest(BaseModel):
    patient_id: int
    file_path: str
    mime_type: str = "application/octet-stream"
    prescription_id: int | None = None
    doctor_name: str | None = None
    patient_name: str | None = None
    document_type: str | None = None
    disease_name: str | None = None
    capture_date: str | None = None
    image_category: str | None = None


class DriveUploadResponse(BaseModel):
    patient_id: int
    file_id: str
    file_name: str
    web_view_link: str | None = None
    prescription_id: int | None = None
    image_category: str | None = None
    doctor_name: str | None = None
    patient_name: str | None = None
    document_type: str | None = None
    disease_name: str | None = None
    capture_date: str | None = None
    drive_path: str | None = None


class CalendarEventRequest(BaseModel):
    patient_id: int
    summary: str
    minutes_from_now: int = 30
    duration_minutes: int = 30
    escalation_case_id: int | None = None


class CalendarEventResponse(BaseModel):
    patient_id: int
    event_id: str
    html_link: str | None = None
    escalation_case_id: int | None = None


class MedicineGroundedAnswerRequest(BaseModel):
    patient_id: int
    medication_name: str


class MedicineGroundedAnswerResponse(BaseModel):
    patient_id: int
    medication_name: str
    safety_summary: str
    source_used: str
    wiki_link: str | None = None


class DrugLabelRequest(BaseModel):
    medication_name: str


class DrugLabelResponse(BaseModel):
    medication_name: str
    found: bool
    label: dict | None = None


class PharmacySearchRequest(BaseModel):
    location_query: str


class PharmacySearchResponse(BaseModel):
    provider: str
    pharmacies: list[dict]


class CareDestinationSearchRequest(BaseModel):
    patient_id: int
    destination_type: str = "pharmacy"
    location_query: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    medication_name: str | None = None
    condition_name: str | None = None


class CareDestinationResponse(BaseModel):
    name: str
    destination_type: str
    address: str
    distance_km: float | None = None
    eta_minutes: int | None = None
    map_query: str | None = None
    map_url: str | None = None
    notes: str | None = None


class CareDestinationSearchResponse(BaseModel):
    patient_id: int
    searched_location: str
    destination_type: str
    source_used: str
    summary: str
    destinations: list[CareDestinationResponse] = Field(default_factory=list)


class CareMapRouteRequest(BaseModel):
    patient_id: int
    destination_name: str
    destination_type: str = "pharmacy"
    destination_address: str | None = None
    location_query: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    medication_name: str | None = None
    condition_name: str | None = None


class CareMapRouteResponse(BaseModel):
    patient_id: int
    source_used: str
    origin_label: str
    destination_label: str
    destination_type: str
    route_summary: str
    estimated_minutes: int | None = None
    distance_km: float | None = None
    map_query: str | None = None
    map_url: str | None = None
    steps: list[str] = Field(default_factory=list)


class RoutineTaskResponse(BaseModel):
    task_id: str
    name: str
    completed: bool
    source: str = "Internal"
    title: str | None = None
    short_summary: str | None = None
    full_details: str | None = None
    due_at: str | None = None
    due_on: str | None = None
    notes: str | None = None


class DoctorResponse(BaseModel):
    id: int
    full_name: str
    specialty: str | None = None
    email: str | None = None
    phone: str | None = None
    profile_image_key: str | None = None
    is_default: bool = False
    relationship_type: str | None = None


class DoctorCreateRequest(BaseModel):
    full_name: str
    specialty: str | None = None
    email: str | None = None
    phone: str | None = None
    profile_image_key: str | None = None


class PatientProfileResponse(BaseModel):
    patient_id: int
    full_name: str
    preferred_language: str
    date_of_birth: str | None = None
    summary: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    blood_group: str | None = None
    allergies: list[str] = Field(default_factory=list)
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    primary_language: str | None = None
    notes: str | None = None
    updated_at: str | None = None


class PatientProfileUpdateRequest(BaseModel):
    full_name: str | None = None
    preferred_language: str | None = None
    date_of_birth: date | None = None
    summary: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    blood_group: str | None = None
    allergies: list[str] | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    primary_language: str | None = None
    notes: str | None = None


class PatientVitalCreateRequest(BaseModel):
    blood_pressure: str | None = None
    heart_rate_bpm: int | None = None
    blood_glucose_mg_dl: float | None = None
    temperature_c: float | None = None
    weight_kg: float | None = None
    source: str | None = "manual_entry"


class PatientVitalResponse(BaseModel):
    id: int
    patient_id: int
    blood_pressure: str | None = None
    heart_rate_bpm: int | None = None
    blood_glucose_mg_dl: float | None = None
    temperature_c: float | None = None
    weight_kg: float | None = None
    source: str | None = None
    recorded_at: str


class PatientConditionSnapshotResponse(BaseModel):
    id: int
    patient_id: int
    snapshot_type: str
    summary: str
    profile: dict | None = None
    conditions: list[dict] = Field(default_factory=list)
    prescriptions: list[dict] = Field(default_factory=list)
    vitals: list[dict] = Field(default_factory=list)
    source_event_type: str | None = None
    source_event_id: str | None = None
    created_at: str


class PatientConditionSnapshotCreateRequest(BaseModel):
    snapshot_type: str = "manual"
    summary: str
    profile: dict | None = None
    conditions: list[dict] = Field(default_factory=list)
    prescriptions: list[dict] = Field(default_factory=list)
    vitals: list[dict] = Field(default_factory=list)
    source_event_type: str | None = None
    source_event_id: str | None = None


class PatientHistoryQueryRequest(BaseModel):
    query_text: str


class PatientDoctorMapRequest(BaseModel):
    doctor_id: int
    relationship_type: str = "primary"
    is_default: bool = False
    notes: str | None = None


class DailyCheckInResponse(BaseModel):
    patient_id: int
    profile: dict | None = None
    conditions: list[dict]
    routine_tasks: list[RoutineTaskResponse]
    message: str


class HitlReportRequest(BaseModel):
    patient_id: int
    context_summary: str | None = None
    create_case: bool = False
    case_type: str = "doctor_review"
    doctor_id: int | None = None
    urgency: str | None = None


class HitlReportResponse(BaseModel):
    patient_id: int
    report: str
    case_id: int | None = None
    external_ticket_id: str | None = None
    external_ticket_url: str | None = None


class RoutineSnapshotResponse(BaseModel):
    patient_id: int
    tasks: list[RoutineTaskResponse]


class DietSupportRequest(BaseModel):
    patient_id: int
    medication_name: str | None = None
    location_query: str | None = None


class DietSupportResponse(BaseModel):
    patient_id: int
    conditions: list[dict]
    diet_plan: dict
    pharmacy_result: dict


class RecipeIngredient(BaseModel):
    name: str
    quantity: float
    unit: str


class DietRecipeSafetyNote(BaseModel):
    severity: str
    message: str
    related_to: str | None = None


class DietRecipe(BaseModel):
    recipe_id: str
    source: str
    title: str
    description: str
    default_servings: int
    cook_time: str
    meal_type: str | None = None
    ingredients: list[RecipeIngredient]
    instructions: list[str]
    safety_notes: list[DietRecipeSafetyNote] = Field(default_factory=list)
    condition_fit: list[str] = Field(default_factory=list)
    medication_fit: list[str] = Field(default_factory=list)
    avoid_flags: list[str] = Field(default_factory=list)
    why_it_fits: str
    dietary_pattern: str | None = None
    cuisine_preference: str | None = None
    image_url: str | None = None
    image_status: str = "unavailable"


class GenerateDietRecipesRequest(BaseModel):
    patient_id: int
    medication_name: str | None = None
    meal_type: str = "any"
    available_ingredients: list[str] = Field(default_factory=list)
    avoid_ingredients: list[str] = Field(default_factory=list)
    cuisine_preference: str | None = None
    dietary_pattern: str | None = None
    max_cook_minutes: int | None = None
    servings: int = 4
    count: int = 3


class GenerateDietRecipesResponse(BaseModel):
    patient_id: int
    conditions: list[dict]
    medication_name: str | None = None
    recipes: list[DietRecipe]
    fallback_used: bool = False
    safety_summary: str


class ScaleDietRecipeRequest(BaseModel):
    servings: int = Field(default=4, ge=1, le=20)


class ScaleDietRecipeResponse(BaseModel):
    recipe: DietRecipe



class DietRecipeTutorialResponse(BaseModel):
    recipe_id: str
    search_query: str
    youtube_url: str


class SavedDietRecipesResponse(BaseModel):
    patient_id: int
    recipes: list[DietRecipe]


class SaveDietRecipeResponse(BaseModel):
    patient_id: int
    recipe_id: str
    saved: bool = True


class MarketIngredientResponse(BaseModel):
    patient_id: int
    recipe_id: str | None = None
    ingredients: list[dict] = Field(default_factory=list)


class DocumentPipelineRequest(BaseModel):
    patient_id: int
    file_path: str
    raw_text_hint: str | None = None
    prescription_id: int | None = None


class DocumentPipelineResponse(BaseModel):
    patient_id: int
    file_name: str
    file_path: str
    prescription_id: int | None = None
    ocr_model: str
    reasoning_model: str
    support_model: str | None = None
    storage_target: str
    ocr_strategy: str
    raw_text_hint: str | None = None
    route_type: str
    route_reason: str
    execution_plan: list[str]


class ConversationRoutingRequest(BaseModel):
    patient_id: int
    message: str


class ConversationRoutingResponse(BaseModel):
    patient_id: int
    profile: dict | None = None
    message: str
    route_type: str
    primary_model: str
    support_model: str | None = None
    reason: str
    audio_base64: str | None = None
    suggested_response_style: str
    execution_plan: list[str]
    action_id: int | None = None
    intent: str | None = None
    question: str | None = None
    options: list[dict] = Field(default_factory=list)
    allow_custom_input: bool = False
    preview: str | None = None


class ActionDraftRequest(BaseModel):
    patient_id: int
    intent: str
    message: str


class ActionDraftResponse(BaseModel):
    action_id: int
    intent: str
    question: str
    options: list[dict] = Field(default_factory=list)
    allow_custom_input: bool = True
    preview: str | None = None


class ActionConfirmRequest(BaseModel):
    action_id: int
    selected_option: str | None = None
    custom_input: str | None = None


class ActionConfirmResponse(BaseModel):
    action_id: int
    status: str
    result: dict = Field(default_factory=dict)


class PendingActionResponse(BaseModel):
    action_id: int
    patient_id: int
    action_type: str
    status: str
    options: list[dict] = Field(default_factory=list)
    selected_option: dict | None = None
    result: dict | None = None
    created_at: str
    confirmed_at: str | None = None


class MedicalRoutingRequest(BaseModel):
    patient_id: int
    query_text: str | None = None
    file_path: str | None = None


class MedicalRoutingResponse(BaseModel):
    patient_id: int
    profile: dict | None = None
    query_text: str | None = None
    file_path: str | None = None
    route_type: str
    primary_model: str
    secondary_model: str | None = None
    support_model: str | None = None
    reason: str
    execution_plan: list[str]


class MedicalMemoryStoreRequest(BaseModel):
    patient_id: int
    source_type: str = "manual_upload"
    query_text: str | None = None
    file_path: str | None = None
    drive_file_id: str | None = None
    drive_file_url: str | None = None
    drive_path: str | None = None
    use_live_embedding: bool = False
    metadata: dict = Field(default_factory=dict)


class MedicalMemoryStoreResponse(BaseModel):
    memory_id: int
    patient_id: int
    source_type: str
    modality: str
    embedding_model: str
    summary_text: str | None = None
    live_embedding_used: bool
    route_type: str
    route_reason: str


class MedicalMemorySearchRequest(BaseModel):
    patient_id: int
    query_text: str
    modality: str | None = None
    limit: int = 5


class MedicalMemorySearchResult(BaseModel):
    memory_id: int
    source_type: str
    source_reference: str | None = None
    modality: str
    embedding_model: str
    summary_text: str | None = None
    drive_file_id: str | None = None
    drive_file_url: str | None = None
    metadata: dict
    similarity: float


class MedicalMemorySearchResponse(BaseModel):
    patient_id: int
    profile: dict | None = None
    query_text: str
    results: list[MedicalMemorySearchResult]




class DocumentFlowRequest(BaseModel):
    patient_id: int
    image_reference: str | None = None
    raw_text_hint: str | None = None
    document_file_path: str | None = None
    pharmacy_location_query: str | None = None
    create_calendar_event: bool = True


class DocumentFlowResponse(BaseModel):
    patient_id: int
    prescription: dict
    document_pipeline: dict
    drive_result: dict | None = None
    memory_result: dict
    alternatives: list[dict]
    diet_support: dict
    pharmacy_result: dict | None = None
    escalation_required: bool
    safety_summary: str
    case: dict | None = None
    calendar_result: dict | None = None
    notification: dict
    flow_notes: list[str]


class CareDestinationRequest(BaseModel):
    patient_id: int
    location_query: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    destination_type: str = "pharmacy"
    medication_name: str | None = None
    condition_context: str | None = None


class CareRouteResponse(BaseModel):
    patient_id: int
    destination_type: str
    origin_label: str
    destination_label: str
    source: str
    route_summary: str
    map_embed_url: str | None = None
    map_query_url: str | None = None


class RoutineAutomationResponse(BaseModel):
    patient_id: int
    profile: dict | None = None
    routine_tasks: list[RoutineTaskResponse]
    routine_summary: str
    risk_level: str
    overdue_count: int
    due_today_count: int
    message: str
    case: dict | None = None


class CareDestinationPatientResponse(BaseModel):
    patient_id: int
    destination_type: str
    origin_label: str
    source: str
    destinations: list[CareDestinationResponse]
    map_query_url: str | None = None


class OrchestrationManifestResponse(BaseModel):
    patient_id: int
    profile: dict | None = None
    conditions: list[dict]
    routine_tasks: list[RoutineTaskResponse]
    agent_manifest: dict
    trigger_manifest: dict


class SymptomAnalysisResponse(BaseModel):
    patient_id: int
    severity: str
    confidence: int
    findings: list[str]
    summary: str
    model_used: str
    diagnostic_image_base64: str | None = None


class PrescriptionAnalysisResponse(BaseModel):
    patient_id: int
    medication_name: str
    dosage: str | None = None
    instructions: str | None = None
    confidence: int
    findings: list[str]
    summary: str
    model_used: str


class VisionSuggestedAction(BaseModel):
    action_id: str
    label: str
    description: str


class VisionUploadAnalyzeResponse(BaseModel):
    patient_id: int
    category: str
    analysis_type: str
    detected_type: str | None = None
    medication_name: str | None = None
    dosage: str | None = None
    instructions: str | None = None
    severity: str | None = None
    confidence: int
    findings: list[str] = Field(default_factory=list)
    summary: str
    diet_relevant: bool = False
    model_used: str
    diagnostic_image_base64: str | None = None
    drive_upload: DriveUploadResponse
    prescription_id: int | None = None
    snapshot_id: int | None = None
    created_case_id: int | None = None
    suggested_actions: list[VisionSuggestedAction] = Field(default_factory=list)


# ── Doctor-Patient Chat models ──────────────────────────────────────


class ChatThreadCreateRequest(BaseModel):
    patient_id: int
    doctor_id: int
    subject: str = "General consultation"


SenderRole = Literal["patient", "doctor"]


class ChatMessageCreateRequest(BaseModel):
    sender_role: SenderRole
    sender_display_name: str
    body: str


class ChatMessageResponse(BaseModel):
    id: int
    thread_id: int
    sender_role: SenderRole
    sender_display_name: str
    body: str
    created_at: str


class ChatThreadResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    subject: str
    status: str
    created_at: str
    updated_at: str
    last_message: ChatMessageResponse | None = None
    message_count: int = 0


class ChatThreadListResponse(BaseModel):
    threads: list[ChatThreadResponse]


class ChatMessageListResponse(BaseModel):
    thread_id: int
    messages: list[ChatMessageResponse]


# ── Cart models ──────────────────────────────────────────────────────


class CartItemCreateRequest(BaseModel):
    item_name: str
    item_type: str = "ingredient"  # "medicine" or "ingredient"
    price: float | None = None
    source_url: str | None = None


class CartItemResponse(BaseModel):
    id: int
    patient_id: int
    item_name: str
    item_type: str
    price: float | None = None
    status: str
    source_url: str | None = None
    original_price: float | None = None
    coupon_code: str | None = None
    last_checked: str | None = None
    created_at: str


class CartCheckoutResponse(BaseModel):
    success: bool
    message: str
    order_id: str | None = None
    item_name: str | None = None
    price: float | None = None

