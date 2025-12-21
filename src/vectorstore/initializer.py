"""
Vector Database Initializer

Handles automatic initialization and population of the vector database
using the generic data pipeline.
"""

import logging
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from src.domain.entities.regulation import Regulation
from src.infrastructure.repositories.chroma_repository import ChromaRegulationRepository

logger = logging.getLogger(__name__)


class VectorDBInitializer:
    """Handles initialization of vector database using generic data pipeline."""
    
    def __init__(self, repository: ChromaRegulationRepository):
        """Initialize with a regulation repository.
        
        Args:
            repository: ChromaDB regulation repository
        """
        self.repository = repository
        self._pipeline = None
    
    @property
    def pipeline(self):
        """Lazy load generic pipeline."""
        if self._pipeline is None:
            from src.data_pipeline import (
                GenericPipeline,
                ConsolePipelineObserver,
                VectorDBLoader,
                IPlanDataSource,
            )
            from src.infrastructure.services.cache_service import FileCacheService
            
            # Create components
            cache = FileCacheService()
            source = IPlanDataSource(cache=cache)
            loader = VectorDBLoader(self.repository)
            observer = ConsolePipelineObserver()
            
            # Create pipeline
            self._pipeline = GenericPipeline(
                source=source,
                loader=loader,
                observer=observer
            )
        
        return self._pipeline
    
    def check_and_initialize(self) -> bool:
        """Check if database is initialized, and initialize if needed.
        
        Uses generic data pipeline to fetch and index real iPlan data.
        
        Returns:
            True if database is ready (was already initialized or just initialized)
        """
        if self.repository.is_initialized():
            logger.info("Vector database already initialized")
            stats = self.repository.get_statistics()
            logger.info(f"Current regulations count: {stats.get('total_regulations', 0)}")
            return True
        
        logger.warning("Vector database is empty. Running data pipeline...")
        return self.initialize_with_pipeline()
    
    def initialize_with_pipeline(self, max_records: Optional[int] = 5000) -> bool:
        """Initialize database using generic data pipeline.
        
        Args:
            max_records: Maximum number of records to fetch (default 5000 for initial load)
        
        Returns:
            True if initialization succeeded
        """
        try:
            from src.data_pipeline import PipelineConfig
            
            logger.info("🚀 Starting generic data pipeline for initialization...")
            logger.info(f"   Max records: {max_records or 'unlimited'}")
            
            # Configure pipeline
            config = PipelineConfig(
                source_name='iPlan',
                max_records=max_records,
                batch_size=50,
                use_cache=True,
            )
            
            # Run pipeline
            result = self.pipeline.run(config)
            
            if result.loaded > 0:
                logger.info(f"✅ Successfully initialized with {result.loaded} regulations")
                logger.info(f"   Duration: {result.duration_seconds:.2f}s")
                return True
            else:
                logger.error(f"Pipeline completed but no regulations were loaded")
                if result.errors:
                    logger.error(f"Errors: {result.errors[:3]}")
                return self._fallback_to_samples()
                
        except Exception as e:
            logger.error(f"Pipeline initialization failed: {e}", exc_info=True)
            return self._fallback_to_samples()
    
    def _fallback_to_samples(self) -> bool:
        """Fallback to sample data if pipeline fails."""
        try:
            logger.warning("Falling back to sample regulations...")
            from src.vectorstore.data_sources import get_sample_regulations
            
            regulations = self._create_sample_regulations()
            if not regulations:
                return False
            
            count = self.repository.add_regulations_batch(regulations)
            if count > 0:
                logger.info(f"✓ Initialized with {count} sample regulations")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Even fallback failed: {e}")
            return False
    
    def _create_sample_regulations(self) -> List[Regulation]:
        """Create Regulation entities from sample data.
        
        Returns:
            List of Regulation entities
        """
        regulations = []
        sample_data = get_sample_regulations("default")
        
        for sample in sample_data:
            reg = Regulation(
                id=sample["id"],
                type=sample["type"],
                title=sample["title"],
                content=sample["content"],
                summary=sample.get("summary"),
                jurisdiction=sample["jurisdiction"],
                effective_date=datetime.now(),
                metadata={
                    "source": "system_initialization",
                    "initialized_at": datetime.now().isoformat()
                }
            )
            regulations.append(reg)
        
        return regulations
    
    def get_initialization_status(self) -> dict:
        """Get detailed initialization status.
        
        Returns:
            Dictionary with status information
        """
        try:
            is_init = self.repository.is_initialized()
            stats = self.repository.get_statistics()
            
            return {
                "initialized": is_init,
                "total_regulations": stats.get("total_regulations", 0),
                "collection_name": stats.get("collection_name"),
                "persist_directory": stats.get("persist_directory"),
                "status": "ready" if is_init else "empty",
                "error": stats.get("error")
            }
        except Exception as e:
            return {
                "initialized": False,
                "status": "error",
                "error": str(e)
            }
