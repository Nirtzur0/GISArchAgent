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
from src.infrastructure.factory import get_factory
from src.vectorstore.management_service import VectorDBManagementService

st.set_page_config(page_title="Data Management", page_icon="💾", layout="wide")

st.markdown("# 💾 Data Management")
st.markdown("### Manage planning data sources, updates, and statistics")

# Initialize data store
@st.cache_resource
def get_data_store():
    return DataStore()

@st.cache_resource
def get_vectordb_service():
    factory = get_factory()
    repo = factory.get_regulation_repository()
    return VectorDBManagementService(repo)

data_store = get_data_store()
vectordb_service = get_vectordb_service()

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
    
    1. Visit [iPlan W�️ Vector Database Management")
    
    # Get status
    try:
        status = vectordb_service.get_status()
        
        # Status overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if status.get("initialized"):
                st.success("✓ Initialized")
            else:
                st.error("✗ Not Initialized")
        
        with col2:
            st.metric("Total Regulations", status.get("total_regulations", 0))
        
        with col3:
            health = status.get("health", "unknown")
            if health == "healthy":
                st.success(f"Health: {health}")
            else:
                st.warning(f"Health: {health}")
        
        st.markdown("---")
        
        # Details
        st.markdown("### 📋 Database Details")
        
        details_col1, details_col2 = st.columns(2)
        
        with details_col1:
            st.text(f"Collection: {status['statistics'].get('collection_name', 'N/A')}")
            st.text(f"Status: {status.get('status', 'N/A')}")
        
        with details_col2:
            st.text(f"Directory: {status['statistics'].get('persist_directory', 'N/A')}")
            st.text(f"Last Checked: {status.get('last_checked', 'N/A')[:19]}")
        
        st.markdown("---")
        
        # Actions
        st.markdown("### 🛠️ Management Actions")
        
        action_col1, action_col2, action_col3 = st.columns(3)
        
        with action_col1:
            if st.button("🔄 Check & Initialize", use_container_width=True):
                with st.spinner("Checking database..."):
                    result = vectordb_service.initialize_if_needed()
                    if result:
                        st.success("✓ Database is ready!")
                    else:
                        st.error("Failed to initialize database")
                    st.rerun()
        
        with action_col2:
            if st.button("📊 Refresh Status", use_container_width=True):
                st.cache_resource.clear()
                st.rerun()
        
        with action_col3:
            if st.button("🔨 Rebuild Database", use_container_width=True, type="secondary"):
                if st.session_state.get("confirm_rebuild"):
                    with st.spinner("Rebuilding database..."):
                        success = vectordb_service.rebuild_database()
                        if success:
                            st.success("✓ Database rebuilt successfully!")
                        else:
                            st.error("Failed to rebuild database")
                        st.session_state.confirm_rebuild = False
                        st.rerun()
                else:
                    st.session_state.confirm_rebuild = True
                    st.warning("⚠️ This will delete all data! Click again to confirm.")
        
        st.markdown("---")
        
        # Add regulation form
        with st.expander("➕ Add New Regulation"):
            st.markdown("#### Add a Regulation to Vector Database")
            
            reg_title = st.text_input("Title", placeholder="e.g., Building Height Regulations")
            reg_type = st.selectbox("Type", ["local", "national", "district"])
            reg_jurisdiction = st.text_input("Jurisdiction", value="national", placeholder="e.g., Tel Aviv, national")
            reg_summary = st.text_area("Summary (Optional)", placeholder="Brief summary of the regulation")
            reg_content = st.text_area("Content", height=200, placeholder="Full regulation text...")
            
            if st.button("Add Regulation", type="primary"):
                if not reg_title or not reg_content:
                    st.error("Title and content are required!")
                else:
                    from src.domain.entities.regulation import RegulationType
                    success = vectordb_service.add_regulation(
                        title=reg_title,
                        content=reg_content,
                        reg_type=RegulationType(reg_type),
                        jurisdiction=reg_jurisdiction,
                        summary=reg_summary if reg_summary else None
                    )
                    
                    if success:
                        st.success("✓ Regulation added successfully!")
                        st.cache_resource.clear()
                    else:
                        st.error("Failed to add regulation")
        
        # Search regulations
        with st.expander("🔍 Search Regulations"):
            st.markdown("#### Search Vector Database")
            
            search_query = st.text_input("Search Query", placeholder="e.g., parking requirements")
            search_limit = st.slider("Max Results", 1, 20, 5)
            
            if st.button("Search", type="primary"):
                if search_query:
                    results = vectordb_service.search_regulations(search_query, limit=search_limit)
                    
                    if results:
                        st.success(f"Found {len(results)} results")
                        for i, reg in enumerate(results):
                            with st.container():
                                st.markdown(f"**{i+1}. {reg.title}**")
                                st.text(f"Type: {reg.type.value} | Jurisdiction: {reg.jurisdiction}")
                                if reg.summary:
                                    st.markdown(f"*{reg.summary}*")
                                with st.expander("View Content"):
                                    st.text(reg.content)
                                st.markdown("---")
                    else:
                        st.info("No results found")
                else:
                    st.warning("Please enter a search query")
        
        # Import/Export
        with st.expander("📥 Import/Export Regulations"):
            st.markdown("#### Import from JSON File")
            
            uploaded_reg_file = st.file_uploader(
                "Upload Regulations JSON",
                type=["json"],
                help="Upload a JSON file with regulations"
            )
            
            if uploaded_reg_file:
                try:
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as tmp:
                        tmp.write(uploaded_reg_file.getvalue())
                        tmp_path = tmp.name
                    
                    if st.button("Import Regulations", type="primary"):
                        result = vectordb_service.import_from_file(tmp_path)
                        if result.get("error"):
                            st.error(f"Import failed: {result['error']}")
                        else:
                            st.success(f"✓ Imported {result['success']} regulations")
                            if result.get("failed", 0) > 0:
                                st.warning(f"Failed to import {result['failed']} regulations")
                        st.cache_resource.clear()
                except Exception as e:
                    st.error(f"Error: {e}")
            
            st.markdown("---")
            st.markdown("#### Export to JSON File")
            
            export_filename = st.text_input("Export Filename", value="regulations_export.json")
            
            if st.button("Export All Regulations"):
                import tempfile
                from pathlib import Path
                
                with tempfile.TemporaryDirectory() as tmpdir:
                    export_path = Path(tmpdir) / export_filename
                    success = vectordb_service.export_to_file(str(export_path))
                    
                    if success:
                        with open(export_path, 'rb') as f:
                            st.download_button(
                                label="📥 Download Export",
                                data=f.read(),
                                file_name=export_filename,
                                mime="application/json"
                            )
                    else:
                        st.error("Export failed")
    
    except Exception as e:
        st.error(f"Error accessing vector database: {e}")
        st.info("The vector database may not be initialized yet. Try clicking 'Check & Initialize' above.")

with tab5:
    st.markdown("## �ebsite](https://www.iplan.gov.il)
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
