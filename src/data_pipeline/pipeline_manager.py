"""
Data Pipeline Manager: Orchestrates the complete data flow.

Coordinates: Discovery → Indexing → Lazy Loading → Caching
"""

import logging
from typing import Optional, List
from pathlib import Path

from .discovery_service import DiscoveryService, PlanMetadata
from .indexing_service import IndexingService
from .detail_fetcher import DetailFetcher
from src.infrastructure.repositories.chroma_repository import ChromaRegulationRepository
from src.domain.entities.regulation import Regulation

logger = logging.getLogger(__name__)


class DataPipelineManager:
    """
    Unified manager for the complete iPlan data pipeline.
    
    Workflow:
    1. discover() - Fetch all plan metadata from iPlan API
    2. index() - Store lightweight metadata in vector DB
    3. fetch_details() - Lazy load full details when needed
    """
    
    def __init__(self, repository: ChromaRegulationRepository, data_dir: str = "data/processed"):
        self.discovery = DiscoveryService()
        self.indexing = IndexingService(repository)
        self.detail_fetcher = DetailFetcher()
        self.repository = repository
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.discovered_metadata_file = self.data_dir / "iplan_discovered_metadata.json"
    
    def run_full_pipeline(self, max_records: Optional[int] = None, force_rediscover: bool = False) -> dict:
        """
        Run the complete data pipeline: discover → index.
        
        Args:
            max_records: Optional limit on records to process (for testing)
            force_rediscover: If True, fetch from API even if cached metadata exists
        
        Returns:
            Dictionary with pipeline statistics
        """
        logger.info("=" * 70)
        logger.info("🚀 Starting unified iPlan data pipeline")
        logger.info("=" * 70)
        
        stats = {
            'discovered': 0,
            'indexed': 0,
            'errors': [],
        }
        
        # Step 1: Discover all plans
        logger.info("\n📡 STEP 1: Discovery")
        logger.info("-" * 70)
        
        if not force_rediscover and self.discovered_metadata_file.exists():
            logger.info(f"Loading existing metadata from {self.discovered_metadata_file}")
            plans = self.discovery.load_discovery_results(str(self.discovered_metadata_file))
        else:
            logger.info("Discovering plans from iPlan API...")
            plans = self.discovery.discover_all_plans(max_records=max_records)
            
            if plans:
                self.discovery.save_discovery_results(str(self.discovered_metadata_file))
        
        stats['discovered'] = len(plans)
        
        if not plans:
            logger.error("❌ No plans discovered. Pipeline stopped.")
            return stats
        
        logger.info(f"✅ Discovered {len(plans)} plans")
        
        # Show discovery statistics
        discovery_stats = self.discovery.get_statistics()
        logger.info(f"\n📊 Discovery Statistics:")
        logger.info(f"   Total plans: {discovery_stats['total_plans']}")
        logger.info(f"   Plan types: {len(discovery_stats['by_type'])}")
        logger.info(f"   Municipalities: {len(discovery_stats['by_municipality'])}")
        
        # Show top municipalities
        logger.info(f"\n🏛️  Top Municipalities:")
        for muni, count in list(discovery_stats['by_municipality'].items())[:5]:
            logger.info(f"   {muni}: {count} plans")
        
        # Step 2: Index into vector DB
        logger.info("\n" + "=" * 70)
        logger.info("📇 STEP 2: Indexing")
        logger.info("-" * 70)
        
        indexed = self.indexing.index_plans(plans)
        stats['indexed'] = indexed
        
        if indexed > 0:
            logger.info(f"✅ Indexed {indexed} plans into vector database")
        else:
            logger.error("❌ Failed to index plans")
            stats['errors'].append("Indexing failed")
        
        # Final statistics
        logger.info("\n" + "=" * 70)
        logger.info("📈 PIPELINE COMPLETE")
        logger.info("=" * 70)
        logger.info(f"✅ Discovered: {stats['discovered']} plans")
        logger.info(f"✅ Indexed: {stats['indexed']} plans")
        
        if stats['errors']:
            logger.warning(f"⚠️  Errors: {len(stats['errors'])}")
            for error in stats['errors']:
                logger.warning(f"   - {error}")
        
        logger.info("\n💡 Next steps:")
        logger.info("   • Search the vector DB for specific plans")
        logger.info("   • Use detail_fetcher to load full plan data on demand")
        logger.info("   • Full details cached automatically for performance")
        logger.info("=" * 70 + "\n")
        
        return stats
    
    def discover_only(self, max_records: Optional[int] = None, save: bool = True) -> List[PlanMetadata]:
        """
        Run only the discovery phase without indexing.
        
        Args:
            max_records: Optional limit on records to fetch
            save: Whether to save results to file
        
        Returns:
            List of discovered PlanMetadata
        """
        logger.info("Running discovery only...")
        plans = self.discovery.discover_all_plans(max_records=max_records)
        
        if save and plans:
            self.discovery.save_discovery_results(str(self.discovered_metadata_file))
        
        return plans
    
    def index_only(self, plans: Optional[List[PlanMetadata]] = None) -> int:
        """
        Run only the indexing phase.
        
        Args:
            plans: Optional list of plans to index. If None, loads from saved metadata.
        
        Returns:
            Number of plans indexed
        """
        if plans is None:
            if not self.discovered_metadata_file.exists():
                logger.error("No saved metadata found. Run discover_only first.")
                return 0
            
            plans = self.discovery.load_discovery_results(str(self.discovered_metadata_file))
        
        if not plans:
            logger.error("No plans to index")
            return 0
        
        logger.info(f"Indexing {len(plans)} plans...")
        return self.indexing.index_plans(plans)
    
    def get_full_details(self, plan_id: str, objectid: Optional[int] = None) -> Optional[Regulation]:
        """
        Fetch full details for a specific plan (lazy loading).
        
        Args:
            plan_id: Plan identifier
            objectid: Optional OBJECTID from iPlan
        
        Returns:
            Complete Regulation object with all details
        """
        return self.detail_fetcher.fetch_full_details(plan_id, objectid)
    
    def search_and_fetch_details(self, query: str, limit: int = 5) -> List[Regulation]:
        """
        Search vector DB and automatically fetch full details for results.
        
        Args:
            query: Search query (Hebrew or English)
            limit: Maximum number of results
        
        Returns:
            List of Regulations with complete details
        """
        logger.info(f"Searching for: {query}")
        
        # Search the indexed metadata
        lightweight_results = self.repository.search(query, limit=limit)
        
        logger.info(f"Found {len(lightweight_results)} results in index")
        
        # Fetch full details for each result
        detailed_results = []
        for reg in lightweight_results:
            # Check if this is already a full details entry
            if reg.metadata.get('full_details') == 'true':
                detailed_results.append(reg)
                continue
            
            # Otherwise, fetch full details
            full_reg = self.detail_fetcher.fetch_full_details(
                reg.id,
                objectid=reg.metadata.get('objectid')
            )
            
            if full_reg:
                detailed_results.append(full_reg)
            else:
                # Fallback to lightweight version
                detailed_results.append(reg)
        
        logger.info(f"Returned {len(detailed_results)} results with full details")
        return detailed_results
    
    def get_pipeline_status(self) -> dict:
        """Get current status of the data pipeline."""
        status = {
            'metadata_file_exists': self.discovered_metadata_file.exists(),
            'discovered_plans': 0,
            'indexed_plans': 0,
        }
        
        # Check discovered plans
        if self.discovered_metadata_file.exists():
            plans = self.discovery.load_discovery_results(str(self.discovered_metadata_file))
            status['discovered_plans'] = len(plans)
        
        # Check indexed plans
        try:
            stats = self.repository.get_statistics()
            status['indexed_plans'] = stats.get('total_regulations', 0)
        except:
            pass
        
        return status
    
    def reset_pipeline(self):
        """Reset the entire pipeline (clear metadata and index)."""
        logger.warning("Resetting pipeline...")
        
        # Remove metadata file
        if self.discovered_metadata_file.exists():
            self.discovered_metadata_file.unlink()
            logger.info("Removed metadata file")
        
        # Note: Vector DB reset would require deleting data/vectorstore directory
        logger.warning("Vector DB must be manually reset (delete data/vectorstore)")
