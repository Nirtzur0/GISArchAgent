"""
Vector Database Management Service

Provides functionality for managing and updating the vector database,
including adding new regulations, updating existing ones, and batch operations.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.domain.entities.regulation import Regulation, RegulationType
from src.infrastructure.repositories.chroma_repository import ChromaRegulationRepository
from src.vectorstore.initializer import VectorDBInitializer

logger = logging.getLogger(__name__)


class VectorDBManagementService:
    """Service for managing vector database operations."""
    
    def __init__(self, repository: ChromaRegulationRepository):
        """Initialize the management service.
        
        Args:
            repository: ChromaDB regulation repository
        """
        self.repository = repository
        self.initializer = VectorDBInitializer(repository)
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive database status.
        
        Returns:
            Dictionary with status information
        """
        status = self.initializer.get_initialization_status()
        stats = self.repository.get_statistics()
        
        return {
            **status,
            "health": "healthy" if status.get("initialized") else "needs_initialization",
            "last_checked": datetime.now().isoformat(),
            "statistics": stats
        }
    
    def initialize_if_needed(self) -> bool:
        """Check and initialize database if empty.
        
        Returns:
            True if database is ready (already initialized or just initialized)
        """
        return self.initializer.check_and_initialize()
    
    def add_regulation(
        self, 
        title: str,
        content: str,
        reg_type: RegulationType = RegulationType.LOCAL,
        jurisdiction: str = "national",
        summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add a new regulation to the database.
        
        Args:
            title: Regulation title
            content: Full regulation content
            reg_type: Type of regulation
            jurisdiction: Jurisdiction (city name or 'national')
            summary: Optional summary
            metadata: Optional additional metadata
            
        Returns:
            True if added successfully
        """
        try:
            # Generate ID from title
            reg_id = f"reg_{title.lower().replace(' ', '_')[:50]}_{datetime.now().timestamp()}"
            
            # Create regulation entity
            regulation = Regulation(
                id=reg_id,
                type=reg_type,
                title=title,
                content=content,
                summary=summary,
                jurisdiction=jurisdiction,
                effective_date=datetime.now(),
                metadata=metadata or {}
            )
            
            # Add to repository
            success = self.repository.add_regulation(regulation)
            
            if success:
                logger.info(f"Added regulation: {title}")
            else:
                logger.error(f"Failed to add regulation: {title}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error adding regulation: {e}", exc_info=True)
            return False
    
    def add_regulations_batch(self, regulations_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add multiple regulations in a batch.
        
        Args:
            regulations_data: List of regulation dictionaries
            
        Returns:
            Dictionary with results (success count, failed count, details)
        """
        try:
            regulations = []
            failed = []
            
            for idx, data in enumerate(regulations_data):
                try:
                    reg_id = data.get("id") or f"reg_{idx}_{datetime.now().timestamp()}"
                    
                    regulation = Regulation(
                        id=reg_id,
                        type=RegulationType(data.get("type", "local")),
                        title=data["title"],
                        content=data["content"],
                        summary=data.get("summary"),
                        jurisdiction=data.get("jurisdiction", "national"),
                        effective_date=datetime.now(),
                        metadata=data.get("metadata", {})
                    )
                    regulations.append(regulation)
                    
                except Exception as e:
                    failed.append({
                        "index": idx,
                        "title": data.get("title", "Unknown"),
                        "error": str(e)
                    })
            
            # Add valid regulations
            count = self.repository.add_regulations_batch(regulations)
            
            return {
                "success": count,
                "failed": len(failed),
                "total": len(regulations_data),
                "failures": failed
            }
            
        except Exception as e:
            logger.error(f"Error in batch add: {e}", exc_info=True)
            return {
                "success": 0,
                "failed": len(regulations_data),
                "error": str(e)
            }
    
    def search_regulations(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Regulation]:
        """Search for regulations.
        
        Args:
            query: Search query
            filters: Optional filters
            limit: Maximum results
            
        Returns:
            List of matching regulations
        """
        return self.repository.search(query, filters, limit)
    
    def get_regulation_by_id(self, regulation_id: str) -> Optional[Regulation]:
        """Get a specific regulation by ID.
        
        Args:
            regulation_id: Regulation identifier
            
        Returns:
            Regulation if found, None otherwise
        """
        return self.repository.get_by_id(regulation_id)
    
    def update_regulation(
        self,
        regulation_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update an existing regulation.
        
        Args:
            regulation_id: ID of regulation to update
            updates: Dictionary of fields to update
            
        Returns:
            True if updated successfully
        """
        try:
            # Get existing regulation
            existing = self.repository.get_by_id(regulation_id)
            if not existing:
                logger.error(f"Regulation not found: {regulation_id}")
                return False
            
            # Update fields
            if "title" in updates:
                existing.title = updates["title"]
            if "content" in updates:
                existing.content = updates["content"]
            if "summary" in updates:
                existing.summary = updates["summary"]
            if "jurisdiction" in updates:
                existing.jurisdiction = updates["jurisdiction"]
            
            # Update metadata
            if existing.metadata is None:
                existing.metadata = {}
            existing.metadata["updated_at"] = datetime.now().isoformat()
            
            # Remove old and add updated
            # Note: ChromaDB doesn't have native update, so we delete and re-add
            # This is a simple implementation - in production, you'd use upsert
            self.repository._collection.delete(ids=[regulation_id])
            success = self.repository.add_regulation(existing)
            
            if success:
                logger.info(f"Updated regulation: {regulation_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating regulation: {e}", exc_info=True)
            return False
    
    def delete_regulation(self, regulation_id: str) -> bool:
        """Delete a regulation from the database.
        
        Args:
            regulation_id: ID of regulation to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            self.repository._collection.delete(ids=[regulation_id])
            logger.info(f"Deleted regulation: {regulation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting regulation: {e}", exc_info=True)
            return False
    
    def import_from_file(self, file_path: str) -> Dict[str, Any]:
        """Import regulations from a JSON file.
        
        Args:
            file_path: Path to JSON file with regulations
            
        Returns:
            Dictionary with import results
        """
        try:
            import json
            from pathlib import Path
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Support both single regulation and list
            if isinstance(data, dict):
                data = [data]
            
            return self.add_regulations_batch(data)
            
        except Exception as e:
            logger.error(f"Error importing from file: {e}", exc_info=True)
            return {
                "success": 0,
                "failed": 0,
                "error": str(e)
            }
    
    def export_to_file(self, file_path: str, regulation_ids: Optional[List[str]] = None) -> bool:
        """Export regulations to a JSON file.
        
        Args:
            file_path: Path to save JSON file
            regulation_ids: Optional list of specific regulation IDs to export
            
        Returns:
            True if exported successfully
        """
        try:
            import json
            from pathlib import Path
            
            # Get regulations
            if regulation_ids:
                regulations = [self.repository.get_by_id(rid) for rid in regulation_ids]
                regulations = [r for r in regulations if r is not None]
            else:
                # Export all - search with empty query
                regulations = self.repository.search("", limit=1000)
            
            # Convert to dict format
            data = []
            for reg in regulations:
                data.append({
                    "id": reg.id,
                    "type": reg.type.value,
                    "title": reg.title,
                    "content": reg.content,
                    "summary": reg.summary,
                    "jurisdiction": reg.jurisdiction,
                    "metadata": reg.metadata
                })
            
            # Write to file
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Exported {len(data)} regulations to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to file: {e}", exc_info=True)
            return False
    
    def rebuild_database(self) -> bool:
        """Rebuild the entire database with sample data.
        
        Warning: This will clear all existing data!
        
        Returns:
            True if rebuilt successfully
        """
        try:
            logger.warning("Rebuilding vector database - all data will be lost!")
            
            # Clear existing collection
            self.repository._collection.delete(where={})
            
            # Re-initialize with samples
            success = self.initializer.initialize_with_samples()
            
            if success:
                logger.info("Database rebuilt successfully")
            else:
                logger.error("Failed to rebuild database")
            
            return success
            
        except Exception as e:
            logger.error(f"Error rebuilding database: {e}", exc_info=True)
            return False
