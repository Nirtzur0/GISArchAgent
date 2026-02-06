"""Building rights value object."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class BuildingRights:
    """
    Immutable value object representing building rights for a plot.
    
    Building rights define what can be built on a specific plot based on
    zoning regulations and planning requirements.
    """
    
    # Plot information
    plot_size_sqm: Decimal
    zone_type: str
    
    # Coverage
    max_coverage_percent: Decimal  # Maximum building footprint as % of plot
    max_coverage_sqm: Decimal  # Maximum building footprint in sqm
    
    # Floor area
    floor_area_ratio: Decimal  # FAR - total building area / plot size
    max_building_area_sqm: Decimal  # Total allowed building area
    
    # Height
    max_height_meters: Decimal
    max_floors: int
    
    # Setbacks (distance from boundaries)
    front_setback_meters: Decimal
    side_setback_meters: Decimal
    rear_setback_meters: Decimal
    
    # Parking
    parking_spaces_required: int
    
    # Additional requirements
    open_space_percent: Decimal  # Required open space as % of plot
    open_space_sqm: Decimal  # Required open space in sqm
    
    # Optional features
    commercial_allowed: bool = False
    mixed_use_allowed: bool = False
    basement_allowed: bool = True
    roof_structures_allowed: bool = True
    
    def __post_init__(self):
        """Validate building rights after initialization."""
        if self.plot_size_sqm <= 0:
            raise ValueError("Plot size must be positive")
        
        if self.max_coverage_percent < 0 or self.max_coverage_percent > 100:
            raise ValueError("Coverage percent must be between 0 and 100")
        
        if self.floor_area_ratio < 0:
            raise ValueError("FAR must be non-negative")
        
        if self.max_floors < 0:
            raise ValueError("Max floors must be non-negative")
    
    def get_available_building_area(self, existing_area: Decimal = Decimal('0')) -> Decimal:
        """
        Calculate remaining available building area.
        
        Args:
            existing_area: Already built area in sqm
            
        Returns:
            Remaining buildable area in sqm
        """
        return max(Decimal('0'), self.max_building_area_sqm - existing_area)
    
    def get_available_coverage(self, existing_coverage: Decimal = Decimal('0')) -> Decimal:
        """
        Calculate remaining available ground coverage.
        
        Args:
            existing_coverage: Already covered area in sqm
            
        Returns:
            Remaining coverage area in sqm
        """
        return max(Decimal('0'), self.max_coverage_sqm - existing_coverage)
    
    def calculate_typical_floor_area(self) -> Decimal:
        """Calculate typical floor area assuming efficient use."""
        if self.max_floors == 0:
            return Decimal('0')
        
        # Typical floor is slightly less than max coverage to allow for setbacks
        return self.max_coverage_sqm * Decimal('0.9')
    
    def is_compliant_height(self, proposed_height: Decimal) -> bool:
        """Check if proposed height is compliant."""
        return proposed_height <= self.max_height_meters
    
    def is_compliant_coverage(self, proposed_coverage: Decimal) -> bool:
        """Check if proposed coverage is compliant."""
        return proposed_coverage <= self.max_coverage_sqm
    
    def is_compliant_building_area(self, proposed_area: Decimal) -> bool:
        """Check if proposed building area is compliant."""
        return proposed_area <= self.max_building_area_sqm
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'plot_size_sqm': str(self.plot_size_sqm),
            'zone_type': self.zone_type,
            'max_coverage_percent': str(self.max_coverage_percent),
            'max_coverage_sqm': str(self.max_coverage_sqm),
            'floor_area_ratio': str(self.floor_area_ratio),
            'max_building_area_sqm': str(self.max_building_area_sqm),
            'max_height_meters': str(self.max_height_meters),
            'max_floors': self.max_floors,
            'front_setback_meters': str(self.front_setback_meters),
            'side_setback_meters': str(self.side_setback_meters),
            'rear_setback_meters': str(self.rear_setback_meters),
            'parking_spaces_required': self.parking_spaces_required,
            'open_space_percent': str(self.open_space_percent),
            'open_space_sqm': str(self.open_space_sqm),
            'commercial_allowed': self.commercial_allowed,
            'mixed_use_allowed': self.mixed_use_allowed,
            'basement_allowed': self.basement_allowed,
            'roof_structures_allowed': self.roof_structures_allowed,
        }
    
    def get_summary(self) -> str:
        """Get human-readable summary."""
        return f"""Building Rights Summary:
- Plot Size: {self.plot_size_sqm} sqm
- Max Coverage: {self.max_coverage_sqm} sqm ({self.max_coverage_percent}%)
- Max Building Area: {self.max_building_area_sqm} sqm (FAR: {self.floor_area_ratio})
- Max Height: {self.max_height_meters}m ({self.max_floors} floors)
- Setbacks: Front {self.front_setback_meters}m, Side {self.side_setback_meters}m, Rear {self.rear_setback_meters}m
- Parking: {self.parking_spaces_required} spaces
- Open Space: {self.open_space_sqm} sqm ({self.open_space_percent}%)
"""
    
    def __str__(self) -> str:
        """String representation."""
        return f"BuildingRights(plot={self.plot_size_sqm}sqm, FAR={self.floor_area_ratio}, max_area={self.max_building_area_sqm}sqm)"


@dataclass(frozen=True)
class BuildingRightsCalculator:
    """
    Helper class for calculating building rights.
    
    This encapsulates the logic for deriving building rights from
    zoning regulations and plot characteristics.
    """
    
    @staticmethod
    def calculate_from_zone(
        plot_size_sqm: Decimal,
        zone_type: str,
        location: str = ""
    ) -> BuildingRights:
        """
        Calculate building rights based on zone type.
        
        This uses typical Israeli planning regulations. In production,
        this would query actual regulation database.
        
        Args:
            plot_size_sqm: Plot size in square meters
            zone_type: Zone designation (e.g., 'R1', 'C1', 'TAMA35')
            location: City/region for location-specific rules
            
        Returns:
            BuildingRights object
        """
        # Default values for residential zones
        coverage_percent = Decimal('40')
        far = Decimal('1.2')
        max_height = Decimal('15')
        max_floors = 4
        
        # Adjust based on zone type
        zone_upper = (zone_type or "").upper()
        zone_norm = zone_upper.replace(" ", "").replace("-", "")

        # Prefer explicit codes used by the app UI (R1/R2/R3/C1/MIXED/TAMA35).
        if zone_norm.startswith("TAMA35"):
            # TAMA 35 - Urban renewal
            coverage_percent = Decimal('50')
            far = Decimal('2.5')
            max_height = Decimal('30')
            max_floors = 8

        elif zone_norm.startswith("R1") or zone_norm in {"A", "ZONEA"}:
            # Low-density residential
            coverage_percent = Decimal('30')
            far = Decimal('0.9')
            max_height = Decimal('12')
            max_floors = 3

        elif zone_norm.startswith("R2") or zone_norm in {"B", "ZONEB"}:
            # Medium-density residential
            coverage_percent = Decimal('40')
            far = Decimal('1.2')
            max_height = Decimal('15')
            max_floors = 4

        elif zone_norm.startswith("R3") or zone_norm in {"C", "ZONEC"}:
            # High-density residential
            coverage_percent = Decimal('50')
            far = Decimal('2.0')
            max_height = Decimal('25')
            max_floors = 7

        elif zone_norm.startswith("C1"):
            # Commercial
            coverage_percent = Decimal('70')
            far = Decimal('3.0')
            max_height = Decimal('40')
            max_floors = 10
        
        # Calculate derived values
        max_coverage_sqm = plot_size_sqm * (coverage_percent / Decimal('100'))
        max_building_area_sqm = plot_size_sqm * far
        open_space_percent = Decimal('100') - coverage_percent
        open_space_sqm = plot_size_sqm - max_coverage_sqm
        
        # Calculate parking (1 space per 50 sqm typically)
        parking_spaces = int(max_building_area_sqm / Decimal('50'))
        
        # Standard setbacks
        front_setback = Decimal('5')
        side_setback = Decimal('3')
        rear_setback = Decimal('4')
        
        return BuildingRights(
            plot_size_sqm=plot_size_sqm,
            zone_type=zone_type,
            max_coverage_percent=coverage_percent,
            max_coverage_sqm=max_coverage_sqm,
            floor_area_ratio=far,
            max_building_area_sqm=max_building_area_sqm,
            max_height_meters=max_height,
            max_floors=max_floors,
            front_setback_meters=front_setback,
            side_setback_meters=side_setback,
            rear_setback_meters=rear_setback,
            parking_spaces_required=parking_spaces,
            open_space_percent=open_space_percent,
            open_space_sqm=open_space_sqm,
            commercial_allowed='C' in zone_upper or 'MIXED' in zone_upper,
            mixed_use_allowed='MIXED' in zone_upper,
        )
