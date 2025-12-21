"""
Discovery Service: Fetches ALL available plan metadata from iPlan API.

Uses pagination to retrieve complete dataset without hardcoded limits.
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class PlanMetadata:
    """Lightweight metadata for a planning regulation."""
    id: str
    plan_number: str
    plan_name: str
    entity_subtype: str
    municipality_name: str
    submission_date: Optional[str] = None
    approval_date: Optional[str] = None
    objectid: Optional[int] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            'id': self.id,
            'plan_number': self.plan_number,
            'plan_name': self.plan_name,
            'entity_subtype': self.entity_subtype,
            'municipality_name': self.municipality_name,
            'submission_date': self.submission_date,
            'approval_date': self.approval_date,
            'objectid': self.objectid,
        }


class DiscoveryService:
    """Discovers all available plans from iPlan API."""
    
    BASE_URL = "https://ags.iplan.gov.il/arcgisiplan/rest/services/PlanningPublic/xplan_without_77_78/MapServer/1/query"
    
    def __init__(self):
        self.discovered_plans: List[PlanMetadata] = []
    
    def discover_all_plans(self, max_records: Optional[int] = None) -> List[PlanMetadata]:
        """
        Fetch all available plan metadata from iPlan API using pagination.
        
        Args:
            max_records: Optional limit on total records to fetch (for testing)
        
        Returns:
            List of PlanMetadata objects
        """
        logger.info("Starting iPlan discovery process...")
        
        all_plans = []
        offset = 0
        page_size = 1000  # Max per request
        total_fetched = 0
        
        while True:
            # Check if we've reached the limit
            if max_records and total_fetched >= max_records:
                logger.info(f"Reached max_records limit of {max_records}")
                break
            
            # Fetch one page
            plans = self._fetch_page(offset, page_size)
            
            if not plans:
                logger.info(f"No more plans found. Total discovered: {total_fetched}")
                break
            
            all_plans.extend(plans)
            total_fetched += len(plans)
            offset += page_size
            
            logger.info(f"Fetched {len(plans)} plans (offset {offset}, total: {total_fetched})")
            
            # If we got fewer than page_size, we've reached the end
            if len(plans) < page_size:
                logger.info(f"Reached end of available data. Total: {total_fetched}")
                break
        
        self.discovered_plans = all_plans
        logger.info(f"✅ Discovery complete: {len(all_plans)} plans found")
        return all_plans
    
    def _fetch_page(self, offset: int, limit: int) -> List[PlanMetadata]:
        """
        Fetch a single page of results from iPlan API.
        
        Args:
            offset: Record offset for pagination
            limit: Number of records per page
        
        Returns:
            List of PlanMetadata objects for this page
        """
        try:
            # Import here to avoid circular dependencies
            from src.infrastructure.services.cache_service import FileCacheService
            
            # Build query parameters
            params = {
                'where': '1=1',  # Get all records
                'outFields': '*',
                'returnGeometry': 'false',
                'f': 'json',
                'resultOffset': offset,
                'resultRecordCount': limit,
            }
            
            # Build cache key
            cache_key = f"iplan_discovery_{offset}_{limit}"
            
            # Try cache first
            cache = FileCacheService()
            cached_data = cache.get(cache_key)
            
            if cached_data:
                logger.debug(f"Using cached data for offset {offset}")
                return self._parse_response(cached_data)
            
            # Fetch from API using requests (more reliable than fetch_webpage for this)
            import requests
            
            logger.debug(f"Fetching from iPlan API: offset={offset}, limit={limit}")
            response = requests.get(self.BASE_URL, params=params, timeout=30, verify=False)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache the response
            cache.set(cache_key, data, ttl=86400)  # Cache for 24 hours
            
            return self._parse_response(data)
            
        except Exception as e:
            logger.error(f"Error fetching page at offset {offset}: {e}")
            return []
    
    def _parse_response(self, data: Dict) -> List[PlanMetadata]:
        """Parse iPlan API response into PlanMetadata objects."""
        plans = []
        
        features = data.get('features', [])
        for feature in features:
            try:
                attrs = feature.get('attributes', {})
                
                # Extract required fields
                objectid = attrs.get('OBJECTID', '')
                plan_number = attrs.get('PL_NUMBER', '')
                plan_name = attrs.get('PL_NAME', '')
                entity_subtype = attrs.get('ENTITY_SUBTYPE_DESC', '')
                municipality = attrs.get('MUNICIPALITY_NAME', '')
                
                # Skip if missing critical data
                if not plan_number or not plan_name:
                    continue
                
                # Create metadata object
                metadata = PlanMetadata(
                    id=f"iplan_{objectid}",
                    plan_number=plan_number,
                    plan_name=plan_name,
                    entity_subtype=entity_subtype,
                    municipality_name=municipality,
                    submission_date=attrs.get('DEPOSITION_DATE'),
                    approval_date=attrs.get('PL_DATE_8'),
                    objectid=objectid,
                )
                
                plans.append(metadata)
                
            except Exception as e:
                logger.warning(f"Error parsing plan: {e}")
                continue
        
        return plans
    
    def get_statistics(self) -> Dict:
        """Get statistics about discovered plans."""
        if not self.discovered_plans:
            return {
                'total_plans': 0,
                'by_type': {},
                'by_municipality': {},
            }
        
        # Count by type
        type_counts = {}
        for plan in self.discovered_plans:
            type_counts[plan.entity_subtype] = type_counts.get(plan.entity_subtype, 0) + 1
        
        # Count by municipality (top 10)
        muni_counts = {}
        for plan in self.discovered_plans:
            muni_counts[plan.municipality_name] = muni_counts.get(plan.municipality_name, 0) + 1
        
        top_municipalities = dict(sorted(muni_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        
        return {
            'total_plans': len(self.discovered_plans),
            'by_type': type_counts,
            'by_municipality': top_municipalities,
        }
    
    def save_discovery_results(self, filepath: str):
        """Save discovered metadata to JSON file."""
        data = {
            'total_plans': len(self.discovered_plans),
            'plans': [plan.to_dict() for plan in self.discovered_plans],
            'statistics': self.get_statistics(),
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved discovery results to {filepath}")
    
    def load_discovery_results(self, filepath: str) -> List[PlanMetadata]:
        """Load previously discovered metadata from JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            plans = []
            for plan_dict in data.get('plans', []):
                plans.append(PlanMetadata(**plan_dict))
            
            self.discovered_plans = plans
            logger.info(f"Loaded {len(plans)} plans from {filepath}")
            return plans
            
        except Exception as e:
            logger.error(f"Error loading discovery results: {e}")
            return []
