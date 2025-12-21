"""Configuration management for the GIS Architecture Agent."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # LLM Configuration
    openai_api_key: str
    anthropic_api_key: Optional[str] = None
    model_name: str = "gpt-4-turbo-preview"
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
    iplan_api_url: str = "https://ags.iplan.gov.il/arcgisiplan/rest/services/PlanningPublic/"
    
    # ArcGIS (optional)
    arcgis_username: Optional[str] = None
    arcgis_password: Optional[str] = None
    
    # Application
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
