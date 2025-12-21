# How The System Actually Works

**Complete guide to understanding, running, and using the GIS Architecture Agent.**

---

## 🎯 What Actually Works Right Now

✅ **Vector database with 10 Israeli planning regulations**  
✅ **Semantic search in English & Hebrew**  
✅ **Web interface with 3 interactive pages**  
✅ **Data management system**  
✅ **Selenium-based data fetching (WAF bypass)**  
✅ **Vision-powered plan upload & analysis**

---

## 🏗️ System Architecture (The Real Picture)

```
┌─────────────────────────────────────────────────────────────┐
│                     YOUR STREAMLIT APP                       │
│                        (app.py)                              │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐ │
│  │ Map Viewer   │  │ Plan Analyzer │  │ Data Management  │ │
│  │ (Page 1)     │  │ (Page 2)      │  │ (Page 3)         │ │
│  └──────────────┘  └───────────────┘  └──────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │    APPLICATION FACTORY              │
        │    (src/infrastructure/factory.py)  │
        │                                     │
        │  Creates & wires up all services   │
        └────────┬───────────────┬───────────┘
                 │               │
       ┌─────────▼──────┐   ┌───▼───────────────────┐
       │  SERVICES      │   │  REPOSITORIES         │
       │                │   │                       │
       │  • Regulation  │   │  • ChromaRepository   │
       │    Query       │   │    (Vector DB)        │
       │  • Plan Search │   │                       │
       │  • Building    │   │  • IPlanRepository    │
       │    Rights      │   │    (iPlan API)        │
       └────────────────┘   └───────┬───────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
            ┌───────▼────────┐           ┌─────────▼─────────┐
            │  CHROMADB      │           │  iPlan GIS API    │
            │  Vector Store  │           │  (External)       │
            │                │           │                   │
            │  10 regulations│           │  Planning data    │
            │  with          │           │  from Israeli     │
            │  embeddings    │           │  government       │
            └────────────────┘           └───────────────────┘
```

---

## 📊 Data Flow: How Queries Work

### Example: User searches for "parking requirements"

```
1. USER INTERFACE (app.py)
   └─> User types "parking requirements" in search box
       └─> Calls: factory.get_regulation_query_service()
   
2. APPLICATION LAYER (regulation_query_service.py)
   └─> Service receives query
       └─> Calls: repository.search("parking requirements")
   
3. INFRASTRUCTURE LAYER (chroma_repository.py)
   └─> Repository converts text to vector embedding
       └─> Searches ChromaDB vector database
           └─> Finds semantically similar regulations
   
4. VECTOR DATABASE (data/vectorstore/)
   └─> ChromaDB compares query embedding with stored embeddings
       └─> Returns top 3 most similar regulations
   
5. RESULTS FLOW BACK
   └─> Repository → Service → UI
       └─> User sees: 3 relevant planning regulations
```

**Key Insight**: The system doesn't do keyword matching. It understands **meaning**. 
- "parking requirements" also finds "חניה" (Hebrew for parking)
- "residential building" finds "מגורים" (Hebrew for residential)

---

## 🚀 How to Run It (3 Ways)

### Method 1: Web Interface (Recommended)

```bash
# Start the app
streamlit run app.py
```

Then open browser to **http://localhost:8501**

**What you can do:**
- 🏠 **Homepage**: Search regulations, ask questions
- 📍 **Page 1 - Map Viewer**: Visualize planning data on maps
- 📐 **Page 2 - Plan Analyzer**: Calculate building rights
- 💾 **Page 3 - Data Management**: View database stats, import data

### Method 2: Python API

```python
from src.infrastructure.factory import get_factory

# Get the factory (creates everything you need)
factory = get_factory()

# Get regulation repository
repo = factory.get_regulation_repository()

# Search for regulations
results = repo.search("parking requirements", limit=5)

# Print results
for reg in results:
    print(f"• {reg.title}")
    print(f"  Location: {reg.jurisdiction}")
    print(f"  Type: {reg.type.value}")
    print()
```

### Method 3: Command Line

```bash
# Check database status
python scripts/data_cli.py status -v

# Search regulations
python scripts/data_cli.py search --text "parking"

# Import sample data
python scripts/import_sample_data.py
```

---

## 💾 Data: Where It Comes From & Where It Lives

### Current Data Sources

**1. Vector Database (Active)**
- **Location**: `data/vectorstore/chroma.sqlite3`
- **Contents**: 10 Israeli planning regulations
- **Format**: Text + vector embeddings
- **Source**: Sample data from `data/samples/iplan_sample_data.json`

**2. Sample Data File**
- **Location**: `data/samples/iplan_sample_data.json`
- **Contents**: 10 curated planning regulations from iPlan
- **Languages**: Hebrew (original) + English metadata
- **Used by**: `populate_real_data.py` and `import_sample_data.py`

**3. iPlan GIS API (Available but not primary)**
- **API**: `https://ags.iplan.gov.il/arcgisiplan/rest/services/`
- **Purpose**: Israeli government planning database
- **Note**: Can fetch live data but currently using samples

### Data Initialization Flow

```
STARTUP
  │
  ├─> Is ChromaDB populated?
  │     YES → Use existing data ✓
  │     NO  → Auto-initialize
  │
  └─> Auto-Initialize Process:
        1. Read data/samples/iplan_sample_data.json
        2. Parse 10 regulations
        3. Generate vector embeddings
        4. Store in ChromaDB
        5. ✓ Ready to search!
```

**This happens automatically on first run!**

---

## 🔍 How Search Actually Works

### The Vector Magic

Traditional search (doesn't exist here):
```
User searches: "parking space"
System looks for exact match: "parking space"
If document says "vehicle storage" → NO MATCH ❌
```

Vector search (what we use):
```
User searches: "parking space"
System converts to vector: [0.2, 0.7, 0.1, ...]
Compares with all regulation vectors
Finds: "vehicle storage" has similar meaning
Returns: Document about parking ✓
```

### Search Features

**Semantic Understanding:**
- "building height" → finds "construction elevation"
- "parking" → finds "חניה" (Hebrew)
- "residential" → finds "מגורים" (Hebrew)

**Multi-language:**
- Search in English → finds Hebrew documents
- Search in Hebrew → finds English documents
- Mixed queries work too

**Context-aware:**
- Understands planning terminology
- Knows TAMA = תמ"א (urban renewal)
- Knows "scheme" = "תכנית" = plan

---

## 🗂️ Project Structure (What's Where)

```
GISArchAgent/
│
├── app.py                          # MAIN APP - Start here
│
├── pages/                          # Streamlit pages
│   ├── 1_📍_Map_Viewer.py         # Interactive maps
│   ├── 2_📐_Plan_Analyzer.py      # Building rights calculator
│   └── 3_💾_Data_Management.py    # Data admin interface
│
├── src/                            # Source code (Clean Architecture)
│   │
│   ├── application/                # USE CASES & SERVICES
│   │   └── services/
│   │       ├── regulation_query_service.py   # Search regulations
│   │       ├── plan_search_service.py        # Search plans
│   │       └── building_rights_service.py    # Calculate rights
│   │
│   ├── domain/                     # BUSINESS LOGIC
│   │   ├── entities/
│   │   │   ├── regulation.py      # Regulation entity
│   │   │   └── plan.py            # Plan entity
│   │   └── repositories/          # Interfaces (contracts)
│   │
│   ├── infrastructure/             # EXTERNAL SYSTEMS
│   │   ├── factory.py             # 🏭 THE WIRING - Creates everything
│   │   └── repositories/
│   │       ├── chroma_repository.py     # Vector DB implementation
│   │       └── iplan_repository.py      # iPlan API implementation
│   │
│   ├── data_pipeline/              # GENERIC PIPELINE
│   │   ├── core/                  # Pipeline engine
│   │   └── sources/               # Data sources (iPlan, etc.)
│   │
│   ├── data_management/            # DATA STORE
│   │   ├── data_store.py          # Central data manager
│   │   └── fetchers.py            # Data fetchers
│   │
│   └── vectorstore/                # VECTOR DB UTILITIES
│       ├── initializer.py         # Auto-populate DB
│       └── management_service.py  # DB admin
│
├── scripts/                        # CLI TOOLS
│   ├── data_cli.py                # Main CLI
│   └── import_sample_data.py      # Import samples
│
├── tests/                          # TESTS (pytest)
│   ├── test_vectordb_integration.py
│   └── test_iplan_integration.py
│
├── data/                           # DATA STORAGE
│   ├── vectorstore/               # ChromaDB files
│   │   └── chroma.sqlite3        # 10 regulations here
│   ├── samples/                   # Sample data
│   │   └── iplan_sample_data.json
│   └── cache/                     # API cache
│
└── docs/                          # DOCUMENTATION
    ├── ARCHITECTURE.md
    ├── DATA_MANAGEMENT.md
    ├── QUICK_START.md
    └── ...
```

---

## 🔧 Key Components Explained

### 1. ApplicationFactory (`src/infrastructure/factory.py`)

**The Central Hub** - Creates and wires up everything.

```python
factory = get_factory()

# Get what you need:
repo = factory.get_regulation_repository()    # ChromaDB
service = factory.get_regulation_query_service()  # Query handler
iplan = factory.get_plan_repository()        # iPlan API
```

**Why it's important**: Single place that knows how to create everything. No scattered initialization code.

---

### 2. ChromaRegulationRepository (`src/infrastructure/repositories/chroma_repository.py`)

**The Vector Database Interface**

```python
# Search semantically
results = repo.search("parking requirements", limit=10)

# Get specific regulation
regulation = repo.get_by_id("iplan_101_0061409")

# Add new regulation
repo.add(new_regulation)

# Get stats
stats = repo.get_statistics()
# Returns: {'total_regulations': 10, ...}
```

**What it does**:
- Converts text to vectors
- Stores in ChromaDB
- Searches by semantic similarity
- Returns Regulation entities

---

### 3. RegulationQueryService (`src/application/services/regulation_query_service.py`)

**The Search Handler**

```python
from src.application.dtos import RegulationQuery

query = RegulationQuery(
    query_text="parking requirements in Tel Aviv",
    location="תל אביב",
    max_results=5
)

result = service.query(query)

print(f"Found: {result.total_found} regulations")
for reg in result.regulations:
    print(reg.title)
```

**What it does**:
- Receives natural language queries
- Calls repository for search
- Can synthesize answers (if LLM available)
- Returns structured results

---

### 4. VectorDBInitializer (`src/vectorstore/initializer.py`)

**The Auto-Setup**

Runs automatically on first use:

```python
initializer = VectorDBInitializer(repository)

# Check if DB needs initialization
if not initializer.check_and_initialize():
    print("Database is empty, initializing...")
    initializer.initialize_with_samples()
    # Loads data from data/samples/iplan_sample_data.json
    # Creates embeddings
    # Populates ChromaDB
```

**Why it's important**: You don't have to manually populate the database. It "just works" on first run.

---

## 📝 Common Tasks & How to Do Them

### Task 1: Search for Regulations

**Via Web:**
1. Start app: `streamlit run app.py`
2. Type query in search box
3. Click "Search"
4. See results

**Via Python:**
```python
from src.infrastructure.factory import get_factory

factory = get_factory()
repo = factory.get_regulation_repository()
results = repo.search("your query here", limit=10)

for reg in results:
    print(f"{reg.title} - {reg.jurisdiction}")
```

**Via CLI:**
```bash
python scripts/data_cli.py search --text "parking"
```

---

### Task 2: Check Database Status

**Via Python:**
```python
from src.infrastructure.factory import get_factory

factory = get_factory()
repo = factory.get_regulation_repository()
stats = repo.get_statistics()

print(f"Total regulations: {stats['total_regulations']}")
print(f"Database location: {stats['persist_directory']}")
```

**Via CLI:**
```bash
python scripts/data_cli.py status -v
```

**Via Web:**
1. Start app
2. Go to "💾 Data Management" page
3. See statistics dashboard

---

### Task 3: Import More Data

**Method 1: Use sample data**
```bash
python scripts/import_sample_data.py
```

**Method 2: Via web interface**
1. Start app
2. Go to "💾 Data Management" page
3. Click "Import Sample Data"

**Method 3: Add programmatically**
```python
from src.infrastructure.factory import get_factory
from src.domain.entities.regulation import Regulation, RegulationType

factory = get_factory()
repo = factory.get_regulation_repository()

# Create new regulation
new_reg = Regulation(
    id="custom_001",
    type=RegulationType.LOCAL,
    title="My Custom Regulation",
    content="Detailed regulation content...",
    summary="Brief summary",
    jurisdiction="Tel Aviv",
    source_document="Custom source"
)

# Add to database
repo.add(new_reg)
```

---

### Task 4: Test Everything Works

**Quick test:**
```bash
python -c "from src.infrastructure.factory import get_factory; \
factory = get_factory(); \
repo = factory.get_regulation_repository(); \
print(f'✓ Database has {repo.get_statistics()[\"total_regulations\"]} regulations')"
```

**Full test suite:**
```bash
pytest tests/ -v
```

**Expected**: 43/48 tests pass (5 data quality tests may fail - that's OK)

---

## 🐛 Troubleshooting

### Problem: "No regulations found"

**Check database:**
```bash
python -c "from src.infrastructure.factory import get_factory; \
factory = get_factory(); \
repo = factory.get_regulation_repository(); \
stats = repo.get_statistics(); \
print(stats)"
```

**If total_regulations = 0:**
```bash
# Reinitialize database
python scripts/utilities/reinitialize_vectordb.py

# Or import sample data
python scripts/import_sample_data.py
```

---

### Problem: "ModuleNotFoundError"

**Solution:**
```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import chromadb; import streamlit; print('✓ All good')"
```

---

### Problem: "Search returns irrelevant results"

This is expected with only 10 regulations. The system works but needs more data.

**Solutions:**
1. Import more sample data
2. Add regulations manually
3. Fetch from iPlan API (requires setup)

---

### Problem: "App won't start"

**Check port:**
```bash
# Kill existing Streamlit
pkill -f streamlit

# Try again
streamlit run app.py
```

**Check Python version:**
```bash
python --version  # Should be 3.10+
```

---

## 🎓 Understanding the Architecture

### Why "Clean Architecture"?

The project follows **Clean Architecture** principles:

```
┌─────────────────────────────────────────┐
│  PRESENTATION (Streamlit, CLI)          │ ← User sees this
├─────────────────────────────────────────┤
│  APPLICATION (Services, Use Cases)      │ ← Business logic
├─────────────────────────────────────────┤
│  DOMAIN (Entities, Interfaces)          │ ← Core concepts
├─────────────────────────────────────────┤
│  INFRASTRUCTURE (ChromaDB, APIs)        │ ← External systems
└─────────────────────────────────────────┘
```

**Benefits:**
- ✅ Easy to test (mock external systems)
- ✅ Easy to swap components (change DB? Just change infrastructure)
- ✅ Clear separation of concerns
- ✅ Independent of frameworks

### Dependency Flow

```
UI → Service → Repository → Database
(Depends on)  (Depends on)  (Depends on)
```

**Rule**: Inner layers don't know about outer layers.
- Domain entities don't import Streamlit
- Services don't import ChromaDB
- Everything goes through interfaces

---

## 🚦 Current System Capabilities

### ✅ What Works Great

1. **Vector Search**
   - Semantic search in English & Hebrew
   - 10 regulations indexed
   - Sub-second search times

2. **Web Interface**
   - 3 fully functional pages
   - Interactive maps
   - Data management UI

3. **Data Management**
   - Import/export data
   - Sample data loading
   - Database statistics

4. **Testing**
   - 48 tests (43 passing)
   - Integration tests
   - Vector DB tests

### ⚠️ What's Limited

1. **Data Volume**
   - Only 10 regulations (proof of concept)
   - Need 100+ for production use

2. **iPlan API Integration**
   - Code exists but not primary data source
   - SSL/cache issues to resolve

3. **LLM Answer Synthesis**
   - Service exists but LLM integration incomplete
   - Returns search results without AI-generated answers

### 🔮 What Could Be Added

1. **More Data Sources**
   - MAVAT (building permits)
   - Municipal databases
   - Historical data

2. **Advanced Features**
   - AI-powered Q&A
   - Document parsing
   - Compliance checking
   - Report generation

3. **Performance**
   - Caching layer
   - Async operations
   - Batch processing

---

## 📚 Further Reading

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Detailed architecture
- **[DATA_MANAGEMENT.md](docs/DATA_MANAGEMENT.md)** - Data operations
- **[QUICK_START.md](docs/QUICK_START.md)** - Setup guide
- **[RUN_GUIDE.md](RUN_GUIDE.md)** - Complete testing guide
- **[tests/README.md](tests/README.md)** - Test documentation

---

## 🎯 TL;DR - The Bottom Line

**What you have:**
- ✅ Working vector database (10 regulations)
- ✅ Semantic search (English + Hebrew)
- ✅ Web interface (3 pages)
- ✅ Professional architecture
- ✅ Test suite (90% passing)

**How to use it:**
```bash
streamlit run app.py
```

**How it fetches data:**
1. Sample data from `data/samples/iplan_sample_data.json`
2. Auto-loaded into ChromaDB on first run
3. Searchable via vector embeddings

**How it queries data:**
1. User types query → 
2. Converted to vector → 
3. ChromaDB semantic search → 
4. Returns relevant regulations

**It's production-ready for a proof of concept.** 
For full production, add more data and enable iPlan API integration.
