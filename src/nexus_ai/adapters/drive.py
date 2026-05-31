import logging
import re
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

from nexus_ai.config import get_settings
from nexus_ai.services.google_workspace import get_google_credentials

logger = logging.getLogger(__name__)

DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.file"]


class GoogleDriveAdapter:
    def __init__(self) -> None:
        self.settings = get_settings()
        # In-memory cache: (parent_id, folder_name) -> folder_id
        self._folder_cache: dict[tuple[str, str], str] = {}

    def _service(self, credentials: Credentials | None = None):
        creds = credentials or get_google_credentials(DRIVE_SCOPES, self.settings.google_drive_token_file)
        return build("drive", "v3", credentials=creds)

    def list_accessible_files(self, page_size: int = 10, credentials: Credentials | None = None) -> list[dict]:
        service = self._service(credentials)
        response = (
            service.files()
            .list(pageSize=page_size, fields="files(id,name,mimeType,modifiedTime,webViewLink)")
            .execute()
        )
        return response.get("files", [])

    def get_or_create_subfolder(self, parent_folder_id: str, folder_name: str, credentials: Credentials | None = None) -> str:
        """Return the Drive folder ID for *folder_name* under *parent_folder_id*.

        If the subfolder already exists it is reused; otherwise it is created.
        Results are cached for the lifetime of this adapter instance.
        """
        cache_key = (parent_folder_id, folder_name)
        if cache_key in self._folder_cache:
            return self._folder_cache[cache_key]

        service = self._service(credentials)

        # Search for an existing folder with this name under the parent.
        query = (
            f"name = '{folder_name}' "
            f"and '{parent_folder_id}' in parents "
            f"and mimeType = 'application/vnd.google-apps.folder' "
            f"and trashed = false"
        )
        results = service.files().list(q=query, fields="files(id,name)", pageSize=1).execute()
        matches = results.get("files", [])

        if matches:
            folder_id = matches[0]["id"]
            logger.info("Found existing Drive subfolder '%s' (id=%s)", folder_name, folder_id)
        else:
            # Create the subfolder.
            folder_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [parent_folder_id],
            }
            created = service.files().create(body=folder_metadata, fields="id,name").execute()
            folder_id = created["id"]
            logger.info("Created Drive subfolder '%s' (id=%s)", folder_name, folder_id)

        self._folder_cache[cache_key] = folder_id
        return folder_id

    @staticmethod
    def _slugify(value: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
        return normalized or "unknown"

    def build_storage_filename(
        self,
        disease_name: str | None,
        capture_date: str,
        mime_type: str,
    ) -> str:
        disease_slug = self._slugify(disease_name or "unknown-disease")
        extension = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/webp": ".webp",
        }.get(mime_type, ".png")
        return f"{disease_slug}_{capture_date}{extension}"

    def resolve_hierarchical_folder(
        self,
        root_folder_id: str,
        doctor_name: str,
        patient_name: str,
        category_name: str,
        credentials: Credentials | None = None,
    ) -> tuple[str, str]:
        # Ensure the Nexus_ai root folder exists under the global Drive folder ID
        nexus_ai_root = self.get_or_create_subfolder(
            parent_folder_id=root_folder_id,
            folder_name="Nexus_ai",
            credentials=credentials,
        )
        doctor_folder = self.get_or_create_subfolder(
            parent_folder_id=nexus_ai_root,
            folder_name=f"Doctor-{doctor_name}",
            credentials=credentials,
        )
        patient_folder = self.get_or_create_subfolder(
            parent_folder_id=doctor_folder,
            folder_name=f"Patient-{patient_name}",
            credentials=credentials,
        )
        category_folder = self.get_or_create_subfolder(
            parent_folder_id=patient_folder,
            folder_name=category_name,
            credentials=credentials,
        )
        return category_folder, f"Nexus_ai/Doctor-{doctor_name}/Patient-{patient_name}/{category_name}"

    def _ensure_unique_name(
        self,
        folder_id: str,
        file_name: str,
        credentials: Credentials | None = None,
    ) -> str:
        service = self._service(credentials)
        stem = Path(file_name).stem
        suffix = Path(file_name).suffix
        candidate = file_name
        version = 1

        while True:
            query = (
                f"name = '{candidate}' "
                f"and '{folder_id}' in parents "
                "and trashed = false"
            )
            results = service.files().list(q=query, fields="files(id)", pageSize=1).execute()
            matches = results.get("files", [])
            if not matches:
                return candidate
            version += 1
            candidate = f"{stem}_v{version}{suffix}"

    def upload_file(
        self,
        file_path: str,
        mime_type: str = "application/octet-stream",
        folder_id: str | None = None,
        file_name: str | None = None,
        credentials: Credentials | None = None,
    ) -> dict:
        """Upload a file to Google Drive.

        Parameters
        ----------
        folder_id:
            If provided, the file is uploaded into this specific folder.
            Otherwise falls back to the global ``GOOGLE_DRIVE_FOLDER_ID``.
        """
        service = self._service(credentials)
        path = Path(file_path)
        metadata: dict[str, object] = {"name": file_name or path.name}

        target_folder = folder_id or self.settings.google_drive_folder_id
        if target_folder:
            metadata["name"] = self._ensure_unique_name(
                folder_id=target_folder,
                file_name=str(metadata["name"]),
                credentials=credentials,
            )
            metadata["parents"] = [target_folder]

        media = MediaFileUpload(str(path), mimetype=mime_type, resumable=False)
        created = (
            service.files()
            .create(body=metadata, media_body=media, fields="id,name,webViewLink,parents")
            .execute()
        )
        return created
