"""
iPlan GIS data source implementation.

Implements the generic DataSource interface for Israeli national planning database.
"""

import logging
from typing import Iterator, Dict, Any, Optional
from datetime import datetime
import requests
import urllib3

from src.infrastructure.services.cache_service import FileCacheService
from ...core.interfaces import DataSource, DataRecord

# Disable SSL warnings for iPlan API
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class IPlanDataSource(DataSource):
    """
    Data source implementation for iPlan GIS API.
    
    Fetches planning regulations from Israeli national planning database.
    """
    
    BASE_URL = "https://ags.iplan.gov.il/arcgisiplan/rest/services/PlanningPublic/xplan_without_77_78/MapServer/1/query"
    
    def __init__(self, cache: Optional[FileCacheService] = None):
        """
        Initialize iPlan data source.
        
        Args:
            cache: Optional cache service for caching responses
        """
        self.cache = cache or FileCacheService()
    
    def get_name(self) -> str:
        """Return the name of this data source."""
        return "iPlan_GIS"
    
    def discover(self, limit: Optional[int] = None) -> Iterator[Dict[str, Any]]:
        """
        Discover available plans from iPlan API with pagination.
        
        Args:
            limit: Optional maximum number of records to discover
            
        Yields:
            Raw record dictionaries from iPlan API
        """
        offset = 0
        page_size = 1000  # Max per request
        total_fetched = 0
        
        while True:
            # Check limit
            if limit and total_fetched >= limit:
                break
            
            # Fetch one page
            records = self._fetch_page(offset, page_size)
            
            if not records:
                break
            
            # Yield each record
            for record in records:
                yield record
                total_fetched += 1
                
                if limit and total_fetched >= limit:
                    break
            
            # If we got fewer than page_size, we've reached the end
            if len(records) < page_size:
                break
            
            offset += page_size
    
    def fetch_details(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch complete details for a specific plan.
        
        Args:
            record_id: The plan identifier (e.g., 'iplan_12345')
            
        Returns:
            Complete record data or None if not found
        """
        try:
            # Extract OBJECTID from plan_id
            objectid = int(record_id.replace('iplan_', ''))
        except (ValueError, AttributeError):
            logger.error(f"Invalid plan_id format: {record_id}")
            return None
        
        # Check cache first
        cache_key = f"iplan_details_{objectid}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        # Fetch from API
        try:
            params = {
                'where': f'OBJECTID={objectid}',
                'outFields': '*',
                'returnGeometry': 'true',
                'f': 'json',
            }
            
            logger.info(f"Fetching details for {record_id} (OBJECTID={objectid})")
            response = requests.get(self.BASE_URL, params=params, timeout=30, verify=False)
            response.raise_for_status()
            
            data = response.json()
            features = data.get('features', [])
            
            if not features:
                logger.warning(f"No data found for {record_id}")
                return None
            
            record = features[0]
            
            # Cache the result
            self.cache.set(cache_key, record, ttl=86400)
            
            return record
            
        except Exception as e:
            logger.error(f"Error fetching details for {record_id}: {e}")
            return None
    
    def parse_record(self, raw_data: Dict[str, Any]) -> DataRecord:
        """
        Parse iPlan API response into a standardized DataRecord.
        
        Args:
            raw_data: Raw feature data from iPlan API
            
        Returns:
            Standardized DataRecord object
        """
        attrs = raw_data.get('attributes', {})
        
        # Extract core fields
        objectid = attrs.get('OBJECTID', '')
        plan_number = attrs.get('PL_NUMBER', '')
        plan_name = attrs.get('PL_NAME', '')
        entity_subtype = attrs.get('ENTITY_SUBTYPE_DESC', '')
        municipality = attrs.get('MUNICIPALITY_NAME', '')
        
        # Build searchable content (Hebrew)
        content = f"{plan_name}\nתוכנית מספר: {plan_number}"
        if municipality:
            content += f"\nרשות: {municipality}"
        if entity_subtype:
            content += f"\nסוג: {entity_subtype}"
        
        # Additional details if available
        targets = attrs.get('PLAN_TARGETS', '')
        if targets:
            content += f"\n\nיעדים: {targets}"
        
        main_details = attrs.get('MAIN_DETAILS', '')
        if main_details:
            content += f"\n\nפרטים: {main_details}"
        
        # Build metadata
        metadata = {
            'plan_number': plan_number,
            'entity_subtype': entity_subtype,
            'municipality_name': municipality,
            'objectid': str(objectid),
            'source_system': 'iPlan GIS',
        }
        
        # Add optional fields
        optional_fields = {
            'submission_date': 'DEPOSITION_DATE',
            'approval_date': 'PL_DATE_8',
            'status': 'PL_STATUS_DESC',
            'plan_area_dunam': 'PL_AREA_DUNAM',
            'jurisdiction': 'JURISTICTION_NAME',
        }
        
        for key, field in optional_fields.items():
            value = attrs.get(field)
            if value:
                metadata[key] = str(value)
        
        # Create DataRecord
        record = DataRecord(
            id=f"iplan_{objectid}",
            title=plan_name,
            content=content,
            source="iPlan GIS",
            metadata=metadata,
            fetched_at=datetime.now()
        )
        
        return record
    
    def _fetch_page(self, offset: int, limit: int) -> list:
        """
        Fetch a single page of results from iPlan API.
        
        Args:
            offset: Record offset for pagination
            limit: Number of records per page
            
        Returns:
            List of raw feature dictionaries
        """
        # Build cache key
        cache_key = f"iplan_page_{offset}_{limit}"
        
        # Try cache first
        cached_data = self.cache.get(cache_key)
        if cached_data:
            logger.debug(f"Using cached data for offset {offset}")
            return cached_data.get('features', [])
        
        # Fetch from API
        try:
            params = {
                'where': '1=1',  # Get all records
                'outFields': '*',
                'returnGeometry': 'false',
                'f': 'json',
                'resultOffset': offset,
                'resultRecordCount': limit,
            }
            
            logger.debug(f"Fetching from iPlan API: offset={offset}, limit={limit}")
            response = requests.get(self.BASE_URL, params=params, timeout=30, verify=False)
            response.raise_for_status()
            
            data = response.json()
            features = data.get('features', [])
            
            # Cache the response
            self.cache.set(cache_key, data, ttl=86400)
            
            return features
            
        except Exception as e:
            logger.error(f"Error fetching page at offset {offset}: {e}")
            return []
