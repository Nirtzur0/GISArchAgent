# Software Architecture - GIS Architecture Agent

## Overview

The GIS Architecture Agent is designed using **Clean Architecture** principles with clear separation of concerns, dependency inversion, and professional OOP patterns suitable for an enterprise architecture firm.

## Design Principles

### 1. **Clean Architecture Layers**
- **Domain Layer**: Core business logic and entities (planning regulations, plans, zones)
- **Application Layer**: Use cases and orchestration (query processing, analysis workflows)
- **Infrastructure Layer**: External dependencies (databases, APIs, file systems)
- **Presentation Layer**: User interfaces (Web UI, CLI)

### 2. **SOLID Principles**
- **Single Responsibility**: Each class has one reason to change
- **Open/Closed**: Open for extension, closed for modification
- **Liskov Substitution**: Interfaces can be substituted
- **Interface Segregation**: Clients don't depend on unused interfaces
- **Dependency Inversion**: Depend on abstractions, not concretions

### 3. **Design Patterns**
- **Repository Pattern**: Data access abstraction
- **Factory Pattern**: Object creation
- **Strategy Pattern**: Interchangeable algorithms (LLM providers, search strategies)
- **Observer Pattern**: Event notifications
- **Singleton Pattern**: Shared resources (config, connections)

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Streamlit   │  │   CLI App    │  │   REST API   │     │
│  │   Web UI     │  │   Interface  │  │   (Future)   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                   APPLICATION LAYER                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Query Processing Service                     │  │
│  │  • Plan Search      • Regulation Query               │  │
│  │  • Vision Analysis  • Compliance Check               │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Agent Orchestration (LangGraph)              │  │
│  │  • Reasoning       • Tool Selection                  │  │
│  │  • Synthesis       • Context Management              │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                    DOMAIN LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Entities   │  │   Services   │  │ Repositories │     │
│  │              │  │              │  │  (Interfaces)│     │
│  │ • Plan       │  │ • Regulation │  │              │     │
│  │ • Regulation │  │   Service    │  │ • IPlanRepo  │     │
│  │ • Zone       │  │ • Vision     │  │ • VectorRepo │     │
│  │ • Analysis   │  │   Service    │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Data Access  │  │  External    │  │   Caching    │     │
│  │              │  │    APIs      │  │              │     │
│  │ • ChromaDB   │  │ • iPlan GIS  │  │ • Redis      │     │
│  │ • File System│  │ • OpenAI     │  │ • Memory     │     │
│  │              │  │ • Gemini     │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. **Domain Entities**

Clean business objects with no framework dependencies:

```python
# src/domain/entities/plan.py
@dataclass
class Plan:
    """Represents a planning scheme."""
    id: str
    name: str
    location: str
    status: PlanStatus
    zone_type: ZoneType
    geometry: Optional[Geometry]
    metadata: Dict[str, Any]
    
    def is_approved(self) -> bool:
        return self.status == PlanStatus.APPROVED
    
    def get_building_rights(self) -> BuildingRights:
        """Calculate building rights based on zone type."""
        pass

# src/domain/entities/regulation.py
@dataclass
class Regulation:
    """Represents a planning regulation."""
    id: str
    type: RegulationType
    title: str
    content: str
    effective_date: date
    jurisdiction: str
    
    def applies_to(self, location: str) -> bool:
        """Check if regulation applies to location."""
        pass
```

### 2. **Repository Interfaces** (Domain Layer)

Abstract data access - domain doesn't know about ChromaDB or iPlan:

```python
# src/domain/repositories/plan_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional

class IPlanRepository(ABC):
    """Interface for plan data access."""
    
    @abstractmethod
    def get_by_id(self, plan_id: str) -> Optional[Plan]:
        """Retrieve plan by ID."""
        pass
    
    @abstractmethod
    def search_by_location(self, location: str) -> List[Plan]:
        """Search plans by location."""
        pass
    
    @abstractmethod
    def search_by_keyword(self, keyword: str) -> List[Plan]:
        """Search plans by keyword."""
        pass

# src/domain/repositories/regulation_repository.py
class IRegulationRepository(ABC):
    """Interface for regulation data access."""
    
    @abstractmethod
    def search(self, query: str, filters: Dict) -> List[Regulation]:
        """Search regulations."""
        pass
    
    @abstractmethod
    def get_by_type(self, reg_type: RegulationType) -> List[Regulation]:
        """Get regulations by type."""
        pass
```

### 3. **Domain Services**

Business logic that doesn't belong to entities:

```python
# src/domain/services/regulation_service.py
class RegulationService:
    """Business logic for regulation analysis."""
    
    def __init__(self, repository: IRegulationRepository):
        self._repository = repository
    
    def find_applicable_regulations(
        self, 
        plan: Plan, 
        building_type: str
    ) -> List[Regulation]:
        """Find all regulations applicable to a plan."""
        regulations = []
        
        # National regulations (TAMA)
        regulations.extend(
            self._repository.get_by_type(RegulationType.TAMA)
        )
        
        # Regional regulations
        regional = self._repository.search(
            query=plan.location,
            filters={'type': 'regional'}
        )
        regulations.extend(regional)
        
        # Filter by applicability
        return [r for r in regulations if r.applies_to(plan.location)]
    
    def check_compliance(
        self, 
        plan: Plan, 
        regulations: List[Regulation]
    ) -> ComplianceReport:
        """Check plan compliance with regulations."""
        pass
```

### 4. **Application Services** (Use Cases)

Orchestrate domain logic and coordinate between layers:

```python
# src/application/services/plan_search_service.py
class PlanSearchService:
    """Application service for plan search use case."""
    
    def __init__(
        self,
        plan_repository: IPlanRepository,
        vision_service: IVisionService,
        cache_service: ICacheService
    ):
        self._plan_repo = plan_repository
        self._vision = vision_service
        self._cache = cache_service
    
    def search_plans_with_analysis(
        self,
        query: PlanSearchQuery
    ) -> PlanSearchResult:
        """
        Search plans and automatically analyze images.
        
        This is the main use case for architecture firms.
        """
        # 1. Search for plans
        plans = self._search_plans(query)
        
        # 2. Fetch images for each plan
        plans_with_images = self._fetch_plan_images(plans)
        
        # 3. Analyze with vision AI (cached)
        analyzed_plans = []
        for plan in plans_with_images:
            analysis = self._analyze_plan_image(plan)
            analyzed_plans.append(
                AnalyzedPlan(plan=plan, analysis=analysis)
            )
        
        # 4. Return comprehensive result
        return PlanSearchResult(
            plans=analyzed_plans,
            query=query,
            timestamp=datetime.now()
        )
    
    def _search_plans(self, query: PlanSearchQuery) -> List[Plan]:
        """Search based on query type."""
        if query.plan_id:
            plan = self._plan_repo.get_by_id(query.plan_id)
            return [plan] if plan else []
        elif query.location:
            return self._plan_repo.search_by_location(query.location)
        else:
            return self._plan_repo.search_by_keyword(query.keyword)
    
    def _analyze_plan_image(self, plan: Plan) -> VisionAnalysis:
        """Analyze plan image with caching."""
        cache_key = f"vision:{plan.id}"
        
        # Check cache first
        cached = self._cache.get(cache_key)
        if cached:
            return cached
        
        # Analyze and cache
        analysis = self._vision.analyze_plan(plan.image)
        self._cache.set(cache_key, analysis, ttl=86400)
        
        return analysis
```

### 5. **Infrastructure Implementations**

Concrete implementations of repository interfaces:

```python
# src/infrastructure/repositories/iplan_repository.py
class IPlanGISRepository(IPlanRepository):
    """iPlan ArcGIS REST API implementation."""
    
    def __init__(self, base_url: str, ssl_context: SSLContext):
        self._base_url = base_url
        self._ssl_context = ssl_context
        self._services = self._load_services()
    
    def get_by_id(self, plan_id: str) -> Optional[Plan]:
        """Fetch plan from iPlan ArcGIS."""
        response = self._query_service(
            'planning',
            where=f"PLAN_NUMBER = '{plan_id}'"
        )
        return self._map_to_entity(response) if response else None
    
    def search_by_location(self, location: str) -> List[Plan]:
        """Search iPlan by location."""
        response = self._query_service(
            'planning',
            where=f"CITY_NAME LIKE '%{location}%'"
        )
        return [self._map_to_entity(r) for r in response]
    
    def _map_to_entity(self, raw_data: Dict) -> Plan:
        """Map ArcGIS response to domain entity."""
        return Plan(
            id=raw_data['attributes']['PLAN_NUMBER'],
            name=raw_data['attributes']['PLAN_NAME'],
            location=raw_data['attributes']['CITY_NAME'],
            status=PlanStatus.from_string(
                raw_data['attributes']['PLAN_STATUS']
            ),
            zone_type=ZoneType.from_code(
                raw_data['attributes']['ZONE_CODE']
            ),
            geometry=Geometry.from_arcgis(raw_data['geometry']),
            metadata=raw_data['attributes']
        )

# src/infrastructure/repositories/vector_repository.py
class ChromaRegulationRepository(IRegulationRepository):
    """ChromaDB implementation for regulations."""
    
    def __init__(self, client: chromadb.Client, collection_name: str):
        self._client = client
        self._collection = client.get_or_create_collection(collection_name)
    
    def search(self, query: str, filters: Dict) -> List[Regulation]:
        """Vector similarity search."""
        results = self._collection.query(
            query_texts=[query],
            where=filters,
            n_results=10
        )
        return [self._map_to_entity(r) for r in results['documents'][0]]
```

## What Architecture Firms Actually Need

Based on industry analysis, we focus on **5 core workflows**:

### 1. **Quick Plan Lookup** ⚡
- Search by plan ID, location, or keyword
- Instant visual analysis
- Downloadable reports

### 2. **Regulation Research** 📚
- Natural language queries about regulations
- TAMA plan details
- Zoning requirements

### 3. **Building Rights Calculator** 📐
- Input plot size and zone
- Calculate max building area, height, parking
- Generate compliance checklist

### 4. **Visual Plan Analysis** 🎨
- Automatic AI analysis of plan images
- Text extraction (Hebrew/English)
- Zone identification

### 5. **Precedent Search** 🔍
- Find similar approved projects
- Historical data analysis
- Compare requirements

## Removed/Simplified Features

To maintain professional focus, we've removed or simplified:

❌ **Removed**:
- Overly complex example notebooks
- Redundant CLI features (focus on web UI)
- Multiple scraping approaches (unified one)
- Unused local project features (can be added later)

✅ **Simplified**:
- Single unified data access layer
- One vision provider (Gemini) as default
- Streamlined UI (4 focused pages instead of scattered features)
- Clear error handling and logging

## Error Handling Strategy

Professional error handling at each layer:

```python
# Domain Layer: Business rule violations
class RegulationNotApplicableError(DomainException):
    """Raised when regulation doesn't apply to location."""
    pass

# Application Layer: Use case failures
class PlanNotFoundException(ApplicationException):
    """Raised when plan cannot be found."""
    pass

# Infrastructure Layer: External system failures
class IPlanAPIError(InfrastructureException):
    """Raised when iPlan API fails."""
    pass

# Presentation Layer: User-friendly messages
@st.cache_data
def search_plans_safe(query: str) -> Result:
    try:
        return service.search_plans(query)
    except PlanNotFoundException:
        st.warning("No plans found. Try different search terms.")
    except IPlanAPIError:
        st.error("iPlan system temporarily unavailable.")
    except Exception as e:
        logger.exception("Unexpected error")
        st.error("An error occurred. Please try again.")
```

## Testing Strategy

```
tests/
├── unit/              # Fast, isolated tests
│   ├── domain/        # Entity and service tests
│   ├── application/   # Use case tests
│   └── infrastructure/# Repository tests (mocked)
├── integration/       # Component integration tests
│   ├── test_iplan_integration.py
│   ├── test_vector_store.py
│   └── test_vision_api.py
└── e2e/              # End-to-end user scenarios
    ├── test_plan_search.py
    ├── test_regulation_query.py
    └── test_vision_analysis.py
```

## Performance Considerations

### Caching Strategy
```
Level 1: Memory (LRU Cache)     - Hot data, sub-ms
Level 2: Redis (Future)         - Session data, <10ms  
Level 3: File System            - Vision analysis, <100ms
Level 4: Database               - Regulations, <500ms
```

### Optimization Targets
- Plan search: < 2 seconds
- Vision analysis: < 5 seconds (cached: < 100ms)
- Regulation query: < 1 second
- UI responsiveness: < 200ms

## Security Considerations

1. **API Key Management**: Environment variables, never in code
2. **Input Validation**: Sanitize all user inputs
3. **Rate Limiting**: Prevent API abuse
4. **Data Privacy**: No PII stored without consent
5. **SSL/TLS**: Secure external communications

## Deployment Architecture

```
Production Environment:
┌─────────────────────────────────────────┐
│         Load Balancer / CDN             │
└──────────────┬──────────────────────────┘
               │
┌──────────────┴──────────────────────────┐
│      Streamlit App (Container)          │
│  • Python 3.12                          │
│  • 2GB RAM                              │
│  • Auto-scaling                         │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┴──────────┬──────────────┐
    │                     │              │
┌───┴────┐          ┌────┴───┐    ┌────┴──────┐
│ChromaDB│          │ iPlan  │    │ OpenAI/   │
│(Local) │          │ API    │    │ Gemini    │
└────────┘          └────────┘    └───────────┘
```


## Future Enhancements

Potential improvements:

- Add Redis caching for better performance
- Implement REST API for external integrations
- Add advanced analytics and reporting
- Performance optimization and monitoring
- Add comprehensive test coverage


```
src/
├── domain/
│   ├── entities/
│   │   ├── plan.py
│   │   ├── regulation.py
│   │   ├── zone.py
│   │   └── analysis.py
│   ├── repositories/  # Interfaces only
│   │   ├── plan_repository.py
│   │   └── regulation_repository.py
│   ├── services/
│   │   ├── regulation_service.py
│   │   └── compliance_service.py
│   └── value_objects/
│       ├── geometry.py
│       └── building_rights.py
├── application/
│   ├── services/
│   │   ├── plan_search_service.py
│   │   ├── query_service.py
│   │   └── vision_service.py
│   ├── dtos/
│   │   ├── plan_search_query.py
│   │   └── search_result.py
│   └── interfaces/
│       └── cache_service.py
├── infrastructure/
│   ├── repositories/
│   │   ├── iplan_repository.py
│   │   └── chroma_repository.py
│   ├── cache/
│   │   └── file_cache.py
│   ├── external/
│   │   ├── iplan_client.py
│   │   └── vision_client.py
│   └── config/
│       └── settings.py
└── presentation/
    ├── web/           # Streamlit
    │   ├── app.py
    │   └── pages/
    ├── cli/           # Command line
    │   └── cli.py
    └── api/           # Future REST API
        └── routes.py
```

## Conclusion

This architecture provides:
- ✅ Clear separation of concerns
- ✅ Testable components
- ✅ Maintainable codebase
- ✅ Professional OOP design
- ✅ Focused on firm needs
- ✅ Scalable foundation

The architecture follows industry best practices while remaining practical for a small team to maintain and extend.
