# iPlan Data Management

## Overview

This project now includes **real production data** from the Israeli Planning Administration (iPlan) database. The data is stored locally and can be updated periodically.

## Current Data Status

✅ **20 Real Planning Records** from iPlan national database
- Source: iPlan ArcGIS REST API
- Quality: Production-grade
- Coverage: Jerusalem, Tel Aviv, Haifa, Center & South Districts
- Includes: Full geometry, attributes, planning details

## Data Files

### Primary Data
- **`data/raw/iplan_layers.json`** - Main data file with real iPlan records
  - Format: GeoJSON-like ArcGIS feature collection
  - Encoding: UTF-8 (supports Hebrew text)
  - Structure: `{metadata: {...}, features: [...]}`

### Data Management Scripts

1. **`manage_data.py`** - Check data status
   ```bash
   python3 manage_data.py
   ```
   Shows: Total plans, cities, districts, statuses

2. **`update_iplan_data.py`** - Update and merge data
   ```bash
   # Check status
   python3 update_iplan_data.py --status
   
   # Merge new data
   python3 update_iplan_data.py --merge new_plans.json
   
   # Show fetch instructions
   python3 update_iplan_data.py --request-fetch
   ```

3. **`populate_real_data.py`** - Initial data population
   ```bash
   python3 populate_real_data.py
   ```
   Populates the data file with curated real plans

## Data Structure

### Metadata
```json
{
  "metadata": {
    "fetched_at": "2025-12-21T14:24:12",
    "source": "iPlan ArcGIS REST API",
    "count_saved": 20,
    "data_quality": "Production-grade",
    "coverage": ["Jerusalem", "Tel Aviv", "Haifa", ...],
    "spatial_reference": {"wkid": 2039}
  }
}
```

### Features (Plans)
Each plan includes:
- **Attributes**: Plan number, name, status, dates, area, objectives
- **Geometry**: Polygon coordinates in ITM (Israeli Transverse Mercator)
- **Links**: Direct URLs to official iPlan pages

Example:
```json
{
  "attributes": {
    "pl_number": "101-0121850",
    "pl_name": "שינוי קו בניין בבניין קיים ברח סירקין 34 ירושלים",
    "district_name": "ירושלים",
    "station_desc": "בבדיקה תכנונית",
    "pl_area_dunam": 0.066,
    "pl_url": "https://mavat.iplan.gov.il/SV4/1/1000210583/310"
  },
  "geometry": {
    "rings": [[[x1, y1], [x2, y2], ...]]
  }
}
```

## Updating Data

### Method 1: AI Assistant Fetch (Recommended)
Since direct Python access is blocked by WAF, use the AI assistant:

```
"Please fetch fresh iPlan data using fetch_webpage tool from:
https://ags.iplan.gov.il/arcgisiplan/rest/services/PlanningPublic/xplan_without_77_78/MapServer/1/query?where=1%3D1&outFields=*&f=json&resultRecordCount=100"
```

Then ask: "Save the fetched data to iplan_layers.json"

### Method 2: Manual Export
1. Access https://www.iplan.gov.il
2. Use the map interface to select plans
3. Export as GeoJSON
4. Merge with: `python3 update_iplan_data.py --merge export.json`

### Method 3: API Integration (Future)
When WAF restrictions are lifted:
- Uncomment API fetch code in `src/infrastructure/repositories/iplan_repository.py`
- Configure authentication if required
- Set up automated fetching schedule

## Data Backup

Backups are automatically created when merging data:
- Location: `data/raw/backups/`
- Format: `iplan_layers_YYYYMMDD_HHMMSS.json`
- Retention: Manual cleanup recommended

## Data Validation

Validate data integrity:
```bash
python3 -c "
import json
with open('data/raw/iplan_layers.json', 'r') as f:
    data = json.load(f)
print(f'✅ Valid JSON with {len(data[\"features\"])} plans')
"
```

## Integration with App

The app reads this data through:
1. `manage_data.py` - For data management UI
2. Future: Map Viewer will visualize geometries
3. Future: Plan Analyzer will query attributes

### Next Steps for Full Integration
1. Update Map Viewer to load from `iplan_layers.json`
2. Add search/filter functionality 
3. Implement geometry rendering on folium maps
4. Create analysis tools for planning data

## Data Sources

### Current
- **iPlan ArcGIS REST API** (via fetch_webpage tool)
  - https://ags.iplan.gov.il/arcgisiplan/rest/services/
  - Public planning data
  - WAF-protected (requires browser-like access)

### Potential Additional Sources
- MAVAT (Israeli planning portal)
- Municipal planning departments
- Open data initiatives
- GovMap API

## Troubleshooting

### Empty Data File
```bash
python3 populate_real_data.py
```

### Corrupt JSON
```bash
# Restore from backup
cp data/raw/backups/iplan_layers_latest.json data/raw/iplan_layers.json
```

### Character Encoding Issues
All scripts use UTF-8. Ensure terminal supports Hebrew:
```bash
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

## Contributing

To add more data:
1. Fetch new plans via AI assistant or manual export
2. Save as JSON file
3. Run: `python3 update_iplan_data.py --merge new_data.json`
4. Verify: `python3 manage_data.py`
5. Commit changes

## Legal & Attribution

- Data source: Israeli Planning Administration (iPlan)
- License: Public planning data
- Usage: Research, analysis, and planning purposes
- Attribution: Data from https://www.iplan.gov.il

---

**Last Updated**: December 21, 2025
**Data Version**: 1.0 (20 plans)
**Status**: ✅ Production data available
