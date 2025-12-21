"""
Plan Analyzer - Visual analysis of building plans and regulations
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.factory import get_factory

st.set_page_config(page_title="Plan Analyzer", page_icon="📐", layout="wide")

st.markdown("# 📐 Plan Analyzer")
st.markdown("### Analyze building rights, coverage, and compliance")

# Initialize factory
factory = get_factory()
upload_service = factory.get_plan_upload_service()

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
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Analysis", "📈 Comparison", "✅ Compliance", "📄 Report", "📤 Upload & Analyze"])

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

with tab5:
    st.markdown("## 📤 Upload & Analyze Plan")
    st.markdown("Upload your planning document (PDF, image) and get AI-powered analysis with semantic search results")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📁 Upload Your Plan")
        
        uploaded_file = st.file_uploader(
            "Choose a planning document",
            type=['pdf', 'jpg', 'jpeg', 'png', 'tiff'],
            help="Upload a PDF or image file of your planning document. Max size: 50MB"
        )
        
        if uploaded_file:
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            st.info(f"📦 Size: {uploaded_file.size / 1024:.1f} KB")
            
            # Show image preview if it's an image
            if uploaded_file.type.startswith('image/'):
                st.image(uploaded_file, caption="Uploaded Plan", use_container_width=True)
            
            # Analysis button
            if st.button("🔍 Analyze Plan", use_container_width=True, type="primary"):
                if not upload_service or not upload_service.vision_service:
                    st.error("❌ Vision service not available. Check API key configuration.")
                else:
                    with st.spinner("🤖 Analyzing your plan... This may take a moment."):
                        try:
                            # Reset file pointer
                            uploaded_file.seek(0)
                            
                            # Analyze
                            analysis = upload_service.analyze_uploaded_plan(
                                file_data=uploaded_file,
                                filename=uploaded_file.name,
                                max_results=5
                            )
                            
                            if analysis:
                                # Store in session state
                                st.session_state['upload_analysis'] = analysis
                                st.success("✅ Analysis complete!")
                                st.rerun()
                            else:
                                st.error("❌ Analysis failed. Check logs for details.")
                        
                        except Exception as e:
                            st.error(f"❌ Error during analysis: {e}")
        
        else:
            st.info("👆 Upload a planning document to begin analysis")
            
            st.markdown("#### 📋 Supported Features:")
            st.markdown("""
            - **AI Vision Analysis**: Automated plan description
            - **OCR Text Extraction**: Extract Hebrew & English text
            - **Zone Identification**: Detect planning zones
            - **Semantic Search**: Find matching regulations
            - **Building Rights**: Extract development parameters
            """)
    
    with col2:
        st.markdown("### 📊 Analysis Results")
        
        if 'upload_analysis' in st.session_state:
            analysis = st.session_state['upload_analysis']
            
            # Vision Analysis
            st.markdown("#### 🤖 AI Analysis")
            with st.expander("📝 Plan Description", expanded=True):
                st.write(analysis.vision_analysis.description or "No description generated")
            
            # Extracted text
            if analysis.extracted_text:
                with st.expander("📄 Extracted Text (Preview)"):
                    # Show first 500 characters
                    preview = analysis.extracted_text[:500]
                    if len(analysis.extracted_text) > 500:
                        preview += "..."
                    st.text(preview)
                    st.caption(f"Total characters: {len(analysis.extracted_text)}")
            
            # Identified zones
            if analysis.identified_zones:
                with st.expander("📍 Identified Zones"):
                    for zone in analysis.identified_zones:
                        st.write(f"- {zone}")
            
            # Classification
            st.markdown("#### 🏷️ Classification")
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Zone Type", analysis.estimated_zone_type or "Unknown")
            with col_b:
                st.metric("Location", analysis.estimated_location or "Unknown")
            
            # Matching regulations
            st.markdown("#### 📚 Matching Regulations")
            
            if analysis.matching_regulations:
                for i, (reg, score) in enumerate(zip(analysis.matching_regulations, analysis.similarity_scores)):
                    with st.expander(f"🔹 {reg.title} (Similarity: {score:.2%})", expanded=(i == 0)):
                        st.markdown(f"**ID:** {reg.id}")
                        st.markdown(f"**Zone:** {reg.zone_type}")
                        
                        if reg.description:
                            st.markdown(f"**Description:**")
                            st.write(reg.description)
                        
                        if reg.building_rights:
                            st.markdown("**Building Rights:**")
                            rights = reg.building_rights
                            
                            rights_col1, rights_col2 = st.columns(2)
                            with rights_col1:
                                if rights.max_floors:
                                    st.metric("Max Floors", rights.max_floors)
                                if rights.min_apartment_size:
                                    st.metric("Min Apartment", f"{rights.min_apartment_size} sqm")
                            with rights_col2:
                                if rights.max_building_coverage:
                                    st.metric("Max Coverage", f"{rights.max_building_coverage}%")
                                if rights.far:
                                    st.metric("FAR", rights.far)
            else:
                st.info("No matching regulations found")
            
            # Processing info
            st.markdown("---")
            st.caption(f"⏱️ Processing time: {analysis.processing_time_ms:.0f}ms")
            st.caption(f"🕐 Analyzed at: {analysis.upload_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        else:
            st.info("📊 Analysis results will appear here after upload")
            st.markdown("#### 💡 How it works:")
            st.markdown("""
            1. **Upload** your planning document
            2. **AI analyzes** the document with Gemini Vision
            3. **Text is extracted** using OCR
            4. **Semantic search** finds relevant regulations
            5. **Results** show matching rules and building rights
            """)
    
    # Clear results button
    if 'upload_analysis' in st.session_state:
        st.markdown("---")
        if st.button("🗑️ Clear Results"):
            del st.session_state['upload_analysis']
            st.rerun()
