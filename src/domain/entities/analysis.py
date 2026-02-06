"""Analysis result entities."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from decimal import Decimal


class ComplianceStatus(Enum):
    """Compliance check status."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    REQUIRES_VARIANCE = "requires_variance"
    NEEDS_REVIEW = "needs_review"
    UNKNOWN = "unknown"


@dataclass
class VisionAnalysis:
    """
    Result of AI vision analysis on a plan image.
    
    Contains extracted information from visual plan analysis including
    zones, measurements, text, and AI-generated descriptions.
    """
    
    # Identity
    plan_id: str
    image_hash: str
    
    # Analysis content
    description: str
    zones_identified: List[str] = field(default_factory=list)
    measurements: Dict[str, Any] = field(default_factory=dict)
    
    # Extracted data
    ocr_text: Optional[str] = None
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    provider: str = "gemini"  # AI provider used
    model: str = "gemini-1.5-flash"
    tokens_used: int = 0
    cost_usd: Decimal = Decimal('0')
    
    # Caching
    from_cache: bool = False
    cached_at: Optional[datetime] = None
    
    # Timestamp
    analyzed_at: datetime = field(default_factory=datetime.now)
    
    # Confidence scores
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    
    def get_key_findings(self) -> List[str]:
        """Extract key findings from analysis."""
        findings = []
        
        if self.zones_identified:
            findings.append(f"{len(self.zones_identified)} zones identified")
        
        if self.measurements:
            findings.append(f"{len(self.measurements)} measurements extracted")
        
        if self.ocr_text:
            word_count = len(self.ocr_text.split())
            findings.append(f"{word_count} words extracted via OCR")
        
        return findings

    @property
    def text_content(self) -> Optional[str]:
        """Backwards-compatible alias for extracted OCR text."""
        return self.ocr_text

    @property
    def zones(self) -> List[str]:
        """Backwards-compatible alias for identified zones."""
        return self.zones_identified
    
    def was_cached(self) -> bool:
        """Check if result came from cache."""
        return self.from_cache
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'plan_id': self.plan_id,
            'image_hash': self.image_hash,
            'description': self.description,
            'zones_identified': self.zones_identified,
            'measurements': self.measurements,
            'ocr_text': self.ocr_text,
            'extracted_data': self.extracted_data,
            'provider': self.provider,
            'model': self.model,
            'tokens_used': self.tokens_used,
            'cost_usd': str(self.cost_usd),
            'from_cache': self.from_cache,
            'cached_at': self.cached_at.isoformat() if self.cached_at else None,
            'analyzed_at': self.analyzed_at.isoformat(),
            'confidence_scores': self.confidence_scores,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VisionAnalysis":
        """Rehydrate VisionAnalysis from a dict (for caching)."""
        cost = data.get("cost_usd", "0")
        try:
            cost_dec = Decimal(str(cost))
        except Exception:
            cost_dec = Decimal("0")

        cached_at = None
        if data.get("cached_at"):
            try:
                cached_at = datetime.fromisoformat(data["cached_at"])
            except Exception:
                cached_at = None

        analyzed_at = datetime.now()
        if data.get("analyzed_at"):
            try:
                analyzed_at = datetime.fromisoformat(data["analyzed_at"])
            except Exception:
                analyzed_at = datetime.now()

        return cls(
            plan_id=data["plan_id"],
            image_hash=data["image_hash"],
            description=data.get("description", ""),
            zones_identified=list(data.get("zones_identified") or []),
            measurements=dict(data.get("measurements") or {}),
            ocr_text=data.get("ocr_text"),
            extracted_data=dict(data.get("extracted_data") or {}),
            provider=data.get("provider", "gemini"),
            model=data.get("model", "gemini-1.5-flash"),
            tokens_used=int(data.get("tokens_used") or 0),
            cost_usd=cost_dec,
            from_cache=bool(data.get("from_cache") or False),
            cached_at=cached_at,
            analyzed_at=analyzed_at,
            confidence_scores=dict(data.get("confidence_scores") or {}),
        )
    
    def __str__(self) -> str:
        """String representation."""
        return f"VisionAnalysis(plan_id={self.plan_id}, zones={len(self.zones_identified)}, tokens={self.tokens_used})"


@dataclass
class ComplianceRequirement:
    """A single compliance requirement check."""
    name: str
    description: str
    required_value: Any
    actual_value: Any
    status: ComplianceStatus
    notes: Optional[str] = None
    regulation_ref: Optional[str] = None
    
    def is_compliant(self) -> bool:
        """Check if requirement is met."""
        return self.status == ComplianceStatus.COMPLIANT
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'description': self.description,
            'required_value': self.required_value,
            'actual_value': self.actual_value,
            'status': self.status.value,
            'notes': self.notes,
            'regulation_ref': self.regulation_ref,
        }


@dataclass
class ComplianceReport:
    """
    Compliance check report for a plan.
    
    Contains the results of checking a plan against applicable regulations.
    """
    
    # Identity
    plan_id: str
    plan_name: str
    
    # Requirements checked
    requirements: List[ComplianceRequirement] = field(default_factory=list)
    
    # Summary
    total_requirements: int = 0
    compliant_count: int = 0
    non_compliant_count: int = 0
    needs_review_count: int = 0
    
    # Overall status
    overall_status: ComplianceStatus = ComplianceStatus.UNKNOWN
    
    # Analysis
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    # Metadata
    checked_at: datetime = field(default_factory=datetime.now)
    checked_by: str = "system"
    regulations_checked: List[str] = field(default_factory=list)
    
    def calculate_compliance_rate(self) -> float:
        """Calculate percentage of compliant requirements."""
        if self.total_requirements == 0:
            return 0.0
        return (self.compliant_count / self.total_requirements) * 100
    
    def is_fully_compliant(self) -> bool:
        """Check if fully compliant."""
        return (self.overall_status == ComplianceStatus.COMPLIANT and 
                self.non_compliant_count == 0)
    
    def get_non_compliant_requirements(self) -> List[ComplianceRequirement]:
        """Get list of non-compliant requirements."""
        return [r for r in self.requirements 
                if r.status == ComplianceStatus.NON_COMPLIANT]
    
    def get_critical_issues(self) -> List[str]:
        """Get list of critical compliance issues."""
        issues = []
        for req in self.get_non_compliant_requirements():
            if req.notes:
                issues.append(f"{req.name}: {req.notes}")
            else:
                issues.append(req.name)
        return issues
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'plan_id': self.plan_id,
            'plan_name': self.plan_name,
            'requirements': [r.to_dict() for r in self.requirements],
            'total_requirements': self.total_requirements,
            'compliant_count': self.compliant_count,
            'non_compliant_count': self.non_compliant_count,
            'needs_review_count': self.needs_review_count,
            'overall_status': self.overall_status.value,
            'summary': self.summary,
            'recommendations': self.recommendations,
            'checked_at': self.checked_at.isoformat(),
            'checked_by': self.checked_by,
            'regulations_checked': self.regulations_checked,
            'compliance_rate': self.calculate_compliance_rate(),
        }
    
    def __str__(self) -> str:
        """String representation."""
        rate = self.calculate_compliance_rate()
        return f"ComplianceReport(plan={self.plan_id}, compliance={rate:.1f}%, status={self.overall_status.value})"
