"""
Generic data loader for vector database.

Loads DataRecord objects into ChromaDB vector store.
"""

import logging
from typing import List
from datetime import datetime

from src.domain.entities.regulation import Regulation, RegulationType
from src.infrastructure.repositories.chroma_repository import ChromaRegulationRepository
from ..core.interfaces import DataLoader, DataRecord

logger = logging.getLogger(__name__)


class VectorDBLoader(DataLoader):
    """Generic loader that stores DataRecords in vector database."""
    
    def __init__(self, repository: ChromaRegulationRepository):
        """
        Initialize the loader.
        
        Args:
            repository: ChromaDB repository instance
        """
        self.repository = repository
    
    def load(self, records: List[DataRecord]) -> int:
        """
        Load records into vector database.
        
        Args:
            records: List of DataRecord objects to load
            
        Returns:
            Number of records successfully loaded
        """
        regulations = []
        
        for record in records:
            try:
                regulation = self._convert_to_regulation(record)
                regulations.append(regulation)
            except Exception as e:
                logger.warning(f"Failed to convert record {record.id}: {e}")
                continue
        
        if not regulations:
            return 0
        
        # Batch load into repository
        try:
            count = self.repository.add_regulations_batch(regulations)
            return count
        except Exception as e:
            logger.error(f"Failed to load batch: {e}")
            return 0
    
    def get_statistics(self) -> dict:
        """Get statistics about loaded data."""
        try:
            return self.repository.get_statistics()
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def _convert_to_regulation(self, record: DataRecord) -> Regulation:
        """
        Convert a generic DataRecord to a Regulation entity.
        
        Args:
            record: DataRecord to convert
            
        Returns:
            Regulation entity
        """
        # Parse regulation type from metadata
        reg_type = self._parse_regulation_type(record.metadata)
        
        # Parse effective date
        effective_date = self._parse_date(record.metadata.get('approval_date'))
        
        # Build source document reference
        source_doc = f"{record.source}: {record.metadata.get('plan_number', record.id)}"
        
        # Create regulation
        regulation = Regulation(
            id=record.id,
            title=record.title,
            content=record.content,
            type=reg_type,
            effective_date=effective_date,
            source_document=source_doc,
            metadata=record.metadata
        )
        
        return regulation
    
    def _parse_regulation_type(self, metadata: dict) -> RegulationType:
        """
        Parse regulation type from metadata.
        
        Args:
            metadata: Record metadata
            
        Returns:
            RegulationType enum value
        """
        # Check entity subtype if present
        entity_subtype = metadata.get('entity_subtype', '').lower()
        
        if any(keyword in entity_subtype for keyword in ['מגורים', 'דיור', 'משכנות']):
            return RegulationType.RESIDENTIAL
        elif any(keyword in entity_subtype for keyword in ['תעשיה', 'מסחר', 'משרדים', 'תעסוקה']):
            return RegulationType.COMMERCIAL
        elif any(keyword in entity_subtype for keyword in ['תחבורה', 'תנועה', 'דרך', 'כביש']):
            return RegulationType.TRANSPORTATION
        elif any(keyword in entity_subtype for keyword in ['שימור', 'מורשת', 'היסטורי']):
            return RegulationType.PRESERVATION
        else:
            return RegulationType.GENERAL
    
    def _parse_date(self, date_value) -> datetime | None:
        """Parse date from various formats."""
        if not date_value:
            return None
        
        try:
            # iPlan uses milliseconds since epoch
            if isinstance(date_value, (int, float)):
                return datetime.fromtimestamp(date_value / 1000)
            elif isinstance(date_value, str) and date_value.isdigit():
                return datetime.fromtimestamp(int(date_value) / 1000)
            elif isinstance(date_value, str):
                # Try ISO format
                return datetime.fromisoformat(date_value)
        except Exception as e:
            logger.debug(f"Could not parse date '{date_value}': {e}")
        
        return None
