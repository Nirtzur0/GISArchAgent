#!/usr/bin/env python3
"""
Quick script to check vector database status after the build.
"""
import json
from pathlib import Path

print("=" * 70)
print("📊 GIS Architecture Agent - Database Status Report")
print("=" * 70)
print()

# Check pipeline stats
stats_file = Path("data/cache/pipeline_stats.json")
if stats_file.exists():
    with open(stats_file) as f:
        stats = json.load(f)

    print("✅ PIPELINE EXECUTION SUMMARY:")
    print(f"  Duration: {stats['duration_seconds']:.2f} seconds")
    print(f"  Plans discovered: {stats['plans_discovered']}")
    print(f"  Plans processed: {stats['plans_processed']}")
    print(f"  Plans failed: {stats['plans_failed']}")
    print(f"  Documents found: {stats['documents_found']}")
    print(f"  Regulations indexed: {stats['regulations_indexed']}")
    print()

# Check cache directory
cache_dir = Path("data/cache/selenium")
if cache_dir.exists():
    cache_files = list(cache_dir.glob("*.json"))
    print(f"📦 CACHE STATUS:")
    print(f"  Cached discovery files: {len(cache_files)}")
    total_size = sum(f.stat().st_size for f in cache_files)
    print(f"  Total cache size: {total_size / 1024 / 1024:.2f} MB")
    print()

# Check vector database
try:
    import chromadb
    db_path = Path("data/vectorstore")

    if db_path.exists():
        client = chromadb.PersistentClient(path=str(db_path))
        collections = client.list_collections()

        print(f"🗄️  VECTOR DATABASE STATUS:")
        print(f"  Database path: {db_path}")
        print(f"  Collections: {len(collections)}")

        for collection in collections:
            count = collection.count()
            print(f"    • {collection.name}: {count} items")
        print()
    else:
        print("⚠️  Vector database not found")
        print()
except Exception as e:
    print(f"❌ Error checking vector database: {e}")
    print()

# Check discovery files
discovery_file = Path("data/processed/iplan_discovered_metadata.json")
if discovery_file.exists():
    with open(discovery_file) as f:
        discovery = json.load(f)

    print(f"📝 DISCOVERY DATA:")
    print(f"  Total plans in metadata: {discovery['total_plans']}")
    print(f"  Plan types: {len(discovery['statistics']['by_type'])}")
    print(f"  Municipalities: {len(discovery['statistics']['by_municipality'])}")
    print()

print("=" * 70)
print()

# Summary and recommendations
print("📋 SUMMARY:")
print()
if stats.get('plans_discovered', 0) > 0:
    print(f"✅ Successfully discovered {stats['plans_discovered']} plans from iPlan")

    if stats.get('regulations_indexed', 0) == 0:
        print("⚠️  WARNING: Plans were discovered but not indexed in vector database")
        print()
        print("💡 NEXT STEPS:")
        print("  The pipeline discovered plan metadata but couldn't fetch documents")
        print("  because of a missing method in the data source.")
        print()
        print("  To properly index the data, you can:")
        print("  1. Use the Data Management page in the web app to import data")
        print("  2. Or run the simpler pipeline without document fetching:")
        print("     python3 -m src.data_pipeline.pipeline_manager")
    else:
        print(f"✅ Successfully indexed {stats['regulations_indexed']} regulations")
else:
    print("❌ No plans were discovered")

print()
print("=" * 70)

