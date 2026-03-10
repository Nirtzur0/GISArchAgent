"""
Building Rights Service - Calculate building rights for plots.

This service calculates maximum building area, coverage, height, and
other requirements based on plot size, zone type, and location.
"""

import logging
from typing import List, Optional, Callable
from decimal import Decimal

from src.domain.repositories import IRegulationRepository
from src.domain.entities.regulation import Regulation, RegulationType
from src.domain.value_objects.building_rights import (
    BuildingRights,
    BuildingRightsCalculator,
)
from src.application.dtos import BuildingRightsQuery, BuildingRightsResult

logger = logging.getLogger(__name__)


class BuildingRightsService:
    """
    Application service for building rights calculation.

    Calculates what can be built on a plot based on zoning regulations.
    This is a core feature for architecture firms planning projects.
    """

    def __init__(
        self,
        regulation_repository: Optional[IRegulationRepository] = None,
        regulation_repo_provider: Optional[Callable[[], IRegulationRepository]] = None,
    ):
        """
        Initialize service.

        Args:
            regulation_repository: Repository for regulation data
        """
        self._regulation_repo = regulation_repository
        self._regulation_repo_provider = regulation_repo_provider

    def calculate_building_rights(
        self,
        query: BuildingRightsQuery,
        include_regulations: bool = True,
    ) -> BuildingRightsResult:
        """
        Calculate building rights for a plot.

        Args:
            query: Query with plot details

        Returns:
            Building rights and applicable regulations
        """
        logger.info(f"Calculating building rights: {query}")

        try:
            # Calculate building rights
            building_rights = BuildingRightsCalculator.calculate_from_zone(
                plot_size_sqm=Decimal(str(query.plot_size_sqm)),
                zone_type=query.zone_type,
                location=query.location,
            )

            regulations = []
            if include_regulations:
                if (
                    self._regulation_repo is None
                    and self._regulation_repo_provider is not None
                ):
                    self._regulation_repo = self._regulation_repo_provider()
                regulations = self._find_applicable_regulations(query)

            return BuildingRightsResult(
                building_rights=building_rights,
                applicable_regulations=regulations,
                query=query,
            )

        except Exception as e:
            logger.error(f"Building rights calculation failed: {e}", exc_info=True)
            raise

    def _find_applicable_regulations(
        self, query: BuildingRightsQuery
    ) -> List[Regulation]:
        """
        Find regulations applicable to the plot.

        Args:
            query: Building rights query

        Returns:
            List of applicable regulations
        """
        regulations = []

        if self._regulation_repo is None:
            return []

        try:
            # Get location-specific regulations
            location_regs = self._regulation_repo.get_applicable_to_location(
                location=query.location, limit=5
            )
            regulations.extend(location_regs)

            # Get zoning regulations
            zoning_regs = self._regulation_repo.get_by_type(
                regulation_type="zoning", limit=5
            )
            regulations.extend(
                [r for r in zoning_regs if r.applies_to_zone(query.zone_type)]
            )

            # Get TAMA regulations if applicable
            if "TAMA" in query.zone_type.upper():
                tama_regs = self._regulation_repo.get_by_type(
                    regulation_type="tama", limit=3
                )
                regulations.extend(tama_regs)

            # Remove duplicates
            seen = set()
            unique_regs = []
            for reg in regulations:
                if reg.id not in seen:
                    seen.add(reg.id)
                    unique_regs.append(reg)

            return unique_regs

        except Exception as e:
            logger.error(f"Failed to find regulations: {e}")
            return []

    def get_parking_requirements(
        self, building_area_sqm: float, use_type: str = "residential"
    ) -> int:
        """
        Calculate parking space requirements.

        Args:
            building_area_sqm: Total building area
            use_type: Type of use (residential, commercial, etc.)

        Returns:
            Number of required parking spaces
        """
        # Typical Israeli parking requirements
        if use_type.lower() == "residential":
            # 1 space per 50 sqm
            return int(building_area_sqm / 50)
        elif use_type.lower() == "commercial":
            # 1 space per 40 sqm
            return int(building_area_sqm / 40)
        elif use_type.lower() == "office":
            # 1 space per 30 sqm
            return int(building_area_sqm / 30)
        else:
            # Default: 1 space per 50 sqm
            return int(building_area_sqm / 50)

    def validate_proposed_building(
        self,
        query: BuildingRightsQuery,
        proposed_area: float,
        proposed_coverage: float,
        proposed_height: float,
    ) -> dict:
        """
        Validate a proposed building against rights.

        Args:
            query: Building rights query
            proposed_area: Proposed total building area (sqm)
            proposed_coverage: Proposed ground coverage (sqm)
            proposed_height: Proposed height (meters)

        Returns:
            Dict with validation results
        """
        result = self.calculate_building_rights(query)
        rights = result.building_rights

        return {
            "area_compliant": proposed_area <= float(rights.max_building_area_sqm),
            "area_allowed": float(rights.max_building_area_sqm),
            "area_proposed": proposed_area,
            "coverage_compliant": proposed_coverage <= float(rights.max_coverage_sqm),
            "coverage_allowed": float(rights.max_coverage_sqm),
            "coverage_proposed": proposed_coverage,
            "height_compliant": proposed_height <= float(rights.max_height_meters),
            "height_allowed": float(rights.max_height_meters),
            "height_proposed": proposed_height,
            "overall_compliant": all(
                [
                    proposed_area <= float(rights.max_building_area_sqm),
                    proposed_coverage <= float(rights.max_coverage_sqm),
                    proposed_height <= float(rights.max_height_meters),
                ]
            ),
        }
