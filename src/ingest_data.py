"""Data ingestion pipeline for loading iPlan data into vector store."""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict
import json

from langchain.schema import Document

from src.config import settings
from src.scrapers import IPlanScraper
from src.vectorstore import VectorStoreManager

logger = logging.getLogger(__name__)


class DataIngestionPipeline:
    """Pipeline for ingesting iPlan data into the vector store."""
    
    def __init__(self):
        """Initialize the ingestion pipeline."""
        self.vectorstore = VectorStoreManager(collection_name="iplan_regulations")
        self.data_dir = Path("./data")
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        
        # Create directories
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    async def scrape_iplan_data(self) -> Dict[str, List]:
        """Scrape data from the iPlan system.
        
        Returns:
            Dictionary with scraped data
        """
        logger.info("Starting iPlan data scraping...")
        
        data = {
            "layers": [],
            "plans": [],
            "regulations": []
        }
        
        async with IPlanScraper() as scraper:
            # Get planning layers
            layers = await scraper.get_planning_layers()
            data["layers"] = layers
            
            logger.info(f"Scraped {len(layers)} layers")
            
            # Save raw data
            raw_file = self.raw_dir / "iplan_layers.json"
            with open(raw_file, 'w', encoding='utf-8') as f:
                json.dump(layers, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved raw data to {raw_file}")
        
        return data
    
    def load_sample_regulations(self) -> List[Document]:
        """Load sample Israeli planning regulations.
        
        This is a placeholder that should be replaced with actual scraped data.
        
        Returns:
            List of Document objects
        """
        logger.info("Loading sample regulations...")
        
        sample_docs = [
            Document(
                page_content="""
                TAMA 35 - National Outline Plan for Building Construction and Urban Renewal
                
                Purpose: Encourage urban renewal and strengthen buildings against earthquakes.
                
                Key Provisions:
                - Allows adding 2-3 floors to existing residential buildings
                - Provides building rights incentives for strengthening structures
                - Applies to buildings built before 1980
                - Requires agreement from 80% of apartment owners in building
                - Demolition and reconstruction option available
                
                Building Rights:
                - Original building: 100% of existing floor area
                - Additional floors: Up to 30% increase in floor area
                - Balconies and protected spaces: Additional allowances
                
                Applicable Zones: Residential zones in urban areas
                """,
                metadata={
                    "title": "TAMA 35 - Urban Renewal",
                    "type": "national_plan",
                    "plan_id": "TAMA_35",
                    "status": "approved",
                    "source": "iPlan System"
                }
            ),
            Document(
                page_content="""
                TAMA 38 - National Outline Plan for National Infrastructure
                
                Purpose: Planning framework for national infrastructure projects.
                
                Scope:
                - Transportation infrastructure (roads, railways, ports, airports)
                - Energy infrastructure (power plants, transmission lines)
                - Water and sewage systems
                - Communication infrastructure
                
                Planning Process:
                - Streamlined approval process for national projects
                - Coordination between different authorities
                - Environmental impact assessment required
                
                Key Requirements:
                - Public participation in planning stages
                - Alignment with national development goals
                - Consideration of regional and local impacts
                """,
                metadata={
                    "title": "TAMA 38 - National Infrastructure",
                    "type": "national_plan",
                    "plan_id": "TAMA_38",
                    "status": "approved",
                    "source": "iPlan System"
                }
            ),
            Document(
                page_content="""
                Building Height Regulations - Tel Aviv
                
                General Residential Zones (R1):
                - Maximum height: 4 stories (approximately 14 meters)
                - Setback requirements: 3 meters from property line
                - Building coverage: Maximum 40% of plot
                - Floor Area Ratio (FAR): 120%
                
                High-Density Residential (R2):
                - Maximum height: 8 stories (approximately 28 meters)
                - Setback requirements: 4 meters from property line
                - Building coverage: Maximum 50% of plot
                - Floor Area Ratio (FAR): 280%
                
                Commercial Zones (C1):
                - Maximum height: 6 stories (approximately 22 meters)
                - Ground floor: Minimum 4 meters height
                - Setback: 2 meters from property line
                - Building coverage: Maximum 60% of plot
                """,
                metadata={
                    "title": "Building Height Regulations",
                    "type": "zoning",
                    "location": "Tel Aviv",
                    "source": "Local Planning Committee"
                }
            ),
            Document(
                page_content="""
                Parking Requirements - National Building Regulations
                
                Residential Buildings:
                - Apartments up to 100 sqm: 1 parking space per unit
                - Apartments 100-150 sqm: 1.5 parking spaces per unit
                - Apartments over 150 sqm: 2 parking spaces per unit
                - Visitor parking: 0.25 spaces per unit (minimum)
                
                Commercial Uses:
                - Offices: 1 space per 50 sqm of floor area
                - Retail: 1 space per 40 sqm of floor area
                - Restaurants: 1 space per 25 sqm of dining area
                
                Special Provisions:
                - Near public transportation: 20% reduction allowed
                - City centers: Up to 50% reduction with local approval
                - Bicycle parking required: 1 space per 2 parking spaces
                """,
                metadata={
                    "title": "Parking Requirements",
                    "type": "building_regulation",
                    "source": "National Building Law"
                }
            ),
            Document(
                page_content="""
                Green Building Requirements - Planning Policy
                
                Energy Efficiency:
                - All new buildings must meet Standard 5282 (thermal insulation)
                - Solar water heating mandatory for residential buildings
                - Energy-efficient lighting in common areas
                
                Water Conservation:
                - Low-flow fixtures required
                - Rainwater collection recommended for irrigation
                - Graywater systems encouraged
                
                Sustainable Materials:
                - Minimum 20% recycled materials in construction
                - Local materials preferred (within 500km)
                - Low-VOC paints and finishes
                
                Site Planning:
                - Preserve existing trees where possible
                - Minimum 15% of site area for landscaping
                - Permeable surfaces for parking areas
                """,
                metadata={
                    "title": "Green Building Requirements",
                    "type": "building_regulation",
                    "source": "Ministry of Environmental Protection"
                }
            ),
            Document(
                page_content="""
                Plan Approval Process - Standard Procedure
                
                Step 1: Pre-Application Consultation
                - Meet with local planning department
                - Discuss project concept and requirements
                - Identify potential issues
                - Duration: 2-4 weeks
                
                Step 2: Application Submission
                - Complete application forms
                - Architectural drawings and site plans
                - Environmental impact assessment (if required)
                - Engineering reports
                
                Step 3: Public Review Period
                - Plans published for public objections
                - Duration: 60 days
                - Objections must be submitted in writing
                
                Step 4: Planning Committee Review
                - Committee meets monthly
                - Reviews application and objections
                - May request revisions
                
                Step 5: Approval and Appeals
                - Approval granted or denied
                - Appeals can be filed within 30 days
                - Appeals heard by District Committee
                
                Total Timeline: 6-12 months (standard projects)
                """,
                metadata={
                    "title": "Plan Approval Process",
                    "type": "procedure",
                    "source": "Planning and Building Law"
                }
            ),
        ]
        
        return sample_docs
    
    def ingest_documents(self, documents: List[Document]) -> None:
        """Ingest documents into the vector store.
        
        Args:
            documents: List of documents to ingest
        """
        logger.info(f"Ingesting {len(documents)} documents into vector store...")
        
        # Add documents to vector store
        ids = self.vectorstore.add_documents(documents)
        
        logger.info(f"Successfully ingested {len(ids)} document chunks")
    
    async def run_full_pipeline(self) -> None:
        """Run the complete ingestion pipeline."""
        logger.info("Starting full ingestion pipeline...")
        
        # Step 1: Scrape iPlan data
        logger.info("Step 1: Scraping iPlan data...")
        scraped_data = await self.scrape_iplan_data()
        
        # Step 2: Load sample regulations (replace with actual scraped data)
        logger.info("Step 2: Loading sample regulations...")
        sample_docs = self.load_sample_regulations()
        
        # Step 3: Ingest into vector store
        logger.info("Step 3: Ingesting into vector store...")
        self.ingest_documents(sample_docs)
        
        # Step 4: Get statistics
        stats = self.vectorstore.get_collection_stats()
        logger.info(f"Pipeline complete. Stats: {stats}")
        
        print("\n" + "="*60)
        print("DATA INGESTION COMPLETE")
        print("="*60)
        print(f"Documents ingested: {len(sample_docs)}")
        print(f"Vector store: {stats['collection_name']}")
        print(f"Total chunks: {stats['document_count']}")
        print("="*60 + "\n")


async def main():
    """Main function to run data ingestion."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    pipeline = DataIngestionPipeline()
    await pipeline.run_full_pipeline()


if __name__ == "__main__":
    asyncio.run(main())
