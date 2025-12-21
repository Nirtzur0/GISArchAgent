"""
Vector Database Health Check and Validation

Comprehensive validation system to ensure vector database is:
- Initialized with data
- Fresh (not outdated)
- Complete (sufficient regulations)
- Healthy (no corruption)
- Up-to-date with source
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path

from src.infrastructure.repositories.chroma_repository import ChromaRegulationRepository
from src.vectorstore.initializer import VectorDBInitializer

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of vector database health check."""
    is_healthy: bool
    status: str  # 'healthy', 'warning', 'critical', 'uninitialized'
    issues: list[str]
    recommendations: list[str]
    stats: Dict[str, Any]
    last_updated: Optional[datetime] = None
    needs_refresh: bool = False


class VectorDBHealthChecker:
    """
    Performs comprehensive health checks on vector database.
    
    Checks:
    1. Initialization status (has data)
    2. Data freshness (not too old)
    3. Data completeness (minimum thresholds)
    4. Data integrity (no corruption)
    5. Metadata consistency
    """
    
    # Thresholds
    MIN_REGULATIONS = 10  # Minimum acceptable regulations
    RECOMMENDED_REGULATIONS = 100  # Recommended minimum
    MAX_AGE_DAYS = 30  # Data older than this triggers warning
    CRITICAL_AGE_DAYS = 90  # Data older than this is critical
    
    def __init__(
        self,
        repository: ChromaRegulationRepository,
        metadata_file: str = "data/vectorstore/metadata.json"
    ):
        """
        Initialize health checker.
        
        Args:
            repository: ChromaDB regulation repository
            metadata_file: Path to metadata tracking file
        """
        self.repository = repository
        self.metadata_file = Path(metadata_file)
        self.initializer = VectorDBInitializer(repository)
    
    def perform_health_check(self) -> HealthCheckResult:
        """
        Perform comprehensive health check.
        
        Returns:
            HealthCheckResult with status and recommendations
        """
        issues = []
        recommendations = []
        
        # Get basic stats
        stats = self.repository.get_statistics()
        total_regs = stats.get('total_regulations', 0)
        
        # Check 1: Initialization
        if total_regs == 0:
            return HealthCheckResult(
                is_healthy=False,
                status='uninitialized',
                issues=['Vector database is empty'],
                recommendations=['Run initialization to populate with regulations'],
                stats=stats,
                needs_refresh=True
            )
        
        # Check 2: Data completeness
        if total_regs < self.MIN_REGULATIONS:
            issues.append(f'Only {total_regs} regulations (minimum: {self.MIN_REGULATIONS})')
            recommendations.append('Fetch more regulations from iPlan')
        
        if total_regs < self.RECOMMENDED_REGULATIONS:
            issues.append(f'Low regulation count: {total_regs} (recommended: {self.RECOMMENDED_REGULATIONS})')
            recommendations.append('Consider running full data sync')
        
        # Check 3: Data freshness
        metadata = self._load_metadata()
        last_updated = metadata.get('last_updated')
        
        if last_updated:
            age_days = (datetime.now() - last_updated).days
            
            if age_days > self.CRITICAL_AGE_DAYS:
                issues.append(f'Data critically outdated: {age_days} days old')
                recommendations.append('URGENT: Run data refresh immediately')
                status = 'critical'
            elif age_days > self.MAX_AGE_DAYS:
                issues.append(f'Data may be outdated: {age_days} days old')
                recommendations.append('Consider refreshing data from iPlan')
                status = 'warning'
            else:
                status = 'healthy'
        else:
            issues.append('Unknown data age - no metadata found')
            recommendations.append('Run data refresh to track freshness')
            status = 'warning'
            last_updated = None
        
        # Check 4: Data integrity
        integrity_issues = self._check_integrity()
        if integrity_issues:
            issues.extend(integrity_issues)
            recommendations.append('Some regulations may be corrupted - consider re-indexing')
        
        # Determine overall health
        if not issues:
            is_healthy = True
            status = 'healthy'
        elif status == 'critical' or total_regs < self.MIN_REGULATIONS:
            is_healthy = False
            status = 'critical'
        else:
            is_healthy = True  # Warnings but functional
            status = 'warning'
        
        needs_refresh = (
            total_regs < self.RECOMMENDED_REGULATIONS or
            (last_updated and (datetime.now() - last_updated).days > self.MAX_AGE_DAYS)
        )
        
        return HealthCheckResult(
            is_healthy=is_healthy,
            status=status,
            issues=issues,
            recommendations=recommendations,
            stats=stats,
            last_updated=last_updated,
            needs_refresh=needs_refresh
        )
    
    def _check_integrity(self) -> list[str]:
        """Check data integrity by sampling regulations."""
        issues = []
        
        try:
            # Sample a few regulations
            results = self.repository._collection.get(limit=5)
            
            if not results or not results.get('documents'):
                issues.append('No documents returned from database')
                return issues
            
            # Check for required fields
            for i, doc in enumerate(results['documents']):
                if not doc or len(doc.strip()) < 10:
                    issues.append(f'Regulation {i+1} has empty or very short content')
                
                metadata = results['metadatas'][i] if results.get('metadatas') else {}
                if not metadata:
                    issues.append(f'Regulation {i+1} missing metadata')
        
        except Exception as e:
            issues.append(f'Integrity check failed: {str(e)}')
        
        return issues
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata tracking file."""
        import json
        
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, 'r') as f:
                data = json.load(f)
                
                # Parse datetime if present
                if 'last_updated' in data:
                    data['last_updated'] = datetime.fromisoformat(data['last_updated'])
                
                return data
        
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            return {}
    
    def update_metadata(self, regulations_added: int = 0):
        """Update metadata after data refresh.
        
        Args:
            regulations_added: Number of new regulations added
        """
        import json
        
        metadata = self._load_metadata()
        
        metadata.update({
            'last_updated': datetime.now().isoformat(),
            'total_regulations': self.repository.get_statistics()['total_regulations'],
            'last_refresh_added': regulations_added,
            'last_check': datetime.now().isoformat()
        })
        
        # Ensure directory exists
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Metadata updated: {metadata}")
        
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def get_status_display(self) -> str:
        """Get human-readable status display.
        
        Returns:
            Formatted status string for display
        """
        result = self.perform_health_check()
        
        status_emoji = {
            'healthy': '✅',
            'warning': '⚠️',
            'critical': '❌',
            'uninitialized': '⚪'
        }
        
        emoji = status_emoji.get(result.status, '❓')
        
        lines = [
            f"{emoji} Vector Database Status: **{result.status.upper()}**",
            f"",
            f"📊 **Statistics:**",
            f"- Total Regulations: {result.stats.get('total_regulations', 0)}",
        ]
        
        if result.last_updated:
            age_days = (datetime.now() - result.last_updated).days
            lines.append(f"- Last Updated: {age_days} days ago")
        
        if result.issues:
            lines.append(f"")
            lines.append(f"⚠️ **Issues:**")
            for issue in result.issues:
                lines.append(f"- {issue}")
        
        if result.recommendations:
            lines.append(f"")
            lines.append(f"💡 **Recommendations:**")
            for rec in result.recommendations:
                lines.append(f"- {rec}")
        
        return "\n".join(lines)


def check_vectordb_health(repository: ChromaRegulationRepository) -> HealthCheckResult:
    """
    Convenience function to perform health check.
    
    Args:
        repository: ChromaDB regulation repository
        
    Returns:
        HealthCheckResult
    """
    checker = VectorDBHealthChecker(repository)
    return checker.perform_health_check()
