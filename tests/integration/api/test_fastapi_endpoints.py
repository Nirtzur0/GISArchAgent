import importlib
import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


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

    import src.api.app as api_app_module

    reloaded = importlib.reload(api_app_module)
    app = reloaded.create_app()
    return TestClient(app)


def test_health__reports_provider_shape(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "base_url" in payload["provider"]


def test_system_status__returns_core_sections(client):
    response = client.get("/api/system/status")
    assert response.status_code == 200
    payload = response.json()
    assert "vector_db" in payload
    assert "data_store" in payload


def test_regulation_query__returns_sources(client):
    response = client.post(
        "/api/regulations/query",
        json={"query_text": "parking requirements", "max_results": 5},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_found"] >= 1
    assert len(payload["regulations"]) >= 1


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
