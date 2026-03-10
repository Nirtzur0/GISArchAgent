#!/usr/bin/env python3
"""Quick local status checks for vector DB and external dependency boundaries."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_EVENTS_SINK_PATH = Path("data/cache/observability/events_backend.jsonl")
DEFAULT_ALERTS_SINK_PATH = Path("data/cache/observability/alerts.jsonl")


@dataclass
class DrillResult:
    """Summary for one deterministic dependency drill command."""

    name: str
    command: str
    returncode: int
    summary: str


@dataclass
class WarningNoiseDiagnostics:
    """Counts used to classify warning windows before escalation."""

    build_timeout_error_events: int
    non_build_error_events: int
    build_timeout_sev1_alerts: int
    non_build_sev1_alerts: int

    @property
    def error_events_total(self) -> int:
        return self.build_timeout_error_events + self.non_build_error_events

    @property
    def sev1_alerts_total(self) -> int:
        return self.build_timeout_sev1_alerts + self.non_build_sev1_alerts

    @property
    def is_build_timeout_sev1_dominant(self) -> bool:
        return (
            self.build_timeout_error_events > 0
            and self.non_build_error_events == 0
            and self.sev1_alerts_total > 0
            and self.non_build_sev1_alerts == 0
        )


def _get_observability_paths() -> tuple[Path, Path]:
    events_path = Path(os.getenv("OBS_EVENTS_SINK_PATH", str(DEFAULT_EVENTS_SINK_PATH)))
    alerts_path = Path(os.getenv("OBS_ALERTS_SINK_PATH", str(DEFAULT_ALERTS_SINK_PATH)))
    return events_path, alerts_path


def _extract_pytest_summary(output: str) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    for line in reversed(lines):
        if (
            " passed" in line
            or " failed" in line
            or " skipped" in line
            or " errors" in line
            or " error" in line
        ):
            return line
    return lines[-1] if lines else "no output"


def _run_deterministic_drills(timeout_seconds: int) -> list[DrillResult]:
    venv_python = PROJECT_ROOT / "venv" / "bin" / "python"
    python_exec = (
        str(venv_python) if venv_python.exists() else (sys.executable or "python3")
    )
    commands = [
        (
            "External dependency drill suite",
            [
                python_exec,
                "-m",
                "pytest",
                "tests/integration/iplan/test_external_dependency_drills.py",
                "-q",
            ],
        ),
        (
            "Boundary payload contracts",
            [
                python_exec,
                "-m",
                "pytest",
                "tests/integration/data_contracts/test_boundary_payload_contracts.py",
                "-q",
            ],
        ),
        (
            "iPlan sample data quality",
            [
                python_exec,
                "-m",
                "pytest",
                "tests/integration/iplan/test_iplan_sample_data_quality.py",
                "-q",
            ],
        ),
    ]

    results: list[DrillResult] = []
    for name, command in commands:
        joined = shlex.join(command)
        try:
            proc = subprocess.run(
                command,
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=max(30, timeout_seconds),
                check=False,
            )
            summary = _extract_pytest_summary(f"{proc.stdout}\n{proc.stderr}")
            results.append(
                DrillResult(
                    name=name,
                    command=joined,
                    returncode=proc.returncode,
                    summary=summary,
                )
            )
        except subprocess.TimeoutExpired:
            results.append(
                DrillResult(
                    name=name,
                    command=joined,
                    returncode=124,
                    summary=f"timeout after {max(30, timeout_seconds)}s",
                )
            )
    return results


def _bucket_external_reasons(reason_counts: dict[str, int]) -> dict[str, int]:
    buckets = {"iplan": 0, "mavat": 0, "gemini": 0, "vision": 0, "other": 0}

    for reason, count in reason_counts.items():
        text = reason.lower()
        if text.startswith("iplan_"):
            buckets["iplan"] += count
        elif "mavat" in text:
            buckets["mavat"] += count
        elif "llm_" in text or "gemini" in text:
            buckets["gemini"] += count
        elif "vision" in text:
            buckets["vision"] += count
        else:
            buckets["other"] += count

    return buckets


def _derive_external_status(
    summary: dict[str, Any], drill_results: list[DrillResult]
) -> str:
    if any(result.returncode != 0 for result in drill_results):
        return "DEGRADED"

    events_total = int(summary.get("events_total", 0) or 0)
    events_by_outcome = summary.get("events_by_outcome", {})
    alerts_by_severity = summary.get("alerts_by_severity", {})
    degraded_reason_counts = summary.get("degraded_reason_counts", {})

    error_events = int(events_by_outcome.get("error", 0) or 0)
    sev1_alerts = int(alerts_by_severity.get("sev1", 0) or 0)

    if events_total == 0:
        return "UNKNOWN"
    if error_events > 0 or sev1_alerts > 0 or bool(degraded_reason_counts):
        return "WARNING"
    return "HEALTHY"


def _derive_warning_context(
    summary: dict[str, Any],
    reason_buckets: dict[str, int],
    *,
    run_drills: bool,
    drill_results: list[DrillResult],
    warning_noise: WarningNoiseDiagnostics | None = None,
) -> str:
    events_by_outcome = summary.get("events_by_outcome", {})
    alerts_by_severity = summary.get("alerts_by_severity", {})
    error_events = int(events_by_outcome.get("error", 0) or 0)
    sev1_alerts = int(alerts_by_severity.get("sev1", 0) or 0)
    degraded_total = int(sum(reason_buckets.values()))
    drills_failed = any(result.returncode != 0 for result in drill_results)
    drills_passed = bool(drill_results) and not drills_failed

    if degraded_total > 0:
        return "boundary_degraded_signals_present"

    if error_events > 0 or sev1_alerts > 0:
        if run_drills and drills_passed:
            if warning_noise and warning_noise.is_build_timeout_sev1_dominant:
                return "historical_build_timeout_sev1_noise"
            return "historical_runtime_window_noise"
        return "runtime_errors_or_alerts_unconfirmed"

    return "generic_warning"


def _derive_warning_follow_up(context: str) -> str:
    if context == "boundary_degraded_signals_present":
        return (
            "follow-up: degraded reasons are present; run CMD-035, then inspect "
            "CMD-027/CMD-028 slices before escalation."
        )

    if context == "historical_build_timeout_sev1_noise":
        return (
            "follow-up: warning is dominated by recurring build timeout sev1 noise; "
            "treat as non-boundary first-pass signal, rerun CMD-040 with a narrower "
            "window, then inspect CMD-026/CMD-028 before escalating."
        )

    if context == "historical_runtime_window_noise":
        return (
            "follow-up: deterministic drills passed and degraded reasons are zero; "
            "warning is likely historical window noise (for example prior sev1/build "
            "errors). Narrow --since-minutes and inspect CMD-025/CMD-028 before escalating."
        )

    if context == "runtime_errors_or_alerts_unconfirmed":
        return (
            "follow-up: runtime errors/sev1 alerts exist without degraded reasons; rerun "
            "with --run-drills and inspect CMD-028 before escalation."
        )

    return "follow-up: review CMD-029/CMD-024 context and rerun CMD-040 with a tighter window."


def _load_observability_summary(
    since_minutes: int, events_limit: int, alerts_limit: int
) -> tuple[dict[str, Any], Path, Path]:
    from src.observability.query import (
        filter_records,
        read_jsonl,
        summarize_observability,
    )

    events_path, alerts_path = _get_observability_paths()
    events = read_jsonl(events_path, limit=max(1, events_limit))
    alerts = read_jsonl(alerts_path, limit=max(1, alerts_limit))
    filtered_events = filter_records(events, since_minutes=max(1, since_minutes))
    filtered_alerts = filter_records(alerts, since_minutes=max(1, since_minutes))
    return (
        summarize_observability(filtered_events, filtered_alerts),
        events_path,
        alerts_path,
    )


def _load_observability_window_records(
    since_minutes: int, events_limit: int, alerts_limit: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from src.observability.query import filter_records, read_jsonl

    events_path, alerts_path = _get_observability_paths()
    events = read_jsonl(events_path, limit=max(1, events_limit))
    alerts = read_jsonl(alerts_path, limit=max(1, alerts_limit))
    filtered_events = filter_records(events, since_minutes=max(1, since_minutes))
    filtered_alerts = filter_records(alerts, since_minutes=max(1, since_minutes))
    return filtered_events, filtered_alerts


def _row_looks_timeout_related(row: dict[str, Any]) -> bool:
    message = str(row.get("message", "")).lower()
    error_class = str(row.get("error_class", "")).lower()
    reasons_value = row.get("reasons")
    if isinstance(reasons_value, str):
        reasons = [reasons_value.lower()]
    elif isinstance(reasons_value, list):
        reasons = [str(item).lower() for item in reasons_value]
    else:
        reasons = []

    return (
        "timeout" in message
        or "timeout" in error_class
        or any("timeout" in reason for reason in reasons)
        or error_class == "httperror"
    )


def _derive_warning_noise_diagnostics(
    events: list[dict[str, Any]], alerts: list[dict[str, Any]]
) -> WarningNoiseDiagnostics:
    build_timeout_request_ids: set[str] = set()
    build_timeout_error_events = 0
    non_build_error_events = 0
    for row in events:
        if str(row.get("outcome", "")).lower() != "error":
            continue

        operation = str(row.get("operation", "")).lower()
        if operation == "build" and _row_looks_timeout_related(row):
            build_timeout_error_events += 1
            request_id = str(row.get("request_id", "")).strip()
            if request_id:
                build_timeout_request_ids.add(request_id)
        else:
            non_build_error_events += 1

    build_timeout_sev1_alerts = 0
    non_build_sev1_alerts = 0
    for row in alerts:
        if str(row.get("severity", "")).lower() != "sev1":
            continue

        operation = str(row.get("operation", "")).lower()
        request_id = str(row.get("request_id", "")).strip()
        if operation == "build" and (
            request_id in build_timeout_request_ids or _row_looks_timeout_related(row)
        ):
            build_timeout_sev1_alerts += 1
        else:
            non_build_sev1_alerts += 1

    return WarningNoiseDiagnostics(
        build_timeout_error_events=build_timeout_error_events,
        non_build_error_events=non_build_error_events,
        build_timeout_sev1_alerts=build_timeout_sev1_alerts,
        non_build_sev1_alerts=non_build_sev1_alerts,
    )


def check_vectordb_status() -> None:
    """Check vector DB status without loading heavy app wiring."""
    import chromadb

    db_path = Path("data/vectorstore")
    metadata_file = db_path / "metadata.json"

    print("Vector Database Status")
    print("=" * 70)
    print()

    chroma_db = db_path / "chroma.sqlite3"
    if not chroma_db.exists():
        print("  Status: UNINITIALIZED")
        print("  Vector database not found")
        print()
        print("  Run: python3 scripts/build_vectordb_cli.py build --max-plans 10")
        return

    try:
        client = chromadb.PersistentClient(path=str(db_path))
        collections = client.list_collections()
        if not collections:
            print("  Status: EMPTY")
            print("  No collections found")
            return

        reg_count = 0
        for collection in collections:
            if "regulation" in collection.name.lower():
                try:
                    reg_count = collection.count()
                    break
                except Exception:
                    continue

        status = (
            "HEALTHY" if reg_count >= 100 else "WARNING" if reg_count >= 10 else "LOW"
        )
        print(f"  Status: {status}")
        print(f"  Regulation count: {reg_count}")
        print()

        if reg_count < 10:
            print("  Issues:")
            print("    - very low regulation count")
            print()
            print("  Recommendations:")
            print("    - python3 scripts/build_vectordb_cli.py build --max-plans 100")
        elif reg_count < 100:
            print("  Recommendations:")
            print("    - consider building more data (currently < 100 regulations)")
            print("    - python3 scripts/build_vectordb_cli.py build --max-plans 1000")
        else:
            print("  Database looks healthy.")

        print()
        if metadata_file.exists():
            metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
            last_updated = metadata.get("last_updated")
            if last_updated:
                print(f"  Last updated: {last_updated}")
    except Exception as exc:
        print(f"  Error checking database: {exc}")


def check_external_dependency_status(
    *,
    since_minutes: int,
    events_limit: int,
    alerts_limit: int,
    run_drills: bool,
    drill_timeout_seconds: int,
) -> int:
    """Render one-shot external dependency health snapshot bundle."""
    from src.config import settings

    summary, events_path, alerts_path = _load_observability_summary(
        since_minutes=since_minutes,
        events_limit=events_limit,
        alerts_limit=alerts_limit,
    )
    window_events, window_alerts = _load_observability_window_records(
        since_minutes=since_minutes,
        events_limit=events_limit,
        alerts_limit=alerts_limit,
    )

    reason_counts = summary.get("degraded_reason_counts", {})
    reason_buckets = _bucket_external_reasons(reason_counts)
    warning_noise = _derive_warning_noise_diagnostics(window_events, window_alerts)
    drill_results: list[DrillResult] = []
    if run_drills:
        drill_results = _run_deterministic_drills(drill_timeout_seconds)

    status = _derive_external_status(summary, drill_results)

    gemini_key_present = bool(
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or settings.gemini_api_key
        or settings.google_api_key
    )
    pydoll_installed = importlib.util.find_spec("pydoll") is not None
    network_opt_in = os.getenv("RUN_NETWORK_TESTS") == "1"

    print("External Dependency Health Snapshot")
    print("=" * 78)
    print(
        f"Window: last {max(1, since_minutes)} minute(s) | "
        f"events={summary.get('events_total', 0)} alerts={summary.get('alerts_total', 0)}"
    )
    print()

    print("Configuration")
    print("-" * 78)
    print(
        f"iPlan API URL          : {os.getenv('IPLAN_API_URL', settings.iplan_api_url)}"
    )
    print(
        f"iPlan base URL         : {os.getenv('IPLAN_BASE_URL', settings.iplan_base_url)}"
    )
    print(f"Gemini API key present : {'yes' if gemini_key_present else 'no'}")
    print(f"pydoll installed       : {'yes' if pydoll_installed else 'no'}")
    print(f"RUN_NETWORK_TESTS      : {'1' if network_opt_in else '0'}")
    print()

    print("Observability Boundary Signals")
    print("-" * 78)
    print(f"events sink            : {events_path}")
    print(f"alerts sink            : {alerts_path}")
    events_by_outcome = summary.get("events_by_outcome", {})
    alerts_by_severity = summary.get("alerts_by_severity", {})
    print(
        "events by outcome      : "
        f"start={events_by_outcome.get('start', 0)} "
        f"success={events_by_outcome.get('success', 0)} "
        f"degraded={events_by_outcome.get('degraded', 0)} "
        f"error={events_by_outcome.get('error', 0)}"
    )
    print(
        "alerts by severity     : "
        f"sev1={alerts_by_severity.get('sev1', 0)} "
        f"sev2={alerts_by_severity.get('sev2', 0)} "
        f"sev3={alerts_by_severity.get('sev3', 0)}"
    )

    latency = summary.get("latency_p95_ms_by_operation", {})
    print(
        "latency p95 ms         : "
        f"regulation_query={latency.get('regulation_query')} "
        f"plan_search={latency.get('plan_search')} "
        f"build={latency.get('build')}"
    )
    print(
        "degraded reasons       : "
        f"iplan={reason_buckets['iplan']} "
        f"mavat={reason_buckets['mavat']} "
        f"gemini={reason_buckets['gemini']} "
        f"vision={reason_buckets['vision']} "
        f"other={reason_buckets['other']}"
    )
    print()

    print("Deterministic Drill Bundle")
    print("-" * 78)
    if not run_drills:
        print("Not run. Use --run-drills to execute deterministic non-network checks.")
    else:
        for result in drill_results:
            outcome = "PASS" if result.returncode == 0 else "FAIL"
            print(f"[{outcome}] {result.name}")
            print(f"  command: {result.command}")
            print(f"  result : {result.summary}")
    print()

    print("Live-Network Rehearsal (optional)")
    print("-" * 78)
    print(
        "RUN_NETWORK_TESTS=1 RUN_NETWORK_REHEARSAL_MAX_ATTEMPTS=2 "
        "RUN_NETWORK_REHEARSAL_TIMEOUT_SECONDS=45 "
        "./venv/bin/python -m pytest "
        "tests/integration/iplan/test_pydoll_live_mavat_documents__optional.py -q"
    )
    print()

    print("Snapshot Verdict")
    print("-" * 78)
    print(f"status: {status}")

    if status == "DEGRADED":
        print(
            "follow-up: inspect failed drill output and run CMD-027/CMD-028 triage slices."
        )
    elif status == "WARNING":
        warning_context = _derive_warning_context(
            summary,
            reason_buckets,
            run_drills=run_drills,
            drill_results=drill_results,
            warning_noise=warning_noise,
        )
        print(f"warning_context: {warning_context}")
        if warning_context in {
            "historical_build_timeout_sev1_noise",
            "historical_runtime_window_noise",
        }:
            print(
                "warning_noise_profile: "
                f"build_timeout_error_events={warning_noise.build_timeout_error_events} "
                f"non_build_error_events={warning_noise.non_build_error_events} "
                f"build_timeout_sev1_alerts={warning_noise.build_timeout_sev1_alerts} "
                f"non_build_sev1_alerts={warning_noise.non_build_sev1_alerts}"
            )
        print(_derive_warning_follow_up(warning_context))
    elif status == "UNKNOWN":
        print(
            "follow-up: no recent observability data found; run build/query flows and rerun snapshot."
        )
    else:
        print("follow-up: boundary health looks stable in this window.")

    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Quick status checks for vector DB and external dependency boundaries."
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "vectordb",
        help="Check vector database persistence/collection status (default command).",
    )

    external = subparsers.add_parser(
        "external",
        help="Render one-shot external dependency health snapshot bundle.",
    )
    external.add_argument(
        "--since-minutes",
        type=int,
        default=180,
        help="Observability lookback window in minutes (default: 180).",
    )
    external.add_argument(
        "--events-limit",
        type=int,
        default=1000,
        help="Maximum number of events to read from JSONL sink (default: 1000).",
    )
    external.add_argument(
        "--alerts-limit",
        type=int,
        default=500,
        help="Maximum number of alerts to read from JSONL sink (default: 500).",
    )
    external.add_argument(
        "--run-drills",
        action="store_true",
        help="Run deterministic non-network dependency drill tests as part of snapshot.",
    )
    external.add_argument(
        "--drill-timeout-seconds",
        type=int,
        default=240,
        help="Per-drill pytest timeout in seconds when --run-drills is enabled (default: 240).",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command in (None, "vectordb"):
        check_vectordb_status()
        return 0

    if args.command == "external":
        return check_external_dependency_status(
            since_minutes=max(1, args.since_minutes),
            events_limit=max(1, args.events_limit),
            alerts_limit=max(1, args.alerts_limit),
            run_drills=bool(args.run_drills),
            drill_timeout_seconds=max(30, args.drill_timeout_seconds),
        )

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
