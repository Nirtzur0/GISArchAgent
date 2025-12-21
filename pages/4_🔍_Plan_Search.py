"""
Plan Search Page with Automatic Vision Analysis
Search for plans from iPlan and get automatic AI visual analysis
"""

import streamlit as st
from PIL import Image
from io import BytesIO
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scrapers.realtime_fetcher import get_fetcher
from src.vision import get_vision_analyzer

st.set_page_config(
    page_title="Plan Search",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .plan-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .analysis-box {
        background: #f8f9fa;
        padding: 15px;
        border-left: 4px solid #667eea;
        border-radius: 5px;
        margin: 10px 0;
    }
    .stats-badge {
        display: inline-block;
        padding: 5px 10px;
        background: #667eea;
        color: white;
        border-radius: 15px;
        font-size: 12px;
        margin: 5px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔍 Plan Search with Vision AI")
st.markdown("Search for planning schemes from iPlan and get automatic visual analysis powered by AI")

# Initialize services
@st.cache_resource
def init_services():
    fetcher = get_fetcher()
    analyzer = get_vision_analyzer()
    return fetcher, analyzer

fetcher, analyzer = init_services()

# Search interface
st.markdown("### 🔎 Search Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    search_mode = st.selectbox(
        "Search By",
        ["Location", "Plan ID", "Keyword"],
        help="Choose how to search for plans"
    )

with col2:
    if search_mode == "Location":
        search_value = st.text_input("City/Location", placeholder="e.g., Tel Aviv, Jerusalem")
    elif search_mode == "Plan ID":
        search_value = st.text_input("Plan Number", placeholder="e.g., 101-0123456")
    else:
        search_value = st.text_input("Search Term", placeholder="e.g., TAMA 35, residential")

with col3:
    include_analysis = st.checkbox("🎨 Include Vision Analysis", value=True, 
                                   help="Automatically analyze plan images with AI")
    max_results = st.slider("Max Results", 1, 5, 3)

# Search button
if st.button("🔍 Search Plans", type="primary", use_container_width=True):
    if not search_value:
        st.warning("⚠️ Please enter a search value")
    else:
        with st.spinner(f"Searching for plans in {search_value}..."):
            try:
                results = []
                
                # Perform search based on mode
                if search_mode == "Plan ID":
                    result = fetcher.get_plan_with_image('planning', search_value)
                    if result:
                        results = [result]
                elif search_mode == "Location":
                    # Get plans by location
                    plans = fetcher.get_plans_by_location(search_value)
                    # Fetch images for top results
                    for plan in plans[:max_results]:
                        plan_num = plan.get('attributes', {}).get('PLAN_NUMBER') or plan.get('attributes', {}).get('PLAN_ID')
                        if plan_num:
                            plan_with_img = fetcher.get_plan_with_image('planning', str(plan_num))
                            if plan_with_img:
                                results.append(plan_with_img)
                else:  # Keyword
                    features = fetcher.search_by_keyword(search_value)
                    for feature in features[:max_results]:
                        plan_num = feature.get('attributes', {}).get('PLAN_NUMBER') or feature.get('attributes', {}).get('PLAN_ID')
                        if plan_num:
                            plan_with_img = fetcher.get_plan_with_image('planning', str(plan_num))
                            if plan_with_img:
                                results.append(plan_with_img)
                
                if not results:
                    st.info("ℹ️ No plans found. Try a different search term or location.")
                else:
                    st.success(f"✅ Found {len(results)} plan(s)")
                    
                    # Display results
                    for idx, result in enumerate(results, 1):
                        st.markdown("---")
                        
                        plan_data = result.get('plan_data', {})
                        
                        # Plan header
                        st.markdown(f"""
                        <div class="plan-card">
                            <h3>{idx}. {plan_data.get('PLAN_NAME', plan_data.get('PL_NAME_HEB', 'Unnamed Plan'))}</h3>
                            <p><strong>Plan ID:</strong> {plan_data.get('PLAN_NUMBER', plan_data.get('PLAN_ID', 'N/A'))}</p>
                            <p><strong>Location:</strong> {plan_data.get('CITY_NAME', plan_data.get('SETTLEMENT', 'N/A'))}</p>
                            <p><strong>Status:</strong> {plan_data.get('PLAN_STATUS', 'N/A')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Image and analysis
                        if result.get('has_image'):
                            col_img, col_analysis = st.columns([1, 1])
                            
                            with col_img:
                                st.markdown("#### 🗺️ Plan Map")
                                image_bytes = result.get('image_bytes')
                                image = Image.open(BytesIO(image_bytes))
                                st.image(image, use_container_width=True)
                                
                                # Download button
                                st.download_button(
                                    label="📥 Download Image",
                                    data=image_bytes,
                                    file_name=f"plan_{plan_data.get('PLAN_NUMBER', idx)}.png",
                                    mime="image/png",
                                    key=f"download_{idx}"
                                )
                            
                            with col_analysis:
                                st.markdown("#### 🎨 Vision Analysis")
                                
                                if include_analysis:
                                    with st.spinner("Analyzing plan image with AI..."):
                                        try:
                                            analysis_result = analyzer.analyze_plan_image(
                                                image,
                                                question="Analyze this planning map in detail. What are the key features, zones, land use designations, and any notable patterns or regulations visible?"
                                            )
                                            
                                            st.markdown(f"""
                                            <div class="analysis-box">
                                                <h5>🤖 AI Analysis:</h5>
                                                <p>{analysis_result['analysis']}</p>
                                            </div>
                                            """, unsafe_allow_html=True)
                                            
                                            # Stats
                                            stats_col1, stats_col2, stats_col3 = st.columns(3)
                                            with stats_col1:
                                                st.metric("Tokens Used", analysis_result.get('tokens_used', 0))
                                            with stats_col2:
                                                if analysis_result.get('ocr_text'):
                                                    word_count = len(analysis_result['ocr_text'].split())
                                                    st.metric("Text Extracted", f"{word_count} words")
                                                else:
                                                    st.metric("Text Extracted", "0 words")
                                            with stats_col3:
                                                st.metric("From Cache", "✅" if analysis_result.get('from_cache') else "🔄")
                                            
                                            # OCR text expander
                                            if analysis_result.get('ocr_text'):
                                                with st.expander("📝 View Extracted Text"):
                                                    st.text_area(
                                                        "OCR Text",
                                                        analysis_result['ocr_text'],
                                                        height=200,
                                                        key=f"ocr_{idx}"
                                                    )
                                            
                                            # Ask follow-up question
                                            with st.expander("❓ Ask a Question About This Plan"):
                                                question = st.text_input(
                                                    "Your question",
                                                    placeholder="e.g., What are the building height restrictions?",
                                                    key=f"q_{idx}"
                                                )
                                                if st.button("Ask", key=f"ask_{idx}"):
                                                    if question:
                                                        with st.spinner("Analyzing..."):
                                                            answer = analyzer.ask_about_plan(image, question)
                                                            st.markdown(f"**Answer:** {answer['analysis']}")
                                                    else:
                                                        st.warning("Please enter a question")
                                        
                                        except Exception as e:
                                            st.error(f"⚠️ Vision analysis failed: {str(e)}")
                                else:
                                    st.info("Vision analysis disabled. Enable it in search parameters to analyze this plan.")
                        else:
                            st.warning("⚠️ No map image available for this plan")
                        
                        # Additional plan details
                        with st.expander("📋 Full Plan Details"):
                            st.json(plan_data)
            
            except Exception as e:
                st.error(f"❌ Search failed: {str(e)}")
                st.exception(e)

# Sidebar info
with st.sidebar:
    st.markdown("### 🔍 Search Tips")
    st.markdown("""
    **By Location:**
    - Use Hebrew or English city names
    - Try "Tel Aviv", "Jerusalem", "Haifa"
    
    **By Plan ID:**
    - Format: 101-0123456
    - Check iPlan website for exact IDs
    
    **By Keyword:**
    - Try "TAMA 35", "residential", "commercial"
    - Search by regulation type
    
    **Vision Analysis:**
    - Automatically analyzes plan maps
    - Extracts text with OCR
    - Identifies zones and features
    - Cached for efficiency
    """)
    
    st.markdown("---")
    st.markdown("### 💡 About Vision Analysis")
    st.markdown("""
    The AI analyzes planning maps to:
    - 🏗️ Identify building zones
    - 📏 Detect dimensions
    - 📝 Extract text from maps
    - 🎨 Describe visual features
    - ⚖️ Identify regulations
    """)
    
    # Cache stats
    st.markdown("---")
    st.markdown("### 💾 Cache Stats")
    cache_info = analyzer.get_cache_stats()
    st.metric("Cached Images", cache_info['total_cached'])
    st.metric("Total Size", f"{cache_info['total_size_mb']:.1f} MB")
