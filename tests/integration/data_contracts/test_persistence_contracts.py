import json
import pytest

from src.infrastructure.factory import ApplicationFactory

from tests.helpers.assertions import assert_required_fields


pytestmark = [pytest.mark.integration, pytest.mark.db, pytest.mark.data_contracts]


@pytest.fixture(scope="module")
def vectorstore_path(tmp_path_factory):
    return tmp_path_factory.mktemp("vectorstore")


def test_persistence_artifacts__after_factory_init__exist(vectorstore_path):
    # Arrange
    factory = ApplicationFactory(chroma_persist_dir=str(vectorstore_path))

    # Act
    _ = factory.get_regulation_repository()

    # Assert
    db_file = vectorstore_path / "chroma.sqlite3"
    assert db_file.exists()

    metadata_file = vectorstore_path / "metadata.json"
    assert metadata_file.exists(), "Expected health-check metadata to be stored alongside the persist dir"

    data = json.loads(metadata_file.read_text(encoding="utf-8"))
    assert_required_fields(data, fields=["last_updated", "total_regulations"], context="integration:metadata.json")
    assert int(data["total_regulations"]) > 0
