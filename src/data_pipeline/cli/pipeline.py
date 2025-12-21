#!/usr/bin/env python3
"""
Generic Data Pipeline CLI

Command-line interface for managing data ingestion into vector database.
Supports multiple data sources through generic architecture.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data_pipeline import (
    GenericPipeline,
    ConsolePipelineObserver,
    PipelineRegistry,
    VectorDBLoader,
    IPlanDataSource,
    PipelineConfig,
)
from src.infrastructure.services.cache_service import FileCacheService
from src.infrastructure.repositories.chroma_repository import ChromaRegulationRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_pipeline_registry() -> PipelineRegistry:
    """
    Initialize pipeline registry with available sources and loaders.
    
    Returns:
        Configured pipeline registry
    """
    registry = PipelineRegistry()
    
    # Register iPlan data source
    cache = FileCacheService()
    iplan_source = IPlanDataSource(cache=cache)
    registry.register_source("iplan", iplan_source)
    
    # Register vector DB loader
    persist_dir = "data/vectorstore"
    repo = ChromaRegulationRepository(persist_directory=persist_dir)
    loader = VectorDBLoader(repo)
    registry.register_loader("vectordb", loader)
    
    logger.info("Pipeline registry initialized with iPlan source and VectorDB loader")
    return registry


def cmd_run(args):
    """Run data ingestion pipeline."""
    logger.info(f"Running {args.source} → {args.loader} pipeline")
    
    # Setup registry
    registry = setup_pipeline_registry()
    
    # Create pipeline
    pipeline = registry.create_pipeline(
        source_name=args.source,
        loader_name=args.loader,
        observer=ConsolePipelineObserver()
    )
    
    if not pipeline:
        logger.error(f"Failed to create pipeline with source='{args.source}', loader='{args.loader}'")
        return 1
    
    # Configure pipeline
    config = PipelineConfig(
        source_name=args.source,
        max_records=args.limit,
        batch_size=args.batch_size,
        use_cache=not args.no_cache,
    )
    
    # Run pipeline
    try:
        result = pipeline.run(config)
        
        # Print summary
        print("\n" + "="*60)
        print(f"Pipeline execution completed")
        print("="*60)
        print(f"Source: {result.source_name}")
        print(f"Records discovered: {result.discovered}")
        print(f"Records loaded: {result.loaded}")
        print(f"Records failed: {result.failed}")
        print(f"Duration: {result.duration_seconds:.2f}s")
        
        if result.errors:
            print(f"\nErrors encountered: {len(result.errors)}")
            for error in result.errors[:5]:  # Show first 5
                print(f"  - {error}")
        
        # Success if at least one record loaded
        return 0 if result.loaded > 0 else 1
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        return 1


def cmd_list_sources(args):
    """List available data sources."""
    registry = setup_pipeline_registry()
    sources = registry.list_sources()
    
    print("\nAvailable data sources:")
    print("="*60)
    for name in sources:
        print(f"  - {name}")
    
    return 0


def cmd_list_loaders(args):
    """List available loaders."""
    registry = setup_pipeline_registry()
    loaders = registry.list_loaders()
    
    print("\nAvailable loaders:")
    print("="*60)
    for name in loaders:
        print(f"  - {name}")
    
    return 0


def cmd_stats(args):
    """Show pipeline statistics."""
    # Get loader stats
    persist_dir = "data/vectorstore"
    repo = ChromaRegulationRepository(persist_directory=persist_dir)
    loader = VectorDBLoader(repo)
    stats = loader.get_statistics()
    
    print("\nVector Database Statistics:")
    print("="*60)
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generic Data Pipeline CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run iPlan pipeline with limit
  %(prog)s run --source iplan --limit 1000
  
  # Run with custom batch size
  %(prog)s run --source iplan --batch-size 100
  
  # Skip cache and force fresh fetch
  %(prog)s run --source iplan --no-cache
  
  # List available sources
  %(prog)s list-sources
  
  # Show statistics
  %(prog)s stats
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run data ingestion pipeline')
    run_parser.add_argument(
        '--source',
        type=str,
        default='iplan',
        help='Data source name (default: iplan)'
    )
    run_parser.add_argument(
        '--loader',
        type=str,
        default='vectordb',
        help='Loader name (default: vectordb)'
    )
    run_parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum records to process (default: all)'
    )
    run_parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Batch size for loading (default: 50)'
    )
    run_parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Skip cache and force fresh discovery'
    )
    run_parser.add_argument(
        '--cache-file',
        type=str,
        default=None,
        help='Custom cache file path'
    )
    run_parser.set_defaults(func=cmd_run)
    
    # List sources command
    list_sources_parser = subparsers.add_parser('list-sources', help='List available data sources')
    list_sources_parser.set_defaults(func=cmd_list_sources)
    
    # List loaders command
    list_loaders_parser = subparsers.add_parser('list-loaders', help='List available loaders')
    list_loaders_parser.set_defaults(func=cmd_list_loaders)
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show pipeline statistics')
    stats_parser.set_defaults(func=cmd_stats)
    
    # Parse and execute
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
