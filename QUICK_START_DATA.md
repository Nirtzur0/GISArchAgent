# Quick Start Guide - Data Management Integration

## 🎉 What's New?

Your data management scripts are now fully integrated into the Streamlit app with a professional architecture that supports multiple data sources!

## 🚀 Getting Started (2 Minutes)

### Option 1: Web Interface (Easiest)
```bash
streamlit run app.py
```
Then:
1. Click **💾 Data Management** button
2. Explore the Overview tab (statistics & charts)
3. Try the Browse tab (search & filter)
4. Click **📍 View Maps** to see plans on the map

### Option 2: Command Line
```bash
# See what you have
python3 scripts/data_cli.py status -v

# Search for plans
python3 scripts/data_cli.py search --city "ירושלים" -v
```

## 📊 What You Can Do Now

### Web Interface Features

**💾 Data Management Page**
- View statistics (10 plans across 3 districts)
- Search and filter plans
- Upload new data files
- See data quality metrics

**📍 Map Viewer Page**
- See real plan boundaries on the map
- Color-coded by district/status/city
- Click markers for details
- Filter sidebar
- Plan summary table

### CLI Features

```bash
# Status and statistics
python3 scripts/data_cli.py status
python3 scripts/data_cli.py status -v    # Detailed

# Search
python3 scripts/data_cli.py search --district "חיפה"
python3 scripts/data_cli.py search --city "ירושלים" -v
python3 scripts/data_cli.py search --text "keyword"

# Export
python3 scripts/data_cli.py export plans.json --pretty
python3 scripts/data_cli.py export haifa.json --district "חיפה"

# Backups
python3 scripts/data_cli.py backup list
python3 scripts/data_cli.py backup restore backup_file.json
```

## 🎯 Common Tasks

### Task 1: Browse Your Data
**Web:** Open app → Data Management → Browse tab  
**CLI:** `python3 scripts/data_cli.py search --limit 20 -v`

### Task 2: See Plans on Map
**Web:** Open app → Map Viewer → Play with filters  
**CLI:** N/A (use web interface)

### Task 3: Import New Data
**Web:** Data Management → Upload file in sidebar  
**CLI:** `python3 scripts/import_sample_data.py`

### Task 4: Export Filtered Data
**Web:** N/A (coming soon)  
**CLI:** `python3 scripts/data_cli.py export output.json --city "ירושלים"`

### Task 5: Check Statistics
**Web:** Data Management → Overview tab  
**CLI:** `python3 scripts/data_cli.py status -v`

## 📁 Where Everything Is

```
Your Project/
├── Web Interface
│   ├── pages/3_💾_Data_Management.py  ← Data browsing UI
│   └── pages/1_📍_Map_Viewer.py       ← Map with real data
│
├── CLI Tools  
│   ├── scripts/data_cli.py             ← Main CLI
│   └── scripts/import_sample_data.py   ← Import helper
│
├── Core Module
│   └── src/data_management/
│       ├── data_store.py               ← CRUD operations
│       └── fetchers.py                 ← Data sources
│
└── Data Storage
    └── data/raw/
        ├── iplan_layers.json           ← Your 10 plans
        └── backups/                    ← Auto backups
```

## 🔥 Cool Features

### 1. Automatic Backups
Every time you save, a backup is created automatically:
```
data/raw/backups/iplan_layers_20231221_143022.json
```

### 2. Smart Duplicate Detection
When importing, duplicates are automatically skipped:
```python
store.add_features(new_plans, avoid_duplicates=True)
```

### 3. Hebrew Support
Full UTF-8 encoding throughout:
- Search Hebrew text: `--text "ירושלים"`
- Display Hebrew properly in CLI
- Hebrew metadata preserved

### 4. Real Map Integration
Plans are rendered with:
- Polygon boundaries (ITM → WGS84 transformed)
- Interactive popups
- Color coding
- Filtering

### 5. Extensible Architecture
Add new data sources easily:
```python
# Future: MAVAT, municipal APIs, etc.
class MavatFetcher(DataFetcher):
    def fetch(self):
        # Your code here
        pass
```

## 🆘 Troubleshooting

### "No data found"
```bash
# Import sample data
python3 scripts/import_sample_data.py
```

### "Import error in Streamlit"
```bash
# Verify module works
python3 -c "from src.data_management import DataStore; print('OK')"
```

### "Search returns nothing"
```bash
# Check what you have
python3 scripts/data_cli.py status -v
```

### "Map doesn't show plans"
- Check Data Management page first
- Click "Reload Data" in sidebar
- Verify data file exists: `ls data/raw/iplan_layers.json`

## 📚 Learn More

- **Full docs:** [docs/DATA_MANAGEMENT.md](docs/DATA_MANAGEMENT.md)
- **CLI reference:** [scripts/README.md](scripts/README.md)
- **Implementation:** [docs/INTEGRATION_SUMMARY.md](docs/INTEGRATION_SUMMARY.md)

## 💡 Pro Tips

1. **Use verbose mode** for detailed output: `-v`
2. **Export before experiments** to save your work
3. **Check backups** if something goes wrong
4. **Use filters** to narrow down searches
5. **Try the map** - it's the best way to visualize data

## 🎊 What's Next?

The architecture is ready for:
- ✨ Automatic fetching from iPlan (when API access opens)
- 🌐 MAVAT integration
- 🏛️ Municipal planning portals
- 📊 More data sources
- 🔄 Scheduled updates
- 📧 Notifications for new plans

## Questions?

Just ask! The system is designed to be intuitive and self-documenting.

---

**Enjoy your integrated data management system! 🚀**
