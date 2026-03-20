import importlib
import shutil

import pytest
from fastapi.testclient import TestClient


pytestmark = [pytest.mark.e2e]


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
    return TestClient(reloaded.create_app())


def test_fastapi_core_flow__smoke(client):
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["provider"]["configured"] is False

    plans = client.get("/api/data/search")
    assert plans.status_code == 200
    payload = plans.json()
    assert payload["total"] >= 1

    plan_number = payload["items"][0]["attributes"]["pl_number"]
    overview = client.get(f"/api/workspace/overview?plan_number={plan_number}")
    assert overview.status_code == 200
    assert overview.json()["selected_plan"]["attributes"]["pl_number"] == plan_number

    regulation = client.post(
        "/api/regulations/query",
        json={"query_text": "parking requirements", "location": "national"},
    )
    assert regulation.status_code == 200
    regulation_payload = regulation.json()
    assert regulation_payload["total_found"] >= 1
    assert regulation_payload["answer_status"] in {
        "synthesized",
        "retrieval_only",
        "no_results",
    }

    rights = client.post(
        "/api/building-rights/calculate",
        json={
            "plot_size_sqm": 500,
            "zone_type": "R2",
            "location": "Tel Aviv",
            "include_regulations": True,
        },
    )
    assert rights.status_code == 200
    assert rights.json()["building_rights"]["max_floors"] >= 1


def test_fastapi_operations_flow__smoke(client):
    operations = client.get("/api/operations/overview")
    assert operations.status_code == 200
    operations_payload = operations.json()
    assert operations_payload["inventory"]["total_plans"] >= 1
    assert operations_payload["scraper"]["status"] == "unvalidated"

    data_status = client.get("/api/data/status")
    assert data_status.status_code == 200
    assert data_status.json()["total_plans"] >= 1

    vectordb_status = client.get("/api/vectordb/status")
    assert vectordb_status.status_code == 200
    assert "status" in vectordb_status.json()

    fetcher_health = client.get("/api/data/fetcher-health?probe_limit=1&timeout_seconds=5")
    assert fetcher_health.status_code == 200
    assert fetcher_health.json()["status"] in {"skipped", "unvalidated"}
