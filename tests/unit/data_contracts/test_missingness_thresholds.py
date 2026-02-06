import pytest

from src.vectorstore.data_sources import get_sample_regulations

from tests.helpers.assertions import assert_missing_rate


pytestmark = [pytest.mark.unit, pytest.mark.data_contracts]


def test_iplan_like_samples__plan_number_missingness__zero():
    # Arrange
    samples = [s for s in get_sample_regulations("default") if str(s.get("id", "")).startswith("iplan_sample_")]
    rows = [s.get("metadata") or {} for s in samples]

    # Act / Assert
    assert_missing_rate(rows, field="plan_number", max_rate=0.0, context="unit:sample_iplan:metadata")


def test_iplan_like_samples__municipality_missingness__zero():
    # Arrange
    samples = [s for s in get_sample_regulations("default") if str(s.get("id", "")).startswith("iplan_sample_")]
    rows = [s.get("metadata") or {} for s in samples]

    # Act / Assert
    assert_missing_rate(rows, field="municipality", max_rate=0.0, context="unit:sample_iplan:metadata")
