"""
Pydoll-based browser fetcher for iPlan + MAVAT.

This replaces the legacy Selenium-based approach with a CDP (Chrome DevTools
Protocol) browser controller. Key advantages for scale:
- async-first APIs (easy to parallelize with bounded concurrency)
- direct in-browser HTTP via `tab.request` (hybrid scraping)
- network event logs (extract JS-triggered download URLs)

Notes:
- "Scrape the entire site" is not a realistic guarantee; we implement the
  nominal artifact types exposed via MAVAT's documents UI (PDF/KML/ZIP/DOC/etc).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlencode, urlparse, parse_qs

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions, PageLoadState
from pydoll.interactions.keyboard import Key
import threading

logger = logging.getLogger(__name__)


def _stable_cache_key(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _guess_artifact_type(url: str) -> str:
    """
    Infer a coarse artifact type from MAVAT attachment URL.

    MAVAT uses URLs like:
      https://mavat.iplan.gov.il/rest/api/Attacments/?eid=...&fn=...pdf
    """
    try:
        q = parse_qs(urlparse(url).query)
        fn = (q.get("fn") or [""])[0].lower()
        if fn.endswith(".pdf") or ".pdf" in fn:
            return "pdf"
        if fn.endswith(".kml") or ".kml" in fn:
            return "kml"
        if fn.endswith(".zip") or ".zip" in fn:
            return "zip"
        if fn.endswith(".dwg") or ".dwg" in fn:
            return "dwg"
        if fn.endswith(".doc") or fn.endswith(".docx") or ".doc" in fn:
            return "doc"
        if fn.endswith(".xls") or fn.endswith(".xlsx") or ".xls" in fn:
            return "xls"
    except Exception:
        pass

    lower = (url or "").lower()
    for ext, typ in [
        (".pdf", "pdf"),
        (".kml", "kml"),
        (".zip", "zip"),
        (".dwg", "dwg"),
        (".doc", "doc"),
        (".docx", "doc"),
        (".xls", "xls"),
        (".xlsx", "xls"),
    ]:
        if ext in lower:
            return typ
    return "unknown"


@dataclass(frozen=True)
class ExtractedArtifact:
    plan_id: str
    title: str
    url: str
    artifact_type: str


class PydollFetcher:
    """
    Async browser fetcher using Pydoll (CDP).

    A single instance owns one Chrome + one tab. For parallel plan processing,
    create multiple instances or build a pool at a higher layer.
    """

    def __init__(
        self,
        *,
        headless: bool = True,
        cache_dir: Optional[Path] = None,
        profile_dir: Optional[Path] = None,
    ):
        self.headless = headless
        self.cache_dir = cache_dir or Path("data/cache/pydoll")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        # Persist a Chrome profile across restarts to reduce flakiness (cookies,
        # localStorage, WAF sessions). For multi-worker scraping, provide a
        # distinct profile_dir per worker.
        self.profile_dir = profile_dir or (self.cache_dir / "profile_default")
        self.profile_dir.mkdir(parents=True, exist_ok=True)

        self._browser: Optional[Chrome] = None
        self._tab = None

    async def __aenter__(self) -> "PydollFetcher":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def start(self):
        if self._browser and self._tab:
            return
        opts = ChromiumOptions()
        opts.headless = bool(self.headless)
        # Allow more time for the spawned browser to become responsive.
        opts.start_timeout = 30
        # MAVAT/iPlan pages keep background network activity; don't wait for full
        # "complete" readyState or navigation may time out.
        opts.page_load_state = PageLoadState.INTERACTIVE

        # Basic anti-detection + consistency.
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--lang=he-IL,he,en-US,en")
        opts.add_argument(f"--user-data-dir={self.profile_dir}")
        opts.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self._browser = Chrome(options=opts)
        self._tab = await self._browser.start()

        # Enable network events for download URL extraction on JS-heavy pages.
        try:
            await self._tab.enable_network_events()
        except Exception:
            pass

    async def restart(self):
        await self.close()
        await self.start()

    async def close(self):
        # Pydoll's `Chrome.stop()` can occasionally hang (CDP disconnect issues).
        # Ensure we never block indefinitely, especially under pytest.
        browser = self._browser
        try:
            if browser:
                try:
                    await asyncio.wait_for(browser.stop(), timeout=8.0)
                except Exception:
                    # Best-effort hard kill of the underlying Chrome process.
                    try:
                        bpm = getattr(browser, "_browser_process_manager", None)
                        proc = getattr(bpm, "_process", None)
                        if proc and getattr(proc, "poll", lambda: None)() is None:
                            try:
                                proc.terminate()
                            except Exception:
                                pass
                            await asyncio.sleep(0.3)
                            if getattr(proc, "poll", lambda: None)() is None:
                                try:
                                    proc.kill()
                                except Exception:
                                    pass
                    except Exception:
                        pass
        except Exception:
            pass
        self._browser = None
        self._tab = None

    @property
    def tab(self):
        if not self._tab:
            raise RuntimeError("PydollFetcher not started")
        return self._tab

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{_stable_cache_key(key)}.json"

    async def fetch_json(self, url: str, *, use_cache: bool = True, timeout_s: int = 60) -> dict[str, Any]:
        """
        Fetch and parse JSON through the browser session.
        """
        cache_path = self._cache_path(url)
        if use_cache and cache_path.exists():
            try:
                return json.loads(cache_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        # Seed the origin once; some WAFs behave differently on direct deep-links.
        origin = f"{urlparse(url).scheme}://{urlparse(url).netloc}/"

        last_err: Exception | None = None
        for attempt in range(1, 4):
            try:
                try:
                    await self.tab.go_to(origin, timeout=timeout_s)
                except Exception:
                    # Origin seeding is best-effort.
                    pass

                resp = await self.tab.request.get(url)
                break
            except Exception as e:
                last_err = e
                logger.warning(f"fetch_json failed (attempt {attempt}/3): {e}")
                await self.restart()
                await asyncio.sleep(0.5 + random.random())
        else:
            raise last_err or RuntimeError("fetch_json failed")

        data = resp.json() if hasattr(resp, "json") else json.loads(resp.text)

        try:
            cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

        # Small jitter to reduce regularity.
        await asyncio.sleep(0.2 + random.random() * 0.5)
        return data

    async def fetch_arcgis_service(
        self,
        service_url: str,
        *,
        where: str = "1=1",
        out_fields: str = "*",
        return_geometry: bool = True,
        result_offset: int = 0,
        result_record_count: int = 1000,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        params = {
            "where": where,
            "outFields": out_fields,
            "returnGeometry": "true" if return_geometry else "false",
            "resultOffset": str(result_offset),
            "resultRecordCount": str(result_record_count),
            "f": "json",
        }
        url = f"{service_url}/query?{urlencode(params)}"
        return await self.fetch_json(url, use_cache=use_cache)

    async def fetch_all_features(
        self,
        service_url: str,
        *,
        where: str = "1=1",
        batch_size: int = 1000,
        max_features: Optional[int] = None,
        use_cache: bool = True,
    ) -> list[dict[str, Any]]:
        all_features: list[dict[str, Any]] = []
        offset = 0

        while True:
            resp = await self.fetch_arcgis_service(
                service_url,
                where=where,
                result_offset=offset,
                result_record_count=batch_size,
                use_cache=use_cache,
            )

            features = resp.get("features", []) if isinstance(resp, dict) else []
            if not features:
                break

            all_features.extend(features)
            offset += batch_size

            if max_features and len(all_features) >= max_features:
                return all_features[:max_features]
            if len(features) < batch_size:
                break

            await asyncio.sleep(0.5 + random.random() * 0.5)

        return all_features

    async def fetch_mavat_page(self, plan_id: str, *, timeout_s: int = 45) -> None:
        url = f"https://mavat.iplan.gov.il/SV4/1/{plan_id}/310"

        async def _mavat_ui_state() -> str:
            # On a good load we see either the accordion titles or document rows.
            el = await self.tab.query(
                ".uk-accordion-title, span.uk-text-lead.doc-info, div[role='row']",
                timeout=5,
                find_all=False,
                raise_exc=False,
            )
            if el:
                return "ready"

            # Sometimes the deep-link resolves to a generic informational page.
            body = await self.tab.query("body", timeout=2, find_all=False, raise_exc=False)
            if body:
                try:
                    t = body.text
                    if asyncio.iscoroutine(t):
                        t = await t
                    t = (t or "")[:2000]
                    if "אתר מידע תכנוני" in t and "מה מתוכנן" in t:
                        return "wrong_page"
                    if "access denied" in t.lower() or "request blocked" in t.lower() or "cloudflare" in t.lower():
                        return "wrong_page"
                except Exception:
                    pass
            return "waiting"

        last_err: Exception | None = None
        for attempt in range(1, 5):
            try:
                # Seed origin; MAVAT sometimes serves a partial shell on deep links.
                try:
                    await self.tab.go_to("https://mavat.iplan.gov.il/", timeout=timeout_s)
                    await asyncio.sleep(1.0)
                except Exception:
                    pass

                await self.tab.go_to(url, timeout=timeout_s)
                # Allow Angular UI to render; don't assume a fixed sleep is enough.
                deadline = time.time() + timeout_s
                while time.time() < deadline:
                    state = await _mavat_ui_state()
                    if state == "ready":
                        return None
                    if state == "wrong_page":
                        raise RuntimeError("MAVAT deep-link did not resolve to the plan UI")
                    await asyncio.sleep(0.6 + random.random() * 0.4)

                raise TimeoutError("MAVAT UI did not become ready before timeout")
            except Exception as e:
                last_err = e
                logger.warning(f"fetch_mavat_page failed (attempt {attempt}/4): {e}")
                await self.restart()
                await asyncio.sleep(0.7 + random.random())

        raise last_err or RuntimeError("fetch_mavat_page failed")

    async def extract_mavat_artifacts(self, plan_id: str, *, max_clicks: int = 200) -> list[ExtractedArtifact]:
        """
        Extract nominal artifact download URLs by expanding the documents UI and
        clicking download icons to trigger `/rest/api/Attacments` requests.
        """
        rows = None
        for attempt in range(1, 5):
            await self.fetch_mavat_page(plan_id)

            # If document rows are already present, skip expensive accordion expansion.
            doc_info = await self.tab.query("span.uk-text-lead.doc-info", timeout=3, find_all=True, raise_exc=False)
            if not doc_info:
                # Expand accordions (if present) so document rows become available.
                titles = await self.tab.query(".uk-accordion-title", timeout=8, find_all=True, raise_exc=False)
                if titles:
                    for t in titles:
                        try:
                            await t.scroll_into_view()
                            await t.click()
                            await asyncio.sleep(0.06)
                        except Exception:
                            continue

            await asyncio.sleep(0.6)

            # Rows are "div[role=row]" in the rendered DOM.
            rows = await self.tab.query("div[role='row']", timeout=12, find_all=True, raise_exc=False)
            if rows:
                break

            logger.warning(
                f"MAVAT docs UI not visible (attempt {attempt}/4) for plan {plan_id}; restarting browser"
            )
            await self.restart()

        if not rows:
            return []

        artifacts: list[ExtractedArtifact] = []
        seen_urls: set[str] = set()

        def _extract_attachment_urls(logs: list[dict[str, Any]]) -> set[str]:
            out: set[str] = set()
            for log in logs or []:
                # We only care about request events that include the request URL.
                if (log.get("method") or "") != "Network.requestWillBeSent":
                    continue
                try:
                    url = (log.get("params") or {}).get("request", {}).get("url", "")
                except Exception:
                    url = ""
                if url and "/rest/api/Attacments" in url and "mavat.iplan.gov.il" in url:
                    out.add(url)
            return out

        async def _current_attachment_urls() -> set[str]:
            logs = await self.tab.get_network_logs()
            return _extract_attachment_urls(logs)

        async def _wait_for_new_attachment_urls(before: set[str], timeout_s: float = 4.5) -> set[str]:
            deadline = time.time() + timeout_s
            while time.time() < deadline:
                after = await _current_attachment_urls()
                new = after - before
                if new:
                    return new
                await asyncio.sleep(0.15)
            return set()

        clicks = 0
        for row in rows:
            if clicks >= max_clicks:
                break

            try:
                try:
                    await row.scroll_into_view()
                    await asyncio.sleep(0.05)
                except Exception:
                    pass

                title_el = await row.query("span.uk-text-lead.doc-info", find_all=False, raise_exc=False)
                title_val = ""
                if title_el is not None:
                    try:
                        title_val = title_el.text  # type: ignore[assignment]
                        if asyncio.iscoroutine(title_val):
                            title_val = await title_val
                    except Exception:
                        title_val = ""
                title = (title_val or "").strip()
                if not title:
                    continue

                # In practice each row exposes one or more clickable "file" icons.
                # Clicking triggers a `/rest/api/Attacments?...` request; we record
                # that URL without downloading the file.
                # Prefer the actual icon (img) rather than the container div, to
                # avoid `ElementNotVisible` errors on layout-only wrappers.
                clickables = await row.query(
                    "div.clickable img[tabindex='0'], div.clickable img, img[tabindex='0']",
                    timeout=1,
                    find_all=True,
                    raise_exc=False,
                )
                if not clickables:
                    icon = await row.query(
                        "img[alt*='PDF'], img[title*='PDF'], img.sv4-icon-file, img.pdf-download, img[src*='download']",
                        timeout=1,
                        find_all=False,
                        raise_exc=False,
                    )
                    clickables = [icon] if icon else []

                if not clickables:
                    continue

                for el in clickables:
                    if clicks >= max_clicks:
                        break
                    before = await _current_attachment_urls()
                    try:
                        await el.scroll_into_view()
                    except Exception:
                        pass

                    try:
                        # Best-effort visibility/interactability check; pydoll exposes these as methods.
                        vis = getattr(el, "is_visible", None)
                        if callable(vis):
                            vis = vis()
                        if asyncio.iscoroutine(vis):
                            vis = await vis
                        # Don't hard-skip hidden elements: some icons report as
                        # non-visible but still trigger the download XHR when clicked.
                    except Exception:
                        pass

                    try:
                        await el.click()
                    except Exception:
                        try:
                            # `click_using_js` still performs visibility checks in some cases;
                            # fall back to a raw `Runtime.callFunctionOn` click.
                            await el.click_using_js()
                        except Exception:
                            try:
                                await self.tab.execute_script("arguments[0].click();", element=el, user_gesture=True)
                            except Exception:
                                continue

                    clicks += 1
                    new_urls = await _wait_for_new_attachment_urls(before)

                    # Close any modal/viewer that might have opened.
                    try:
                        kb = self.tab.keyboard
                        if asyncio.iscoroutine(kb):
                            kb = await kb
                        await kb.press(Key.ESCAPE, interval=0.05)
                    except Exception:
                        pass

                    for url in sorted(new_urls):
                        if url in seen_urls:
                            continue
                        seen_urls.add(url)
                        artifacts.append(
                            ExtractedArtifact(
                                plan_id=plan_id,
                                title=title,
                                url=url,
                                artifact_type=_guess_artifact_type(url),
                            )
                        )
            except Exception:
                continue

        # De-dupe by URL (titles may repeat).
        uniq: dict[str, ExtractedArtifact] = {a.url: a for a in artifacts if a.url}
        return list(uniq.values())


class IPlanPydollSource:
    """
    iPlan source implemented over PydollFetcher.

    Mirrors the legacy Selenium source interface so the rest of the app can be
    updated with minimal churn.
    """

    SERVICES = {
        "xplan": "https://ags.iplan.gov.il/arcgisiplan/rest/services/PlanningPublic/xplan_without_77_78/MapServer/1",
        "xplan_full": "https://ags.iplan.gov.il/arcgis/rest/services/PlanningPublic/Xplan/MapServer/0",
        "tama35": "https://ags.iplan.gov.il/arcgis/rest/services/PlanningPublic/Tama35/MapServer/0",
        "tama": "https://ags.iplan.gov.il/arcgis/rest/services/PlanningPublic/Tama/MapServer/0",
    }

    def __init__(self, *, headless: bool = True, cache_dir: Optional[Path] = None):
        self.fetcher = PydollFetcher(headless=headless, cache_dir=cache_dir)

    async def __aenter__(self) -> "IPlanPydollSource":
        await self.fetcher.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.fetcher.close()

    async def discover_plans(
        self,
        *,
        service_name: str = "xplan",
        max_plans: Optional[int] = None,
        where: str = "1=1",
        use_cache: bool = True,
    ) -> list[dict[str, Any]]:
        service_url = self.SERVICES.get(service_name)
        if not service_url:
            raise ValueError(f"Unknown service: {service_name}")

        return await self.fetcher.fetch_all_features(
            service_url,
            where=where,
            max_features=max_plans,
            use_cache=use_cache,
        )

    async def fetch_plan_details(self, objectid: str, *, service_name: str = "xplan", use_cache: bool = True) -> dict[str, Any]:
        service_url = self.SERVICES.get(service_name)
        if not service_url:
            raise ValueError(f"Unknown service: {service_name}")

        where = f"OBJECTID={objectid}"
        resp = await self.fetcher.fetch_arcgis_service(service_url, where=where, use_cache=use_cache)
        feats = resp.get("features", []) if isinstance(resp, dict) else []
        return feats[0] if feats else {}

    async def fetch_plan_documents(self, mavat_plan_id: str) -> list[dict[str, str]]:
        last_err: Exception | None = None
        for attempt in range(1, 4):
            try:
                arts = await self.fetcher.extract_mavat_artifacts(mavat_plan_id)
                return [
                    {"url": a.url, "title": a.title, "plan_id": a.plan_id, "artifact_type": a.artifact_type}
                    for a in arts
                ]
            except Exception as e:
                last_err = e
                logger.warning(f"fetch_plan_documents failed (attempt {attempt}/3) for plan {mavat_plan_id}: {e}")
                try:
                    await self.fetcher.restart()
                except Exception:
                    pass
                await asyncio.sleep(0.8 + random.random())

        logger.error(f"fetch_plan_documents giving up for plan {mavat_plan_id}: {last_err}")
        return []


class SyncIPlanPydollSource:
    """
    Synchronous facade over IPlanPydollSource.

    The rest of the codebase (generic pipeline, some services) is synchronous.
    This wrapper runs the async browser in a dedicated event-loop thread so we
    can reuse one Chrome session without forcing a full async refactor.
    """

    def __init__(self, *, headless: bool = True, cache_dir: Optional[Path] = None):
        self._headless = headless
        self._cache_dir = cache_dir

        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._source: Optional[IPlanPydollSource] = None
        self._started = threading.Event()
        self._closed = False

        self._start_thread()

    def _start_thread(self):
        if self._thread:
            return

        def _run_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loop = loop

            async def _init():
                self._source = IPlanPydollSource(headless=self._headless, cache_dir=self._cache_dir)
                await self._source.__aenter__()
                self._started.set()

            loop.create_task(_init())
            loop.run_forever()

        self._thread = threading.Thread(target=_run_loop, name="pydoll-loop", daemon=True)
        self._thread.start()
        if not self._started.wait(timeout=120):
            raise TimeoutError("Timed out starting Pydoll browser thread")

    def _run(self, coro):
        if self._closed:
            raise RuntimeError("SyncIPlanPydollSource is closed")
        if not self._loop:
            raise RuntimeError("Event loop not initialized")
        fut = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return fut.result(timeout=180)

    def discover_plans(self, *, service_name: str = "xplan", max_plans: Optional[int] = None, where: str = "1=1") -> list[dict[str, Any]]:
        assert self._source is not None
        return self._run(self._source.discover_plans(service_name=service_name, max_plans=max_plans, where=where))

    def fetch_plan_details(self, objectid: str, *, service_name: str = "xplan") -> dict[str, Any]:
        assert self._source is not None
        return self._run(self._source.fetch_plan_details(objectid, service_name=service_name))

    def fetch_plan_documents(self, mavat_plan_id: str) -> list[dict[str, str]]:
        assert self._source is not None
        return self._run(self._source.fetch_plan_documents(mavat_plan_id))

    def close(self):
        if self._closed:
            return
        self._closed = True

        if self._loop:
            async def _shutdown():
                try:
                    if self._source:
                        await self._source.__aexit__(None, None, None)
                finally:
                    self._source = None

            try:
                self._run(_shutdown())
            except Exception:
                pass

            try:
                self._loop.call_soon_threadsafe(self._loop.stop)
            except Exception:
                pass

        self._thread = None
        self._loop = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
