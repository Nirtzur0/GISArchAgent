import pytest
import chromadb
from chromadb.config import Settings

from src.infrastructure.factory import ApplicationFactory

from tests.helpers.assertions import assert_required_fields


pytestmark = [pytest.mark.integration, pytest.mark.db, pytest.mark.data_contracts]


@pytest.fixture(scope="module")
def vectorstore_path(tmp_path_factory):
    return tmp_path_factory.mktemp("vectorstore")


@pytest.fixture(scope="module")
def factory(vectorstore_path):
    return ApplicationFactory(chroma_persist_dir=str(vectorstore_path))


@pytest.fixture(scope="module")
def repo(factory):
    return factory.get_regulation_repository()


@pytest.fixture(scope="module")
def chroma_client(vectorstore_path):
    return chromadb.PersistentClient(path=str(vectorstore_path), settings=Settings(anonymized_telemetry=False))


def test_chroma_metadata__required_keys_present__no_null_values(chroma_client, repo):
    # Ensure the repository was instantiated (it creates the collection).
    _ = repo
    collection = chroma_client.get_collection("regulations")
    got = collection.get(limit=20)

    metadatas = got.get("metadatas") or []
    assert metadatas

    for md in metadatas:
        assert_required_fields(md, fields=["id", "title", "type", "jurisdiction"], context="integration:chroma:metadata")
        assert all(v is not None for v in md.values())


def test_repository_entities__required_fields_present(repo):
    results = repo.search("תכנית", limit=10)
    assert results

    for r in results:
        assert_required_fields(r, fields=["id", "title", "type", "content"], context="integration:repo.search")
