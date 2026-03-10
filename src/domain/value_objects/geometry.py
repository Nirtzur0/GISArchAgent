"""Geometry value object."""

from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from decimal import Decimal
import math


@dataclass(frozen=True)
class Geometry:
    """
    Immutable value object representing geometric data.

    Supports points, lines, and polygons in various coordinate systems.
    """

    geometry_type: str  # 'point', 'line', 'polygon'
    coordinates: Tuple[Tuple[float, ...], ...]  # Immutable nested tuples
    srid: int = 2039  # Spatial Reference ID (Israeli TM Grid by default)

    def __post_init__(self):
        """Validate geometry after initialization."""
        valid_types = ("point", "line", "polygon", "multipolygon")
        if self.geometry_type not in valid_types:
            raise ValueError(f"Geometry type must be one of {valid_types}")

        if not self.coordinates:
            raise ValueError("Coordinates cannot be empty")

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """
        Get bounding box (minx, miny, maxx, maxy).

        Returns:
            Tuple of (min_x, min_y, max_x, max_y)
        """
        all_x = []
        all_y = []

        for coord in self.coordinates:
            if len(coord) >= 2:
                all_x.append(coord[0])
                all_y.append(coord[1])

        if not all_x or not all_y:
            return (0.0, 0.0, 0.0, 0.0)

        return (min(all_x), min(all_y), max(all_x), max(all_y))

    def get_center(self) -> Tuple[float, float]:
        """
        Get geometric center (centroid approximation).

        Returns:
            Tuple of (center_x, center_y)
        """
        bounds = self.get_bounds()
        center_x = (bounds[0] + bounds[2]) / 2
        center_y = (bounds[1] + bounds[3]) / 2
        return (center_x, center_y)

    def calculate_area(self) -> Optional[Decimal]:
        """
        Calculate area for polygon geometry.

        Uses shoelace formula for simple polygons.

        Returns:
            Area in square meters, or None for non-polygon types
        """
        if self.geometry_type not in ("polygon", "multipolygon"):
            return None

        if len(self.coordinates) < 3:
            return Decimal("0")

        # Shoelace formula
        area = Decimal("0")
        n = len(self.coordinates)

        for i in range(n):
            j = (i + 1) % n
            area += Decimal(str(self.coordinates[i][0])) * Decimal(
                str(self.coordinates[j][1])
            )
            area -= Decimal(str(self.coordinates[j][0])) * Decimal(
                str(self.coordinates[i][1])
            )

        return abs(area) / Decimal("2")

    def calculate_perimeter(self) -> Optional[Decimal]:
        """
        Calculate perimeter for polygon geometry.

        Returns:
            Perimeter in meters, or None for non-polygon types
        """
        if self.geometry_type not in ("polygon", "line"):
            return None

        if len(self.coordinates) < 2:
            return Decimal("0")

        perimeter = Decimal("0")
        n = len(self.coordinates)

        for i in range(n - 1):
            dx = Decimal(str(self.coordinates[i + 1][0] - self.coordinates[i][0]))
            dy = Decimal(str(self.coordinates[i + 1][1] - self.coordinates[i][1]))
            distance = (dx * dx + dy * dy).sqrt()
            perimeter += distance

        # Close the polygon
        if self.geometry_type == "polygon" and n > 2:
            dx = Decimal(str(self.coordinates[0][0] - self.coordinates[n - 1][0]))
            dy = Decimal(str(self.coordinates[0][1] - self.coordinates[n - 1][1]))
            distance = (dx * dx + dy * dy).sqrt()
            perimeter += distance

        return perimeter

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (GeoJSON-like)."""
        return {
            "type": self.geometry_type,
            "coordinates": self.coordinates,
            "srid": self.srid,
        }

    def to_geojson(self) -> Dict[str, Any]:
        """Convert to GeoJSON format."""
        geom_type_map = {
            "point": "Point",
            "line": "LineString",
            "polygon": "Polygon",
            "multipolygon": "MultiPolygon",
        }

        return {
            "type": geom_type_map.get(self.geometry_type, "Polygon"),
            "coordinates": list(self.coordinates),
        }

    @classmethod
    def from_arcgis(cls, arcgis_geom: Dict[str, Any], srid: int = 2039) -> "Geometry":
        """
        Create Geometry from ArcGIS REST API response.

        Args:
            arcgis_geom: Geometry dict from ArcGIS (with 'rings', 'paths', or 'x'/'y')
            srid: Spatial reference ID

        Returns:
            Geometry object
        """
        if not arcgis_geom:
            # Default point at origin
            return cls("point", ((0.0, 0.0),), srid)

        # Point geometry
        if "x" in arcgis_geom and "y" in arcgis_geom:
            coords = ((float(arcgis_geom["x"]), float(arcgis_geom["y"])),)
            return cls("point", coords, srid)

        # Polygon geometry (rings)
        if "rings" in arcgis_geom and arcgis_geom["rings"]:
            # Use first ring (exterior ring)
            ring = arcgis_geom["rings"][0]
            coords = tuple(tuple(float(c) for c in pt) for pt in ring)
            return cls("polygon", coords, srid)

        # Line geometry (paths)
        if "paths" in arcgis_geom and arcgis_geom["paths"]:
            path = arcgis_geom["paths"][0]
            coords = tuple(tuple(float(c) for c in pt) for pt in path)
            return cls("line", coords, srid)

        # Default to empty point
        return cls("point", ((0.0, 0.0),), srid)

    @classmethod
    def from_wkt(cls, wkt_string: str, srid: int = 2039) -> "Geometry":
        """
        Create Geometry from Well-Known Text (WKT).

        Simplified parser for common geometry types.

        Args:
            wkt_string: WKT representation (e.g., "POINT (180000 620000)")
            srid: Spatial reference ID

        Returns:
            Geometry object
        """
        wkt_upper = wkt_string.upper().strip()

        if wkt_upper.startswith("POINT"):
            # Extract coordinates from "POINT (x y)"
            coords_str = wkt_upper.replace("POINT", "").strip("() ")
            x, y = map(float, coords_str.split())
            return cls("point", ((x, y),), srid)

        elif wkt_upper.startswith("POLYGON"):
            # Extract coordinates from "POLYGON ((x1 y1, x2 y2, ...))"
            coords_str = wkt_upper.replace("POLYGON", "").strip("() ")
            points = coords_str.split(",")
            coords = tuple(tuple(map(float, pt.strip().split())) for pt in points)
            return cls("polygon", coords, srid)

        # Default to point at origin
        return cls("point", ((0.0, 0.0),), srid)

    def __str__(self) -> str:
        """String representation."""
        if self.geometry_type == "point":
            return f"Point({self.coordinates[0][0]}, {self.coordinates[0][1]})"
        else:
            return f"{self.geometry_type.capitalize()}({len(self.coordinates)} points)"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"Geometry(type='{self.geometry_type}', points={len(self.coordinates)}, srid={self.srid})"
