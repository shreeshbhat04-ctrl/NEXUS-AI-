from datetime import datetime, date, UTC
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Integer, Float, Date, DateTime, Boolean, JSON, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

def utcnow() -> datetime:
    return datetime.now(UTC)

class Base(DeclarativeBase):
    pass

class Patient(Base):
    __tablename__ = "patients"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    preferred_language: Mapped[str] = mapped_column(String(50), default="en")
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    summary: Mapped[Optional[str]] = mapped_column(String)
    google_email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    google_access_token: Mapped[Optional[str]] = mapped_column(String)
    google_refresh_token: Mapped[Optional[str]] = mapped_column(String)
    google_token_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class PatientVital(Base):
    __tablename__ = "patient_vitals"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    blood_pressure: Mapped[Optional[str]] = mapped_column(String(50))
    heart_rate_bpm: Mapped[Optional[int]] = mapped_column(Integer)
    blood_glucose_mg_dl: Mapped[Optional[float]] = mapped_column(Float)
    temperature_c: Mapped[Optional[float]] = mapped_column(Float)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float)
    source: Mapped[Optional[str]] = mapped_column(String(100))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class PatientProfileDetail(Base):
    __tablename__ = "patient_profile_details"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    height_cm: Mapped[Optional[float]] = mapped_column(Float)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float)
    blood_group: Mapped[Optional[str]] = mapped_column(String(10))
    allergies_json: Mapped[Optional[str]] = mapped_column(String)
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(255))
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(50))
    primary_language: Mapped[Optional[str]] = mapped_column(String(50))
    notes: Mapped[Optional[str]] = mapped_column(String)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class ChronicCondition(Base):
    __tablename__ = "chronic_conditions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    condition_type: Mapped[str] = mapped_column(String(100), default="chronic")
    last_updated: Mapped[Optional[date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(String)

class Prescription(Base):
    __tablename__ = "prescriptions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    source_reference: Mapped[Optional[str]] = mapped_column(String(255))
    raw_text: Mapped[Optional[str]] = mapped_column(String)
    medication_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dosage: Mapped[Optional[str]] = mapped_column(String(255))
    instructions: Mapped[Optional[str]] = mapped_column(String)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    review_status: Mapped[str] = mapped_column(String(50), default="pending")
    document_drive_file_id: Mapped[Optional[str]] = mapped_column(String(255))
    document_drive_file_url: Mapped[Optional[str]] = mapped_column(String)
    drive_path: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class Notification(Base):
    __tablename__ = "notifications"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    channel: Mapped[str] = mapped_column(String(100), nullable=False)
    message_type: Mapped[str] = mapped_column(String(100), nullable=False)
    body: Mapped[str] = mapped_column(String, nullable=False)
    delivery_status: Mapped[str] = mapped_column(String(50), default="queued")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class Doctor(Base):
    __tablename__ = "doctors"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    specialty: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    profile_image_key: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class PatientDoctorMap(Base):
    __tablename__ = "patient_doctor_maps"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    doctor_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(100), default="primary")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class EscalationCase(Base):
    __tablename__ = "escalation_cases"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    case_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="open")
    summary: Mapped[str] = mapped_column(String, nullable=False)
    doctor_id: Mapped[Optional[int]] = mapped_column(Integer)
    doctor_name: Mapped[Optional[str]] = mapped_column(String(255))
    doctor_email: Mapped[Optional[str]] = mapped_column(String(255))
    urgency: Mapped[Optional[str]] = mapped_column(String(50))
    external_ticket_id: Mapped[Optional[str]] = mapped_column(String(255))
    external_ticket_url: Mapped[Optional[str]] = mapped_column(String)
    drive_file_id: Mapped[Optional[str]] = mapped_column(String(255))
    drive_file_url: Mapped[Optional[str]] = mapped_column(String)
    calendar_event_id: Mapped[Optional[str]] = mapped_column(String(255))
    calendar_event_url: Mapped[Optional[str]] = mapped_column(String)
    pharmacy_search_summary: Mapped[Optional[str]] = mapped_column(String)
    drive_path: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class MedicalMemory(Base):
    __tablename__ = "medical_memories"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_reference: Mapped[Optional[str]] = mapped_column(String(255))
    modality: Mapped[str] = mapped_column(String(50), default="text")
    embedding_model: Mapped[str] = mapped_column(String(255), nullable=False)
    embedding_vector: Mapped[str] = mapped_column(String)  # Stored as JSON string to support pgvector logic in the adapter
    summary_text: Mapped[Optional[str]] = mapped_column(String)
    drive_file_id: Mapped[Optional[str]] = mapped_column(String(255))
    drive_file_url: Mapped[Optional[str]] = mapped_column(String)
    drive_path: Mapped[Optional[str]] = mapped_column(String)
    metadata_json: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class PatientConditionSnapshot(Base):
    __tablename__ = "patient_condition_snapshots"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    snapshot_type: Mapped[str] = mapped_column(String(100), default="profile_update")
    summary: Mapped[str] = mapped_column(String, nullable=False)
    profile_json: Mapped[Optional[str]] = mapped_column(String)
    conditions_json: Mapped[Optional[str]] = mapped_column(String)
    prescriptions_json: Mapped[Optional[str]] = mapped_column(String)
    vitals_json: Mapped[Optional[str]] = mapped_column(String)
    source_event_type: Mapped[Optional[str]] = mapped_column(String(100))
    source_event_id: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class PendingAction(Base):
    __tablename__ = "pending_actions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    draft_payload_json: Mapped[Optional[str]] = mapped_column(String)
    options_json: Mapped[Optional[str]] = mapped_column(String)
    selected_option_json: Mapped[Optional[str]] = mapped_column(String)
    result_json: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

class ChatThread(Base):
    __tablename__ = "chat_threads"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    doctor_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    subject: Mapped[str] = mapped_column(String(255), default="General consultation")
    status: Mapped[str] = mapped_column(String(50), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    thread_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    sender_role: Mapped[str] = mapped_column(String(50), nullable=False)
    sender_display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class SavedDietRecipe(Base):
    __tablename__ = "saved_diet_recipes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    recipe_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class MedicationEvent(Base):
    __tablename__ = "medication_events"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    medication_name: Mapped[Optional[str]] = mapped_column(String(255))
    details: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CartItem(Base):
    __tablename__ = "cart_items"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    item_type: Mapped[str] = mapped_column(String(50), default="ingredient")  # "medicine" or "ingredient"
    price: Mapped[Optional[float]] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(50), default="checking")  # "checking", "in_stock", "out_of_stock", "price_drop"
    source_url: Mapped[Optional[str]] = mapped_column(String)
    original_price: Mapped[Optional[float]] = mapped_column(Float)
    coupon_code: Mapped[Optional[str]] = mapped_column(String(100))
    last_checked: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

