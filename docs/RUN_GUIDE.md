# Complete Application Run Guide

Comprehensive guide to running and testing **every component** of the GIS Architecture Agent.

---

## 🚀 Quick Start

### 1. Run the Full Web Application
```bash
# Main Streamlit app
streamlit run app.py

# Or use the provided script
./run_webapp.sh
```

**Access at**: http://localhost:8501

### 2. Run All Tests
```bash
# Run complete test suite
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

---

## 🗺️ Application Components Map

### **Main App** ([app.py](app.py))
- Homepage with regulation search
- Natural language query interface
- Building rights calculator
- Plan search functionality

**Test it manually:**
```bash
streamlit run app.py
```

Then try:
- ✅ Search for regulations: "parking requirements in Tel Aviv"
- ✅ Search for plans by PLAN_ID
- ✅ Calculate building rights for a location
- ✅ Test Hebrew queries: "תקנות חניה"

---

### **Page 1: Map Viewer** ([pages/1_📍_Map_Viewer.py](pages/1_📍_Map_Viewer.py))
Interactive map visualization of:
- Planning schemes
- TAMA zones
- Building locations
- Coordinate conversion (ITM ↔ WGS84)

**Test it manually:**
1. Navigate to "Map Viewer" page
2. ✅ Select feature types (Plans, TAMA, Buildings)
3. ✅ Filter by municipality
4. ✅ Click markers for details
5. ✅ Test coordinate conversion
6. ✅ Verify Hebrew text displays correctly

**Features to test:**
- Map renders correctly
- Markers appear for selected types
- Popups show feature details
- Filters work (municipality, plan type)
- Statistics update correctly

---

### **Page 2: Plan Analyzer** ([pages/2_📐_Plan_Analyzer.py](pages/2_📐_Plan_Analyzer.py))
Visual analysis tools for:
- Building rights calculations
- Plot coverage analysis
- Compliance checking
- Plan upload & AI-powered analysis

**Test it manually:**
1. Navigate to "Plan Analyzer" page
2. ✅ Enter project details (name, location, plot size)
3. ✅ Select zone type (R1, R2, C1, M1)
4. ✅ Adjust building parameters (floors, coverage)
5. ✅ View analysis charts
6. ✅ Check compliance indicators
7. ✅ Upload plan documents for AI analysis (in Upload & Analyze tab)

**Features to test:**
- Parameter inputs work
- Charts render (Plotly graphs)
- Compliance calculations correct
- Floor area ratios accurate
- Plan upload and vision analysis works

---

### **Page 3: Data Management** ([pages/3_💾_Data_Management.py](pages/3_💾_Data_Management.py))
Data administration interface:
- Vector database statistics
- iPlan data fetching
- Data source management
- Cache clearing

**Test it manually:**
1. Navigate to "Data Management" page
2. ✅ View vector database statistics
3. ✅ Reload data sources
4. ✅ Test iPlan API connection
5. ✅ View cached data
6. ✅ Clear cache
7. ✅ Import sample data

**Features to test:**
- Statistics display correctly
- Reload button works
- iPlan connection status
- Cache operations work
- Sample data imports successfully

---

## 🧪 Automated Testing Map

### **Test Suite 1: Vector Database Integration**
File: [tests/test_vectordb_integration.py](tests/test_vectordb_integration.py)

```bash
# Run all vector DB tests
pytest tests/test_vectordb_integration.py -v

# Run specific test class
pytest tests/test_vectordb_integration.py::TestChromaDBPersistence -v
pytest tests/test_vectordb_integration.py::TestVectorSearch -v
```

**What it tests:**
- ✅ ChromaDB file persistence (4 tests)
- ✅ Database connection (4 tests)
- ✅ Repository integration (4 tests)
- ✅ Service integration (3 tests)
- ✅ Data quality (4 tests)
- ✅ Semantic search (5 tests)

**Total:** 24 tests

---

### **Test Suite 2: iPlan Integration**
File: [tests/test_iplan_integration.py](tests/test_iplan_integration.py)

```bash
# Run all iPlan tests
pytest tests/test_iplan_integration.py -v

# Run specific test class
pytest tests/test_iplan_integration.py::TestHebrewSupport -v
pytest tests/test_iplan_integration.py::TestDatabasePopulation -v
```

**What it tests:**
- ✅ Database population (3 tests)
- ✅ Hebrew language support (6 tests - parametrized)
- ✅ iPlan data quality (4 tests)
- ✅ Data diversity (4 tests)
- ✅ Search relevance (3 tests)
- ✅ Metadata integrity (4 tests)

**Total:** 24 tests

---

## 🎯 Test By Feature Area

### **Search & Query**
```bash
# Test semantic search
pytest tests/test_vectordb_integration.py::TestVectorSearch -v

# Test Hebrew search
pytest tests/test_iplan_integration.py::TestHebrewSupport -v

# Test search relevance
pytest tests/test_iplan_integration.py::TestSearchRelevance -v
```

### **Data Storage**
```bash
# Test persistence
pytest tests/test_vectordb_integration.py::TestChromaDBPersistence -v

# Test database connection
pytest tests/test_vectordb_integration.py::TestChromaDBConnection -v

# Test population
pytest tests/test_iplan_integration.py::TestDatabasePopulation -v
```

### **Data Quality**
```bash
# Test data quality
pytest tests/test_vectordb_integration.py::TestDataQuality -v

# Test iPlan quality
pytest tests/test_iplan_integration.py::TestIPlanDataQuality -v

# Test metadata
pytest tests/test_iplan_integration.py::TestMetadataIntegrity -v
```

---

## 🔍 Test By Marker

```bash
# Run all integration tests
pytest -m integration -v

# Run only vector DB tests
pytest -m vectordb -v

# Run only iPlan tests
pytest -m iplan -v

# Skip slow tests
pytest -m "not slow" -v

# Combine markers
pytest -m "integration and vectordb" -v
```

---

## 📊 Coverage Analysis

### Generate Coverage Report
```bash
# Run with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term

# Open HTML report
open htmlcov/index.html
```

### Check Specific Modules
```bash
# Test specific module coverage
pytest tests/ --cov=src.application.services --cov-report=term

# Test infrastructure coverage
pytest tests/ --cov=src.infrastructure --cov-report=term

# Test data management coverage
pytest tests/ --cov=src.data_management --cov-report=term
```

---

## 🛠️ Backend Services Testing

### **Data Pipeline CLI**
```bash
# Run generic data pipeline
python -m src.data_pipeline.cli.pipeline load iplan

# Load from specific source
python -m src.data_pipeline.cli.pipeline load iplan --limit 50

# Check pipeline status
python -m src.data_pipeline.cli.pipeline status
```

### **Data Management CLI**
```bash
# Run data management script
python scripts/data_cli.py list

# Import sample data
python scripts/import_sample_data.py

# Manage vector database
python -m src.vectorstore.manager stats
```

---

## 🌐 End-to-End Testing Workflow

### **Complete System Test**
```bash
# 1. Run all automated tests
pytest tests/ -v --cov=src

# 2. Start the web app
streamlit run app.py

# 3. Manual testing checklist:
```

**Main App (Homepage):**
- [ ] Search regulations with English query
- [ ] Search regulations with Hebrew query (תקנות חניה)
- [ ] Search for specific plan (PLAN_ID)
- [ ] Calculate building rights
- [ ] Verify results display correctly

**Map Viewer Page:**
- [ ] Map loads and displays
- [ ] Markers appear for different feature types
- [ ] Click marker shows popup with details
- [ ] Filters work (municipality, type)
- [ ] Coordinate conversion works
- [ ] Statistics update correctly

**Plan Analyzer Page:**
- [ ] Input project parameters
- [ ] Charts render correctly
- [ ] Building rights calculations work
- [ ] Compliance indicators accurate
- [ ] Floor visualization displays
- [ ] Report generation works

**Data Management Page:**
- [ ] Statistics display
- [ ] Database info loads
- [ ] iPlan connection works
- [ ] Reload button functions
- [ ] Cache operations work
- [ ] Sample data import works

---

## 🎭 Performance Testing

### **Load Testing**
```bash
# Test with multiple concurrent searches
python -c "
from src.infrastructure.factory import get_factory
import time

factory = get_factory()
service = factory.get_regulation_query_service()

# Run 100 searches
start = time.time()
for i in range(100):
    service.query_regulations('parking')
end = time.time()

print(f'100 searches: {end-start:.2f}s')
print(f'Average: {(end-start)/100*1000:.2f}ms per search')
"
```

### **Database Performance**
```bash
# Test vector search performance
python -c "
from src.infrastructure.factory import get_factory
import time

factory = get_factory()
repo = factory.get_regulation_repository()

queries = ['parking', 'building height', 'zoning', 'residential']
for query in queries:
    start = time.time()
    results = repo.search(query, limit=10)
    duration = (time.time() - start) * 1000
    print(f'{query}: {duration:.2f}ms ({len(results)} results)')
"
```

---

## 📈 Monitoring & Debugging

### **Enable Debug Logging**
```bash
# Run with debug logging
STREAMLIT_LOG_LEVEL=debug streamlit run app.py

# Or in pytest
pytest tests/ -v -s --log-cli-level=DEBUG
```

### **Check Database Status**
```bash
# Verify ChromaDB
python -c "
from src.infrastructure.factory import ApplicationFactory
factory = ApplicationFactory()
repo = factory.get_regulation_repository()
stats = repo.get_statistics()
print(f'Total regulations: {stats.total_regulations}')
print(f'Last updated: {stats.last_updated}')
"
```

### **Validate Data**
```bash
# Check vector store
python -c "
from pathlib import Path
db_path = Path('data/vectorstore/chroma.sqlite3')
print(f'Database exists: {db_path.exists()}')
print(f'Database size: {db_path.stat().st_size / 1024 / 1024:.2f} MB')
"
```

---

## 🔧 Troubleshooting

### **Tests Failing?**
```bash
# Clear cache and retry
rm -rf data/cache/*
rm -rf data/vectorstore/*
pytest tests/ -v

# Run tests one at a time
pytest tests/test_vectordb_integration.py::TestChromaDBPersistence -v -s
```

### **Web App Not Loading?**
```bash
# Check port availability
lsof -i :8501

# Kill existing Streamlit processes
pkill -f streamlit

# Restart
streamlit run app.py
```

### **No Search Results?**
```bash
# Verify database has data
python -c "
from src.infrastructure.factory import get_factory
factory = get_factory()
repo = factory.get_regulation_repository()
print(repo.get_statistics())
"

# Repopulate if needed
python populate_real_data.py
```

---

## 📋 Complete Testing Checklist

### Automated Tests (Run Once)
- [ ] `pytest tests/ -v` - All 48 tests
- [ ] `pytest -m vectordb -v` - Vector DB tests
- [ ] `pytest -m iplan -v` - iPlan tests
- [ ] `pytest --cov=src` - Coverage report

### Manual Web Testing (Run for each deployment)
- [ ] Homepage loads
- [ ] Search with English query works
- [ ] Search with Hebrew query works
- [ ] Map Viewer page renders
- [ ] Plan Analyzer page works
- [ ] Data Management page functional
- [ ] All charts/visualizations render
- [ ] Navigation between pages works
- [ ] Error handling graceful

### Performance Testing (Run periodically)
- [ ] Search response < 500ms
- [ ] Page load time < 2s
- [ ] Map renders < 3s
- [ ] Database queries < 100ms

### Data Validation (Run after data updates)
- [ ] Database has content
- [ ] Hebrew text displays correctly
- [ ] Search returns relevant results
- [ ] Metadata complete
- [ ] No duplicate entries

---

## 🎉 Success Criteria

Your system is fully functional when:

✅ **All automated tests pass** (43+ out of 48)
✅ **Web app starts** without errors
✅ **All 4 pages load** successfully
✅ **Search returns results** (English + Hebrew)
✅ **Maps render** with markers
✅ **Charts display** correctly
✅ **Database has data** (10+ regulations)
✅ **No console errors** in browser
✅ **Performance acceptable** (<500ms searches)

---

## 📚 Additional Resources

- **Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Data Management**: [docs/DATA_MANAGEMENT.md](docs/DATA_MANAGEMENT.md)
- **Vector DB**: [docs/VECTOR_DB_MANAGEMENT.md](docs/VECTOR_DB_MANAGEMENT.md)
- **Quick Start**: [docs/QUICK_START.md](docs/QUICK_START.md)
- **Test Documentation**: [tests/README.md](tests/README.md)
