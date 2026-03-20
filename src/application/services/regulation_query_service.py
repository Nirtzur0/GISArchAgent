"""
Regulation Query Service - Natural language queries about regulations.

This service handles queries about planning regulations, zoning requirements,
and procedural questions using semantic search and LLM synthesis.
"""

import logging
from typing import Optional, List, Any
from datetime import datetime
from time import perf_counter
from uuid import uuid4

from src.domain.repositories import IRegulationRepository
from src.domain.entities.regulation import Regulation
from src.application.dtos import RegulationQuery, RegulationResult
from src.telemetry import emit_observability_event

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
        llm_service: Optional[Any] = None,
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
        request_id = query.request_id or uuid4().hex
        started_at = perf_counter()
        degraded_reasons: list[str] = []
        logger.info("Executing regulation query")
        emit_observability_event(
            logger,
            component="RegulationQueryService",
            operation="regulation_query",
            request_id=request_id,
            outcome="start",
            query_length=len(query.query_text or ""),
            max_results=query.max_results,
            has_location=bool(query.location),
            has_type_filter=bool(query.regulation_type),
        )

        try:
            # Search for relevant regulations
            regulations = self._search_regulations(query)

            # Generate answer using LLM if available
            answer: Optional[str] = None
            answer_status = "no_results"
            answer_warning: Optional[str] = None
            if regulations:
                if self._llm:
                    answer = self._synthesize_answer(query, regulations)
                    if not answer:
                        degraded_reasons.append("llm_synthesis_unavailable")
                        answer_status = "retrieval_only"
                        answer_warning = "LLM synthesis is unavailable. Showing retrieved regulations only."
                        answer = self._build_retrieval_only_answer(
                            query=query, regulations=regulations
                        )
                    else:
                        answer_status = "synthesized"
                else:
                    answer_status = "retrieval_only"
                    answer_warning = "LLM synthesis is unavailable. Showing retrieved regulations only."
                    answer = self._build_retrieval_only_answer(
                        query=query, regulations=regulations
                    )

            duration_ms = round((perf_counter() - started_at) * 1000, 2)
            result = RegulationResult(
                regulations=regulations,
                query=query,
                total_found=len(regulations),
                answer=answer,
                answer_status=answer_status,
                answer_warning=answer_warning,
            )
            emit_observability_event(
                logger,
                component="RegulationQueryService",
                operation="regulation_query",
                request_id=request_id,
                outcome="degraded" if degraded_reasons else "success",
                total_found=result.total_found,
                answer_generated=bool(result.answer),
                llm_enabled=bool(self._llm),
                llm_attempted=bool(self._llm and regulations),
                degraded_reasons=degraded_reasons,
                latency_ms=duration_ms,
            )
            return result

        except Exception as e:
            logger.error(f"Regulation query failed: {e}", exc_info=True)
            duration_ms = round((perf_counter() - started_at) * 1000, 2)
            emit_observability_event(
                logger,
                component="RegulationQueryService",
                operation="regulation_query",
                request_id=request_id,
                outcome="error",
                level=logging.ERROR,
                error_class=type(e).__name__,
                message=str(e),
                latency_ms=duration_ms,
            )
            return RegulationResult(regulations=[], query=query, total_found=0)

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
                regulations = [
                    r for r in regulations if r.applies_to_location(query.location)
                ]

        return regulations

    def _synthesize_answer(
        self, query: RegulationQuery, regulations: List[Regulation]
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
                question=query.query_text, context=context
            )

            # Normalize provider-side failures to an empty string so caller can
            # route to deterministic fallback and emit degraded telemetry.
            if not isinstance(answer, str):
                return ""
            normalized = answer.strip()
            if not normalized:
                return ""
            if normalized.startswith("Error processing query:"):
                return ""
            if normalized == "Unable to generate answer from available regulations.":
                return ""
            return normalized

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
            context_parts.append(
                f"""
Regulation {i}: {reg.title}
Type: {reg.type.value}
Jurisdiction: {reg.jurisdiction}
{reg.summary if reg.summary else reg.content[:500]}
"""
            )

        return "\n---\n".join(context_parts)

    def _build_retrieval_only_answer(
        self, query: RegulationQuery, regulations: List[Regulation]
    ) -> str:
        """
        Build a deterministic fallback answer when LLM synthesis is unavailable.

        This keeps the response useful for callers and preserves a stable
        degraded-mode contract for tests and API consumers.
        """
        titles = ", ".join(reg.title for reg in regulations[:3])
        summary = f"Matched {len(regulations)} regulation"
        if len(regulations) != 1:
            summary += "s"
        if titles:
            summary += f": {titles}"
        if len(regulations) > 3:
            summary += ", and more"
        return (
            "LLM synthesis is unavailable. Showing retrieved regulations only. "
            f"{summary}. Query: {query.query_text}"
        )

    def get_tama_info(self, tama_number: str) -> List[Regulation]:
        """
        Get information about a specific TAMA plan.

        Args:
            tama_number: TAMA number (e.g., "35", "TAMA 35")

        Returns:
            List of TAMA-related regulations
        """
        # Normalize TAMA number
        tama_query = (
            f"TAMA {tama_number}"
            if not tama_number.upper().startswith("TAMA")
            else tama_number
        )

        # Search for TAMA regulations
        regulations = self._regulation_repo.search(
            query=tama_query, filters={"type": "tama"}, limit=5
        )

        return regulations

    def get_regulations_for_location(
        self, location: str, limit: int = 10
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
            location=location, limit=limit
        )
