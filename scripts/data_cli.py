#!/usr/bin/env python3
"""
Data management CLI tool.

Provides command-line access to data store operations:
- View data statistics
- Search and filter plans
- Export data
- Backup management

Usage:
    python scripts/data_cli.py status
    python scripts/data_cli.py search --city "ירושלים"
    python scripts/data_cli.py export output.json
    python scripts/data_cli.py backup list
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import click
import json
from datetime import datetime
from src.data_management import DataStore


@click.group()
def cli():
    """Data management CLI tool."""
    pass


@cli.command()
@click.option('--verbose', '-v', is_flag=True, help='Show detailed statistics')
def status(verbose):
    """Show data store status and statistics."""
    
    data_store = DataStore()
    stats = data_store.get_statistics()
    
    print("📊 Data Store Status")
    print("=" * 60)
    print(f"\n📁 Location: {data_store.data_file}")
    
    if data_store.data_file.exists():
        size_kb = data_store.data_file.stat().st_size / 1024
        print(f"💾 Size: {size_kb:.1f} KB")
    else:
        print("⚠️  No data file found")
        return
    
    print(f"\n📋 Total Plans: {stats['total_plans']}")
    print(f"🗺️  Districts: {len(stats['by_district'])}")
    print(f"🏙️  Cities: {len(stats['by_city'])}")
    print(f"📌 Statuses: {len(stats['by_status'])}")
    
    if verbose:
        print("\n" + "=" * 60)
        print("Districts:")
        for district, count in sorted(stats["by_district"].items(), key=lambda x: x[1], reverse=True):
            print(f"  {district}: {count}")
        
        print("\nTop Cities:")
        sorted_cities = sorted(stats["by_city"].items(), key=lambda x: x[1], reverse=True)
        for city, count in sorted_cities[:10]:
            print(f"  {city}: {count}")
        
        print("\nStatuses:")
        for status, count in sorted(stats["by_status"].items(), key=lambda x: x[1], reverse=True):
            print(f"  {status}: {count}")
        
        # Metadata
        metadata = stats.get("metadata", {})
        if metadata:
            print("\n" + "=" * 60)
            print("Metadata:")
            for key, value in metadata.items():
                if isinstance(value, list):
                    print(f"  {key}:")
                    for item in value:
                        print(f"    - {item}")
                else:
                    print(f"  {key}: {value}")


@cli.command()
@click.option('--district', '-d', help='Filter by district')
@click.option('--city', '-c', help='Filter by city')
@click.option('--status', '-s', help='Filter by status')
@click.option('--text', '-t', help='Search in plan name/number')
@click.option('--limit', '-l', default=10, help='Maximum results to show')
@click.option('--verbose', '-v', is_flag=True, help='Show full plan details')
def search(district, city, status, text, limit, verbose):
    """Search for plans with filters."""
    
    data_store = DataStore()
    
    print("🔍 Searching Plans")
    print("=" * 60)
    
    # Show filters
    filters = []
    if district:
        filters.append(f"District: {district}")
    if city:
        filters.append(f"City: {city}")
    if status:
        filters.append(f"Status: {status}")
    if text:
        filters.append(f"Text: {text}")
    
    if filters:
        print("Filters:")
        for f in filters:
            print(f"  {f}")
        print()
    
    # Search
    results = data_store.search_features(
        district=district,
        city=city,
        status=status,
        text=text
    )
    
    print(f"Found {len(results)} plans\n")
    
    # Display results
    for idx, feature in enumerate(results[:limit]):
        attrs = feature.get("attributes", {})
        
        print(f"{idx + 1}. {attrs.get('pl_number', 'N/A')}")
        print(f"   Name: {attrs.get('pl_name', 'N/A')}")
        
        if verbose:
            print(f"   District: {attrs.get('district_name', 'N/A')}")
            print(f"   City: {attrs.get('plan_county_name', 'N/A')}")
            print(f"   Status: {attrs.get('station_desc', 'N/A')}")
            print(f"   Area: {attrs.get('pl_area_dunam', 0)} dunam")
            
            if attrs.get('pl_url'):
                print(f"   URL: {attrs['pl_url']}")
        
        print()
    
    if len(results) > limit:
        print(f"... and {len(results) - limit} more. Use --limit to see more.")


@cli.command()
@click.argument('output_file', type=click.Path())
@click.option('--district', '-d', help='Filter by district')
@click.option('--city', '-c', help='Filter by city')
@click.option('--status', '-s', help='Filter by status')
@click.option('--pretty', '-p', is_flag=True, help='Pretty-print JSON')
def export(output_file, district, city, status, pretty):
    """Export plans to JSON file."""
    
    data_store = DataStore()
    
    # Get features (filtered if specified)
    if district or city or status:
        features = data_store.search_features(
            district=district,
            city=city,
            status=status
        )
        print(f"Exporting {len(features)} filtered plans...")
    else:
        features = data_store.get_all_features()
        print(f"Exporting all {len(features)} plans...")
    
    # Export
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    export_data = {
        "metadata": {
            "exported_at": datetime.now().isoformat(),
            "source": "GISArchAgent Data Store",
            "count": len(features)
        },
        "features": features
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        if pretty:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        else:
            json.dump(export_data, f, ensure_ascii=False)
    
    size_kb = output_path.stat().st_size / 1024
    print(f"✅ Exported to {output_path}")
    print(f"   Size: {size_kb:.1f} KB")


@cli.group()
def backup():
    """Backup management commands."""
    pass


@backup.command(name='list')
@click.option('--limit', '-l', default=10, help='Number of backups to show')
def list_backups(limit):
    """List available backups."""
    
    data_store = DataStore()
    backup_dir = data_store.data_file.parent / "backups"
    
    if not backup_dir.exists():
        print("No backups found.")
        return
    
    backups = sorted(backup_dir.glob("iplan_layers_*.json"), reverse=True)
    
    print(f"📦 Backups ({len(backups)} total)")
    print("=" * 60)
    
    for idx, backup in enumerate(backups[:limit]):
        size_kb = backup.stat().st_size / 1024
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        print(f"{idx + 1}. {backup.name}")
        print(f"   Size: {size_kb:.1f} KB")
        print(f"   Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    if len(backups) > limit:
        print(f"... and {len(backups) - limit} more.")


@backup.command()
@click.argument('backup_file', type=click.Path(exists=True))
@click.option('--force', '-f', is_flag=True, help='Overwrite without confirmation')
def restore(backup_file, force):
    """Restore from a backup file."""
    
    data_store = DataStore()
    backup_path = Path(backup_file)
    
    if not force:
        print(f"⚠️  This will replace current data with backup:")
        print(f"   {backup_path.name}")
        if not click.confirm("Continue?"):
            print("Cancelled.")
            return
    
    # Load backup
    with open(backup_path, 'r', encoding='utf-8') as f:
        backup_data = json.load(f)
    
    # Create backup of current data first
    print("Creating backup of current data...")
    data_store.save(backup=True)
    
    # Restore
    data_store.data = backup_data
    data_store.save(backup=False)
    
    count = len(backup_data.get("features", []))
    print(f"✅ Restored {count} plans from backup")


if __name__ == "__main__":
    cli()
