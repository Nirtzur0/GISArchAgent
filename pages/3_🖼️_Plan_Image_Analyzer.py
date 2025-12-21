"""
Plan Image Analyzer Page - Upload and analyze architectural plans with AI vision
"""

import streamlit as st
from PIL import Image
import io
from datetime import datetime

from src.vision import get_vision_analyzer

st.set_page_config(page_title="Plan Image Analyzer", page_icon="🖼️", layout="wide")

st.markdown("# 🖼️ Plan Image Analyzer")
st.markdown("### Upload architectural plans and ask questions using AI vision")

# Initialize vision analyzer
if 'vision_analyzer' not in st.session_state:
    st.session_state.vision_analyzer = get_vision_analyzer()

# Sidebar
with st.sidebar:
    st.markdown("## 📤 Upload Options")
    
    upload_method = st.radio(
        "How do you want to provide the plan?",
        ["Upload Image", "Image URL", "Sample Plans"]
    )
    
    st.markdown("---")
    
    st.markdown("### 💡 Tips")
    st.info("""
    **Best Practices:**
    - Use clear, high-resolution images
    - Ensure text is readable
    - JPEG or PNG formats
    - Max size: 10MB
    
    **AI can extract:**
    - Dimensions & measurements
    - Room labels & numbers
    - Zoning information
    - Regulatory markings
    - Hebrew & English text
    """)
    
    st.markdown("---")
    
    # Cache stats
    cache_stats = st.session_state.vision_analyzer.get_cache_stats()
    st.markdown("### 📊 Cache Stats")
    st.metric("Cached Analyses", cache_stats['total_cached_analyses'])
    st.metric("Tokens Saved", f"{cache_stats['estimated_tokens_saved']:,}")

# Main content
tab1, tab2, tab3 = st.tabs(["🔍 Analyze", "📚 History", "⚙️ Settings"])

with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📸 Plan Image")
        
        image_to_analyze = None
        image_source = None
        
        if upload_method == "Upload Image":
            uploaded_file = st.file_uploader(
                "Choose an image file",
                type=['png', 'jpg', 'jpeg', 'pdf'],
                help="Upload architectural plans, site maps, or zoning diagrams"
            )
            
            if uploaded_file:
                # Save uploaded file temporarily
                image_bytes = uploaded_file.read()
                image_to_analyze = Image.open(io.BytesIO(image_bytes))
                image_source = f"uploaded_{uploaded_file.name}"
                st.image(image_to_analyze, caption="Uploaded Plan", use_container_width=True)
        
        elif upload_method == "Image URL":
            image_url = st.text_input(
                "Enter image URL",
                placeholder="https://example.com/plan.jpg"
            )
            
            if image_url:
                try:
                    import requests
                    response = requests.get(image_url)
                    image_bytes = response.content
                    image_to_analyze = Image.open(io.BytesIO(image_bytes))
                    image_source = image_url
                    st.image(image_to_analyze, caption="Plan from URL", use_container_width=True)
                except Exception as e:
                    st.error(f"Error loading image: {e}")
        
        else:  # Sample Plans
            sample_plans = {
                "Sample Site Plan": "https://via.placeholder.com/800x600/2E86AB/FFFFFF?text=Sample+Site+Plan",
                "Sample Floor Plan": "https://via.placeholder.com/600x800/A23B72/FFFFFF?text=Sample+Floor+Plan",
                "Sample Zoning Map": "https://via.placeholder.com/800x600/F18F01/FFFFFF?text=Sample+Zoning+Map",
            }
            
            selected_sample = st.selectbox("Choose a sample plan", list(sample_plans.keys()))
            
            if selected_sample:
                image_url = sample_plans[selected_sample]
                try:
                    import requests
                    response = requests.get(image_url)
                    image_bytes = response.content
                    image_to_analyze = Image.open(io.BytesIO(image_bytes))
                    image_source = image_url
                    st.image(image_to_analyze, caption=selected_sample, use_container_width=True)
                except Exception as e:
                    st.error(f"Error loading sample: {e}")
    
    with col2:
        st.markdown("### 💬 Ask Questions")
        
        # Analysis mode
        analysis_mode = st.radio(
            "What do you want to do?",
            ["General Analysis", "Ask Specific Question"],
            horizontal=True
        )
        
        question = ""
        if analysis_mode == "Ask Specific Question":
            question = st.text_area(
                "Your question about the plan",
                placeholder="E.g., What is the plot size? What zoning is shown? What are the setback requirements?",
                height=100
            )
        
        # Quick question buttons
        st.markdown("**Quick Questions:**")
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("📏 Plot Dimensions", use_container_width=True):
                question = "What are the plot dimensions and total area shown in this plan?"
            if st.button("🏢 Building Info", use_container_width=True):
                question = "What building information is shown (floors, height, coverage)?"
        
        with col_b:
            if st.button("🗺️ Zoning Details", use_container_width=True):
                question = "What zoning designation and requirements are indicated?"
            if st.button("📝 All Text", use_container_width=True):
                question = "Extract all text visible in the plan (Hebrew and English)"
        
        # Analyze button
        st.markdown("---")
        
        analyze_button = st.button(
            "🔍 Analyze Plan with AI Vision",
            type="primary",
            use_container_width=True,
            disabled=image_to_analyze is None
        )
        
        if analyze_button and image_to_analyze:
            with st.spinner("🤖 AI is analyzing the plan... This may take a moment."):
                try:
                    # Convert image to bytes for analysis
                    img_byte_arr = io.BytesIO()
                    image_to_analyze.save(img_byte_arr, format='JPEG')
                    img_byte_arr = img_byte_arr.getvalue()
                    
                    # Perform analysis
                    if question:
                        result = st.session_state.vision_analyzer.analyze_plan_image(
                            image_bytes=img_byte_arr,
                            question=question,
                            use_cache=True
                        )
                    else:
                        result = st.session_state.vision_analyzer.analyze_plan_image(
                            image_bytes=img_byte_arr,
                            use_cache=True
                        )
                    
                    # Display results
                    st.markdown("---")
                    st.markdown("## 📋 Analysis Results")
                    
                    st.success("✅ Analysis complete!")
                    
                    # Main analysis
                    st.markdown("### 🔍 AI Vision Analysis")
                    st.markdown(result['analysis'])
                    
                    # OCR text if available
                    if result.get('ocr_text'):
                        with st.expander("📝 Extracted Text (OCR)"):
                            st.text(result['ocr_text'])
                    
                    # Metadata
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Estimated Tokens", result['estimated_tokens'])
                    with col2:
                        st.metric("Analysis Time", datetime.fromisoformat(result['timestamp']).strftime("%H:%M:%S"))
                    with col3:
                        cached = "Yes" if result['image_hash'] in st.session_state.vision_analyzer.analysis_cache else "No"
                        st.metric("From Cache", cached)
                    
                    # Save to history
                    if 'analysis_history' not in st.session_state:
                        st.session_state.analysis_history = []
                    
                    st.session_state.analysis_history.insert(0, {
                        'timestamp': result['timestamp'],
                        'question': question if question else "General Analysis",
                        'analysis': result['analysis'],
                        'image_source': image_source,
                        'tokens': result['estimated_tokens']
                    })
                    
                    # Download button
                    st.markdown("---")
                    report = f"""# Plan Analysis Report
Generated: {result['timestamp']}

## Question
{question if question else 'General Analysis'}

## Analysis
{result['analysis']}

## Extracted Text
{result.get('ocr_text', 'N/A')}

## Metadata
- Tokens Used: {result['estimated_tokens']}
- Image Hash: {result['image_hash']}
"""
                    st.download_button(
                        "📥 Download Report",
                        report,
                        file_name=f"plan_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
                    
                except Exception as e:
                    st.error(f"Error during analysis: {e}")
                    import traceback
                    st.code(traceback.format_exc())

with tab2:
    st.markdown("## 📚 Analysis History")
    
    if 'analysis_history' in st.session_state and st.session_state.analysis_history:
        for i, item in enumerate(st.session_state.analysis_history):
            with st.expander(f"🕐 {item['timestamp']} - {item['question'][:50]}..."):
                st.markdown(f"**Question:** {item['question']}")
                st.markdown(f"**Source:** {item['image_source']}")
                st.markdown(f"**Tokens:** {item['tokens']}")
                st.markdown("**Analysis:**")
                st.markdown(item['analysis'])
    else:
        st.info("No analysis history yet. Upload a plan and analyze it to build your history!")

with tab3:
    st.markdown("## ⚙️ Vision Analysis Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🖼️ Image Processing")
        
        max_width = st.slider("Max Image Width", 512, 2048, 1024, 128)
        max_height = st.slider("Max Image Height", 512, 2048, 1024, 128)
        image_quality = st.slider("JPEG Quality", 50, 100, 85, 5)
        
        st.info(f"Larger images = better quality but more tokens. Current settings will use approximately {85 * ((max_width + 511) // 512) * ((max_height + 511) // 512)} tokens per image.")
    
    with col2:
        st.markdown("### 🤖 AI Model Settings")
        
        use_ocr = st.checkbox("Enable OCR text extraction", value=True)
        use_cache = st.checkbox("Use analysis cache", value=True)
        
        st.markdown("**Model Provider:**")
        st.info("Using model configured in main settings")
        
        if st.button("🗑️ Clear Cache", use_container_width=True):
            st.session_state.vision_analyzer.analysis_cache = {}
            st.session_state.vision_analyzer._save_cache_index()
            st.success("Cache cleared!")
            st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 💰 Cost Estimates")
    
    st.markdown("""
    **Vision Model Costs (per image):**
    - **Gemini 1.5 Flash**: ~$0.0001 - $0.0005 (Cheapest!)
    - **GPT-4o-mini**: ~$0.001 - $0.005
    - **Claude 3 Haiku**: ~$0.0025 - $0.0125
    
    💡 **Pro Tip**: Enable caching to avoid reanalyzing the same images!
    """)
