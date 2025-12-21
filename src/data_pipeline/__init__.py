"""
Generic data pipeline for ingesting data from multiple sources into vector database.

Architecture:
- Core: Generic interfaces and pipeline orchestrator (source-agnostic)
- Sources: Source-specific implementations (iPlan, etc.)
- CLI: Command-line tools for pipeline management

This design allows adding new data sources without changing core pipeline logic.
"""

# Core generic components
from .core import (
    DataSource,
    DataRecord,
    DataLoader,
    CacheProvider,
    PipelineObserver,
    PipelineConfig,
    PipelineResult,
    GenericPipeline,
    ConsolePipelineObserver,
    PipelineRegistry,
    VectorDBLoader,
)

# Source implementations
from .sources import IPlanDataSource

# Legacy (deprecated - use GenericPipeline instead)
from .pipeline_manager import DataPipelineManager
from .discovery_service import DiscoveryService
from .indexing_service import IndexingService
from .detail_fetcher import DetailFetcher

__all__ = [
    # Core interfaces
    'DataSource',
    'DataRecord',
    'DataLoader',
    'CacheProvider',
    'PipelineObserver',
    'PipelineConfig',
    'PipelineResult',
    # Pipeline
    'GenericPipeline',
    'ConsolePipelineObserver',
    'PipelineRegistry',
    'VectorDBLoader',
    # Sources
    'IPlanDataSource',
    # Legacy (deprecated)
    'DataPipelineManager',
    'DiscoveryService',
    'IndexingService',
    'DetailFetcher',
]
