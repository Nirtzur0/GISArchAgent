import pytest

from src.infrastructure.factory import ApplicationFactory
from src.application.dtos import RegulationQuery

from tests.helpers.assertions import assert_required_fields


pytestmark = [pytest.mark.integration, pytest.mark.db, pytest.mark.vectordb]


@pytest.fixture(scope="module")
def vectorstore_path(tmp_path_factory):
    return tmp_path_factory.mktemp("vectorstore")


@pytest.fixture(scope="module")
def factory(vectorstore_path):
    return ApplicationFactory(chroma_persist_dir=str(vectorstore_path))


def test_query__without_llm__returns_consistent_result(factory):
    # Arrange
    svc = factory.get_regulation_query_service()
    q = RegulationQuery(query_text="parking requirements", location="national")

    # Act
    result = svc.query(q)

    # Assert
    assert_required_fields(result, fields=["total_found", "regulations", "query"], context="RegulationQueryService.query")
    assert result.total_found == len(result.regulations)

    # No LLM configured in tests by default; fallback answer should exist when results exist.
    assert result.total_found > 0
    assert isinstance(result.answer, str)
    assert result.answer
