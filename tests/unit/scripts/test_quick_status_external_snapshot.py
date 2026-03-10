import importlib.util
from pathlib import Path
import sys

import pytest


pytestmark = pytest.mark.unit


def _load_quick_status_module():
    module_path = Path(__file__).resolve().parents[3] / "scripts" / "quick_status.py"
    spec = importlib.util.spec_from_file_location("quick_status", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_bucket_external_reasons_groups_provider_boundaries():
    quick_status = _load_quick_status_module()

    buckets = quick_status._bucket_external_reasons(
        {
            "iplan_search_by_location_failed": 2,
            "mavat_attachment_unreachable": 1,
            "llm_synthesis_unavailable": 3,
            "vision_service_unavailable": 4,
            "unexpected_reason": 5,
        }
    )

    assert buckets == {
        "iplan": 2,
        "mavat": 1,
        "gemini": 3,
        "vision": 4,
        "other": 5,
    }


def test_derive_external_status_is_degraded_when_drill_fails():
    quick_status = _load_quick_status_module()

    summary = {
        "events_total": 10,
        "events_by_outcome": {"error": 0},
        "alerts_by_severity": {"sev1": 0},
        "degraded_reason_counts": {},
    }
    drill_results = [
        quick_status.DrillResult(
            name="drill",
            command="pytest tests/example.py -q",
            returncode=1,
            summary="1 failed",
        )
    ]

    assert quick_status._derive_external_status(summary, drill_results) == "DEGRADED"


def test_derive_external_status_is_warning_when_runtime_errors_exist():
    quick_status = _load_quick_status_module()

    summary = {
        "events_total": 7,
        "events_by_outcome": {"error": 1},
        "alerts_by_severity": {"sev1": 0},
        "degraded_reason_counts": {},
    }

    assert quick_status._derive_external_status(summary, []) == "WARNING"


def test_warning_context_identifies_historical_runtime_noise():
    quick_status = _load_quick_status_module()

    summary = {
        "events_by_outcome": {"error": 1},
        "alerts_by_severity": {"sev1": 1},
    }
    reason_buckets = {"iplan": 0, "mavat": 0, "gemini": 0, "vision": 0, "other": 0}
    drills = [
        quick_status.DrillResult(
            name="drill",
            command="pytest tests/example.py -q",
            returncode=0,
            summary="1 passed",
        )
    ]

    context = quick_status._derive_warning_context(
        summary,
        reason_buckets,
        run_drills=True,
        drill_results=drills,
    )

    assert context == "historical_runtime_window_noise"
    follow_up = quick_status._derive_warning_follow_up(context)
    assert "historical window noise" in follow_up


def test_warning_context_identifies_build_timeout_noise_dominance():
    quick_status = _load_quick_status_module()

    summary = {
        "events_by_outcome": {"error": 1},
        "alerts_by_severity": {"sev1": 1},
    }
    reason_buckets = {"iplan": 0, "mavat": 0, "gemini": 0, "vision": 0, "other": 0}
    drills = [
        quick_status.DrillResult(
            name="drill",
            command="pytest tests/example.py -q",
            returncode=0,
            summary="1 passed",
        )
    ]
    warning_noise = quick_status.WarningNoiseDiagnostics(
        build_timeout_error_events=2,
        non_build_error_events=0,
        build_timeout_sev1_alerts=2,
        non_build_sev1_alerts=0,
    )

    context = quick_status._derive_warning_context(
        summary,
        reason_buckets,
        run_drills=True,
        drill_results=drills,
        warning_noise=warning_noise,
    )

    assert context == "historical_build_timeout_sev1_noise"
    follow_up = quick_status._derive_warning_follow_up(context)
    assert "CMD-026/CMD-028" in follow_up


def test_warning_context_identifies_boundary_degraded_signals():
    quick_status = _load_quick_status_module()

    summary = {
        "events_by_outcome": {"error": 0},
        "alerts_by_severity": {"sev1": 0},
    }
    reason_buckets = {"iplan": 1, "mavat": 0, "gemini": 0, "vision": 0, "other": 0}

    context = quick_status._derive_warning_context(
        summary,
        reason_buckets,
        run_drills=False,
        drill_results=[],
    )

    assert context == "boundary_degraded_signals_present"
    follow_up = quick_status._derive_warning_follow_up(context)
    assert "CMD-035" in follow_up


def test_warning_noise_diagnostics_detects_build_timeout_dominance():
    quick_status = _load_quick_status_module()

    diagnostics = quick_status._derive_warning_noise_diagnostics(
        events=[
            {
                "operation": "build",
                "outcome": "error",
                "error_class": "HTTPError",
                "message": "request timed out",
                "request_id": "run-1",
            }
        ],
        alerts=[
            {
                "operation": "build",
                "severity": "sev1",
                "request_id": "run-1",
            }
        ],
    )

    assert diagnostics.build_timeout_error_events == 1
    assert diagnostics.non_build_error_events == 0
    assert diagnostics.build_timeout_sev1_alerts == 1
    assert diagnostics.non_build_sev1_alerts == 0
    assert diagnostics.is_build_timeout_sev1_dominant is True


def test_warning_noise_diagnostics_marks_non_build_errors_as_not_dominant():
    quick_status = _load_quick_status_module()

    diagnostics = quick_status._derive_warning_noise_diagnostics(
        events=[
            {
                "operation": "build",
                "outcome": "error",
                "error_class": "HTTPError",
                "message": "request timed out",
                "request_id": "run-1",
            },
            {
                "operation": "regulation_query",
                "outcome": "error",
                "error_class": "ValueError",
                "message": "failed parse",
                "request_id": "req-2",
            },
        ],
        alerts=[
            {
                "operation": "build",
                "severity": "sev1",
                "request_id": "run-1",
            },
            {
                "operation": "regulation_query",
                "severity": "sev1",
                "request_id": "req-2",
            },
        ],
    )

    assert diagnostics.is_build_timeout_sev1_dominant is False


def test_external_snapshot_renders_follow_up_for_historical_noise(monkeypatch, capsys):
    quick_status = _load_quick_status_module()

    summary = {
        "events_total": 12,
        "alerts_total": 2,
        "events_by_outcome": {"start": 4, "success": 7, "degraded": 0, "error": 1},
        "alerts_by_severity": {"sev1": 1, "sev2": 0, "sev3": 1},
        "latency_p95_ms_by_operation": {
            "regulation_query": 3200.0,
            "plan_search": None,
            "build": 41000.0,
        },
        "degraded_reason_counts": {},
    }

    monkeypatch.setattr(
        quick_status,
        "_load_observability_summary",
        lambda **_: (summary, Path("events.jsonl"), Path("alerts.jsonl")),
    )
    monkeypatch.setattr(
        quick_status,
        "_load_observability_window_records",
        lambda **_: ([], []),
    )
    monkeypatch.setattr(
        quick_status,
        "_run_deterministic_drills",
        lambda timeout_seconds: [
            quick_status.DrillResult(
                name="drill",
                command="pytest tests/example.py -q",
                returncode=0,
                summary="1 passed",
            )
        ],
    )
    monkeypatch.setenv("RUN_NETWORK_TESTS", "0")

    exit_code = quick_status.check_external_dependency_status(
        since_minutes=180,
        events_limit=1000,
        alerts_limit=500,
        run_drills=True,
        drill_timeout_seconds=60,
    )

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "status: WARNING" in captured
    assert "warning_context: historical_runtime_window_noise" in captured
    assert "historical window noise" in captured


def test_external_snapshot_renders_follow_up_for_build_timeout_noise(
    monkeypatch, capsys
):
    quick_status = _load_quick_status_module()

    summary = {
        "events_total": 12,
        "alerts_total": 2,
        "events_by_outcome": {"start": 4, "success": 7, "degraded": 0, "error": 1},
        "alerts_by_severity": {"sev1": 1, "sev2": 0, "sev3": 1},
        "latency_p95_ms_by_operation": {
            "regulation_query": 3200.0,
            "plan_search": None,
            "build": 41000.0,
        },
        "degraded_reason_counts": {},
    }
    warning_events = [
        {
            "operation": "build",
            "outcome": "error",
            "error_class": "HTTPError",
            "message": "request timed out",
            "request_id": "build-1",
        }
    ]
    warning_alerts = [
        {
            "operation": "build",
            "severity": "sev1",
            "request_id": "build-1",
        }
    ]

    monkeypatch.setattr(
        quick_status,
        "_load_observability_summary",
        lambda **_: (summary, Path("events.jsonl"), Path("alerts.jsonl")),
    )
    monkeypatch.setattr(
        quick_status,
        "_load_observability_window_records",
        lambda **_: (warning_events, warning_alerts),
    )
    monkeypatch.setattr(
        quick_status,
        "_run_deterministic_drills",
        lambda timeout_seconds: [
            quick_status.DrillResult(
                name="drill",
                command="pytest tests/example.py -q",
                returncode=0,
                summary="1 passed",
            )
        ],
    )
    monkeypatch.setenv("RUN_NETWORK_TESTS", "0")

    exit_code = quick_status.check_external_dependency_status(
        since_minutes=180,
        events_limit=1000,
        alerts_limit=500,
        run_drills=True,
        drill_timeout_seconds=60,
    )

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "status: WARNING" in captured
    assert "warning_context: historical_build_timeout_sev1_noise" in captured
    assert "warning_noise_profile: build_timeout_error_events=1" in captured
    assert "CMD-026/CMD-028" in captured


def test_external_snapshot_renders_follow_up_for_unconfirmed_runtime_warning(
    monkeypatch, capsys
):
    quick_status = _load_quick_status_module()

    summary = {
        "events_total": 5,
        "alerts_total": 1,
        "events_by_outcome": {"start": 2, "success": 2, "degraded": 0, "error": 1},
        "alerts_by_severity": {"sev1": 0, "sev2": 0, "sev3": 1},
        "latency_p95_ms_by_operation": {
            "regulation_query": 4100.0,
            "plan_search": None,
            "build": None,
        },
        "degraded_reason_counts": {},
    }

    monkeypatch.setattr(
        quick_status,
        "_load_observability_summary",
        lambda **_: (summary, Path("events.jsonl"), Path("alerts.jsonl")),
    )
    monkeypatch.setenv("RUN_NETWORK_TESTS", "0")

    exit_code = quick_status.check_external_dependency_status(
        since_minutes=60,
        events_limit=1000,
        alerts_limit=500,
        run_drills=False,
        drill_timeout_seconds=60,
    )

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "status: WARNING" in captured
    assert "warning_context: runtime_errors_or_alerts_unconfirmed" in captured
    assert "rerun with --run-drills" in captured
