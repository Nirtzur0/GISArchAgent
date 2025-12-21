"""
Detail Fetcher: Lazy loads full regulation details on demand.

Only fetches complete plan data when actually needed for display/analysis.
"""

import logging
from typing import Optional, Dict
import requests
from datetime import datetime

from src.domain.entities.regulation import Regulation, RegulationType
from src.infrastructure.services.cache_service import FileCacheService

logger = logging.getLogger(__name__)


class DetailFetcher:
    """Fetches full regulation details on demand."""
    
    BASE_URL = "https://ags.iplan.gov.il/arcgisiplan/rest/services/PlanningPublic/xplan_without_77_78/MapServer/1/query"
    
    def __init__(self):
        self.cache = FileCacheService()
    
    def fetch_full_details(self, plan_id: str, objectid: Optional[int] = None) -> Optional[Regulation]:
        """
        Fetch full details for a specific plan.
        
        Args:
            plan_id: The plan identifier (e.g., 'iplan_12345')
            objectid: Optional OBJECTID from iPlan (extracted from plan_id if not provided)
        
        Returns:
            Complete Regulation object with all details, or None if not found
        """
        # Extract OBJECTID from plan_id if not provided
        if objectid is None:
            try:
                objectid = int(plan_id.replace('iplan_', ''))
            except (ValueError, AttributeError):
                logger.error(f"Invalid plan_id format: {plan_id}")
                return None
        
        # Check cache first
        cache_key = f"iplan_details_{objectid}"
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"Using cached details for {plan_id}")
            return self._dict_to_regulation(cached)
        
        # Fetch from API
        try:
            params = {
                'where': f'OBJECTID={objectid}',
                'outFields': '*',
                'returnGeometry': 'true',
                'f': 'json',
            }
            
            logger.info(f"Fetching full details for {plan_id} (OBJECTID={objectid})")
            response = requests.get(self.BASE_URL, params=params, timeout=30, verify=False)
            response.raise_for_status()
            
            data = response.json()
            features = data.get('features', [])
            
            if not features:
                logger.warning(f"No data found for {plan_id}")
                return None
            
            # Parse the first feature
            regulation = self._parse_full_regulation(features[0], plan_id)
            
            # Cache the result
            if regulation:
                self.cache.set(cache_key, self._regulation_to_dict(regulation), ttl=86400)
            
            return regulation
            
        except Exception as e:
            logger.error(f"Error fetching details for {plan_id}: {e}")
            return None
    
    def fetch_batch_details(self, plan_ids: list[str]) -> Dict[str, Regulation]:
        """
        Fetch full details for multiple plans efficiently.
        
        Args:
            plan_ids: List of plan identifiers
        
        Returns:
            Dictionary mapping plan_id to Regulation object
        """
        results = {}
        
        for plan_id in plan_ids:
            regulation = self.fetch_full_details(plan_id)
            if regulation:
                results[plan_id] = regulation
        
        logger.info(f"Fetched details for {len(results)}/{len(plan_ids)} plans")
        return results
    
    def _parse_full_regulation(self, feature: Dict, plan_id: str) -> Optional[Regulation]:
        """
        Parse a full iPlan feature into a complete Regulation entity.
        
        Includes all available fields, geometry, and rich metadata.
        """
        try:
            attrs = feature.get('attributes', {})
            geometry = feature.get('geometry', {})
            
            # Extract core fields
            objectid = attrs.get('OBJECTID', '')
            plan_number = attrs.get('PL_NUMBER', '')
            plan_name = attrs.get('PL_NAME', '')
            entity_subtype = attrs.get('ENTITY_SUBTYPE_DESC', '')
            municipality = attrs.get('MUNICIPALITY_NAME', '')
            
            # Extract detailed information
            plan_area = attrs.get('PL_AREA_DUNAM', '')
            jurisdiction = attrs.get('JURISTICTION_NAME', '')
            status = attrs.get('PL_STATUS_DESC', '')
            targets = attrs.get('PLAN_TARGETS', '')
            main_details = attrs.get('MAIN_DETAILS', '')
            instructions = attrs.get('PL_INSTRACTIONS', '')
            
            # Build comprehensive content
            content_parts = [plan_name]
            
            if plan_number:
                content_parts.append(f"\n\n📋 מספר תוכנית: {plan_number}")
            
            if entity_subtype:
                content_parts.append(f"📂 סוג: {entity_subtype}")
            
            if municipality:
                content_parts.append(f"🏛️ רשות: {municipality}")
            
            if status:
                content_parts.append(f"📊 סטטוס: {status}")
            
            if plan_area:
                content_parts.append(f"📐 שטח: {plan_area} דונם")
            
            if targets:
                content_parts.append(f"\n\n🎯 יעדים:\n{targets}")
            
            if main_details:
                content_parts.append(f"\n\n📝 פרטים עיקריים:\n{main_details}")
            
            if instructions:
                content_parts.append(f"\n\n📜 הוראות:\n{instructions}")
            
            content = '\n'.join(content_parts)
            
            # Parse dates
            effective_date = self._parse_date(attrs.get('PL_DATE_8'))
            
            # Build rich metadata
            metadata = {
                'plan_number': plan_number,
                'entity_subtype': entity_subtype,
                'municipality_name': municipality,
                'jurisdiction': jurisdiction,
                'status': status,
                'plan_area_dunam': str(plan_area) if plan_area else '',
                'source': 'iPlan GIS',
                'objectid': str(objectid),
                'full_details': 'true',  # Flag indicating this has full details
            }
            
            # Add optional fields
            optional_fields = [
                'DEPOSITION_DATE', 'PL_LANDUSE_STRING', 'REGIONAL_COMMITTEE_NAME',
                'PL_DISTRICT_NAME', 'PL_ORDER_PRINT_VERSION', 'MAVAT_CODE',
            ]
            
            for field in optional_fields:
                value = attrs.get(field)
                if value:
                    metadata[field.lower()] = str(value)
            
            # Add geometry if present
            if geometry:
                metadata['has_geometry'] = 'true'
                if 'rings' in geometry:
                    metadata['geometry_type'] = 'polygon'
                elif 'paths' in geometry:
                    metadata['geometry_type'] = 'polyline'
                elif 'x' in geometry and 'y' in geometry:
                    metadata['geometry_type'] = 'point'
            
            # Determine regulation type
            reg_type = self._parse_regulation_type(entity_subtype)
            
            # Create complete regulation
            regulation = Regulation(
                id=plan_id,
                title=plan_name,
                content=content,
                type=reg_type,
                effective_date=effective_date,
                source_document=f"iPlan: {plan_number}",
                metadata=metadata,
            )
            
            return regulation
            
        except Exception as e:
            logger.error(f"Error parsing full regulation: {e}")
            return None
    
    def _parse_regulation_type(self, entity_subtype: str) -> RegulationType:
        """Map Hebrew entity subtype to RegulationType enum."""
        entity_subtype_lower = entity_subtype.lower() if entity_subtype else ''
        
        if any(keyword in entity_subtype_lower for keyword in ['מגורים', 'דיור', 'משכנות']):
            return RegulationType.RESIDENTIAL
        elif any(keyword in entity_subtype_lower for keyword in ['תעשיה', 'מסחר', 'משרדים', 'תעסוקה']):
            return RegulationType.COMMERCIAL
        elif any(keyword in entity_subtype_lower for keyword in ['תחבורה', 'תנועה', 'דרך', 'כביש']):
            return RegulationType.TRANSPORTATION
        elif any(keyword in entity_subtype_lower for keyword in ['שימור', 'מורשת', 'היסטורי']):
            return RegulationType.PRESERVATION
        else:
            return RegulationType.GENERAL
    
    def _parse_date(self, date_value) -> Optional[datetime]:
        """Parse date from iPlan format."""
        if not date_value:
            return None
        
        try:
            if isinstance(date_value, (int, float)):
                return datetime.fromtimestamp(date_value / 1000)
            elif isinstance(date_value, str) and date_value.isdigit():
                return datetime.fromtimestamp(int(date_value) / 1000)
        except Exception as e:
            logger.debug(f"Could not parse date: {e}")
        
        return None
    
    def _regulation_to_dict(self, regulation: Regulation) -> Dict:
        """Convert Regulation to dictionary for caching."""
        return {
            'id': regulation.id,
            'title': regulation.title,
            'content': regulation.content,
            'type': regulation.type.value,
            'effective_date': regulation.effective_date.isoformat() if regulation.effective_date else None,
            'source_document': regulation.source_document,
            'metadata': regulation.metadata,
        }
    
    def _dict_to_regulation(self, data: Dict) -> Regulation:
        """Convert dictionary to Regulation object."""
        return Regulation(
            id=data['id'],
            title=data['title'],
            content=data['content'],
            type=RegulationType(data['type']),
            effective_date=datetime.fromisoformat(data['effective_date']) if data.get('effective_date') else None,
            source_document=data['source_document'],
            metadata=data.get('metadata', {}),
        )
    
    def clear_cache(self, plan_id: Optional[str] = None):
        """
        Clear cached details.
        
        Args:
            plan_id: Optional specific plan to clear. If None, clears all.
        """
        if plan_id:
            try:
                objectid = int(plan_id.replace('iplan_', ''))
                cache_key = f"iplan_details_{objectid}"
                # CacheService doesn't have a delete method in current implementation
                logger.warning("Cache clear not fully implemented")
            except Exception as e:
                logger.error(f"Error clearing cache for {plan_id}: {e}")
        else:
            logger.warning("Bulk cache clear not implemented")
