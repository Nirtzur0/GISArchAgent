"""Lightweight observability helpers for structured logs and JSONL metrics."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_OBSERVABILITY_DIR = Path("data/cache/observability")
DEFAULT_EVENTS_SINK = DEFAULT_OBSERVABILITY_DIR / "events_backend.jsonl"
DEFAULT_ALERTS_SINK = DEFAULT_OBSERVABILITY_DIR / "alerts.jsonl"
ALERT_ROUTES = {
    "sev1": "maintainer-oncall",
    "sev2": "maintainer-primary",
    "sev3": "maintainer",
}
_SEVERITY_RANK = {"sev1": 1, "sev2": 2, "sev3": 3}
_LATENCY_THRESHOLDS_MS = {
    # 2026-02-09 calibration snapshot (local backend, 180m window):
    # p95 ~= 3453ms, p99 ~= 4379ms for regulation_query success events.
    # Raise sev3 threshold to reduce persistent low-signal alert noise.
    "regulation_query": {"sev2": 8000, "sev3": 4000},
    "plan_search": {"sev2": 10000, "sev3": 5000},
    "build": {"sev2": 300000, "sev3": 120000},
}


def utc_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def emit_observability_event(
    logger: logging.Logger,
    *,
    component: str,
    operation: str,
    request_id: str,
    outcome: str,
    level: int = logging.INFO,
    error_class: str | None = None,
    message: str | None = None,
    **fields: Any,
) -> dict[str, Any]:
    """Emit a structured observability event as a single log line."""
    payload: dict[str, Any] = {
        "timestamp": utc_timestamp(),
        "level": logging.getLevelName(level),
        "component": component,
        "operation": operation,
        "request_id": request_id,
        "outcome": outcome,
    }
    if error_class:
        payload["error_class"] = error_class
    if message:
        payload["message"] = message
    payload.update(fields)

    logger.log(
        level, "OBS_EVENT %s", json.dumps(payload, ensure_ascii=False, sort_keys=True)
    )
    persist_backend_event(logger, payload)
    route_alert(logger, payload)
    return payload


def append_jsonl_record(path: Path, payload: dict[str, Any]) -> None:
    """Append a JSON record to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        fp.write("\n")


def _backend_enabled() -> bool:
    """Check whether local observability backend sinks are enabled."""
    value = os.getenv("OBS_BACKEND_ENABLED", "1").strip().lower()
    return value not in {"0", "false", "no", "off"}


def _observability_sinks() -> tuple[Path, Path]:
    """Resolve backend event/alert sink paths."""
    root = Path(os.getenv("OBS_CACHE_DIR", str(DEFAULT_OBSERVABILITY_DIR)))
    events_path = Path(
        os.getenv("OBS_EVENTS_SINK_PATH", str(root / "events_backend.jsonl"))
    )
    alerts_path = Path(os.getenv("OBS_ALERTS_SINK_PATH", str(root / "alerts.jsonl")))
    return events_path, alerts_path


def _coerce_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _pick_severity(candidates: list[str]) -> str:
    """Pick the highest severity from candidates."""
    if not candidates:
        return "sev3"
    return sorted(candidates, key=lambda sev: _SEVERITY_RANK.get(sev, 999))[0]


def evaluate_alert(payload: dict[str, Any]) -> dict[str, Any] | None:
    """
    Evaluate a structured event against alert rules.

    Returns an alert payload if the event crosses a threshold, otherwise None.
    """
    candidates: list[str] = []
    reasons: list[str] = []

    outcome = str(payload.get("outcome", "")).lower()
    operation = str(payload.get("operation", "")).lower()
    latency_ms = _coerce_float(payload.get("latency_ms"))
    saturation_ratio = _coerce_float(payload.get("saturation_ratio_1m"))
    memory_used_ratio = _coerce_float(payload.get("memory_used_ratio"))
    disk_free_ratio = _coerce_float(payload.get("disk_free_ratio_cache_dir"))

    if outcome == "error":
        candidates.append("sev1")
        reasons.append("outcome=error")
    elif outcome == "degraded":
        candidates.append("sev2")
        reasons.append("outcome=degraded")

    thresholds = _LATENCY_THRESHOLDS_MS.get(operation, {})
    if latency_ms is not None:
        if latency_ms >= thresholds.get("sev2", float("inf")):
            candidates.append("sev2")
            reasons.append(f"latency_ms>={thresholds['sev2']}")
        elif latency_ms >= thresholds.get("sev3", float("inf")):
            candidates.append("sev3")
            reasons.append(f"latency_ms>={thresholds['sev3']}")

    if saturation_ratio is not None:
        if saturation_ratio >= 1.25:
            candidates.append("sev2")
            reasons.append("saturation_ratio_1m>=1.25")
        elif saturation_ratio >= 1.0:
            candidates.append("sev3")
            reasons.append("saturation_ratio_1m>=1.0")

    if memory_used_ratio is not None:
        if memory_used_ratio >= 0.95:
            candidates.append("sev2")
            reasons.append("memory_used_ratio>=0.95")
        elif memory_used_ratio >= 0.90:
            candidates.append("sev3")
            reasons.append("memory_used_ratio>=0.90")

    if disk_free_ratio is not None:
        if disk_free_ratio <= 0.10:
            candidates.append("sev2")
            reasons.append("disk_free_ratio_cache_dir<=0.10")
        elif disk_free_ratio <= 0.20:
            candidates.append("sev3")
            reasons.append("disk_free_ratio_cache_dir<=0.20")

    if not candidates:
        return None

    severity = _pick_severity(candidates)
    return {
        "timestamp": utc_timestamp(),
        "severity": severity,
        "route": ALERT_ROUTES.get(severity, "maintainer"),
        "component": payload.get("component"),
        "operation": payload.get("operation"),
        "request_id": payload.get("request_id"),
        "outcome": payload.get("outcome"),
        "reasons": reasons,
        "latency_ms": payload.get("latency_ms"),
        "error_class": payload.get("error_class"),
        "saturation_ratio_1m": payload.get("saturation_ratio_1m"),
        "memory_used_ratio": payload.get("memory_used_ratio"),
        "disk_free_ratio_cache_dir": payload.get("disk_free_ratio_cache_dir"),
    }


def persist_backend_event(logger: logging.Logger, payload: dict[str, Any]) -> None:
    """Persist event payload to the local backend event sink."""
    if not _backend_enabled():
        return

    events_path, _ = _observability_sinks()
    try:
        append_jsonl_record(events_path, payload)
    except Exception as exc:  # pragma: no cover - defensive only
        logger.warning("Failed to persist observability backend event: %s", exc)


def route_alert(
    logger: logging.Logger, payload: dict[str, Any]
) -> dict[str, Any] | None:
    """Evaluate and route alert records to the alert sink."""
    if not _backend_enabled():
        return None

    alert_payload = evaluate_alert(payload)
    if not alert_payload:
        return None

    _, alerts_path = _observability_sinks()
    try:
        append_jsonl_record(alerts_path, alert_payload)
    except Exception as exc:  # pragma: no cover - defensive only
        logger.warning("Failed to persist observability alert record: %s", exc)
        return None

    logger.warning(
        "OBS_ALERT %s", json.dumps(alert_payload, ensure_ascii=False, sort_keys=True)
    )
    return alert_payload
