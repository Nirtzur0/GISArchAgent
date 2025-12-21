"""Local projects integration module for extending RAG to firm-specific data."""

import logging
from typing import List, Dict, Optional
from pathlib import Path
import json

from langchain.schema import Document
from langchain.document_loaders import (
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredExcelLoader,
    TextLoader
)

from src.vectorstore import VectorStoreManager

logger = logging.getLogger(__name__)


class LocalProjectManager:
    """Manager for local architecture firm projects and documents."""
    
    def __init__(self, projects_dir: str = "./data/local_projects"):
        """Initialize the local project manager.
        
        Args:
            projects_dir: Directory containing local project files
        """
        self.projects_dir = Path(projects_dir)
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        
        # Separate vector store for local projects
        self.vectorstore = VectorStoreManager(collection_name="local_projects")
        
        logger.info(f"Local project manager initialized: {projects_dir}")
    
    def load_document(self, file_path: Path) -> List[Document]:
        """Load a document based on its file type.
        
        Args:
            file_path: Path to the document
            
        Returns:
            List of Document objects
        """
        logger.info(f"Loading document: {file_path}")
        
        suffix = file_path.suffix.lower()
        
        try:
            if suffix == '.pdf':
                loader = PyPDFLoader(str(file_path))
            elif suffix in ['.doc', '.docx']:
                loader = UnstructuredWordDocumentLoader(str(file_path))
            elif suffix in ['.xls', '.xlsx']:
                loader = UnstructuredExcelLoader(str(file_path))
            elif suffix in ['.txt', '.md']:
                loader = TextLoader(str(file_path))
            else:
                logger.warning(f"Unsupported file type: {suffix}")
                return []
            
            documents = loader.load()
            
            # Add file metadata
            for doc in documents:
                doc.metadata.update({
                    "source_file": str(file_path),
                    "file_type": suffix,
                    "project_type": "local"
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {e}")
            return []
    
    def ingest_project(
        self,
        project_name: str,
        project_files: List[Path],
        metadata: Optional[Dict] = None
    ) -> int:
        """Ingest a complete project into the vector store.
        
        Args:
            project_name: Name of the project
            project_files: List of file paths for the project
            metadata: Optional metadata for the project
            
        Returns:
            Number of documents ingested
        """
        logger.info(f"Ingesting project: {project_name}")
        
        all_docs = []
        
        for file_path in project_files:
            docs = self.load_document(file_path)
            
            # Add project metadata
            for doc in docs:
                doc.metadata.update({
                    "project_name": project_name,
                    **(metadata or {})
                })
            
            all_docs.extend(docs)
        
        if all_docs:
            ids = self.vectorstore.add_documents(all_docs)
            logger.info(f"Ingested {len(ids)} chunks for project {project_name}")
            return len(ids)
        
        return 0
    
    def ingest_project_directory(
        self,
        project_dir: Path,
        project_name: Optional[str] = None
    ) -> int:
        """Ingest all documents from a project directory.
        
        Args:
            project_dir: Directory containing project files
            project_name: Optional project name (uses dir name if not provided)
            
        Returns:
            Number of documents ingested
        """
        if not project_dir.exists():
            logger.error(f"Project directory not found: {project_dir}")
            return 0
        
        project_name = project_name or project_dir.name
        
        # Find all supported files
        supported_extensions = ['.pdf', '.docx', '.doc', '.txt', '.md', '.xlsx', '.xls']
        project_files = []
        
        for ext in supported_extensions:
            project_files.extend(project_dir.rglob(f'*{ext}'))
        
        logger.info(f"Found {len(project_files)} files in {project_dir}")
        
        return self.ingest_project(project_name, project_files)
    
    def search_local_projects(
        self,
        query: str,
        project_name: Optional[str] = None,
        k: int = 5
    ) -> List[Document]:
        """Search local projects.
        
        Args:
            query: Search query
            project_name: Optional project name to filter by
            k: Number of results
            
        Returns:
            List of relevant documents
        """
        filter_dict = {"project_type": "local"}
        if project_name:
            filter_dict["project_name"] = project_name
        
        results = self.vectorstore.similarity_search(
            query,
            k=k,
            filter=filter_dict
        )
        
        return results
    
    def create_project_index(self, project_dir: Path) -> Dict:
        """Create an index of a project's contents.
        
        Args:
            project_dir: Project directory
            
        Returns:
            Dictionary with project index
        """
        index = {
            "project_name": project_dir.name,
            "location": str(project_dir),
            "files": [],
            "total_size": 0
        }
        
        for file_path in project_dir.rglob('*'):
            if file_path.is_file():
                index["files"].append({
                    "name": file_path.name,
                    "path": str(file_path.relative_to(project_dir)),
                    "size": file_path.stat().st_size,
                    "type": file_path.suffix
                })
                index["total_size"] += file_path.stat().st_size
        
        # Save index
        index_file = project_dir / "project_index.json"
        with open(index_file, 'w') as f:
            json.dump(index, f, indent=2)
        
        logger.info(f"Created index for project: {project_dir.name}")
        
        return index


class HybridSearchManager:
    """Manager for searching across both iPlan regulations and local projects."""
    
    def __init__(self):
        """Initialize the hybrid search manager."""
        self.regulations_store = VectorStoreManager(collection_name="iplan_regulations")
        self.projects_store = VectorStoreManager(collection_name="local_projects")
    
    def hybrid_search(
        self,
        query: str,
        search_regulations: bool = True,
        search_projects: bool = True,
        k: int = 5
    ) -> Dict[str, List[Document]]:
        """Search across both regulations and local projects.
        
        Args:
            query: Search query
            search_regulations: Whether to search regulations
            search_projects: Whether to search local projects
            k: Number of results per source
            
        Returns:
            Dictionary with results from each source
        """
        results = {}
        
        if search_regulations:
            results["regulations"] = self.regulations_store.similarity_search(query, k=k)
        
        if search_projects:
            results["local_projects"] = self.projects_store.similarity_search(query, k=k)
        
        return results
    
    def contextualized_search(
        self,
        query: str,
        project_context: Optional[str] = None,
        k: int = 5
    ) -> List[Document]:
        """Search with project context to find relevant regulations.
        
        This is useful for finding regulations applicable to a specific project.
        
        Args:
            query: Search query
            project_context: Context from a specific project
            k: Number of results
            
        Returns:
            Combined results from both sources
        """
        # If we have project context, search it first
        all_results = []
        
        if project_context:
            # Search local projects
            project_results = self.projects_store.similarity_search(
                project_context,
                k=2
            )
            all_results.extend(project_results)
        
        # Search regulations
        regulation_results = self.regulations_store.similarity_search(
            query,
            k=k
        )
        all_results.extend(regulation_results)
        
        return all_results
