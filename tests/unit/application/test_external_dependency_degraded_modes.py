import pytest

from src.application.dtos import PlanSearchQuery
from src.application.services.plan_search_service import PlanSearchService
from src.application.services.regulation_query_service import RegulationQueryService
from src.domain.entities.plan import Plan, PlanStatus, ZoneType
from src.domain.entities.regulation import Regulation, RegulationType

from tests.helpers.factories import make_regulation_query

pytestmark = [pytest.mark.unit]


class _FakeRegulationRepo:
    def __init__(self, results):
        self._results = list(results)

    def search(self, *, query: str, filters=None, limit: int = 10):
        return self._results[:limit]


class _FailingLLM:
    def generate_answer(self, *, question: str, context: str) -> str:
        raise RuntimeError("simulated llm outage")


class _FakePlanRepo:
    def __init__(
        self, plans, *, error_signal=None, image_bytes: bytes | None = b"fake"
    ):
        self._plans = list(plans)
        self._error_signal = error_signal
        self._image_bytes = image_bytes

    def consume_last_error(self):
        payload = self._error_signal
        self._error_signal = None
        return payload

    def get_by_id(self, plan_id: str):
        return self._plans[0] if self._plans else None

    def search_by_location(self, location: str, limit: int = 10):
        return self._plans[:limit]

    def search_by_keyword(self, keyword: str, limit: int = 10):
        return self._plans[:limit]

    def search_by_status(self, status: str, location=None, limit: int = 10):
        return self._plans[:limit]

    def get_plan_image(self, plan_id: str):
        return self._image_bytes


def _make_plan(plan_id: str = "101-0001") -> Plan:
    return Plan(
        id=plan_id,
        name="Demo Plan",
        location="Tel Aviv",
        status=PlanStatus.APPROVED,
        zone_type=ZoneType.RESIDENTIAL,
    )


def test_query__llm_failure__falls_back_and_emits_degraded(monkeypatch):
    events = []

    def _capture_event(_logger, **payload):
        events.append(payload)
        return payload

    import src.application.services.regulation_query_service as module

    monkeypatch.setattr(module, "emit_observability_event", _capture_event)

    repo = _FakeRegulationRepo(
        [
            Regulation(
                id="r1",
                type=RegulationType.LOCAL,
                title="Parking",
                content="Minimum parking requirements",
                jurisdiction="national",
            )
        ]
    )
    svc = RegulationQueryService(regulation_repository=repo, llm_service=_FailingLLM())

    result = svc.query(make_regulation_query(query_text="parking", location="national"))

    assert result.total_found == 1
    assert isinstance(result.answer, str) and result.answer
    assert "LLM synthesis is unavailable" in result.answer

    assert events and events[-1]["outcome"] == "degraded"
    assert "llm_synthesis_unavailable" in events[-1]["degraded_reasons"]


def test_search_plans__repo_error_signal__emits_degraded(monkeypatch):
    events = []

    def _capture_event(_logger, **payload):
        events.append(payload)
        return payload

    import src.application.services.plan_search_service as module

    monkeypatch.setattr(module, "emit_observability_event", _capture_event)

    repo = _FakePlanRepo(
        [],
        error_signal={
            "operation": "search_by_location",
            "error_class": "ReadTimeout",
            "message": "simulated timeout",
        },
    )
    svc = PlanSearchService(
        plan_repository=repo, vision_service=None, cache_service=None
    )

    result = svc.search_plans(
        PlanSearchQuery(
            location="Tel Aviv", include_vision_analysis=False, max_results=3
        )
    )

    assert result.total_found == 0
    assert events and events[-1]["outcome"] == "degraded"
    assert "iplan_search_by_location_failed" in events[-1]["degraded_reasons"]


def test_search_plans__vision_requested_without_service__emits_degraded(monkeypatch):
    events = []

    def _capture_event(_logger, **payload):
        events.append(payload)
        return payload

    import src.application.services.plan_search_service as module

    monkeypatch.setattr(module, "emit_observability_event", _capture_event)

    repo = _FakePlanRepo([_make_plan()])
    svc = PlanSearchService(
        plan_repository=repo, vision_service=None, cache_service=None
    )

    result = svc.search_plans(
        PlanSearchQuery(
            location="Tel Aviv", include_vision_analysis=True, max_results=3
        )
    )

    assert result.total_found == 1
    assert len(result.plans) == 1
    assert events and events[-1]["outcome"] == "degraded"
    assert "vision_service_unavailable" in events[-1]["degraded_reasons"]
