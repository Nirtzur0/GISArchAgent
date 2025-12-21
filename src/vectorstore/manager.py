"""Vector store management for document storage and retrieval."""

import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.config import settings

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages the vector store for document storage and retrieval."""
    
    def __init__(self, collection_name: str = "iplan_regulations"):
        """Initialize the vector store manager.
        
        Args:
            collection_name: Name of the collection in the vector store
        """
        self.collection_name = collection_name
        self.persist_directory = Path(settings.chroma_persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key
        )
        
        # Initialize vector store
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=str(self.persist_directory)
        )
        
        # Text splitter for chunking documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        logger.info(f"Vector store initialized: {collection_name}")
    
    def add_documents(
        self, 
        documents: List[Document],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Add documents to the vector store.
        
        Args:
            documents: List of documents to add
            metadata: Optional metadata to add to all documents
            
        Returns:
            List of document IDs
        """
        # Add metadata if provided
        if metadata:
            for doc in documents:
                doc.metadata.update(metadata)
        
        # Split documents into chunks
        chunks = self.text_splitter.split_documents(documents)
        
        logger.info(f"Adding {len(chunks)} chunks to vector store")
        
        # Add to vector store
        ids = self.vectorstore.add_documents(chunks)
        
        return ids
    
    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Add text strings to the vector store.
        
        Args:
            texts: List of text strings to add
            metadatas: Optional list of metadata dicts for each text
            
        Returns:
            List of document IDs
        """
        logger.info(f"Adding {len(texts)} texts to vector store")
        
        # Add to vector store
        ids = self.vectorstore.add_texts(texts, metadatas=metadatas)
        
        return ids
    
    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Search for similar documents.
        
        Args:
            query: Query string
            k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of similar documents
        """
        logger.info(f"Searching for: {query[:100]}...")
        
        results = self.vectorstore.similarity_search(
            query,
            k=k,
            filter=filter
        )
        
        return results
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Document, float]]:
        """Search for similar documents with relevance scores.
        
        Args:
            query: Query string
            k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of (document, score) tuples
        """
        results = self.vectorstore.similarity_search_with_score(
            query,
            k=k,
            filter=filter
        )
        
        return results
    
    def as_retriever(self, **kwargs):
        """Get a retriever interface for the vector store.
        
        Args:
            **kwargs: Arguments to pass to the retriever
            
        Returns:
            Retriever object
        """
        return self.vectorstore.as_retriever(**kwargs)
    
    def delete_collection(self):
        """Delete the entire collection."""
        logger.warning(f"Deleting collection: {self.collection_name}")
        self.vectorstore.delete_collection()
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection.
        
        Returns:
            Dictionary with collection statistics
        """
        collection = self.vectorstore._collection
        count = collection.count()
        
        return {
            "collection_name": self.collection_name,
            "document_count": count,
            "persist_directory": str(self.persist_directory)
        }


class MultiCollectionManager:
    """Manages multiple vector store collections."""
    
    def __init__(self):
        """Initialize the multi-collection manager."""
        self.collections: Dict[str, VectorStoreManager] = {}
    
    def get_collection(self, name: str) -> VectorStoreManager:
        """Get or create a collection.
        
        Args:
            name: Collection name
            
        Returns:
            VectorStoreManager instance
        """
        if name not in self.collections:
            self.collections[name] = VectorStoreManager(collection_name=name)
        
        return self.collections[name]
    
    def search_all_collections(
        self,
        query: str,
        k: int = 4
    ) -> Dict[str, List[Document]]:
        """Search across all collections.
        
        Args:
            query: Query string
            k: Number of results per collection
            
        Returns:
            Dictionary mapping collection names to results
        """
        results = {}
        
        for name, collection in self.collections.items():
            results[name] = collection.similarity_search(query, k=k)
        
        return results
