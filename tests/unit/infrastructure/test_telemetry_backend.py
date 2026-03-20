import json
import logging

import pytest

from src.telemetry import emit_observability_event, persist_ui_event

pytestmark = [pytest.mark.unit]


def _read_jsonl(path):
    with path.open("r", encoding="utf-8") as fp:
        return [json.loads(line) for line in fp if line.strip()]


def test_emit_observability_event__persists_backend_event(monkeypatch, tmp_path):
    events_path = tmp_path / "events.jsonl"
    alerts_path = tmp_path / "alerts.jsonl"

    monkeypatch.setenv("OBS_BACKEND_ENABLED", "1")
    monkeypatch.setenv("OBS_EVENTS_SINK_PATH", str(events_path))
    monkeypatch.setenv("OBS_ALERTS_SINK_PATH", str(alerts_path))

    logger = logging.getLogger("tests.telemetry.backend")
    payload = emit_observability_event(
        logger,
        component="RegulationQueryService",
        operation="regulation_query",
        request_id="req-1",
        outcome="success",
        latency_ms=120,
    )

    assert payload["outcome"] == "success"
    assert events_path.exists()

    rows = _read_jsonl(events_path)
    assert len(rows) == 1
    assert rows[0]["component"] == "RegulationQueryService"
    assert rows[0]["request_id"] == "req-1"

    assert not alerts_path.exists()


def test_emit_observability_event__routes_error_alert(monkeypatch, tmp_path):
    events_path = tmp_path / "events.jsonl"
    alerts_path = tmp_path / "alerts.jsonl"

    monkeypatch.setenv("OBS_BACKEND_ENABLED", "1")
    monkeypatch.setenv("OBS_EVENTS_SINK_PATH", str(events_path))
    monkeypatch.setenv("OBS_ALERTS_SINK_PATH", str(alerts_path))

    logger = logging.getLogger("tests.telemetry.alert.error")
    emit_observability_event(
        logger,
        component="PlanSearchService",
        operation="plan_search",
        request_id="req-2",
        outcome="error",
        level=logging.ERROR,
        error_class="RuntimeError",
        message="boom",
        latency_ms=50,
    )

    assert alerts_path.exists()
    alerts = _read_jsonl(alerts_path)
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "sev1"
    assert alerts[0]["route"] == "maintainer-oncall"
    assert "outcome=error" in alerts[0]["reasons"]


def test_emit_observability_event__routes_latency_alert(monkeypatch, tmp_path):
    events_path = tmp_path / "events.jsonl"
    alerts_path = tmp_path / "alerts.jsonl"

    monkeypatch.setenv("OBS_BACKEND_ENABLED", "1")
    monkeypatch.setenv("OBS_EVENTS_SINK_PATH", str(events_path))
    monkeypatch.setenv("OBS_ALERTS_SINK_PATH", str(alerts_path))

    logger = logging.getLogger("tests.telemetry.alert.latency")
    emit_observability_event(
        logger,
        component="RegulationQueryService",
        operation="regulation_query",
        request_id="req-3",
        outcome="success",
        latency_ms=4200,
    )

    assert alerts_path.exists()
    alerts = _read_jsonl(alerts_path)
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "sev3"
    assert "latency_ms>=4000" in alerts[0]["reasons"]


def test_emit_observability_event__below_calibrated_latency_threshold__does_not_alert(
    monkeypatch, tmp_path
):
    events_path = tmp_path / "events.jsonl"
    alerts_path = tmp_path / "alerts.jsonl"

    monkeypatch.setenv("OBS_BACKEND_ENABLED", "1")
    monkeypatch.setenv("OBS_EVENTS_SINK_PATH", str(events_path))
    monkeypatch.setenv("OBS_ALERTS_SINK_PATH", str(alerts_path))

    logger = logging.getLogger("tests.telemetry.alert.latency.below_threshold")
    emit_observability_event(
        logger,
        component="RegulationQueryService",
        operation="regulation_query",
        request_id="req-3b",
        outcome="success",
        latency_ms=3500,
    )

    assert events_path.exists()
    assert not alerts_path.exists()


def test_emit_observability_event__routes_memory_disk_saturation_alert(
    monkeypatch, tmp_path
):
    events_path = tmp_path / "events.jsonl"
    alerts_path = tmp_path / "alerts.jsonl"

    monkeypatch.setenv("OBS_BACKEND_ENABLED", "1")
    monkeypatch.setenv("OBS_EVENTS_SINK_PATH", str(events_path))
    monkeypatch.setenv("OBS_ALERTS_SINK_PATH", str(alerts_path))

    logger = logging.getLogger("tests.telemetry.alert.saturation")
    emit_observability_event(
        logger,
        component="UnifiedDataPipeline",
        operation="build",
        request_id="req-4",
        outcome="success",
        memory_used_ratio=0.96,
        disk_free_ratio_cache_dir=0.08,
    )

    assert alerts_path.exists()
    alerts = _read_jsonl(alerts_path)
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "sev2"
    assert "memory_used_ratio>=0.95" in alerts[0]["reasons"]
    assert "disk_free_ratio_cache_dir<=0.10" in alerts[0]["reasons"]


def test_persist_ui_event__writes_backend_event_without_alert(monkeypatch, tmp_path):
    events_path = tmp_path / "events.jsonl"
    alerts_path = tmp_path / "alerts.jsonl"

    monkeypatch.setenv("OBS_BACKEND_ENABLED", "1")
    monkeypatch.setenv("OBS_EVENTS_SINK_PATH", str(events_path))
    monkeypatch.setenv("OBS_ALERTS_SINK_PATH", str(alerts_path))

    logger = logging.getLogger("tests.telemetry.ui")
    payload = persist_ui_event(
        logger,
        event_name="workspace_plan_selected",
        route="/",
        plan_number="101-0001",
        context={"source": "test"},
    )

    rows = _read_jsonl(events_path)
    assert payload["kind"] == "ui_event"
    assert rows[-1]["kind"] == "ui_event"
    assert rows[-1]["operation"] == "workspace_plan_selected"
    assert rows[-1]["route"] == "/"
    assert not alerts_path.exists()
