"""Generic data pipeline core module."""

from .interfaces import (
    DataSource,
    DataRecord,
    DataLoader,
    CacheProvider,
    PipelineObserver,
    PipelineConfig,
    PipelineResult,
)
from .pipeline import GenericPipeline, ConsolePipelineObserver, PipelineRegistry
from .loader import VectorDBLoader

__all__ = [
    # Interfaces
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
    # Loader
    'VectorDBLoader',
]
