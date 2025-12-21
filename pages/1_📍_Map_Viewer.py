"""
Map Viewer Page - Interactive map for visualizing plans and locations
"""

import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Map Viewer", page_icon="📍", layout="wide")

st.markdown("# 📍 Interactive Map Viewer")
st.markdown("### Visualize planning schemes, TAMA zones, and building locations")

# Initialize session state for map markers
if 'map_markers' not in st.session_state:
    st.session_state.map_markers = []

# Sidebar controls
with st.sidebar:
    st.markdown("## 🗺️ Map Controls")
    
    # Location search
    location = st.text_input("🔍 Search Location", placeholder="Tel Aviv, Jerusalem...")
    
    # Layer selection
    st.markdown("### 📊 Layers")
    show_tama35 = st.checkbox("TAMA 35 Zones", value=True)
    show_tama38 = st.checkbox("TAMA 38 Zones", value=True)
    show_zoning = st.checkbox("Zoning Areas", value=True)
    show_plans = st.checkbox("Planning Schemes", value=False)
    
    # Map style
    st.markdown("### 🎨 Map Style")
    map_style = st.selectbox(
        "Style",
        ["OpenStreetMap", "CartoDB Positron", "CartoDB Dark Matter"],
        label_visibility="collapsed"
    )

# Main content
col1, col2 = st.columns([3, 1])

with col1:
    # Create base map centered on Israel
    m = folium.Map(
        location=[31.7683, 35.2137],  # Jerusalem coordinates
        zoom_start=8,
        tiles=map_style.replace(" ", "")
    )
    
    # Sample TAMA 35 zones (Tel Aviv area)
    if show_tama35:
        tama35_locations = [
            {"name": "Tel Aviv North", "lat": 32.0853, "lon": 34.7818, "buildings": 245},
            {"name": "Ramat Gan", "lat": 32.0853, "lon": 34.8116, "buildings": 180},
            {"name": "Givatayim", "lat": 32.0719, "lon": 34.8106, "buildings": 156},
        ]
        
        for loc in tama35_locations:
            folium.Circle(
                location=[loc["lat"], loc["lon"]],
                radius=1000,
                popup=f"<b>{loc['name']}</b><br>TAMA 35 Zone<br>Buildings: {loc['buildings']}",
                color="#2E86AB",
                fill=True,
                fillColor="#2E86AB",
                fillOpacity=0.3
            ).add_to(m)
            
            folium.Marker(
                location=[loc["lat"], loc["lon"]],
                popup=f"<b>{loc['name']}</b><br>TAMA 35 Zone",
                icon=folium.Icon(color="blue", icon="home", prefix="fa")
            ).add_to(m)
    
    # Sample TAMA 38 zones (Jerusalem area)
    if show_tama38:
        tama38_locations = [
            {"name": "Jerusalem Center", "lat": 31.7683, "lon": 35.2137, "projects": 42},
            {"name": "Jerusalem South", "lat": 31.7467, "lon": 35.2190, "projects": 38},
        ]
        
        for loc in tama38_locations:
            folium.Circle(
                location=[loc["lat"], loc["lon"]],
                radius=1500,
                popup=f"<b>{loc['name']}</b><br>TAMA 38 Zone<br>Projects: {loc['projects']}",
                color="#A23B72",
                fill=True,
                fillColor="#A23B72",
                fillOpacity=0.3
            ).add_to(m)
            
            folium.Marker(
                location=[loc["lat"], loc["lon"]],
                popup=f"<b>{loc['name']}</b><br>TAMA 38 Zone",
                icon=folium.Icon(color="purple", icon="building", prefix="fa")
            ).add_to(m)
    
    # Zoning areas
    if show_zoning:
        zoning_areas = [
            {"name": "Haifa Port", "lat": 32.8191, "lon": 34.9983, "zone": "Mixed Use", "color": "#F18F01"},
            {"name": "Beersheba Center", "lat": 31.2529, "lon": 34.7915, "zone": "Commercial", "color": "#667eea"},
        ]
        
        for zone in zoning_areas:
            folium.Marker(
                location=[zone["lat"], zone["lon"]],
                popup=f"<b>{zone['name']}</b><br>Zone: {zone['zone']}",
                icon=folium.Icon(color="orange", icon="info-sign")
            ).add_to(m)
    
    # Display map
    folium_static(m, width=1000, height=600)

with col2:
    st.markdown("### 📊 Map Statistics")
    
    # Stats cards
    st.metric("TAMA 35 Zones", "3", delta="Active")
    st.metric("TAMA 38 Projects", "2", delta="In Progress")
    st.metric("Total Buildings", "581", delta="+23 this month")
    
    st.markdown("---")
    
    st.markdown("### 🎯 Selected Location")
    st.info("Click on a marker to view details")
    
    st.markdown("---")
    
    st.markdown("### 📥 Export Options")
    if st.button("📄 Export as PDF", use_container_width=True):
        st.toast("PDF export coming soon!", icon="ℹ️")
    
    if st.button("📊 Export Data", use_container_width=True):
        st.toast("Data export coming soon!", icon="ℹ️")

# Legend
st.markdown("---")
st.markdown("### 🗺️ Map Legend")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("🔵 **TAMA 35** - Building reinforcement zones")
with col2:
    st.markdown("🟣 **TAMA 38** - Public building protection")
with col3:
    st.markdown("🟠 **Zoning** - Land use designations")
with col4:
    st.markdown("📍 **Plans** - Active planning schemes")

# Recent activity
st.markdown("---")
st.markdown("### 📅 Recent Planning Activity")

recent_data = pd.DataFrame({
    'Date': ['2025-12-20', '2025-12-19', '2025-12-18', '2025-12-17'],
    'Location': ['Tel Aviv North', 'Jerusalem Center', 'Haifa Port', 'Ramat Gan'],
    'Type': ['TAMA 35', 'TAMA 38', 'Zoning Change', 'TAMA 35'],
    'Status': ['Approved', 'Under Review', 'Approved', 'Approved']
})

st.dataframe(recent_data, use_container_width=True)
