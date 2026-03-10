import json
from datetime import datetime, timedelta, timezone

import pytest

from src.observability.query import (
    filter_records,
    parse_iso_timestamp,
    read_jsonl,
    summarize_observability,
)

pytestmark = [pytest.mark.unit]


def test_read_jsonl__returns_newest_first_and_skips_bad_lines(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps(
                    {"request_id": "old", "timestamp": "2026-02-08T00:00:00+00:00"}
                ),
                "{bad-json",
                json.dumps(
                    {"request_id": "new", "timestamp": "2026-02-08T01:00:00+00:00"}
                ),
            ]
        ),
        encoding="utf-8",
    )

    rows = read_jsonl(path)

    assert [row["request_id"] for row in rows] == ["new", "old"]


def test_filter_records__applies_component_outcome_and_time_window():
    now = datetime(2026, 2, 8, 12, 0, tzinfo=timezone.utc)
    records = [
        {
            "component": "PlanSearchService",
            "outcome": "success",
            "timestamp": (now - timedelta(minutes=2)).isoformat(),
        },
        {
            "component": "PlanSearchService",
            "outcome": "error",
            "timestamp": (now - timedelta(minutes=30)).isoformat(),
        },
        {
            "component": "RegulationQueryService",
            "outcome": "success",
            "timestamp": (now - timedelta(minutes=1)).isoformat(),
        },
    ]

    filtered = filter_records(
        records,
        component="PlanSearchService",
        outcome="success",
        since_minutes=10,
        now=now,
    )

    assert len(filtered) == 1
    assert filtered[0]["component"] == "PlanSearchService"
    assert filtered[0]["outcome"] == "success"


def test_summarize_observability__builds_counts_and_latency_p95():
    events = [
        {
            "operation": "regulation_query",
            "outcome": "success",
            "latency_ms": 100,
            "saturation_ratio_1m": 0.5,
            "memory_used_ratio": 0.65,
            "disk_free_ratio_cache_dir": 0.45,
            "rss_mb": 120,
            "timestamp": "2026-02-08T00:00:00+00:00",
        },
        {
            "operation": "regulation_query",
            "outcome": "success",
            "latency_ms": 500,
            "saturation_ratio_1m": 0.9,
            "memory_used_ratio": 0.85,
            "disk_free_ratio_cache_dir": 0.35,
            "rss_mb": 140,
            "timestamp": "2026-02-08T00:01:00+00:00",
        },
        {
            "operation": "plan_search",
            "outcome": "degraded",
            "latency_ms": 300,
            "degraded_reasons": ["iplan_search_by_location_failed"],
            "saturation_ratio_1m": 1.4,
            "memory_used_ratio": 0.93,
            "disk_free_ratio_cache_dir": 0.15,
            "rss_mb": 260,
            "timestamp": "2026-02-08T00:02:00+00:00",
        },
    ]
    alerts = [
        {
            "severity": "sev1",
            "route": "maintainer-oncall",
            "timestamp": "2026-02-08T00:02:00+00:00",
        },
        {
            "severity": "sev3",
            "route": "maintainer",
            "timestamp": "2026-02-08T00:03:00+00:00",
        },
    ]

    summary = summarize_observability(events, alerts)

    assert summary["events_total"] == 3
    assert summary["alerts_total"] == 2
    assert summary["events_by_outcome"]["success"] == 2
    assert summary["events_by_outcome"]["degraded"] == 1
    assert summary["alerts_by_severity"]["sev1"] == 1
    assert summary["latency_p95_ms_by_operation"]["regulation_query"] == 500.0
    assert summary["degraded_reason_counts"]["iplan_search_by_location_failed"] == 1
    assert summary["saturation_signals"]["saturation_ratio_1m_p95"] == 1.4
    assert summary["saturation_signals"]["memory_used_ratio_p95"] == 0.93
    assert summary["saturation_signals"]["disk_free_ratio_cache_dir_p05"] == 0.15
    assert summary["saturation_signals"]["rss_mb_p95"] == 260.0
    assert summary["memory_signal_context"]["status"] == "available"
    assert summary["memory_signal_context"]["samples_total"] == 3
    assert summary["memory_signal_context"]["samples_with_memory_used_ratio"] == 3
    assert summary["memory_signal_context"]["latest_source"] is None


def test_summarize_observability__reports_explicit_unavailable_memory_signal():
    events = [
        {
            "operation": "build",
            "outcome": "degraded",
            "latency_ms": 120000,
            "saturation_ratio_1m": 0.6,
            "memory_used_ratio": None,
            "memory_used_ratio_unavailable_reason": "host_memory_probe_unavailable",
            "timestamp": "2026-02-08T00:00:00+00:00",
        }
    ]

    summary = summarize_observability(events, alerts=[])

    assert summary["saturation_signals"]["memory_used_ratio_p95"] is None
    assert summary["memory_signal_context"]["status"] == "explicitly_unavailable"
    assert summary["memory_signal_context"]["samples_total"] == 1
    assert summary["memory_signal_context"]["samples_with_memory_used_ratio"] == 0
    assert summary["memory_signal_context"]["latest_unavailable_reason"] == (
        "host_memory_probe_unavailable"
    )


def test_parse_iso_timestamp__returns_none_for_invalid_values():
    assert parse_iso_timestamp(None) is None
    assert parse_iso_timestamp(123) is None
    assert parse_iso_timestamp("not-a-time") is None
