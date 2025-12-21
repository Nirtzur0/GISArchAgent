# Tests

**Professional pytest test suite** for the GIS Architecture Agent.

## Quick Start

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_vectordb_integration.py

# Run specific test class
pytest tests/test_iplan_integration.py::TestHebrewSupport

# Run tests by marker
pytest -m vectordb          # Only vector DB tests
pytest -m iplan             # Only iPlan tests
pytest -m "not slow"        # Skip slow tests
```

## Test Structure

### test_vectordb_integration.py
Comprehensive vector database integration tests organized in pytest classes:

**Classes:**
- `TestChromaDBPersistence` - File storage and persistence
- `TestChromaDBConnection` - Direct database connection
- `TestRepositoryIntegration` - Repository pattern integration
- `TestServiceIntegration` - End-to-end service tests
- `TestDataQuality` - Data quality and freshness
- `TestVectorSearch` - Semantic search functionality

**Total Tests:** ~25 test functions

**Usage:**
```bash
# Run all vector DB tests
pytest tests/test_vectordb_integration.py -v

# Run specific test class
pytest tests/test_vectordb_integration.py::TestVectorSearch -v

# Run with markers
pytest -m vectordb
```

---

### test_iplan_integration.py
iPlan data integration tests with pytest fixtures:

**Classes:**
- `TestDatabasePopulation` - Database content verification
- `TestHebrewSupport` - Hebrew language support (with parametrize)
- `TestIPlanDataQuality` - iPlan-specific data quality
- `TestDataDiversity` - Coverage and variety
- `TestSearchRelevance` - Search result quality
- `TestMetadataIntegrity` - Metadata validation

**Total Tests:** ~30 test functions (including parametrized)

**Usage:**
```bash
# Run all iPlan tests
pytest tests/test_iplan_integration.py -v

# Run Hebrew search tests
pytest tests/test_iplan_integration.py::TestHebrewSupport -v

# Run with markers
pytest -m iplan
```

---

## Test Markers

Tests are organized with pytest markers:

- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.vectordb` - Vector database tests
- `@pytest.mark.iplan` - iPlan data tests
- `@pytest.mark.slow` - Slow running tests

**Usage:**
```bash
# Run only integration tests
pytest -m integration

# Run everything except slow tests
pytest -m "not slow"

# Combine markers
pytest -m "integration and vectordb"
```

## Test Fixtures

Shared fixtures defined in `conftest.py`:

- `factory` - ApplicationFactory instance (module scope)
- `repo` - Regulation repository (module scope)
- `project_root` - Project root path
- `vectorstore_path` - Vector store directory
- `chroma_client` - Direct ChromaDB client

Module-scoped fixtures are created once per test file for efficiency.

## Configuration

Tests are configured via `pytest.ini` in project root:

```ini
[pytest]
testpaths = tests
markers = integration, vectordb, iplan, slow
addopts = -v --strict-markers --tb=short
```

## Running Tests

### Local Development
```bash
# Run all tests with coverage
pytest --cov=src tests/

# Run fast tests only
pytest -m "not slow"

# Run with live output
pytest -v -s

# Run specific test
pytest tests/test_vectordb_integration.py::test_database_file_exists
```

### CI/CD
```bash
# Run all tests with XML output for CI
pytest --junitxml=test-results.xml

# Run with strict mode
pytest --strict-markers --strict-config
```

## Writing New Tests

### Test File Template
```python
"""Test description"""

import pytest
from src.infrastructure.factory import ApplicationFactory


@pytest.fixture(scope="module")
def repo():
    """Repository fixture"""
    factory = ApplicationFactory()
    return factory.get_regulation_repository()


class TestFeature:
    """Test feature description"""
    
    def test_something(self, repo):
        """Test specific behavior"""
        result = repo.search("query")
        assert result is not None
```

### Best Practices
- ✅ Use descriptive test names starting with `test_`
- ✅ Organize tests in classes for grouping
- ✅ Use fixtures for shared setup
- ✅ Use parametrize for multiple test cases
- ✅ Add markers for categorization
- ✅ Keep tests independent
- ✅ Use clear assertion messages

## Continuous Integration

Add to `.github/workflows/test.yml`:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run pytest
        run: pytest -v --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Test Requirements

These tests require:
- ChromaDB initialized with data
- Vector database at `data/vectorstore/`
- At least some regulations loaded

## First Time Setup

If tests fail because database is empty:

```bash
# Initialize database with iPlan data
python3 src/data_pipeline/cli/pipeline.py run --source iplan --limit 1000

# Or reinitialize completely
python3 scripts/utilities/reinitialize_vectordb.py

# Then run tests
python3 tests/test_vectordb_integration.py
```

## Continuous Integration

These tests can be integrated into CI/CD:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: |
          python3 tests/test_vectordb_integration.py
          python3 tests/test_iplan_integration.py
```

## Troubleshooting

### "Database is empty"
Run initialization:
```bash
python3 src/data_pipeline/cli/pipeline.py run --source iplan --limit 100
```

### "No module named 'src'"
Ensure you run from project root:
```bash
cd /path/to/GISArchAgent
python3 tests/test_vectordb_integration.py
```

### "ChromaDB not found"
Install dependencies:
```bash
pip install -r requirements.txt
```
