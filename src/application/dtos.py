"""Data Transfer Objects for application services."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from src.domain.entities.plan import Plan
from src.domain.entities.regulation import Regulation
from src.domain.entities.analysis import VisionAnalysis
from src.domain.value_objects.building_rights import BuildingRights


@dataclass
class PlanSearchQuery:
    """Query for plan search use case."""

    plan_id: Optional[str] = None
    location: Optional[str] = None
    keyword: Optional[str] = None
    status: Optional[str] = None
    include_vision_analysis: bool = True
    max_results: int = 3


@dataclass
class AnalyzedPlan:
    """Plan with vision analysis."""

    plan: Plan
    vision_analysis: Optional[VisionAnalysis] = None
    image_bytes: Optional[bytes] = None


@dataclass
class PlanSearchResult:
    """Result of plan search."""

    plans: List[AnalyzedPlan]
    query: PlanSearchQuery
    total_found: int
    timestamp: datetime = field(default_factory=datetime.now)
    execution_time_ms: float = 0.0


@dataclass
class RegulationQuery:
    """Query for regulation search."""

    query_text: str
    location: Optional[str] = None
    regulation_type: Optional[str] = None
    max_results: int = 5
    request_id: Optional[str] = None


@dataclass
class RegulationResult:
    """Result of regulation query."""

    regulations: List[Regulation]
    query: RegulationQuery
    total_found: int
    answer: Optional[str] = None  # AI-generated answer
    answer_status: str = "unavailable"
    answer_warning: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class BuildingRightsQuery:
    """Query for building rights calculation."""

    plot_size_sqm: float
    zone_type: str
    location: str


@dataclass
class BuildingRightsResult:
    """Result of building rights calculation."""

    building_rights: BuildingRights
    applicable_regulations: List[Regulation]
    query: BuildingRightsQuery
    timestamp: datetime = field(default_factory=datetime.now)
