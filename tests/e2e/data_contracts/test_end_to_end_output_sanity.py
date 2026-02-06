import pytest

from src.infrastructure.factory import ApplicationFactory
from src.application.dtos import RegulationQuery

from tests.helpers.assertions import assert_required_fields, assert_unique


pytestmark = [pytest.mark.e2e, pytest.mark.data_contracts]


def test_regulation_query_flow__happy_path__outputs_sane(tmp_path):
    # Arrange
    vectorstore_path = tmp_path / "vectorstore"
    factory = ApplicationFactory(chroma_persist_dir=str(vectorstore_path))
    svc = factory.get_regulation_query_service()

    q = RegulationQuery(query_text="parking requirements", location="national")

    # Act
    result = svc.query(q)

    # Assert
    assert_required_fields(result, fields=["total_found", "regulations", "answer"], context="e2e:regulation_query")
    assert result.total_found == len(result.regulations)
    assert result.total_found > 0
    assert isinstance(result.answer, str) and result.answer.strip()

    assert_unique([r.id for r in result.regulations], context="e2e:regulation_query:ids")

    for r in result.regulations:
        assert_required_fields(r, fields=["id", "title", "type", "content"], context="e2e:regulation")
