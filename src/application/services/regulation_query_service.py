"""
Regulation Query Service - Natural language queries about regulations.

This service handles queries about planning regulations, zoning requirements,
and procedural questions using semantic search and LLM synthesis.
"""

import logging
from typing import Optional, List, Any
from datetime import datetime

from src.domain.repositories import IRegulationRepository
from src.domain.entities.regulation import Regulation
from src.application.dtos import RegulationQuery, RegulationResult

logger = logging.getLogger(__name__)


class RegulationQueryService:
    """
    Application service for regulation queries.
    
    Handles natural language questions about planning regulations,
    TAMA plans, zoning rules, and procedures.
    """
    
    def __init__(
        self,
        regulation_repository: IRegulationRepository,
        llm_service: Optional[Any] = None
    ):
        """
        Initialize service with dependencies.
        
        Args:
            regulation_repository: Repository for regulation data
            llm_service: Optional LLM for answer synthesis
        """
        self._regulation_repo = regulation_repository
        self._llm = llm_service
    
    def query(self, query: RegulationQuery) -> RegulationResult:
        """
        Execute regulation query.
        
        Args:
            query: Query parameters
            
        Returns:
            Regulations and synthesized answer
        """
        logger.info(f"Executing regulation query: {query.query_text}")
        
        try:
            # Search for relevant regulations
            regulations = self._search_regulations(query)
            
            # Generate answer using LLM if available
            answer: Optional[str] = None
            if regulations:
                if self._llm:
                    answer = self._synthesize_answer(query, regulations)
                else:
                    answer = self._fallback_answer(query, regulations)
            
            return RegulationResult(
                regulations=regulations,
                query=query,
                total_found=len(regulations),
                answer=answer
            )
        
        except Exception as e:
            logger.error(f"Regulation query failed: {e}", exc_info=True)
            return RegulationResult(
                regulations=[],
                query=query,
                total_found=0
            )

    def _fallback_answer(self, query: RegulationQuery, regulations: List[Regulation]) -> str:
        """Generate a minimal, deterministic answer when no LLM is configured."""
        top = regulations[: min(3, len(regulations))]
        lines = [
            "LLM synthesis is not configured. Showing the most relevant regulations found:",
            "",
        ]
        for i, reg in enumerate(top, 1):
            snippet = (reg.summary or reg.content or "").strip().replace("\n", " ")
            snippet = snippet[:220] + ("..." if len(snippet) > 220 else "")
            lines.append(f"{i}. {reg.title} ({reg.type.value}, {reg.jurisdiction})")
            if snippet:
                lines.append(f"   {snippet}")
        return "\n".join(lines)
    
    def _search_regulations(self, query: RegulationQuery) -> List[Regulation]:
        """
        Search for relevant regulations.
        
        Args:
            query: Query parameters
            
        Returns:
            List of relevant regulations
        """
        # Build filters. Avoid turning "location" into a hard DB filter: we want
        # semantic recall first, and then do an application-level applicability
        # check (especially when user passes "national"/"Israel").
        filters: dict[str, Any] = {}
        if query.regulation_type:
            filters["type"] = query.regulation_type
        
        regulations = self._regulation_repo.search(
            query=query.query_text,
            filters=filters if filters else None,
            limit=query.max_results,
        )
        
        # Optional post-filter for location applicability (skip for "national").
        if query.location and regulations:
            loc = query.location.strip().lower()
            if loc and loc not in {"national", "israel", "ישראל", "ארצי", "ארצית"}:
                regulations = [r for r in regulations if r.applies_to_location(query.location)]
        
        return regulations
    
    def _synthesize_answer(
        self, 
        query: RegulationQuery, 
        regulations: List[Regulation]
    ) -> str:
        """
        Synthesize answer from regulations using LLM.
        
        Args:
            query: Original query
            regulations: Relevant regulations found
            
        Returns:
            Synthesized answer
        """
        if not self._llm:
            return ""
        
        try:
            # Prepare context from regulations
            context = self._prepare_context(regulations)
            
            # Generate answer
            answer = self._llm.generate_answer(
                question=query.query_text,
                context=context
            )
            
            return answer
        
        except Exception as e:
            logger.error(f"Answer synthesis failed: {e}")
            return ""
    
    def _prepare_context(self, regulations: List[Regulation]) -> str:
        """
        Prepare regulation context for LLM.
        
        Args:
            regulations: List of regulations
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, reg in enumerate(regulations, 1):
            context_parts.append(f"""
Regulation {i}: {reg.title}
Type: {reg.type.value}
Jurisdiction: {reg.jurisdiction}
{reg.summary if reg.summary else reg.content[:500]}
""")
        
        return "\n---\n".join(context_parts)
    
    def get_tama_info(self, tama_number: str) -> List[Regulation]:
        """
        Get information about a specific TAMA plan.
        
        Args:
            tama_number: TAMA number (e.g., "35", "TAMA 35")
            
        Returns:
            List of TAMA-related regulations
        """
        # Normalize TAMA number
        tama_query = f"TAMA {tama_number}" if not tama_number.upper().startswith('TAMA') else tama_number
        
        # Search for TAMA regulations
        regulations = self._regulation_repo.search(
            query=tama_query,
            filters={'type': 'tama'},
            limit=5
        )
        
        return regulations
    
    def get_regulations_for_location(
        self, 
        location: str, 
        limit: int = 10
    ) -> List[Regulation]:
        """
        Get all regulations applicable to a location.
        
        Args:
            location: City or region name
            limit: Maximum results
            
        Returns:
            List of applicable regulations
        """
        return self._regulation_repo.get_applicable_to_location(
            location=location,
            limit=limit
        )
