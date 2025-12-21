# Unified Data Pipeline Documentation

## 🎯 Overview

The **Unified Data Pipeline** is a complete solution for building and maintaining the vector database from iPlan/Mavat data. It replaces the previous fragmented approach with a single, maintainable system.

### Key Innovation: Selenium-Based WAF Bypass

Instead of relying on LLM tools (like `fetch_webpage`), we use **Selenium with headless Chrome** to access iPlan/Mavat data. This approach:

- ✅ **Bypasses WAF protection** - Acts like a real browser
- ✅ **Handles JavaScript challenges** - Can execute client-side code
- ✅ **More reliable** - No dependency on AI assistant tools
- ✅ **Maintainable** - Standard web automation approach
- ✅ **Cacheable** - Smart caching reduces redundant requests

---

## 🏗️ Architecture

### Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Unified Data Pipeline                         │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐     ┌──────────────┐
│   Selenium   │      │   Document   │     │   Vision     │
│   Fetcher    │──────│   Service    │─────│   Service    │
└──────────────┘      └──────────────┘     └──────────────┘
        │                     │                     │
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────────────────────────────────────────────────┐
│                    Vector Database                        │
│                   (ChromaDB + Metadata)                   │
└──────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. Discovery (Selenium)
   ├─ iPlan ArcGIS API → Plans metadata
   ├─ Cache responses (7 days)
   └─ Return plan features

2. Document Fetching (Selenium)
   ├─ Navigate to Mavat portal
   ├─ Extract document links
   ├─ Download PDFs/DWGs
   └─ Cache documents (30 days)

3. Vision Processing
   ├─ Convert PDF → Images
   ├─ Run Gemini analysis
   ├─ Extract regulations
   ├─ Parse building rights
   └─ Cache analysis (90 days)

4. Vector DB Indexing
   ├─ Create regulation entities
   ├─ Generate embeddings
   ├─ Store in ChromaDB
   └─ Update metadata
```

---

## 🚀 Quick Start

### Installation

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install ChromeDriver (macOS)
brew install --cask chromedriver

# 3. Or download manually
# https://chromedriver.chromium.org/

# 4. Set environment variables
export GEMINI_API_KEY="your_api_key_here"
```

### Basic Usage

```bash
# Check prerequisites
python build_vectordb.py --check

# Check current status
python build_vectordb.py --status

# Build with first 10 plans (testing)
python build_vectordb.py --max-plans 10

# Build with 100 plans
python build_vectordb.py --max-plans 100

# Clear and rebuild entire database
python build_vectordb.py --rebuild --max-plans 1000
```

### Advanced Usage

```bash
# Build from TAMA 35 service
python build_vectordb.py --service tama35 --max-plans 50

# Build from specific location (SQL WHERE clause)
python build_vectordb.py --where "municipality_name='ירושלים'" --max-plans 100

# Skip document fetching (metadata only, faster)
python build_vectordb.py --no-documents --max-plans 500

# Show browser window (debugging)
python build_vectordb.py --no-headless --max-plans 5

# Verbose logging
python build_vectordb.py --max-plans 10 -v
```

---

## 📁 File Structure

```
GISArchAgent/
├── build_vectordb.py                   # CLI entry point
├── src/
│   ├── data_management/
│   │   └── selenium_fetcher.py         # Selenium-based fetcher
│   ├── vectorstore/
│   │   ├── unified_pipeline.py         # Main pipeline orchestration
│   │   ├── health_check.py             # Vector DB validation
│   │   └── management_service.py       # Vector DB operations
│   └── infrastructure/
│       └── services/
│           ├── document_service.py     # Document fetching/processing
│           └── vision_service.py       # Gemini vision analysis
├── data/
│   ├── cache/
│   │   └── selenium/                   # API response cache
│   ├── vision_cache/                   # Document cache
│   └── vectorstore/
│       ├── chroma.sqlite3              # ChromaDB database
│       └── metadata.json               # Vector DB metadata
└── docs/
    ├── IPLAN_DATA_SOURCES_MAP.md       # Complete data mapping
    └── UNIFIED_PIPELINE.md             # This file
```

---

## 🔧 Configuration

### PipelineConfig

```python
from src.vectorstore.unified_pipeline import PipelineConfig

config = PipelineConfig(
    # Data source
    service_name='xplan',           # xplan, xplan_full, tama35, tama
    max_plans=None,                 # None = fetch all
    where_clause='1=1',             # SQL filter
    
    # Document fetching
    fetch_documents=True,
    max_documents_per_plan=10,
    
    # Vision processing
    process_documents=True,
    vision_model='gemini-1.5-flash-8b',
    
    # Vector DB
    rebuild_vectordb=False,         # True = clear and rebuild
    batch_size=100,
    
    # Caching
    use_cache=True,
    cache_dir=Path('data/cache'),
    
    # Performance
    headless=True,                  # Run browser headless
    max_workers=4,
)
```

### Available Services

| Service | URL | Description |
|---------|-----|-------------|
| `xplan` | `.../xplan_without_77_78/MapServer/1` | Main planning DB (default) |
| `xplan_full` | `.../Xplan/MapServer/0` | Full DB including sections 77/78 |
| `tama35` | `.../Tama35/MapServer/0` | TAMA 35 urban renewal plans |
| `tama` | `.../Tama/MapServer/0` | National outline plans |

---

## 💡 How It Works

### 1. Selenium Fetcher (`selenium_fetcher.py`)

The core innovation that bypasses WAF protection:

```python
from src.data_management.selenium_fetcher import IPlanSeleniumSource

# Use as context manager
with IPlanSeleniumSource(headless=True) as source:
    # Discover plans
    plans = source.discover_plans(max_plans=10)
    
    # Fetch plan details
    plan = source.fetch_plan_details(plan_id='12345')
    
    # Get documents from Mavat
    docs = source.fetch_plan_documents(mavat_plan_id='67890')
```

#### Anti-Detection Features

```python
# Browser fingerprinting
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_experimental_option('excludeSwitches', ['enable-automation'])

# Hide webdriver property
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

# Custom user agent
driver.execute_cdp_cmd('Network.setUserAgentOverride', {
    "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...'
})
```

### 2. Unified Pipeline (`unified_pipeline.py`)

Orchestrates the entire process:

```python
from src.vectorstore.unified_pipeline import UnifiedDataPipeline

pipeline = UnifiedDataPipeline(config=config)
stats = pipeline.run()

print(f"Indexed {stats.regulations_indexed} regulations")
```

#### Pipeline Phases

**Phase 0: Clear (if rebuild)**
```python
if config.rebuild_vectordb:
    vectordb_service.clear()
```

**Phase 1: Discovery**
```python
plans = iplan_source.discover_plans(
    service_name=config.service_name,
    max_plans=config.max_plans,
    where=config.where_clause
)
```

**Phase 2: Processing**
```python
for plan in plans:
    # 2.1: Fetch documents
    documents = fetch_plan_documents(plan)
    
    # 2.2: Process with vision
    regulations = process_documents(documents)
    
    # 2.3: Index in vector DB
    index_regulations(regulations)
```

**Phase 3: Finalize**
```python
stats.end_time = datetime.now()
stats.save('data/cache/pipeline_stats.json')
```

### 3. Smart Caching Strategy

Three-tier caching for optimal performance:

```python
# Tier 1: API Response Cache (7 days)
# - Raw ArcGIS responses
# - Fast re-indexing without API calls
cache_file = f"data/cache/selenium/{hash(url)}.json"

# Tier 2: Document Cache (30 days)
# - Downloaded PDFs/DWGs
# - Avoid re-downloading large files
doc_cache = f"data/vision_cache/{plan_id}/{doc_name}"

# Tier 3: Analysis Cache (90 days)
# - Vision analysis results
# - Expensive to regenerate
analysis_cache = f"data/vision_cache/{plan_id}/analysis.json"
```

### 4. Health Check Integration

The pipeline automatically validates the vector DB:

```python
from src.vectorstore.health_check import VectorDBHealthChecker

checker = VectorDBHealthChecker()
result = checker.check_health()

if result.status == 'critical':
    # Trigger rebuild
    pipeline.run(rebuild=True)
```

---

## 📊 Statistics Tracking

The pipeline tracks comprehensive statistics:

```python
@dataclass
class PipelineStats:
    # Discovery
    plans_discovered: int = 0
    plans_processed: int = 0
    plans_failed: int = 0
    
    # Documents
    documents_found: int = 0
    documents_downloaded: int = 0
    documents_processed: int = 0
    documents_failed: int = 0
    
    # Extraction
    regulations_extracted: int = 0
    building_rights_extracted: int = 0
    
    # Vector DB
    regulations_indexed: int = 0
    indexing_failed: int = 0
    
    # Performance
    cache_hits: int = 0
    cache_misses: int = 0
    duration_seconds: float = 0
```

Stats are saved to `data/cache/pipeline_stats.json` after each run.

---

## 🎯 Use Cases

### 1. Initial Database Build

```bash
# Build with first 1000 plans
python build_vectordb.py --max-plans 1000

# Expected time: ~2-3 hours
# Expected size: ~500MB-1GB
```

### 2. Incremental Updates

```bash
# Add new plans (no rebuild)
python build_vectordb.py --where "last_update_date > 1704067200000" --max-plans 100

# Only new/updated plans since date
```

### 3. Testing & Development

```bash
# Quick test with 5 plans, visible browser
python build_vectordb.py --max-plans 5 --no-headless -v

# Skip vision processing for faster testing
python build_vectordb.py --max-plans 20 --no-vision
```

### 4. Specialized Datasets

```bash
# Build Jerusalem plans only
python build_vectordb.py --where "municipality_name='ירושלים'" --max-plans 500

# Build TAMA 35 plans
python build_vectordb.py --service tama35
```

### 5. Full Rebuild

```bash
# Clear and rebuild from scratch
python build_vectordb.py --rebuild

# Warning: This will delete existing data!
```

---

## 🐛 Troubleshooting

### Issue: ChromeDriver not found

**Error:**
```
WebDriverException: Message: 'chromedriver' executable needs to be in PATH
```

**Solution:**
```bash
# macOS
brew install --cask chromedriver

# Verify
chromedriver --version
```

### Issue: WAF still blocking

**Error:**
```
HTTP 302 redirect to /error.htm
```

**Solution:**
1. Check if you're using `SeleniumFetcher` (not direct `requests`)
2. Try with visible browser: `--no-headless`
3. Add delays: Increase `time.sleep()` values
4. Update user agent string

### Issue: Vision service fails

**Error:**
```
google.api_core.exceptions.PermissionDenied: API key not valid
```

**Solution:**
```bash
# Set Gemini API key
export GEMINI_API_KEY="your_key_here"

# Verify
echo $GEMINI_API_KEY
```

### Issue: Slow performance

**Symptoms:**
- Takes too long
- High memory usage

**Solutions:**
```bash
# 1. Enable headless mode
python build_vectordb.py --max-plans 100  # headless by default

# 2. Skip documents for faster metadata indexing
python build_vectordb.py --no-documents --max-plans 500

# 3. Use smaller batches
python build_vectordb.py --max-plans 50  # run multiple times

# 4. Clear old cache
rm -rf data/cache/selenium/*
```

### Issue: ChromaDB errors

**Error:**
```
sqlite3.OperationalError: database is locked
```

**Solution:**
```bash
# 1. Close all app instances
# 2. Remove lock file
rm data/vectorstore/chroma.sqlite3-journal

# 3. Rebuild database
python build_vectordb.py --rebuild --max-plans 10
```

---

## 🔄 Maintenance

### Regular Updates

```bash
# Weekly: Add new/updated plans
python build_vectordb.py --where "last_update_date > $(date -d '7 days ago' +%s)000"

# Monthly: Check health and refresh if needed
python build_vectordb.py --status
```

### Cache Management

```bash
# Clear API response cache (7 days retention)
find data/cache/selenium -mtime +7 -delete

# Clear old documents (30 days)
find data/vision_cache -mtime +30 -delete

# Clear old analysis (90 days)
find data/vision_cache -name "analysis.json" -mtime +90 -delete
```

### Health Monitoring

```bash
# Check status regularly
python build_vectordb.py --status

# Expected output:
# Status: HEALTHY
# Regulation count: 5247
# Last updated: 2024-01-15
```

---

## 📈 Performance Benchmarks

Based on testing with first 100 plans:

| Metric | Value |
|--------|-------|
| **Discovery** | ~30s (100 plans) |
| **Document Fetching** | ~5s per plan |
| **Vision Processing** | ~10s per document |
| **Vector DB Indexing** | ~1s per regulation |
| **Total Time** | ~2-3 hours (1000 plans) |
| **Cache Hit Rate** | ~80% (after initial run) |
| **Memory Usage** | ~500MB peak |
| **Disk Usage** | ~1GB (1000 plans) |

---

## 🚦 Status Monitoring

The pipeline integrates with the health check system:

```python
from src.vectorstore.health_check import VectorDBHealthChecker

checker = VectorDBHealthChecker()
result = checker.check_health()

# Status levels
if result.status == 'healthy':
    # ✅ All good
    pass
elif result.status == 'warning':
    # ⚠️ Low count or old data
    # Consider refreshing
    pass
elif result.status == 'critical':
    # ❌ Needs rebuild
    # Run: python build_vectordb.py --rebuild
    pass
```

See [VECTOR_DB_VALIDATION.md](VECTOR_DB_VALIDATION.md) for details.

---

## 🔗 Related Documentation

- [IPLAN_DATA_SOURCES_MAP.md](IPLAN_DATA_SOURCES_MAP.md) - Complete data source mapping
- [VECTOR_DB_VALIDATION.md](VECTOR_DB_VALIDATION.md) - Health check system
- [VISION_IMPLEMENTATION_SUMMARY.md](VISION_IMPLEMENTATION_SUMMARY.md) - Vision processing details
- [DOCUMENTATION_MAP.md](../DOCUMENTATION_MAP.md) - Master documentation index

---

## 💪 Key Advantages

### vs. LLM-Based Approach

| Aspect | LLM Approach | Selenium Approach |
|--------|-------------|-------------------|
| **Reliability** | ❌ Depends on AI tool | ✅ Standard automation |
| **WAF Bypass** | ⚠️ Sometimes works | ✅ Consistent |
| **Performance** | ❌ Slow, rate limited | ✅ Faster, cacheable |
| **Maintainability** | ❌ Black box | ✅ Clear code |
| **Cost** | ❌ API calls | ✅ Free (except vision) |
| **Debugging** | ❌ Hard to diagnose | ✅ Easy to debug |

### vs. Direct API Approach

| Aspect | Direct API | Selenium Approach |
|--------|-----------|-------------------|
| **WAF Issues** | ❌ Blocked (302) | ✅ Bypassed |
| **Speed** | ✅ Faster | ⚠️ Slower |
| **Setup** | ✅ Simple | ⚠️ Needs ChromeDriver |
| **JavaScript** | ❌ Can't execute | ✅ Full support |
| **Reliability** | ❌ Unstable | ✅ Reliable |

---

## 🎓 Best Practices

1. **Start small**: Test with `--max-plans 10` first
2. **Use cache**: Don't disable cache unless needed
3. **Monitor health**: Run `--status` regularly
4. **Incremental updates**: Don't rebuild unless necessary
5. **Backup data**: Save `data/vectorstore/` before rebuild
6. **Rate limiting**: Respect iPlan servers (built-in delays)
7. **Error handling**: Check logs for failed plans
8. **Resource usage**: Run during off-peak hours for large builds

---

## 🤝 Contributing

When extending the pipeline:

1. **Add new services**: Update `SERVICES` dict in `IPlanSeleniumSource`
2. **Custom extractors**: Extend `_extract_regulation_from_document()`
3. **New document types**: Update `DocumentProcessor`
4. **Performance optimization**: Add more caching layers
5. **Documentation**: Update this file and [IPLAN_DATA_SOURCES_MAP.md](IPLAN_DATA_SOURCES_MAP.md)

---

## 📝 License

Part of GISArchAgent project. See main README for license information.

---

**Last Updated**: 2024-01-15  
**Maintainer**: GISArchAgent Team  
**Status**: ✅ Production Ready
