import pytest
import requests

from src.infrastructure.repositories.iplan_repository import IPlanGISRepository

pytestmark = [pytest.mark.unit]


def test_search_by_location__network_failure__captures_error_signal(monkeypatch):
    repo = IPlanGISRepository(timeout=1)

    def _raise_timeout(*args, **kwargs):
        raise requests.exceptions.ReadTimeout("simulated timeout")

    monkeypatch.setattr(repo._session, "get", _raise_timeout)

    result = repo.search_by_location("Tel Aviv", limit=2)
    assert result == []

    err = repo.consume_last_error()
    assert err is not None
    assert err["operation"] == "search_by_location"
    assert err["error_class"] == "ReadTimeout"
    assert "simulated timeout" in err["message"]

    assert repo.consume_last_error() is None
