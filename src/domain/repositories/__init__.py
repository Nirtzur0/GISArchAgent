"""Repository interfaces - Domain layer abstractions.

These interfaces define what data access operations are needed,
without specifying how they are implemented. This follows the
Dependency Inversion Principle - the domain depends on abstractions,
not concrete implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from src.domain.entities.plan import Plan
from src.domain.entities.regulation import Regulation


class IPlanRepository(ABC):
    """
    Interface for plan data access.

    Implementations might include:
    - iPlan ArcGIS REST API client
    - Local file system cache
    - Database storage
    """

    @abstractmethod
    def get_by_id(self, plan_id: str) -> Optional[Plan]:
        """
        Retrieve a plan by its unique identifier.

        Args:
            plan_id: Unique plan identifier

        Returns:
            Plan if found, None otherwise
        """
        pass

    @abstractmethod
    def search_by_location(self, location: str, limit: int = 10) -> List[Plan]:
        """
        Search for plans in a specific location.

        Args:
            location: City, region, or address
            limit: Maximum number of results

        Returns:
            List of matching plans
        """
        pass

    @abstractmethod
    def search_by_keyword(self, keyword: str, limit: int = 10) -> List[Plan]:
        """
        Search for plans by keyword.

        Args:
            keyword: Search term
            limit: Maximum number of results

        Returns:
            List of matching plans
        """
        pass

    @abstractmethod
    def search_by_status(
        self, status: str, location: Optional[str] = None, limit: int = 10
    ) -> List[Plan]:
        """
        Search for plans by approval status.

        Args:
            status: Plan status (approved, pending, etc.)
            location: Optional location filter
            limit: Maximum number of results

        Returns:
            List of matching plans
        """
        pass

    @abstractmethod
    def get_plan_image(self, plan_id: str) -> Optional[bytes]:
        """
        Retrieve map image for a plan.

        Args:
            plan_id: Unique plan identifier

        Returns:
            Image bytes (PNG format) if available, None otherwise
        """
        pass


class IRegulationRepository(ABC):
    """
    Interface for regulation data access.

    Implementations might include:
    - Vector database (ChromaDB, Pinecone)
    - Full-text search engine (Elasticsearch)
    - SQL database with embeddings
    """

    @abstractmethod
    def search(
        self, query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 10
    ) -> List[Regulation]:
        """
        Semantic search for regulations.

        Args:
            query: Natural language query
            filters: Optional filters (type, location, date range)
            limit: Maximum number of results

        Returns:
            List of relevant regulations
        """
        pass

    @abstractmethod
    def get_by_id(self, regulation_id: str) -> Optional[Regulation]:
        """
        Retrieve a regulation by ID.

        Args:
            regulation_id: Unique regulation identifier

        Returns:
            Regulation if found, None otherwise
        """
        pass

    @abstractmethod
    def get_by_type(self, regulation_type: str, limit: int = 10) -> List[Regulation]:
        """
        Get regulations by type.

        Args:
            regulation_type: Type of regulation (TAMA, district, local, etc.)
            limit: Maximum number of results

        Returns:
            List of regulations of specified type
        """
        pass

    @abstractmethod
    def get_applicable_to_location(
        self, location: str, limit: int = 10
    ) -> List[Regulation]:
        """
        Get regulations applicable to a location.

        Args:
            location: City or region name
            limit: Maximum number of results

        Returns:
            List of applicable regulations
        """
        pass

    @abstractmethod
    def add_regulation(self, regulation: Regulation) -> bool:
        """
        Add a new regulation to the repository.

        Args:
            regulation: Regulation entity to add

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get repository statistics.

        Returns:
            Dictionary with stats (count, types, etc.)
        """
        pass
