"""
Application Factory

This is your one-stop shop for getting services. It handles all the wiring up
of dependencies so you don't have to worry about it.
"""

import logging
import os
from typing import Optional
from pathlib import Path
from datetime import datetime

from src.domain.repositories import IPlanRepository, IRegulationRepository
from src.infrastructure.repositories.iplan_repository import IPlanGISRepository
from src.infrastructure.repositories.chroma_repository import ChromaRegulationRepository
from src.infrastructure.services.vision_service import OpenAICompatibleVisionService
from src.infrastructure.services.llm_service import (
    OpenAICompatibleLLMService,
    probe_openai_compatible_provider,
)
from src.infrastructure.services.cache_service import FileCacheService
from src.infrastructure.services.document_service import (
    MavatDocumentFetcher,
    DocumentProcessor,
)
from src.application.services.plan_search_service import PlanSearchService
from src.application.services.regulation_query_service import RegulationQueryService
from src.application.services.building_rights_service import BuildingRightsService
from src.application.services.plan_upload_service import PlanUploadService
from src.config import settings

logger = logging.getLogger(__name__)


class ApplicationFactory:
    """
    Your service factory - ask for what you need, get it wired up properly.
    Everything's a singleton so you're not creating multiple instances.
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        chroma_persist_dir: str = "data/vectorstore",
        cache_dir: str = "data/cache",
        gemini_api_key: Optional[str] = None,
    ):
        """Set up the factory with your config."""
        resolved_api_key = openai_api_key
        if resolved_api_key is None:
            resolved_api_key = gemini_api_key
        self.openai_api_key = resolved_api_key or settings.openai_api_key
        self.openai_base_url = settings.openai_base_url.strip()
        self.openai_model = settings.openai_model
        self.openai_vision_model = settings.openai_vision_model
        self.chroma_persist_dir = chroma_persist_dir
        self.cache_dir = cache_dir

        # We keep one instance of each (singletons)
        self._plan_repository: Optional[IPlanRepository] = None
        self._regulation_repository: Optional[IRegulationRepository] = None
        self._vision_service: Optional[OpenAICompatibleVisionService] = None
        self._llm_service: Optional[OpenAICompatibleLLMService] = None
        self._cache_service: Optional[FileCacheService] = None
        self._document_fetcher: Optional[MavatDocumentFetcher] = None
        self._document_processor: Optional[DocumentProcessor] = None

        # Application services (singletons)
        self._plan_search_service: Optional[PlanSearchService] = None
        self._regulation_query_service: Optional[RegulationQueryService] = None
        self._building_rights_service: Optional[BuildingRightsService] = None
        self._plan_upload_service: Optional[PlanUploadService] = None

        logger.info("Factory ready to go!")

    def get_plan_repository(self) -> IPlanRepository:
        """Get the plan repository (talks to iPlan API)."""
        if not self._plan_repository:
            self._plan_repository = IPlanGISRepository(
                timeout=settings.iplan_request_timeout_seconds
            )
            logger.info("Plan repository created")

        return self._plan_repository

    def get_regulation_repository(self) -> IRegulationRepository:
        """Get the regulation repository (ChromaDB with vector search)."""
        if not self._regulation_repository:
            self._regulation_repository = ChromaRegulationRepository(
                persist_directory=self.chroma_persist_dir
            )
            logger.info("Regulation repository created")

            # Auto-initialize if empty
            self._ensure_vectordb_initialized()

        return self._regulation_repository

    def _ensure_vectordb_initialized(self):
        """Ensure vector database is initialized with data and perform health check."""
        # Lazy import to avoid circular dependency
        from src.vectorstore.initializer import VectorDBInitializer
        from src.vectorstore.health_check import (
            VectorDBHealthChecker,
            check_vectordb_health,
        )

        try:
            if self._regulation_repository:
                # Perform health check
                health_result = check_vectordb_health(self._regulation_repository)

                if health_result.status == "uninitialized":
                    logger.warning("Vector database is empty. Auto-initializing...")
                    initializer = VectorDBInitializer(self._regulation_repository)
                    success = initializer.initialize_with_samples()

                    if success:
                        logger.info("✓ Vector database initialized successfully")
                        # Update metadata
                        checker = VectorDBHealthChecker(self._regulation_repository)
                        checker.update_metadata()
                    else:
                        logger.error("✗ Failed to initialize vector database")

                elif health_result.status == "critical":
                    logger.error(f"❌ Vector database health: CRITICAL")
                    for issue in health_result.issues:
                        logger.error(f"   - {issue}")
                    for rec in health_result.recommendations:
                        logger.warning(f"   💡 {rec}")

                elif health_result.status == "warning":
                    logger.warning(f"⚠️ Vector database health: WARNING")
                    logger.info(
                        f"   Regulations: {health_result.stats.get('total_regulations', 0)}"
                    )
                    if health_result.last_updated:
                        age_days = (datetime.now() - health_result.last_updated).days
                        logger.info(f"   Last updated: {age_days} days ago")
                    for issue in health_result.issues:
                        logger.warning(f"   - {issue}")

                else:  # healthy
                    logger.info(
                        f"✅ Vector database healthy: {health_result.stats.get('total_regulations', 0)} regulations"
                    )
                    if health_result.last_updated:
                        age_days = (datetime.now() - health_result.last_updated).days
                        logger.info(f"   Last updated: {age_days} days ago")

        except Exception as e:
            logger.error(f"Error checking vector database health: {e}")

    def get_vectordb_status(self) -> dict:
        """Get comprehensive vector database health status.

        Returns:
            Dictionary with detailed health information
        """
        # Lazy import to avoid circular dependency
        from src.vectorstore.health_check import check_vectordb_health

        try:
            if not self._regulation_repository:
                return {
                    "initialized": False,
                    "status": "not_created",
                    "message": "Repository not yet instantiated",
                }

            # Perform health check
            health_result = check_vectordb_health(self._regulation_repository)

            return {
                "initialized": health_result.is_healthy
                or health_result.status == "warning",
                "status": health_result.status,
                "health": "healthy"
                if (health_result.is_healthy or health_result.status == "warning")
                else "needs_initialization",
                "total_regulations": health_result.stats.get("total_regulations", 0),
                "last_updated": (
                    health_result.last_updated.isoformat()
                    if health_result.last_updated
                    else None
                ),
                "needs_refresh": health_result.needs_refresh,
                "issues": health_result.issues,
                "recommendations": health_result.recommendations,
                "collection_name": health_result.stats.get("collection_name"),
                "persist_directory": health_result.stats.get("persist_directory"),
            }
        except Exception as e:
            return {"initialized": False, "status": "error", "error": str(e)}

    def get_vision_service(self) -> Optional[OpenAICompatibleVisionService]:
        """Get the OpenAI-compatible vision service for image analysis."""
        if not self.openai_base_url:
            return None
        if not self._vision_service:
            try:
                self._vision_service = OpenAICompatibleVisionService(
                    api_key=self.openai_api_key,
                    base_url=self.openai_base_url,
                    model=self.openai_vision_model,
                )
                logger.info("Vision service created")
            except Exception as e:
                logger.error(f"Failed to create vision service: {e}")
                return None

        return self._vision_service

    def get_llm_service(self) -> Optional[OpenAICompatibleLLMService]:
        """Get OpenAI-compatible LLM service for answer synthesis."""
        if not self.openai_base_url:
            return None
        if not self._llm_service:
            try:
                self._llm_service = OpenAICompatibleLLMService(
                    api_key=self.openai_api_key,
                    base_url=self.openai_base_url,
                    model=self.openai_model,
                )
                logger.info("LLM service created")
            except Exception as e:
                logger.error(f"Failed to create LLM service: {e}")
                return None

        return self._llm_service

    def get_provider_status(self) -> dict:
        """Return OpenAI-compatible provider health for text and vision flows."""
        base_probe = probe_openai_compatible_provider(
            base_url=self.openai_base_url,
            api_key=self.openai_api_key,
            timeout_seconds=5,
        )
        return {
            "configured": bool(self.openai_base_url),
            "base_url": self.openai_base_url or None,
            "model": self.openai_model,
            "vision_model": self.openai_vision_model,
            "text": base_probe,
            "vision": dict(base_probe),
        }

    def get_cache_service(self) -> FileCacheService:
        """Get cache service instance."""
        if not self._cache_service:
            self._cache_service = FileCacheService(cache_dir=self.cache_dir)
            logger.info("Created cache service")

        return self._cache_service

    def get_plan_search_service(self) -> PlanSearchService:
        """Get plan search service."""
        if not self._plan_search_service:
            self._plan_search_service = PlanSearchService(
                plan_repository=self.get_plan_repository(),
                vision_service=self.get_vision_service(),
                cache_service=self.get_cache_service(),
            )
            logger.info("Created plan search service")

        return self._plan_search_service

    def get_regulation_query_service(self) -> RegulationQueryService:
        """Get regulation query service."""
        if not self._regulation_query_service:
            self._regulation_query_service = RegulationQueryService(
                regulation_repository=self.get_regulation_repository(),
                llm_service=self.get_llm_service(),
            )
            logger.info("Created regulation query service")

        return self._regulation_query_service

    def get_building_rights_service(self) -> BuildingRightsService:
        """Get building rights service."""
        if not self._building_rights_service:
            self._building_rights_service = BuildingRightsService(
                regulation_repo_provider=self.get_regulation_repository
            )
            logger.info("Created building rights service")

        return self._building_rights_service

    def get_document_fetcher(self) -> MavatDocumentFetcher:
        """Get document fetcher service for Mavat."""
        if not self._document_fetcher:
            self._document_fetcher = MavatDocumentFetcher()
            logger.info("Created document fetcher service")

        return self._document_fetcher

    def get_document_processor(self) -> DocumentProcessor:
        """Get document processor service."""
        if not self._document_processor:
            self._document_processor = DocumentProcessor()
            logger.info("Created document processor service")

        return self._document_processor

    def get_plan_upload_service(self) -> Optional[PlanUploadService]:
        """Get plan upload service."""
        if not self._plan_upload_service:
            vision_service = self.get_vision_service()
            if not vision_service:
                logger.warning("Vision service not available - upload service disabled")
                return None

            self._plan_upload_service = PlanUploadService(
                vision_service=vision_service,
                regulation_repo=self.get_regulation_repository(),
            )
            logger.info("Created plan upload service")

        return self._plan_upload_service

    def cleanup(self):
        """Cleanup resources."""
        # Clear expired cache
        if self._cache_service:
            self._cache_service.clear_expired()

        logger.info("Factory cleanup completed")


# Global factory instance
_factory: Optional[ApplicationFactory] = None


def get_factory() -> ApplicationFactory:
    """
    Get global factory instance.

    Returns:
        ApplicationFactory singleton
    """
    global _factory

    if not _factory:
        _factory = ApplicationFactory()

    return _factory


def reset_factory():
    """Reset factory (useful for testing)."""
    global _factory
    _factory = None
