import pytest
from datetime import date

from src.domain.entities.regulation import Regulation, RegulationType


pytestmark = [pytest.mark.unit]


def test_applies_to_location__tama_or_national__always_true():
    # Arrange
    tama = Regulation(
        id="tama_35",
        type=RegulationType.TAMA,
        title="TAMA 35",
        content="...",
        jurisdiction="national",
    )

    # Act / Assert
    assert tama.applies_to_location("Tel Aviv") is True
    assert tama.applies_to_location("ירושלים") is True


def test_applies_to_location__jurisdiction_match__true_otherwise_false():
    # Arrange
    reg = Regulation(
        id="local_1",
        type=RegulationType.LOCAL,
        title="Local plan",
        content="...",
        jurisdiction="Tel Aviv",
    )

    # Act / Assert
    assert reg.applies_to_location("Tel Aviv") is True
    assert reg.applies_to_location("Haifa") is False


def test_applies_to_location__metadata_locations__honored():
    # Arrange
    reg = Regulation(
        id="local_2",
        type=RegulationType.LOCAL,
        title="Local plan",
        content="...",
        jurisdiction="Somewhere",
        metadata={"locations": ["Jerusalem", "חיפה"]},
    )

    # Act / Assert
    assert reg.applies_to_location("Jerusalem") is True
    assert reg.applies_to_location("חיפה") is True


def test_applies_to_zone__no_applicable_zones__applies_to_all():
    # Arrange
    reg = Regulation(
        id="zoning_1",
        type=RegulationType.ZONING,
        title="Zoning",
        content="...",
    )

    # Act / Assert
    assert reg.applies_to_zone("R1") is True


def test_applies_to_zone__with_applicable_zones__filters():
    # Arrange
    reg = Regulation(
        id="zoning_2",
        type=RegulationType.ZONING,
        title="Zoning",
        content="...",
        applicable_zones=["R1", "R2"],
    )

    # Act / Assert
    assert reg.applies_to_zone("R1") is True
    assert reg.applies_to_zone("C1") is False


def test_to_dict_from_dict__roundtrip__preserves_fields():
    # Arrange
    reg = Regulation(
        id="reg_1",
        type=RegulationType.LOCAL,
        title="Title",
        content="Content",
        jurisdiction="national",
        effective_date=date(2020, 1, 1),
        metadata={"plan_number": "101-0121850"},
        tags=["a"],
    )

    # Act
    data = reg.to_dict()
    reg2 = Regulation.from_dict(data)

    # Assert
    assert reg2.id == reg.id
    assert reg2.type == reg.type
    assert reg2.title == reg.title
    assert reg2.content == reg.content
    assert reg2.jurisdiction == reg.jurisdiction
    assert reg2.effective_date == reg.effective_date
    assert reg2.metadata["plan_number"] == "101-0121850"
