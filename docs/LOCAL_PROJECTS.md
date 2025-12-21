# Extending to Local Projects

This guide explains how to extend the GIS Architecture Agent to include your firm's local projects and plans.

## Overview

The system can be extended to search and analyze your firm's own project documentation alongside Israeli planning regulations. This creates a unified knowledge base that combines:

1. **National and local regulations** from the iPlan system
2. **Your firm's project files** (PDFs, Word docs, spreadsheets, etc.)
3. **Historical project data** and precedents

## Setting Up Local Projects

### 1. Organize Your Project Files

Create a directory structure for your projects:

```
data/local_projects/
├── project_a/
│   ├── plans/
│   │   ├── architectural_plans.pdf
│   │   └── site_plan.pdf
│   ├── approvals/
│   │   ├── building_permit.pdf
│   │   └── variance_approval.pdf
│   └── reports/
│       └── planning_report.docx
├── project_b/
│   └── ...
└── templates/
    ├── permit_application_template.docx
    └── compliance_checklist.xlsx
```

### 2. Ingest Local Projects

#### Option A: Using Python API

```python
from src.local_projects import LocalProjectManager

# Initialize manager
manager = LocalProjectManager()

# Ingest a single project directory
manager.ingest_project_directory(
    project_dir=Path("data/local_projects/project_a"),
    project_name="Residential Tower - Tel Aviv"
)

# Or ingest specific files
from pathlib import Path

manager.ingest_project(
    project_name="Office Building - Haifa",
    project_files=[
        Path("data/local_projects/project_b/plans.pdf"),
        Path("data/local_projects/project_b/report.docx")
    ],
    metadata={
        "location": "Haifa",
        "project_type": "commercial",
        "year": 2024,
        "status": "approved"
    }
)
```

#### Option B: Using CLI (Coming Soon)

```bash
# Ingest all projects in a directory
python -m src.cli ingest-local ./data/local_projects

# Ingest a specific project
python -m src.cli ingest-local ./data/local_projects/project_a --name "Tower Project"
```

### 3. Query with Hybrid Search

The agent automatically searches both regulations and local projects:

```python
from src.main import GISArchAgent

app = GISArchAgent()

# This will search both iPlan regulations AND your local projects
response = app.query(
    "What parking requirements applied to our previous residential project in Tel Aviv?"
)
```

### 4. Context-Aware Queries

Use project context to find relevant regulations:

```python
from src.local_projects import HybridSearchManager

hybrid = HybridSearchManager()

# Search with project context
results = hybrid.contextualized_search(
    query="height restrictions",
    project_context="residential building Tel Aviv Rothschild Boulevard"
)
```

## Supported File Types

The system supports the following file formats:

- **PDF** (`.pdf`) - Plans, permits, reports
- **Word** (`.doc`, `.docx`) - Reports, specifications
- **Excel** (`.xls`, `.xlsx`) - Calculations, schedules
- **Text** (`.txt`, `.md`) - Notes, documentation

## Best Practices

### 1. Organize by Project

Keep each project in its own directory with clear structure:

```
project_name/
├── plans/           # Architectural and engineering plans
├── approvals/       # Permits and approvals
├── reports/         # Planning and technical reports
├── correspondence/  # Letters and communications
└── photos/          # Site photos (not indexed, for reference)
```

### 2. Use Meaningful Metadata

When ingesting projects, add relevant metadata:

```python
metadata = {
    "location": "Tel Aviv, Rothschild 45",
    "project_type": "residential",
    "building_type": "high-rise",
    "floors": 20,
    "year_submitted": 2023,
    "year_approved": 2024,
    "status": "approved",
    "architect": "Firm Name",
    "plot_size": 1200,  # sqm
    "built_area": 8500,  # sqm
}
```

### 3. Create Project Indexes

Generate indexes for better organization:

```python
manager = LocalProjectManager()
index = manager.create_project_index(
    Path("data/local_projects/project_a")
)
```

### 4. Regular Updates

Re-ingest projects when documents are updated:

```python
# The system will update existing documents
manager.ingest_project_directory(
    project_dir=Path("data/local_projects/project_a")
)
```

## Advanced Features

### Cross-Reference Projects and Regulations

Find which regulations applied to past projects:

```python
# Query example
query = """
Looking at our 2023 residential project in Tel Aviv, 
what were the key height and parking regulations that applied?
"""

response = app.query(query)
```

### Precedent Search

Find similar past projects:

```python
manager = LocalProjectManager()

similar_projects = manager.search_local_projects(
    query="residential building 15 floors parking variance",
    k=3
)
```

### Project Compliance Check

Compare new projects against regulations and past approvals:

```python
query = """
I'm planning a 12-story residential building in Tel Aviv R2 zone.
Based on current regulations and our past projects, what are the key 
requirements I need to meet?
"""

response = app.query(query)
```

## Example Queries

Once local projects are ingested, you can ask:

1. **Precedent Queries**
   - "Show me similar projects we've done in Haifa"
   - "What parking solutions did we use in previous projects?"
   - "Find examples of height variance approvals we received"

2. **Compliance Queries**
   - "Does this project comply with the same regulations as Project X?"
   - "What changed in the regulations since our 2020 project?"

3. **Learning Queries**
   - "What objections did we face in similar projects?"
   - "How long did approval take for residential projects in Tel Aviv?"

4. **Cross-Reference Queries**
   - "Which TAMA plans affected our projects in the last 3 years?"
   - "Find all projects where we applied for parking variances"

## Privacy and Security

### Local-Only Storage

All local project data is stored in your vector database and never sent to external services except:
- The text content is sent to OpenAI/Anthropic for embeddings and LLM processing
- Consider using local LLMs if you need complete data privacy

### Sensitive Information

Remove or redact sensitive information before ingesting:
- Client names (if confidential)
- Financial information
- Personal details
- Proprietary designs

### Access Control

Add authentication if exposing the system as a service (not included in base system).

## Integration with Existing Tools

### CAD Integration (Future)

Plan for extracting data from:
- AutoCAD (`.dwg`)
- Revit (`.rvt`)
- SketchUp (`.skp`)

### GIS Integration

Import spatial data from:
- Shapefiles
- GeoJSON
- KML files

### Document Management Systems

Connect to existing systems:
- SharePoint
- Dropbox
- Google Drive

## Troubleshooting

### Files Not Loading

Check file formats and ensure they're not corrupted:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Poor Search Results

1. Check that documents were ingested properly
2. Verify metadata is correct
3. Try rephrasing queries
4. Increase `k` parameter for more results

### Performance Issues

For large document sets:
- Use metadata filters to narrow search
- Consider multiple collections per project type
- Increase chunk size for faster processing

## Next Steps

1. Start with a single test project
2. Verify search quality
3. Gradually add more projects
4. Refine metadata structure
5. Create custom tools for your workflow
