#!/usr/bin/env python3
"""
Import sample iPlan data into the data store.

This script provides a CLI interface to import the curated sample data
into the data management system. The sample data is loaded from JSON files
for easier maintenance and extensibility.

Usage:
    python scripts/import_sample_data.py [--force] [--source default]
    
Options:
    --force     Overwrite existing data (default: merge with duplicates avoided)
    --source    Data source to load from (default: "default")
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import click
from datetime import datetime
from src.data_management import DataStore

# Import the data loader
from populate_real_data import load_iplan_sample_data


@click.command()
@click.option('--force', is_flag=True, help='Overwrite existing data')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
@click.option('--source', default='default', help='Data source to load (default: "default")')
def main(force, verbose, source):
    """Import sample iPlan data into the data store."""
    
    print("🏗️  iPlan Sample Data Importer")
    print("=" * 60)
    print(f"📦 Loading data from source: {source}")
    
    # Initialize data store
    data_store = DataStore()
    
    # Check existing data
    existing_count = len(data_store.get_all_features())
    
    if existing_count > 0 and not force:
        print(f"ℹ️  Found {existing_count} existing plans")
        print("   New data will be merged (duplicates avoided)")
    elif existing_count > 0 and force:
        print(f"⚠️  Found {existing_count} existing plans")
        print("   All data will be replaced!")
        
        if not click.confirm("Continue?"):
            print("Cancelled.")
            return
    
    # Load sample data from JSON file
    try:
        sample_data = load_iplan_sample_data(source)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ Error loading sample data: {e}")
        return
    
    # Extract features
    features = sample_data.get("features", [])
    metadata = sample_data.get("metadata", {})
    
    print(f"\n📥 Importing {len(features)} sample plans...")
    
    if verbose:
        print(f"\nMetadata:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")

    
    # Import data
    if force:
        # Clear and replace
        data_store.data = {
            "metadata": metadata,
            "features": features
        }
        added = len(features)
    else:
        # Merge with duplicate detection
        added = data_store.add_features(features, avoid_duplicates=True)
    
    # Save with backup
    print(f"\n💾 Saving data...")
    data_store.save(backup=True)
    
    # Show results
    print(f"\n✅ Import complete!")
    print(f"   Added: {added} plans")
    print(f"   Total: {len(data_store.get_all_features())} plans")
    
    # Show statistics
    if verbose:
        print("\n📊 Statistics:")
        stats = data_store.get_statistics()
        
        print(f"\n  Districts:")
        for district, count in sorted(stats["by_district"].items(), key=lambda x: x[1], reverse=True):
            print(f"    {district}: {count}")
        
        print(f"\n  Statuses:")
        for status, count in sorted(stats["by_status"].items(), key=lambda x: x[1], reverse=True):
            print(f"    {status}: {count}")
    
    print(f"\n✨ Data ready to use in the Streamlit app!")


if __name__ == "__main__":
    main()
