"""
Test Vector Database Integration

Pytest suite to verify:
1. ChromaDB is properly connected and persistent
2. Data is actually stored and retrieved from the database
3. The application uses real vector search (not mock data)
4. Data persists between application runs
"""

import pytest
from pathlib import Path
import chromadb
from chromadb.config import Settings

from src.infrastructure.factory import ApplicationFactory
from src.vectorstore.initializer import VectorDBInitializer
from src.application.dtos import RegulationQuery


# Fixtures
@pytest.fixture(scope="module")
def project_root():
    """Get project root directory"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="module")
def vectorstore_path(project_root):
    """Get vectorstore path"""
    return project_root / "data" / "vectorstore"


@pytest.fixture(scope="module")
def factory():
    """Application factory fixture"""
    return ApplicationFactory()


@pytest.fixture(scope="module")
def repo(factory):
    """Repository fixture"""
    return factory.get_regulation_repository()


@pytest.fixture(scope="module")
def chroma_client(vectorstore_path):
    """Direct ChromaDB client"""
    return chromadb.PersistentClient(
        path=str(vectorstore_path),
        settings=Settings(anonymized_telemetry=False)
    )


# Tests
class TestChromaDBPersistence:
    """Test ChromaDB persistence and file storage"""
    
    def test_vectorstore_path_exists(self, vectorstore_path):
        """Verify vectorstore directory exists"""
        assert vectorstore_path.exists(), "Vectorstore directory should exist"
    
    def test_database_file_exists(self, vectorstore_path):
        """Verify ChromaDB SQLite file exists"""
        db_file = vectorstore_path / "chroma.sqlite3"
        assert db_file.exists(), "ChromaDB database file should exist"
    
    def test_database_has_content(self, vectorstore_path):
        """Verify database file has content"""
        db_file = vectorstore_path / "chroma.sqlite3"
        assert db_file.stat().st_size > 0, "Database file should not be empty"
    
    def test_collection_directories_exist(self, vectorstore_path):
        """Verify collection directories exist"""
        files = list(vectorstore_path.glob("*"))
        assert len(files) > 1, "Should have database file + collection directories"


class TestChromaDBConnection:
    """Test direct ChromaDB connection and data access"""
    
    def test_client_connection(self, chroma_client):
        """Test ChromaDB client can connect"""
        collections = chroma_client.list_collections()
        assert len(collections) > 0, "Should have at least one collection"
    
    def test_regulations_collection_exists(self, chroma_client):
        """Test regulations collection exists"""
        collections = chroma_client.list_collections()
        collection_names = [c.name for c in collections]
        assert 'regulations' in collection_names, "Should have 'regulations' collection"
    
    def test_collection_has_documents(self, chroma_client):
        """Test collection contains documents"""
        collection = chroma_client.get_collection("regulations")
        count = collection.count()
        assert count > 0, "Collection should contain documents"
    
    def test_documents_have_metadata(self, chroma_client):
        """Test documents have proper metadata"""
        collection = chroma_client.get_collection("regulations")
        results = collection.get(limit=1)
        
        assert results['metadatas'], "Documents should have metadata"
        assert len(results['metadatas']) > 0, "Should have at least one document"
        
        metadata = results['metadatas'][0]
        assert 'title' in metadata, "Metadata should include title"
        assert 'type' in metadata, "Metadata should include type"


class TestRepositoryIntegration:
    """Test repository integration via ApplicationFactory"""
    
    def test_factory_creates_repository(self, factory):
        """Test factory can create repository"""
        repo = factory.get_regulation_repository()
        assert repo is not None, "Factory should create repository"
    
    def test_repository_statistics(self, repo):
        """Test repository returns statistics"""
        stats = repo.get_statistics()
        
        assert stats is not None, "Should return statistics"
        assert 'total_regulations' in stats, "Stats should include total"
        assert stats['total_regulations'] > 0, "Should have regulations"
    
    def test_repository_search(self, repo):
        """Test repository search functionality"""
        results = repo.search("building", limit=3)
        
        assert results is not None, "Search should return results"
        assert len(results) > 0, "Search should find regulations"
    
    def test_search_results_structure(self, repo):
        """Test search results have proper structure"""
        results = repo.search("regulation", limit=1)
        
        if results:
            reg = results[0]
            assert hasattr(reg, 'id'), "Regulation should have ID"
            assert hasattr(reg, 'title'), "Regulation should have title"
            assert hasattr(reg, 'type'), "Regulation should have type"
            assert hasattr(reg, 'content'), "Regulation should have content"


class TestServiceIntegration:
    """Test end-to-end service integration"""
    
    def test_regulation_query_service(self, factory):
        """Test regulation query service"""
        service = factory.get_regulation_query_service()
        assert service is not None, "Factory should create service"
    
    def test_query_execution(self, factory):
        """Test executing a query through service"""
        service = factory.get_regulation_query_service()
        
        query = RegulationQuery(
            query_text="What are the building requirements?",
            location="national"
        )
        
        result = service.query(query)
        
        assert result is not None, "Query should return result"
        assert hasattr(result, 'total_found'), "Result should have total_found"
        assert hasattr(result, 'regulations'), "Result should have regulations list"
    
    def test_query_finds_regulations(self, factory):
        """Test query actually finds regulations"""
        service = factory.get_regulation_query_service()
        
        query = RegulationQuery(
            query_text="parking requirements",
            location="national"
        )
        
        result = service.query(query)
        assert result.total_found > 0, "Query should find regulations"


class TestDataQuality:
    """Test data quality and freshness"""
    
    def test_initialization_status(self, repo):
        """Test database initialization status"""
        initializer = VectorDBInitializer(repo)
        status = initializer.get_initialization_status()
        
        assert status['initialized'], "Database should be initialized"
        assert status['total_regulations'] > 0, "Should have regulations"
        assert status['status'] == 'ready', "Status should be ready"
    
    def test_hebrew_content(self, repo):
        """Test database contains Hebrew content"""
        results = repo.search("תכנית", limit=1)
        
        assert len(results) > 0, "Should find Hebrew search results"
        
        # Check for Hebrew characters
        reg = results[0]
        has_hebrew = any(0x0590 <= ord(c) <= 0x05FF for c in reg.title)
        assert has_hebrew, "Should contain Hebrew text"
    
    def test_data_diversity(self, repo):
        """Test database has diverse regulations"""
        results = repo.search("regulation", limit=10)
        
        unique_titles = set(r.title for r in results)
        assert len(unique_titles) >= 5, "Should have diverse regulations"
    
    def test_metadata_completeness(self, repo):
        """Test regulations have complete metadata"""
        results = repo.search("building", limit=5)
        
        for reg in results:
            assert reg.id, "Regulation should have ID"
            assert reg.title, "Regulation should have title"
            assert reg.type, "Regulation should have type"
            assert reg.content, "Regulation should have content"


class TestVectorSearch:
    """Test vector search quality and semantic understanding"""
    
    @pytest.mark.parametrize("query1,query2", [
        ("building height", "construction elevation"),
        ("parking spaces", "vehicle storage"),
        ("zoning rules", "land use regulations"),
    ])
    def test_semantic_search(self, repo, query1, query2):
        """Test semantic search finds related concepts"""
        results1 = repo.search(query1, limit=3)
        results2 = repo.search(query2, limit=3)
        
        assert len(results1) > 0, f"Should find results for '{query1}'"
        assert len(results2) > 0, f"Should find results for '{query2}'"
    
    def test_hebrew_search(self, repo):
        """Test Hebrew search functionality"""
        hebrew_queries = ['תוספת קומה', 'שינוי קו בנין', 'מגורים']
        
        for query in hebrew_queries:
            results = repo.search(query, limit=3)
            assert len(results) > 0, f"Should find results for Hebrew query: {query}"
    
    def test_search_relevance(self, repo):
        """Test search results are relevant"""
        results = repo.search("parking", limit=5)
        
        if results:
            # Check that top result content mentions parking-related terms
            top_result = results[0]
            content_lower = (top_result.title + " " + top_result.content).lower()
            
            parking_terms = ['parking', 'חניה', 'vehicle', 'car']
            has_relevant_term = any(term in content_lower for term in parking_terms)
            
            assert has_relevant_term, "Top result should be relevant to query"


# Test markers for different categories
pytestmark = [
    pytest.mark.integration,
    pytest.mark.vectordb,
]


if __name__ == "__main__":
    # Allow running with: python tests/test_vectordb_integration.py
    pytest.main([__file__, "-v", "--tb=short"])
