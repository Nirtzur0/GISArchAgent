# 🏗️ GIS Architecture Agent - Complete System Flow

## 📋 Overview
The system follows Clean Architecture principles with clear separation between domain, application, infrastructure, and presentation layers.

---

## 🚀 1. APPLICATION STARTUP FLOW

### Step 1: User runs `streamlit run app.py`

### Step 2: App Initialization ([app.py](../app.py))
```
app.py (lines 1-100)
├─→ Import factory: from src.infrastructure.factory import get_factory
├─→ Set up Streamlit page config
├─→ Initialize session state:
│   ├─ factory (singleton)
│   ├─ query_history (list)
│   └─ current_answer (cache)
└─→ Load custom CSS
```

### Step 3: Factory Initialization ([src/infrastructure/factory.py](../src/infrastructure/factory.py))
```
get_factory()
├─→ Create ApplicationFactory instance
│   ├─ Load config from settings (src/config.py)
│   │   ├─ GEMINI_API_KEY from .env
│   │   ├─ Model settings (gemini-2.5-flash)
│   │   └─ Database paths
│   │
│   └─ Initialize empty singletons:
│       ├─ _regulation_repository = None
│       ├─ _llm_service = None
│       ├─ _vision_service = None
│       └─ _plan_repository = None
│
└─→ Return factory (singleton pattern)
```

---

## 🗄️ 2. VECTOR DATABASE INITIALIZATION FLOW

### Triggered by: First call to `factory.get_regulation_repository()`

```
get_regulation_repository()
├─→ Create ChromaRegulationRepository
│   ├─ Connect to ChromaDB (data/vectorstore)
│   ├─ Get or create "regulations" collection
│   └─ Set up embedding function
│
├─→ Run health check (lazy import to avoid circular dependency)
│   │
│   └─→ check_vectordb_health(repository)
│       ├─ Check if collection exists
│       ├─ Count regulations (currently: 10)
│       ├─ Check metadata (last_updated)
│       ├─ Determine status:
│       │   ├─ uninitialized (0 regs) → auto-init
│       │   ├─ critical (<10 regs or >90 days old)
│       │   ├─ warning (10-99 regs or >30 days old)
│       │   └─ healthy (≥100 regs, <30 days old)
│       │
│       └─ Return HealthResult:
│           ├─ status: "warning"
│           ├─ total_regulations: 10
│           ├─ issues: ["Low regulation count"]
│           └─ recommendations: ["Build more data"]
│
└─→ If status = 'uninitialized':
    └─→ VectorDBInitializer.initialize_with_pipeline()
        ├─ Load sample regulations (10 Israeli plans)
        ├─ Create Regulation entities
        └─ Index in ChromaDB
```

---

## 💬 3. USER QUERY FLOW (Main Feature)

### User types question in Streamlit UI and clicks "Ask"

```
User Input: "What are the parking requirements?"
    ↓
app.py (line ~250-280)
├─→ Create RegulationQuery DTO
│   ├─ query_text: "What are the parking requirements?"
│   └─ max_results: 5
│
├─→ Get regulation_query_service from factory
│   │
│   └─→ factory.get_regulation_query_service()
│       ├─→ Create RegulationQueryService
│       │   ├─ regulation_repository: ChromaRegulationRepository
│       │   └─ llm_service: GeminiLLMService
│       │       │
│       │       └─→ factory.get_llm_service()
│       │           ├─ Create GeminiLLMService
│       │           ├─ API key from .env
│       │           └─ Model: gemini-2.5-flash
│       │
│       └─→ Return service (cached singleton)
│
└─→ Execute query
    │
    └─→ regulation_service.query(query)
        │
        ├─→ Step 1: SEARCH REGULATIONS
        │   └─→ _search_regulations(query)
        │       ├─→ repository.search()
        │       │   ├─ Embed query text (OpenAI embeddings)
        │       │   ├─ Semantic search in ChromaDB
        │       │   ├─ Apply filters (location, type)
        │       │   └─ Return top 5 regulations
        │       │
        │       └─→ Returns: List[Regulation]
        │           [
        │             Regulation(title="הרחבת יח״ד ברח׳ אביעד 3"),
        │             Regulation(title="שינוי קו בניין..."),
        │             ...
        │           ]
        │
        ├─→ Step 2: SYNTHESIZE ANSWER (if LLM available)
        │   └─→ _synthesize_answer(query, regulations)
        │       │
        │       ├─→ Step 2a: Prepare context
        │       │   └─→ _prepare_context(regulations)
        │       │       └─ Format regulations into text:
        │       │           """
        │       │           Regulation 1: הרחבת יח״ד...
        │       │           Type: local_plan
        │       │           Content: תוספת קומה...
        │       │           ---
        │       │           Regulation 2: ...
        │       │           """
        │       │
        │       └─→ Step 2b: Generate answer with LLM
        │           └─→ llm_service.generate_answer(question, context)
        │               │
        │               └─→ GeminiLLMService.generate_answer()
        │                   ├─ Build prompt:
        │                   │   """
        │                   │   You are an expert in Israeli planning...
        │                   │   Context: [regulations]
        │                   │   Question: [user question]
        │                   │   """
        │                   │
        │                   ├─→ Call Gemini API
        │                   │   └─ client.models.generate_content()
        │                   │       ├─ model: gemini-2.5-flash
        │                   │       ├─ temperature: 0.1
        │                   │       └─ max_tokens: 1000
        │                   │
        │                   └─ Return synthesized answer
        │
        └─→ Return RegulationResult
            ├─ regulations: [List of 5 regulations]
            ├─ answer: "Based on the provided regulations..."
            ├─ total_found: 5
            └─ timestamp: 2025-12-22 01:30:00
```

### Display Results
```
app.py receives RegulationResult
├─→ Display answer in styled box
├─→ Show matching regulations
│   ├─ Title (Hebrew)
│   ├─ Type badge
│   └─ Content preview
│
└─→ Save to query history
```

---

## 🔄 4. VECTOR DATABASE BUILD FLOW

### User runs: `python3 scripts/build_vectordb_cli.py build --max-plans 100`

```
build_vectordb_cli.py
├─→ Parse CLI arguments (Click framework)
│   ├─ max_plans: 100
│   ├─ no_documents: False
│   └─ no_vision: False
│
├─→ Create PipelineConfig
│   ├─ service_name: 'xplan'
│   ├─ max_plans: 100
│   ├─ fetch_documents: True
│   └─ process_documents: True
│
└─→ Initialize UnifiedDataPipeline
    │
    └─→ UnifiedDataPipeline.__init__(config)
        ├─→ Create IPlanDataSource (lazy)
        │   └─→ IPlanDataSource(headless=True)
        │       ├─ Uses IPlanSeleniumSource internally
        │       └─→ SeleniumFetcher
        │           ├─ Initialize Chrome WebDriver
        │           ├─ Set anti-detection flags
        │           ├─ Configure user agent
        │           └─ Ready to bypass WAF
        │
        ├─→ Create GeminiVisionService (lazy)
        │   ├─ Get API key from .env
        │   └─ Initialize Gemini client
        │
        └─→ Create VectorDBManagementService (lazy)
            └─ ChromaRegulationRepository
```

### Pipeline Execution
```
pipeline.run()
│
├─→ PHASE 1: DISCOVER PLANS
│   └─→ iplan_source.discover(limit=100)
│       │
│       └─→ IPlanSeleniumSource.discover_plans()
│           ├─→ Build iPlan API URL
│           │   https://ags.iplan.gov.il/arcgisiplan/rest/services/
│           │   PlanningPublic/xplan/MapServer/0/query
│           │
│           ├─→ SeleniumFetcher.fetch_json()
│           │   ├─ Check cache first
│           │   ├─ If miss: Use Selenium
│           │   │   ├─ driver.get(url)
│           │   │   ├─ Wait for page load
│           │   │   ├─ Extract JSON from page
│           │   │   └─ Cache result (7 days)
│           │   └─ Parse GeoJSON response
│           │
│           └─→ Yield plan records:
│               {
│                 'attributes': {
│                   'pl_name': 'תוספת קומה...',
│                   'pl_number': '101-0057273',
│                   'pl_objectives': '...',
│                   'pl_url': 'https://mavat.iplan.gov.il/...',
│                   'district_name': 'ירושלים',
│                   ...
│                 },
│                 'geometry': {...}
│               }
│
├─→ PHASE 2: PROCESS EACH PLAN
│   └─→ For each plan:
│       │
│       ├─→ Extract metadata
│       │   ├─ Plan name (Hebrew)
│       │   ├─ Plan number
│       │   ├─ Objectives/essence
│       │   └─ Mavat URL
│       │
│       ├─→ If fetch_documents:
│       │   └─→ document_fetcher.fetch_from_mavat()
│       │       ├─ Parse Mavat URL
│       │       ├─ Download PDFs/images
│       │       └─ Cache in data/vision_cache/
│       │
│       ├─→ If process_documents:
│       │   └─→ vision_service.analyze_plan()
│       │       ├─ Convert PDF to images
│       │       ├─→ Call Gemini Vision API
│       │       │   └─ Extract regulations
│       │       └─ Return VisionAnalysis
│       │
│       └─→ Create Regulation entity
│           └─ Regulation(
│                 id='iplan_1000216487',
│                 title='תוספת קומה...',
│                 content='[full text]',
│                 type=RegulationType.LOCAL_PLAN,
│                 jurisdiction='ירושלים',
│                 ...
│             )
│
└─→ PHASE 3: INDEX IN VECTOR DB
    └─→ vectordb_service.add_regulations(regulations)
        ├─→ For each regulation:
        │   ├─ Generate embedding (OpenAI)
        │   └─ Add to ChromaDB collection
        │
        └─→ Update metadata
            ├─ Total count: 110
            ├─ Last updated: 2025-12-22
            └─ Save to metadata file
```

### Results
```
Pipeline Complete!
├─ Plans discovered: 100
├─ Plans processed: 100
├─ Regulations indexed: 100
└─ Duration: ~10 minutes
```

---

## 🏛️ 5. ARCHITECTURE LAYERS

```
┌─────────────────────────────────────────────────────┐
│           PRESENTATION LAYER                        │
│   ┌──────────────┐  ┌──────────────┐              │
│   │  app.py      │  │  CLI scripts │              │
│   │  (Streamlit) │  │              │              │
│   └──────────────┘  └──────────────┘              │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────┐
│           APPLICATION LAYER                         │
│   ┌─────────────────────────────────────────────┐  │
│   │ Services:                                    │  │
│   │  • RegulationQueryService                   │  │
│   │  • PlanSearchService                        │  │
│   │  • BuildingRightsService                    │  │
│   │  • PlanUploadService                        │  │
│   └─────────────────────────────────────────────┘  │
│   ┌─────────────────────────────────────────────┐  │
│   │ DTOs (Data Transfer Objects):               │  │
│   │  • RegulationQuery / RegulationResult       │  │
│   │  • PlanSearchQuery / PlanSearchResult       │  │
│   └─────────────────────────────────────────────┘  │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────┐
│           DOMAIN LAYER                              │
│   ┌─────────────────────────────────────────────┐  │
│   │ Entities:                                    │  │
│   │  • Regulation                                │  │
│   │  • Plan                                      │  │
│   │  • VisionAnalysis                           │  │
│   └─────────────────────────────────────────────┘  │
│   ┌─────────────────────────────────────────────┐  │
│   │ Value Objects:                               │  │
│   │  • BuildingRights                           │  │
│   │  • Geometry                                  │  │
│   └─────────────────────────────────────────────┘  │
│   ┌─────────────────────────────────────────────┐  │
│   │ Repository Interfaces:                       │  │
│   │  • IRegulationRepository                    │  │
│   │  • IPlanRepository                          │  │
│   └─────────────────────────────────────────────┘  │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────┐
│           INFRASTRUCTURE LAYER                      │
│   ┌─────────────────────────────────────────────┐  │
│   │ Repository Implementations:                  │  │
│   │  • ChromaRegulationRepository               │  │
│   │  • IPlanGISRepository                       │  │
│   └─────────────────────────────────────────────┘  │
│   ┌─────────────────────────────────────────────┐  │
│   │ Services:                                    │  │
│   │  • GeminiVisionService                      │  │
│   │  • GeminiLLMService                         │  │
│   │  • SeleniumFetcher                          │  │
│   │  • CacheService                             │  │
│   └─────────────────────────────────────────────┘  │
│   ┌─────────────────────────────────────────────┐  │
│   │ Factory:                                     │  │
│   │  • ApplicationFactory (wires everything)    │  │
│   └─────────────────────────────────────────────┘  │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────┐
│           EXTERNAL SYSTEMS                          │
│   ┌──────────┐  ┌──────────┐  ┌──────────────┐    │
│   │ ChromaDB │  │ iPlan    │  │ Gemini API   │    │
│   │ (Vector  │  │ GIS API  │  │ (Google AI)  │    │
│   │  Store)  │  │          │  │              │    │
│   └──────────┘  └──────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────┘
```

---

## 📦 6. KEY COMPONENTS

### Factory Pattern ([src/infrastructure/factory.py](../src/infrastructure/factory.py))
- **Purpose**: Single entry point for all services
- **Pattern**: Singleton for each service
- **Benefits**: 
  - Centralized dependency injection
  - Lazy initialization
  - Easy testing/mocking

### Repository Pattern ([src/infrastructure/repositories/](../src/infrastructure/repositories/))
- **ChromaRegulationRepository**: Vector DB operations
- **IPlanGISRepository**: iPlan API integration
- **Benefits**: 
  - Abstract data source
  - Swappable implementations
  - Clean separation

### Service Layer ([src/application/services/](../src/application/services/))
- **RegulationQueryService**: NL queries → answers
- **PlanSearchService**: Search iPlan data
- **Benefits**:
  - Business logic isolation
  - Reusable across interfaces

---

## 🔐 7. CONFIGURATION FLOW

```
.env file
├─ GEMINI_API_KEY=AIza...
├─ MODEL_NAME=gemini-2.5-flash
└─ LLM_PROVIDER=google
    ↓
src/config.py (Settings class)
├─ Load with pydantic_settings
├─ Validate environment variables
└─ Provide settings object
    ↓
ApplicationFactory.__init__()
├─ settings.gemini_api_key
├─ settings.model_name
└─ Pass to services
```

---

## 🎯 8. TYPICAL USER JOURNEY

1. **User opens app** → `streamlit run app.py`
2. **App initializes** → Factory creates singletons
3. **Vector DB checks health** → 10 regulations loaded
4. **User types question** → "What are parking requirements?"
5. **System searches** → Semantic search in ChromaDB
6. **System finds** → 5 relevant regulations
7. **LLM synthesizes** → Gemini creates answer
8. **User sees** → Clear answer + source regulations
9. **User can explore** → Click regulations for details

---

## 🚀 9. PERFORMANCE OPTIMIZATIONS

1. **Caching**:
   - Selenium responses: 7 days
   - Vision analysis: 30 days
   - Query results: Session-based

2. **Lazy Loading**:
   - Services created only when needed
   - ChromaDB connection on first query

3. **Singleton Pattern**:
   - One instance per service
   - Reused across requests

4. **Batch Processing**:
   - Vector DB bulk inserts
   - Parallel document processing

---

## 📊 10. DATA FLOW SUMMARY

```
User Question
    ↓
Streamlit UI (app.py)
    ↓
RegulationQueryService
    ↓
ChromaRegulationRepository
    ↓
ChromaDB (Vector Search)
    ↓
Top 5 Regulations
    ↓
GeminiLLMService
    ↓
Synthesized Answer
    ↓
Display to User
```

---

## 🔧 11. HOW TO RUN EVERYTHING

### Initial Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 3. Initialize vector database (one-time)
python3 scripts/build_vectordb_cli.py build --max-plans 10
```

### Running the Application
```bash
# Start the Streamlit web app
streamlit run app.py
# Opens at http://localhost:8501
```

### Building More Data
```bash
# Fetch 100 plans and build vector DB (takes ~10 mins)
python3 scripts/build_vectordb_cli.py build --max-plans 100

# Check database status
python3 scripts/quick_status.py
```

### Testing Components
```bash
# Test regulation search
python3 -c "
from src.infrastructure.factory import get_factory
factory = get_factory()
repo = factory.get_regulation_repository()
results = repo.search('parking requirements', limit=5)
for r in results:
    print(r.title)
"

# Test LLM service
python3 -c "
from src.infrastructure.factory import get_factory
factory = get_factory()
service = factory.get_regulation_query_service()
result = service.query('What are parking requirements?')
print(result.answer)
"
```

---

## 📚 12. FILE ORGANIZATION

```
GISArchAgent/
├─ app.py                        # Main Streamlit app
├─ requirements.txt              # Python dependencies
├─ .env                          # Environment config
│
├─ src/
│  ├─ config.py                  # Settings (Pydantic)
│  ├─ domain/                    # Business entities
│  ├─ application/               # Use cases/services
│  └─ infrastructure/            # External integrations
│     ├─ factory.py              # Dependency injection
│     ├─ repositories/           # Data access
│     └─ services/               # External services
│        ├─ llm_service.py       # Gemini LLM
│        ├─ vision_service.py    # Gemini Vision
│        └─ cache_service.py     # Caching
│
├─ scripts/                      # CLI tools
│  ├─ build_vectordb_cli.py     # Build vector DB
│  └─ quick_status.py            # Check DB health
│
├─ data/
│  ├─ vectorstore/               # ChromaDB files
│  ├─ cache/                     # Selenium cache
│  └─ vision_cache/              # Vision API cache
│
└─ docs/                         # Documentation
   ├─ SYSTEM_FLOW.md             # This file
   ├─ ARCHITECTURE.md            # Architecture details
   └─ QUICK_START.md             # Getting started
```

---

## 🎓 Summary

This system is a **Clean Architecture** application that:

1. **Fetches** Israeli planning regulations from iPlan using Selenium
2. **Processes** documents using Gemini Vision API
3. **Stores** regulations in ChromaDB vector database
4. **Searches** regulations using semantic search
5. **Synthesizes** answers using Gemini LLM
6. **Displays** results in Streamlit web interface

The architecture ensures:
- ✅ Clear separation of concerns
- ✅ Easy testing and mocking
- ✅ Swappable implementations
- ✅ Maintainable codebase
- ✅ Production-ready patterns
