# Sample Data Sources

This directory contains sample data from various sources that can be used to populate the GIS Architecture Agent system.

## Structure

Each data source is stored as a separate JSON file to make it easy to:
- Maintain and update data without touching code
- Add new data sources from different regions/systems
- Version control data changes independently
- Share and exchange data with other systems

## Available Data Sources

### `iplan_sample_data.json`
- **Source**: Israeli iPlan ArcGIS REST API
- **Type**: Israeli planning data (תכניות)
- **Count**: 10 sample plans
- **Coverage**: Jerusalem, Haifa, Center District
- **Plan Types**: 
  - Local detailed plans (תכניות מפורטות)
  - Local outline plans (תכניות מתאר מקומיות)
  - Building line modifications (שינוי קווי בניין)

## Usage

### Loading Data in Code

```python
from populate_real_data import load_iplan_sample_data

# Load default sample data
data = load_iplan_sample_data("default")

# Access features
features = data["features"]
metadata = data["metadata"]
```

### Using the Import Script

```bash
# Import default sample data
python scripts/import_sample_data.py

# Import with verbose output
python scripts/import_sample_data.py --verbose

# Force overwrite existing data
python scripts/import_sample_data.py --force

# Specify a different source (when available)
python scripts/import_sample_data.py --source custom_source
```

## Adding New Data Sources

To add a new data source:

1. **Create a JSON file** in this directory with the following structure:
   ```json
   {
     "metadata": {
       "source": "Description of data source",
       "endpoint": "API endpoint or data origin",
       "count_saved": 10,
       "coverage": ["Region1", "Region2"],
       "note": "Any additional information"
     },
     "features": [
       {
         "attributes": { ... },
         "geometry": { ... }
       }
     ]
   }
   ```

2. **Update `populate_real_data.py`** to support the new source:
   ```python
   def load_iplan_sample_data(source: str = "default") -> Dict:
       if source == "default":
           data_file = Path(__file__).parent / "data" / "samples" / "iplan_sample_data.json"
       elif source == "new_source":
           data_file = Path(__file__).parent / "data" / "samples" / "new_source_data.json"
       # ...
   ```

3. **Test** by running the import script with your new source

## Data Format

All data files should follow the GeoJSON-like format with Israeli planning attributes:

### Required Attributes
- `pl_number`: Plan number
- `pl_name`: Plan name (Hebrew)
- `district_name`: District name
- `station_desc`: Current status
- `pl_area_dunam`: Area in dunams
- `geometry`: Polygon geometry in ITM coordinates (EPSG:2039)

### Optional Attributes
- `pl_url`: Link to plan details
- `pl_objectives`: Plan objectives
- `entity_subtype_desc`: Plan type description
- Various quantity and date fields

## Notes

- Coordinate system: ITM (EPSG:2039) - Israeli Transverse Mercator
- All text fields support Hebrew (UTF-8 encoding)
- Dates are stored as Unix timestamps (milliseconds)
- Areas are in dunams (1 dunam = 1000 m²)
