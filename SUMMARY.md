# Project Summary - GIS Architecture Agent

## What I've Built

I've created a complete **agentic RAG system** for architecture firms to query Israeli planning regulations and extend to their own local projects. The system is based on data from the iPlan system (https://ags.iplan.gov.il/xplan/).

## Key Features

### 1. **Intelligent Agent Architecture**
- Built with LangGraph for multi-step reasoning
- Uses LangChain for RAG implementation
- Multiple specialized tools for different query types
- Autonomous decision-making for complex queries

### 2. **Dual Knowledge Base**
- **iPlan Regulations**: National and local planning regulations from Israeli government
- **Local Projects**: Your firm's own project documentation and precedents

### 3. **Comprehensive Data Sources**
- National Outline Plans (TAMA 35, 38, etc.)
- Zoning regulations and designations
- Building codes and requirements
- Plan approval procedures
- Green building standards

### 4. **Multiple Interfaces**
- **CLI**: Interactive command-line interface
- **Python API**: Programmatic access
- **Direct Tools**: Low-level access to search functions

## Project Structure

```
GISArchAgent/
├── src/
│   ├── agents/              # LangGraph-based agentic system
│   │   └── architecture_agent.py
│   ├── scrapers/            # Web scraping for iPlan
│   │   └── iplan_scraper.py
│   ├── vectorstore/         # ChromaDB vector storage
│   │   └── manager.py
│   ├── tools/               # Agent tools (search, analyze)
│   │   └── architecture_tools.py
│   ├── local_projects.py    # Local project integration
│   ├── config.py            # Configuration management
│   ├── ingest_data.py       # Data ingestion pipeline
│   ├── main.py              # Main application
│   └── cli.py               # Command-line interface
├── data/
│   ├── raw/                 # Raw scraped data
│   ├── processed/           # Processed documents
│   └── vectorstore/         # Vector database files
├── docs/
│   ├── QUICKSTART.md        # Quick start guide
│   └── LOCAL_PROJECTS.md    # Guide for adding local projects
├── examples/
│   └── usage_examples.py    # Example usage patterns
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
└── README.md                # Main documentation
```

## Technology Stack

- **LLM**: OpenAI GPT-4 (configurable)
- **Agent Framework**: LangGraph + LangChain
- **Vector Database**: ChromaDB
- **Embeddings**: OpenAI text-embedding-3-small
- **Web Scraping**: BeautifulSoup, Selenium, ArcGIS API
- **Document Processing**: PyPDF, python-docx, openpyxl

## How It Works

### 1. Data Ingestion
```python
# Scrapes iPlan system and loads sample regulations
python -m src.cli init
```

### 2. Query Processing
```
User Question
     ↓
Agent (LangGraph)
     ↓
Tool Selection (search regulations, plans, zoning)
     ↓
Vector Store Retrieval
     ↓
LLM Synthesis
     ↓
Structured Answer
```

### 3. Agent Workflow
- **Agent Node**: Reasons about the query and decides which tools to use
- **Tools Node**: Executes searches in the vector store
- **Synthesize Node**: Combines information into a coherent answer

## Quick Start

### 1. Install
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your OpenAI API key
```

### 2. Initialize
```bash
python -m src.cli init
```

### 3. Query
```bash
# Interactive mode
python -m src.cli query --interactive

# Single query
python -m src.cli query "What are TAMA 35 provisions?"
```

### 4. Python API
```python
from src.main import GISArchAgent

app = GISArchAgent()
response = app.query("What are parking requirements?")
print(response)
```

## Extending to Local Projects

### Add Your Projects
```python
from src.local_projects import LocalProjectManager
from pathlib import Path

manager = LocalProjectManager()
manager.ingest_project_directory(
    Path("./data/local_projects/your_project")
)
```

### Query Both Sources
```python
# Automatically searches both regulations and local projects
response = app.query(
    "What parking solutions did we use in previous Tel Aviv projects?"
)
```

## Example Queries

The system can answer:

1. **Regulatory Questions**
   - "What are TAMA 35 provisions?"
   - "What are height restrictions in Tel Aviv?"
   - "What parking is required for 150 sqm apartment?"

2. **Procedural Questions**
   - "What is the plan approval process?"
   - "How long does approval take?"
   - "What documents do I need?"

3. **Project-Specific Questions** (after adding local projects)
   - "Find similar projects in Haifa"
   - "What variances did we get in past projects?"
   - "How did we handle parking in Project X?"

4. **Complex Analysis**
   - "I'm planning a 14-story building in Tel Aviv. What regulations apply?"
   - "Compare requirements between R1 and R2 zones"

## Advanced Features

### Hybrid Search
Searches both regulations and your projects simultaneously:
```python
from src.local_projects import HybridSearchManager

hybrid = HybridSearchManager()
results = hybrid.hybrid_search("parking requirements", k=5)
```

### Context-Aware Search
Finds regulations relevant to a specific project:
```python
results = hybrid.contextualized_search(
    query="height restrictions",
    project_context="residential tower Tel Aviv"
)
```

### Direct Tool Access
For specialized queries:
```python
from src.tools import ArchitectureTools

tools = ArchitectureTools(vectorstore)
tama_info = tools.get_tama_info("35")
zoning = tools.analyze_zoning("Tel Aviv", "residential")
```

## Next Steps

### Immediate
1. ✅ Run `python -m src.cli init` to set up
2. ✅ Try example queries
3. ✅ Review [docs/QUICKSTART.md](docs/QUICKSTART.md)

### Short-term
1. Add your first local project
2. Customize the agent prompt
3. Add more regulations from iPlan
4. Create firm-specific tools

### Long-term
1. Deploy as web service (FastAPI)
2. Add authentication/authorization
3. Integrate with CAD tools
4. Create mobile app interface
5. Add real-time iPlan monitoring

## Customization Points

### 1. Agent Behavior
Edit [src/agents/architecture_agent.py](src/agents/architecture_agent.py):
- System prompt
- Tool selection logic
- Answer formatting

### 2. Tools
Add new tools in [src/tools/architecture_tools.py](src/tools/architecture_tools.py):
- Custom calculations
- External API integrations
- Specialized searches

### 3. Data Sources
Extend [src/scrapers/iplan_scraper.py](src/scrapers/iplan_scraper.py):
- More iPlan layers
- Other government sites
- Local planning committees

### 4. Vector Store
Modify [src/vectorstore/manager.py](src/vectorstore/manager.py):
- Multiple collections
- Different embedding models
- Custom chunk strategies

## Deployment Options

### Local Development
```bash
python -m src.cli query --interactive
```

### Web API
```python
from fastapi import FastAPI
from src.main import GISArchAgent

app = FastAPI()
agent = GISArchAgent()

@app.post("/query")
async def query(question: str):
    return await agent.aquery(question)
```

### Docker (Future)
```dockerfile
FROM python:3.11
COPY . /app
RUN pip install -r requirements.txt
CMD ["python", "-m", "src.main"]
```

## Important Notes

### Data Privacy
- All queries are processed through OpenAI/Anthropic APIs
- Vector embeddings are stored locally
- Consider local LLMs for sensitive data

### Data Updates
- iPlan data should be re-scraped periodically
- Regulations change - implement monitoring
- Update local projects as they evolve

### Performance
- First query may be slow (loading models)
- Subsequent queries are faster
- Consider caching for production

## Support & Resources

- **Documentation**: See [docs/](docs/) folder
- **Examples**: See [examples/usage_examples.py](examples/usage_examples.py)
- **Issues**: Track in your issue system
- **API Docs**: OpenAI, LangChain, LangGraph

## License

MIT License - See LICENSE file

---

**Built for architecture firms to streamline regulatory research and leverage institutional knowledge.**
