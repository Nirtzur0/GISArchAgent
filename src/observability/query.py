"""Query and summarization helpers for local observability JSONL sinks."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def read_jsonl(path: Path, *, limit: int | None = None) -> list[dict[str, Any]]:
    """Read JSONL records from file and return newest-first rows."""
    if not path.exists():
        return []

    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fp:
        for line in fp:
            text = line.strip()
            if not text:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                rows.append(payload)

    rows = list(reversed(rows))
    if limit is not None:
        return rows[: max(0, int(limit))]
    return rows


def parse_iso_timestamp(value: Any) -> datetime | None:
    """Parse ISO timestamp into an aware UTC datetime."""
    if not isinstance(value, str) or not value.strip():
        return None

    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def filter_records(
    records: list[dict[str, Any]],
    *,
    component: str | None = None,
    operation: str | None = None,
    outcome: str | None = None,
    severity: str | None = None,
    route: str | None = None,
    since_minutes: int | None = None,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Filter observability records by common dimensions."""
    result = records

    if component:
        needle = component.lower()
        result = [
            row for row in result if str(row.get("component", "")).lower() == needle
        ]

    if operation:
        needle = operation.lower()
        result = [
            row for row in result if str(row.get("operation", "")).lower() == needle
        ]

    if outcome:
        needle = outcome.lower()
        result = [
            row for row in result if str(row.get("outcome", "")).lower() == needle
        ]

    if severity:
        needle = severity.lower()
        result = [
            row for row in result if str(row.get("severity", "")).lower() == needle
        ]

    if route:
        needle = route.lower()
        result = [row for row in result if str(row.get("route", "")).lower() == needle]

    if since_minutes is not None:
        now_dt = now or datetime.now(timezone.utc)
        cutoff = now_dt - timedelta(minutes=max(0, since_minutes))
        filtered: list[dict[str, Any]] = []
        for row in result:
            ts = parse_iso_timestamp(row.get("timestamp"))
            if ts is not None and ts >= cutoff:
                filtered.append(row)
        result = filtered

    return result


def _count_by(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in records:
        value = str(row.get(key, "unknown"))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: item[0]))


def _percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * p))
    index = max(0, min(index, len(ordered) - 1))
    return float(ordered[index])


def _degraded_reason_counts(events: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in events:
        reasons_value = row.get("degraded_reasons")
        if isinstance(reasons_value, str):
            reasons = [reasons_value]
        elif isinstance(reasons_value, list):
            reasons = [str(item) for item in reasons_value if str(item).strip()]
        else:
            reasons = []

        for reason in reasons:
            counts[reason] = counts.get(reason, 0) + 1

    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _signal(values: list[float], *, p: float) -> float | None:
    value = _percentile(values, p)
    if value is None:
        return None
    return round(value, 4)


def _memory_signal_context(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize memory signal availability/provenance for saturation samples."""
    candidates: list[dict[str, Any]] = []
    for row in events:
        operation = str(row.get("operation", "")).lower()
        outcome = str(row.get("outcome", "")).lower()
        has_saturation_fields = any(
            key in row
            for key in (
                "saturation_ratio_1m",
                "memory_used_ratio",
                "disk_free_ratio_cache_dir",
                "rss_mb",
                "memory_used_ratio_source",
                "memory_used_ratio_unavailable_reason",
            )
        )
        is_terminal_build = operation == "build" and outcome in {
            "success",
            "degraded",
            "error",
        }
        if has_saturation_fields or is_terminal_build:
            candidates.append(row)

    available = 0
    missing = 0
    source_counts: dict[str, int] = {}
    unavailable_reason_counts: dict[str, int] = {}
    latest_source: str | None = None
    latest_unavailable_reason: str | None = None

    for row in candidates:
        try:
            float(row.get("memory_used_ratio"))
        except (TypeError, ValueError):
            missing += 1
        else:
            available += 1

        source_value = row.get("memory_used_ratio_source")
        source = source_value.strip() if isinstance(source_value, str) else ""
        if source:
            source_counts[source] = source_counts.get(source, 0) + 1
            if latest_source is None:
                latest_source = source

        reason_value = row.get("memory_used_ratio_unavailable_reason")
        unavailable_reason = (
            reason_value.strip() if isinstance(reason_value, str) else ""
        )
        if unavailable_reason:
            unavailable_reason_counts[unavailable_reason] = (
                unavailable_reason_counts.get(unavailable_reason, 0) + 1
            )
            if latest_unavailable_reason is None:
                latest_unavailable_reason = unavailable_reason

    if available > 0:
        status = "available"
    elif missing > 0 and unavailable_reason_counts:
        status = "explicitly_unavailable"
    elif missing > 0:
        status = "missing_unexplained"
    else:
        status = "no_samples"

    return {
        "status": status,
        "samples_total": len(candidates),
        "samples_with_memory_used_ratio": available,
        "samples_missing_memory_used_ratio": missing,
        "source_counts": dict(
            sorted(source_counts.items(), key=lambda item: (-item[1], item[0]))
        ),
        "unavailable_reason_counts": dict(
            sorted(
                unavailable_reason_counts.items(), key=lambda item: (-item[1], item[0])
            )
        ),
        "latest_source": latest_source,
        "latest_unavailable_reason": latest_unavailable_reason,
    }


def summarize_observability(
    events: list[dict[str, Any]], alerts: list[dict[str, Any]]
) -> dict[str, Any]:
    """Produce an operator-oriented summary from event and alert streams."""
    op_latencies: dict[str, list[float]] = {}
    saturation_ratio_values: list[float] = []
    memory_used_ratio_values: list[float] = []
    disk_free_ratio_values: list[float] = []
    rss_mb_values: list[float] = []
    for row in events:
        operation = str(row.get("operation", "unknown"))
        latency = row.get("latency_ms")
        try:
            latency_value = float(latency)
        except (TypeError, ValueError):
            pass
        else:
            op_latencies.setdefault(operation, []).append(latency_value)

        try:
            sat = float(row.get("saturation_ratio_1m"))
            saturation_ratio_values.append(sat)
        except (TypeError, ValueError):
            pass
        try:
            mem = float(row.get("memory_used_ratio"))
            memory_used_ratio_values.append(mem)
        except (TypeError, ValueError):
            pass
        try:
            disk = float(row.get("disk_free_ratio_cache_dir"))
            disk_free_ratio_values.append(disk)
        except (TypeError, ValueError):
            pass
        try:
            rss = float(row.get("rss_mb"))
            rss_mb_values.append(rss)
        except (TypeError, ValueError):
            pass

    latency_p95_by_operation = {
        op: _percentile(values, 0.95) for op, values in sorted(op_latencies.items())
    }

    def _latest_timestamp(records: list[dict[str, Any]]) -> str | None:
        latest: datetime | None = None
        for row in records:
            ts = parse_iso_timestamp(row.get("timestamp"))
            if ts is not None and (latest is None or ts > latest):
                latest = ts
        if latest is None:
            return None
        return latest.isoformat()

    return {
        "events_total": len(events),
        "events_by_outcome": _count_by(events, "outcome"),
        "events_by_operation": _count_by(events, "operation"),
        "degraded_reason_counts": _degraded_reason_counts(events),
        "latency_p95_ms_by_operation": latency_p95_by_operation,
        "saturation_signals": {
            "saturation_ratio_1m_p95": _signal(saturation_ratio_values, p=0.95),
            "memory_used_ratio_p95": _signal(memory_used_ratio_values, p=0.95),
            "disk_free_ratio_cache_dir_p05": _signal(disk_free_ratio_values, p=0.05),
            "rss_mb_p95": _signal(rss_mb_values, p=0.95),
        },
        "memory_signal_context": _memory_signal_context(events),
        "alerts_total": len(alerts),
        "alerts_by_severity": _count_by(alerts, "severity"),
        "alerts_by_route": _count_by(alerts, "route"),
        "latest_event_timestamp": _latest_timestamp(events),
        "latest_alert_timestamp": _latest_timestamp(alerts),
    }
