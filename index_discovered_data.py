#!/usr/bin/env python3
"""
Index discovered iPlan data into vector database.

This script takes the cached discovery data and indexes it properly
using the DataPipelineManager which handles the metadata-only indexing.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_pipeline.pipeline_manager import DataPipelineManager
from src.infrastructure.repositories.chroma_repository import ChromaRegulationRepository

def main():
    print("=" * 70)
    print("🗄️  Indexing iPlan Data into Vector Database")
    print("=" * 70)
    print()

    # Initialize repository and manager
    print("📦 Initializing repository...")
    repo = ChromaRegulationRepository()

    print("🔧 Creating pipeline manager...")
    manager = DataPipelineManager(repo)

    print()
    print("🚀 Running indexing pipeline...")
    print("   This will index up to 1000 plan records")
    print()

    # Run the pipeline with force_rediscover=False to use cached data
    stats = manager.run_full_pipeline(
        max_records=1000,
        force_rediscover=False  # Use cached discovery data
    )

    print()
    print("=" * 70)
    print("✅ Indexing Complete!")
    print("=" * 70)
    print()
    print(f"📊 Results:")
    print(f"  Plans discovered: {stats.get('discovered', 0)}")
    print(f"  Plans indexed: {stats.get('indexed', 0)}")

    if stats.get('errors'):
        print(f"  Errors: {len(stats['errors'])}")
        print()
        print("❌ Errors encountered:")
        for error in stats['errors'][:5]:  # Show first 5 errors
            print(f"  - {error}")

    print()
    print("🎉 You can now query the data through the web app!")
    print()
    print("To verify, run: python3 scripts/quick_status.py")
    print()

if __name__ == "__main__":
    main()

