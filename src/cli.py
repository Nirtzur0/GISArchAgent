"""Command-line interface for the GIS Architecture Agent."""

import asyncio
import sys
from typing import Optional

import click

from src.main import GISArchAgent
from src.ingest_data import DataIngestionPipeline


@click.group()
def cli():
    """GIS Architecture Agent - Israeli Planning Regulations Assistant."""
    pass


@cli.command()
def init():
    """Initialize the system and ingest data."""
    click.echo("🚀 Initializing GIS Architecture Agent...")
    click.echo("This will scrape and ingest data from the iPlan system.\n")
    
    async def run_init():
        pipeline = DataIngestionPipeline()
        await pipeline.run_full_pipeline()
    
    asyncio.run(run_init())
    click.echo("\n✅ Initialization complete!")


@cli.command()
@click.argument('question', required=False)
@click.option('--interactive', '-i', is_flag=True, help='Start interactive mode')
def query(question: Optional[str], interactive: bool):
    """Query the agent with a question about planning regulations."""
    app = GISArchAgent()
    
    if interactive or not question:
        # Interactive mode
        click.echo("\n" + "="*60)
        click.echo("GIS ARCHITECTURE AGENT - Interactive Mode")
        click.echo("="*60)
        click.echo("Ask questions about Israeli planning regulations.")
        click.echo("Type 'exit' or 'quit' to end the session.\n")
        
        while True:
            try:
                user_input = click.prompt("\n📋 Your question", type=str)
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    click.echo("\n👋 Goodbye!")
                    break
                
                click.echo("\n🤔 Thinking...\n")
                response = app.query(user_input)
                
                click.echo("="*60)
                click.echo("📝 Answer:")
                click.echo("="*60)
                click.echo(response)
                click.echo("="*60)
                
            except (KeyboardInterrupt, EOFError):
                click.echo("\n\n👋 Goodbye!")
                break
    else:
        # Single query mode
        click.echo(f"\n📋 Question: {question}\n")
        click.echo("🤔 Thinking...\n")
        
        response = app.query(question)
        
        click.echo("="*60)
        click.echo("📝 Answer:")
        click.echo("="*60)
        click.echo(response)
        click.echo("="*60 + "\n")


@cli.command()
def stats():
    """Show statistics about the knowledge base."""
    app = GISArchAgent()
    stats = app.get_stats()
    
    click.echo("\n" + "="*60)
    click.echo("📊 KNOWLEDGE BASE STATISTICS")
    click.echo("="*60)
    click.echo(f"Collection: {stats['collection_name']}")
    click.echo(f"Document Count: {stats['document_count']}")
    click.echo(f"Location: {stats['persist_directory']}")
    click.echo("="*60 + "\n")


@cli.command()
def examples():
    """Show example queries."""
    examples = [
        {
            "question": "What are the main provisions of TAMA 35?",
            "description": "Learn about urban renewal and building strengthening"
        },
        {
            "question": "What are the parking requirements for a 150 sqm apartment?",
            "description": "Check parking regulations for residential units"
        },
        {
            "question": "How tall can I build in Tel Aviv R1 zone?",
            "description": "Find height restrictions for residential zones"
        },
        {
            "question": "What is the plan approval process?",
            "description": "Understand the steps for getting planning approval"
        },
        {
            "question": "What are green building requirements?",
            "description": "Learn about sustainability requirements"
        },
    ]
    
    click.echo("\n" + "="*60)
    click.echo("💡 EXAMPLE QUERIES")
    click.echo("="*60 + "\n")
    
    for i, example in enumerate(examples, 1):
        click.echo(f"{i}. {example['question']}")
        click.echo(f"   → {example['description']}\n")
    
    click.echo("="*60)
    click.echo("Run: python -m src.cli query --interactive")
    click.echo("Or:  python -m src.cli query \"Your question here\"")
    click.echo("="*60 + "\n")


if __name__ == '__main__':
    cli()
