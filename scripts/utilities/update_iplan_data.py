#!/usr/bin/env python3
"""
Update iPlan data when new data is available.

This script provides a framework for updating the local iPlan data cache.
Since the iPlan API is protected by a WAF, this script serves as:

1. A template for manual data updates
2. A handler when AI assistant provides new data via fetch_webpage
3. Documentation of the update process

USAGE:
    # Check current data
    python3 update_iplan_data.py --status
    
    # Merge new data from a file
    python3 update_iplan_data.py --merge new_data.json
    
    # Request AI assistant to fetch fresh data
    # (This displays instructions for the AI assistant)
    python3 update_iplan_data.py --request-fetch
"""

import json
import argparse
from pathlib import Path
from datetime import datetime


DATA_FILE = Path("data/raw/iplan_layers.json")
BACKUP_DIR = Path("data/raw/backups")


def load_current_data():
    """Load existing data from the data file."""
    if not DATA_FILE.exists():
        return {"metadata": {}, "features": []}
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_data(data, backup=True):
    """Save data to file, optionally creating a backup."""
    if backup and DATA_FILE.exists():
        # Create backup
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"iplan_layers_{timestamp}.json"
        
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            backup_data = f.read()
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(backup_data)
        print(f"📦 Backup created: {backup_file}")
    
    # Save new data
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Data saved: {DATA_FILE}")


def show_status():
    """Display current data status."""
    data = load_current_data()
    features = data.get("features", [])
    metadata = data.get("metadata", {})
    
    print("=" * 70)
    print("iPlan Data Status")
    print("=" * 70)
    print()
    print(f"📊 Total Plans: {len(features)}")
    
    if metadata:
        print(f"📅 Last Updated: {metadata.get('fetched_at', 'Unknown')}")
        print(f"🌍 Source: {metadata.get('source', 'Unknown')}")
        print(f"📍 Coverage: {', '.join(metadata.get('coverage', []))}")
    
    if features:
        # Statistics
        districts = {}
        statuses = {}
        for feature in features:
            attrs = feature.get("attributes", {})
            district = attrs.get("district_name", "Unknown")
            status = attrs.get("station_desc", "Unknown")
            districts[district] = districts.get(district, 0) + 1
            statuses[status] = statuses.get(status, 0) + 1
        
        print()
        print("By District:")
        for district, count in sorted(districts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  • {district}: {count}")
        
        print()
        print("By Status:")
        for status, count in sorted(statuses.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {status}: {count}")
    
    print()
    print("=" * 70)


def merge_new_data(new_data_file):
    """Merge new data from a file with existing data."""
    # Load existing data
    current_data = load_current_data()
    current_features = current_data.get("features", [])
    
    # Load new data
    with open(new_data_file, 'r', encoding='utf-8') as f:
        new_data = json.load(f)
    
    if isinstance(new_data, dict) and "features" in new_data:
        new_features = new_data["features"]
    elif isinstance(new_data, list):
        new_features = new_data
    else:
        print("❌ Invalid data format in new file")
        return
    
    # Merge (avoid duplicates based on pl_number)
    existing_ids = {
        f["attributes"].get("pl_number") 
        for f in current_features 
        if f.get("attributes", {}).get("pl_number")
    }
    
    added = 0
    for feature in new_features:
        pl_number = feature.get("attributes", {}).get("pl_number")
        if pl_number and pl_number not in existing_ids:
            current_features.append(feature)
            existing_ids.add(pl_number)
            added += 1
    
    # Update metadata
    current_data["features"] = current_features
    current_data["metadata"] = {
        "last_updated": datetime.now().isoformat(),
        "source": "iPlan ArcGIS REST API",
        "count_total": len(current_features),
        "merged_from": str(new_data_file),
        "added_in_merge": added
    }
    
    # Save
    save_data(current_data, backup=True)
    
    print(f"✅ Merged {added} new plans")
    print(f"📊 Total plans now: {len(current_features)}")


def request_fetch_instructions():
    """Display instructions for AI assistant to fetch new data."""
    print("=" * 70)
    print("Request Data Fetch from AI Assistant")
    print("=" * 70)
    print()
    print("To request the AI assistant to fetch fresh iPlan data:")
    print()
    print("1. Say: 'Please fetch fresh iPlan data using fetch_webpage'")
    print()
    print("2. The assistant will use the fetch_webpage tool to access:")
    print("   https://ags.iplan.gov.il/arcgisiplan/rest/services/")
    print("   PlanningPublic/xplan_without_77_78/MapServer/1/query")
    print()
    print("3. Request format for maximum results:")
    print("   where=1%3D1&outFields=*&f=json")
    print("   &resultRecordCount=1000&resultOffset=0")
    print()
    print("4. Once data is received, ask the assistant to:")
    print("   'Save the fetched data to iplan_layers.json'")
    print()
    print("5. Or provide the data as JSON and run:")
    print("   python3 update_iplan_data.py --merge <new_data.json>")
    print()
    print("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Manage iPlan data updates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("--status", action="store_true",
                       help="Show current data status")
    parser.add_argument("--merge", type=str, metavar="FILE",
                       help="Merge new data from JSON file")
    parser.add_argument("--request-fetch", action="store_true",
                       help="Show instructions for requesting data fetch")
    
    args = parser.parse_args()
    
    if args.status:
        show_status()
    elif args.merge:
        merge_new_data(args.merge)
    elif args.request_fetch:
        request_fetch_instructions()
    else:
        # Default: show status
        show_status()


if __name__ == "__main__":
    main()
