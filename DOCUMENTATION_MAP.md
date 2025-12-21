# Documentation Map & Maintenance Guide

> **Master reference for all project documentation and when to update each file**

## 📋 Documentation Structure

All detailed documentation lives in the `docs/` folder. This file serves as your index.

---

## 🗂️ Core Documentation Files

### 1. **Architecture & System Design**

#### [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
**What**: Clean architecture layers, design patterns, system overview
**Update When**:
- Adding new domain entities
- Changing repository interfaces
- Modifying service layer structure
- Updating dependency injection patterns

#### [docs/HOW_IT_WORKS.md](docs/HOW_IT_WORKS.md)
**What**: Complete system explanation - data flow, search mechanics, components
**Update When**:
- Changing data pipeline workflow
- Modifying semantic search implementation
- Adding new major features
- Updating integration points

---

### 2. **Features & Capabilities**

#### [docs/VISION_FEATURES.md](docs/VISION_FEATURES.md)
**What**: Vision service features - document processing, upload & analyze
**Update When**:
- Modifying vision service capabilities
- Changing document processing workflow
- Updating upload service
- Adding new AI analysis features
- Changing supported file formats

#### [docs/VISION_IMPLEMENTATION_SUMMARY.md](docs/VISION_IMPLEMENTATION_SUMMARY.md)
**What**: Implementation details of vision features
**Update When**:
- Completing vision feature development
- Changing vision service architecture
- Updating document fetcher/processor
- Modifying upload workflow

#### [docs/GENERIC_PIPELINE_ARCHITECTURE.md](docs/GENERIC_PIPELINE_ARCHITECTURE.md)
**What**: Generic data pipeline architecture and design
**Update When**:
- Changing pipeline components
- Modifying data processing workflow
- Adding new data sources to pipeline
- Updating observers or loaders

#### [docs/IPLAN_DATA_SOURCES_MAP.md](docs/IPLAN_DATA_SOURCES_MAP.md) ✨ NEW
**What**: Complete mapping of all iPlan/Mavat data sources and innovative WAF bypass solutions
**Update When**:
- Discovering new iPlan API endpoints
- Adding new data source services
- Updating WAF bypass techniques
- Changing data structure mappings
- Documenting new document types

#### [docs/UNIFIED_PIPELINE.md](docs/UNIFIED_PIPELINE.md) ✨ NEW
**What**: Selenium-based unified data pipeline - architecture, configuration, usage
**Update When**:
- Modifying pipeline orchestration
- Changing Selenium fetcher implementation
- Updating caching strategies
- Adding new pipeline phases
- Changing configuration options
- Performance optimization changes

#### [docs/BUILD_VECTORDB_GUIDE.md](docs/BUILD_VECTORDB_GUIDE.md) ✨ NEW
**What**: Complete guide for building and maintaining the vector database
**Update When**:
- Adding new CLI commands
- Changing build workflow
- Updating troubleshooting steps
- Adding new usage examples
- Performance benchmarks change
- Maintenance procedures update

---

### 3. **Data & Storage**

#### [docs/VECTOR_DB_VALIDATION.md](docs/VECTOR_DB_VALIDATION.md)
**What**: Vector database health check system, validation mechanisms
**Update When**:
- Changing health check thresholds
- Adding new validation checks
- Modifying metadata tracking
- Updating auto-initialization logic

#### [docs/VECTOR_DB_MANAGEMENT.md](docs/VECTOR_DB_MANAGEMENT.md)
**What**: Vector database operations, maintenance, indexing strategies
**Update When**:
- Changing indexing methods
- Updating ChromaDB configuration
- Modifying regulation schema
- Adding new data sources

#### [docs/DATA_MANAGEMENT.md](docs/DATA_MANAGEMENT.md)
**What**: Data pipeline, fetching, caching, storage strategies
**Update When**:
- Modifying data pipeline architecture
- Changing cache strategies
- Updating iPlan data fetching
- Adding new data sources

#### [docs/README.md](docs/README.md)
**What**: Documentation folder overview and quick links
**Update When**:
- Adding new documentation files
- Reorganizing docs structure
- Major documentation updates

---

### 4. **Setup & Usage**

#### [docs/QUICK_START.md](docs/QUICK_START.md)
---

### 5. **Project Management**

These files are referenced but may not exist yet - create as needed:

#### docs/RUN_GUIDE.md (Future)
**What**: How to run, test, and use the system
**Update When**:
- Adding new run modes
- Changing CLI commands
- Updating test procedures
- Modifying web interface access

#### docs/INTEGRATION_SUMMARY.md (Future)
**What**: Integration points, APIs, service connections
**Update When**:
- Adding new external services
- Modifying API endpoints
- Changing authentication methods
- Updating service integrations

#### docs/COMPLETION_REPORT.md (Future)
**What**: Project completion status, implemented features
**Update When**:
- Completing major features
- Finishing development milestones
- Moving features from planned to implemented

#### docs/DATA_ACCESS_STATUS.md (Future)
**What**: Status of iPlan API access, workarounds, solutions
**Update When**:
- iPlan API access changes
- Finding new data access methods
- Updating workarounds

#### docs/IMPLEMENTATION_SUMMARY.md (Future
**What**: Status of iPlan API access, workarounds, solutions
**Update When**:
- iPlan API access changes
- Finding new data access methods
- Updating workarounds

#### [docs/IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md)
**What**: Overall implementation progress and technical decisions
**Update When**:
- Major architectural decisions made
- Significant refactoring completed
- Technology stack changes

---

## 🔄 Update Triggers by Component

### When Modifying Services

| Service Changed | Update These Docs |
|----------------|-------------------|
| `vision_service.py` | VISION_FEATURES.md, HOW_IT_WORKS.md |
| `document_service.py` | VISION_FEATURES.md, VISION_IMPLEMENTATION_SUMMARY.md |
| `plan_upload_service.py` | VISION_FEATURES.md, RUN_GUIDE.md |
| `health_check.py` | VECTOR_DB_VALIDATION.md, ARCHITECTURE.md |
| `chroma_repository.py` | VECTOR_DB_MANAGEMENT.md, ARCHITECTURE.md |

### When Modifying Infrastructure

| Component Changed | Update These Docs |
|------------------|-------------------|
| `factory.py` | ARCHITECTURE.md, HOW_IT_WORKS.md |
| `config.py` | QUICK_START.md, INTEGRATION_SUMMARY.md |
| Pipeline architecture | DATA_MANAGEMENT.md, HOW_IT_WORKS.md |
| Cache service | DATA_MANAGEMENT.md |

### When Adding Features

| Feature Type | Update These Docs |
|-------------|-------------------|
| New AI capability | VISION_FEATURES.md, HOW_IT_WORKS.md |
| New data source | DATA_MANAGEMENT.md, INTEGRATION_SUMMARY.md |
| New validation check | VECTOR_DB_VALIDATION.md |
| New UI page | RUN_GUIDE.md, HOW_IT_WORKS.md |

---

## 📝 Documentation Maintenance Checklist

### After Major Changes

- [ ] Update relevant docs/ files
- [ ] Update COMPLETION_REPORT.md with progress
- [ ] Check all code examples still work
- [ ] Verify screenshots/diagrams if any
- [ ] Update API references
- [ ] Check links between documents

### Weekly Review

- [ ] Scan for outdated information
- [ ] Update status documents
- [ ] Add new examples if needed
- [ ] Archive obsolete sections

---

## 🎯 Quick Reference for Common Updates

### Vision Features Changed?
→ Update: `docs/VISION_FEATURES.md`

### Health Check Modified?
→ Update: `docs/VECTOR_DB_VALIDATION.md`

### Architecture Refactored?
→ Update: `docs/ARCHITECTURE.md`, `docs/HOW_IT_WORKS.md`

### New Feature Completed?
→ Update: `docs/COMPLETION_REPORT.md`, relevant feature doc

### Setup Process Changed?
→ Update: `docs/QUICK_START.md`

### Data Pipeline Modified?
→ Update: `docs/DATA_MANAGEMENT.md`, `docs/HOW_IT_WORKS.md`

---

## 📚 Documentation Best Practices

1. **Keep docs in sync**: Update documentation immediately when changing code
2. **Use this map**: Check this file when unsure what to update
3. **Link between docs**: Cross-reference related documentation
4. **Include examples**: Add code examples that actually work
5. **Date updates**: Note when major updates were made
6. **Version info**: Mention version numbers for external dependencies

---

## 🔍 Finding Information Quick Reference

| Looking For... | Check... |
|---------------|----------|
| How system works overall | HOW_IT_WORKS.md |
| How to get started | QUICK_START.md |
| Vision capabilities | VISION_FEATURES.md |
| Architecture details | ARCHITECTURE.md |
| Database validation | VECTOR_DB_VALIDATION.md |
| Data pipeline | DATA_MANAGEMENT.md |
| Running/testing | RUN_GUIDE.md |
| What's implemented | COMPLETION_REPORT.md |

---

**Last Updated**: 2025-12-22
**Maintained By**: Development Team
