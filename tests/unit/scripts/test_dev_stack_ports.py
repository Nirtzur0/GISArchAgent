import importlib.util
from pathlib import Path
import sys

import pytest


pytestmark = pytest.mark.unit


def _load_dev_stack_ports_module():
    module_path = Path(__file__).resolve().parents[3] / "scripts" / "dev_stack_ports.py"
    spec = importlib.util.spec_from_file_location("dev_stack_ports", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_resolve_port_keeps_requested_port_when_available(monkeypatch):
    module = _load_dev_stack_ports_module()

    monkeypatch.setattr(module, "is_port_available", lambda host, port: True)

    assert module.resolve_port("127.0.0.1", 8000) == 8000


def test_resolve_port_advances_until_free(monkeypatch):
    module = _load_dev_stack_ports_module()
    attempts = {8000: False, 8001: False, 8002: True}

    monkeypatch.setattr(
        module,
        "is_port_available",
        lambda host, port: attempts[port],
    )

    assert module.resolve_port("127.0.0.1", 8000) == 8002
