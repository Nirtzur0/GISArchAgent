"""
Data Store - Local storage and retrieval of planning data.

Handles loading, saving, and querying planning data from local JSON files.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataStore:
    """
    Manages local storage of planning data.
    
    Provides methods to load, save, query, and manage planning data
    stored in JSON format.
    """
    
    def __init__(self, data_file: str = "data/raw/iplan_layers.json"):
        """
        Initialize data store.
        
        Args:
            data_file: Path to the data file
        """
        self.data_file = Path(data_file)
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self._data: Optional[Dict] = None
        self._load_data()
    
    def _load_data(self):
        """Load data from file."""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
                logger.info(f"Loaded {len(self.get_all_features())} plans from {self.data_file}")
            else:
                self._data = {"metadata": {}, "features": []}
                logger.info(f"Initialized empty data store at {self.data_file}")
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            self._data = {"metadata": {}, "features": []}
    
    def get_all_features(self) -> List[Dict]:
        """Get all planning features."""
        if self._data is None:
            self._load_data()
        return self._data.get("features", [])
    
    def get_metadata(self) -> Dict:
        """Get data metadata."""
        if self._data is None:
            self._load_data()
        return self._data.get("metadata", {})
    
    def get_feature_by_plan_number(self, plan_number: str) -> Optional[Dict]:
        """
        Get a specific plan by plan number.
        
        Args:
            plan_number: The plan number to search for
            
        Returns:
            The feature dict or None if not found
        """
        for feature in self.get_all_features():
            attrs = feature.get("attributes", {})
            if attrs.get("pl_number") == plan_number:
                return feature
        return None
    
    def search_features(
        self,
        district: Optional[str] = None,
        city: Optional[str] = None,
        status: Optional[str] = None,
        text: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for features matching criteria.
        
        Args:
            district: Filter by district name
            city: Filter by city/county name
            status: Filter by plan status
            text: Search in plan name/number
            
        Returns:
            List of matching features
        """
        results = self.get_all_features()
        
        if district:
            results = [f for f in results 
                      if f.get("attributes", {}).get("district_name") == district]
        
        if city:
            results = [f for f in results 
                      if f.get("attributes", {}).get("plan_county_name") == city]
        
        if status:
            results = [f for f in results 
                      if f.get("attributes", {}).get("station_desc") == status]
        
        if text:
            text_lower = text.lower()
            results = [f for f in results 
                      if text_lower in str(f.get("attributes", {}).get("pl_name", "")).lower()
                      or text_lower in str(f.get("attributes", {}).get("pl_number", "")).lower()]
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored data.
        
        Returns:
            Dict with counts by district, status, city, etc.
        """
        features = self.get_all_features()
        
        districts = {}
        cities = {}
        statuses = {}
        
        for feature in features:
            attrs = feature.get("attributes", {})
            
            district = attrs.get("district_name", "Unknown")
            districts[district] = districts.get(district, 0) + 1
            
            city = attrs.get("plan_county_name", "Unknown")
            cities[city] = cities.get(city, 0) + 1
            
            status = attrs.get("station_desc", "Unknown")
            statuses[status] = statuses.get(status, 0) + 1
        
        return {
            "total_plans": len(features),
            "by_district": districts,
            "by_city": cities,
            "by_status": statuses,
            "metadata": self.get_metadata()
        }
    
    def add_features(self, features: List[Dict], avoid_duplicates: bool = True) -> int:
        """
        Add new features to the data store.
        
        Args:
            features: List of feature dicts to add
            avoid_duplicates: Skip features with duplicate plan numbers
            
        Returns:
            Number of features actually added
        """
        if self._data is None:
            self._load_data()
        
        existing_ids = set()
        if avoid_duplicates:
            existing_ids = {
                f["attributes"].get("pl_number")
                for f in self._data.get("features", [])
                if f.get("attributes", {}).get("pl_number")
            }
        
        added = 0
        for feature in features:
            pl_number = feature.get("attributes", {}).get("pl_number")
            if not avoid_duplicates or pl_number not in existing_ids:
                self._data["features"].append(feature)
                if pl_number:
                    existing_ids.add(pl_number)
                added += 1
        
        if added > 0:
            self._update_metadata(f"Added {added} features")
            logger.info(f"Added {added} new features to data store")
        
        return added
    
    def _update_metadata(self, note: str):
        """Update metadata with timestamp and note."""
        if "metadata" not in self._data:
            self._data["metadata"] = {}
        
        self._data["metadata"]["last_updated"] = datetime.now().isoformat()
        self._data["metadata"]["update_note"] = note
        self._data["metadata"]["count_total"] = len(self._data.get("features", []))
    
    def save(self, backup: bool = True):
        """
        Save data to file.
        
        Args:
            backup: Create backup before saving
        """
        if backup and self.data_file.exists():
            backup_dir = self.data_file.parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"{self.data_file.stem}_{timestamp}.json"
            
            with open(self.data_file, 'r', encoding='utf-8') as f:
                backup_data = f.read()
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(backup_data)
            logger.info(f"Created backup: {backup_file}")
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved data to {self.data_file}")
    
    def reload(self):
        """Reload data from file."""
        self._load_data()
    
    def get_unique_values(self, field: str) -> List[str]:
        """
        Get unique values for a specific field.
        
        Args:
            field: Field name in attributes
            
        Returns:
            Sorted list of unique values
        """
        values = set()
        for feature in self.get_all_features():
            value = feature.get("attributes", {}).get(field)
            if value:
                values.add(str(value))
        return sorted(list(values))
