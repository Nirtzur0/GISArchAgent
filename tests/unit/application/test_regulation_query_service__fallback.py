import pytest

from src.application.services.regulation_query_service import RegulationQueryService
from src.domain.entities.regulation import Regulation, RegulationType

from tests.helpers.fakes import FakeLLM
from tests.helpers.factories import make_regulation_query


pytestmark = [pytest.mark.unit]


class _FakeRepo:
    def __init__(self, results):
        self._results = list(results)
        self.calls = []

    def search(self, *, query: str, filters=None, limit: int = 10):
        self.calls.append({"query": query, "filters": filters, "limit": limit})
        return self._results[:limit]


def test_query__no_llm__returns_fallback_answer_when_results_exist():
    # Arrange
    regs = [
        Regulation(id="r1", type=RegulationType.LOCAL, title="Parking", content="...", jurisdiction="national"),
        Regulation(id="r2", type=RegulationType.TAMA, title="Green", content="...", jurisdiction="national"),
    ]
    repo = _FakeRepo(regs)
    svc = RegulationQueryService(regulation_repository=repo, llm_service=None)

    q = make_regulation_query(query_text="parking requirements", location="national", max_results=5)

    # Act
    result = svc.query(q)

    # Assert
    assert result.total_found == 2
    assert len(result.regulations) == 2
    assert isinstance(result.answer, str)
    assert "LLM synthesis is not configured" in result.answer


def test_query__with_llm__uses_llm_answer():
    # Arrange
    regs = [Regulation(id="r1", type=RegulationType.LOCAL, title="Parking", content="...", jurisdiction="national")]
    repo = _FakeRepo(regs)
    llm = FakeLLM(answer="hello")
    svc = RegulationQueryService(regulation_repository=repo, llm_service=llm)

    q = make_regulation_query(query_text="parking requirements", location="national", max_results=5)

    # Act
    result = svc.query(q)

    # Assert
    assert result.total_found == 1
    assert result.answer == "hello"
    assert llm.calls and llm.calls[0]["question"] == "parking requirements"


def test_query__location_not_national__filters_by_applies_to_location():
    # Arrange
    regs = [
        Regulation(id="ta", type=RegulationType.LOCAL, title="TA", content="...", jurisdiction="Tel Aviv"),
        Regulation(id="haifa", type=RegulationType.LOCAL, title="Haifa", content="...", jurisdiction="Haifa"),
    ]
    repo = _FakeRepo(regs)
    svc = RegulationQueryService(regulation_repository=repo, llm_service=None)

    q = make_regulation_query(query_text="something", location="Tel Aviv", max_results=5)

    # Act
    result = svc.query(q)

    # Assert
    assert [r.id for r in result.regulations] == ["ta"]


def test_query__location_national__does_not_filter_by_location():
    # Arrange
    regs = [
        Regulation(id="ta", type=RegulationType.LOCAL, title="TA", content="...", jurisdiction="Tel Aviv"),
        Regulation(id="haifa", type=RegulationType.LOCAL, title="Haifa", content="...", jurisdiction="Haifa"),
    ]
    repo = _FakeRepo(regs)
    svc = RegulationQueryService(regulation_repository=repo, llm_service=None)

    q = make_regulation_query(query_text="something", location="national", max_results=5)

    # Act
    result = svc.query(q)

    # Assert
    assert [r.id for r in result.regulations] == ["ta", "haifa"]
