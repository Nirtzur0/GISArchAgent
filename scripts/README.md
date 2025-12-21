# Data Management Scripts

CLI utilities for managing planning data outside of the Streamlit interface.

## Available Scripts

### 1. data_cli.py - Main Data Management Tool

Comprehensive CLI for data operations.

#### Status
```bash
# Basic status
python3 scripts/data_cli.py status

# Detailed statistics
python3 scripts/data_cli.py status -v
```

#### Search
```bash
# Search by district
python3 scripts/data_cli.py search --district "ירושלים"

# Search by city
python3 scripts/data_cli.py search --city "תל אביב"

# Search by status
python3 scripts/data_cli.py search --status "אישור"

# Text search in plan name/number
python3 scripts/data_cli.py search --text "מגורים"

# Combine filters
python3 scripts/data_cli.py search -d "ירושלים" -c "ירושלים" --limit 20

# Show full details
python3 scripts/data_cli.py search --text "תמא" -v
```

#### Export
```bash
# Export all data
python3 scripts/data_cli.py export output.json

# Export pretty-printed
python3 scripts/data_cli.py export output.json --pretty

# Export filtered data
python3 scripts/data_cli.py export jerusalem_plans.json --city "ירושלים"
```

#### Backup Management
```bash
# List backups
python3 scripts/data_cli.py backup list

# List all backups
python3 scripts/data_cli.py backup list --limit 100

# Restore from backup
python3 scripts/data_cli.py backup restore data/raw/backups/iplan_layers_20231221_123456.json

# Force restore (no confirmation)
python3 scripts/data_cli.py backup restore backup.json --force
```

### 2. import_sample_data.py - Import Sample Data

Import the curated sample data from populate_real_data.py.

```bash
# Merge with existing data
python3 scripts/import_sample_data.py

# Replace all data
python3 scripts/import_sample_data.py --force

# Show detailed output
python3 scripts/import_sample_data.py --verbose
```

## Architecture Integration

These scripts use the new `src/data_management/` module:
- `DataStore` - Central data management class
- `DataFetcher` - Abstract base for data sources
- `DataFetcherFactory` - Source registry

The same module powers the Streamlit UI, ensuring consistency.

## Legacy Scripts

The following scripts in the root directory are preserved for reference
but are now superseded by the new architecture:

- `populate_real_data.py` - Contains hardcoded sample data (still used by import_sample_data.py)
- `update_iplan_data.py` - CLI for merging data (replaced by data_cli.py)
- `manage_data.py` - Simple status viewer (replaced by data_cli.py status)
- `fetch_and_save_iplan_data.py` - Utility functions (replaced by DataStore methods)

## Adding New Data Sources

To add support for a new data source (MAVAT, municipal APIs, etc.):

1. Create a fetcher class:
```python
from src.data_management.fetchers import DataFetcher

class MyNewFetcher(DataFetcher):
    def fetch(self, **kwargs) -> dict:
        # Fetch logic here
        return {"features": [...]}
    
    def get_source_name(self) -> str:
        return "My New Source"
    
    def is_available(self) -> bool:
        # Check if source is accessible
        return True
```

2. Register it:
```python
from src.data_management import DataFetcherFactory
DataFetcherFactory.register_fetcher("my_source", MyNewFetcher())
```

3. Use in Streamlit or CLI:
```python
data_store = DataStore()
fetcher = DataFetcherFactory.get_fetcher("my_source")
new_data = fetcher.fetch()
data_store.add_features(new_data["features"])
data_store.save(backup=True)
```

## Data Flow

```
External Source → Fetcher → DataStore → JSON File
                                ↓
                          Streamlit UI
                                ↓
                            User Display
```

## Quick Reference

| Task | Command |
|------|---------|
| Check data status | `python3 scripts/data_cli.py status` |
| Import sample data | `python3 scripts/import_sample_data.py` |
| Search plans | `python3 scripts/data_cli.py search --text "keyword"` |
| Export filtered | `python3 scripts/data_cli.py export out.json --city "City"` |
| List backups | `python3 scripts/data_cli.py backup list` |
| Restore backup | `python3 scripts/data_cli.py backup restore file.json` |

## Tips

1. **Always use backups**: The system automatically creates backups when saving
2. **UTF-8 encoding**: All files use UTF-8 to support Hebrew text
3. **Duplicate prevention**: Use `add_features(avoid_duplicates=True)` when merging
4. **Filter before export**: Export only what you need to reduce file size
5. **Check status first**: Run `status -v` to understand your data before operations

## Troubleshooting

### Import fails
- Check that `populate_real_data.py` exists in root directory
- Verify JSON structure in that file

### Data not showing in Streamlit
- Run `python3 scripts/data_cli.py status` to verify data exists
- Click "Reload Data" in the Streamlit sidebar
- Check file permissions on `data/raw/iplan_layers.json`

### Search returns no results
- Use `-v` flag to see what's in the database
- Check spelling (Hebrew text is case-sensitive)
- Try broader search terms

### Backup restore fails
- Verify backup file is valid JSON
- Check you have write permissions
- Use `--force` if you're certain about the restore

## See Also

- [../docs/DATA_MANAGEMENT.md](../docs/DATA_MANAGEMENT.md) - Complete data management guide
- [../src/data_management/](../src/data_management/) - Source code
- [../pages/3_💾_Data_Management.py](../pages/3_💾_Data_Management.py) - Streamlit UI
