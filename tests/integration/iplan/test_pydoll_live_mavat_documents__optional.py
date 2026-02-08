import os

import pytest


pytestmark = [pytest.mark.integration, pytest.mark.network]


@pytest.mark.skipif(os.getenv("RUN_NETWORK_TESTS") != "1", reason="Set RUN_NETWORK_TESTS=1 to run live network test")
def test_pydoll__can_extract_mavat_document_urls_for_known_plan():
    """
    Live smoke test against a known MAVAT plan that typically exposes PDF and KML artifacts.

    This is intentionally opt-in because it depends on network + target availability.
    """
    import asyncio

    from src.data_management.pydoll_fetcher import IPlanPydollSource

    async def _run():
        # MAVAT often blocks/downgrades headless browsers; run headed for this smoke test.
        async with IPlanPydollSource(headless=False) as src:
            # The target is JS-heavy and occasionally serves a partial shell; retry
            # a few times within the same browser session to reduce flakiness.
            last = []
            for _ in range(5):
                docs = await asyncio.wait_for(src.fetch_plan_documents("1000216487"), timeout=60)
                if docs:
                    return docs
                last = docs
                await asyncio.sleep(1.5)
            return last

    try:
        docs = asyncio.run(_run())
    except TimeoutError:
        pytest.skip("Live MAVAT scrape timed out (target likely throttling/blocked)")

    if not docs:
        pytest.skip("Live MAVAT returned no artifacts (target likely throttling/blocked)")

    assert all(d.get("url") for d in docs), "All docs must have a URL"
    types = {d.get("artifact_type") for d in docs}
    # Nominally we expect multiple artifact types (KML/ZIP/DWG/PDF depending on UI state).
    assert len(types) >= 2
    assert any(t in types for t in ("kml", "pdf"))
