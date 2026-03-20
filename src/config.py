"""Configuration management for the GIS Architecture Agent."""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Keep `model_name` as a first-class setting without pydantic namespace warnings.
        protected_namespaces=("settings_",),
    )

    # Canonical provider configuration.
    openai_base_url: str = ""
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_vision_model: str = "gpt-4o-mini"

    # Legacy compatibility fields retained for older docs/config only.
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    model_name: str = "gpt-4o-mini"
    llm_provider: str = "openai"
    temperature: float = 0.1
    max_tokens: int = 4000

    # LangSmith
    langchain_tracing_v2: bool = False
    langchain_api_key: Optional[str] = None
    langchain_project: str = "gis-arch-agent"

    # Vector Database
    chroma_persist_directory: str = "./data/vectorstore"
    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # iPlan System
    iplan_base_url: str = "https://ags.iplan.gov.il/xplan/"
    iplan_api_url: str = (
        "https://ags.iplan.gov.il/arcgisiplan/rest/services/PlanningPublic/"
    )
    iplan_request_timeout_seconds: int = 8

    # ArcGIS (optional)
    arcgis_username: Optional[str] = None
    arcgis_password: Optional[str] = None

    # Application
    log_level: str = "INFO"


# Global settings instance
settings = Settings()
