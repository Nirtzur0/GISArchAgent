#!/bin/bash
# Run the Streamlit web application

echo "🚀 Starting GIS Architecture Agent Web App..."
echo "================================================"
echo ""

# Activate virtual environment
source venv/bin/activate

# Run Streamlit
streamlit run app.py
