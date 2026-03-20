import importlib
import json
import shutil
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.application.dtos import AnalyzedPlan, PlanSearchQuery, PlanSearchResult
from src.domain.entities.plan import Plan, PlanStatus, ZoneType


pytestmark = [pytest.mark.integration]


@pytest.fixture()
def client(tmp_path, monkeypatch):
    vectorstore_dir = tmp_path / "vectorstore"
    cache_dir = tmp_path / "cache"
    data_file = tmp_path / "iplan_layers.json"
    shutil.copyfile("data/samples/iplan_sample_data.json", data_file)

    monkeypatch.setenv("GISARCHAGENT_VECTORSTORE_DIR", str(vectorstore_dir))
    monkeypatch.setenv("GISARCHAGENT_CACHE_DIR", str(cache_dir))
    monkeypatch.setenv("GISARCHAGENT_DATA_FILE", str(data_file))
    monkeypatch.setenv("GISARCHAGENT_SKIP_FETCHER_PROBE", "1")
    monkeypatch.setenv("OPENAI_BASE_URL", "")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    import src.api.app as api_app_module

    reloaded = importlib.reload(api_app_module)
    app = reloaded.create_app()
    return TestClient(app)


def test_health__reports_provider_shape(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ok", "degraded"}
    assert "base_url" in payload["provider"]
    assert "scraping" in payload
    assert payload["provider"]["configured"] is False
    assert payload["provider"]["text"]["status"] == "unconfigured"


def test_system_status__returns_core_sections(client):
    response = client.get("/api/system/status")
    assert response.status_code == 200
    payload = response.json()
    assert "vector_db" in payload
    assert "data_store" in payload
    assert "provider" in payload
    assert "scraping" in payload


def test_workspace_overview__returns_summary_and_selected_plan(client):
    search_payload = client.get("/api/data/search").json()
    plan_number = search_payload["items"][0]["attributes"]["pl_number"]

    response = client.get(f"/api/workspace/overview?plan_number={plan_number}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary_metrics"]["tracked_plans"] >= 1
    assert payload["selected_plan"]["attributes"]["pl_number"] == plan_number
    assert payload["brief"]["title"]
    assert payload["shareable_brief"]
    assert payload["summary_metrics"]["vector_status"] == "healthy"
    assert "Vector DB status: Healthy" in payload["shareable_brief"]


def test_operations_overview__returns_grouped_status(client):
    response = client.get("/api/operations/overview")
    assert response.status_code == 200
    payload = response.json()
    assert payload["inventory"]["total_plans"] >= 1
    assert "provider" in payload
    assert "scraper" in payload
    assert "vector_db" in payload
    assert payload["recommended_actions"]
    assert payload["freshness"]["last_updated"] == payload["freshness"]["fetched_at"]
    assert payload["freshness"]["source"] == "iPlan ArcGIS REST API"


def test_ui_events__persists_lightweight_event(client):
    response = client.post(
        "/api/ui/events",
        json={
            "event_name": "workspace_plan_selected",
            "route": "/",
            "plan_number": "101-0001",
            "context": {"source": "playwright"},
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["event_id"]
    assert payload["received_at"]


def test_regulation_query__returns_sources(client):
    response = client.post(
        "/api/regulations/query",
        json={"query_text": "parking requirements", "max_results": 5},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_found"] >= 1
    assert len(payload["regulations"]) >= 1
    assert payload["answer_status"] in {"synthesized", "retrieval_only", "no_results"}


def test_building_rights__returns_metrics(client):
    response = client.post(
        "/api/building-rights/calculate",
        json={
            "plot_size_sqm": 500,
            "zone_type": "R2",
            "location": "Tel Aviv",
            "include_regulations": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["building_rights"]["max_floors"] >= 1


def test_data_search__returns_geo_items(client):
    response = client.get("/api/data/search")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 1
    assert payload["items"][0]["attributes"]["pl_number"]


def test_data_import_and_vectordb_mutations__work_on_temp_state(client, tmp_path):
    new_feature = {
        "attributes": {
            "pl_number": "999-TEST",
            "pl_name": "Temporary imported plan",
            "district_name": "Test District",
            "plan_county_name": "Test City",
            "station_desc": "Draft",
            "pl_area_dunam": 1.2,
        },
        "geometry": {"rings": [[[220000, 630000], [220010, 630000], [220010, 630010], [220000, 630010], [220000, 630000]]]},
    }

    import_response = client.post(
        "/api/data/import",
        files={"file": ("import.json", json.dumps({"features": [new_feature]}), "application/json")},
    )
    assert import_response.status_code == 200
    assert import_response.json()["added"] == 1

    add_reg_response = client.post(
        "/api/vectordb/regulations",
        json={
            "title": "Temporary Regulation",
            "content": "Temporary regulation content for testing.",
            "reg_type": "local",
            "jurisdiction": "Test City",
        },
    )
    assert add_reg_response.status_code == 200

    search_response = client.post(
        "/api/vectordb/search",
        json={"query": "Temporary regulation", "limit": 5},
    )
    assert search_response.status_code == 200
    assert search_response.json()["total"] >= 1


def test_fetcher_health__returns_probe_payload(client):
    response = client.get("/api/data/fetcher-health?probe_limit=1&timeout_seconds=5")
    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "iplan"
    assert "status" in payload


def test_health_surfaces__default_scraper_state_is_unvalidated_without_probe(client, monkeypatch):
    import src.api.app as api_app_module

    def _unexpected_fetch(**kwargs):
        raise AssertionError("Passive health surfaces must not launch a live probe")

    monkeypatch.setattr(api_app_module, "_execute_fetch", _unexpected_fetch)

    health_payload = client.get("/api/health").json()
    operations_payload = client.get("/api/operations/overview").json()
    system_payload = client.get("/api/system/status").json()

    assert health_payload["scraping"]["status"] == "unvalidated"
    assert health_payload["scraping"]["runtime_ready"] is False
    assert operations_payload["scraper"]["status"] == "unvalidated"
    assert system_payload["scraping"]["status"] == "unvalidated"


def test_fetcher_health__successful_probe_is_cached_for_status_endpoints(client, monkeypatch):
    import src.api.app as api_app_module

    monkeypatch.delenv("GISARCHAGENT_SKIP_FETCHER_PROBE", raising=False)

    monkeypatch.setattr(
        api_app_module,
        "_execute_fetch",
        lambda **kwargs: {
            "metadata": {
                "status": "success",
                "fetched_at": "2026-03-11T10:00:00+00:00",
            },
            "features": [{"attributes": {"pl_number": "101-0001"}}],
        },
    )

    probe_payload = client.get("/api/data/fetcher-health?probe_limit=1&timeout_seconds=5").json()
    health_payload = client.get("/api/health").json()
    operations_payload = client.get("/api/operations/overview").json()
    system_payload = client.get("/api/system/status").json()

    assert probe_payload["status"] == "ready"
    assert probe_payload["runtime_ready"] is True
    assert probe_payload["last_probe_count"] == 1
    assert health_payload["scraping"]["status"] == "ready"
    assert operations_payload["scraper"]["runtime_ready"] is True
    assert system_payload["scraping"]["status"] == "ready"


def test_fetcher_health__timeout_probe_is_cached_with_detail(client, monkeypatch):
    import src.api.app as api_app_module

    monkeypatch.delenv("GISARCHAGENT_SKIP_FETCHER_PROBE", raising=False)

    monkeypatch.setattr(
        api_app_module,
        "_execute_fetch",
        lambda **kwargs: {
            "metadata": {
                "status": "timeout",
                "error": "Scrape timed out before the provider returned data.",
                "fetched_at": None,
            },
            "features": [],
        },
    )

    probe_payload = client.get("/api/data/fetcher-health?probe_limit=1&timeout_seconds=5").json()
    operations_payload = client.get("/api/operations/overview").json()

    assert probe_payload["status"] == "timeout"
    assert probe_payload["runtime_ready"] is False
    assert "timed out" in probe_payload["detail"]
    assert operations_payload["scraper"]["status"] == "timeout"
    assert operations_payload["freshness"]["probe_detail"] == probe_payload["detail"]


def test_live_plan_search__defaults_to_no_vision_and_returns_payload(client, monkeypatch):
    import src.api.app as api_app_module

    class _FakePlanSearchService:
        def search_plans(self, query: PlanSearchQuery) -> PlanSearchResult:
            assert query.include_vision_analysis is False
            return PlanSearchResult(
                plans=[
                    AnalyzedPlan(
                        plan=Plan(
                            id="LIVE-101",
                            name="Live Test Plan",
                            location="Tel Aviv",
                            region="Tel Aviv District",
                            status=PlanStatus.APPROVED,
                            zone_type=ZoneType.RESIDENTIAL,
                            document_url="https://example.com/live-plan",
                        )
                    )
                ],
                query=query,
                total_found=1,
                execution_time_ms=12.5,
            )

    monkeypatch.setattr(
        api_app_module.ctx.factory,
        "get_plan_search_service",
        lambda: _FakePlanSearchService(),
    )

    response = client.get("/api/plans/search?location=Tel+Aviv&max_results=1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["query"]["include_vision_analysis"] is False
    assert payload["total_found"] == 1
    assert payload["plans"][0]["plan"]["id"] == "LIVE-101"


def test_live_plan_search__timeout_returns_warning_payload(client, monkeypatch):
    import src.api.app as api_app_module

    class _SlowPlanSearchService:
        def search_plans(self, query: PlanSearchQuery) -> PlanSearchResult:
            time.sleep(0.05)
            return PlanSearchResult(
                plans=[],
                query=query,
                total_found=0,
                execution_time_ms=50.0,
            )

    monkeypatch.setattr(api_app_module, "LIVE_PLAN_SEARCH_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(
        api_app_module.ctx.factory,
        "get_plan_search_service",
        lambda: _SlowPlanSearchService(),
    )

    response = client.get("/api/plans/search?location=Jerusalem&max_results=1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["warning_code"] == "live_search_timeout"
    assert "timed out" in payload["warning"]
    assert payload["total_found"] == 0
