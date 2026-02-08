"""
Data Fetchers - Abstract interfaces and implementations for fetching data.

Provides a pluggable architecture for fetching planning data from various sources:
- iPlan API (via Pydoll/CDP browser - bypasses WAF)
- Manual file import
- Future: MAVAT, municipal APIs, open data portals
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
    iPlan data fetcher (Legacy - deprecated).
    
    Note: Direct API access is blocked by WAF. 
    Use IPlanPydollFetcher instead for actual data fetching.
    This class is kept for backwards compatibility and documentation.
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
            "Use IPlanPydollFetcher instead."
        )
        
        return {
            "metadata": {
                "source": "iPlan API (deprecated - use IPlanPydollFetcher)",
                "endpoint": self.endpoint,
                "fetched_at": datetime.now().isoformat(),
                "status": "deprecated",
                "instructions": (
                    "Use IPlanPydollFetcher for automated data fetching "
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
        
        Method 1 (Recommended): Pydoll/CDP Browser Fetcher
        --------------------------------------------------
        Use the built-in `iplan` fetcher (registered as `IPlanPydollFetcher`)
        to fetch data through a real Chrome session.
        
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


class IPlanPydollFetcher(DataFetcher):
    """
    iPlan data fetcher using Pydoll (WAF bypass).
    
    This is the recommended way to fetch iPlan data. Uses a real browser via
    CDP (Chrome DevTools Protocol) to bypass WAF protection and access the
    iPlan API reliably.
    """
    
    def __init__(self, headless: bool = True):
        """
        Initialize Pydoll-based iPlan fetcher.
        
        Args:
            headless: Run browser in headless mode
        """
        from .pydoll_fetcher import SyncIPlanPydollSource
        self.source = SyncIPlanPydollSource(headless=headless)
    
    def fetch(
        self,
        service_name: str = 'xplan',
        max_plans: Optional[int] = None,
        where: str = "1=1"
    ) -> Dict[str, Any]:
        """
        Fetch data from iPlan using a browser (Pydoll).
        
        Args:
            service_name: Service to query (xplan, xplan_full, tama35, tama)
            max_plans: Maximum plans to fetch
            where: SQL WHERE clause for filtering
            
        Returns:
            Dict with metadata and features
        """
        try:
            plans = self.source.discover_plans(
                service_name=service_name,
                max_plans=max_plans,
                where=where
            )
            
            return {
                "metadata": {
                    "source": f"iPlan API ({service_name})",
                    "fetched_at": datetime.now().isoformat(),
                    "status": "success",
                    "count": len(plans),
                    "method": "pydoll"
                },
                "features": plans
            }
        except Exception as e:
            logger.error(f"Failed to fetch from iPlan: {e}")
            return {
                "metadata": {
                    "source": "iPlan API",
                    "fetched_at": datetime.now().isoformat(),
                    "status": "error",
                    "error": str(e)
                },
                "features": []
            }
    
    def get_source_name(self) -> str:
        """Get human-readable source name."""
        return "iPlan GIS (Pydoll)"
    
    def is_available(self) -> bool:
        """Check if Pydoll fetcher is available."""
        try:
            import pydoll  # noqa: F401
            return True
        except ImportError:
            return False
    
    def close(self):
        """Close browser resources."""
        if hasattr(self, 'source'):
            self.source.close()


# Register the Pydoll fetcher as the default iPlan fetcher
DataFetcherFactory.register_fetcher('iplan_pydoll', IPlanPydollFetcher)
DataFetcherFactory.register_fetcher('iplan', IPlanPydollFetcher)  # Make it default
