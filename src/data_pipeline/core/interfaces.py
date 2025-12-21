"""
Generic data pipeline interfaces.

Defines abstract contracts for building extensible data pipelines
that can work with any data source.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Iterator
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DataRecord:
    """Generic data record with metadata."""
    id: str
    title: str
    content: str
    source: str
    metadata: Dict[str, Any]
    fetched_at: Optional[datetime] = None


class DataSource(ABC):
    """Abstract interface for any data source."""
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the name of this data source."""
        pass
    
    @abstractmethod
    def discover(self, limit: Optional[int] = None) -> Iterator[Dict[str, Any]]:
        """
        Discover available records from the source.
        
        Args:
            limit: Optional maximum number of records to discover
            
        Yields:
            Raw record dictionaries from the source
        """
        pass
    
    @abstractmethod
    def fetch_details(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch complete details for a specific record.
        
        Args:
            record_id: Unique identifier for the record
            
        Returns:
            Complete record data or None if not found
        """
        pass
    
    @abstractmethod
    def parse_record(self, raw_data: Dict[str, Any]) -> DataRecord:
        """
        Parse raw data into a standardized DataRecord.
        
        Args:
            raw_data: Raw data from the source
            
        Returns:
            Standardized DataRecord object
        """
        pass


class DataParser(ABC):
    """Abstract interface for parsing source-specific data."""
    
    @abstractmethod
    def parse(self, raw_data: Dict[str, Any]) -> DataRecord:
        """
        Parse raw data into a standardized format.
        
        Args:
            raw_data: Raw data from the source
            
        Returns:
            Standardized DataRecord
        """
        pass
    
    @abstractmethod
    def validate(self, record: DataRecord) -> bool:
        """
        Validate that a record meets quality standards.
        
        Args:
            record: DataRecord to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass


class DataLoader(ABC):
    """Abstract interface for loading data into storage."""
    
    @abstractmethod
    def load(self, records: List[DataRecord]) -> int:
        """
        Load records into storage.
        
        Args:
            records: List of DataRecord objects to load
            
        Returns:
            Number of records successfully loaded
        """
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about loaded data.
        
        Returns:
            Dictionary with statistics
        """
        pass


class CacheProvider(ABC):
    """Abstract interface for caching."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get cached value."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set cached value with optional TTL."""
        pass
    
    @abstractmethod
    def clear(self, key: Optional[str] = None):
        """Clear cache for specific key or all keys."""
        pass


class PipelineObserver(ABC):
    """Observer interface for pipeline events."""
    
    @abstractmethod
    def on_discovery_start(self, source_name: str):
        """Called when discovery starts."""
        pass
    
    @abstractmethod
    def on_discovery_progress(self, source_name: str, discovered: int):
        """Called during discovery with progress."""
        pass
    
    @abstractmethod
    def on_discovery_complete(self, source_name: str, total: int):
        """Called when discovery completes."""
        pass
    
    @abstractmethod
    def on_load_start(self, record_count: int):
        """Called when loading starts."""
        pass
    
    @abstractmethod
    def on_load_progress(self, loaded: int, total: int):
        """Called during loading with progress."""
        pass
    
    @abstractmethod
    def on_load_complete(self, loaded: int, failed: int):
        """Called when loading completes."""
        pass
    
    @abstractmethod
    def on_error(self, error: Exception, context: str):
        """Called when an error occurs."""
        pass


@dataclass
class PipelineConfig:
    """Configuration for a data pipeline."""
    source_name: str
    batch_size: int = 100
    max_records: Optional[int] = None
    use_cache: bool = True
    cache_ttl: int = 86400  # 24 hours
    parallel_fetching: bool = False
    validate_records: bool = True


@dataclass
class PipelineResult:
    """Result of a pipeline execution."""
    source_name: str
    discovered: int
    loaded: int
    failed: int
    errors: List[str]
    duration_seconds: float
    statistics: Dict[str, Any]
