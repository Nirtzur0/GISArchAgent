#!/usr/bin/env python3
"""
Simplified iPlan data manager.

Since direct API access is blocked by WAF, this script helps manage
the data we can fetch through other means (browser-based tools).
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_existing_data(file_path: str = "data/raw/iplan_layers.json") -> Dict:
    """Load existing iPlan data from file."""
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"No existing data found at {file_path}")
        return {"features": []}
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle different data formats
    if isinstance(data, list):
        return {"features": data}
    elif isinstance(data, dict) and "features" in data:
        return data
    else:
        return {"features": []}


def save_data(data: Dict, file_path: str = "data/raw/iplan_layers.json") -> None:
    """Save iPlan data to file."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Saved data to {file_path}")


def get_stats(data: Dict) -> Dict:
    """Get statistics about the data."""
    features = data.get("features", [])
    
    if not features:
        return {"count": 0}
    
    # Get unique cities
    cities = set()
    districts = set()
    statuses = set()
    
    for feature in features:
        attrs = feature.get("attributes", {})
        if attrs.get("plan_county_name"):
            cities.add(attrs["plan_county_name"])
        if attrs.get("district_name"):
            districts.add(attrs["district_name"])
        if attrs.get("station_desc"):
            statuses.add(attrs["station_desc"])
    
    return {
        "count": len(features),
        "cities": len(cities),
        "districts": len(districts),
        "statuses": len(statuses),
        "sample_cities": list(cities)[:10],
        "sample_statuses": list(statuses),
    }


def main():
    """Display current data status."""
    print("=" * 60)
    print("iPlan Data Manager")
    print("=" * 60)
    
    data = load_existing_data()
    stats = get_stats(data)
    
    print(f"\nCurrent Data Status:")
    print(f"  Plans: {stats['count']}")
    
    if stats['count'] > 0:
        print(f"  Cities: {stats['cities']}")
        print(f"  Districts: {stats['districts']}")
        print(f"  Statuses: {stats['statuses']}")
        
        if stats.get('sample_cities'):
            print(f"\n  Sample cities:")
            for city in stats['sample_cities']:
                print(f"    - {city}")
        
        if stats.get('sample_statuses'):
            print(f"\n  Plan statuses:")
            for status in stats['sample_statuses']:
                print(f"    - {status}")
    else:
        print("\n  ⚠️  No data available yet")
        print("\n  To fetch data:")
        print("  1. The iPlan API is protected by a WAF")
        print("  2. Direct Python/curl access is blocked")
        print("  3. Data can be accessed through the web interface")
        print("  4. Use the Streamlit app to query plans interactively")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
