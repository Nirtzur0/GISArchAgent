import pytest

from src.domain.entities.regulation import RegulationType
from src.vectorstore.data_sources import get_sample_regulations

from tests.helpers.assertions import assert_allowed_values


pytestmark = [pytest.mark.unit, pytest.mark.data_contracts]


def test_sample_regulations__types__in_allowed_set():
    # Arrange
    samples = get_sample_regulations("default")
    values = [s.get("type") for s in samples]

    # Act / Assert
    assert_allowed_values(values, allowed=set(RegulationType), context="unit:sample_regulations:type")
