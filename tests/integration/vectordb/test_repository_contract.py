import pytest
import chromadb
from chromadb.config import Settings

from src.infrastructure.factory import ApplicationFactory

from tests.helpers.assertions import assert_required_fields, assert_unique


pytestmark = [pytest.mark.integration, pytest.mark.db, pytest.mark.vectordb]


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


def test_get_statistics__after_init__contains_expected_keys(repo):
    stats = repo.get_statistics()
    assert_required_fields(stats, fields=["total_regulations", "collection_name", "persist_directory"], context="repo.get_statistics")
    assert stats["total_regulations"] > 0


def test_search__english_query__returns_regulations_with_required_fields(repo):
    results = repo.search("parking", limit=5)
    assert results

    for r in results:
        assert_required_fields(r, fields=["id", "title", "type", "content"], context="repo.search:parking")


def test_search__hebrew_query__returns_hebrew_title(repo):
    results = repo.search("תכנית", limit=5)
    assert results

    top = results[0]
    has_hebrew = any(0x0590 <= ord(c) <= 0x05FF for c in top.title)
    assert has_hebrew


def test_search_by_text__returns_scored_matches(repo):
    matches = repo.search_by_text("parking", limit=5)
    assert matches

    for m in matches:
        assert_required_fields(m, fields=["regulation", "similarity"], context="repo.search_by_text")
        assert 0.0 <= float(m["similarity"]) <= 1.0


def test_chroma_collection__metadata_contract__has_required_keys(chroma_client):
    collection = chroma_client.get_collection("regulations")
    got = collection.get(limit=10)

    metadatas = got.get("metadatas") or []
    assert metadatas

    for md in metadatas:
        assert_required_fields(md, fields=["id", "title", "type", "jurisdiction"], context="chroma.get:metadatas")
        assert all(v is not None for v in md.values())


def test_search_results__ids_unique_within_page(repo):
    results = repo.search("תכנית", limit=20)
    assert results

    assert_unique([r.id for r in results], context="repo.search:ids")
