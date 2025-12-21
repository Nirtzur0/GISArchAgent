"""
Real-time iPlan Data Fetcher
Queries the iPlan ArcGIS REST API on-demand without needing to scrape everything.
Includes automatic map image generation and vision analysis integration.
"""

import asyncio
import logging
import ssl
import certifi
from typing import List, Dict, Optional, Tuple
import aiohttp
import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3
from io import BytesIO

# Suppress SSL warnings when using verify=False
urllib3.disable_warnings(InsecureRequestWarning)

logger = logging.getLogger(__name__)


class IPlanRealtimeFetcher:
    """
    Real-time data fetcher for iPlan ArcGIS services.
    
    This class provides on-demand querying of the iPlan system without
    needing to scrape and cache everything. It intelligently routes queries
    to the appropriate ArcGIS REST endpoints.
    """
    
    # Known iPlan ArcGIS service endpoints
    SERVICES = {
        'planning': 'https://ags.iplan.gov.il/arcgisiplan/rest/services/PlanningPublic/xplan_without_77_78/MapServer',
        'special_plans': 'https://ags.iplan.gov.il/arcgisiplan/rest/services/PlanningPublic/Xplan_77_78/MapServer',
        'tama': 'https://ags.iplan.gov.il/arcgisiplan/rest/services/PlanningPublic/TAMA_1/MapServer',
        'tama_35': 'https://ags.iplan.gov.il/arcgisiplan/rest/services/PlanningPublic/tma_35_compilation_tasrit_mirkamim/MapServer',
        'tama_70': 'https://ags.iplan.gov.il/arcgisiplan/rest/services/PlanningPublic/tma_70/MapServer',
        'blue_lines': 'https://ags.iplan.gov.il/arcgisiplan/rest/services/PlanningPublic/ttl_all_blue_lines/MapServer',
    }
    
    def __init__(self):
        self._ssl_context = self._create_ssl_context()
        
    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context with relaxed verification."""
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        return ssl_context
    
    def search_by_keyword(self, keyword: str, service_type: Optional[str] = None) -> List[Dict]:
        """
        Search for plans/regulations by keyword across services.
        
        Args:
            keyword: Search term (e.g., "TAMA 35", "Tel Aviv", "residential")
            service_type: Optional specific service to search (e.g., 'tama', 'planning')
        
        Returns:
            List of matching features
        """
        results = []
        
        # Determine which services to search
        services_to_search = {}
        if service_type and service_type in self.SERVICES:
            services_to_search[service_type] = self.SERVICES[service_type]
        else:
            # Search relevant services based on keyword
            if 'tama' in keyword.lower() or 'תמא' in keyword.lower():
                services_to_search['tama'] = self.SERVICES['tama']
                if '35' in keyword:
                    services_to_search['tama_35'] = self.SERVICES['tama_35']
            else:
                services_to_search = self.SERVICES.copy()
        
        # Query each service
        for service_name, service_url in services_to_search.items():
            logger.info(f"Searching {service_name} for '{keyword}'")
            features = self._query_service(service_url, keyword)
            
            if features:
                for feature in features:
                    feature['_service'] = service_name
                    results.append(feature)
        
        logger.info(f"Found {len(results)} results for '{keyword}'")
        return results
    
    def _query_service(self, service_url: str, keyword: str, max_results: int = 50) -> List[Dict]:
        """
        Query a specific ArcGIS service.
        
        Args:
            service_url: Base URL of the MapServer
            keyword: Search keyword
            max_results: Maximum number of results to return
        
        Returns:
            List of features
        """
        try:
            # First, get service info to find queryable layers
            info = self._get_service_info(service_url)
            if not info or 'layers' not in info:
                return []
            
            all_features = []
            
            # Query each layer
            for layer in info['layers'][:5]:  # Limit to first 5 layers for performance
                layer_id = layer.get('id')
                layer_name = layer.get('name', '')
                
                query_url = f"{service_url}/{layer_id}/query"
                
                # Build WHERE clause based on keyword and available fields
                where_clause = self._build_where_clause(keyword, layer_name)
                
                params = {
                    'where': where_clause,
                    'outFields': '*',
                    'returnGeometry': 'false',
                    'resultRecordCount': max_results,
                    'f': 'json'
                }
                
                features = self._make_request(query_url, params)
                
                if features:
                    # Add layer context to each feature
                    for feature in features:
                        if 'attributes' in feature:
                            feature['attributes']['_layer_name'] = layer_name
                            feature['attributes']['_layer_id'] = layer_id
                    all_features.extend(features)
            
            return all_features[:max_results]
            
        except Exception as e:
            logger.error(f"Error querying service {service_url}: {e}")
            return []
    
    def _get_service_info(self, service_url: str) -> Dict:
        """Get metadata about a MapServer service."""
        try:
            params = {'f': 'json'}
            return self._make_request(service_url, params, return_json=True)
        except Exception as e:
            logger.error(f"Error getting service info from {service_url}: {e}")
            return {}
    
    def _make_request(self, url: str, params: Dict, return_json: bool = True) -> any:
        """
        Make HTTP request with SSL error handling.
        
        Args:
            url: Request URL
            params: Query parameters
            return_json: If True, return JSON response, else return features list
        
        Returns:
            Response data or features list
        """
        try:
            # Try with requests library and disabled SSL verification
            response = requests.get(
                url,
                params=params,
                verify=False,  # Bypass SSL verification
                timeout=30,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json',
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            if return_json:
                return data
            else:
                return data.get('features', [])
                
        except requests.exceptions.SSLError as e:
            logger.warning(f"SSL error for {url}: {e}")
            # Try alternative approach
            return self._make_request_alternative(url, params, return_json)
        except Exception as e:
            logger.error(f"Request failed for {url}: {e}")
            return {} if return_json else []
    
    def _make_request_alternative(self, url: str, params: Dict, return_json: bool) -> any:
        """Alternative request method with even more relaxed SSL."""
        try:
            import urllib.request
            import json
            from urllib.parse import urlencode
            
            # Build URL with parameters
            full_url = f"{url}?{urlencode(params)}"
            
            # Create request with no SSL verification
            context = ssl._create_unverified_context()
            req = urllib.request.Request(
                full_url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            with urllib.request.urlopen(req, context=context, timeout=30) as response:
                data = json.loads(response.read().decode())
                
            if return_json:
                return data
            else:
                return data.get('features', [])
                
        except Exception as e:
            logger.error(f"Alternative request also failed for {url}: {e}")
            return {} if return_json else []
    
    def get_plan_map_image(self, service_key: str, plan_id: str, 
                          extent: Optional[Tuple[float, float, float, float]] = None,
                          width: int = 800, height: int = 600) -> Optional[bytes]:
        """
        Fetch a map image for a specific plan from the ArcGIS MapServer.
        
        Args:
            service_key: Service identifier (e.g., 'planning', 'tama_35')
            plan_id: Plan identifier to query
            extent: Map extent as (xmin, ymin, xmax, ymax) in EPSG:2039
            width: Image width in pixels
            height: Image height in pixels
            
        Returns:
            Image bytes (PNG format) or None if failed
        """
        try:
            service_url = self.SERVICES.get(service_key)
            if not service_url:
                logger.error(f"Unknown service: {service_key}")
                return None
            
            # Build export endpoint
            export_url = f"{service_url}/export"
            
            # If no extent provided, try to get it from plan geometry
            if extent is None:
                # Query to get the plan's extent
                query_url = f"{service_url}/query"
                where_clause = f"OBJECTID = '{plan_id}'" if plan_id.isdigit() else f"PL_NUMBER = '{plan_id}'"
                
                params = {
                    'where': where_clause,
                    'returnGeometry': 'true',
                    'returnExtentOnly': 'true',
                    'f': 'json',
                    'outSR': '2039'
                }
                
                result = self._make_request(query_url, params, return_json=True)
                
                if 'extent' in result:
                    ext = result['extent']
                    # Add 10% buffer
                    width_buf = (ext['xmax'] - ext['xmin']) * 0.1
                    height_buf = (ext['ymax'] - ext['ymin']) * 0.1
                    extent = (
                        ext['xmin'] - width_buf,
                        ext['ymin'] - height_buf,
                        ext['xmax'] + width_buf,
                        ext['ymax'] + height_buf
                    )
                else:
                    # Default extent for Israel center (in EPSG:2039)
                    extent = (180000, 620000, 220000, 680000)
            
            # Build export parameters
            export_params = {
                'bbox': f"{extent[0]},{extent[1]},{extent[2]},{extent[3]}",
                'size': f"{width},{height}",
                'dpi': 96,
                'format': 'png',
                'transparent': 'true',
                'f': 'image',
                'imageSR': '2039',
                'bboxSR': '2039'
            }
            
            # Make request for image
            response = requests.get(
                export_url,
                params=export_params,
                verify=False,
                timeout=30,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            response.raise_for_status()
            
            # Return image bytes
            return response.content
            
        except Exception as e:
            logger.error(f"Error fetching map image for plan {plan_id}: {e}")
            return None
    
    def get_plan_with_image(self, service_key: str, plan_id: str) -> Optional[Dict]:
        """
        Get plan data along with its map image.
        
        Args:
            service_key: Service identifier
            plan_id: Plan identifier
            
        Returns:
            Dict with plan data and image, or None
        """
        try:
            service_url = self.SERVICES.get(service_key)
            if not service_url:
                return None
            
            # Query plan data
            query_url = f"{service_url}/query"
            where_clause = f"OBJECTID = '{plan_id}'" if plan_id.isdigit() else f"PL_NUMBER = '{plan_id}'"
            
            params = {
                'where': where_clause,
                'outFields': '*',
                'returnGeometry': 'true',
                'f': 'json',
                'outSR': '2039'
            }
            
            features = self._make_request(query_url, params, return_json=False)
            
            if not features:
                return None
            
            feature = features[0]
            
            # Get map image
            extent = None
            if 'geometry' in feature and feature['geometry']:
                geom = feature['geometry']
                if 'rings' in geom:
                    # Polygon
                    coords = [pt for ring in geom['rings'] for pt in ring]
                    xs = [pt[0] for pt in coords]
                    ys = [pt[1] for pt in coords]
                    width_buf = (max(xs) - min(xs)) * 0.1
                    height_buf = (max(ys) - min(ys)) * 0.1
                    extent = (min(xs) - width_buf, min(ys) - height_buf, 
                             max(xs) + width_buf, max(ys) + height_buf)
            
            image_bytes = self.get_plan_map_image(service_key, plan_id, extent)
            
            return {
                'plan_data': feature['attributes'],
                'geometry': feature.get('geometry'),
                'image_bytes': image_bytes,
                'has_image': image_bytes is not None
            }
            
        except Exception as e:
            logger.error(f"Error getting plan with image: {e}")
            return None
    
    def _build_where_clause(self, keyword: str, layer_name: str = '') -> str:
        """
        Build SQL WHERE clause for ArcGIS query based on keyword.
        
        Args:
            keyword: Search keyword
            layer_name: Name of the layer being queried
        
        Returns:
            SQL WHERE clause string
        """
        # Common field names in Israeli planning layers
        common_fields = [
            'PLAN_NAME', 'PLAN_ID', 'PLAN_NUMBER', 'PLAN_STATUS',
            'CITY_NAME', 'STREET_NAME', 'TAMA_NAME', 'TAMA_NUMBER',
            'PL_NAME_HEB', 'PL_NUMBER', 'SETTLEMENT', 'LOCATION',
            'OBJECTID', 'PLAN_TYPE', 'APPROVAL_DATE'
        ]
        
        # Build OR clause for searching across multiple fields
        conditions = []
        
        # For text fields, use LIKE
        for field in common_fields:
            if 'NAME' in field or 'CITY' in field or 'STREET' in field or 'LOCATION' in field:
                conditions.append(f"UPPER({field}) LIKE UPPER('%{keyword}%')")
        
        # For number fields (TAMA numbers, plan IDs)
        if keyword.replace(' ', '').isdigit():
            number = keyword.replace(' ', '')
            for field in common_fields:
                if 'NUMBER' in field or 'ID' in field:
                    conditions.append(f"{field} = {number}")
        
        # If no conditions, return a basic filter
        if not conditions:
            return "1=1"  # Returns all records
        
        # Join conditions with OR
        where_clause = ' OR '.join(conditions[:10])  # Limit to 10 conditions for performance
        
        return where_clause
    
    def get_plan_details(self, plan_id: str, service_type: str = 'planning') -> Optional[Dict]:
        """
        Get detailed information about a specific plan.
        
        Args:
            plan_id: Plan identifier
            service_type: Which service to query
        
        Returns:
            Plan details dictionary
        """
        service_url = self.SERVICES.get(service_type)
        if not service_url:
            logger.error(f"Unknown service type: {service_type}")
            return None
        
        # Query for specific plan
        results = self._query_service(service_url, plan_id, max_results=1)
        
        if results:
            return results[0]
        return None
    
    def get_plans_by_location(self, city: str, street: Optional[str] = None) -> List[Dict]:
        """
        Get all plans for a specific location.
        
        Args:
            city: City name (Hebrew or English)
            street: Optional street name
        
        Returns:
            List of plans for that location
        """
        keyword = city
        if street:
            keyword = f"{city} {street}"
        
        return self.search_by_keyword(keyword, service_type='planning')
    
    def get_tama_plans(self, tama_number: Optional[str] = None) -> List[Dict]:
        """
        Get TAMA (National Outline Plan) information.
        
        Args:
            tama_number: Optional specific TAMA number (e.g., "35", "38")
        
        Returns:
            List of TAMA plans
        """
        if tama_number:
            keyword = f"TAMA {tama_number}"
            service_type = f"tama_{tama_number}" if f"tama_{tama_number}" in self.SERVICES else 'tama'
        else:
            keyword = "TAMA"
            service_type = 'tama'
        
        return self.search_by_keyword(keyword, service_type=service_type)


# Singleton instance
_fetcher_instance = None

def get_fetcher() -> IPlanRealtimeFetcher:
    """Get or create the singleton fetcher instance."""
    global _fetcher_instance
    if _fetcher_instance is None:
        _fetcher_instance = IPlanRealtimeFetcher()
    return _fetcher_instance


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    fetcher = IPlanRealtimeFetcher()
    
    # Test searches
    print("\n=== Searching for TAMA 35 ===")
    results = fetcher.search_by_keyword("TAMA 35")
    print(f"Found {len(results)} results")
    
    print("\n=== Searching for Tel Aviv ===")
    results = fetcher.get_plans_by_location("תל אביב")
    print(f"Found {len(results)} results")
