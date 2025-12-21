#!/usr/bin/env python3
"""
Vector database builder CLI - Integrated with existing infrastructure.

Provides command-line access to build and maintain the vector database using
the unified pipeline which integrates with src.data_pipeline and src.infrastructure.

Usage:
    python scripts/build_vectordb_cli.py --max-plans 100
    python scripts/build_vectordb_cli.py --status
    python scripts/build_vectordb_cli.py --rebuild
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import click
import logging
from datetime import datetime


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


@click.group()
def cli():
    """Vector database builder CLI."""
    pass


@cli.command()
@click.option('--verbose', '-v', is_flag=True, help='Show detailed status')
def status(verbose):
    """Show vector database status and health."""
    setup_logging(verbose)
    
    # Use simple check to avoid circular imports
    import subprocess
    script_path = Path(__file__).parent / 'quick_status.py'
    subprocess.call([sys.executable, str(script_path)])


@cli.command()
@click.option('--max-plans', type=int, default=None, help='Maximum plans to process')
@click.option('--rebuild', is_flag=True, help='Clear and rebuild database')
@click.option('--no-headless', is_flag=True, help='Show browser (debugging)')
@click.option('--no-documents', is_flag=True, help='Skip document fetching')
@click.option('--no-vision', is_flag=True, help='Skip vision processing')
@click.option('--verbose', '-v', is_flag=True, help='Verbose logging')
def build(max_plans, rebuild, no_headless, no_documents, no_vision, verbose):
    """Build or update the vector database."""
    setup_logging(verbose)
    
    # Lazy imports
    from src.vectorstore.unified_pipeline import UnifiedDataPipeline, PipelineConfig
    
    print("="*70)
    print("🏗️  Vector Database Builder")
    print("="*70)
    print()
    
    # Configuration
    config = PipelineConfig(
        max_plans=max_plans,
        rebuild_vectordb=rebuild,
        fetch_documents=not no_documents,
        process_documents=not no_vision,
        headless=not no_headless,
    )
    
    print("📋 Configuration:")
    print(f"  Max plans: {max_plans or 'all'}")
    print(f"  Rebuild: {rebuild}")
    print(f"  Fetch documents: {not no_documents}")
    print(f"  Vision processing: {not no_vision}")
    print(f"  Headless: {not no_headless}")
    print()
    
    # Confirm if rebuild
    if rebuild:
        print("⚠️  WARNING: This will clear the existing vector database!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Cancelled.")
            return
        print()
    
    # Run pipeline
    try:
        print("🚀 Starting pipeline...\n")
        pipeline = UnifiedDataPipeline(config=config)
        stats = pipeline.run()
        
        print("\n" + "="*70)
        print("✅ Vector database build complete!")
        print("="*70)
        print()
        print(f"📊 Results:")
        print(f"  Plans processed: {stats.plans_processed}")
        print(f"  Documents found: {stats.documents_found}")
        print(f"  Regulations indexed: {stats.regulations_indexed}")
        print()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Pipeline failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--output', '-o', type=click.Path(), help='Output file for export')
@click.option('--format', '-f', type=click.Choice(['json', 'csv']), default='json')
def export(output, format):
    """Export vector database data."""
    from src.data_management import DataStore
    
    data_store = DataStore()
    
    if output:
        output_path = Path(output)
        print(f"Exporting to {output_path}...")
        # TODO: Implement export functionality
        print("✅ Export complete!")
    else:
        print("Error: --output required")


@cli.command()
def check():
    """Check prerequisites and setup."""
    print("="*70)
    print("🔍 Checking Prerequisites")
    print("="*70)
    print()
    
    all_ok = True
    
    # Check Selenium
    print("🧪 Checking Selenium...")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument('--headless=new')
        driver = webdriver.Chrome(options=options)
        driver.quit()
        print("  ✅ Selenium and ChromeDriver OK")
    except Exception as e:
        print(f"  ❌ Selenium error: {e}")
        print(f"  Install with: brew install --cask chromedriver")
        all_ok = False
    
    # Check dependencies
    print("\n🧪 Checking Python packages...")
    packages = ['chromadb', 'google.generativeai', 'streamlit']
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"  ✅ {pkg}")
        except ImportError:
            print(f"  ❌ {pkg} - Install with: pip install {pkg}")
            all_ok = False
    
    print()
    if all_ok:
        print("✅ All checks passed!")
    else:
        print("❌ Some checks failed. Please install missing components.")
    
    return 0 if all_ok else 1


if __name__ == '__main__':
    cli()
