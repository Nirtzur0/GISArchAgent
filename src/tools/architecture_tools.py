"""Tools for the architecture agent to query regulations and plans."""

from typing import Optional, List, Dict, Any
import logging
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from io import BytesIO
from PIL import Image

from src.vectorstore import VectorStoreManager
from src.scrapers import IPlanScraper
from src.scrapers.realtime_fetcher import get_fetcher
from src.vision import get_vision_analyzer

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
    """Tools for the architecture agent with real-time iPlan data fetching and vision analysis."""
    
    def __init__(self, vectorstore: VectorStoreManager):
        """Initialize tools with vector store access.
        
        Args:
            vectorstore: Vector store manager instance
        """
        self.vectorstore = vectorstore
        self.scraper = None
        self.realtime_fetcher = get_fetcher()  # Real-time data fetcher
        self.vision_analyzer = get_vision_analyzer()  # Vision analyzer for plan images
    
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
                    status: Optional[str] = None,
                    include_vision_analysis: bool = True) -> str:
        """Search for planning schemes with automatic vision analysis of plan images.
        
        Args:
            plan_id: Specific plan ID
            location: Location to search
            status: Plan status filter
            include_vision_analysis: Whether to analyze plan images with AI (default: True)
            
        Returns:
            Formatted string with plans and their visual analysis
        """
        logger.info(f"Searching plans: ID={plan_id}, location={location}, status={status}")
        
        # Try real-time fetch from iPlan with images
        realtime_results = []
        try:
            if plan_id:
                # Get plan with image
                result = self.realtime_fetcher.get_plan_with_image('planning', plan_id)
                if result:
                    realtime_results = [result]
            elif location:
                # Get plans by location (will need to fetch images separately)
                plans = self.realtime_fetcher.get_plans_by_location(location)
                # For each plan, try to get its image
                for plan in plans[:3]:  # Limit to 3 plans to avoid too many API calls
                    plan_num = plan.get('attributes', {}).get('PLAN_NUMBER') or plan.get('attributes', {}).get('PLAN_ID')
                    if plan_num:
                        plan_with_image = self.realtime_fetcher.get_plan_with_image('planning', str(plan_num))
                        if plan_with_image:
                            realtime_results.append(plan_with_image)
        except Exception as e:
            logger.warning(f"Real-time fetch failed, falling back to vector store: {e}")
        
        # Build search query for vector store fallback
        query_parts = []
        if plan_id:
            query_parts.append(f"plan {plan_id}")
        if location:
            query_parts.append(location)
        if status:
            query_parts.append(status)
        
        query = " ".join(query_parts) if query_parts else "planning schemes"
        
        # Search vector store as fallback or supplement
        filter_dict = {}
        if status:
            filter_dict["status"] = status
        if location:
            filter_dict["location"] = location
        
        results = self.vectorstore.similarity_search_with_score(
            query,
            k=5,
            filter=filter_dict if filter_dict else None
        )
        
        # Format results with vision analysis
        formatted = "**Relevant Plans:**\n\n"
        
        if realtime_results:
            formatted += "📡 **Live Data from iPlan with Visual Analysis:**\n\n"
            for i, result in enumerate(realtime_results, 1):
                # Plan data
                plan_data = result.get('plan_data', {})
                formatted += f"{i}. **{plan_data.get('PLAN_NAME', plan_data.get('PL_NAME_HEB', 'Plan'))}**\n"
                formatted += f"   Plan ID: {plan_data.get('PLAN_NUMBER', plan_data.get('PLAN_ID', 'N/A'))}\n"
                formatted += f"   Location: {plan_data.get('CITY_NAME', plan_data.get('SETTLEMENT', 'N/A'))}\n"
                formatted += f"   Status: {plan_data.get('PLAN_STATUS', 'N/A')}\n"
                
                # Vision analysis if image available
                if result.get('has_image') and include_vision_analysis:
                    try:
                        image_bytes = result.get('image_bytes')
                        image = Image.open(BytesIO(image_bytes))
                        
                        # Analyze with vision AI
                        analysis = self.vision_analyzer.analyze_plan_image(
                            image,
                            question="Describe this planning map. What are the key features, zones, and land use designations visible?"
                        )
                        
                        formatted += f"\n   🎨 **Visual Analysis:**\n"
                        formatted += f"   {analysis['analysis'][:500]}...\n"
                        
                        if analysis.get('ocr_text'):
                            formatted += f"   📝 **Text Found:** {len(analysis['ocr_text'].split())} words extracted\n"
                        
                        formatted += f"   💰 **Cost:** ~{analysis.get('tokens_used', 0)} tokens\n"
                        
                    except Exception as e:
                        logger.error(f"Vision analysis failed for plan {i}: {e}")
                        formatted += f"   ⚠️ Visual analysis unavailable\n"
                
                formatted += "\n"
        
        if results:
            if realtime_results:
                formatted += "\n💾 **Cached Regulations:**\n\n"
            for i, (doc, score) in enumerate(results, 1):
                formatted += f"{i}. **{doc.metadata.get('plan_id', 'Plan')}**\n"
                formatted += f"   Location: {doc.metadata.get('location', 'N/A')}\n"
                formatted += f"   Status: {doc.metadata.get('status', 'N/A')}\n"
                formatted += f"   {doc.page_content[:300]}...\n\n"
        
        if not realtime_results and not results:
            return "No relevant plans found in database or iPlan system."
        
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
        """Get information about a TAMA (National Outline Plan) with real-time data.
        
        Args:
            tama_number: TAMA number (e.g., "35", "38")
            
        Returns:
            TAMA information and provisions
        """
        logger.info(f"Getting TAMA info: {tama_number}")
        
        # Clean TAMA number
        tama_clean = tama_number.replace("TAMA", "").replace("תמא", "").strip()
        
        # Try real-time fetch first
        realtime_results = []
        try:
            realtime_results = self.realtime_fetcher.get_tama_plans(tama_clean)
            logger.info(f"Real-time fetch returned {len(realtime_results)} results")
        except Exception as e:
            logger.warning(f"Real-time TAMA fetch failed: {e}")
        
        # Search vector store
        query = f"TAMA {tama_clean} תמא provisions requirements"
        results = self.vectorstore.similarity_search(query, k=3)
        
        formatted = f"**TAMA {tama_clean} Information:**\n\n"
        
        # Add real-time data if available
        if realtime_results:
            formatted += "📡 **Live iPlan Data:**\n\n"
            for i, result in enumerate(realtime_results[:3], 1):
                attrs = result.get('attributes', {})
                formatted += f"{i}. **{attrs.get('TAMA_NAME', attrs.get('PLAN_NAME', f'TAMA {tama_clean}'))}**\n"
                formatted += f"   Number: {attrs.get('TAMA_NUMBER', attrs.get('PLAN_NUMBER', tama_clean))}\n"
                formatted += f"   Status: {attrs.get('PLAN_STATUS', 'N/A')}\n"
                formatted += f"   Service: {result.get('_service', 'N/A')}\n\n"
        
        # Add cached data
        if results:
            if realtime_results:
                formatted += "\n💾 **Detailed Regulations:**\n\n"
            for doc in results:
                formatted += f"{doc.page_content}\n\n"
        
        if not realtime_results and not results:
            return f"No information found for TAMA {tama_clean}. It may not be in the database yet."
        
        return formatted
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
    
    def get_tools(self) -> List:
        """Get all tools as LangChain tool functions decorated with @tool.
        
        Returns:
            List of tool functions
        """
        @tool
        def search_regulations(query: str) -> str:
            """Search for building regulations, zoning laws, and planning requirements.
            
            Args:
                query: Search query describing what regulations you need
            
            Returns:
                String with relevant regulations
            """
            return self.search_regulations(query)
        
        @tool
        def search_plans(location: str) -> str:
            """Search for planning schemes, proposals, and approved plans.
            
            Args:
                location: Location or plan ID to search for
            
            Returns:
                String with relevant plans
            """
            return self.search_plans(location=location)
        
        @tool
        def analyze_zoning(location: str) -> str:
            """Analyze zoning requirements for a specific location.
            
            Args:
                location: Location name to analyze
            
            Returns:
                String with zoning information
            """
            return self.analyze_zoning(location)
        
        @tool
        def get_tama_info(tama_number: str) -> str:
            """Get information about a specific TAMA (National Outline Plan).
            
            Args:
                tama_number: TAMA plan number (e.g., 'TAMA 35', '35')
            
            Returns:
                String with TAMA information
            """
            return self.get_tama_info(tama_number)
        
        @tool
        def analyze_plan_image(image_path_or_url: str, question: str = "") -> str:
            """Analyze an architectural plan image using AI vision to extract information.
            Use this when the user provides an image or asks about visual aspects of a plan.
            
            Args:
                image_path_or_url: Path to local image file or URL to online image
                question: Specific question about the plan image (optional)
            
            Returns:
                String with visual analysis of the plan including dimensions, labels, and features
            """
            return self.analyze_plan_visual(image_path_or_url, question)
        
        return [
            search_regulations,
            search_plans,
            analyze_zoning,
            get_tama_info,
            analyze_plan_image,
        ]
    
    def analyze_plan_visual(self, image_source: str, question: str = "") -> str:
        """Analyze a plan image using vision language model.
        
        Args:
            image_source: Path or URL to plan image
            question: Optional specific question about the image
        
        Returns:
            Formatted analysis string
        """
        logger.info(f"Analyzing plan image: {image_source}, question: {question}")
        
        try:
            if question:
                result = self.vision_analyzer.ask_about_plan(image_source, question)
                return f"**Visual Analysis Answer:**\n\n{result}"
            else:
                result = self.vision_analyzer.analyze_plan_image(
                    image_path=image_source if not image_source.startswith('http') else None,
                    image_url=image_source if image_source.startswith('http') else None
                )
                
                formatted = "**Plan Image Analysis:**\n\n"
                formatted += f"{result['analysis']}\n\n"
                
                if result.get('ocr_text'):
                    formatted += f"**Text Extracted:**\n{result['ocr_text'][:300]}...\n\n"
                
                formatted += f"_Analysis cached for future queries (saved ~{result['estimated_tokens']} tokens)_"
                
                return formatted
                
        except Exception as e:
            logger.error(f"Error analyzing plan image: {e}")
            return f"Error analyzing image: {str(e)}. Please ensure the image path/URL is valid."

