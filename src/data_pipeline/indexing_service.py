"""
Indexing Service: Stores lightweight plan metadata in vector DB for search.

Creates searchable index without loading full regulation details.
"""

import logging
from typing import List, Optional
from datetime import datetime

from src.domain.entities.regulation import Regulation, RegulationType
from src.infrastructure.repositories.chroma_repository import ChromaRegulationRepository
from .discovery_service import PlanMetadata

logger = logging.getLogger(__name__)


class IndexingService:
    """Indexes plan metadata into vector database for search."""
    
    def __init__(self, repository: ChromaRegulationRepository):
        self.repository = repository
    
    def index_plans(self, plans: List[PlanMetadata], batch_size: int = 100) -> int:
        """
        Index plan metadata into vector database.
        
        Args:
            plans: List of PlanMetadata to index
            batch_size: Number of plans to index per batch
        
        Returns:
            Number of plans successfully indexed
        """
        logger.info(f"Starting indexing of {len(plans)} plans...")
        
        indexed_count = 0
        failed_count = 0
        
        for i in range(0, len(plans), batch_size):
            batch = plans[i:i + batch_size]
            
            for plan in batch:
                try:
                    regulation = self._create_lightweight_regulation(plan)
                    self.repository.add_regulation(regulation)
                    indexed_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to index plan {plan.id}: {e}")
                    failed_count += 1
            
            logger.info(f"Indexed batch {i // batch_size + 1}: {indexed_count} total, {failed_count} failed")
        
        logger.info(f"✅ Indexing complete: {indexed_count} indexed, {failed_count} failed")
        return indexed_count
    
    def _create_lightweight_regulation(self, plan: PlanMetadata) -> Regulation:
        """
        Convert PlanMetadata to lightweight Regulation entity for vector DB.
        
        The content is just the plan name and number, searchable in Hebrew.
        Full details will be fetched on demand.
        """
        # Parse regulation type from entity_subtype
        reg_type = self._parse_regulation_type(plan.entity_subtype)
        
        # Create searchable content (lightweight)
        content = f"{plan.plan_name}\nתוכנית מספר: {plan.plan_number}"
        if plan.municipality_name:
            content += f"\nרשות: {plan.municipality_name}"
        
        # Parse dates
        effective_date = self._parse_date(plan.approval_date) if plan.approval_date else None
        
        # Create metadata
        metadata = {
            'plan_number': plan.plan_number,
            'entity_subtype': plan.entity_subtype,
            'municipality_name': plan.municipality_name,
            'source': 'iPlan GIS',
            'indexed': 'true',  # Flag to indicate this is a lightweight index
            'objectid': str(plan.objectid) if plan.objectid else '',
        }
        
        if plan.submission_date:
            metadata['submission_date'] = plan.submission_date
        
        # Create regulation entity
        regulation = Regulation(
            id=plan.id,
            title=plan.plan_name,
            content=content,
            type=reg_type,
            effective_date=effective_date,
            source_document=f"iPlan: {plan.plan_number}",
            metadata=metadata,
        )
        
        return regulation
    
    def _parse_regulation_type(self, entity_subtype: str) -> RegulationType:
        """Map Hebrew entity subtype to RegulationType enum."""
        entity_subtype_lower = entity_subtype.lower() if entity_subtype else ''
        
        # Mapping based on Hebrew keywords
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
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string from iPlan format."""
        if not date_str:
            return None
        
        try:
            # iPlan uses timestamp format (milliseconds since epoch)
            if isinstance(date_str, (int, float)):
                return datetime.fromtimestamp(date_str / 1000)
            elif isinstance(date_str, str) and date_str.isdigit():
                return datetime.fromtimestamp(int(date_str) / 1000)
            else:
                # Try standard date formats
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%dT%H:%M:%S']:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
        except Exception as e:
            logger.debug(f"Could not parse date '{date_str}': {e}")
        
        return None
    
    def rebuild_index(self, plans: List[PlanMetadata]) -> int:
        """
        Clear existing index and rebuild from scratch.
        
        Args:
            plans: List of PlanMetadata to index
        
        Returns:
            Number of plans successfully indexed
        """
        logger.info("Clearing existing index...")
        
        # Note: ChromaDB doesn't have a clear_all method in our current implementation
        # We'd need to implement this if needed
        logger.warning("Full index clear not implemented yet. Adding to existing index.")
        
        return self.index_plans(plans)
    
    def get_indexing_statistics(self) -> dict:
        """Get statistics about the indexed data."""
        try:
            stats = self.repository.get_statistics()
            return stats
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
