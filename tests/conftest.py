"""
Pytest configuration for GIS Architecture Agent tests
"""

import sys
from pathlib import Path

# Add project root to path for all tests
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers", "vectordb: mark test as vector database test"
    )
    config.addinivalue_line(
        "markers", "iplan: mark test as iPlan data test"
    )
    config.addinivalue_line(
        "markers", "data_contracts: mark test as a data contract/range/completeness check"
    )
    config.addinivalue_line(
        "markers", "db: mark test as touching a DB/persistence boundary"
    )
    config.addinivalue_line(
        "markers", "ui: mark test as executing UI scripts"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring real network access"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
