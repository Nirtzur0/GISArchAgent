import pytest
from decimal import Decimal

from src.domain.value_objects.building_rights import BuildingRightsCalculator

from tests.helpers.assertions import assert_in_range


pytestmark = [pytest.mark.unit, pytest.mark.data_contracts]


@pytest.mark.parametrize("zone", ["R1", "R2", "R3", "C1", "TAMA35", "MIXED"])
def test_building_rights__calculated_fields__within_sane_ranges(zone):
    # Arrange
    plot = Decimal("1200")

    # Act
    rights = BuildingRightsCalculator.calculate_from_zone(plot_size_sqm=plot, zone_type=zone, location="")

    # Assert
    assert_in_range(float(rights.max_coverage_percent), min=0, max=100, context=f"rights:{zone}:coverage_percent")
    assert_in_range(float(rights.open_space_percent), min=0, max=100, context=f"rights:{zone}:open_space_percent")
    assert_in_range(float(rights.floor_area_ratio), min=0, max=10, context=f"rights:{zone}:far")
    assert_in_range(float(rights.max_height_meters), min=1, max=200, context=f"rights:{zone}:height")
    assert rights.max_floors >= 0
    assert rights.parking_spaces_required >= 0
