"""
ChromaDB Repository Implementation.

Concrete implementation of IRegulationRepository using ChromaDB vector database.
"""

import logging
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings

from src.domain.repositories import IRegulationRepository
from src.domain.entities.regulation import Regulation, RegulationType

logger = logging.getLogger(__name__)


class ChromaRegulationRepository(IRegulationRepository):
    """
    ChromaDB implementation for regulation storage and retrieval.
    
    Uses vector embeddings for semantic search of regulations.
    """
    
    def __init__(
        self,
        persist_directory: str,
        collection_name: str = "regulations",
        embedding_function = None
    ):
        """
        Initialize repository.
        
        Args:
            persist_directory: Directory for ChromaDB persistence
            collection_name: Name of the collection
            embedding_function: Optional embedding function
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize ChromaDB client
        self._client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function
        )
        
        logger.info(f"ChromaDB repository initialized: {collection_name}")
    
    def search(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Regulation]:
        """Semantic search for regulations."""
        try:
            # Build where clause from filters
            where_clause = self._build_where_clause(filters) if filters else None
            
            # Execute query
            results = self._collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_clause
            )
            
            # Map results to entities
            regulations = []
            if results and results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    reg = self._map_to_entity(doc, metadata)
                    if reg:
                        regulations.append(reg)
            
            return regulations
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_by_id(self, regulation_id: str) -> Optional[Regulation]:
        """Get regulation by ID."""
        try:
            result = self._collection.get(ids=[regulation_id])
            
            if result and result['documents']:
                metadata = result['metadatas'][0] if result['metadatas'] else {}
                return self._map_to_entity(result['documents'][0], metadata)
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get regulation {regulation_id}: {e}")
            return None
    
    def get_by_type(self, regulation_type: str, limit: int = 10) -> List[Regulation]:
        """Get regulations by type."""
        try:
            results = self._collection.get(
                where={'type': regulation_type},
                limit=limit
            )
            
            regulations = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents']):
                    metadata = results['metadatas'][i] if results['metadatas'] else {}
                    reg = self._map_to_entity(doc, metadata)
                    if reg:
                        regulations.append(reg)
            
            return regulations
        
        except Exception as e:
            logger.error(f"Failed to get regulations by type {regulation_type}: {e}")
            return []
    
    def get_applicable_to_location(self, location: str, limit: int = 10) -> List[Regulation]:
        """Get regulations applicable to location."""
        try:
            # Search for regulations mentioning the location
            results = self._collection.query(
                query_texts=[location],
                n_results=limit
            )
            
            regulations = []
            if results and results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    reg = self._map_to_entity(doc, metadata)
                    if reg and reg.applies_to_location(location):
                        regulations.append(reg)
            
            return regulations
        
        except Exception as e:
            logger.error(f"Failed to get regulations for location {location}: {e}")
            return []
    
    def add_regulation(self, regulation: Regulation) -> bool:
        """Add regulation to repository."""
        try:
            # Prepare document
            document = self._prepare_document(regulation)
            metadata = self._prepare_metadata(regulation)
            
            # Add to collection
            self._collection.add(
                documents=[document],
                metadatas=[metadata],
                ids=[regulation.id]
            )
            
            logger.info(f"Added regulation: {regulation.id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to add regulation: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get repository statistics."""
        try:
            count = self._collection.count()
            
            return {
                'total_regulations': count,
                'collection_name': self.collection_name,
                'persist_directory': self.persist_directory
            }
        
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {
                'total_regulations': 0,
                'collection_name': self.collection_name,
                'error': str(e)
            }
    
    def _build_where_clause(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build ChromaDB where clause from filters."""
        where = {}
        
        if 'type' in filters:
            where['type'] = filters['type']
        
        if 'location' in filters:
            where['jurisdiction'] = filters['location']
        
        return where if where else None
    
    def _prepare_document(self, regulation: Regulation) -> str:
        """Prepare regulation document for storage."""
        parts = [
            regulation.title,
            regulation.content,
        ]
        
        if regulation.summary:
            parts.insert(1, regulation.summary)
        
        return "\n\n".join(parts)
    
    def _prepare_metadata(self, regulation: Regulation) -> Dict[str, Any]:
        """Prepare regulation metadata for storage."""
        return {
            'type': regulation.type.value,
            'jurisdiction': regulation.jurisdiction,
            'title': regulation.title,
            'effective_date': regulation.effective_date.isoformat() if regulation.effective_date else None,
        }
    
    def _map_to_entity(self, document: str, metadata: Dict[str, Any]) -> Optional[Regulation]:
        """Map stored document to Regulation entity."""
        try:
            # Extract regulation ID from metadata or generate
            reg_id = metadata.get('id', metadata.get('title', '')[:50])
            
            return Regulation(
                id=reg_id,
                type=RegulationType(metadata.get('type', 'local')),
                title=metadata.get('title', 'Untitled'),
                content=document,
                summary=metadata.get('summary'),
                jurisdiction=metadata.get('jurisdiction', 'national'),
                metadata=metadata
            )
        
        except Exception as e:
            logger.error(f"Failed to map regulation: {e}")
            return None
