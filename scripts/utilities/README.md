# Utility Scripts

Useful standalone scripts for various maintenance and data management tasks.

## Database Management

### reinitialize_vectordb.py
Completely clear and reinitialize the vector database.

**Usage**:
```bash
python3 scripts/utilities/reinitialize_vectordb.py
```

**What it does**:
- Removes existing ChromaDB data
- Triggers fresh initialization
- Uses the generic pipeline to load data

**When to use**:
- Database corruption
- Need to start fresh
- Testing initialization process

---

## Data Management

### manage_data.py
Manage and inspect iPlan data files.

**Usage**:
```bash
# Show statistics
python3 scripts/utilities/manage_data.py

# With custom data file
python3 scripts/utilities/manage_data.py --file data/raw/custom_data.json
```

**What it does**:
- Load and inspect data files
- Show statistics (plan counts, types, etc.)
- Basic data validation

---

### fetch_iplan_data.py
Framework for fetching iPlan data from the API.

**Usage**:
```bash
python3 scripts/utilities/fetch_iplan_data.py
```

**Note**: Due to SSL/WAF issues with direct API access, this is primarily a template and documentation.

**What it provides**:
- Data structure documentation
- Save/load helper functions
- Template for manual data updates

---

### update_iplan_data.py
Update and merge iPlan data files.

**Usage**:
```bash
# Check current data status
python3 scripts/utilities/update_iplan_data.py --status

# Merge new data from a file
python3 scripts/utilities/update_iplan_data.py --merge new_data.json

# Show instructions for AI-assisted fetching
python3 scripts/utilities/update_iplan_data.py --request-fetch
```

**What it does**:
- Check current data status
- Merge new data with existing
- Create backups before updates
- Deduplicate records

---

## Parsing and Processing

### parse_iplan_response.py
Parse and process iPlan API responses.

**Usage**:
```bash
python3 scripts/utilities/parse_iplan_response.py [input_file]
```

**What it does**:
- Parse raw iPlan API JSON
- Extract relevant fields
- Convert to internal format

---

## Notes

### SSL/WAF Issues
Direct Python access to iPlan API often fails due to:
- SSL certificate issues
- Web Application Firewall (WAF) blocking
- Rate limiting

**Workarounds**:
1. Use AI assistant's `fetch_webpage` tool
2. Use browser-based data export
3. Use cached data files

### Data Pipeline
For automated, production-grade data loading, use the **generic pipeline** instead:

```bash
python3 src/data_pipeline/cli/pipeline.py run --source iplan --limit 5000
```

See: [Generic Pipeline Architecture](../../docs/GENERIC_PIPELINE_ARCHITECTURE.md)
