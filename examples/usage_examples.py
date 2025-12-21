"""
Example usage of the GIS Architecture Agent.

This script demonstrates various ways to use the system.
"""

import asyncio
import logging
from pathlib import Path

from src.main import GISArchAgent
from src.vectorstore import VectorStoreManager
from src.local_projects import LocalProjectManager, HybridSearchManager
from src.tools import ArchitectureTools

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def example_basic_query():
    """Example 1: Basic query about regulations."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Regulation Query")
    print("="*60 + "\n")
    
    # Initialize the agent
    app = GISArchAgent()
    
    # Ask a question
    question = "What are the main provisions of TAMA 35?"
    print(f"Question: {question}\n")
    
    response = app.query(question)
    print(f"Answer:\n{response}\n")


def example_specific_requirements():
    """Example 2: Query about specific building requirements."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Specific Building Requirements")
    print("="*60 + "\n")
    
    app = GISArchAgent()
    
    questions = [
        "What parking requirements apply to a 150 sqm residential apartment?",
        "How tall can a building be in Tel Aviv R1 residential zone?",
        "What are the green building requirements for new construction?",
    ]
    
    for question in questions:
        print(f"Q: {question}")
        response = app.query(question)
        print(f"A: {response[:200]}...\n")


async def example_async_query():
    """Example 3: Async query for better performance."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Async Query")
    print("="*60 + "\n")
    
    app = GISArchAgent()
    
    question = "What is the typical plan approval process and timeline?"
    print(f"Question: {question}\n")
    
    response = await app.aquery(question)
    print(f"Answer:\n{response}\n")


def example_direct_vectorstore_search():
    """Example 4: Direct vector store search without agent."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Direct Vector Store Search")
    print("="*60 + "\n")
    
    vectorstore = VectorStoreManager(collection_name="iplan_regulations")
    
    query = "building height restrictions"
    print(f"Searching for: {query}\n")
    
    results = vectorstore.similarity_search_with_score(query, k=3)
    
    for i, (doc, score) in enumerate(results, 1):
        print(f"{i}. Score: {score:.3f}")
        print(f"   Title: {doc.metadata.get('title', 'N/A')}")
        print(f"   Content: {doc.page_content[:150]}...\n")


def example_with_tools():
    """Example 5: Using tools directly."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Using Tools Directly")
    print("="*60 + "\n")
    
    vectorstore = VectorStoreManager(collection_name="iplan_regulations")
    tools = ArchitectureTools(vectorstore)
    
    # Search regulations
    print("Searching regulations about parking...")
    result = tools.search_regulations(
        query="parking requirements residential",
        regulation_type="building_regulation"
    )
    print(result[:300], "...\n")
    
    # Get TAMA info
    print("Getting TAMA 35 information...")
    result = tools.get_tama_info("35")
    print(result[:300], "...\n")
    
    # Analyze zoning
    print("Analyzing zoning for Tel Aviv...")
    result = tools.analyze_zoning("Tel Aviv", "residential")
    print(result[:300], "...\n")


def example_local_projects():
    """Example 6: Working with local projects (requires data)."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Local Projects Integration")
    print("="*60 + "\n")
    
    # Initialize local project manager
    manager = LocalProjectManager()
    
    # Create a sample project directory structure
    sample_project_dir = Path("./data/local_projects/sample_project")
    sample_project_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a sample project document
    sample_doc = sample_project_dir / "project_summary.txt"
    sample_doc.write_text("""
    Project: Residential Tower - Tel Aviv
    Location: Rothschild Boulevard
    
    Project Details:
    - 15 story residential building
    - 45 apartments (average 120 sqm)
    - Commercial ground floor
    - 2 underground parking levels (60 spaces)
    - Green roof and solar panels
    
    Approvals:
    - Building permit approved: March 2024
    - Variance granted for height (from 12 to 15 stories)
    - TAMA 35 compliance certified
    
    Key Challenges:
    - Parking variance required due to lot size
    - Height variance approved based on street width
    - Underground construction required archaeological survey
    """)
    
    print(f"Created sample project at: {sample_project_dir}\n")
    
    # Ingest the project
    print("Ingesting project...")
    count = manager.ingest_project_directory(sample_project_dir)
    print(f"Ingested {count} document chunks\n")
    
    # Search local projects
    print("Searching local projects for 'parking variance'...")
    results = manager.search_local_projects(
        query="parking variance height",
        k=2
    )
    
    for i, doc in enumerate(results, 1):
        print(f"{i}. Project: {doc.metadata.get('project_name', 'N/A')}")
        print(f"   Content: {doc.page_content[:200]}...\n")


def example_hybrid_search():
    """Example 7: Hybrid search across regulations and projects."""
    print("\n" + "="*60)
    print("EXAMPLE 7: Hybrid Search")
    print("="*60 + "\n")
    
    hybrid = HybridSearchManager()
    
    query = "parking requirements residential buildings"
    print(f"Searching both regulations and projects for: {query}\n")
    
    results = hybrid.hybrid_search(query, k=2)
    
    if "regulations" in results:
        print("From Regulations:")
        for doc in results["regulations"]:
            print(f"  - {doc.metadata.get('title', 'N/A')}")
            print(f"    {doc.page_content[:150]}...\n")
    
    if "local_projects" in results:
        print("From Local Projects:")
        for doc in results["local_projects"]:
            print(f"  - {doc.metadata.get('project_name', 'N/A')}")
            print(f"    {doc.page_content[:150]}...\n")


def example_complex_query():
    """Example 8: Complex multi-step query."""
    print("\n" + "="*60)
    print("EXAMPLE 8: Complex Query")
    print("="*60 + "\n")
    
    app = GISArchAgent()
    
    question = """
    I'm planning a 14-story residential building in Tel Aviv with 50 apartments.
    Each apartment is about 110 sqm. The plot is 1000 sqm in an R2 zone.
    
    What are the key regulations I need to consider regarding:
    1. Building height and setbacks
    2. Parking requirements
    3. Green building standards
    4. Any relevant TAMA plans that might apply
    """
    
    print(f"Complex Question:\n{question}\n")
    print("Processing (this may take 30-60 seconds)...\n")
    
    response = app.query(question)
    print(f"Answer:\n{response}\n")


def show_statistics():
    """Show system statistics."""
    print("\n" + "="*60)
    print("SYSTEM STATISTICS")
    print("="*60 + "\n")
    
    app = GISArchAgent()
    stats = app.get_stats()
    
    print(f"Collection: {stats['collection_name']}")
    print(f"Document Count: {stats['document_count']}")
    print(f"Storage Location: {stats['persist_directory']}")
    print()


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("GIS ARCHITECTURE AGENT - EXAMPLE USAGE")
    print("="*70)
    
    # Show statistics first
    show_statistics()
    
    # Run examples
    examples = [
        ("Basic Query", example_basic_query),
        ("Specific Requirements", example_specific_requirements),
        ("Direct Vector Search", example_direct_vectorstore_search),
        ("Using Tools", example_with_tools),
        ("Local Projects", example_local_projects),
        ("Hybrid Search", example_hybrid_search),
    ]
    
    print("Available examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")
    print(f"{len(examples) + 1}. Async Query")
    print(f"{len(examples) + 2}. Complex Query")
    print("0. Run all examples")
    
    choice = input("\nEnter example number to run (or 0 for all): ")
    
    try:
        choice = int(choice)
        
        if choice == 0:
            # Run all examples
            for name, func in examples:
                print(f"\n\nRunning: {name}")
                func()
            
            # Run async examples
            print("\n\nRunning: Async Query")
            asyncio.run(example_async_query())
            
            print("\n\nRunning: Complex Query")
            example_complex_query()
            
        elif 1 <= choice <= len(examples):
            examples[choice - 1][1]()
            
        elif choice == len(examples) + 1:
            asyncio.run(example_async_query())
            
        elif choice == len(examples) + 2:
            example_complex_query()
            
        else:
            print("Invalid choice")
            
    except ValueError:
        print("Invalid input")
    
    print("\n" + "="*70)
    print("Examples complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
