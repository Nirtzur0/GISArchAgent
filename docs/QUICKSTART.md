# Quick Start Guide

Get started with the GIS Architecture Agent in minutes.

## Prerequisites

- Python 3.9 or higher
- OpenAI API key (or Anthropic API key)
- 2GB free disk space
- Internet connection (for initial data scraping)

## Installation

### 1. Clone or Download the Project

```bash
cd /Users/nirtzur/Documents/projects/GISArchAgent
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
OPENAI_API_KEY=sk-your-key-here
# Optional: ANTHROPIC_API_KEY=sk-ant-your-key-here
```

## Initialize the System

### Option 1: Using CLI

```bash
# Initialize and ingest data from iPlan
python -m src.cli init
```

This will:
1. Scrape data from the iPlan system
2. Load sample regulations
3. Create the vector store
4. Index all documents

**Expected time:** 2-5 minutes

### Option 2: Using Python

```python
import asyncio
from src.ingest_data import DataIngestionPipeline

async def main():
    pipeline = DataIngestionPipeline()
    await pipeline.run_full_pipeline()

asyncio.run(main())
```

## Using the System

### Interactive Mode (Recommended for first use)

```bash
python -m src.cli query --interactive
```

Example session:

```
📋 Your question: What are the main provisions of TAMA 35?

🤔 Thinking...

============================================================
📝 Answer:
============================================================
TAMA 35 is the National Outline Plan for Building Construction 
and Urban Renewal. Key provisions include:

1. **Purpose**: Encourage urban renewal and strengthen buildings 
   against earthquakes

2. **Building Rights**:
   - Add 2-3 floors to existing buildings
   - 30% increase in floor area allowed
   - Additional space for balconies and protected areas

3. **Eligibility**: 
   - Buildings constructed before 1980
   - Located in residential zones
   - Requires 80% owner agreement

4. **Options**:
   - Building strengthening with additions
   - Complete demolition and reconstruction

[Additional details...]
============================================================
```

### Single Query Mode

```bash
python -m src.cli query "What are parking requirements for residential buildings?"
```

### Python API

```python
from src.main import GISArchAgent

# Initialize
app = GISArchAgent()

# Query
response = app.query(
    "How tall can a building be in Tel Aviv residential zone R1?"
)

print(response)
```

### Async Python API

```python
import asyncio
from src.main import GISArchAgent

async def main():
    app = GISArchAgent()
    response = await app.aquery(
        "What is the plan approval process?"
    )
    print(response)

asyncio.run(main())
```

## Example Queries

Try these questions to test the system:

### Regulations

```
What are the main provisions of TAMA 35?
What parking requirements apply to a 120 sqm apartment?
What are the green building requirements?
```

### Zoning

```
How tall can I build in Tel Aviv residential zones?
What is the maximum building coverage in R1 zone?
What setback requirements apply to commercial buildings?
```

### Procedures

```
What is the plan approval process?
How long does plan approval typically take?
What documents are needed for a building permit application?
```

### Specific Plans

```
Tell me about TAMA 38
What is the difference between TAMA 35 and TAMA 38?
What are the requirements under TAMA plans?
```

## View System Statistics

```bash
python -m src.cli stats
```

Output:

```
============================================================
📊 KNOWLEDGE BASE STATISTICS
============================================================
Collection: iplan_regulations
Document Count: 24
Location: ./data/vectorstore
============================================================
```

## Next Steps

### 1. Add Local Projects

See [LOCAL_PROJECTS.md](./LOCAL_PROJECTS.md) for details on integrating your firm's projects.

```python
from src.local_projects import LocalProjectManager
from pathlib import Path

manager = LocalProjectManager()
manager.ingest_project_directory(
    Path("./data/local_projects/my_project")
)
```

### 2. Customize the Agent

Modify [src/agents/architecture_agent.py](../src/agents/architecture_agent.py) to:
- Adjust the system prompt
- Add custom tools
- Modify the reasoning workflow

### 3. Add More Regulations

Update [src/ingest_data.py](../src/ingest_data.py) to:
- Scrape more data from iPlan
- Add local planning committee regulations
- Include building codes and standards

### 4. Deploy as a Service

Create a web API:

```python
from fastapi import FastAPI
from src.main import GISArchAgent

app = FastAPI()
agent = GISArchAgent()

@app.post("/query")
async def query(question: str):
    response = await agent.aquery(question)
    return {"response": response}
```

Run with:

```bash
uvicorn api:app --reload
```

## Troubleshooting

### "No module named 'src'"

Make sure you're in the project root directory:

```bash
cd /Users/nirtzur/Documents/projects/GISArchAgent
```

### "OpenAI API key not found"

Check your `.env` file has the correct key:

```bash
cat .env | grep OPENAI_API_KEY
```

### "Vector store empty"

Run initialization:

```bash
python -m src.cli init
```

### Selenium/WebDriver errors

Install ChromeDriver:

```bash
# macOS
brew install chromedriver

# Or let the script auto-install
pip install webdriver-manager
```

### Rate limiting errors

If you hit OpenAI rate limits:
1. Wait a few minutes
2. Reduce chunk size in config
3. Use smaller batches for ingestion

## Getting Help

### View Examples

```bash
python -m src.cli examples
```

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check System Health

```python
from src.main import GISArchAgent

app = GISArchAgent()
stats = app.get_stats()
print(f"Documents indexed: {stats['document_count']}")
```

## What's Next?

- ✅ System is running
- ✅ Sample data loaded
- 📋 Try example queries
- 🏗️ Add your local projects
- 🔧 Customize for your needs
- 🚀 Deploy to production

See the full [README.md](../README.md) for more details.
