import pytest

from src.vectorstore.data_sources import get_sample_regulations

from tests.helpers.assertions import assert_unique


pytestmark = [pytest.mark.unit, pytest.mark.data_contracts]


def test_sample_regulations__ids__unique():
    # Arrange
    samples = get_sample_regulations("default")

    # Act / Assert
    assert_unique([s.get("id") for s in samples], context="unit:sample_regulations:ids")


def test_iplan_like_samples__plan_numbers__unique():
    # Arrange
    samples = [s for s in get_sample_regulations("default") if str(s.get("id", "")).startswith("iplan_sample_")]
    plan_numbers = [(s.get("metadata") or {}).get("plan_number") for s in samples]

    # Act / Assert
    assert_unique(plan_numbers, context="unit:sample_iplan:plan_number")
