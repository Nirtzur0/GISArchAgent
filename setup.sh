#!/bin/bash

# Setup script for GIS Architecture Agent

echo "=========================================="
echo "GIS Architecture Agent - Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Check if version is 3.9 or higher
required_version="3.9"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo "Error: Python 3.9 or higher is required"
    exit 1
fi

echo "✓ Python version OK"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists"
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ pip upgraded"
echo ""

# Install requirements
echo "Installing dependencies..."
echo "(This may take a few minutes)"
pip install -r requirements.txt > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed"
else
    echo "⚠ Some dependencies may have failed to install"
    echo "Run 'pip install -r requirements.txt' manually to see errors"
fi
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠ IMPORTANT: Edit .env and add your OpenAI API key"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Create data directories
echo "Creating data directories..."
mkdir -p data/raw
mkdir -p data/processed
mkdir -p data/vectorstore
mkdir -p data/local_projects
echo "✓ Data directories created"
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env and add your OpenAI API key:"
echo "   nano .env"
echo ""
echo "2. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "3. Initialize the system:"
echo "   python -m src.cli init"
echo ""
echo "4. Start querying:"
echo "   python -m src.cli query --interactive"
echo ""
echo "For more information, see:"
echo "  - README.md"
echo "  - docs/QUICKSTART.md"
echo "  - docs/LOCAL_PROJECTS.md"
echo ""
