"""
Generic data pipeline orchestrator.

Coordinates the flow: Discovery → Parsing → Loading
Works with any data source that implements the DataSource interface.
"""

import logging
import time
from typing import List, Optional
from pathlib import Path
import json
from datetime import datetime

from .interfaces import (
    DataSource, DataLoader, CacheProvider, PipelineObserver,
    PipelineConfig, PipelineResult, DataRecord
)

logger = logging.getLogger(__name__)


class ConsolePipelineObserver(PipelineObserver):
    """Simple console-based observer for pipeline events."""
    
    def on_discovery_start(self, source_name: str):
        logger.info(f"📡 Starting discovery from {source_name}...")
    
    def on_discovery_progress(self, source_name: str, discovered: int):
        if discovered % 100 == 0:
            logger.info(f"   Discovered {discovered} records...")
    
    def on_discovery_complete(self, source_name: str, total: int):
        logger.info(f"✅ Discovery complete: {total} records from {source_name}")
    
    def on_load_start(self, record_count: int):
        logger.info(f"📇 Starting to load {record_count} records...")
    
    def on_load_progress(self, loaded: int, total: int):
        if loaded % 50 == 0:
            logger.info(f"   Loaded {loaded}/{total} records...")
    
    def on_load_complete(self, loaded: int, failed: int):
        logger.info(f"✅ Loading complete: {loaded} loaded, {failed} failed")
    
    def on_error(self, error: Exception, context: str):
        logger.error(f"❌ Error in {context}: {error}")


class GenericPipeline:
    """
    Generic data pipeline that works with any data source.
    
    Usage:
        source = MyDataSource()
        loader = MyDataLoader()
        pipeline = GenericPipeline(source, loader)
        result = pipeline.run(max_records=1000)
    """
    
    def __init__(
        self,
        source: DataSource,
        loader: DataLoader,
        cache: Optional[CacheProvider] = None,
        observer: Optional[PipelineObserver] = None,
        output_dir: str = "data/processed"
    ):
        """
        Initialize the pipeline.
        
        Args:
            source: Data source implementation
            loader: Data loader implementation
            cache: Optional cache provider
            observer: Optional observer for events
            output_dir: Directory for saving discovery results
        """
        self.source = source
        self.loader = loader
        self.cache = cache
        self.observer = observer or ConsolePipelineObserver()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def run(
        self,
        config: Optional[PipelineConfig] = None,
        force_rediscover: bool = False
    ) -> PipelineResult:
        """
        Run the complete pipeline: discover → parse → load.
        
        Args:
            config: Pipeline configuration
            force_rediscover: Force rediscovery even if cached
            
        Returns:
            PipelineResult with statistics
        """
        if config is None:
            config = PipelineConfig(source_name=self.source.get_name())
        
        start_time = time.time()
        errors = []
        
        try:
            # Step 1: Discover
            records = self._discover(config, force_rediscover)
            
            if not records:
                logger.warning("No records discovered")
                return PipelineResult(
                    source_name=config.source_name,
                    discovered=0,
                    loaded=0,
                    failed=0,
                    errors=["No records discovered"],
                    duration_seconds=time.time() - start_time,
                    statistics={}
                )
            
            # Step 2: Load
            loaded = self._load(records, config)
            
            # Step 3: Statistics
            stats = self.loader.get_statistics()
            
            duration = time.time() - start_time
            
            result = PipelineResult(
                source_name=config.source_name,
                discovered=len(records),
                loaded=loaded,
                failed=len(records) - loaded,
                errors=errors,
                duration_seconds=duration,
                statistics=stats
            )
            
            logger.info(f"\n{'='*70}")
            logger.info(f"Pipeline complete in {duration:.1f}s")
            logger.info(f"  Discovered: {result.discovered}")
            logger.info(f"  Loaded: {result.loaded}")
            logger.info(f"  Failed: {result.failed}")
            logger.info(f"{'='*70}\n")
            
            return result
            
        except Exception as e:
            self.observer.on_error(e, "pipeline execution")
            duration = time.time() - start_time
            return PipelineResult(
                source_name=config.source_name,
                discovered=0,
                loaded=0,
                failed=0,
                errors=[str(e)],
                duration_seconds=duration,
                statistics={}
            )
    
    def _discover(
        self,
        config: PipelineConfig,
        force_rediscover: bool
    ) -> List[DataRecord]:
        """Discover and parse records from the source."""
        
        # Check cache first
        cache_file = self.output_dir / f"{config.source_name}_discovery.json"
        if not force_rediscover and cache_file.exists() and config.use_cache:
            logger.info(f"Loading cached discovery from {cache_file}")
            return self._load_cached_discovery(cache_file)
        
        # Discover from source
        self.observer.on_discovery_start(config.source_name)
        
        records = []
        discovered = 0
        
        for raw_data in self.source.discover(limit=config.max_records):
            try:
                # Parse the record
                record = self.source.parse_record(raw_data)
                
                # Validate if configured
                if config.validate_records:
                    # Basic validation
                    if not record.id or not record.title:
                        continue
                
                records.append(record)
                discovered += 1
                
                self.observer.on_discovery_progress(config.source_name, discovered)
                
                if config.max_records and discovered >= config.max_records:
                    break
                    
            except Exception as e:
                self.observer.on_error(e, f"parsing record {discovered}")
                continue
        
        self.observer.on_discovery_complete(config.source_name, len(records))
        
        # Save to cache
        if config.use_cache:
            self._save_discovery(records, cache_file)
        
        return records
    
    def _load(self, records: List[DataRecord], config: PipelineConfig) -> int:
        """Load records into storage."""
        self.observer.on_load_start(len(records))
        
        loaded = 0
        batch = []
        
        for i, record in enumerate(records):
            batch.append(record)
            
            if len(batch) >= config.batch_size:
                try:
                    count = self.loader.load(batch)
                    loaded += count
                    self.observer.on_load_progress(loaded, len(records))
                    batch = []
                except Exception as e:
                    self.observer.on_error(e, f"loading batch at index {i}")
                    batch = []
        
        # Load remaining
        if batch:
            try:
                count = self.loader.load(batch)
                loaded += count
            except Exception as e:
                self.observer.on_error(e, "loading final batch")
        
        self.observer.on_load_complete(loaded, len(records) - loaded)
        return loaded
    
    def _save_discovery(self, records: List[DataRecord], filepath: Path):
        """Save discovered records to cache."""
        data = {
            'discovered_at': datetime.now().isoformat(),
            'source': self.source.get_name(),
            'count': len(records),
            'records': [
                {
                    'id': r.id,
                    'title': r.title,
                    'content': r.content,
                    'source': r.source,
                    'metadata': r.metadata,
                    'fetched_at': r.fetched_at.isoformat() if r.fetched_at else None
                }
                for r in records
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved discovery cache to {filepath}")
    
    def _load_cached_discovery(self, filepath: Path) -> List[DataRecord]:
        """Load previously discovered records from cache."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        records = []
        for r in data['records']:
            fetched_at = datetime.fromisoformat(r['fetched_at']) if r.get('fetched_at') else None
            record = DataRecord(
                id=r['id'],
                title=r['title'],
                content=r['content'],
                source=r['source'],
                metadata=r['metadata'],
                fetched_at=fetched_at
            )
            records.append(record)
        
        logger.info(f"Loaded {len(records)} records from cache")
        return records


class PipelineRegistry:
    """Registry for managing multiple data sources and pipelines."""
    
    def __init__(self):
        self._sources = {}
        self._loaders = {}
    
    def register_source(self, name: str, source: DataSource):
        """Register a data source."""
        self._sources[name] = source
        logger.info(f"Registered data source: {name}")
    
    def register_loader(self, name: str, loader: DataLoader):
        """Register a data loader."""
        self._loaders[name] = loader
        logger.info(f"Registered data loader: {name}")
    
    def get_source(self, name: str) -> Optional[DataSource]:
        """Get a registered data source."""
        return self._sources.get(name)
    
    def get_loader(self, name: str) -> Optional[DataLoader]:
        """Get a registered data loader."""
        return self._loaders.get(name)
    
    def list_sources(self) -> List[str]:
        """List all registered data sources."""
        return list(self._sources.keys())
    
    def create_pipeline(
        self,
        source_name: str,
        loader_name: str,
        **kwargs
    ) -> Optional[GenericPipeline]:
        """Create a pipeline for a registered source and loader."""
        source = self.get_source(source_name)
        loader = self.get_loader(loader_name)
        
        if not source or not loader:
            logger.error(f"Source '{source_name}' or loader '{loader_name}' not found")
            return None
        
        return GenericPipeline(source, loader, **kwargs)
