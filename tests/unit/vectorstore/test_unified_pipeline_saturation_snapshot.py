from pathlib import Path
from types import SimpleNamespace

import pytest

from src.vectorstore.unified_pipeline import UnifiedDataPipeline

pytestmark = [pytest.mark.unit]


def test_parse_memory_pressure_free_percent__extracts_value():
    text = """
The system has 25769803776 (1572864 pages with a page size of 16384).
System-wide memory free percentage: 48%
"""
    percent = UnifiedDataPipeline._parse_memory_pressure_free_percent(text)
    assert percent == 48.0


def test_memory_used_ratio_snapshot__prefers_sysconf_when_available(monkeypatch):
    pipeline = object.__new__(UnifiedDataPipeline)
    pipeline.config = SimpleNamespace(cache_dir=Path("."))

    values = {
        "SC_PHYS_PAGES": 100,
        "SC_PAGE_SIZE": 10,
        "SC_AVPHYS_PAGES": 35,
    }

    def _sysconf(name: str):
        return values[name]

    monkeypatch.setattr("src.vectorstore.unified_pipeline.os.sysconf", _sysconf)

    ratio, source, unavailable_reason = pipeline._memory_used_ratio_snapshot()

    assert ratio == 0.65
    assert source == "sysconf_sc_avphys_pages"
    assert unavailable_reason is None


def test_memory_used_ratio_snapshot__falls_back_to_memory_pressure(monkeypatch):
    pipeline = object.__new__(UnifiedDataPipeline)
    pipeline.config = SimpleNamespace(cache_dir=Path("."))

    def _sysconf(name: str):
        if name == "SC_AVPHYS_PAGES":
            raise ValueError("unrecognized configuration name")
        if name == "SC_PHYS_PAGES":
            return 100
        if name == "SC_PAGE_SIZE":
            return 10
        raise ValueError(name)

    class _Result:
        returncode = 0
        stdout = "System-wide memory free percentage: 48%\n"

    monkeypatch.setattr("src.vectorstore.unified_pipeline.os.sysconf", _sysconf)
    monkeypatch.setattr("src.vectorstore.unified_pipeline.sys.platform", "darwin")
    monkeypatch.setattr(
        "src.vectorstore.unified_pipeline.subprocess.run",
        lambda *args, **kwargs: _Result(),
    )

    ratio, source, unavailable_reason = pipeline._memory_used_ratio_snapshot()

    assert ratio == 0.52
    assert source == "memory_pressure_q"
    assert unavailable_reason is None
