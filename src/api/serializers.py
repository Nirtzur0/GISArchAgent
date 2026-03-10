"""Serialization helpers for API responses."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pyproj import Transformer


_ITM_TO_WGS84 = Transformer.from_crs("EPSG:2039", "EPSG:4326", always_xy=True)


def to_jsonable(value: Any) -> Any:
    """Convert domain objects into JSON-safe structures."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    if hasattr(value, "to_dict"):
        return to_jsonable(value.to_dict())
    if is_dataclass(value):
        return to_jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(item) for item in value]
    return str(value)


def serialize_data_feature(feature: dict[str, Any]) -> dict[str, Any]:
    """Serialize a DataStore feature and attach WGS84 geometry."""
    attrs = dict(feature.get("attributes") or {})
    geometry = dict(feature.get("geometry") or {})
    return {
        "attributes": to_jsonable(attrs),
        "geometry": to_jsonable(geometry),
        "geometry_wgs84": _serialize_geometry_wgs84(geometry),
        "has_geometry": bool(geometry.get("rings")),
    }


def _serialize_geometry_wgs84(geometry: dict[str, Any]) -> dict[str, Any] | None:
    rings = geometry.get("rings")
    if not rings:
        return None

    transformed_rings: list[list[list[float]]] = []
    centroids: list[tuple[float, float]] = []
    for ring in rings:
        current_ring: list[list[float]] = []
        for point in ring:
            if len(point) < 2:
                continue
            lon, lat = _ITM_TO_WGS84.transform(point[0], point[1])
            current_ring.append([lat, lon])
        if current_ring:
            transformed_rings.append(current_ring)
            avg_lat = sum(item[0] for item in current_ring) / len(current_ring)
            avg_lon = sum(item[1] for item in current_ring) / len(current_ring)
            centroids.append((avg_lat, avg_lon))

    if not transformed_rings:
        return None

    centroid = None
    if centroids:
        centroid = {
            "lat": sum(lat for lat, _ in centroids) / len(centroids),
            "lon": sum(lon for _, lon in centroids) / len(centroids),
        }

    return {"rings": transformed_rings, "centroid": centroid}

