import importlib.util
from pathlib import Path
import sys

import pytest


pytestmark = pytest.mark.unit


def _load_build_vectordb_cli_module():
    module_path = (
        Path(__file__).resolve().parents[3] / "scripts" / "build_vectordb_cli.py"
    )
    spec = importlib.util.spec_from_file_location("build_vectordb_cli", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_check_provider_configuration__reports_optional_when_unconfigured():
    module = _load_build_vectordb_cli_module()

    result = module.check_provider_configuration(base_url="")

    assert result.required is False
    assert result.ok is False
    assert "not configured" in result.detail


def test_summarize_prerequisite_checks__fails_only_on_required_checks():
    module = _load_build_vectordb_cli_module()

    checks = [
        module.PrerequisiteCheck(
            name="required check",
            ok=True,
            detail="ok",
            required=True,
        ),
        module.PrerequisiteCheck(
            name="optional check",
            ok=False,
            detail="missing",
            required=False,
        ),
    ]

    all_ok, lines = module.summarize_prerequisite_checks(checks)

    assert all_ok is True
    assert any("⚠️ optional check" in line for line in lines)


def test_check_python_module__reports_required_import_failure(monkeypatch):
    module = _load_build_vectordb_cli_module()

    def _raise_import_error(name):
        raise ImportError(f"missing {name}")

    monkeypatch.setattr(module.importlib, "import_module", _raise_import_error)

    result = module.check_python_module("missing.module", label="Missing Module")

    assert result.required is True
    assert result.ok is False
    assert "missing missing.module" in result.detail
