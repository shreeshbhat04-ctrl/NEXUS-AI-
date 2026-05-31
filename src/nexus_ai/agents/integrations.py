import logging
from datetime import date
from urllib.parse import quote_plus
import zlib
import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session
import time

from nexus_ai.adapters.analytics import BigQueryAnalyticsAdapter
from nexus_ai.adapters.calendar import GoogleCalendarAdapter
from nexus_ai.adapters.drive import GoogleDriveAdapter
from nexus_ai.adapters.gmail import GoogleGmailAdapter
from nexus_ai.adapters.medical_memory import MedicalMemoryAdapter
from nexus_ai.adapters.wikipedia import WikipediaAdapter
from nexus_ai.adapters.speech import GoogleSpeechAdapter
from nexus_ai.db.models import EscalationCase, Patient, Prescription
from nexus_ai.services.google_workspace import credentials_from_tokens
from nexus_ai.services.image_classifier import ImageClassifierService, CATEGORY_FOLDER_MAP

logger = logging.getLogger(__name__)


class IntegrationAgent:
    def __init__(self) -> None:
        self.drive = GoogleDriveAdapter()
        self.calendar = GoogleCalendarAdapter()
        self.gmail = GoogleGmailAdapter()
        self.analytics = BigQueryAnalyticsAdapter()
        self.wikipedia = WikipediaAdapter()
        self.medical_memory = MedicalMemoryAdapter()
        self.image_classifier = ImageClassifierService()
        self.speech = GoogleSpeechAdapter()

    def _with_retry(self, fn, *args, **kwargs):
        attempts = max(1, self.drive.settings.integration_max_retries + 1)
        delay_seconds = self.drive.settings.integration_retry_delay_ms / 1000.0
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                return fn(*args, **kwargs)
            except Exception as error:
                last_error = error
                if attempt == attempts - 1:
                    raise
                time.sleep(delay_seconds)
        raise last_error or RuntimeError("Unknown integration retry failure.")

    def _get_patient_google_credentials(self, db: Session, patient_id: int):
        patient = db.scalar(select(Patient).where(Patient.id == patient_id))
        if not patient or not patient.google_access_token:
            return None
        return credentials_from_tokens(
            access_token=patient.google_access_token,
            refresh_token=patient.google_refresh_token,
        )

    def upload_document(
        self,
        db: Session,
        patient_id: int,
        file_path: str,
        mime_type: str,
        prescription_id: int | None = None,
        doctor_name: str | None = None,
        patient_name: str | None = None,
        document_type: str | None = None,
        disease_name: str | None = None,
        capture_date: str | None = None,
        image_category: str | None = None,
    ) -> dict:
        settings = self.drive.settings
        patient_credentials = self._get_patient_google_credentials(db, patient_id)

        # --- AI-powered image classification & subfolder routing ---
        target_folder_id: str | None = None
        drive_path: str | None = None

        resolved_capture_date = capture_date or date.today().isoformat()

        patient_record = db.scalar(select(Patient).where(Patient.id == patient_id))
        resolved_patient_name = patient_name or (patient_record.full_name if patient_record else f"patient-{patient_id}")
        resolved_doctor_name = doctor_name or "General"

        if image_category:
            resolved_image_category = image_category.upper()
        elif document_type:
            resolved_image_category = document_type.upper()
        elif settings.google_drive_classification_enabled:
            resolved_image_category = self.image_classifier.classify_medical_image(file_path)
        else:
            resolved_image_category = "OTHER"

        if settings.google_drive_folder_id:
            subfolder_name = CATEGORY_FOLDER_MAP.get(resolved_image_category, "Other")
            logger.info(
                "Image classified as %s → routing to subfolder '%s'",
                resolved_image_category,
                subfolder_name,
            )
            try:
                target_folder_id, drive_path = self._with_retry(
                    self.drive.resolve_hierarchical_folder,
                    root_folder_id=settings.google_drive_folder_id,
                    doctor_name=resolved_doctor_name,
                    patient_name=resolved_patient_name,
                    category_name=subfolder_name,
                    credentials=patient_credentials,
                )
            except Exception:
                logger.exception("Failed to resolve hierarchical subfolder — uploading to root folder")
                target_folder_id = None

        resolved_file_name = self.drive.build_storage_filename(
            disease_name=disease_name,
            capture_date=resolved_capture_date,
            mime_type=mime_type,
        )

        result = self._with_retry(
            self.drive.upload_file,
            file_path=file_path,
            mime_type=mime_type,
            folder_id=target_folder_id,
            file_name=resolved_file_name,
            credentials=patient_credentials,
        )

        # Attach the classification result to the response.
        result["image_category"] = resolved_image_category
        result["doctor_name"] = resolved_doctor_name
        result["patient_name"] = resolved_patient_name
        result["document_type"] = subfolder_name.lower()
        result["disease_name"] = disease_name
        result["capture_date"] = resolved_capture_date
        if drive_path:
            result["drive_path"] = drive_path

        if prescription_id is not None:
            prescription = db.scalar(select(Prescription).where(Prescription.id == prescription_id))
            if prescription is not None:
                prescription.document_drive_file_id = result.get("id")
                prescription.document_drive_file_url = result.get("webViewLink")
                prescription.drive_path = result.get("drive_path")
                db.commit()
        return result

    def create_calendar_event(
        self,
        db: Session,
        patient_id: int,
        summary: str,
        minutes_from_now: int,
        duration_minutes: int,
        escalation_case_id: int | None = None,
    ) -> dict:
        patient_credentials = self._get_patient_google_credentials(db, patient_id)
        result = self._with_retry(
            self.calendar.create_demo_event,
            summary=summary,
            minutes_from_now=minutes_from_now,
            duration_minutes=duration_minutes,
            credentials=patient_credentials,
        )
        if escalation_case_id is not None:
            case = db.scalar(select(EscalationCase).where(EscalationCase.id == escalation_case_id))
            if case is not None:
                case.calendar_event_id = result.get("id")
                case.calendar_event_url = result.get("htmlLink")
                db.commit()
        return result

    def log_integration_event(self, event_type: str, payload: dict) -> dict:
        try:
            return self.analytics.log_event(event_type=event_type, payload=payload)
        except Exception as error:
            return {
                "logged": False,
                "event_id": None,
                "provider": "bigquery",
                "errors": [str(error)],
            }

    def lookup_drug_label(self, medication_name: str) -> dict:
        return self._with_retry(self.wikipedia.lookup_drug_label, medication_name)

    @staticmethod
    def _format_location_label(
        location_query: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> str:
        if location_query and location_query.strip():
            return location_query.strip()
        if latitude is not None and longitude is not None:
            return f"{latitude:.4f}, {longitude:.4f}"
        return "current area"

    @staticmethod
    def _build_google_maps_link(query: str) -> str:
        return f"https://www.google.com/maps/search/?api=1&query={quote_plus(query)}"

    @staticmethod
    def _build_google_maps_directions(origin: str, destination: str) -> str:
        return (
            "https://www.google.com/maps/dir/?api=1"
            f"&origin={quote_plus(origin)}"
            f"&destination={quote_plus(destination)}"
        )

    @staticmethod
    def _deterministic_seed(*parts: str) -> int:
        joined = "|".join(parts)
        return zlib.crc32(joined.encode("utf-8")) or 1

    def _allow_synthetic_maps(self) -> bool:
        settings = self.drive.settings
        return settings.use_synthetic_maps and settings.app_env != "production"

    def _search_real_care_destinations(
        self,
        normalized_type: str,
        location_label: str,
        context_name: str,
    ) -> dict | None:
        settings = self.drive.settings
        if not settings.google_maps_api_key:
            return None

        query = f"{normalized_type} near {location_label}"
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                "https://maps.googleapis.com/maps/api/place/textsearch/json",
                params={"query": query, "key": settings.google_maps_api_key},
            )
            response.raise_for_status()
            payload = response.json()

        places = payload.get("results", [])[:3]
        destinations = []
        for place in places:
            name = place.get("name") or f"Nearby {normalized_type.title()}"
            address = place.get("formatted_address") or location_label
            destination_query = f"{name}, {address}"
            destinations.append(
                {
                    "name": name,
                    "destination_type": normalized_type,
                    "address": address,
                    "distance_km": None,
                    "eta_minutes": None,
                    "map_query": destination_query,
                    "map_url": self._build_google_maps_link(destination_query),
                    "notes": f"Live Google Maps result for {context_name} support.",
                }
            )

        return {
            "provider": "google_maps_places",
            "source_used": "google_maps_places_text_search",
            "searched_location": location_label,
            "destination_type": normalized_type,
            "summary": (
                f"Found {len(destinations)} live {normalized_type} options around {location_label} "
                "using Google Maps Places."
            ),
            "destinations": destinations,
        }

    def _build_real_care_route(
        self,
        destination_name: str,
        destination_type: str,
        origin_label: str,
        destination_label: str,
        context_hint: str,
    ) -> dict | None:
        settings = self.drive.settings
        if not settings.google_maps_api_key:
            return None

        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                "https://maps.googleapis.com/maps/api/directions/json",
                params={
                    "origin": origin_label,
                    "destination": destination_label,
                    "key": settings.google_maps_api_key,
                },
            )
            response.raise_for_status()
            payload = response.json()

        route = (payload.get("routes") or [{}])[0]
        leg = (route.get("legs") or [{}])[0]
        distance_text = (leg.get("distance") or {}).get("text")
        duration_text = (leg.get("duration") or {}).get("text")
        steps = [
            step.get("html_instructions", "").replace("<b>", "").replace("</b>", "")
            for step in leg.get("steps", [])[:5]
            if step.get("html_instructions")
        ]
        if not steps:
            steps = [f"Open Google Maps directions for live route details to {destination_name}."]

        route_url = self._build_google_maps_directions(origin_label, destination_label)
        return {
            "source_used": "google_maps_directions",
            "origin_label": origin_label,
            "destination_label": destination_name,
            "destination_type": destination_type,
            "route_summary": (
                f"Live route to {destination_name} from {origin_label}"
                f"{f' is about {distance_text}' if distance_text else ''}"
                f"{f' and {duration_text}' if duration_text else ''}."
            ),
            "estimated_minutes": None,
            "distance_km": None,
            "map_query": f"{destination_name}, {destination_label}",
            "map_url": route_url,
            "steps": [*steps, f"Keep {context_hint} context ready during check-in or pickup."],
        }

    def search_nearby_care_destinations(
        self,
        destination_type: str,
        location_query: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        medication_name: str | None = None,
        condition_name: str | None = None,
    ) -> dict:
        normalized_type = (destination_type or "pharmacy").strip().lower() or "pharmacy"
        location_label = self._format_location_label(location_query, latitude, longitude)
        context_name = medication_name or condition_name or "general care"
        real_result = self._search_real_care_destinations(normalized_type, location_label, context_name)
        if real_result is not None:
            return real_result

        if not self._allow_synthetic_maps():
            demo_locations = [
                {
                    "name": f"Demo Care {normalized_type.title()} Hub",
                    "destination_type": normalized_type,
                    "address": f"{location_label} - Demo stop 1",
                    "distance_km": 0.9,
                    "eta_minutes": 9,
                    "map_query": f"Demo Care {normalized_type.title()} Hub, {location_label}",
                    "map_url": self._build_google_maps_link(f"Demo Care {normalized_type.title()} Hub, {location_label}"),
                    "notes": f"Hardcoded demo preview for {context_name or normalized_type} support.",
                },
                {
                    "name": f"Neighbourhood {normalized_type.title()} Desk",
                    "destination_type": normalized_type,
                    "address": f"{location_label} - Demo stop 2",
                    "distance_km": 1.8,
                    "eta_minutes": 16,
                    "map_query": f"Neighbourhood {normalized_type.title()} Desk, {location_label}",
                    "map_url": self._build_google_maps_link(f"Neighbourhood {normalized_type.title()} Desk, {location_label}"),
                    "notes": "Hardcoded demo preview so the route stays populated even without map access.",
                },
                {
                    "name": f"Rapid {normalized_type.title()} Point",
                    "destination_type": normalized_type,
                    "address": f"{location_label} - Demo stop 3",
                    "distance_km": 2.7,
                    "eta_minutes": 23,
                    "map_query": f"Rapid {normalized_type.title()} Point, {location_label}",
                    "map_url": self._build_google_maps_link(f"Rapid {normalized_type.title()} Point, {location_label}"),
                    "notes": "Hardcoded demo preview for the presentation deck and backend fallback.",
                },
            ]
            return {
                "provider": "caremaze_demo_preview",
                "source_used": "caremaze_hardcoded_demo_preview",
                "searched_location": location_label,
                "destination_type": normalized_type,
                "summary": (
                    f"Hardcoded demo preview for {context_name or normalized_type} support around {location_label}. "
                    f"Three starter destinations are still shown so the screen never looks empty."
                ),
                "destinations": demo_locations,
            }

        seed = self._deterministic_seed(location_label, normalized_type, context_name)

        suffixes = ["Central", "Community", "Rapid Care"]
        destinations: list[dict] = []
        for index, suffix in enumerate(suffixes, start=1):
            distance_km = round(((seed % 9) + 2) * 0.35 + (index - 1) * 0.9, 1)
            eta_minutes = max(7, int(distance_km * 6 + index * 4))
            name = f"{location_label.split(',')[0][:24].strip() or 'Nearby'} {suffix} {normalized_type.title()}"
            address = f"{location_label} - Stop {index}"
            destination_query = f"{name}, {address}"
            destinations.append(
                {
                    "name": f"DEMO/SYNTHETIC - {name}",
                    "destination_type": normalized_type,
                    "address": f"DEMO/SYNTHETIC - {address}",
                    "distance_km": distance_km,
                    "eta_minutes": eta_minutes,
                    "map_query": destination_query,
                    "map_url": self._build_google_maps_link(destination_query),
                    "notes": (
                        f"DEMO/SYNTHETIC preview only. Recommended for {context_name} support."
                        if context_name
                        else f"DEMO/SYNTHETIC preview only. Recommended nearby {normalized_type} option."
                    ),
                }
            )

        source_used = "DEMO/SYNTHETIC caremaze_synthetic_preview"
        return {
            "provider": "DEMO/SYNTHETIC caremaze_map_agent",
            "source_used": source_used,
            "searched_location": location_label,
            "destination_type": normalized_type,
            "summary": (
                f"DEMO/SYNTHETIC preview: generated {len(destinations)} nearby {normalized_type} options around {location_label} "
                f"using {source_used}."
            ),
            "destinations": destinations,
        }

    def build_care_route(
        self,
        destination_name: str,
        destination_type: str,
        location_query: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        destination_address: str | None = None,
        medication_name: str | None = None,
        condition_name: str | None = None,
    ) -> dict:
        origin_label = self._format_location_label(location_query, latitude, longitude)
        destination_label = destination_address or destination_name
        context_hint = medication_name or condition_name or destination_type
        real_result = self._build_real_care_route(
            destination_name=destination_name,
            destination_type=destination_type,
            origin_label=origin_label,
            destination_label=destination_label,
            context_hint=context_hint,
        )
        if real_result is not None:
            return real_result

        if not self._allow_synthetic_maps():
            return {
                "source_used": "caremaze_hardcoded_demo_preview",
                "origin_label": origin_label,
                "destination_label": destination_name,
                "destination_type": destination_type,
                "route_summary": (
                    f"Hardcoded demo route from {origin_label} to {destination_name} remains available even without live maps."
                ),
                "estimated_minutes": 18,
                "distance_km": 2.4,
                "map_query": f"{destination_name}, {destination_label}",
                "map_url": self._build_google_maps_directions(origin_label, destination_label),
                "steps": [
                    f"Start from {origin_label}.",
                    f"Head to {destination_name} for {destination_type} support.",
                    f"Keep {context_hint} context ready for the handoff.",
                ],
            }

        route_seed = self._deterministic_seed(origin_label, destination_label, destination_type)
        distance_km = round(((route_seed % 11) + 3) * 0.45, 1)
        estimated_minutes = max(8, int(distance_km * 7))
        route_url = self._build_google_maps_directions(origin_label, destination_label)
        source_used = "DEMO/SYNTHETIC caremaze_synthetic_preview"
        steps = [
            f"DEMO/SYNTHETIC preview only: start from {origin_label}.",
            f"DEMO/SYNTHETIC preview only: head toward {destination_name} for {destination_type} support.",
            f"DEMO/SYNTHETIC preview only: keep {context_hint} context ready during check-in or pickup.",
        ]
        return {
            "source_used": source_used,
            "origin_label": origin_label,
            "destination_label": destination_name,
            "destination_type": destination_type,
            "route_summary": (
                f"DEMO/SYNTHETIC preview: route to {destination_name} from {origin_label} is about "
                f"{distance_km} km and {estimated_minutes} minutes."
            ),
            "estimated_minutes": estimated_minutes,
            "distance_km": distance_km,
            "map_query": f"{destination_name}, {destination_label}",
            "map_url": route_url,
            "steps": steps,
        }

    def list_drive_files(self, credentials=None, max_results: int = 5) -> list[dict]:
        try:
            return self._with_retry(
                self.drive.list_accessible_files,
                page_size=max_results,
                credentials=credentials,
            )
        except Exception as error:
            logger.error("Drive list failed: %s", error)
            return []


    def store_medical_memory(
        self,
        db: Session,
        patient_id: int,
        source_type: str,
        query_text: str | None = None,
        file_path: str | None = None,
        drive_file_id: str | None = None,
        drive_file_url: str | None = None,
        drive_path: str | None = None,
        metadata: dict | None = None,
        use_live_embedding: bool = False,
    ) -> dict:
        content, modality = self.medical_memory.build_content_from_inputs(query_text=query_text, file_path=file_path)
        embedding_vector = None
        embedding_model = None

        if use_live_embedding and content:
            try:
                from google import genai
                settings = self.drive.settings
                if settings.google_genai_use_vertexai:
                    client = genai.Client(
                        vertexai=True,
                        project=settings.google_cloud_project,
                        location=settings.google_cloud_location,
                    )
                else:
                    client = genai.Client(api_key=settings.google_api_key)

                response = client.models.embed_content(
                    model="text-embedding-004",
                    contents=content,
                )
                if response and hasattr(response, "embeddings") and response.embeddings:
                    embedding_vector = response.embeddings[0].values
                    embedding_model = "text-embedding-004"
            except Exception as err:
                logger.error("Live embedding generation failed: %s", err)

        memory, synced = self.medical_memory.store_memory(
            db=db,
            patient_id=patient_id,
            source_type=source_type,
            modality=modality,
            content=content,
            source_reference=file_path,
            drive_file_id=drive_file_id,
            drive_file_url=drive_file_url,
            drive_path=drive_path,
            metadata=metadata,
            embedding_vector=embedding_vector,
            embedding_model=embedding_model,
        )
        return {
            "memory_id": memory.id,
            "patient_id": patient_id,
            "source_type": memory.source_type,
            "modality": memory.modality,
            "embedding_model": memory.embedding_model,
            "summary_text": memory.summary_text,
            "live_embedding_used": embedding_vector is not None,
            "vector_store_synced": synced,
        }

    def search_medical_memory(
        self,
        db: Session,
        patient_id: int,
        query_text: str,
        modality: str | None = None,
        limit: int = 5,
    ) -> dict:
        results = self.medical_memory.search_similar(
            db=db,
            patient_id=patient_id,
            query_text=query_text,
            modality=modality,
            limit=limit,
        )
        return {
            "patient_id": patient_id,
            "query_text": query_text,
            "results": results,
        }

    def transcribe_audio(self, audio_bytes: bytes) -> dict:
        try:
            transcript = self._with_retry(self.speech.transcribe_audio, audio_bytes=audio_bytes)
            return {"transcript": transcript, "error": None}
        except Exception as error:
            logger.error("Audio transcription failed: %s", error)
            return {"transcript": None, "error": str(error)}

    def synthesize_speech(self, text: str) -> dict:
        try:
            audio_bytes = self._with_retry(self.speech.synthesize_speech, text=text)
            return {"audio_bytes": audio_bytes, "error": None}
        except Exception as error:
            logger.error("Speech synthesis failed: %s", error)
            return {"audio_bytes": None, "error": str(error)}

    def ensure_bigquery_table(self) -> dict:
        return self.analytics.ensure_table()

    def list_health_emails(self, credentials=None, max_results: int = 5) -> list[dict]:
        try:
            return self._with_retry(
                self.gmail.list_recent_health_emails,
                credentials=credentials,
                max_results=max_results,
            )
        except Exception as error:
            logger.error("Gmail list failed: %s", error)
            return []

    def send_care_email(self, to: str, subject: str, body_html: str, credentials=None) -> dict:
        try:
            return self._with_retry(
                self.gmail.send_care_summary,
                to=to,
                subject=subject,
                body_html=body_html,
                credentials=credentials,
            )
        except Exception as error:
            logger.error("Gmail send failed: %s", error)
            return {"sent": False, "message_id": None, "error": str(error)}

    def search_nearby_pharmacies(
        self,
        location_query: str,
        latitude: float | None = None,
        longitude: float | None = None,
        medication_name: str | None = None,
        condition_name: str | None = None,
    ) -> dict:
        result = self.search_nearby_care_destinations(
            destination_type="pharmacy",
            location_query=location_query,
            latitude=latitude,
            longitude=longitude,
            medication_name=medication_name,
            condition_name=condition_name,
        )
        return {
            "provider": result["provider"],
            "pharmacies": result["destinations"],
            "source_used": result["source_used"],
            "searched_location": result["searched_location"],
            "summary": result["summary"],
        }
