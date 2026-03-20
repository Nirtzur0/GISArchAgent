import asyncio

import pytest


pytestmark = [pytest.mark.unit]


class _FakeTextElement:
    def __init__(self, text: str):
        self.text = text


class _FakeRow:
    async def scroll_into_view(self):
        return None

    async def query(self, selector, **kwargs):
        if selector == "span.uk-text-lead.doc-info":
            return _FakeTextElement("Document A")
        if selector.startswith("div.clickable"):
            return []
        return None


class _FakeKeyboard:
    async def press(self, *args, **kwargs):
        return None


class _FakeTab:
    def __init__(self):
        self.keyboard = _FakeKeyboard()

    async def query(self, selector, **kwargs):
        if selector == "span.uk-text-lead.doc-info":
            return [_FakeTextElement("Document A")]
        if selector == "div[role='row']":
            return [_FakeRow()]
        return []

    async def get_network_logs(self):
        return []


class _FallbackElement:
    def __init__(self):
        self.scripts: list[tuple[str, bool | None]] = []

    async def click(self):
        raise RuntimeError("native click failed")

    async def click_using_js(self):
        raise RuntimeError("js helper click failed")

    async def execute_script(self, script: str, *, user_gesture: bool | None = None):
        self.scripts.append((script, user_gesture))


def test_classify_mavat_page_text__blocked__returns_blocked():
    from src.data_management.pydoll_fetcher import _classify_mavat_page_text

    status, detail = _classify_mavat_page_text("Access denied by Cloudflare")
    assert status == "blocked"
    assert "blocked" in detail.lower()


def test_classify_mavat_error__timeout__returns_timeout():
    from src.data_management.pydoll_fetcher import _classify_mavat_error

    status, detail = _classify_mavat_error(TimeoutError("timed out"))
    assert status == "timeout"
    assert "timed out" in detail


def test_click_download_element__uses_element_execute_script_fallback():
    from src.data_management.pydoll_fetcher import PydollFetcher

    fetcher = PydollFetcher()
    element = _FallbackElement()

    clicked = asyncio.run(fetcher._click_download_element(element))

    assert clicked is True
    assert element.scripts == [("this.click()", True)]


def test_extract_mavat_artifacts__records_no_attachment_requests_when_rows_have_no_clickables():
    from src.data_management.pydoll_fetcher import PydollFetcher

    fetcher = PydollFetcher()
    fetcher._tab = _FakeTab()

    async def _ready(plan_id: str, *, timeout_s: int = 45):
        return {
            "plan_id": plan_id,
            "status": "ready",
            "detail": "ready",
            "updated_at": "2026-03-11T00:00:00+00:00",
        }

    fetcher.fetch_mavat_page = _ready  # type: ignore[method-assign]

    artifacts = asyncio.run(fetcher.extract_mavat_artifacts("1000216487"))

    assert artifacts == []
    result = fetcher.last_mavat_result()
    assert result["status"] == "no_attachment_requests"
    assert result["plan_id"] == "1000216487"
    assert result["artifacts_found"] == 0
