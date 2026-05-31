from datetime import datetime, timezone
from uuid import uuid4

from google.api_core.exceptions import NotFound

from nexus_ai.config import get_settings

try:
    from google.cloud import bigquery
except ImportError:  # pragma: no cover - optional runtime dependency
    bigquery = None


class BigQueryAnalyticsAdapter:
    def __init__(self) -> None:
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return bool(self.settings.bigquery_project_id and bigquery is not None)

    def ensure_table(self) -> dict:
        if not self.is_configured():
            return {"ready": False, "provider": "disabled"}

        client = bigquery.Client(project=self.settings.bigquery_project_id)
        dataset_id = f"{self.settings.bigquery_project_id}.{self.settings.bigquery_dataset_id}"
        table_id = f"{dataset_id}.{self.settings.bigquery_table_id}"

        try:
            client.get_dataset(dataset_id)
        except NotFound:
            dataset = bigquery.Dataset(dataset_id)
            dataset.location = self.settings.google_cloud_location
            client.create_dataset(dataset)

        schema = [
            bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("event_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("payload_json", "JSON", mode="NULLABLE"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        ]

        try:
            client.get_table(table_id)
        except NotFound:
            client.create_table(bigquery.Table(table_id, schema=schema))

        return {"ready": True, "provider": "bigquery", "table_id": table_id}

    def log_event(self, event_type: str, payload: dict) -> dict:
        if not self.is_configured():
            return {
                "logged": False,
                "event_id": None,
                "provider": "disabled",
            }

        self.ensure_table()
        event_id = str(uuid4())
        client = bigquery.Client(project=self.settings.bigquery_project_id)
        table_id = (
            f"{self.settings.bigquery_project_id}."
            f"{self.settings.bigquery_dataset_id}."
            f"{self.settings.bigquery_table_id}"
        )
        rows = [
            {
                "event_id": event_id,
                "event_type": event_type,
                "payload_json": payload,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ]
        table = client.get_table(table_id)
        errors = client.insert_rows(table=table, rows=rows)
        if errors:
            return {
                "logged": False,
                "event_id": event_id,
                "provider": "bigquery",
                "errors": errors,
            }
        return {
            "logged": True,
            "event_id": event_id,
            "provider": "bigquery",
        }
