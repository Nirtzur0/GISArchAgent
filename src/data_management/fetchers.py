"""
Data Fetchers - Abstract interfaces and implementations for fetching data.

Provides a pluggable architecture for fetching planning data from various sources:
- iPlan API (via AI assistant's fetch_webpage tool)
- Future: MAVAT, municipal APIs, open data portals
- Manual file import
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataFetcher(ABC):
    """
    Abstract base class for data fetchers.
    
    Defines the interface that all data fetchers must implement,
    allowing for easy addition of new data sources.
    """
    
    @abstractmethod
    def fetch(self, **kwargs) -> Dict[str, Any]:
        """
        Fetch data from source.
        
        Returns:
            Dict with 'metadata' and 'features' keys
        """
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Get human-readable source name."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this fetcher can currently fetch data."""
        pass


class IPlanFetcher(DataFetcher):
    """
    iPlan data fetcher.
    
    Note: Direct API access is blocked by WAF. This fetcher provides
    documentation and structure for when automated access becomes possible,
    or for manual data import workflows.
    """
    
    API_ENDPOINT = (
        "https://ags.iplan.gov.il/arcgisiplan/rest/services/"
        "PlanningPublic/xplan_without_77_78/MapServer/1/query"
    )
    
    def __init__(self):
        self.endpoint = self.API_ENDPOINT
    
    def fetch(
        self,
        where: str = "1=1",
        out_fields: str = "*",
        max_records: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Fetch data from iPlan API.
        
        Note: This is currently blocked by WAF. Use AI assistant's
        fetch_webpage tool or manual export instead.
        
        Args:
            where: SQL-like where clause
            out_fields: Fields to return (* for all)
            max_records: Maximum records to fetch
            offset: Starting offset for pagination
            
        Returns:
            Dict with metadata and features
        """
        logger.warning(
            "Direct iPlan API access is blocked by WAF. "
            "Use AI assistant's fetch_webpage tool instead."
        )
        
        return {
            "metadata": {
                "source": "iPlan API (manual fetch required)",
                "endpoint": self.endpoint,
                "fetched_at": datetime.now().isoformat(),
                "status": "requires_manual_fetch",
                "instructions": (
                    "Ask AI assistant: 'Please fetch fresh iPlan data' "
                    "or export manually from https://www.iplan.gov.il"
                )
            },
            "features": []
        }
    
    def get_source_name(self) -> str:
        return "iPlan ArcGIS REST API"
    
    def is_available(self) -> bool:
        """
        iPlan API is technically available but blocked by WAF.
        Returns False to indicate direct access is not possible.
        """
        return False
    
    def get_fetch_instructions(self) -> str:
        """Get instructions for fetching iPlan data."""
        return """
        iPlan Data Fetch Instructions:
        
        Method 1 (Recommended): AI Assistant
        -------------------------------------
        Ask: "Please fetch fresh iPlan data from the API"
        
        The AI assistant will use its fetch_webpage tool to bypass WAF
        and retrieve real planning data.
        
        Method 2: Manual Export
        -----------------------
        1. Visit https://www.iplan.gov.il
        2. Use the map interface to select plans
        3. Export as GeoJSON or CSV
        4. Import using Data Management page
        
        Method 3: Future Automated (when WAF lifted)
        ---------------------------------------------
        This code is ready for automatic fetching when access is enabled.
        Simply update is_available() to return True and implement
        the HTTP request logic.
        """


class ManualFileFetcher(DataFetcher):
    """
    Fetcher for manually provided files.
    
    Allows importing data from exported GeoJSON, JSON, or CSV files.
    """
    
    def __init__(self):
        pass
    
    def fetch(self, file_path: str, format: str = "geojson") -> Dict[str, Any]:
        """
        Load data from a file.
        
        Args:
            file_path: Path to data file
            format: File format ('geojson', 'json', 'csv')
            
        Returns:
            Dict with metadata and features
        """
        import json
        from pathlib import Path
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Normalize format
        if isinstance(data, dict):
            if "features" in data:
                features = data["features"]
            elif "type" in data and data["type"] == "FeatureCollection":
                features = data.get("features", [])
            else:
                features = [data]
        elif isinstance(data, list):
            features = data
        else:
            raise ValueError(f"Unsupported data format in {file_path}")
        
        return {
            "metadata": {
                "source": f"Manual file import: {file_path.name}",
                "fetched_at": datetime.now().isoformat(),
                "file_path": str(file_path),
                "format": format,
                "count": len(features)
            },
            "features": features
        }
    
    def get_source_name(self) -> str:
        return "Manual File Import"
    
    def is_available(self) -> bool:
        return True


class DataFetcherFactory:
    """
    Factory for creating data fetchers.
    
    Provides a central registry of available fetchers and
    methods to get the appropriate fetcher for a source.
    """
    
    _fetchers = {
        "iplan": IPlanFetcher,
        "manual": ManualFileFetcher,
    }
    
    @classmethod
    def get_fetcher(cls, source: str) -> DataFetcher:
        """
        Get a fetcher instance for the specified source.
        
        Args:
            source: Source name ('iplan', 'manual', etc.)
            
        Returns:
            Fetcher instance
        """
        if source not in cls._fetchers:
            raise ValueError(f"Unknown source: {source}. Available: {list(cls._fetchers.keys())}")
        
        return cls._fetchers[source]()
    
    @classmethod
    def list_sources(cls) -> List[str]:
        """Get list of available sources."""
        return list(cls._fetchers.keys())
    
    @classmethod
    def get_available_fetchers(cls) -> List[tuple[str, DataFetcher]]:
        """
        Get list of currently available fetchers.
        
        Returns:
            List of (source_name, fetcher_instance) tuples
        """
        available = []
        for source_name, fetcher_class in cls._fetchers.items():
            fetcher = fetcher_class()
            if fetcher.is_available():
                available.append((source_name, fetcher))
        return available
    
    @classmethod
    def register_fetcher(cls, name: str, fetcher_class: type):
        """
        Register a new fetcher type.
        
        Args:
            name: Source name identifier
            fetcher_class: Fetcher class (must inherit from DataFetcher)
        """
        if not issubclass(fetcher_class, DataFetcher):
            raise TypeError(f"{fetcher_class} must inherit from DataFetcher")
        
        cls._fetchers[name] = fetcher_class
        logger.info(f"Registered new fetcher: {name}")


# Future fetchers can be added here:
# class MAVATFetcher(DataFetcher): ...
# class MunicipalAPIFetcher(DataFetcher): ...
# class OpenDataFetcher(DataFetcher): ...
