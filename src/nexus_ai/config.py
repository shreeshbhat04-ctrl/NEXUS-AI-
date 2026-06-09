from functools import lru_cache
from typing import Literal
from urllib.parse import quote

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "nexus_ai"
    app_env: Literal["development", "test", "production"] = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://192.168.56.1:3000,http://192.168.56.1:3000/"
    app_api_key: str | None = None
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "nexus_ai"
    postgres_host: str = "127.0.0.1"
    database_url: str | None = None
    cloud_sql_connection_name: str | None = None
    cloud_sql_database: str = "postgres"
    cloud_sql_user: str = "postgres"
    cloud_sql_password: str | None = None
    voyage_api_key: str | None = None
    acute_condition_lookback_days: int = 180
    brain_gateway_mode: str = "direct"
    
    alloydb_cluster_id: str | None = None
    alloydb_instance_id: str | None = None
    google_api_key: str | None = None
    google_oauth_client_id: str | None = None
    google_oauth_client_secret: str | None = None
    google_genai_use_vertexai: bool = False
    google_cloud_project: str | None = None
    google_cloud_location: str = "us-central1"
    adk_model: str = "gemini-2.5-pro"
    google_oauth_client_file: str = "credentials/google_oauth_client.json"
    google_drive_token_file: str = "credentials/google_drive_token.json"
    google_calendar_token_file: str = "credentials/google_calendar_token.json"
    google_drive_folder_id: str | None = None
    google_drive_classification_enabled: bool = True
    google_calendar_id: str = "primary"
    bigquery_project_id: str | None = None
    bigquery_dataset_id: str = "nexus_ai"
    bigquery_table_id: str = "integration_events"
    mongodb_uri: str = "mongodb+srv://sreeshhb_db_user:<db_password>@cluster0.j6oez1.mongodb.net/?appName=Cluster0"
    mongodb_database: str = "nexus_ai_finance"
    arize_phoenix_url: str | None = None
    arize_phoenix_project: str = "cure-quest-patient-finance"
    arize_api_key: str | None = None
    arize_space_key: str | None = None

    google_maps_api_key: str | None = None
    use_synthetic_maps: bool = False

    medical_embedding_dimensions: int = 768
    medical_vector_table_name: str = "medical_memories_vector"
    gemini_fast_model_id: str = "gemini-3.1-flash-lite-preview"
    gemini_fast_fallback_model_ids: str = "gemini-2.5-flash,gemini-2.0-flash"

    mcp_server_command: str = "python"
    mcp_server_args: str = "-m nexus_ai.mcp.server"

    # gRPC Service Endpoints
    grpc_brain_host: str = "localhost"
    grpc_brain_port: int = 50061
    grpc_integration_host: str = "localhost"
    grpc_integration_port: int = 50062
    grpc_clinical_host: str = "localhost"
    grpc_clinical_port: int = 50063
    grpc_vision_host: str = "localhost"
    grpc_vision_port: int = 50064
    grpc_diet_host: str = "localhost"
    grpc_diet_port: int = 50065
    grpc_doctor_host: str = "localhost"
    grpc_doctor_port: int = 50066

    @property
    def mcp_server_arg_list(self) -> list[str]:
        return [part for part in self.mcp_server_args.split(" ") if part]

    @property
    def gemini_fast_model_candidates(self) -> list[str]:
        configured = [self.gemini_fast_model_id]
        configured.extend(
            model_id.strip()
            for model_id in self.gemini_fast_fallback_model_ids.split(",")
            if model_id.strip()
        )
        seen: set[str] = set()
        candidates: list[str] = []
        for model_id in configured:
            if model_id not in seen:
                seen.add(model_id)
                candidates.append(model_id)
        return candidates

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def database_backend_hint(self) -> str:
        return "postgresql"

    @property
    def resolved_database_url(self) -> str:
        return self.get_database_url()

    @property
    def gemini_api_key(self) -> str | None:
        return self.google_api_key

    def get_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if self.alloydb_cluster_id and self.alloydb_instance_id and self.google_cloud_project:
            return f"postgresql+psycopg://{self.postgres_user}:{quote(self.postgres_password)}@127.0.0.1:5432/{self.postgres_db}"
        return f"postgresql+psycopg://{self.postgres_user}:{quote(self.postgres_password)}@{self.postgres_host}/{self.postgres_db}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
