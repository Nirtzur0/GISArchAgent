# Vector Database Management Guide

## Overview

The GIS Architecture Agent now includes **automatic vector database initialization and management** for storing and retrieving planning regulations using semantic search.

## What Changed

### Before
- ❌ Vector DB had to be manually created with `populate_real_data.py`
- ❌ No validation or health checks
- ❌ App would fail silently if DB was missing
- ❌ No way to update regulations

### After
- ✅ **Automatic initialization** on first use
- ✅ **Health checks** detect empty or missing DB
- ✅ **Auto-population** with sample regulations
- ✅ **Management UI** in Data Management page
- ✅ **Update mechanisms** for adding/modifying regulations

## Quick Start

### Method 1: Automatic (Recommended)

Just run the app - the vector DB initializes automatically:

```bash
./run_webapp.sh
```

The first time you query regulations:
1. Factory checks if vector DB is initialized
2. If empty, auto-populates with 10 sample regulations
3. Ready to use immediately!

### Method 2: During Setup

The setup script now initializes the vector DB:

```bash
./setup.sh
```

This creates the database during initial setup.

### Method 3: Manual via UI

Navigate to **💾 Data Management** page → **🗄️ Vector DB** tab:
- Click "🔄 Check & Initialize"
- System checks status and initializes if needed

## Features

### 1. Health Checks

The system continuously monitors vector DB health:

```python
from src.infrastructure.factory import get_factory

factory = get_factory()
status = factory.get_vectordb_status()

# Returns:
# {
#   "initialized": True/False,
#   "total_regulations": 10,
#   "status": "ready",
#   "health": "healthy"
# }
```

### 2. Automatic Initialization

When the factory creates a regulation repository:
- Checks if DB has data
- If empty, auto-populates with sample regulations
- Logs status for monitoring

```python
# Happens automatically when you use regulation services
factory = get_factory()
service = factory.get_regulation_query_service()  # DB initialized here
```

### 3. Sample Regulations

Initial DB includes 10 comprehensive regulations:
- Building height regulations
- Parking requirements
- Setback requirements
- Floor area ratio (FAR)
- Lot coverage
- Green building standards
- Accessibility requirements
- Fire safety
- Noise control
- Signage regulations

### 4. Management UI

**Data Management Page → Vector DB Tab**

Features:
- 📊 **Status Dashboard**: View initialization status, regulation count, health
- 🔄 **Check & Initialize**: Manually trigger initialization
- 🔨 **Rebuild Database**: Reset with fresh sample data (with confirmation)
- ➕ **Add Regulation**: Form to add new regulations
- 🔍 **Search**: Test semantic search
- 📥 **Import/Export**: JSON file operations

### 5. Programmatic Management

```python
from src.infrastructure.factory import get_factory
from src.vectorstore.management_service import VectorDBManagementService

# Get service
factory = get_factory()
repo = factory.get_regulation_repository()
service = VectorDBManagementService(repo)

# Check status
status = service.get_status()

# Add regulation
from src.domain.entities.regulation import RegulationType

service.add_regulation(
    title="My Custom Regulation",
    content="Full regulation text here...",
    reg_type=RegulationType.LOCAL,
    jurisdiction="Tel Aviv",
    summary="Brief summary"
)

# Search
results = service.search_regulations("parking", limit=5)

# Import from file
service.import_from_file("regulations.json")

# Export to file
service.export_to_file("backup.json")

# Rebuild (caution!)
service.rebuild_database()
```

## Architecture

### Components

```
ApplicationFactory
  └─> get_regulation_repository()
       └─> ChromaRegulationRepository
            ├─> is_initialized() [Health Check]
            ├─> add_regulation()
            └─> add_regulations_batch()

VectorDBInitializer
  ├─> check_and_initialize()
  ├─> initialize_with_samples()
  └─> get_initialization_status()

VectorDBManagementService
  ├─> get_status()
  ├─> add_regulation()
  ├─> search_regulations()
  ├─> import_from_file()
  ├─> export_to_file()
  └─> rebuild_database()
```

### Data Flow

```
App Startup
    ↓
Factory.get_regulation_repository()
    ↓
ChromaRegulationRepository created
    ↓
Factory._ensure_vectordb_initialized()
    ↓
VectorDBInitializer.check_and_initialize()
    ↓
[If empty] → initialize_with_samples()
    ↓
10 sample regulations added
    ↓
✓ Ready for use
```

## File Locations

- **Vector DB**: `data/vectorstore/chroma.sqlite3`
- **Initialization Module**: `src/vectorstore/initializer.py`
- **Management Service**: `src/vectorstore/management_service.py`
- **Repository**: `src/infrastructure/repositories/chroma_repository.py`

## JSON Import Format

To import regulations from a JSON file:

```json
[
  {
    "id": "reg_unique_id",
    "type": "local",
    "title": "Regulation Title",
    "content": "Full regulation text...",
    "summary": "Brief summary",
    "jurisdiction": "national",
    "metadata": {
      "custom_field": "value"
    }
  }
]
```

## Troubleshooting

### Vector DB Not Initializing

**Problem**: DB remains empty after startup

**Solutions**:
1. Check logs for initialization errors
2. Manually initialize via Data Management page
3. Check permissions on `data/vectorstore/` directory
4. Try rebuilding database

```bash
# Check logs
streamlit run app.py 2>&1 | grep -i vector

# Manual initialization
python3 -c "
from src.infrastructure.factory import get_factory
from src.vectorstore.initializer import VectorDBInitializer

factory = get_factory()
repo = factory.get_regulation_repository()
initializer = VectorDBInitializer(repo)
print(initializer.get_initialization_status())
initializer.initialize_with_samples()
"
```

### Search Returns No Results

**Problem**: Semantic search finds nothing

**Causes**:
1. DB is empty
2. Query doesn't match content
3. Embeddings not generated

**Solutions**:
1. Check initialization status
2. Try broader search terms
3. Rebuild database to regenerate embeddings

### Import Fails

**Problem**: JSON import doesn't work

**Check**:
- File is valid JSON
- Has required fields (`title`, `content`)
- Encoding is UTF-8
- File isn't too large

## Best Practices

### 1. Always Check Status

Before bulk operations:
```python
status = service.get_status()
if not status['initialized']:
    service.initialize_if_needed()
```

### 2. Backup Before Rebuild

Rebuilding destroys all data:
```python
# Export first
service.export_to_file("backup.json")

# Then rebuild
service.rebuild_database()

# Import custom data back if needed
service.import_from_file("custom_regulations.json")
```

### 3. Use Batch Operations

For multiple regulations:
```python
# Better
service.add_regulations_batch(regulations_list)

# Instead of
for reg in regulations_list:
    service.add_regulation(...)
```

### 4. Monitor Health

In production, regularly check health:
```python
status = service.get_status()
if status['health'] != 'healthy':
    # Alert or auto-fix
    service.initialize_if_needed()
```

## Migration Guide

### Existing Installations

If you have an existing installation:

1. **Pull latest code**
2. **Run setup** (will initialize vector DB):
   ```bash
   ./setup.sh
   ```

3. **Or just run the app** (auto-initializes):
   ```bash
   ./run_webapp.sh
   ```

4. **Optionally add your custom regulations**:
   - Via UI: Data Management → Vector DB → Add Regulation
   - Via file: Import JSON with your regulations

### Custom Regulations

If you had custom regulations in the old system:

1. Export them to JSON format (see JSON Import Format above)
2. Import via UI or programmatically:
   ```python
   service.import_from_file("my_regulations.json")
   ```

## Future Enhancements

Planned improvements:
- [ ] Scheduled auto-updates from external sources
- [ ] Version control for regulations
- [ ] Multi-language support
- [ ] Advanced filtering and faceting
- [ ] Regulation change tracking
- [ ] Automatic regulation extraction from PDFs

## API Reference

### VectorDBInitializer

```python
class VectorDBInitializer:
    def check_and_initialize() -> bool
    def initialize_with_samples() -> bool
    def get_initialization_status() -> dict
```

### VectorDBManagementService

```python
class VectorDBManagementService:
    def get_status() -> dict
    def initialize_if_needed() -> bool
    def add_regulation(...) -> bool
    def add_regulations_batch(data: List[dict]) -> dict
    def search_regulations(query: str, ...) -> List[Regulation]
    def get_regulation_by_id(id: str) -> Optional[Regulation]
    def update_regulation(id: str, updates: dict) -> bool
    def delete_regulation(id: str) -> bool
    def import_from_file(path: str) -> dict
    def export_to_file(path: str, ...) -> bool
    def rebuild_database() -> bool
```

### ChromaRegulationRepository

```python
class ChromaRegulationRepository:
    def is_initialized() -> bool
    def add_regulation(reg: Regulation) -> bool
    def add_regulations_batch(regs: List[Regulation]) -> int
    def search(...) -> List[Regulation]
    def get_statistics() -> dict
```

## Support

For issues or questions:
1. Check this guide
2. View logs for error details
3. Use Data Management page for diagnostics
4. See `docs/DATA_MANAGEMENT.md` for related data operations
