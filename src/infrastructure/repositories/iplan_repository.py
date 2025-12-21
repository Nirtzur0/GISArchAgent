"""
iPlan ArcGIS Repository Implementation.

Concrete implementation of IPlanRepository using the iPlan GIS REST API.
"""

import logging
import ssl
import requests
from typing import List, Optional, Dict, Any
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning
import urllib3

from src.domain.repositories import IPlanRepository
from src.domain.entities.plan import Plan, PlanStatus, ZoneType
from src.domain.value_objects.geometry import Geometry

# Suppress SSL warnings
urllib3.disable_warnings(InsecureRequestWarning)

logger = logging.getLogger(__name__)


class IPlanGISRepository(IPlanRepository):
    """
    iPlan ArcGIS REST API repository implementation.
    
    Fetches plan data from the Israeli government iPlan system.
    """
    
    # iPlan ArcGIS Services
    SERVICES = {
        'planning': 'https://ags.iplan.gov.il/arcgis/rest/services/PlanningPublic/Xplan/MapServer/0',
        'tama_35': 'https://ags.iplan.gov.il/arcgis/rest/services/PlanningPublic/Tama35/MapServer/0',
        'tama': 'https://ags.iplan.gov.il/arcgis/rest/services/PlanningPublic/Tama/MapServer/0',
    }
    
    def __init__(self, timeout: int = 30):
        """
        Initialize repository.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self._session = requests.Session()
        self._session.verify = False  # SSL bypass for government servers
        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_by_id(self, plan_id: str) -> Optional[Plan]:
        """Get plan by ID."""
        try:
            # Query primary service
            where = f"PLAN_NUMBER = '{plan_id}' OR OBJECTID = {plan_id if plan_id.isdigit() else '0'}"
            results = self._query_service('planning', where, limit=1)
            
            if results:
                return self._map_to_entity(results[0])
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get plan {plan_id}: {e}")
            return None
    
    def search_by_location(self, location: str, limit: int = 10) -> List[Plan]:
        """Search plans by location."""
        try:
            where = f"CITY_NAME LIKE '%{location}%' OR SETTLEMENT LIKE '%{location}%'"
            results = self._query_service('planning', where, limit=limit)
            return [self._map_to_entity(r) for r in results]
        
        except Exception as e:
            logger.error(f"Failed to search by location {location}: {e}")
            return []
    
    def search_by_keyword(self, keyword: str, limit: int = 10) -> List[Plan]:
        """Search plans by keyword."""
        try:
            where = f"PLAN_NAME LIKE '%{keyword}%' OR PL_NAME_HEB LIKE '%{keyword}%'"
            results = self._query_service('planning', where, limit=limit)
            return [self._map_to_entity(r) for r in results]
        
        except Exception as e:
            logger.error(f"Failed to search by keyword {keyword}: {e}")
            return []
    
    def search_by_status(
        self, 
        status: str, 
        location: Optional[str] = None,
        limit: int = 10
    ) -> List[Plan]:
        """Search plans by status."""
        try:
            where = f"PLAN_STATUS LIKE '%{status}%'"
            
            if location:
                where += f" AND (CITY_NAME LIKE '%{location}%' OR SETTLEMENT LIKE '%{location}%')"
            
            results = self._query_service('planning', where, limit=limit)
            return [self._map_to_entity(r) for r in results]
        
        except Exception as e:
            logger.error(f"Failed to search by status: {e}")
            return []
    
    def get_plan_image(self, plan_id: str) -> Optional[bytes]:
        """Get plan map image."""
        try:
            # First get plan geometry to determine extent
            plan = self.get_by_id(plan_id)
            if not plan or not plan.extent:
                logger.warning(f"No geometry for plan {plan_id}")
                return None
            
            # Build export request
            service_url = self.SERVICES['planning'].rsplit('/', 1)[0]  # Remove layer number
            export_url = f"{service_url}/export"
            
            extent = plan.extent
            params = {
                'bbox': f"{extent['xmin']},{extent['ymin']},{extent['xmax']},{extent['ymax']}",
                'size': '800,600',
                'dpi': 96,
                'format': 'png',
                'transparent': 'true',
                'f': 'image',
                'imageSR': '2039',
                'bboxSR': '2039'
            }
            
            response = self._session.get(export_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            return response.content
        
        except Exception as e:
            logger.error(f"Failed to get image for plan {plan_id}: {e}")
            return None
    
    def _query_service(
        self, 
        service_key: str, 
        where: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query ArcGIS service.
        
        Args:
            service_key: Service identifier
            where: SQL WHERE clause
            limit: Maximum results
            
        Returns:
            List of feature dictionaries
        """
        service_url = self.SERVICES.get(service_key)
        if not service_url:
            logger.error(f"Unknown service: {service_key}")
            return []
        
        query_url = f"{service_url}/query"
        params = {
            'where': where,
            'outFields': '*',
            'returnGeometry': 'true',
            'f': 'json',
            'outSR': '2039',
            'resultRecordCount': limit
        }
        
        try:
            response = self._session.get(query_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            return data.get('features', [])
        
        except Exception as e:
            logger.error(f"Query failed for {service_key}: {e}")
            return []
    
    def _map_to_entity(self, feature: Dict[str, Any]) -> Plan:
        """
        Map ArcGIS feature to Plan entity.
        
        Args:
            feature: ArcGIS feature dictionary
            
        Returns:
            Plan entity
        """
        attrs = feature.get('attributes', {})
        geom = feature.get('geometry')
        
        # Extract extent for image export
        extent = None
        if geom:
            if 'rings' in geom and geom['rings']:
                # Calculate extent from polygon
                coords = [pt for ring in geom['rings'] for pt in ring]
                xs = [pt[0] for pt in coords]
                ys = [pt[1] for pt in coords]
                if xs and ys:
                    extent = {
                        'xmin': min(xs),
                        'ymin': min(ys),
                        'xmax': max(xs),
                        'ymax': max(ys)
                    }
        
        return Plan(
            id=str(attrs.get('PLAN_NUMBER', attrs.get('OBJECTID', ''))),
            name=attrs.get('PLAN_NAME', attrs.get('PL_NAME_HEB', 'Unnamed Plan')),
            location=attrs.get('CITY_NAME', attrs.get('SETTLEMENT', 'Unknown')),
            region=attrs.get('REGION', attrs.get('DISTRICT')),
            status=PlanStatus.from_string(attrs.get('PLAN_STATUS', '')),
            zone_type=ZoneType.from_code(attrs.get('ZONE_CODE')),
            plan_type=attrs.get('PLAN_TYPE', 'local'),
            geometry=Geometry.from_arcgis(geom) if geom else None,
            extent=extent,
            metadata=attrs,
            submitted_date=self._parse_date(attrs.get('SUBMIT_DATE')),
            approved_date=self._parse_date(attrs.get('APPROVAL_DATE')),
            effective_date=self._parse_date(attrs.get('EFFECTIVE_DATE')),
        )
    
    @staticmethod
    def _parse_date(date_value: Any) -> Optional[datetime]:
        """Parse date from various formats."""
        if not date_value:
            return None
        
        try:
            if isinstance(date_value, (int, float)):
                # Unix timestamp in milliseconds
                return datetime.fromtimestamp(date_value / 1000)
            elif isinstance(date_value, str):
                # ISO format
                return datetime.fromisoformat(date_value.replace('Z', '+00:00'))
        except Exception:
            pass
        
        return None
