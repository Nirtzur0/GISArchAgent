# Quick Start \ud83d\ude80

Get up and running in 5 minutes!

## Installation

```bash
# Install everything you need
pip install -r requirements.txt

# Set up your environment
cp .env.example .env
# Open .env and add your GEMINI_API_KEY (you'll need this for vision analysis)
```

## Initialize Data

```bash
# Load up the regulations database
python scripts/populate_regulations.py
```

## Run the App

```bash
# Start the Streamlit app
streamlit run app.py
```

That's it! Open your browser and start exploring.

## Using It in Your Code

Here's the basic pattern you'll use everywhere:

```python
from src.infrastructure.factory import get_factory
from src.application.dtos import PlanSearchQuery

# Get the factory (this is your entry point)
factory = get_factory()

# Grab a service
plan_service = factory.get_plan_search_service()

# Use it!
query = PlanSearchQuery(location=\"\u05ea\u05dc \u05d0\u05d1\u05d9\u05d1\", max_results=10)
result = plan_service.search_plans(query)

# Check what you got
for analyzed_plan in result.plans:
    plan = analyzed_plan.plan
    print(f\"{plan.name} - {plan.get_display_status()}\")
    
    if analyzed_plan.vision_analysis:
        print(f\"  Vision: {analyzed_plan.vision_analysis.description}\")
```

## Common Things You'll Want to Do

### Search for Plans

```python
from src.infrastructure.factory import get_factory
from src.application.dtos import PlanSearchQuery

factory = get_factory()
service = factory.get_plan_search_service()

# By location
query = PlanSearchQuery(
    location=\"\u05ea\u05dc \u05d0\u05d1\u05d9\u05d1\",
    include_vision_analysis=True,  # Get AI analysis of plan images
    max_results=10
)
result = service.search_plans(query)

# By specific plan ID
query = PlanSearchQuery(plan_id=\"101-0524683\")
result = service.search_plans(query)

# By keyword
query = PlanSearchQuery(keyword=\"\u05e4\u05d9\u05e0\u05d5\u05d9 \u05d1\u05d9\u05e0\u05d5\u05d9\")
result = service.search_plans(query)
```

### Ask About Regulations

```python
from src.infrastructure.factory import get_factory
from src.application.dtos import RegulationQuery

factory = get_factory()
service = factory.get_regulation_query_service()

query = RegulationQuery(
    question=\"What are the parking requirements for residential buildings?\",
    max_results=5,
    location=\"\u05ea\u05dc \u05d0\u05d1\u05d9\u05d1\"  # Optional: filter by location
)

result = service.query(query)

print(result.answer)

# View sources
for reg in result.regulations:
    print(f"- {reg.title} ({reg.type.value})")
    print(f"  {reg.summary}")
```

### Calculate Building Rights

```python
from src.infrastructure.factory import get_factory
from src.application.dtos import BuildingRightsQuery

factory = get_factory()
service = factory.get_building_rights_service()

query = BuildingRightsQuery(
    plot_size=500.0,
    zone_type="residential_r2",
    location="תל אביב"
)

result = service.calculate_building_rights(query)

rights = result.building_rights

print(f"Building area: {rights.get_available_building_area():.0f} sqm")
print(f"Coverage: {rights.coverage_percent}%")
print(f"FAR: {rights.floor_area_ratio}")
print(f"Max height: {rights.max_height_meters}m")
print(f"Parking: {rights.parking_requirement} spots")

# Check compliance
is_compliant = rights.is_compliant_height(15.0)
print(f"15m height compliant: {is_compliant}")
```

## Architecture Overview

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│  (Streamlit UI, CLI, API endpoints)     │
└─────────────────┬───────────────────────┘
                  │ Uses DTOs
┌─────────────────▼───────────────────────┐
│        Application Layer                │
│  (Services: orchestrate use cases)      │
│  - PlanSearchService                    │
│  - RegulationQueryService               │
│  - BuildingRightsService                │
└─────────────────┬───────────────────────┘
                  │ Uses Interfaces
┌─────────────────▼───────────────────────┐
│         Domain Layer                    │
│  (Entities, Value Objects, Interfaces)  │
│  - Plan, Regulation, Analysis           │
│  - BuildingRights, Geometry             │
│  - IPlanRepository, IRegulationRepo     │
└─────────────────┬───────────────────────┘
                  │ Implemented by
┌─────────────────▼───────────────────────┐
│      Infrastructure Layer               │
│  (Concrete implementations)             │
│  - IPlanGISRepository                   │
│  - ChromaRegulationRepository           │
│  - GeminiVisionService                  │
│  - FileCacheService                     │
└─────────────────────────────────────────┘
```

## Key Concepts

### 1. Factory Pattern
The `ApplicationFactory` manages all dependencies:

```python
# Grab the factory (think of it as your service desk)
factory = get_factory()

# Get whatever services you need
plan_service = factory.get_plan_search_service()
reg_service = factory.get_regulation_query_service()
rights_service = factory.get_building_rights_service()

# You can also get the lower-level stuff if needed
plan_repo = factory.get_plan_repository()
reg_repo = factory.get_regulation_repository()
vision_service = factory.get_vision_service()
cache_service = factory.get_cache_service()
```

### Repositories
These are your data access layer - they hide the messy API/database stuff:

```python
# The interface (what we promise)
class IPlanRepository(ABC):
    @abstractmethod
    def get_by_id(self, plan_id: str) -> Optional[Plan]:
        pass

# The implementation (how we actually do it)
class IPlanGISRepository(IPlanRepository):
    def get_by_id(self, plan_id: str) -> Optional[Plan]:
        # Talks to the iPlan API
        ...
```

### Services
Services are where the magic happens - they coordinate everything:

```python
class PlanSearchService:
    def __init__(self, plan_repository, vision_service, cache_service):
        self.plan_repo = plan_repository
        self.vision = vision_service
        self.cache = cache_service
    
    def search_plans(self, query: PlanSearchQuery) -> PlanSearchResult:
        # Search, cache, analyze with vision, return results
        ...
```

### DTOs (Data Transfer Objects)
These are just clean containers for moving data around:

```python
@dataclass
class PlanSearchQuery:
    plan_id: Optional[str] = None
    location: Optional[str] = None
    keyword: Optional[str] = None
    include_vision_analysis: bool = False
    max_results: int = 10

@dataclass
class PlanSearchResult:
    plans: List[AnalyzedPlan]
    total_found: int
    execution_time_ms: int
```

## Where Everything Lives

```
src/
├── domain/                  # Pure business logic
│   ├── entities/           # Business entities
│   │   ├── plan.py
│   │   ├── regulation.py
│   │   └── analysis.py
│   ├── value_objects/      # Immutable values
│   │   ├── building_rights.py
│   │   └── geometry.py
│   └── repositories/       # Repository interfaces
│       └── __init__.py
│
├── application/            # Use cases
│   ├── dtos.py            # Data transfer objects
│   └── services/          # Application services
│       ├── plan_search_service.py
│       ├── regulation_query_service.py
│       └── building_rights_service.py
│
├── infrastructure/         # External integrations
│   ├── repositories/      # Repository implementations
│   │   ├── iplan_repository.py
│   │   └── chroma_repository.py
│   ├── services/          # External services
│   │   ├── vision_service.py
│   │   └── cache_service.py
│   └── factory.py         # Dependency injection
│
└── presentation/           # UI layer (to be refactored)
    ├── app_refactored.py  # New Streamlit app
    └── pages/             # Streamlit pages
```

## Testing

### Unit Tests (Domain)
```python
def test_plan_is_approved():
    plan = Plan(
        id="123",
        name="Test Plan",
        status=PlanStatus.APPROVED
    )
    assert plan.is_approved() == True
```

### Integration Tests (Application)
```python
def test_plan_search_service():
    mock_repo = MockPlanRepository()
    service = PlanSearchService(mock_repo, None, None)
    
    query = PlanSearchQuery(plan_id="123")
    result = service.search_plans(query)
    
    assert len(result.plans) > 0
```

### E2E Tests (Infrastructure)
```python
def test_iplan_repository():
    repo = IPlanGISRepository()
    plan = repo.get_by_id("101-0524683")
    
    assert plan is not None
    assert plan.name != ""
```

## Troubleshooting

### Factory Not Initialized
```python
# Make sure to initialize factory first
factory = get_factory()
```

### Missing API Key
```python
# Set in .env
GEMINI_API_KEY=your_key_here

# Or pass to factory
factory = ApplicationFactory(gemini_api_key="your_key")
```

### ChromaDB Not Found
```python
# Initialize with correct path
factory = ApplicationFactory(
    chroma_persist_dir="data/vectorstore"
)
```

### Cache Issues
```python
# Clear cache if needed
cache = factory.get_cache_service()
cache.clear_all()
```

## Best Practices

### 1. Use the Factory
Always get services from the factory, never instantiate directly:

```python
# ✅ Good
factory = get_factory()
service = factory.get_plan_search_service()

# ❌ Bad
service = PlanSearchService(...)  # Don't do this
```

### 2. Use DTOs for Input/Output
Always use DTOs at service boundaries:

```python
# ✅ Good
query = PlanSearchQuery(location="תל אביב")
result = service.search_plans(query)

# ❌ Bad
result = service.search_plans("תל אביב")  # Don't pass strings directly
```

### 3. Handle Errors
Always handle potential errors:

```python
try:
    result = service.search_plans(query)
    if result.total_found == 0:
        print("No plans found")
except Exception as e:
    print(f"Error: {e}")
```

### 4. Check Optional Results
Many methods return Optional types:

```python
plan = repo.get_by_id("123")
if plan:
    print(plan.name)
else:
    print("Plan not found")
```

## Performance Tips

### 1. Cache Results
The cache service is automatic, but you can control TTL:

```python
cache = factory.get_cache_service()
cache.set("my_key", data, ttl=3600)  # 1 hour
```

### 2. Limit Results
Always specify reasonable limits:

```python
query = PlanSearchQuery(
    location="תל אביב",
    max_results=10  # Don't fetch everything
)
```

### 3. Reuse Factory
The factory uses singletons, but create it once per application:

```python
# At app startup
factory = get_factory()

# Reuse throughout app lifecycle
service1 = factory.get_plan_search_service()
service2 = factory.get_regulation_query_service()
```

## Next Steps

1. ✅ Read [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design
2. ✅ Read [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for what's been built
3. 🔄 Start using the services in your UI
4. 🔄 Add tests

## Questions?

Check the documentation:
- `docs/ARCHITECTURE.md` - Architecture guide
- `docs/IMPLEMENTATION_SUMMARY.md` - What's been built
- `docs/QUICK_START.md` - This file

Or explore the code:
- Domain entities in `src/domain/entities/`
- Application services in `src/application/services/`
- Infrastructure implementations in `src/infrastructure/`
