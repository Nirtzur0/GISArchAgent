# 🏗️ GIS Architecture Agent

An intelligent agentic RAG system for architecture firms to query Israeli planning regulations, approvals, and zoning information from the iPlan system (https://ags.iplan.gov.il/xplan/).

## 🎯 What It Does

Ask natural language questions about:
- 📋 **Israeli Planning Regulations** - TAMA plans, zoning laws, building codes
- 🏛️ **Government Data** - Real-time data from iPlan GIS system
- 🏗️ **Your Projects** - Historical projects, precedents, and approvals
- 📊 **Compliance** - Requirements, procedures, and timelines

Get intelligent answers powered by:
- 🤖 **LangGraph Agents** - Multi-step reasoning and tool selection
- 🔍 **RAG System** - Retrieval Augmented Generation
- 💾 **Vector Database** - Semantic search across all documents

## Features

- **Regulatory Knowledge Base**: Query Israeli planning regulations, zoning laws, and approval processes
- **Plan Analysis**: Extract and analyze planning data from the iPlan GIS system
- **Agentic Architecture**: Multi-agent system with specialized tools for different queries
- **Local Project Integration**: Extend to include firm-specific projects and plans
- **Natural Language Queries**: Ask questions in plain language about regulations and plans

## Architecture

The system uses:
- **LangGraph** for agentic workflow orchestration
- **LangChain** for RAG implementation
- **ChromaDB** for vector storage
- **OpenAI/Anthropic** for LLM capabilities
- **BeautifulSoup/Selenium** for web scraping
- **ArcGIS API** for GIS data extraction

## Project Structure

```
├── src/
│   ├── agents/          # Agent definitions and orchestration
│   ├── scrapers/        # Web scraping and data extraction
│   ├── vectorstore/     # Vector database management
│   ├── tools/           # Agent tools (search, query, analyze)
│   ├── chains/          # LangChain RAG chains
│   └── api/             # API endpoints
├── data/
│   ├── raw/             # Raw scraped data
│   ├── processed/       # Processed documents
│   └── vectorstore/     # Vector database files
├── config/              # Configuration files
├── tests/               # Unit and integration tests
└── notebooks/           # Development notebooks
```

## Quick Start

### Installation (5 minutes)

```bash
# 1. Setup
./setup.sh

# 2. Add your OpenAI API key
nano .env  # Add: OPENAI_API_KEY=sk-your-key-here

# 3. Initialize
python -m src.cli init

# 4. Start querying!
python -m src.cli query --interactive
```

### Python API

```python
from src.main import GISArchAgent

app = GISArchAgent()
response = app.query("What are the main provisions of TAMA 35?")
print(response)
```

### Example Queries

Try asking:
- "What are the parking requirements for a 150 sqm residential apartment?"
- "How tall can buildings be in Tel Aviv R1 zone?"
- "What is the plan approval process?"
- "What are TAMA 35 provisions?"

📖 **Full Guide**: See [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)

## iPlan System Integration

The iPlan system provides:
- **Blue Lines (Kav Kachol)**: Planning schemes across Israel
- **Zoning Layers**: Land use designations
- **TAMA Plans**: National outline plans (TAMA 1, 35, 47, 70)
- **Regional Plans**: District and local planning schemes
- **Section 77-78 Notices**: Planning notifications

## License

MIT
