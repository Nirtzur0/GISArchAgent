import pytest

from src.vectorstore.data_sources import get_sample_regulations

from tests.helpers.assertions import assert_required_fields


pytestmark = [pytest.mark.unit, pytest.mark.data_contracts]


def test_sample_regulations__required_fields_present_and_populated():
    # Arrange
    samples = get_sample_regulations("default")

    # Act / Assert
    for s in samples:
        assert_required_fields(
            s,
            fields=["id", "type", "title", "content", "jurisdiction"],
            context=f"sample_regulations:{s.get('id')}",
        )


def test_iplan_like_samples__required_metadata_fields_present():
    # Arrange
    samples = [s for s in get_sample_regulations("default") if str(s.get("id", "")).startswith("iplan_sample_")]

    assert samples, "Expected iPlan-like samples to exist in default sample data"

    # Act / Assert
    for s in samples:
        md = s.get("metadata") or {}
        assert_required_fields(md, fields=["plan_number", "municipality"], context=f"iplan_sample_metadata:{s['id']}")
