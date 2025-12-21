# Generic Data Pipeline Architecture

## Overview

The data pipeline is now **completely generic** and supports multiple data sources through an abstract interface system. iPlan is just one implementation - you can easily add new sources without changing any core pipeline logic.

## Architecture

```
src/data_pipeline/
├── core/                      # Generic, source-agnostic components
│   ├── interfaces.py          # Abstract contracts (DataSource, DataLoader, etc.)
│   ├── pipeline.py            # Generic orchestrator
│   └── loader.py              # Generic VectorDB loader
├── sources/                   # Source-specific implementations
│   ├── iplan/                 # Israeli national planning
│   │   ├── source.py          # IPlanDataSource implementation
│   │   └── __init__.py
│   └── [future sources]/      # Add new sources here
└── cli/                       # Command-line tools
    └── pipeline.py            # Generic CLI
```

## Core Concepts

### 1. DataSource Interface

Any data source must implement this interface:

```python
class DataSource(ABC):
    def get_name(self) -> str:
        """Return source identifier"""
    
    def discover(self, limit: Optional[int]) -> Iterator[Dict[str, Any]]:
        """Discover available records"""
    
    def fetch_details(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Fetch complete details for a record"""
    
    def parse_record(self, raw_data: Dict) -> DataRecord:
        """Parse raw data into standardized DataRecord"""
```

### 2. DataRecord

Standardized container for any data:

```python
@dataclass
class DataRecord:
    id: str                    # Unique identifier
    title: str                 # Human-readable title
    content: str               # Searchable content
    source: str                # Source system name
    metadata: Dict[str, Any]   # Additional structured data
    fetched_at: datetime       # When fetched
```

### 3. GenericPipeline

Source-agnostic orchestrator:

1. **Discovery**: Call `source.discover()` to get raw records
2. **Parsing**: Convert each record to `DataRecord` via `source.parse_record()`
3. **Loading**: Pass `DataRecord` objects to loader
4. **Caching**: Optionally cache discovery results

### 4. VectorDBLoader

Generic loader that works with any `DataRecord`:

```python
class VectorDBLoader(DataLoader):
    def load(self, records: List[DataRecord]) -> Dict[str, Any]:
        """Convert DataRecords to Regulation entities and store in ChromaDB"""
```

## Usage

### Using the CLI

```bash
# Run iPlan pipeline
python src/data_pipeline/cli/pipeline.py run --source iplan --limit 1000

# List available sources
python src/data_pipeline/cli/pipeline.py list-sources

# Show statistics
python src/data_pipeline/cli/pipeline.py stats
```

### Programmatic Usage

```python
from src.data_pipeline import (
    GenericPipeline,
    ConsolePipelineObserver,
    PipelineConfig,
    IPlanDataSource,
    VectorDBLoader,
)
from src.infrastructure.repositories.chroma_repository import ChromaRegulationRepository
from src.infrastructure.services.cache_service import FileCacheService

# Create components
cache = FileCacheService()
source = IPlanDataSource(cache=cache)
repo = ChromaRegulationRepository()
loader = VectorDBLoader(repo)
observer = ConsolePipelineObserver()

# Create pipeline
pipeline = GenericPipeline(
    source=source,
    loader=loader,
    observer=observer
)

# Configure and run
config = PipelineConfig(
    max_records=1000,
    batch_size=50,
    skip_cache=False,
)

result = pipeline.run(config)
print(f"Loaded {result.records_loaded} regulations in {result.duration:.2f}s")
```

### Using PipelineRegistry

For managing multiple sources:

```python
from src.data_pipeline import PipelineRegistry

# Create registry
registry = PipelineRegistry()

# Register sources
registry.register_source("iplan", IPlanDataSource())
registry.register_source("mavat", MavatDataSource())  # Future source

# Register loaders
registry.register_loader("vectordb", VectorDBLoader(repo))

# Create pipeline dynamically
pipeline = registry.create_pipeline(
    source_name="iplan",
    loader_name="vectordb"
)
```

## Adding a New Data Source

To add a new data source (e.g., MAVAT, CSV file, another API):

1. **Create source directory**:
   ```
   src/data_pipeline/sources/mavat/
   ├── __init__.py
   └── source.py
   ```

2. **Implement DataSource**:
   ```python
   from src.data_pipeline.core.interfaces import DataSource, DataRecord
   
   class MavatDataSource(DataSource):
       def get_name(self) -> str:
           return "MAVAT"
       
       def discover(self, limit: Optional[int]) -> Iterator[Dict[str, Any]]:
           # Fetch from MAVAT API
           ...
       
       def fetch_details(self, record_id: str) -> Optional[Dict[str, Any]]:
           # Fetch specific plan details
           ...
       
       def parse_record(self, raw_data: Dict) -> DataRecord:
           # Convert MAVAT format to DataRecord
           ...
   ```

3. **Register in CLI**:
   ```python
   # In cli/pipeline.py
   mavat_source = MavatDataSource(cache=cache)
   registry.register_source("mavat", mavat_source)
   ```

4. **Use it**:
   ```bash
   python src/data_pipeline/cli/pipeline.py run --source mavat --limit 500
   ```

**That's it!** No changes to core pipeline logic needed.

## Benefits

✅ **Extensibility**: Add new sources without touching core code  
✅ **Testability**: Each component is independently testable  
✅ **Maintainability**: Clear separation of concerns  
✅ **Reusability**: Same loader works with any source  
✅ **Flexibility**: Mix and match sources and loaders  

## Migration from Old Architecture

### Old Way (iPlan-specific)
```python
from src.data_pipeline.pipeline_manager import DataPipelineManager

manager = DataPipelineManager(repository)
stats = manager.run_full_pipeline(max_records=1000)
```

### New Way (Generic)
```python
from src.data_pipeline import GenericPipeline, PipelineConfig, IPlanDataSource, VectorDBLoader

pipeline = GenericPipeline(
    source=IPlanDataSource(),
    loader=VectorDBLoader(repository)
)
result = pipeline.run(PipelineConfig(max_records=1000))
```

## Legacy Scripts (To Be Removed)

The following scripts in the main directory are now **obsolete** and can be removed after migration:

- ❌ `bootstrap_metadata.py` - Use generic pipeline instead
- ❌ `bootstrap_iplan_metadata.py` - Use generic pipeline instead  
- ❌ `add_iplan_regulations_simple.py` - Use generic pipeline instead
- ❌ `load_iplan_100_regulations.py` - Use generic pipeline instead
- ❌ `fetch_and_save_iplan_data.py` - Use IPlanDataSource instead
- ❌ `pipeline_cli.py` - Moved to `src/data_pipeline/cli/pipeline.py`

Legacy services (still available but deprecated):
- `src/data_pipeline/discovery_service.py` - Replaced by IPlanDataSource
- `src/data_pipeline/indexing_service.py` - Replaced by VectorDBLoader
- `src/data_pipeline/detail_fetcher.py` - Integrated into IPlanDataSource
- `src/data_pipeline/pipeline_manager.py` - Replaced by GenericPipeline

## Testing

```python
# Test with mock source
class MockDataSource(DataSource):
    def get_name(self) -> str:
        return "Mock"
    
    def discover(self, limit: Optional[int]) -> Iterator[Dict[str, Any]]:
        for i in range(limit or 10):
            yield {"id": f"mock_{i}", "title": f"Test {i}"}
    
    def parse_record(self, raw_data: Dict) -> DataRecord:
        return DataRecord(
            id=raw_data["id"],
            title=raw_data["title"],
            content=f"Content for {raw_data['title']}",
            source="Mock",
            metadata={},
            fetched_at=datetime.now()
        )

# Use in tests
pipeline = GenericPipeline(
    source=MockDataSource(),
    loader=mock_loader
)
```

## Next Steps

1. ✅ Generic architecture implemented
2. ✅ iPlan source migrated to new architecture
3. ✅ CLI tool created
4. ✅ VectorDBInitializer updated
5. ⏳ Remove obsolete scripts from main directory
6. ⏳ Add more data sources (MAVAT, etc.)
7. ⏳ Update documentation throughout codebase
