"""
Plan Search Service - Core use case for architecture firms.

This service orchestrates the entire plan search workflow:
1. Search for plans based on query
2. Fetch plan images
3. Analyze images with vision AI
4. Return comprehensive results
"""

import logging
from typing import Optional, Any
from datetime import datetime
from time import perf_counter
from uuid import uuid4

from src.domain.repositories import IPlanRepository
from src.domain.entities.plan import Plan
from src.domain.entities.analysis import VisionAnalysis
from src.application.dtos import PlanSearchQuery, PlanSearchResult, AnalyzedPlan
from src.telemetry import emit_observability_event

logger = logging.getLogger(__name__)


class PlanSearchService:
    """
    Application service for plan search use case.

    This is the primary use case for architecture firms - finding and
    analyzing planning schemes with automatic AI vision analysis.
    """

    def __init__(
        self,
        plan_repository: IPlanRepository,
        vision_service: Optional["GeminiVisionService"] = None,
        cache_service: Optional["FileCacheService"] = None,
    ):
        """
        Initialize service with dependencies.

        Args:
            plan_repository: Repository for plan data access
            vision_service: Optional service for vision analysis
            cache_service: Optional caching service
        """
        self._plan_repo = plan_repository
        self._vision_service = vision_service
        self._cache = cache_service

    def search_plans(self, query: PlanSearchQuery) -> PlanSearchResult:
        """
        Execute plan search with optional vision analysis.

        This is the main entry point for the plan search use case.

        Args:
            query: Search query parameters

        Returns:
            Comprehensive search results with analyzed plans
        """
        start_time = datetime.now()
        started_at = perf_counter()
        request_id = uuid4().hex
        logger.info(f"Executing plan search: {query}")
        emit_observability_event(
            logger,
            component="PlanSearchService",
            operation="plan_search",
            request_id=request_id,
            outcome="start",
            max_results=query.max_results,
            has_plan_id=bool(query.plan_id),
            has_location=bool(query.location),
            has_keyword=bool(query.keyword),
            include_vision_analysis=query.include_vision_analysis,
        )

        try:
            # Step 1: Search for plans
            plans, degraded_reasons = self._execute_search(query)
            logger.info(f"Found {len(plans)} plans")

            # Step 2: Fetch images and analyze
            analyzed_plans = []
            degraded_plan_count = 0
            for plan in plans[: query.max_results]:
                analyzed_plan, plan_degraded_reasons = self._analyze_plan(
                    plan, query.include_vision_analysis
                )
                analyzed_plans.append(analyzed_plan)
                if plan_degraded_reasons:
                    degraded_plan_count += 1
                    degraded_reasons.extend(plan_degraded_reasons)

            # Step 3: Build result
            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            result = PlanSearchResult(
                plans=analyzed_plans,
                query=query,
                total_found=len(plans),
                execution_time_ms=execution_time,
            )
            deduped_reasons = sorted(set(degraded_reasons))
            emit_observability_event(
                logger,
                component="PlanSearchService",
                operation="plan_search",
                request_id=request_id,
                outcome="degraded" if deduped_reasons else "success",
                total_found=result.total_found,
                returned_results=len(result.plans),
                include_vision_analysis=query.include_vision_analysis,
                degraded_reason_count=len(deduped_reasons),
                degraded_reasons=deduped_reasons,
                degraded_plan_count=degraded_plan_count,
                latency_ms=round((perf_counter() - started_at) * 1000, 2),
            )
            return result

        except Exception as e:
            logger.error(f"Plan search failed: {e}", exc_info=True)
            emit_observability_event(
                logger,
                component="PlanSearchService",
                operation="plan_search",
                request_id=request_id,
                outcome="error",
                level=logging.ERROR,
                error_class=type(e).__name__,
                message=str(e),
                latency_ms=round((perf_counter() - started_at) * 1000, 2),
            )
            # Return empty result on error
            return PlanSearchResult(
                plans=[], query=query, total_found=0, execution_time_ms=0.0
            )

    def _execute_search(self, query: PlanSearchQuery) -> tuple[list[Plan], list[str]]:
        """
        Execute the actual search based on query type.

        Args:
            query: Search parameters

        Returns:
            List of matching plans + degraded reasons, if any
        """
        degraded_reasons: list[str] = []

        # Priority: plan_id > location > keyword
        if query.plan_id:
            plan = self._plan_repo.get_by_id(query.plan_id)
            degraded_reasons.extend(
                self._consume_plan_repo_error(default_operation="get_by_id")
            )
            return [plan] if plan else [], degraded_reasons

        elif query.location:
            if query.status:
                # Combined location and status search
                plans = self._plan_repo.search_by_status(
                    status=query.status,
                    location=query.location,
                    limit=query.max_results * 2,  # Fetch more for filtering
                )
                degraded_reasons.extend(
                    self._consume_plan_repo_error(default_operation="search_by_status")
                )
                return plans, degraded_reasons
            else:
                plans = self._plan_repo.search_by_location(
                    location=query.location, limit=query.max_results * 2
                )
                degraded_reasons.extend(
                    self._consume_plan_repo_error(
                        default_operation="search_by_location"
                    )
                )
                return plans, degraded_reasons

        elif query.keyword:
            plans = self._plan_repo.search_by_keyword(
                keyword=query.keyword, limit=query.max_results * 2
            )
            degraded_reasons.extend(
                self._consume_plan_repo_error(default_operation="search_by_keyword")
            )
            return plans, degraded_reasons

        else:
            # No specific query - return empty
            logger.warning("No search criteria provided")
            return [], degraded_reasons

    def _analyze_plan(
        self, plan: Plan, include_vision: bool
    ) -> tuple[AnalyzedPlan, list[str]]:
        """
        Analyze a plan including optional vision analysis.

        Args:
            plan: Plan to analyze
            include_vision: Whether to include vision analysis

        Returns:
            Analyzed plan with vision results if requested + degraded reasons
        """
        image_bytes = None
        vision_analysis = None
        degraded_reasons: list[str] = []

        try:
            # Fetch plan image
            image_bytes = self._plan_repo.get_plan_image(plan.id)
            if include_vision:
                degraded_reasons.extend(
                    self._consume_plan_repo_error(default_operation="get_plan_image")
                )

            if include_vision:
                if not self._vision_service:
                    degraded_reasons.append("vision_service_unavailable")
                elif image_bytes:
                    # Perform vision analysis
                    vision_analysis = self._get_or_create_vision_analysis(
                        plan, image_bytes
                    )
                    if vision_analysis is None:
                        degraded_reasons.append("vision_analysis_unavailable")

        except Exception as e:
            logger.error(f"Failed to analyze plan {plan.id}: {e}")
            degraded_reasons.append("plan_analysis_exception")

        return AnalyzedPlan(
            plan=plan, vision_analysis=vision_analysis, image_bytes=image_bytes
        ), sorted(set(degraded_reasons))

    def _get_or_create_vision_analysis(
        self, plan: Plan, image_bytes: bytes
    ) -> Optional[VisionAnalysis]:
        """
        Get cached vision analysis or create new one.

        Args:
            plan: Plan being analyzed
            image_bytes: Image data

        Returns:
            Vision analysis result or None
        """
        if not self._vision_service:
            return None

        # Check cache first
        if self._cache:
            cache_key = f"vision:{plan.id}"
            cached = self._cache.get(cache_key)
            if cached:
                logger.info(f"Using cached vision analysis for plan {plan.id}")
                try:
                    return VisionAnalysis.from_dict(cached)
                except Exception:
                    # Cache might contain an older schema; ignore and recompute.
                    return None

        # Perform new analysis
        try:
            analysis = self._vision_service.analyze_plan(
                plan_id=plan.id, image_bytes=image_bytes
            )

            # Cache the result
            if self._cache and analysis:
                self._cache.set(
                    key=f"vision:{plan.id}",
                    value=analysis.to_dict(),
                    ttl=86400,  # 24 hours
                )

            return analysis

        except Exception as e:
            logger.error(f"Vision analysis failed for plan {plan.id}: {e}")
            return None

    def _consume_plan_repo_error(self, *, default_operation: str) -> list[str]:
        """
        Consume optional external-boundary error signal from plan repository.

        Repositories can expose a `consume_last_error()` method that returns
        contextual error metadata when they swallow boundary exceptions.
        """
        consume_fn = getattr(self._plan_repo, "consume_last_error", None)
        if not callable(consume_fn):
            return []

        try:
            payload = consume_fn()
        except Exception:
            return [f"iplan_{default_operation}_error_signal_unavailable"]

        if not isinstance(payload, dict) or not payload:
            return []

        operation = str(payload.get("operation") or default_operation).strip()
        if not operation:
            operation = default_operation
        return [f"iplan_{operation}_failed"]

    def get_plan_by_id(self, plan_id: str) -> Optional[Plan]:
        """
        Simple helper to get a plan by ID.

        Args:
            plan_id: Plan identifier

        Returns:
            Plan if found, None otherwise
        """
        return self._plan_repo.get_by_id(plan_id)
