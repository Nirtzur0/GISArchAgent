import os

import pytest


pytestmark = [pytest.mark.integration, pytest.mark.network]


def _env_int(name: str, default: int, min_value: int, max_value: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError:
        pytest.skip(f"{name} must be an integer")
    return max(min_value, min(parsed, max_value))


@pytest.mark.skipif(
    os.getenv("RUN_NETWORK_TESTS") != "1",
    reason="Set RUN_NETWORK_TESTS=1 to run optional live-network rehearsal",
)
def test_pydoll__can_extract_mavat_document_urls_for_known_plan():
    """
    Bounded live smoke rehearsal against a known MAVAT plan.

    Guardrails:
    - opt-in only (`RUN_NETWORK_TESTS=1`)
    - blocked in CI unless explicitly allowed (`RUN_NETWORK_ALLOW_CI=1`)
    - bounded attempts and timeout (`RUN_NETWORK_REHEARSAL_MAX_ATTEMPTS`, `RUN_NETWORK_REHEARSAL_TIMEOUT_SECONDS`)
    """
    import asyncio

    if os.getenv("CI") and os.getenv("RUN_NETWORK_ALLOW_CI") != "1":
        pytest.skip(
            "Live network rehearsal is disabled in CI unless RUN_NETWORK_ALLOW_CI=1"
        )

    max_attempts = _env_int(
        "RUN_NETWORK_REHEARSAL_MAX_ATTEMPTS", default=2, min_value=1, max_value=5
    )
    timeout_seconds = _env_int(
        "RUN_NETWORK_REHEARSAL_TIMEOUT_SECONDS", default=45, min_value=15, max_value=180
    )
    backoff_seconds = _env_int(
        "RUN_NETWORK_REHEARSAL_BACKOFF_SECONDS", default=2, min_value=1, max_value=10
    )

    try:
        from src.data_management.pydoll_fetcher import IPlanPydollSource
    except ModuleNotFoundError as exc:
        pytest.skip(f"Optional dependency is missing for live rehearsal: {exc}")

    async def _run():
        # MAVAT often blocks/downgrades headless browsers; run headed for this bounded rehearsal.
        async with IPlanPydollSource(headless=False) as src:
            # The target is JS-heavy and occasionally serves a partial shell; bounded
            # retries reduce false negatives while keeping this rehearsal short.
            last = []
            for attempt in range(max_attempts):
                docs = await asyncio.wait_for(
                    src.fetch_plan_documents("1000216487"), timeout=timeout_seconds
                )
                if docs:
                    return docs
                last = docs
                if attempt < max_attempts - 1:
                    await asyncio.sleep(backoff_seconds)
            return last

    try:
        docs = asyncio.run(_run())
    except TimeoutError:
        pytest.skip(
            f"Live MAVAT scrape timed out (attempts={max_attempts}, timeout={timeout_seconds}s, target likely throttling/blocked)"
        )

    if not docs:
        pytest.skip(
            "Live MAVAT returned no artifacts (target likely throttling/blocked)"
        )

    assert all(d.get("url") for d in docs), "All docs must have a URL"
    types = {d.get("artifact_type") for d in docs}
    # Nominally we expect multiple artifact types (KML/ZIP/DWG/PDF depending on UI state).
    assert len(types) >= 2
    assert any(t in types for t in ("kml", "pdf"))
