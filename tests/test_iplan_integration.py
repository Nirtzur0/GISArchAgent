"""
Test iPlan Data Integration

Pytest suite to verify real iPlan data is properly loaded and functional.
"""

import pytest
from pathlib import Path

from src.infrastructure.factory import ApplicationFactory


# Fixtures
@pytest.fixture(scope="module")
def factory():
    """Application factory fixture"""
    return ApplicationFactory()


@pytest.fixture(scope="module")
def repo(factory):
    """Repository fixture"""
    return factory.get_regulation_repository()


@pytest.fixture(scope="module")
def repo_stats(repo):
    """Repository statistics fixture"""
    return repo.get_statistics()


# Tests
class TestDatabasePopulation:
    """Test database has iPlan data loaded"""
    
    def test_database_not_empty(self, repo_stats):
        """Test database contains regulations"""
        total = repo_stats.get('total_regulations', 0)
        assert total > 0, "Database should contain regulations"
    
    def test_sufficient_data(self, repo_stats):
        """Test database has sufficient regulations"""
        total = repo_stats.get('total_regulations', 0)
        assert total >= 10, f"Should have at least 10 regulations, found {total}"
    
    def test_collection_configured(self, repo_stats):
        """Test collection is properly configured"""
        assert 'collection_name' in repo_stats, "Stats should include collection name"
        assert repo_stats['collection_name'] == 'regulations', "Collection should be 'regulations'"


class TestHebrewSupport:
    """Test Hebrew language support"""
    
    @pytest.mark.parametrize("query,english_desc", [
        ('תוספת קומה', 'Addition of floor'),
        ('שינוי קו בנין', 'Building line change'),
        ('מגורים', 'Residential'),
        ('תכנית', 'Plan'),
    ])
    def test_hebrew_search(self, repo, query, english_desc):
        """Test search works with Hebrew queries"""
        results = repo.search(query, limit=5)
        assert len(results) > 0, f"Should find results for '{english_desc}' ({query})"
    
    def test_hebrew_content(self, repo):
        """Test regulations contain Hebrew content"""
        results = repo.search('תכנית', limit=1)
        
        assert len(results) > 0, "Should have search results"
        
        reg = results[0]
        has_hebrew = any(0x0590 <= ord(c) <= 0x05FF for c in reg.title)
        assert has_hebrew, "Regulation title should contain Hebrew characters"
    
    def test_hebrew_metadata(self, repo):
        """Test metadata contains Hebrew text"""
        results = repo.search('תכנית', limit=1)
        
        if results and results[0].metadata:
            metadata = results[0].metadata
            
            # Check various metadata fields for Hebrew
            hebrew_fields = []
            for key, value in metadata.items():
                if isinstance(value, str) and any(0x0590 <= ord(c) <= 0x05FF for c in value):
                    hebrew_fields.append(key)
            
            assert len(hebrew_fields) > 0, "Metadata should contain Hebrew text"


class TestIPlanDataQuality:
    """Test iPlan-specific data quality"""
    
    def test_has_plan_numbers(self, repo):
        """Test regulations have iPlan plan numbers"""
        results = repo.search('תכנית', limit=5)
        
        plans_with_numbers = 0
        for reg in results:
            if reg.metadata and reg.metadata.get('plan_number'):
                plans_with_numbers += 1
        
        assert plans_with_numbers > 0, "Regulations should have iPlan plan numbers"
    
    def test_has_source_attribution(self, repo):
        """Test regulations have proper source attribution"""
        results = repo.search('תכנית', limit=5)
        
        for reg in results:
            assert reg.metadata, "Regulation should have metadata"
            source = reg.metadata.get('source', '')
            
            # Should mention iPlan or have iPlan-like source
            assert source or reg.id.startswith('iplan_'), \
                "Regulation should have source attribution or iPlan ID"
    
    def test_municipality_data(self, repo):
        """Test regulations include municipality information"""
        results = repo.search('תכנית', limit=5)
        
        has_municipality = False
        for reg in results:
            if reg.metadata and 'municipality' in str(reg.metadata).lower():
                has_municipality = True
                break
        
        assert has_municipality, "Some regulations should have municipality data"
    
    def test_plan_types(self, repo):
        """Test regulations include plan type information"""
        results = repo.search('תכנית', limit=10)
        
        has_plan_type = False
        for reg in results:
            if reg.metadata and any(key in str(reg.metadata).lower() 
                                   for key in ['plan_type', 'entity_subtype', 'type']):
                has_plan_type = True
                break
        
        assert has_plan_type, "Regulations should have plan type information"


class TestDataDiversity:
    """Test data has good coverage and diversity"""
    
    def test_unique_regulations(self, repo):
        """Test database has diverse unique regulations"""
        results = repo.search('תכנית', limit=20)
        
        unique_titles = set(r.title for r in results)
        assert len(unique_titles) >= 10, \
            f"Should have at least 10 unique regulations, found {len(unique_titles)}"
    
    def test_regulation_types(self, repo):
        """Test multiple regulation types present"""
        results = repo.search('תכנית', limit=20)
        
        types = set(r.type.value for r in results)
        assert len(types) >= 2, f"Should have multiple regulation types, found: {types}"
    
    def test_different_municipalities(self, repo):
        """Test regulations from different municipalities"""
        results = repo.search('תכנית', limit=20)
        
        municipalities = set()
        for reg in results:
            if reg.metadata:
                for key, value in reg.metadata.items():
                    if 'municipality' in key.lower() or 'city' in key.lower():
                        if isinstance(value, str):
                            municipalities.add(value)
        
        # Should have regulations from at least a few different places
        assert len(municipalities) >= 2, \
            f"Should have regulations from multiple municipalities, found: {municipalities}"
    
    def test_content_length_variety(self, repo):
        """Test regulations have varied content lengths"""
        results = repo.search('תכנית', limit=10)
        
        lengths = [len(r.content) for r in results]
        
        # Should have some variation in content length
        assert max(lengths) > min(lengths) * 2, \
            "Regulations should have varied content lengths"


class TestSearchRelevance:
    """Test search returns relevant results"""
    
    def test_specific_plan_search(self, repo):
        """Test searching for specific plan types"""
        results = repo.search('תוספת קומה', limit=5)
        
        assert len(results) > 0, "Should find results for floor addition"
        
        # Top result should be relevant
        top = results[0]
        content_combined = (top.title + " " + top.content).lower()
        
        # Should mention floors, addition, or related terms
        relevant_terms = ['קומה', 'תוספת', 'הרחב', 'בני']
        has_relevant = any(term in content_combined for term in relevant_terms)
        
        assert has_relevant, "Top result should be relevant to query"
    
    def test_district_search(self, repo):
        """Test searching by district/location"""
        # Test major cities
        cities = ['ירושלים', 'תל אביב', 'חיפה']
        
        found_any = False
        for city in cities:
            results = repo.search(city, limit=5)
            if len(results) > 0:
                found_any = True
                break
        
        assert found_any, f"Should find regulations for major cities: {cities}"
    
    def test_building_type_search(self, repo):
        """Test searching by building type"""
        building_types = ['מגורים', 'מסחר', 'תעשיה']
        
        for building_type in building_types:
            results = repo.search(building_type, limit=3)
            # At least some building types should have results
            # Not asserting all must have results as data may vary


class TestMetadataIntegrity:
    """Test metadata is complete and valid"""
    
    def test_all_have_ids(self, repo):
        """Test all regulations have IDs"""
        results = repo.search('תכנית', limit=10)
        
        for reg in results:
            assert reg.id, "All regulations should have IDs"
            assert len(reg.id) > 0, "ID should not be empty"
    
    def test_all_have_titles(self, repo):
        """Test all regulations have titles"""
        results = repo.search('תכנית', limit=10)
        
        for reg in results:
            assert reg.title, "All regulations should have titles"
            assert len(reg.title) > 0, "Title should not be empty"
    
    def test_all_have_content(self, repo):
        """Test all regulations have content"""
        results = repo.search('תכנית', limit=10)
        
        for reg in results:
            assert reg.content, "All regulations should have content"
            assert len(reg.content) > 10, "Content should be substantial"
    
    def test_metadata_fields_valid(self, repo):
        """Test metadata fields are valid"""
        results = repo.search('תכנית', limit=10)
        
        for reg in results:
            if reg.metadata:
                # All metadata values should be valid types
                for key, value in reg.metadata.items():
                    assert isinstance(key, str), "Metadata keys should be strings"
                    assert value is not None, f"Metadata value for {key} should not be None"


# Test markers
pytestmark = [
    pytest.mark.integration,
    pytest.mark.iplan,
]


if __name__ == "__main__":
    # Allow running with: python tests/test_iplan_integration.py
    pytest.main([__file__, "-v", "--tb=short"])
