import json

import pytest
import requests

from src.application.dtos import PlanSearchQuery
from src.application.services.plan_search_service import PlanSearchService
from src.domain.entities.plan import Plan, PlanStatus, ZoneType
from src.infrastructure.repositories.iplan_repository import IPlanGISRepository

pytestmark = [pytest.mark.integration, pytest.mark.iplan]


def _read_jsonl(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fp:
        return [json.loads(line) for line in fp if line.strip()]


def _make_plan(plan_id: str = "101-0001") -> Plan:
    return Plan(
        id=plan_id,
        name="Drill Plan",
        location="Tel Aviv",
        status=PlanStatus.APPROVED,
        zone_type=ZoneType.RESIDENTIAL,
    )


@pytest.mark.parametrize(
    ("query", "expected_reason"),
    [
        (
            PlanSearchQuery(
                location="Tel Aviv", include_vision_analysis=False, max_results=2
            ),
            "iplan_search_by_location_failed",
        ),
        (
            PlanSearchQuery(
                keyword="מגורים", include_vision_analysis=False, max_results=2
            ),
            "iplan_search_by_keyword_failed",
        ),
        (
            PlanSearchQuery(
                location="Tel Aviv",
                status="approved",
                include_vision_analysis=False,
                max_results=2,
            ),
            "iplan_search_by_status_failed",
        ),
        (
            PlanSearchQuery(
                plan_id="101-0001", include_vision_analysis=False, max_results=2
            ),
            "iplan_get_by_id_failed",
        ),
    ],
    ids=[
        "location-query-failure",
        "keyword-query-failure",
        "status-query-failure",
        "plan-id-query-failure",
    ],
)
def test_plan_search__query_boundary_failure_drill__emits_degraded_reason_and_alert(
    monkeypatch, tmp_path, query, expected_reason
):
    events_path = tmp_path / "events.jsonl"
    alerts_path = tmp_path / "alerts.jsonl"
    monkeypatch.setenv("OBS_BACKEND_ENABLED", "1")
    monkeypatch.setenv("OBS_EVENTS_SINK_PATH", str(events_path))
    monkeypatch.setenv("OBS_ALERTS_SINK_PATH", str(alerts_path))

    repo = IPlanGISRepository(timeout=1)

    def _raise_timeout(*args, **kwargs):
        raise requests.exceptions.ReadTimeout("simulated drill timeout")

    monkeypatch.setattr(repo._session, "get", _raise_timeout)

    service = PlanSearchService(
        plan_repository=repo, vision_service=None, cache_service=None
    )
    result = service.search_plans(query)

    assert result.total_found == 0

    events = _read_jsonl(events_path)
    degraded_events = [
        row
        for row in events
        if row.get("operation") == "plan_search" and row.get("outcome") == "degraded"
    ]
    assert degraded_events
    assert expected_reason in degraded_events[-1].get("degraded_reasons", [])

    alerts = _read_jsonl(alerts_path)
    assert alerts
    assert alerts[-1]["severity"] == "sev2"
    assert "outcome=degraded" in alerts[-1]["reasons"]


def test_plan_search__image_boundary_failure_drill__emits_get_plan_image_reason_and_alert(
    monkeypatch, tmp_path
):
    events_path = tmp_path / "events.jsonl"
    alerts_path = tmp_path / "alerts.jsonl"
    monkeypatch.setenv("OBS_BACKEND_ENABLED", "1")
    monkeypatch.setenv("OBS_EVENTS_SINK_PATH", str(events_path))
    monkeypatch.setenv("OBS_ALERTS_SINK_PATH", str(alerts_path))

    repo = IPlanGISRepository(timeout=1)
    plan = _make_plan()

    monkeypatch.setattr(repo, "search_by_location", lambda location, limit=10: [plan])

    def _failing_get_plan_image(plan_id: str):
        repo._record_error("get_plan_image", RuntimeError("simulated export failure"))
        return None

    monkeypatch.setattr(repo, "get_plan_image", _failing_get_plan_image)

    service = PlanSearchService(
        plan_repository=repo, vision_service=None, cache_service=None
    )
    result = service.search_plans(
        PlanSearchQuery(
            location="Tel Aviv", include_vision_analysis=True, max_results=1
        )
    )

    assert result.total_found == 1
    assert len(result.plans) == 1

    events = _read_jsonl(events_path)
    degraded_events = [
        row
        for row in events
        if row.get("operation") == "plan_search" and row.get("outcome") == "degraded"
    ]
    assert degraded_events
    degraded_reasons = degraded_events[-1].get("degraded_reasons", [])
    assert "iplan_get_plan_image_failed" in degraded_reasons
    assert "vision_service_unavailable" in degraded_reasons

    alerts = _read_jsonl(alerts_path)
    assert alerts
    assert alerts[-1]["severity"] == "sev2"
    assert "outcome=degraded" in alerts[-1]["reasons"]
