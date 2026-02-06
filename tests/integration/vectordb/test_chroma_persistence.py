import pytest
from pathlib import Path

from src.infrastructure.factory import ApplicationFactory


pytestmark = [pytest.mark.integration, pytest.mark.db, pytest.mark.vectordb]


@pytest.fixture(scope="module")
def vectorstore_path(tmp_path_factory):
    return tmp_path_factory.mktemp("vectorstore")


@pytest.fixture(scope="module")
def repo(vectorstore_path):
    factory = ApplicationFactory(chroma_persist_dir=str(vectorstore_path))
    return factory.get_regulation_repository()


def test_persist_directory__after_repo_created__exists(vectorstore_path, repo):
    assert vectorstore_path.exists()


def test_chroma_sqlite__after_init__exists_and_nonempty(vectorstore_path, repo):
    db_file = vectorstore_path / "chroma.sqlite3"
    assert db_file.exists()
    assert db_file.stat().st_size > 0


def test_collection_artifacts__after_init__exist(vectorstore_path, repo):
    # Expect sqlite + at least one collection directory.
    files = list(Path(vectorstore_path).glob("*"))
    assert len(files) > 1
