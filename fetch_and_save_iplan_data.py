#!/usr/bin/env python3
"""
Fetch and save iPlan data from the API.

This script demonstrates the data structure and provides a template
for when automated fetching becomes possible. Currently, the iPlan API
is protected by a WAF that blocks direct Python requests.

The fetch_webpage tool in the AI assistant can access the data,
but cannot be called directly from Python.
"""

import json
from pathlib import Path
from datetime import datetime


def save_iplan_data(features_data, output_file="data/raw/iplan_layers.json"):
    """
    Save iPlan features data to JSON file.
    
    Args:
        features_data: List of feature dictionaries from iPlan API
        output_file: Path to output JSON file
    """
    # Ensure directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare metadata
    metadata = {
        "fetched_at": datetime.now().isoformat(),
        "source": "iPlan ArcGIS REST API",
        "endpoint": "https://ags.iplan.gov.il/arcgisiplan/rest/services/PlanningPublic/xplan_without_77_78/MapServer/1/query",
        "count": len(features_data),
        "note": "Real production data from Israeli planning system"
    }
    
    # Create data structure
    data = {
        "metadata": metadata,
        "features": features_data
    }
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved {len(features_data)} plans to {output_file}")
    print(f"   Fetched at: {metadata['fetched_at']}")
    
    return output_path


def load_existing_data(input_file="data/raw/iplan_layers.json"):
    """Load existing iPlan data if available."""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict) and "features" in data:
                return data["features"]
            elif isinstance(data, list):
                return data
            else:
                return []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def get_plan_summary(features_data):
    """Generate a summary of the plans."""
    if not features_data:
        return "No plans available"
    
    # Count by district
    districts = {}
    for feature in features_data:
        attrs = feature.get("attributes", {})
        district = attrs.get("district_name", "Unknown")
        districts[district] = districts.get(district, 0) + 1
    
    # Count by status
    statuses = {}
    for feature in features_data:
        attrs = feature.get("attributes", {})
        status = attrs.get("station_desc", "Unknown")
        statuses[status] = statuses.get(status, 0) + 1
    
    summary = f"Total Plans: {len(features_data)}\n\n"
    summary += "By District:\n"
    for district, count in sorted(districts.items(), key=lambda x: x[1], reverse=True)[:5]:
        summary += f"  - {district}: {count}\n"
    
    summary += "\nBy Status:\n"
    for status, count in sorted(statuses.items(), key=lambda x: x[1], reverse=True)[:5]:
        summary += f"  - {status}: {count}\n"
    
    return summary


if __name__ == "__main__":
    print("=" * 60)
    print("iPlan Data Fetcher")
    print("=" * 60)
    print()
    print("⚠️  Note: Direct fetching is blocked by WAF")
    print("   Data must be provided via AI assistant's fetch_webpage tool")
    print()
    
    # Check existing data
    existing = load_existing_data()
    print(f"Current data: {len(existing)} plans")
    print()
    
    if existing:
        print("Summary of existing data:")
        print(get_plan_summary(existing))
