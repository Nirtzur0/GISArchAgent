# 🏗️ GIS Architecture Agent

Your AI-powered assistant for Israeli planning regulations and architecture projects.

## What Is This?

This is a tool for architecture firms working in Israel. It helps you:
- 🔍 Search through planning documents (תוכניות) from the iPlan system
- 📋 Query planning regulations and get clear answers
- 📐 Calculate building rights based on zoning
- 🖼️ Analyze plan images with AI vision
- ✅ Check compliance with regulations

Think of it as having a planning expert who knows all the regulations and can read Hebrew planning documents.

## Quick Start

```bash
# Install everything
pip install -r requirements.txt

# Set up your API key (for vision analysis)
echo \"GEMINI_API_KEY=your_key_here\" > .env

# Run the app
streamlit run app.py
```

Open your browser to http://localhost:8501 and start exploring!

## How to Use It

### In the Web App

The Streamlit interface has everything you need:
- Ask questions about regulations in natural language
- Search for plans by location or ID
- Calculate building rights for your plot
- View results with sources and explanations

### In Your Code

```python
from src.infrastructure.factory import get_factory
from src.application.dtos import PlanSearchQuery

# Get the factory
factory = get_factory()

# Get a service
service = factory.get_plan_search_service()

# Search for plans
query = PlanSearchQuery(location=\"תל אביב\", max_results=10)
result = service.search_plans(query)

# Use the results
for plan in result.plans:
    print(plan.plan.name)
```

Check out `examples.py` for more usage patterns.

## What's Inside?

We built this using Clean Architecture, which basically means everything is organized and easy to maintain:

```
src/
├── domain/           # Business logic (plans, regulations, rights calculations)
├── application/      # Use cases (search, query, calculate)
├── infrastructure/   # External stuff (APIs, database, AI services)
└── (other files)
```

The important bits:
- **Domain Layer** - Pure business rules, no dependencies on frameworks
- **Application Services** - The smart stuff that coordinates everything
- **Infrastructure** - Talks to iPlan API, ChromaDB, Gemini AI, etc.

## Features

### 📍 Plan Search
Search for planning documents from the government's iPlan system:
- By location (city, neighborhood)
- By plan ID
- By keywords
- With automatic AI vision analysis of plan images

### 💬 Regulation Queries  
Ask questions in natural language:
- \"What are the parking requirements for residential buildings?\"
- \"What's the maximum building height in Tel Aviv R2 zone?\"
- \"Explain TAMA 35\"

Get answers with sources and citations.

### 📐 Building Rights Calculator
Calculate what you can build:
- Input: plot size, zone type, location
- Output: max building area, coverage %, FAR, height, parking spots
- Based on Israeli regulations (TAMA, local zoning, etc.)

### 🖼️ Vision Analysis
AI analysis of plan images:
- OCR text extraction (Hebrew & English)
- Identify zones and land uses
- Describe what's in the plan
- Powered by Google Gemini

## Tech Stack

- **Python 3.12** - Because we like the new stuff
- **Streamlit** - Beautiful web interface
- **ChromaDB** - Vector database for semantic search
- **Google Gemini** - Vision AI for analyzing plan images  
- **iPlan API** - Israeli government planning system
- **Clean Architecture** - SOLID principles, testable, maintainable

## Project Structure

```
GISArchAgent/
├── app.py                    # Main Streamlit app
├── examples.py               # Usage examples
├── src/
│   ├── domain/              # Business entities and rules
│   ├── application/         # Services and use cases
│   ├── infrastructure/      # API clients, databases, AI
│   ├── vectorstore/         # ChromaDB management
│   └── config.py            # Configuration
├── pages/                   # Streamlit pages
├── docs/                    # Documentation
└── data/                    # Databases and cache
```

## Documentation

- 📘 [Quick Start](docs/QUICK_START.md) - Get running in 5 minutes
- 🏛️ [Architecture Guide](docs/ARCHITECTURE.md) - How it all works
- 📊 [Implementation Summary](docs/IMPLEMENTATION_SUMMARY.md) - What we built

## Development

### Running Tests
```bash
# TODO: Add tests!
pytest
```

### Code Style
We use type hints everywhere and try to keep things readable. Comments explain *why*, not *what*.

### Contributing
Feel free to improve things! Just keep the architecture clean and write readable code.

## Notes

### API Keys
You'll need a Gemini API key for vision analysis. Everything else works without external services (iPlan API is public).

### Hebrew Support
The system handles Hebrew text properly. Plan names, locations, and regulations are all in Hebrew where appropriate.

## License

[Add your license here]

## Questions?

Check the docs folder or look at the examples. The code is pretty readable - if you can't figure something out, that's a bug in the documentation! 😊

---

Built with ❤️ for architecture firms working with Israeli planning regulations.
