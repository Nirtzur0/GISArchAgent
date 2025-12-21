"""
Map Viewer Page - Interactive map for visualizing plans and locations
"""

import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
from datetime import datetime
from pyproj import Transformer

# Import data management
from src.data_management import DataStore

st.set_page_config(page_title="Map Viewer", page_icon="📍", layout="wide")

st.markdown("# 📍 Interactive Map Viewer")
st.markdown("### Visualize planning schemes, TAMA zones, and building locations")

# Initialize session state
if 'map_markers' not in st.session_state:
    st.session_state.map_markers = []

# Load data store
@st.cache_resource
def get_data_store():
    return DataStore()

data_store = get_data_store()

# Get all features and stats
all_features = data_store.get_all_features()
stats = data_store.get_statistics()

# Setup coordinate transformer (ITM to WGS84)
transformer = Transformer.from_crs("EPSG:2039", "EPSG:4326", always_xy=True)

# Sidebar controls
with st.sidebar:
    st.markdown("## 🗺️ Map Controls")
    
    # Filters
    st.markdown("### 🔍 Filters")
    
    districts = ["All"] + data_store.get_unique_values("district_name")
    selected_district = st.selectbox("District", districts)
    
    cities = ["All"] + data_store.get_unique_values("plan_county_name")
    selected_city = st.selectbox("City", cities)
    
    statuses = ["All"] + data_store.get_unique_values("station_desc")
    selected_status = st.selectbox("Status", statuses)
    
    # Layer selection
    st.markdown("### 📊 Display Options")
    show_polygons = st.checkbox("Show Plan Boundaries", value=True)
    show_markers = st.checkbox("Show Plan Markers", value=True)
    color_by = st.selectbox("Color By", ["District", "Status", "City"])
    
    # Map style
    st.markdown("### 🎨 Map Style")
    map_style = st.selectbox(
        "Style",
        ["OpenStreetMap", "CartoDB Positron", "CartoDB Dark Matter"],
        label_visibility="collapsed"
    )

# Main content
col1, col2 = st.columns([3, 1])

# Filter features
filtered_features = data_store.search_features(
    district=None if selected_district == "All" else selected_district,
    city=None if selected_city == "All" else selected_city,
    status=None if selected_status == "All" else selected_status
)

# Color schemes
color_schemes = {
    "District": {
        "מחוז ירושלים": "#FF6B6B",
        "מחוז חיפה": "#4ECDC4",
        "מחוז המרכז": "#45B7D1",
        "מחוז תל אביב": "#FFA07A",
        "מחוז הצפון": "#98D8C8",
        "מחוז הדרום": "#FFD93D",
    },
    "Status": {
        "תכנית שאושרה (מתקדמות)": "#4CAF50",
        "תכנית במוסדות התכנון": "#FF9800",
        "תכנית תלויה ועומדת": "#F44336",
    },
    "City": {}  # Will be generated dynamically
}

def get_color(feature, color_by):
    """Get color for a feature based on color_by field"""
    attrs = feature.get("attributes", {})
    
    if color_by == "District":
        value = attrs.get("district_name", "Unknown")
        return color_schemes["District"].get(value, "#999999")
    elif color_by == "Status":
        value = attrs.get("station_desc", "Unknown")
        return color_schemes["Status"].get(value, "#999999")
    else:  # City
        # Generate consistent color from city name
        value = attrs.get("plan_county_name", "Unknown")
        hash_val = sum(ord(c) for c in value)
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8", "#FFD93D"]
        return colors[hash_val % len(colors)]

def transform_coordinates(rings):
    """Transform ITM coordinates to WGS84"""
    try:
        transformed_rings = []
        for ring in rings:
            transformed_ring = []
            for x, y in ring:
                lon, lat = transformer.transform(x, y)
                transformed_ring.append([lat, lon])
            transformed_rings.append(transformed_ring)
        return transformed_rings
    except Exception as e:
        return None

with col1:
    # Create base map centered on Israel
    m = folium.Map(
        location=[31.7683, 35.2137],  # Jerusalem coordinates
        zoom_start=8,
        tiles=map_style.replace(" ", "")
    )
    
    # Add planning features
    for feature in filtered_features:
        attrs = feature.get("attributes", {})
        geometry = feature.get("geometry", {})
        
        # Get color
        color = get_color(feature, color_by)
        
        # Create popup content
        popup_html = f"""
        <div style="min-width: 200px">
            <h4>{attrs.get('pl_number', 'N/A')}</h4>
            <b>{attrs.get('pl_name', 'Unnamed')[:60]}</b><br><br>
            <b>District:</b> {attrs.get('district_name', 'N/A')}<br>
            <b>City:</b> {attrs.get('plan_county_name', 'N/A')}<br>
            <b>Status:</b> {attrs.get('station_desc', 'N/A')}<br>
            <b>Area:</b> {attrs.get('pl_area_dunam', 0)} dunam<br>
        </div>
        """
        
        # Add polygon if geometry exists
        if show_polygons and geometry.get("rings"):
            transformed = transform_coordinates(geometry["rings"])
            if transformed:
                for ring in transformed:
                    folium.Polygon(
                        locations=ring,
                        popup=folium.Popup(popup_html, max_width=300),
                        color=color,
                        weight=2,
                        fill=True,
                        fillColor=color,
                        fillOpacity=0.3
                    ).add_to(m)
        
        # Add marker at centroid
        if show_markers and geometry.get("rings"):
            transformed = transform_coordinates(geometry["rings"])
            if transformed and transformed[0]:
                # Calculate centroid
                coords = transformed[0]
                center_lat = sum(c[0] for c in coords) / len(coords)
                center_lon = sum(c[1] for c in coords) / len(coords)
                
                folium.CircleMarker(
                    location=[center_lat, center_lon],
                    radius=5,
                    popup=folium.Popup(popup_html, max_width=300),
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.8
                ).add_to(m)
    
    # Display map
    folium_static(m, width=1000, height=600)

with col2:
    st.markdown("### 📊 Map Statistics")
    
    # Stats cards
    st.metric("Displayed Plans", len(filtered_features))
    st.metric("Total Plans", stats["total_plans"])
    st.metric("Districts", len(stats["by_district"]))
    st.metric("Cities", len(stats["by_city"]))
    
    st.markdown("---")
    
    st.markdown("### 🎨 Legend")
    
    if color_by == "District":
        for district, color in color_schemes["District"].items():
            if district in stats["by_district"]:
                count = stats["by_district"][district]
                st.markdown(f"<span style='color:{color}'>●</span> {district} ({count})", unsafe_allow_html=True)
    elif color_by == "Status":
        for status, color in color_schemes["Status"].items():
            if status in stats["by_status"]:
                count = stats["by_status"][status]
                st.markdown(f"<span style='color:{color}'>●</span> {status} ({count})", unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 🎯 Quick Actions")
    
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()
    
    if st.button("📊 View Details", use_container_width=True):
        st.switch_page("pages/3_💾_Data_Management.py")

# Summary
st.markdown("---")
st.markdown(f"### 📋 Showing {len(filtered_features)} of {stats['total_plans']} plans")

if len(filtered_features) > 0:
    # Create summary table
    summary_data = []
    for feature in filtered_features[:10]:  # Show first 10
        attrs = feature.get("attributes", {})
        summary_data.append({
            "Plan Number": attrs.get("pl_number", "N/A"),
            "Name": attrs.get("pl_name", "N/A")[:50],
            "City": attrs.get("plan_county_name", "N/A"),
            "Status": attrs.get("station_desc", "N/A"),
            "Area (dunam)": attrs.get("pl_area_dunam", 0)
        })
    
    df = pd.DataFrame(summary_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    if len(filtered_features) > 10:
        st.info(f"Showing first 10 plans. Use Data Management page to browse all {len(filtered_features)} plans.")
else:
    st.info("No plans match the current filters. Try adjusting the filter criteria.")
