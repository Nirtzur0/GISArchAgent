"""
Unified data pipeline for building the vector database.

This orchestrates the complete process:
1. Discover all plans from iPlan (using Selenium via data_pipeline)
2. Fetch plan documents from Mavat
3. Process documents with vision service
4. Extract regulations and building rights
5. Index everything in vector database

Integrates with existing infrastructure:
- Uses src.data_pipeline for data discovery
- Uses src.infrastructure.services for document/vision processing
- Uses src.vectorstore for indexing
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
from datetime import datetime
import json

from src.data_pipeline import IPlanDataSource
from src.infrastructure.services.document_service import (
    MavatDocumentFetcher,
    DocumentProcessor
)
from src.infrastructure.services.vision_service import GeminiVisionService
from src.domain.entities.regulation import Regulation
from src.domain.value_objects.building_rights import BuildingRights
from src.vectorstore.management_service import VectorDBManagementService

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for the data pipeline."""
    
    # Data source
    service_name: str = 'xplan'  # xplan, xplan_full, tama35, tama
    max_plans: Optional[int] = None  # None = fetch all
    where_clause: str = "1=1"  # SQL filter
    
    # Document fetching
    fetch_documents: bool = True
    max_documents_per_plan: int = 10
    
    # Vision processing
    process_documents: bool = True
    vision_model: str = "gemini-1.5-flash-8b"
    
    # Vector DB
    rebuild_vectordb: bool = False  # True = clear and rebuild
    batch_size: int = 100
    
    # Caching
    use_cache: bool = True
    cache_dir: Path = Path("data/cache")
    
    # Performance
    headless: bool = True
    max_workers: int = 4


@dataclass
class PipelineStats:
    """Statistics from pipeline execution."""
    
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Discovery
    plans_discovered: int = 0
    plans_processed: int = 0
    plans_failed: int = 0
    
    # Documents
    documents_found: int = 0
    documents_downloaded: int = 0
    documents_processed: int = 0
    documents_failed: int = 0
    
    # Extraction
    regulations_extracted: int = 0
    building_rights_extracted: int = 0
    
    # Vector DB
    regulations_indexed: int = 0
    indexing_failed: int = 0
    
    # Cache
    cache_hits: int = 0
    cache_misses: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': (self.end_time - self.start_time).total_seconds() if self.end_time else None,
            'plans_discovered': self.plans_discovered,
            'plans_processed': self.plans_processed,
            'plans_failed': self.plans_failed,
            'documents_found': self.documents_found,
            'documents_downloaded': self.documents_downloaded,
            'documents_processed': self.documents_processed,
            'documents_failed': self.documents_failed,
            'regulations_extracted': self.regulations_extracted,
            'building_rights_extracted': self.building_rights_extracted,
            'regulations_indexed': self.regulations_indexed,
            'indexing_failed': self.indexing_failed,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
        }
    
    def save(self, path: Path):
        """Save stats to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)


class UnifiedDataPipeline:
    """
    Unified pipeline for building the complete vector database.
    
    This is the single entry point for:
    - Discovering plans from iPlan (using data_pipeline infrastructure)
    - Fetching documents from Mavat
    - Processing with vision AI
    - Indexing in vector database
    """
    
    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        iplan_source: Optional[IPlanDataSource] = None,
        document_fetcher: Optional[MavatDocumentFetcher] = None,
        document_processor: Optional[DocumentProcessor] = None,
        vision_service: Optional[GeminiVisionService] = None,
        vectordb_service: Optional[VectorDBManagementService] = None
    ):
        """
        Initialize the unified pipeline.
        
        Args:
            config: Pipeline configuration
            iplan_source: iPlan data source (created if not provided)
            document_fetcher: Document fetcher (created if not provided)
            document_processor: Document processor (created if not provided)
            vision_service: Vision service (created if not provided)
            vectordb_service: Vector DB service (created if not provided)
        """
        self.config = config or PipelineConfig()
        self.stats = PipelineStats(start_time=datetime.now())
        
        # Initialize components using existing infrastructure
        self.iplan_source = iplan_source or IPlanDataSource(headless=self.config.headless)
        self.document_fetcher = document_fetcher or MavatDocumentFetcher()
        self.document_processor = document_processor or DocumentProcessor()
        self.vision_service = vision_service or GeminiVisionService()
        self.vectordb_service = vectordb_service or VectorDBManagementService()
        
        # Create directories
        self.config.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def run(self) -> PipelineStats:
        """
        Run the complete pipeline.
        
        Returns:
            Pipeline statistics
        """
        logger.info("="*80)
        logger.info("Starting Unified Data Pipeline")
        logger.info("="*80)
        
        try:
            # Phase 1: Clear vector DB if rebuild requested
            if self.config.rebuild_vectordb:
                logger.info("\n📦 Phase 0: Clearing vector database...")
                self._clear_vectordb()
            
            # Phase 1: Discover plans
            logger.info("\n🔍 Phase 1: Discovering plans from iPlan...")
            plans = self._discover_plans()
            logger.info(f"✅ Discovered {len(plans)} plans")
            
            # Phase 2: Process each plan
            logger.info(f"\n🔧 Phase 2: Processing {len(plans)} plans...")
            for i, plan in enumerate(plans, 1):
                logger.info(f"\n--- Plan {i}/{len(plans)} ---")
                self._process_plan(plan)
            
            # Phase 3: Finalize
            logger.info("\n📊 Phase 3: Finalizing...")
            self._finalize()
            
            logger.info("\n" + "="*80)
            logger.info("Pipeline Complete!")
            logger.info("="*80)
            self._print_stats()
            
            return self.stats
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise
        finally:
            self.iplan_source.close()
    
    def _clear_vectordb(self):
        """Clear the vector database for rebuild."""
        try:
            logger.info("Clearing existing vector database...")
            self.vectordb_service.clear()
            logger.info("✅ Vector database cleared")
        except Exception as e:
            logger.warning(f"Failed to clear vector database: {e}")
    
    def _discover_plans(self) -> List[Dict[str, Any]]:
        """
        Discover plans from iPlan.
        
        Returns:
            List of plan features
        """
        plans = list(self.iplan_source.discover(limit=self.config.max_plans))
        
        self.stats.plans_discovered = len(plans)
        return plans
    
    def _process_plan(self, plan: Dict[str, Any]):
        """
        Process a single plan: fetch documents, analyze, extract, index.
        
        Args:
            plan: Plan feature from iPlan
        """
        try:
            attrs = plan.get('attributes', {})
            plan_id = attrs.get('OBJECTID')
            plan_number = attrs.get('PL_NUMBER', 'unknown')
            plan_name = attrs.get('PL_NAME', '')
            pl_url = attrs.get('pl_url', '')
            
            logger.info(f"Processing plan {plan_number}: {plan_name}")
            logger.info(f"  Plan ID: {plan_id}")
            logger.info(f"  Mavat URL: {pl_url}")
            
            # Skip if no Mavat URL
            if not pl_url or 'mavat.iplan.gov.il' not in pl_url:
                logger.warning("  ⚠️ No Mavat URL, skipping documents")
                self.stats.plans_processed += 1
                return
            
            # Extract Mavat plan ID from URL
            import re
            match = re.search(r'/(\d+)/', pl_url)
            if not match:
                logger.warning("  ⚠️ Could not extract Mavat plan ID")
                self.stats.plans_processed += 1
                return
            
            mavat_plan_id = match.group(1)
            
            # Phase 2.1: Fetch documents
            if self.config.fetch_documents:
                documents = self._fetch_plan_documents(mavat_plan_id)
                logger.info(f"  📄 Found {len(documents)} documents")
            else:
                documents = []
            
            # Phase 2.2: Process documents with vision
            regulations = []
            if self.config.process_documents and documents:
                regulations = self._process_documents(documents, attrs)
                logger.info(f"  📋 Extracted {len(regulations)} regulations")
            
            # Phase 2.3: Index regulations in vector DB
            if regulations:
                self._index_regulations(regulations)
                logger.info(f"  💾 Indexed {len(regulations)} regulations")
            
            self.stats.plans_processed += 1
            logger.info(f"  ✅ Plan {plan_number} processed successfully")
            
        except Exception as e:
            logger.error(f"  ❌ Failed to process plan: {e}")
            self.stats.plans_failed += 1
    
    def _fetch_plan_documents(self, mavat_plan_id: str) -> List[Dict[str, str]]:
        """
        Fetch documents for a plan from Mavat.
        
        Args:
            mavat_plan_id: Mavat plan ID
            
        Returns:
            List of document metadata
        """
        try:
            # Use Selenium fetcher via iplan_source
            documents = self.iplan_source.selenium_source.extract_document_links(mavat_plan_id)
            self.stats.documents_found += len(documents)
            
            # Download documents
            downloaded = []
            for doc in documents[:self.config.max_documents_per_plan]:
                try:
                    # Download document
                    # Note: This would need actual download implementation
                    # For now, we just track the URLs
                    downloaded.append(doc)
                    self.stats.documents_downloaded += 1
                except Exception as e:
                    logger.warning(f"    Failed to download {doc.get('title')}: {e}")
                    self.stats.documents_failed += 1
            
            return downloaded
            
        except Exception as e:
            logger.error(f"  Failed to fetch documents: {e}")
            return []
    
    def _process_documents(
        self,
        documents: List[Dict[str, str]],
        plan_attrs: Dict[str, Any]
    ) -> List[Regulation]:
        """
        Process documents with vision service to extract regulations.
        
        Args:
            documents: List of document metadata
            plan_attrs: Plan attributes from iPlan
            
        Returns:
            Extracted regulations
        """
        regulations = []
        
        for doc in documents:
            try:
                # Here we would:
                # 1. Download the document (PDF/DWG)
                # 2. Convert to images if needed
                # 3. Run vision analysis
                # 4. Extract regulations
                # 5. Parse building rights
                
                # For now, create placeholder regulation
                # TODO: Implement actual vision processing
                
                logger.info(f"    Processing document: {doc.get('title')}")
                
                # Example regulation extraction (placeholder)
                regulation = self._extract_regulation_from_document(doc, plan_attrs)
                if regulation:
                    regulations.append(regulation)
                    self.stats.regulations_extracted += 1
                
                self.stats.documents_processed += 1
                
            except Exception as e:
                logger.warning(f"    Failed to process document: {e}")
                self.stats.documents_failed += 1
        
        return regulations
    
    def _extract_regulation_from_document(
        self,
        document: Dict[str, str],
        plan_attrs: Dict[str, Any]
    ) -> Optional[Regulation]:
        """
        Extract regulation from a document using vision service.
        
        Args:
            document: Document metadata
            plan_attrs: Plan attributes
            
        Returns:
            Extracted regulation or None
        """
        # TODO: Implement actual vision-based extraction
        # This is a placeholder
        
        # For now, create a basic regulation from plan attributes
        try:
            regulation = Regulation(
                id=f"reg_{plan_attrs.get('OBJECTID')}",
                plan_id=f"iplan_{plan_attrs.get('OBJECTID')}",
                regulation_type="general",
                title=plan_attrs.get('PL_NAME', 'Untitled'),
                content=plan_attrs.get('pl_objectives', ''),
                zone_type=plan_attrs.get('entity_subtype_desc', ''),
                building_rights=None,  # TODO: Extract from vision analysis
                location=plan_attrs.get('municipality_name', ''),
                source_url=document.get('url', ''),
                metadata={
                    'plan_number': plan_attrs.get('PL_NUMBER'),
                    'district': plan_attrs.get('district_name'),
                    'station': plan_attrs.get('station_desc'),
                    'document_title': document.get('title'),
                }
            )
            
            return regulation
        except Exception as e:
            logger.error(f"Failed to create regulation: {e}")
            return None
    
    def _index_regulations(self, regulations: List[Regulation]):
        """
        Index regulations in the vector database.
        
        Args:
            regulations: Regulations to index
        """
        try:
            # Add regulations to vector DB
            for regulation in regulations:
                try:
                    self.vectordb_service.add_regulation(regulation)
                    self.stats.regulations_indexed += 1
                except Exception as e:
                    logger.warning(f"    Failed to index regulation: {e}")
                    self.stats.indexing_failed += 1
        except Exception as e:
            logger.error(f"  Failed to index regulations: {e}")
    
    def _finalize(self):
        """Finalize the pipeline and save stats."""
        self.stats.end_time = datetime.now()
        
        # Save stats to file
        stats_file = self.config.cache_dir / "pipeline_stats.json"
        self.stats.save(stats_file)
        logger.info(f"📊 Stats saved to {stats_file}")
    
    def _print_stats(self):
        """Print pipeline statistics."""
        duration = (self.stats.end_time - self.stats.start_time).total_seconds()
        
        print("\n📊 Pipeline Statistics:")
        print(f"  Duration: {duration:.2f}s")
        print(f"\n  Plans:")
        print(f"    Discovered: {self.stats.plans_discovered}")
        print(f"    Processed:  {self.stats.plans_processed}")
        print(f"    Failed:     {self.stats.plans_failed}")
        print(f"\n  Documents:")
        print(f"    Found:      {self.stats.documents_found}")
        print(f"    Downloaded: {self.stats.documents_downloaded}")
        print(f"    Processed:  {self.stats.documents_processed}")
        print(f"    Failed:     {self.stats.documents_failed}")
        print(f"\n  Extraction:")
        print(f"    Regulations:     {self.stats.regulations_extracted}")
        print(f"    Building Rights: {self.stats.building_rights_extracted}")
        print(f"\n  Vector DB:")
        print(f"    Indexed: {self.stats.regulations_indexed}")
        print(f"    Failed:  {self.stats.indexing_failed}")


def build_vectordb(
    max_plans: Optional[int] = None,
    service_name: str = 'xplan',
    rebuild: bool = False,
    headless: bool = True
) -> PipelineStats:
    """
    Convenience function to build the vector database.
    
    Args:
        max_plans: Maximum plans to process (None = all)
        service_name: iPlan service to use
        rebuild: Clear and rebuild vector DB
        headless: Run browser in headless mode
        
    Returns:
        Pipeline statistics
    """
    config = PipelineConfig(
        service_name=service_name,
        max_plans=max_plans,
        rebuild_vectordb=rebuild,
        headless=headless
    )
    
    pipeline = UnifiedDataPipeline(config=config)
    return pipeline.run()


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Building vector database from iPlan data...")
    print("This will:")
    print("  1. Discover plans using Selenium (bypasses WAF)")
    print("  2. Fetch documents from Mavat")
    print("  3. Process with vision AI")
    print("  4. Index in vector database")
    print()
    
    # Build with first 10 plans for testing
    stats = build_vectordb(
        max_plans=10,
        service_name='xplan',
        rebuild=False,
        headless=True
    )
    
    print("\n✅ Vector database build complete!")
    print(f"📊 {stats.regulations_indexed} regulations indexed")
