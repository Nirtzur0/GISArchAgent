"""
Data Management Page - Manage planning data sources and updates
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import json
from datetime import datetime

# Import data management modules
from src.data_management import DataStore, DataFetcherFactory, IPlanFetcher

st.set_page_config(page_title="Data Management", page_icon="💾", layout="wide")

st.markdown("# 💾 Data Management")
st.markdown("### Manage planning data sources, updates, and statistics")

# Initialize data store
@st.cache_resource
def get_data_store():
    return DataStore()

data_store = get_data_store()

# Sidebar - Actions
with st.sidebar:
    st.markdown("## 🛠️ Actions")
    
    if st.button("🔄 Reload Data", use_container_width=True):
        data_store.reload()
        st.cache_resource.clear()
        st.success("Data reloaded!")
        st.rerun()
    
    if st.button("💾 Save Data", use_container_width=True):
        data_store.save(backup=True)
        st.success("Data saved with backup!")
    
    st.markdown("---")
    st.markdown("## 📥 Import Data")
    
    uploaded_file = st.file_uploader(
        "Upload GeoJSON/JSON",
        type=["json", "geojson"],
        help="Upload a file containing planning data"
    )
    
    if uploaded_file:
        try:
            data = json.load(uploaded_file)
            
            # Extract features
            if isinstance(data, dict) and "features" in data:
                features = data["features"]
            elif isinstance(data, list):
                features = data
            else:
                features = [data]
            
            st.info(f"File contains {len(features)} features")
            
            if st.button("Import Features", use_container_width=True):
                added = data_store.add_features(features, avoid_duplicates=True)
                data_store.save(backup=True)
                st.success(f"Added {added} new features!")
                st.rerun()
        except Exception as e:
            st.error(f"Error reading file: {e}")

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🔍 Browse Data", "📡 Fetch Data", "📖 Instructions"])

with tab1:
    st.markdown("## Data Overview")
    
    # Get statistics
    stats = data_store.get_statistics()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Plans", stats["total_plans"])
    
    with col2:
        st.metric("Districts", len(stats["by_district"]))
    
    with col3:
        st.metric("Cities", len(stats["by_city"]))
    
    with col4:
        st.metric("Statuses", len(stats["by_status"]))
    
    st.markdown("---")
    
    # Metadata
    metadata = stats.get("metadata", {})
    if metadata:
        st.markdown("### 📋 Data Source Info")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Source:** {metadata.get('source', 'Unknown')}")
            st.write(f"**Last Updated:** {metadata.get('last_updated', metadata.get('fetched_at', 'Unknown'))}")
            st.write(f"**Data Quality:** {metadata.get('data_quality', 'N/A')}")
        
        with col2:
            if 'coverage' in metadata:
                st.write("**Coverage:**")
                for region in metadata['coverage']:
                    st.write(f"  • {region}")
    
    # Distribution charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🗺️ By District")
        if stats["by_district"]:
            df_district = pd.DataFrame([
                {"District": k, "Count": v}
                for k, v in sorted(stats["by_district"].items(), key=lambda x: x[1], reverse=True)
            ])
            st.bar_chart(df_district.set_index("District"))
        else:
            st.info("No data available")
    
    with col2:
        st.markdown("### 📌 By Status")
        if stats["by_status"]:
            df_status = pd.DataFrame([
                {"Status": k, "Count": v}
                for k, v in sorted(stats["by_status"].items(), key=lambda x: x[1], reverse=True)
            ])
            st.bar_chart(df_status.set_index("Status"))
        else:
            st.info("No data available")

with tab2:
    st.markdown("## 🔍 Browse Planning Data")
    
    # Search filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        districts = ["All"] + data_store.get_unique_values("district_name")
        selected_district = st.selectbox("District", districts)
    
    with col2:
        cities = ["All"] + data_store.get_unique_values("plan_county_name")
        selected_city = st.selectbox("City", cities)
    
    with col3:
        statuses = ["All"] + data_store.get_unique_values("station_desc")
        selected_status = st.selectbox("Status", statuses)
    
    search_text = st.text_input("🔍 Search in plan name/number", placeholder="Enter search term...")
    
    # Apply filters
    results = data_store.search_features(
        district=None if selected_district == "All" else selected_district,
        city=None if selected_city == "All" else selected_city,
        status=None if selected_status == "All" else selected_status,
        text=search_text if search_text else None
    )
    
    st.markdown(f"**Found {len(results)} plans**")
    
    # Display results
    if results:
        for idx, feature in enumerate(results[:50]):  # Show first 50
            attrs = feature.get("attributes", {})
            
            with st.expander(
                f"📋 {attrs.get('pl_number', 'N/A')} - {attrs.get('pl_name', 'Unnamed')[:80]}"
            ):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Plan Number:** {attrs.get('pl_number', 'N/A')}")
                    st.write(f"**Name:** {attrs.get('pl_name', 'N/A')}")
                    st.write(f"**District:** {attrs.get('district_name', 'N/A')}")
                    st.write(f"**City:** {attrs.get('plan_county_name', 'N/A')}")
                    st.write(f"**Area:** {attrs.get('pl_area_dunam', 0)} dunam")
                    
                    if attrs.get('pl_objectives'):
                        st.write(f"**Objectives:** {attrs['pl_objectives'][:200]}...")
                
                with col2:
                    st.write(f"**Status:** {attrs.get('station_desc', 'N/A')}")
                    st.write(f"**Type:** {attrs.get('entity_subtype_desc', 'N/A')}")
                    
                    if attrs.get('pl_url'):
                        st.markdown(f"[🔗 View on iPlan]({attrs['pl_url']})")
                    
                    has_geometry = bool(feature.get("geometry", {}).get("rings"))
                    st.write(f"**Has Geometry:** {'✅' if has_geometry else '❌'}")
        
        if len(results) > 50:
            st.info(f"Showing first 50 of {len(results)} results. Refine search to see more.")
    else:
        st.info("No plans found matching criteria")

with tab3:
    st.markdown("## 📡 Fetch Fresh Data")
    
    st.markdown("""
    ### Data Sources
    
    Currently supported data sources:
    """)
    
    # List available fetchers
    fetchers = DataFetcherFactory.list_sources()
    
    for source in fetchers:
        fetcher = DataFetcherFactory.get_fetcher(source)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**{fetcher.get_source_name()}**")
            
            if source == "iplan":
                iplan_fetcher = fetcher
                st.markdown("""
                **iPlan API Access:**
                - Direct Python access: ❌ Blocked by WAF
                - AI Assistant access: ✅ Available
                - Manual export: ✅ Available
                """)
        
        with col2:
            available = "✅ Available" if fetcher.is_available() else "⚠️ Manual"
            st.write(available)
    
    st.markdown("---")
    
    # iPlan specific instructions
    st.markdown("### 🤖 Fetch via AI Assistant")
    
    st.info("""
    **Recommended Method:** Ask the AI assistant to fetch data for you:
    
    Simply say:
    > "Please fetch fresh iPlan data"
    
    The AI assistant has access to tools that can bypass the WAF protection
    and retrieve real planning data directly.
    """)
    
    if st.button("📋 Copy Fetch Request", use_container_width=True):
        st.code("Please fetch fresh iPlan data and save it to the data store")
        st.success("Request copied! Paste in chat to fetch data.")
    
    st.markdown("---")
    
    st.markdown("### 📥 Manual Import")
    
    st.markdown("""
    You can also manually export data from iPlan:
    
    1. Visit [iPlan Website](https://www.iplan.gov.il)
    2. Use the map interface to select plans
    3. Export as GeoJSON or JSON
    4. Upload using the sidebar import function
    """)

with tab4:
    st.markdown("## 📖 Data Management Guide")
    
    st.markdown("""
    ### Quick Start
    
    #### Viewing Current Data
    - **Overview Tab**: See statistics and distributions
    - **Browse Tab**: Search and filter through plans
    - Use search to find specific plans by name or number
    
    #### Updating Data
    
    **Method 1: AI Assistant (Recommended)**
    ```
    Ask in chat: "Please fetch fresh iPlan data"
    ```
    The AI will use its fetch_webpage tool to get real data.
    
    **Method 2: Manual File Import**
    1. Click "Browse files" in sidebar
    2. Upload your GeoJSON/JSON file
    3. Click "Import Features"
    
    **Method 3: Future Automated Fetching**
    When direct API access becomes available, automatic fetching
    will be enabled with scheduled updates.
    
    ### Data Structure
    
    Each plan includes:
    - **Attributes**: Plan number, name, status, dates, area
    - **Geometry**: Polygon coordinates (ITM projection)
    - **Links**: Direct URLs to official pages
    
    ### Backups
    
    - Automatic backups created when saving
    - Located in: `data/raw/backups/`
    - Timestamp format: `iplan_layers_YYYYMMDD_HHMMSS.json`
    
    ### Adding New Data Sources
    
    The system is designed for easy extension:
    1. Create a new fetcher class inheriting from `DataFetcher`
    2. Implement `fetch()`, `get_source_name()`, `is_available()`
    3. Register with `DataFetcherFactory.register_fetcher()`
    
    Example future sources:
    - MAVAT (Israeli planning portal)
    - Municipal APIs
    - Open data portals
    - International planning databases
    
    ### Technical Details
    
    - **Storage**: JSON files in `data/raw/`
    - **Format**: GeoJSON-like feature collections
    - **Encoding**: UTF-8 (supports Hebrew)
    - **Coordinate System**: ITM (EPSG:2039)
    
    ### Troubleshooting
    
    **No data showing:**
    - Click "Reload Data" in sidebar
    - Check `data/raw/iplan_layers.json` exists
    - Try importing sample data
    
    **Import fails:**
    - Verify JSON is valid
    - Check file has "features" array
    - Ensure UTF-8 encoding
    
    **Need more help:**
    - See `docs/DATA_MANAGEMENT.md`
    - Ask AI assistant for guidance
    """)

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("📁 **Data File:**")
    st.code(str(data_store.data_file))

with col2:
    st.markdown("🔧 **Status:**")
    if data_store.data_file.exists():
        st.success("Data file exists")
    else:
        st.warning("No data file")

with col3:
    st.markdown("💾 **Size:**")
    if data_store.data_file.exists():
        size_kb = data_store.data_file.stat().st_size / 1024
        st.info(f"{size_kb:.1f} KB")
    else:
        st.info("N/A")
