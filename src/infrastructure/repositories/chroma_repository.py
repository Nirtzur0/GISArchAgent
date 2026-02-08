"""
ChromaDB Repository Implementation.

Concrete implementation of IRegulationRepository using ChromaDB vector database.
"""

import logging
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings
from pathlib import Path

from src.domain.repositories import IRegulationRepository
from src.domain.entities.regulation import Regulation, RegulationType
from src.infrastructure.repositories.embedding_functions import DeterministicHashEmbeddingFunction

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

        # Avoid implicit embedding-model downloads for fresh installs/tests by
        # using a deterministic local embedding unless the caller provides one.
        # For existing persisted DBs, keep default behavior to avoid dimension
        # mismatch with already-stored vectors.
        if embedding_function is None:
            db_file = Path(persist_directory) / "chroma.sqlite3"
            if not db_file.exists():
                embedding_function = DeterministicHashEmbeddingFunction(dim=128)
        
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

    def search_with_scores(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Semantic search that also returns similarity scores.
        
        Returns a list of dicts: {"regulation": Regulation, "similarity": float}.
        Similarity is derived from Chroma's distance metric (smaller is better).
        """
        try:
            where_clause = self._build_where_clause(filters) if filters else None

            results = self._collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_clause,
                include=["documents", "metadatas", "distances"],
            )

            docs = (results.get("documents") or [[]])[0]
            metas = (results.get("metadatas") or [[]])[0]
            dists = (results.get("distances") or [[]])[0]

            out: List[Dict[str, Any]] = []
            for doc, meta, dist in zip(docs, metas, dists):
                reg = self._map_to_entity(doc, meta or {})
                if not reg:
                    continue
                # Convert distance -> similarity in (0, 1]; distance can be 0.
                try:
                    similarity = 1.0 / (1.0 + float(dist))
                except Exception:
                    similarity = 0.0
                out.append({"regulation": reg, "similarity": similarity})

            return out
        except Exception as e:
            logger.error(f"Search with scores failed: {e}")
            return []

    def search_by_text(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Backwards-compatible helper for UI/services that expect scored matches."""
        return self.search_with_scores(query=query, limit=limit)
    
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
    
    def is_initialized(self) -> bool:
        """Check if the vector database is properly initialized.
        
        Returns:
            True if the database exists and has data, False otherwise
        """
        try:
            count = self._collection.count()
            return count > 0
        except Exception as e:
            logger.error(f"Failed to check initialization status: {e}")
            return False
    
    def add_regulations_batch(self, regulations: List[Regulation]) -> int:
        """Add multiple regulations to repository.
        
        Args:
            regulations: List of regulations to add
            
        Returns:
            Number of successfully added regulations
        """
        try:
            documents = []
            metadatas = []
            ids = []
            
            for regulation in regulations:
                documents.append(self._prepare_document(regulation))
                metadatas.append(self._prepare_metadata(regulation))
                ids.append(regulation.id)
            
            self._collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(regulations)} regulations in batch")
            return len(regulations)
        
        except Exception as e:
            logger.error(f"Failed to add regulations batch: {e}")
            return 0

    def upsert_regulation(self, regulation: Regulation) -> bool:
        """Insert or update a regulation (idempotent)."""
        return self.upsert_regulations_batch([regulation]) == 1

    def upsert_regulations_batch(self, regulations: List[Regulation]) -> int:
        """Insert or update regulations in batch (idempotent).

        This is preferred for continuous scraping where reruns should not fail
        on duplicate IDs.
        """
        if not regulations:
            return 0

        try:
            documents: List[str] = []
            metadatas: List[Dict[str, Any]] = []
            ids: List[str] = []

            for regulation in regulations:
                documents.append(self._prepare_document(regulation))
                metadatas.append(self._prepare_metadata(regulation))
                ids.append(regulation.id)

            if hasattr(self._collection, "upsert"):
                self._collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
            else:  # pragma: no cover
                # Older Chroma: emulate upsert via delete+add.
                try:
                    self._collection.delete(ids=ids)
                except Exception:
                    pass
                self._collection.add(documents=documents, metadatas=metadatas, ids=ids)

            logger.info(f"Upserted {len(regulations)} regulations in batch")
            return len(regulations)
        except Exception as e:
            logger.error(f"Failed to upsert regulations batch: {e}")
            return 0
    
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
        """Prepare regulation metadata for storage.
        Note: ChromaDB only accepts string, int, float, or bool values - no None.
        """
        metadata = {
            'id': str(regulation.id),
            'type': str(regulation.type.value),
            'jurisdiction': str(regulation.jurisdiction),
            'title': str(regulation.title),
        }
        
        # Only add optional fields if they have values (ChromaDB doesn't accept None)
        if regulation.effective_date:
            metadata['effective_date'] = regulation.effective_date.isoformat()
        
        if regulation.source_document:
            metadata['source'] = str(regulation.source_document)
        
        # Add any additional metadata from regulation.metadata dict
        if regulation.metadata:
            for key, value in regulation.metadata.items():
                if value is not None and value != '':
                    # Convert all values to strings to ensure ChromaDB compatibility
                    metadata[key] = str(value)
        
        return metadata
    
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
