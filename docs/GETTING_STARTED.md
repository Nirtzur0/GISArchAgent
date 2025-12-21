# Getting Started with GIS Architecture Agent

Welcome! This guide will help you get your agentic RAG system up and running.

## What You're Building

An intelligent assistant that can:
- ✅ Answer questions about Israeli planning regulations
- ✅ Query the iPlan government system data
- ✅ Search your firm's historical projects
- ✅ Provide precedent-based advice
- ✅ Synthesize complex regulatory information

## Prerequisites

Before starting, ensure you have:
- ✅ macOS, Linux, or Windows
- ✅ Python 3.9 or higher ([download](https://www.python.org/downloads/))
- ✅ OpenAI API key ([get one](https://platform.openai.com/api-keys))
- ✅ 2GB free disk space
- ✅ Internet connection

## Installation (5 minutes)

### Option 1: Automatic Setup (Recommended)

```bash
cd /Users/nirtzur/Documents/projects/GISArchAgent
./setup.sh
```

The script will:
1. Check Python version
2. Create virtual environment
3. Install dependencies
4. Create data directories
5. Set up configuration

### Option 2: Manual Setup

```bash
# 1. Navigate to project
cd /Users/nirtzur/Documents/projects/GISArchAgent

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env
```

## Configuration (2 minutes)

### 1. Add Your API Key

Edit `.env` file:

```bash
nano .env
# or use any text editor
```

Add your OpenAI API key:

```env
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

### 2. Optional: Configure Other Settings

```env
# LLM Settings
MODEL_NAME=gpt-4-turbo-preview  # or gpt-4, gpt-3.5-turbo
TEMPERATURE=0.1                  # Lower = more focused answers
MAX_TOKENS=4000                  # Max response length

# Embedding Settings
EMBEDDING_MODEL=text-embedding-3-small
CHUNK_SIZE=1000                  # Document chunk size
CHUNK_OVERLAP=200                # Overlap between chunks

# LangSmith (Optional - for debugging)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-key
```

## Initialize the System (3-5 minutes)

This step scrapes data from iPlan and creates the vector database:

```bash
python -m src.cli init
```

You'll see:

```
🚀 Initializing GIS Architecture Agent...
This will scrape and ingest data from the iPlan system.

Step 1: Scraping iPlan data...
Step 2: Loading sample regulations...
Step 3: Ingesting into vector store...

============================================================
DATA INGESTION COMPLETE
============================================================
Documents ingested: 6
Vector store: iplan_regulations
Total chunks: 24
============================================================

✅ Initialization complete!
```

## First Query (1 minute)

### Interactive Mode

```bash
python -m src.cli query --interactive
```

Try asking:
```
📋 Your question: What are the main provisions of TAMA 35?
```

### Single Query Mode

```bash
python -m src.cli query "What parking requirements apply to residential buildings?"
```

### Python API

```python
from src.main import GISArchAgent

app = GISArchAgent()
response = app.query("How tall can buildings be in Tel Aviv R1 zone?")
print(response)
```

## What to Try Next

### 1. Explore Example Queries

```bash
python -m src.cli examples
```

This shows pre-made queries you can try.

### 2. Run Usage Examples

```bash
python examples/usage_examples.py
```

Choose from 8 different example patterns.

### 3. Check System Stats

```bash
python -m src.cli stats
```

Shows how many documents are indexed.

## Adding Your First Local Project (10 minutes)

### Step 1: Prepare Project Files

Create a folder for your project:

```bash
mkdir -p data/local_projects/my_first_project
```

Add project files:
- PDFs (plans, permits)
- Word docs (reports)
- Text files (notes)
- Excel sheets (calculations)

### Step 2: Ingest the Project

```python
from src.local_projects import LocalProjectManager
from pathlib import Path

manager = LocalProjectManager()
manager.ingest_project_directory(
    Path("data/local_projects/my_first_project"),
    project_name="My First Project"
)
```

### Step 3: Query Your Project

```bash
python -m src.cli query --interactive
```

Ask:
```
📋 Your question: What projects do we have in our database?
📋 Your question: Find information about "My First Project"
```

## Common Issues & Solutions

### "No module named 'src'"

**Solution**: Make sure you're in the project root:
```bash
cd /Users/nirtzur/Documents/projects/GISArchAgent
```

### "OpenAI API key not found"

**Solution**: Check your .env file:
```bash
cat .env | grep OPENAI_API_KEY
```

Make sure it has your actual key (starts with `sk-`).

### "Vector store empty" or "No documents found"

**Solution**: Run initialization:
```bash
python -m src.cli init
```

### ChromeDriver/Selenium errors

**Solution**: Install ChromeDriver:
```bash
# macOS
brew install chromedriver

# Or let it auto-install
pip install webdriver-manager
```

### Rate limit errors from OpenAI

**Solution**: 
- Wait a few minutes between requests
- Reduce chunk size in .env
- Upgrade your OpenAI plan

### Slow responses

**Causes**:
- First query loads models (normal)
- Complex queries take longer
- Large documents need more processing

**Solutions**:
- Be patient on first query
- Use more specific queries
- Break complex questions into parts

## Understanding the System

### How It Works

```
1. Your Question
   ↓
2. Agent analyzes question
   ↓
3. Agent decides which tools to use
   ↓
4. Tools search vector database
   ↓
5. Agent synthesizes answer
   ↓
6. You get structured response
```

### What's in the Vector Database

After initialization, the system contains:
- ✅ TAMA 35 (Urban Renewal Plan)
- ✅ TAMA 38 (Infrastructure Plan)
- ✅ Building height regulations
- ✅ Parking requirements
- ✅ Green building standards
- ✅ Plan approval procedures

### How Agents Work

The system uses **LangGraph** to create an agent that:
1. **Reasons** about your question
2. **Selects** appropriate tools
3. **Executes** searches
4. **Synthesizes** information
5. **Formats** the answer

It's like having an expert assistant who knows when to search regulations vs. when to look at past projects.

## Best Practices

### Writing Good Queries

❌ **Bad**: "regulations"
✅ **Good**: "What are the parking regulations for residential buildings in Tel Aviv?"

❌ **Bad**: "TAMA"
✅ **Good**: "What are the main provisions of TAMA 35 and how does it affect existing buildings?"

### Organizing Local Projects

```
data/local_projects/
├── residential/
│   ├── tel_aviv_tower_2023/
│   ├── haifa_complex_2024/
│   └── jerusalem_apartments_2022/
├── commercial/
│   ├── office_building_tel_aviv/
│   └── shopping_center_haifa/
└── templates/
    └── standard_documents/
```

### Adding Metadata

When ingesting projects, add rich metadata:

```python
metadata = {
    "project_type": "residential",
    "location": "Tel Aviv",
    "year": 2024,
    "status": "approved",
    "floors": 15,
    "apartments": 45,
    "architect": "Your Firm"
}
```

This makes searching more effective.

## Learning Path

### Week 1: Learn the Basics
- ✅ Install and configure
- ✅ Run example queries
- ✅ Understand system architecture
- ✅ Add one test project

### Week 2: Customize
- ✅ Add 5-10 real projects
- ✅ Customize agent prompts
- ✅ Create firm-specific tools
- ✅ Test with real queries

### Week 3: Production
- ✅ Deploy as web service
- ✅ Add authentication
- ✅ Train team members
- ✅ Integrate with workflow

### Ongoing: Maintain
- ✅ Update regulations quarterly
- ✅ Add new projects continuously
- ✅ Monitor query quality
- ✅ Refine based on feedback

## Next Steps

1. **Read the docs**
   - [README.md](../README.md) - Overview
   - [QUICKSTART.md](QUICKSTART.md) - Quick reference
   - [LOCAL_PROJECTS.md](LOCAL_PROJECTS.md) - Detailed project guide
   - [SUMMARY.md](../SUMMARY.md) - Technical summary

2. **Try examples**
   - Run `python examples/usage_examples.py`
   - Experiment with different query types
   - Test edge cases

3. **Join the conversation**
   - Review code in `src/` directory
   - Modify for your needs
   - Share improvements

## Getting Help

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Components

```python
from src.main import GISArchAgent

app = GISArchAgent()

# Check vector store
stats = app.get_stats()
print(f"Documents: {stats['document_count']}")

# Test direct search
from src.vectorstore import VectorStoreManager
vs = VectorStoreManager()
results = vs.similarity_search("parking", k=2)
print(f"Found {len(results)} results")
```

### System Health Check

```bash
# Check Python version
python3 --version

# Check installed packages
pip list | grep langchain

# Check vector store
ls -lh data/vectorstore/

# Check logs
python -m src.main
```

## Resources

### Official Documentation
- [LangChain Docs](https://python.langchain.com/docs/get_started/introduction)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [OpenAI API Docs](https://platform.openai.com/docs/introduction)

### iPlan System
- [iPlan Website](https://ags.iplan.gov.il/xplan/)
- [Planning Administration](https://www.gov.il/he/departments/planning_administration)

### Israeli Planning Law
- TAMA Plans (תמ"א)
- Building Law (חוק התכנון והבנייה)
- Local planning committees

## Support

### Common Questions

**Q: How accurate are the answers?**
A: The system bases answers on documents in the vector store. Accuracy depends on the quality and completeness of the data. Always verify important information with official sources.

**Q: Can I use this offline?**
A: No, it requires internet for OpenAI API calls. Consider using local LLMs for offline use.

**Q: How much does it cost?**
A: Main cost is OpenAI API usage:
- Embeddings: ~$0.0001 per 1K tokens
- GPT-4: ~$0.03 per 1K tokens
- Typical query: $0.05-0.20

**Q: Is my data private?**
A: Your queries and documents are sent to OpenAI for processing. Don't include sensitive data, or use local LLMs.

**Q: Can I deploy this for my team?**
A: Yes! See deployment section in [README.md](../README.md).

---

**Ready to start?** Run `./setup.sh` and you'll be querying regulations in minutes! 🚀
