"""
Plan Analyzer - Visual analysis of building plans and regulations
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Plan Analyzer", page_icon="📐", layout="wide")

st.markdown("# 📐 Plan Analyzer")
st.markdown("### Analyze building rights, coverage, and compliance")

# Sidebar inputs
with st.sidebar:
    st.markdown("## 📝 Project Details")
    
    project_name = st.text_input("Project Name", "My Building Project")
    location = st.text_input("Location", "Tel Aviv")
    
    st.markdown("### 📏 Plot Dimensions")
    plot_size = st.number_input("Plot Size (sqm)", 100, 10000, 500)
    
    st.markdown("### 🏢 Zoning")
    zone_type = st.selectbox(
        "Zone Type",
        ["R1 - General Residential", "R2 - High Density Residential", 
         "C1 - Commercial", "M1 - Mixed Use"]
    )
    
    st.markdown("### 🎯 Building Parameters")
    floors = st.slider("Proposed Floors", 1, 10, 4)
    coverage = st.slider("Building Coverage (%)", 10, 100, 40)

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["📊 Analysis", "📈 Comparison", "✅ Compliance", "📄 Report"])

with tab1:
    st.markdown("## 📊 Building Rights Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📏 Current Parameters")
        
        # Calculate building rights
        max_coverage = {"R1": 40, "R2": 50, "C1": 60, "M1": 55}
        max_floors = {"R1": 4, "R2": 8, "C1": 6, "M1": 7}
        
        zone_key = zone_type.split(" - ")[0]
        allowed_coverage = max_coverage.get(zone_key, 40)
        allowed_floors = max_floors.get(zone_key, 4)
        
        # Display metrics
        st.metric("Plot Size", f"{plot_size} sqm")
        st.metric("Proposed Floors", f"{floors}", 
                 delta=f"{floors - allowed_floors} vs. max" if floors > allowed_floors else "✓ Compliant")
        st.metric("Building Coverage", f"{coverage}%",
                 delta=f"{coverage - allowed_coverage}% vs. max" if coverage > allowed_coverage else "✓ Compliant")
        
        # Calculate floor area
        floor_area = plot_size * (coverage / 100) * floors
        st.metric("Total Floor Area", f"{floor_area:.0f} sqm")
        
        # Building rights visualization
        st.markdown("### 📊 Coverage Visualization")
        
        fig = go.Figure()
        
        # Plot boundaries
        fig.add_trace(go.Scatter(
            x=[0, plot_size**0.5, plot_size**0.5, 0, 0],
            y=[0, 0, plot_size**0.5, plot_size**0.5, 0],
            fill="toself",
            fillcolor="lightgray",
            line=dict(color="black", width=2),
            name="Plot Boundary"
        ))
        
        # Building footprint
        building_width = (plot_size * coverage / 100) ** 0.5
        fig.add_trace(go.Scatter(
            x=[5, 5 + building_width, 5 + building_width, 5, 5],
            y=[5, 5, 5 + building_width, 5 + building_width, 5],
            fill="toself",
            fillcolor="rgba(46, 134, 171, 0.6)",
            line=dict(color="#2E86AB", width=2),
            name="Building Footprint"
        ))
        
        fig.update_layout(
            height=400,
            showlegend=True,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            title="Plot Layout (Top View)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📈 Compliance Status")
        
        # Compliance checks
        compliance_data = {
            'Regulation': [
                'Maximum Floors',
                'Building Coverage',
                'Floor Area Ratio',
                'Setback Requirements',
                'Parking Spaces'
            ],
            'Required': [
                f"≤ {allowed_floors}",
                f"≤ {allowed_coverage}%",
                "≤ 2.5",
                "≥ 3m",
                "1 per 50sqm"
            ],
            'Your Plan': [
                f"{floors}",
                f"{coverage}%",
                f"{floor_area / plot_size:.1f}",
                "3m",
                f"{int(floor_area / 50)}"
            ],
            'Status': [
                '✅' if floors <= allowed_floors else '❌',
                '✅' if coverage <= allowed_coverage else '❌',
                '✅' if floor_area / plot_size <= 2.5 else '❌',
                '✅',
                '✅'
            ]
        }
        
        df = pd.DataFrame(compliance_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Overall compliance score
        compliant_count = df['Status'].value_counts().get('✅', 0)
        total_count = len(df)
        compliance_score = (compliant_count / total_count) * 100
        
        st.markdown("### 🎯 Overall Compliance")
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=compliance_score,
            title={'text': "Compliance Score"},
            delta={'reference': 100},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "#2E86AB"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 75], 'color': "lightyellow"},
                    {'range': [75, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 80
                }
            }
        ))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("## 📈 Scenario Comparison")
    
    st.info("Compare different building scenarios to optimize your project")
    
    # Create comparison scenarios
    scenarios = pd.DataFrame({
        'Scenario': ['Current Plan', 'Max Allowed', 'TAMA 35 Option', 'Optimized'],
        'Floors': [floors, allowed_floors, floors + 2, allowed_floors],
        'Coverage (%)': [coverage, allowed_coverage, coverage - 5, allowed_coverage - 5],
        'Floor Area (sqm)': [
            floor_area,
            plot_size * (allowed_coverage / 100) * allowed_floors,
            plot_size * ((coverage - 5) / 100) * (floors + 2),
            plot_size * ((allowed_coverage - 5) / 100) * allowed_floors
        ]
    })
    
    # Bar chart comparison
    fig = px.bar(
        scenarios,
        x='Scenario',
        y='Floor Area (sqm)',
        color='Floors',
        title="Floor Area Comparison by Scenario",
        color_continuous_scale='Blues'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed comparison table
    st.dataframe(scenarios, use_container_width=True, hide_index=True)
    
    # ROI estimation
    st.markdown("### 💰 Estimated ROI")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Construction Cost", f"₪{floor_area * 6000:,.0f}")
    with col2:
        st.metric("Market Value", f"₪{floor_area * 15000:,.0f}")
    with col3:
        st.metric("Potential Profit", f"₪{floor_area * 9000:,.0f}")

with tab3:
    st.markdown("## ✅ Detailed Compliance Check")
    
    st.markdown("### 📋 Building Code Requirements")
    
    # Detailed compliance checklist
    compliance_categories = {
        '🏗️ Structural': [
            ('Foundation depth minimum 1.5m', True),
            ('Earthquake resistance standard', True),
            ('Fire safety compliance', True)
        ],
        '🚗 Parking & Access': [
            ('Parking spaces: 1 per 50sqm', True),
            ('Accessible parking: 5% of total', True),
            ('Access road width ≥ 6m', True)
        ],
        '🌳 Environmental': [
            ('Green area: 20% minimum', coverage < 80),
            ('Solar panels installation', False),
            ('Rainwater collection', False)
        ],
        '🔌 Utilities': [
            ('Electricity connection', True),
            ('Water supply', True),
            ('Sewage system', True)
        ]
    }
    
    for category, items in compliance_categories.items():
        with st.expander(category, expanded=True):
            for item, status in items:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(item)
                with col2:
                    if status:
                        st.success("✅")
                    else:
                        st.warning("⏳")

with tab4:
    st.markdown("## 📄 Generate Report")
    
    st.markdown("### 📊 Project Summary")
    
    # Report preview
    report_content = f"""
    # Building Analysis Report
    
    **Project:** {project_name}
    **Location:** {location}
    **Date:** {datetime.now().strftime("%Y-%m-%d")}
    
    ## Site Information
    - Plot Size: {plot_size} sqm
    - Zoning: {zone_type}
    
    ## Building Proposal
    - Floors: {floors}
    - Building Coverage: {coverage}%
    - Total Floor Area: {floor_area:.0f} sqm
    
    ## Compliance Status
    - Overall Compliance: {compliance_score:.0f}%
    - Maximum Floors: {'✅ Compliant' if floors <= allowed_floors else '❌ Non-compliant'}
    - Coverage: {'✅ Compliant' if coverage <= allowed_coverage else '❌ Non-compliant'}
    
    ## Recommendations
    1. Review setback requirements with local planning authority
    2. Consider TAMA 35 benefits for additional floors
    3. Ensure proper parking space allocation
    4. Plan for green building standards
    """
    
    st.markdown(report_content)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Download PDF Report", use_container_width=True, type="primary"):
            st.toast("PDF generation coming soon!", icon="ℹ️")
    with col2:
        if st.button("📧 Email Report", use_container_width=True):
            st.toast("Email feature coming soon!", icon="ℹ️")
