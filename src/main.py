"""Main application entry point."""

import asyncio
import logging
from pathlib import Path

from src.config import settings
from src.vectorstore import VectorStoreManager
from src.agents import ArchitectureAgent

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class GISArchAgent:
    """Main application class for the GIS Architecture Agent."""
    
    def __init__(self):
        """Initialize the application."""
        logger.info("Initializing GIS Architecture Agent...")
        
        # Initialize vector store
        self.vectorstore = VectorStoreManager(collection_name="iplan_regulations")
        
        # Initialize agent
        self.agent = ArchitectureAgent(self.vectorstore)
        
        logger.info("Application initialized successfully")
    
    def query(self, question: str) -> str:
        """Query the agent.
        
        Args:
            question: User's question
            
        Returns:
            Agent's response
        """
        return self.agent.query(question)
    
    async def aquery(self, question: str) -> str:
        """Async query to the agent.
        
        Args:
            question: User's question
            
        Returns:
            Agent's response
        """
        return await self.agent.aquery(question)
    
    def get_stats(self) -> dict:
        """Get application statistics.
        
        Returns:
            Dictionary with statistics
        """
        return self.vectorstore.get_collection_stats()


def main():
    """Main entry point."""
    print("\n" + "="*60)
    print("GIS ARCHITECTURE AGENT")
    print("Israeli Planning Regulations Assistant")
    print("="*60 + "\n")
    
    # Initialize application
    app = GISArchAgent()
    
    # Show stats
    stats = app.get_stats()
    print(f"📊 Vector Store: {stats['collection_name']}")
    print(f"📚 Documents: {stats['document_count']}")
    print("\n" + "="*60 + "\n")
    
    # Example queries
    example_questions = [
        "What are the main provisions of TAMA 35?",
        "What are the parking requirements for residential buildings?",
        "How tall can a building be in Tel Aviv residential zones?",
    ]
    
    print("Example questions you can ask:")
    for i, q in enumerate(example_questions, 1):
        print(f"{i}. {q}")
    
    print("\n" + "="*60 + "\n")
    print("Ready to answer questions about Israeli planning regulations!")
    print("(Use the CLI tool or import this module to start querying)\n")


if __name__ == "__main__":
    main()
