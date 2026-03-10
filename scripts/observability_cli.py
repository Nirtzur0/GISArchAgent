#!/usr/bin/env python3
"""CLI for querying local observability backend sinks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.observability.query import filter_records, read_jsonl, summarize_observability

DEFAULT_OBS_DIR = Path("data/cache/observability")


def _events_path(obs_dir: Path) -> Path:
    return obs_dir / "events_backend.jsonl"


def _alerts_path(obs_dir: Path) -> Path:
    return obs_dir / "alerts.jsonl"


@click.group()
def cli() -> None:
    """Query observability events and alerts."""


def _sorted_items_desc(counts: dict[str, int]) -> list[tuple[str, int]]:
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def _display_optional(value: object) -> str:
    if value is None:
        return "-"
    text = str(value).strip()
    return text or "-"


@cli.command()
@click.option(
    "--observability-dir",
    default=str(DEFAULT_OBS_DIR),
    show_default=True,
    help="Observability cache directory",
)
@click.option(
    "--events-limit",
    default=500,
    show_default=True,
    type=int,
    help="Max events to read",
)
@click.option(
    "--alerts-limit",
    default=500,
    show_default=True,
    type=int,
    help="Max alerts to read",
)
@click.option(
    "--since-minutes",
    default=None,
    type=int,
    help="Only include records from the last N minutes",
)
@click.option("--as-json", "as_json", is_flag=True, help="Print summary as JSON")
def summary(
    observability_dir: str,
    events_limit: int,
    alerts_limit: int,
    since_minutes: int | None,
    as_json: bool,
) -> None:
    """Print summary of events, alerts, and latency signals."""
    obs_dir = Path(observability_dir)
    events = read_jsonl(_events_path(obs_dir), limit=events_limit)
    alerts = read_jsonl(_alerts_path(obs_dir), limit=alerts_limit)

    events = filter_records(events, since_minutes=since_minutes)
    alerts = filter_records(alerts, since_minutes=since_minutes)

    payload = summarize_observability(events, alerts)

    if as_json:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return

    click.echo("Observability Summary")
    click.echo("=" * 64)
    click.echo(f"Events total: {payload['events_total']}")
    click.echo(f"Alerts total: {payload['alerts_total']}")
    if since_minutes is not None:
        click.echo(f"Window: last {since_minutes} minute(s)")
    click.echo("")

    click.echo("Events by outcome:")
    for key, value in payload["events_by_outcome"].items():
        click.echo(f"  {key}: {value}")

    click.echo("\nAlerts by severity:")
    for key, value in payload["alerts_by_severity"].items():
        click.echo(f"  {key}: {value}")

    click.echo("\nLatency p95 (ms) by operation:")
    p95_map = payload["latency_p95_ms_by_operation"]
    if not p95_map:
        click.echo("  No latency records")
    else:
        for operation, value in p95_map.items():
            click.echo(f"  {operation}: {value:.2f}")

    click.echo("\nTop degraded reasons:")
    reason_counts = payload["degraded_reason_counts"]
    if not reason_counts:
        click.echo("  No degraded reasons recorded")
    else:
        for reason, count in _sorted_items_desc(reason_counts)[:5]:
            click.echo(f"  {reason}: {count}")

    signals = payload["saturation_signals"]
    memory_context = payload["memory_signal_context"]
    click.echo("\nSaturation signals:")
    click.echo(f"  saturation_ratio_1m_p95: {signals['saturation_ratio_1m_p95']}")
    click.echo(f"  memory_used_ratio_p95: {signals['memory_used_ratio_p95']}")
    click.echo(
        f"  disk_free_ratio_cache_dir_p05: {signals['disk_free_ratio_cache_dir_p05']}"
    )
    click.echo(f"  rss_mb_p95: {signals['rss_mb_p95']}")
    click.echo(f"  memory_signal_status: {memory_context['status']}")
    click.echo(
        "  memory_signal_samples: "
        f"{memory_context['samples_with_memory_used_ratio']}/"
        f"{memory_context['samples_total']}"
    )
    click.echo(
        "  memory_signal_latest_source: "
        f"{_display_optional(memory_context['latest_source'])}"
    )
    click.echo(
        "  memory_signal_latest_unavailable_reason: "
        f"{_display_optional(memory_context['latest_unavailable_reason'])}"
    )

    click.echo("\nLatest records:")
    click.echo(f"  latest_event_timestamp: {payload['latest_event_timestamp']}")
    click.echo(f"  latest_alert_timestamp: {payload['latest_alert_timestamp']}")


@cli.command()
@click.option(
    "--observability-dir",
    default=str(DEFAULT_OBS_DIR),
    show_default=True,
    help="Observability cache directory",
)
@click.option(
    "--limit", default=50, show_default=True, type=int, help="Max records to print"
)
@click.option("--component", default=None, help="Exact component filter")
@click.option("--operation", default=None, help="Exact operation filter")
@click.option("--outcome", default=None, help="Exact outcome filter")
@click.option(
    "--since-minutes",
    default=None,
    type=int,
    help="Only include records from the last N minutes",
)
def events(
    observability_dir: str,
    limit: int,
    component: str | None,
    operation: str | None,
    outcome: str | None,
    since_minutes: int | None,
) -> None:
    """Print event stream records (newest first)."""
    obs_dir = Path(observability_dir)
    rows = read_jsonl(_events_path(obs_dir), limit=None)
    rows = filter_records(
        rows,
        component=component,
        operation=operation,
        outcome=outcome,
        since_minutes=since_minutes,
    )
    rows = rows[: max(0, limit)]

    if not rows:
        click.echo("No matching events.")
        return

    for row in rows:
        click.echo(json.dumps(row, ensure_ascii=False, sort_keys=True))


@cli.command()
@click.option(
    "--observability-dir",
    default=str(DEFAULT_OBS_DIR),
    show_default=True,
    help="Observability cache directory",
)
@click.option(
    "--limit", default=50, show_default=True, type=int, help="Max records to print"
)
@click.option("--severity", default=None, help="Exact severity filter (sev1/sev2/sev3)")
@click.option("--route", default=None, help="Exact route filter")
@click.option(
    "--since-minutes",
    default=None,
    type=int,
    help="Only include records from the last N minutes",
)
def alerts(
    observability_dir: str,
    limit: int,
    severity: str | None,
    route: str | None,
    since_minutes: int | None,
) -> None:
    """Print alert stream records (newest first)."""
    obs_dir = Path(observability_dir)
    rows = read_jsonl(_alerts_path(obs_dir), limit=None)
    rows = filter_records(
        rows,
        severity=severity,
        route=route,
        since_minutes=since_minutes,
    )
    rows = rows[: max(0, limit)]

    if not rows:
        click.echo("No matching alerts.")
        return

    for row in rows:
        click.echo(json.dumps(row, ensure_ascii=False, sort_keys=True))


@cli.command()
@click.option(
    "--observability-dir",
    default=str(DEFAULT_OBS_DIR),
    show_default=True,
    help="Observability cache directory",
)
@click.option(
    "--events-limit",
    default=1000,
    show_default=True,
    type=int,
    help="Max events to read",
)
@click.option(
    "--alerts-limit",
    default=500,
    show_default=True,
    type=int,
    help="Max alerts to read",
)
@click.option(
    "--since-minutes",
    default=180,
    show_default=True,
    type=int,
    help="Only include records from the last N minutes",
)
@click.option(
    "--top-reasons",
    default=8,
    show_default=True,
    type=int,
    help="How many degraded reasons to print",
)
def dashboard(
    observability_dir: str,
    events_limit: int,
    alerts_limit: int,
    since_minutes: int,
    top_reasons: int,
) -> None:
    """Render a compact operator dashboard for observability triage."""
    obs_dir = Path(observability_dir)
    events = read_jsonl(_events_path(obs_dir), limit=events_limit)
    alerts = read_jsonl(_alerts_path(obs_dir), limit=alerts_limit)

    events = filter_records(events, since_minutes=since_minutes)
    alerts = filter_records(alerts, since_minutes=since_minutes)
    payload = summarize_observability(events, alerts)

    click.echo("Observability Dashboard")
    click.echo("=" * 78)
    click.echo(
        f"Window: last {since_minutes} minute(s) | "
        f"events={payload['events_total']} alerts={payload['alerts_total']}"
    )
    click.echo("")

    click.echo("Operations")
    click.echo("-" * 78)
    click.echo(f"{'Operation':<28} {'Count':>8} {'Latency p95 (ms)':>18}")
    event_counts = payload["events_by_operation"]
    latency_map = payload["latency_p95_ms_by_operation"]
    for operation in sorted(event_counts.keys()):
        latency = latency_map.get(operation)
        latency_text = f"{latency:.2f}" if isinstance(latency, (int, float)) else "-"
        click.echo(f"{operation:<28} {event_counts[operation]:>8} {latency_text:>18}")

    click.echo("\nDegraded Reasons")
    click.echo("-" * 78)
    reasons = payload["degraded_reason_counts"]
    if not reasons:
        click.echo("No degraded reasons in selected window.")
    else:
        for reason, count in _sorted_items_desc(reasons)[: max(1, top_reasons)]:
            click.echo(f"{reason:<60} {count:>6}")

    click.echo("\nSaturation Snapshot")
    click.echo("-" * 78)
    signals = payload["saturation_signals"]
    memory_context = payload["memory_signal_context"]
    click.echo(f"saturation_ratio_1m_p95       : {signals['saturation_ratio_1m_p95']}")
    click.echo(f"memory_used_ratio_p95         : {signals['memory_used_ratio_p95']}")
    click.echo(
        "disk_free_ratio_cache_dir_p05 : " f"{signals['disk_free_ratio_cache_dir_p05']}"
    )
    click.echo(f"rss_mb_p95                    : {signals['rss_mb_p95']}")
    click.echo(f"memory_signal_status          : {memory_context['status']}")
    click.echo(
        "memory_signal_samples         : "
        f"{memory_context['samples_with_memory_used_ratio']}/"
        f"{memory_context['samples_total']}"
    )
    click.echo(
        "memory_signal_latest_source   : "
        f"{_display_optional(memory_context['latest_source'])}"
    )
    click.echo(
        "memory_signal_latest_reason   : "
        f"{_display_optional(memory_context['latest_unavailable_reason'])}"
    )

    click.echo("\nAlerts by severity")
    click.echo("-" * 78)
    if not payload["alerts_by_severity"]:
        click.echo("No alerts in selected window.")
    else:
        for severity, count in payload["alerts_by_severity"].items():
            click.echo(f"{severity:<10} {count:>6}")

    click.echo("\nLatest")
    click.echo("-" * 78)
    click.echo(f"latest_event_timestamp: {payload['latest_event_timestamp']}")
    click.echo(f"latest_alert_timestamp: {payload['latest_alert_timestamp']}")


if __name__ == "__main__":
    cli()
