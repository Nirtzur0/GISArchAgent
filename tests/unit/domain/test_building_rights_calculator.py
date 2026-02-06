import pytest
from decimal import Decimal

from src.domain.value_objects.building_rights import BuildingRightsCalculator


pytestmark = [pytest.mark.unit]


def test_calculate_from_zone__r1__returns_expected_bounds():
    # Arrange
    plot = Decimal("1000")

    # Act
    rights = BuildingRightsCalculator.calculate_from_zone(plot_size_sqm=plot, zone_type="R1", location="Tel Aviv")

    # Assert
    assert rights.plot_size_sqm == plot
    assert rights.zone_type == "R1"

    assert Decimal("0") <= rights.max_coverage_percent <= Decimal("100")
    assert rights.max_coverage_sqm == plot * (rights.max_coverage_percent / Decimal("100"))

    assert rights.floor_area_ratio >= 0
    assert rights.max_building_area_sqm == plot * rights.floor_area_ratio

    assert rights.max_height_meters > 0
    assert rights.max_floors > 0

    assert rights.open_space_percent == Decimal("100") - rights.max_coverage_percent
    assert rights.open_space_sqm == plot - rights.max_coverage_sqm

    assert rights.parking_spaces_required >= 0


def test_calculate_from_zone__tama35__more_intense_than_r2():
    # Arrange
    plot = Decimal("1000")

    # Act
    r2 = BuildingRightsCalculator.calculate_from_zone(plot_size_sqm=plot, zone_type="R2", location="")
    t35 = BuildingRightsCalculator.calculate_from_zone(plot_size_sqm=plot, zone_type="TAMA35", location="")

    # Assert
    assert t35.floor_area_ratio >= r2.floor_area_ratio
    assert t35.max_floors >= r2.max_floors


def test_calculate_from_zone__invalid_plot_size__raises():
    with pytest.raises(ValueError, match="Plot size must be positive"):
        BuildingRightsCalculator.calculate_from_zone(plot_size_sqm=Decimal("0"), zone_type="R2", location="")
