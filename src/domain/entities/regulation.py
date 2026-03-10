"""Regulation domain entity."""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional, Dict, Any, List


class RegulationType(Enum):
    """Types of planning regulations."""

    TAMA = "tama"  # National Outline Plan
    DISTRICT = "district"  # District plan
    LOCAL = "local"  # Local plan
    ZONING = "zoning"  # Zoning regulation
    BUILDING_CODE = "building_code"  # Building standards
    ENVIRONMENTAL = "environmental"  # Environmental regulations
    HERITAGE = "heritage"  # Heritage preservation
    PROCEDURE = "procedure"  # Planning procedures

    @classmethod
    def from_string(cls, type_str: str) -> "RegulationType":
        """Convert string to enum."""
        type_map = {
            "תמא": cls.TAMA,
            "מחוז": cls.DISTRICT,
            "מקומי": cls.LOCAL,
            "zoning": cls.ZONING,
            "building": cls.BUILDING_CODE,
        }
        return type_map.get(type_str.lower(), cls.LOCAL)


@dataclass
class Regulation:
    """
    Represents a planning regulation or requirement.

    Regulations are rules that govern planning, construction, and land use.
    They can be national (TAMA), regional (district), or local.
    """

    # Identity
    id: str
    type: RegulationType

    # Content
    title: str
    content: str
    summary: Optional[str] = None

    # Scope
    jurisdiction: str = "national"  # national, district, city
    applicable_zones: List[str] = field(default_factory=list)

    # Dates
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    last_updated: Optional[datetime] = None

    # References
    source_document: Optional[str] = None
    related_regulations: List[str] = field(default_factory=list)
    supersedes: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def is_active(self) -> bool:
        """Check if regulation is currently active."""
        now = datetime.now().date()

        if self.effective_date and self.effective_date > now:
            return False

        if self.expiry_date and self.expiry_date < now:
            return False

        return True

    def applies_to_location(self, location: str) -> bool:
        """
        Check if regulation applies to a specific location.

        Args:
            location: City or region name

        Returns:
            True if regulation applies to location
        """
        location_lower = location.lower()
        jurisdiction_lower = self.jurisdiction.lower()

        # National regulations apply everywhere
        if self.type == RegulationType.TAMA or jurisdiction_lower == "national":
            return True

        # Check if location matches jurisdiction
        if location_lower in jurisdiction_lower or jurisdiction_lower in location_lower:
            return True

        # Check metadata for additional locations
        applicable_locations = self.metadata.get("locations", [])
        return any(loc.lower() in location_lower for loc in applicable_locations)

    def applies_to_zone(self, zone_code: str) -> bool:
        """
        Check if regulation applies to a specific zone.

        Args:
            zone_code: Zone designation code

        Returns:
            True if regulation applies to zone
        """
        if not self.applicable_zones:
            return True  # No specific zones means applies to all

        return zone_code in self.applicable_zones

    def get_key_requirements(self) -> List[str]:
        """Extract key requirements from regulation content."""
        # This is a simplified version
        # In production, might use NLP to extract requirements
        requirements = self.metadata.get("key_requirements", [])
        return requirements if requirements else []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "jurisdiction": self.jurisdiction,
            "applicable_zones": self.applicable_zones,
            "effective_date": (
                self.effective_date.isoformat() if self.effective_date else None
            ),
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "last_updated": (
                self.last_updated.isoformat() if self.last_updated else None
            ),
            "source_document": self.source_document,
            "related_regulations": self.related_regulations,
            "supersedes": self.supersedes,
            "metadata": self.metadata,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Regulation":
        """Create Regulation from dictionary."""
        return cls(
            id=data["id"],
            type=RegulationType(data["type"]),
            title=data["title"],
            content=data["content"],
            summary=data.get("summary"),
            jurisdiction=data.get("jurisdiction", "national"),
            applicable_zones=data.get("applicable_zones", []),
            effective_date=(
                date.fromisoformat(data["effective_date"])
                if data.get("effective_date")
                else None
            ),
            expiry_date=(
                date.fromisoformat(data["expiry_date"])
                if data.get("expiry_date")
                else None
            ),
            last_updated=(
                datetime.fromisoformat(data["last_updated"])
                if data.get("last_updated")
                else None
            ),
            source_document=data.get("source_document"),
            related_regulations=data.get("related_regulations", []),
            supersedes=data.get("supersedes"),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
        )

    def __str__(self) -> str:
        """String representation."""
        return f"Regulation({self.id}: {self.title})"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"Regulation(id='{self.id}', type={self.type}, title='{self.title}')"
