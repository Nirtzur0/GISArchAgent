"""Tools for the architecture agent to query regulations and plans."""

from typing import Optional, List, Dict, Any
import logging
from langchain.tools import Tool
from langchain.pydantic_v1 import BaseModel, Field

from src.vectorstore import VectorStoreManager
from src.scrapers import IPlanScraper

logger = logging.getLogger(__name__)


class RegulationSearchInput(BaseModel):
    """Input for regulation search tool."""
    query: str = Field(description="The search query for regulations")
    location: Optional[str] = Field(None, description="Specific location (city/region)")
    regulation_type: Optional[str] = Field(None, description="Type of regulation (e.g., zoning, height, TAMA)")


class PlanSearchInput(BaseModel):
    """Input for plan search tool."""
    plan_id: Optional[str] = Field(None, description="Specific plan ID to search for")
    location: Optional[str] = Field(None, description="Location to search for plans")
    status: Optional[str] = Field(None, description="Plan status (approved, pending, etc.)")


class ArchitectureTools:
    """Tools for the architecture agent."""
    
    def __init__(self, vectorstore: VectorStoreManager):
        """Initialize tools with vector store access.
        
        Args:
            vectorstore: Vector store manager instance
        """
        self.vectorstore = vectorstore
        self.scraper = None
    
    def search_regulations(self, query: str, location: Optional[str] = None, 
                          regulation_type: Optional[str] = None) -> str:
        """Search for relevant regulations and requirements.
        
        Args:
            query: Search query
            location: Specific location to filter by
            regulation_type: Type of regulation to filter by
            
        Returns:
            Formatted string with relevant regulations
        """
        logger.info(f"Searching regulations: {query}")
        
        # Build filter
        filter_dict = {}
        if location:
            filter_dict["location"] = location
        if regulation_type:
            filter_dict["type"] = regulation_type
        
        # Search vector store
        results = self.vectorstore.similarity_search_with_score(
            query,
            k=5,
            filter=filter_dict if filter_dict else None
        )
        
        if not results:
            return "No relevant regulations found for this query."
        
        # Format results
        formatted = "**Relevant Regulations:**\n\n"
        for i, (doc, score) in enumerate(results, 1):
            formatted += f"{i}. **{doc.metadata.get('title', 'Regulation')}**\n"
            formatted += f"   Relevance: {score:.2f}\n"
            formatted += f"   {doc.page_content[:300]}...\n"
            if doc.metadata.get('source'):
                formatted += f"   Source: {doc.metadata['source']}\n"
            formatted += "\n"
        
        return formatted
    
    def search_plans(self, plan_id: Optional[str] = None, 
                    location: Optional[str] = None,
                    status: Optional[str] = None) -> str:
        """Search for planning schemes and proposals.
        
        Args:
            plan_id: Specific plan ID
            plan_id: Location to search
            status: Plan status filter
            
        Returns:
            Formatted string with relevant plans
        """
        logger.info(f"Searching plans: ID={plan_id}, location={location}, status={status}")
        
        # Build search query
        query_parts = []
        if plan_id:
            query_parts.append(f"plan {plan_id}")
        if location:
            query_parts.append(location)
        if status:
            query_parts.append(status)
        
        query = " ".join(query_parts) if query_parts else "planning schemes"
        
        # Build filter
        filter_dict = {}
        if status:
            filter_dict["status"] = status
        if location:
            filter_dict["location"] = location
        
        # Search vector store
        results = self.vectorstore.similarity_search_with_score(
            query,
            k=5,
            filter=filter_dict if filter_dict else None
        )
        
        if not results:
            return "No relevant plans found."
        
        # Format results
        formatted = "**Relevant Plans:**\n\n"
        for i, (doc, score) in enumerate(results, 1):
            formatted += f"{i}. **{doc.metadata.get('plan_id', 'Plan')}**\n"
            formatted += f"   Location: {doc.metadata.get('location', 'N/A')}\n"
            formatted += f"   Status: {doc.metadata.get('status', 'N/A')}\n"
            formatted += f"   {doc.page_content[:300]}...\n\n"
        
        return formatted
    
    def analyze_zoning(self, location: str, building_type: Optional[str] = None) -> str:
        """Analyze zoning requirements for a specific location.
        
        Args:
            location: Location to analyze
            building_type: Type of building (residential, commercial, etc.)
            
        Returns:
            Zoning analysis and requirements
        """
        logger.info(f"Analyzing zoning for: {location}, type: {building_type}")
        
        query = f"zoning requirements {location}"
        if building_type:
            query += f" {building_type}"
        
        results = self.vectorstore.similarity_search(query, k=3)
        
        if not results:
            return f"No zoning information found for {location}."
        
        formatted = f"**Zoning Analysis for {location}:**\n\n"
        for i, doc in enumerate(results, 1):
            formatted += f"{i}. {doc.page_content}\n\n"
        
        return formatted
    
    def get_tama_info(self, tama_number: str) -> str:
        """Get information about a specific TAMA (National Outline Plan).
        
        Args:
            tama_number: TAMA plan number (e.g., "35", "38")
            
        Returns:
            TAMA plan information
        """
        logger.info(f"Getting TAMA info: {tama_number}")
        
        query = f"TAMA {tama_number} תמא"
        
        results = self.vectorstore.similarity_search(query, k=3)
        
        if not results:
            return f"No information found for TAMA {tama_number}."
        
        formatted = f"**TAMA {tama_number} Information:**\n\n"
        for doc in results:
            formatted += f"{doc.page_content}\n\n"
        
        return formatted
    
    def calculate_building_rights(self, plot_size: float, zone_type: str,
                                 location: str) -> str:
        """Calculate potential building rights based on regulations.
        
        Args:
            plot_size: Size of the plot in square meters
            zone_type: Zoning designation
            location: Location of the plot
            
        Returns:
            Calculated building rights and explanation
        """
        logger.info(f"Calculating building rights: {plot_size}sqm, {zone_type}, {location}")
        
        query = f"building rights {zone_type} {location} floor area ratio coverage"
        
        results = self.vectorstore.similarity_search(query, k=3)
        
        if not results:
            return "Unable to calculate building rights. Insufficient regulation data."
        
        formatted = f"**Building Rights Calculation:**\n\n"
        formatted += f"Plot Size: {plot_size} sqm\n"
        formatted += f"Zone: {zone_type}\n"
        formatted += f"Location: {location}\n\n"
        formatted += "**Applicable Regulations:**\n"
        
        for doc in results:
            formatted += f"- {doc.page_content[:200]}...\n"
        
        formatted += "\n*Note: This is an estimate based on available regulations. "
        formatted += "Always verify with local planning authorities.*"
        
        return formatted
    
    def get_tools(self) -> List[Tool]:
        """Get all tools as LangChain Tool objects.
        
        Returns:
            List of Tool objects
        """
        return [
            Tool(
                name="search_regulations",
                func=lambda q: self.search_regulations(q),
                description="Search for building regulations, zoning laws, and planning requirements. "
                           "Input should be a search query describing what regulations you need."
            ),
            Tool(
                name="search_plans",
                func=lambda q: self.search_plans(location=q),
                description="Search for planning schemes, proposals, and approved plans. "
                           "Input should be a location or plan ID."
            ),
            Tool(
                name="analyze_zoning",
                func=lambda q: self.analyze_zoning(q),
                description="Analyze zoning requirements for a specific location. "
                           "Input should be a location name."
            ),
            Tool(
                name="get_tama_info",
                func=self.get_tama_info,
                description="Get information about a specific TAMA (National Outline Plan). "
                           "Input should be the TAMA number (e.g., '35', '38')."
            ),
        ]
