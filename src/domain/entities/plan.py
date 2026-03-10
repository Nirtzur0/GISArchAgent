"""Domain entities - Core business objects."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from decimal import Decimal


class PlanStatus(Enum):
    """Status of a planning scheme."""

    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_REVIEW = "in_review"
    ARCHIVED = "archived"

    @classmethod
    def from_string(cls, status_str: str) -> "PlanStatus":
        """Convert string to enum, with fallback."""
        status_map = {
            "טיוטה": cls.DRAFT,
            "בהליך": cls.PENDING,
            "אושר": cls.APPROVED,
            "נדחה": cls.REJECTED,
            "בבדיקה": cls.IN_REVIEW,
        }
        return status_map.get(status_str, cls.PENDING)


class ZoneType(Enum):
    """Zone designation types."""

    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    MIXED_USE = "mixed_use"
    PUBLIC = "public"
    OPEN_SPACE = "open_space"
    AGRICULTURAL = "agricultural"
    SPECIAL = "special"

    @classmethod
    def from_code(cls, code: Optional[str]) -> "ZoneType":
        """Convert zone code to enum."""
        if not code:
            return cls.RESIDENTIAL

        code = code.upper()
        if "R" in code or "מגורים" in code:
            return cls.RESIDENTIAL
        elif "C" in code or "מסחר" in code:
            return cls.COMMERCIAL
        elif "I" in code or "תעשייה" in code:
            return cls.INDUSTRIAL
        elif "M" in code or "מעורב" in code:
            return cls.MIXED_USE
        else:
            return cls.RESIDENTIAL


@dataclass
class Plan:
    """
    Represents a planning scheme or proposal.

    This is a core domain entity representing an urban planning document
    that defines land use, building rights, and development regulations
    for a specific area.
    """

    # Identity
    id: str
    name: str

    # Location
    location: str
    region: Optional[str] = None

    # Status
    status: PlanStatus = PlanStatus.PENDING

    # Classification
    zone_type: ZoneType = ZoneType.RESIDENTIAL
    plan_type: str = "local"  # local, district, national

    # Geometry (optional - can be None for regulations without specific boundaries)
    geometry: Optional[Dict[str, Any]] = None
    extent: Optional[Dict[str, float]] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    submitted_date: Optional[datetime] = None
    approved_date: Optional[datetime] = None
    effective_date: Optional[datetime] = None

    # Related data
    image_url: Optional[str] = None
    document_url: Optional[str] = None

    def is_approved(self) -> bool:
        """Check if plan is approved."""
        return self.status == PlanStatus.APPROVED

    def is_active(self) -> bool:
        """Check if plan is currently active."""
        if not self.is_approved():
            return False

        if self.effective_date:
            return self.effective_date <= datetime.now()

        return True

    def get_display_name(self) -> str:
        """Get formatted display name."""
        return f"{self.name} ({self.id})"

    def has_geometry(self) -> bool:
        """Check if plan has geometric data."""
        return self.geometry is not None

    def get_area_sqm(self) -> Optional[Decimal]:
        """Calculate plan area in square meters."""
        if not self.geometry:
            return None

        # This would need proper geometric calculation
        # Placeholder for now
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "region": self.region,
            "status": self.status.value,
            "zone_type": self.zone_type.value,
            "plan_type": self.plan_type,
            "geometry": self.geometry,
            "extent": self.extent,
            "metadata": self.metadata,
            "submitted_date": (
                self.submitted_date.isoformat() if self.submitted_date else None
            ),
            "approved_date": (
                self.approved_date.isoformat() if self.approved_date else None
            ),
            "effective_date": (
                self.effective_date.isoformat() if self.effective_date else None
            ),
            "image_url": self.image_url,
            "document_url": self.document_url,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Plan":
        """Create Plan from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            location=data["location"],
            region=data.get("region"),
            status=PlanStatus(data.get("status", "pending")),
            zone_type=ZoneType(data.get("zone_type", "residential")),
            plan_type=data.get("plan_type", "local"),
            geometry=data.get("geometry"),
            extent=data.get("extent"),
            metadata=data.get("metadata", {}),
            submitted_date=(
                datetime.fromisoformat(data["submitted_date"])
                if data.get("submitted_date")
                else None
            ),
            approved_date=(
                datetime.fromisoformat(data["approved_date"])
                if data.get("approved_date")
                else None
            ),
            effective_date=(
                datetime.fromisoformat(data["effective_date"])
                if data.get("effective_date")
                else None
            ),
            image_url=data.get("image_url"),
            document_url=data.get("document_url"),
        )

    def __str__(self) -> str:
        """String representation."""
        return f"Plan({self.id}: {self.name} - {self.status.value})"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"Plan(id='{self.id}', name='{self.name}', status={self.status})"
