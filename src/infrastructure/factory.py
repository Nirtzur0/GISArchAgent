"""
Application Factory

This is your one-stop shop for getting services. It handles all the wiring up
of dependencies so you don't have to worry about it.
"""

import logging
import os
from typing import Optional
from pathlib import Path

from src.domain.repositories import IPlanRepository, IRegulationRepository
from src.infrastructure.repositories.iplan_repository import IPlanGISRepository
from src.infrastructure.repositories.chroma_repository import ChromaRegulationRepository
from src.infrastructure.services.vision_service import GeminiVisionService
from src.infrastructure.services.cache_service import FileCacheService
from src.application.services.plan_search_service import PlanSearchService
from src.application.services.regulation_query_service import RegulationQueryService
from src.application.services.building_rights_service import BuildingRightsService
from src.vectorstore.initializer import VectorDBInitializer

logger = logging.getLogger(__name__)


class ApplicationFactory:
    """
    Your service factory - ask for what you need, get it wired up properly.
    Everything's a singleton so you're not creating multiple instances.
    """
    
    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        chroma_persist_dir: str = "data/vectorstore",
        cache_dir: str = "data/cache"
    ):
        """Set up the factory with your config."""
        self.gemini_api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        self.chroma_persist_dir = chroma_persist_dir
        self.cache_dir = cache_dir
        
        # We keep one instance of each (singletons)
        self._plan_repository: Optional[IPlanRepository] = None
        self._regulation_repository: Optional[IRegulationRepository] = None
        self._vision_service: Optional[GeminiVisionService] = None
        self._cache_service: Optional[FileCacheService] = None
        
        # Application services (singletons)
        self._plan_search_service: Optional[PlanSearchService] = None
        self._regulation_query_service: Optional[RegulationQueryService] = None
        self._building_rights_service: Optional[BuildingRightsService] = None
        
        logger.info("Factory ready to go!")
    
    def get_plan_repository(self) -> IPlanRepository:
        """Get the plan repository (talks to iPlan API)."""
        if not self._plan_repository:
            self._plan_repository = IPlanGISRepository()
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
        """Ensure vector database is initialized with data."""
        try:
            if self._regulation_repository:
                initializer = VectorDBInitializer(self._regulation_repository)
                status = initializer.get_initialization_status()
                
                if not status.get("initialized"):
                    logger.warning("Vector database is empty. Auto-initializing...")
                    success = initializer.initialize_with_samples()
                    if success:
                        logger.info("✓ Vector database initialized successfully")
                    else:
                        logger.error("✗ Failed to initialize vector database")
                else:
                    logger.info(f"Vector database ready: {status.get('total_regulations', 0)} regulations")
        except Exception as e:
            logger.error(f"Error checking vector database initialization: {e}")
    
    def get_vectordb_status(self) -> dict:
        """Get vector database initialization status.
        
        Returns:
            Dictionary with status information
        """
        try:
            if not self._regulation_repository:
                return {
                    "initialized": False,
                    "status": "not_created",
                    "message": "Repository not yet instantiated"
                }
            
            initializer = VectorDBInitializer(self._regulation_repository)
            return initializer.get_initialization_status()
        except Exception as e:
            return {
                "initialized": False,
                "status": "error",
                "error": str(e)
            }
    
    def get_vision_service(self) -> Optional[GeminiVisionService]:
        """Get the vision service (Gemini AI for image analysis)."""
        if not self._vision_service and self.gemini_api_key:
            self._vision_service = GeminiVisionService(
                api_key=self.gemini_api_key
            )
            logger.info("Vision service created")
        
        return self._vision_service
    
    def get_cache_service(self) -> FileCacheService:
        """Get cache service instance."""
        if not self._cache_service:
            self._cache_service = FileCacheService(
                cache_dir=self.cache_dir
            )
            logger.info("Created cache service")
        
        return self._cache_service
    
    def get_plan_search_service(self) -> PlanSearchService:
        """Get plan search service."""
        if not self._plan_search_service:
            self._plan_search_service = PlanSearchService(
                plan_repository=self.get_plan_repository(),
                vision_service=self.get_vision_service(),
                cache_service=self.get_cache_service()
            )
            logger.info("Created plan search service")
        
        return self._plan_search_service
    
    def get_regulation_query_service(self) -> RegulationQueryService:
        """Get regulation query service."""
        if not self._regulation_query_service:
            self._regulation_query_service = RegulationQueryService(
                regulation_repository=self.get_regulation_repository()
            )
            logger.info("Created regulation query service")
        
        return self._regulation_query_service
    
    def get_building_rights_service(self) -> BuildingRightsService:
        """Get building rights service."""
        if not self._building_rights_service:
            self._building_rights_service = BuildingRightsService(
                regulation_repository=self.get_regulation_repository()
            )
            logger.info("Created building rights service")
        
        return self._building_rights_service
    
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
