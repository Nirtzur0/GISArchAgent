#!/usr/bin/env python3
"""
Data loader for iPlan sample data.

This module provides functions to load sample iPlan data from various sources.
The actual data is stored in separate JSON files to keep the codebase clean
and make it easier to add data from other sources in the future.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


def load_iplan_sample_data(source: str = "default") -> Dict:
    """Load sample iPlan data from a specified source.
    
    Args:
        source: Data source identifier. Options:
            - "default": Sample Israeli planning data (data/samples/iplan_sample_data.json)
            - Future: Add support for other sources/regions
    
    Returns:
        Dictionary containing metadata and features
        
    Raises:
        FileNotFoundError: If the data file doesn't exist
        ValueError: If the source is not recognized
    """
    if source == "default":
        data_file = Path(__file__).parent / "data" / "samples" / "iplan_sample_data.json"
    else:
        raise ValueError(f"Unknown data source: {source}")
    
    if not data_file.exists():
        raise FileNotFoundError(f"Sample data file not found: {data_file}")
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Add dynamic fetched_at timestamp
    if "metadata" in data:
        data["metadata"]["fetched_at"] = datetime.now().isoformat()
    
    return data


# For backward compatibility, provide REAL_IPLAN_DATA
# This will be loaded lazily when accessed
_cached_data: Optional[Dict] = None


def _get_data() -> Dict:
    """Get cached data or load it if not cached."""
    global _cached_data
    if _cached_data is None:
        _cached_data = load_iplan_sample_data("default")
    return _cached_data


# Expose REAL_IPLAN_DATA for backward compatibility
# This makes it work like the old hardcoded dictionary
class _DataProxy:
    """Proxy object that loads data on first access."""
    
    def __getitem__(self, key):
        return _get_data()[key]
    
    def get(self, key, default=None):
        return _get_data().get(key, default)
    
    def keys(self):
        return _get_data().keys()
    
    def values(self):
        return _get_data().values()
    
    def items(self):
        return _get_data().items()


REAL_IPLAN_DATA = _DataProxy()


def save_data(output_file: Optional[Path] = None, source: str = "default"):
    """Save iPlan data to a JSON file.
    
    Args:
        output_file: Path to save the data. Defaults to data/raw/iplan_layers.json
        source: Data source to load from (default: "default")
    """
    if output_file is None:
        output_file = Path("data/raw/iplan_layers.json")
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    data = load_iplan_sample_data(source)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    
    print("=" * 70)
    print("✅ Successfully saved iPlan data!")
    print("=" * 70)
    print()
    print(f"📁 File: {output_file}")
    print(f"📊 Plans saved: {data['metadata']['count_saved']}")
    print(f"🌍 Source: {data['metadata']['source']}")
    print(f"📅 Fetched: {data['metadata']['fetched_at']}")
    print()
    print("Coverage:")
    for region in data['metadata']['coverage']:
        print(f"  • {region}")
    print()
    print("Plan Summary:")
    
    # Generate statistics
    districts = {}
    statuses = {}
    for feature in data['features']:
        attrs = feature['attributes']
        district = attrs.get('district_name', 'Unknown')
        status = attrs.get('station_desc', 'Unknown')
        districts[district] = districts.get(district, 0) + 1
        statuses[status] = statuses.get(status, 0) + 1
    
    print("  By District:")
    for district, count in sorted(districts.items(), key=lambda x: x[1], reverse=True):
        print(f"    - {district}: {count} plans")
    
    print("  By Status:")
    for status, count in sorted(statuses.items(), key=lambda x: x[1], reverse=True):
        print(f"    - {status}: {count} plans")
    print()
    print("=" * 70)


if __name__ == "__main__":
    save_data()

