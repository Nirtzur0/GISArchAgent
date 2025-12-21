"""
Plan Search Service - Core use case for architecture firms.

This service orchestrates the entire plan search workflow:
1. Search for plans based on query
2. Fetch plan images
3. Analyze images with vision AI
4. Return comprehensive results
"""

import logging
from typing import Optional
from datetime import datetime
from io import BytesIO
from PIL import Image

from src.domain.repositories import IPlanRepository
from src.domain.entities.plan import Plan
from src.domain.entities.analysis import VisionAnalysis
from src.application.dtos import PlanSearchQuery, PlanSearchResult, AnalyzedPlan

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
        vision_service: Optional['GeminiVisionService'] = None,
        cache_service: Optional['FileCacheService'] = None
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
        logger.info(f"Executing plan search: {query}")
        
        try:
            # Step 1: Search for plans
            plans = self._execute_search(query)
            logger.info(f"Found {len(plans)} plans")
            
            # Step 2: Fetch images and analyze
            analyzed_plans = []
            for plan in plans[:query.max_results]:
                analyzed_plan = self._analyze_plan(plan, query.include_vision_analysis)
                analyzed_plans.append(analyzed_plan)
            
            # Step 3: Build result
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return PlanSearchResult(
                plans=analyzed_plans,
                query=query,
                total_found=len(plans),
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"Plan search failed: {e}", exc_info=True)
            # Return empty result on error
            return PlanSearchResult(
                plans=[],
                query=query,
                total_found=0,
                execution_time_ms=0.0
            )
    
    def _execute_search(self, query: PlanSearchQuery) -> list[Plan]:
        """
        Execute the actual search based on query type.
        
        Args:
            query: Search parameters
            
        Returns:
            List of matching plans
        """
        # Priority: plan_id > location > keyword
        if query.plan_id:
            plan = self._plan_repo.get_by_id(query.plan_id)
            return [plan] if plan else []
        
        elif query.location:
            if query.status:
                # Combined location and status search
                return self._plan_repo.search_by_status(
                    status=query.status,
                    location=query.location,
                    limit=query.max_results * 2  # Fetch more for filtering
                )
            else:
                return self._plan_repo.search_by_location(
                    location=query.location,
                    limit=query.max_results * 2
                )
        
        elif query.keyword:
            return self._plan_repo.search_by_keyword(
                keyword=query.keyword,
                limit=query.max_results * 2
            )
        
        else:
            # No specific query - return empty
            logger.warning("No search criteria provided")
            return []
    
    def _analyze_plan(
        self, 
        plan: Plan, 
        include_vision: bool
    ) -> AnalyzedPlan:
        """
        Analyze a plan including optional vision analysis.
        
        Args:
            plan: Plan to analyze
            include_vision: Whether to include vision analysis
            
        Returns:
            Analyzed plan with vision results if requested
        """
        image_bytes = None
        vision_analysis = None
        
        try:
            # Fetch plan image
            image_bytes = self._plan_repo.get_plan_image(plan.id)
            
            if image_bytes and include_vision and self._vision_service:
                # Perform vision analysis
                vision_analysis = self._get_or_create_vision_analysis(
                    plan, 
                    image_bytes
                )
        
        except Exception as e:
            logger.error(f"Failed to analyze plan {plan.id}: {e}")
        
        return AnalyzedPlan(
            plan=plan,
            vision_analysis=vision_analysis,
            image_bytes=image_bytes
        )
    
    def _get_or_create_vision_analysis(
        self, 
        plan: Plan, 
        image_bytes: bytes
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
                return cached
        
        # Perform new analysis
        try:
            image = Image.open(BytesIO(image_bytes))
            analysis = self._vision_service.analyze_plan(plan, image)
            
            # Cache the result
            if self._cache and analysis:
                self._cache.set(
                    key=f"vision:{plan.id}",
                    value=analysis,
                    ttl=86400  # 24 hours
                )
            
            return analysis
        
        except Exception as e:
            logger.error(f"Vision analysis failed for plan {plan.id}: {e}")
            return None
    
    def get_plan_by_id(self, plan_id: str) -> Optional[Plan]:
        """
        Simple helper to get a plan by ID.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            Plan if found, None otherwise
        """
        return self._plan_repo.get_by_id(plan_id)
