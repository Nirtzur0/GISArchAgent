"""
GIS Architecture Agent - Main Web App

A friendly interface for working with Israeli planning regulations.
Uses clean architecture so the code doesn't make you cry.
"""

import streamlit as st
import logging
from datetime import datetime
from pathlib import Path

# Get our services
from src.infrastructure.factory import get_factory
from src.application.dtos import (
    PlanSearchQuery,
    RegulationQuery,
    BuildingRightsQuery
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page setup
st.set_page_config(
    page_title="GIS Architecture Agent",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (making it pretty)
st.markdown("""
<style>
    /* Color theme */
    :root {
        --primary-color: #2E86AB;
        --secondary-color: #A23B72;
        --accent-color: #F18F01;
        --background-color: #F8F9FA;
        --text-color: #2C3E50;
    }
    
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        color: var(--primary-color);
        text-align: center;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .sub-header {
        font-size: 1.2rem;
        color: var(--text-color);
        text-align: center;
        margin-bottom: 2rem;
        opacity: 0.8;
    }
    
    .stButton button {
        background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%);
        color: white;
        font-size: 1.1rem;
        font-weight: 600;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    
    .answer-box {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 5px solid var(--primary-color);
        color: #2C3E50;
    }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .answer-box {
            background: #1E1E1E;
            color: #E0E0E0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
    }
    
    /* Streamlit dark mode override */
    [data-testid="stAppViewContainer"][data-theme="dark"] .answer-box,
    .stApp[data-theme="dark"] .answer-box {
        background: #1E1E1E !important;
        color: #E0E0E0 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
    }
</style>
""", unsafe_allow_html=True)


# Keep track of stuff across page reloads
if 'factory' not in st.session_state:
    st.session_state.factory = None
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'current_answer' not in st.session_state:
    st.session_state.current_answer = None


@st.cache_resource
def initialize_factory():
    """Set up the factory once and cache it."""
    try:
        with st.spinner("\ud83d\ude80 Getting everything ready..."):
            factory = get_factory()
            logger.info("Factory is good to go!")
            return factory
    except Exception as e:
        st.error(f"Failed to initialize application: {e}")
        logger.error(f"Initialization error: {e}", exc_info=True)
        return None


def save_query_to_history(query: str, answer: str | None):
    """Save query and answer to history."""
    st.session_state.query_history.insert(0, {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'query': query,
        'answer': answer or ""
    })
    # Keep only last 20 queries
    st.session_state.query_history = st.session_state.query_history[:20]


def main():
    """Main application."""
    
    # Header
    st.markdown('<h1 class="main-header">🏗️ GIS Architecture Agent</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">AI-powered assistant for Israeli planning regulations and architecture</p>', 
        unsafe_allow_html=True
    )
    
    # Quick access buttons
    st.markdown("### 🚀 Quick Access")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📍 **View Maps**", use_container_width=True, help="Interactive planning maps"):
            st.switch_page("pages/1_📍_Map_Viewer.py")
    
    with col2:
        if st.button("📐 **Building Rights**", use_container_width=True, help="Calculate building rights"):
            st.switch_page("pages/2_📐_Plan_Analyzer.py")
    
    with col3:
        if st.button("💾 **Data Management**", use_container_width=True, help="Manage planning data sources"):
            st.switch_page("pages/3_💾_Data_Management.py")
    
    with col4:
        if st.button("💬 **Ask Questions**", use_container_width=True, help="Query planning regulations"):
            # Stay on main page, scroll to query section
            pass
    
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 📍 Navigation")
        
        page = st.radio(
            "Select page",
            ["🔍 Query Assistant", "📊 System Stats", "📜 Query History"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Quick info
        st.markdown("### ℹ️ Available Information")
        st.info("""
        - Israeli National Plans (TAMA)
        - Local Zoning Regulations
        - Building Requirements
        - Planning Procedures
        - Building Rights Calculations
        """)
        
        st.markdown("---")
        
        # System status
        st.markdown("### 🤖 System Status")
        if st.session_state.factory:
            st.success("✅ Services initialized")
        else:
            st.warning("⚠️ Initializing...")
    
    # Main content based on selected page
    if page == "🔍 Query Assistant":
        show_query_page()
    elif page == "📊 System Stats":
        show_stats_page()
    elif page == "📜 Query History":
        show_history_page()


def show_query_page():
    """Show the main regulation query interface."""
    
    # Initialize factory if needed
    if st.session_state.factory is None:
        st.session_state.factory = initialize_factory()
    
    if st.session_state.factory is None:
        st.error("Failed to initialize services. Please refresh the page.")
        return
    
    # Query input section
    st.markdown("## 💬 Ask About Planning Regulations")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        query = st.text_area(
            "Enter your question",
            height=120,
            placeholder="Example: What are the main provisions of TAMA 35 for residential buildings?",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        submit_button = st.button("🚀 Ask", use_container_width=True, type="primary")
        clear_button = st.button("🗑️ Clear", use_container_width=True)
    
    if clear_button:
        st.session_state.current_answer = None
        st.rerun()
    
    # Example queries
    with st.expander("💡 Example Questions"):
        example_queries = [
            "What are the main provisions of TAMA 35?",
            "What are the parking requirements for residential buildings?",
            "What are the height restrictions in Tel Aviv?",
            "What are the building coverage requirements for residential zones?",
            "How do I apply for a building permit?"
        ]
        
        cols = st.columns(2)
        for idx, ex in enumerate(example_queries):
            with cols[idx % 2]:
                if st.button(ex, key=f"example_{idx}", use_container_width=True):
                    query = ex
                    submit_button = True
    
    # Process query
    if submit_button and query:
        with st.spinner("🤔 Analyzing regulations..."):
            try:
                # Get regulation service
                regulation_service = st.session_state.factory.get_regulation_query_service()
                
                # Create query DTO
                reg_query = RegulationQuery(
                    query_text=query,
                    max_results=5
                )
                
                # Execute query
                result = regulation_service.query(reg_query)
                
                # Save to history
                save_query_to_history(query, result.answer)
                st.session_state.current_answer = result
                
            except Exception as e:
                st.error(f"Error processing query: {e}")
                logger.error(f"Query error: {e}", exc_info=True)
    
    # Display answer
    if st.session_state.current_answer:
        result = st.session_state.current_answer
        
        st.markdown("## 📋 Answer")
        if result.answer:
            st.markdown(f'<div class="answer-box">{result.answer}</div>', unsafe_allow_html=True)
        else:
            st.info("No synthesized answer available. See sources below.")
        
        # Show sources
        if result.regulations:
            with st.expander(f"📚 Sources ({len(result.regulations)} regulations)"):
                for idx, reg in enumerate(result.regulations, 1):
                    st.markdown(f"**{idx}. {reg.title}**")
                    st.markdown(f"*Type:* {reg.type.value} | *Jurisdiction:* {reg.jurisdiction}")
                    
                    if reg.summary:
                        st.markdown(reg.summary[:300] + "...")
                    else:
                        st.markdown(reg.content[:200] + "...")
                    
                    st.markdown("---")
        
        # Query metadata
        with st.expander("ℹ️ Query Information"):
            st.json({
                "timestamp": result.timestamp.isoformat() if hasattr(result, 'timestamp') else "N/A",
                "regulations_found": len(result.regulations),
                "query": query if 'query' in locals() else "N/A"
            })


def show_stats_page():
    """Show system statistics."""
    st.markdown("## 📊 System Statistics")
    
    if st.session_state.factory is None:
        st.session_state.factory = initialize_factory()
    
    if not st.session_state.factory:
        st.error("Services not initialized")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📦 Regulation Repository")
        try:
            reg_repo = st.session_state.factory.get_regulation_repository()
            stats = reg_repo.get_statistics()
            
            st.metric("Total Regulations", stats.get('total_regulations', 0))
            st.info(f"**Collection:** {stats.get('collection_name', 'N/A')}")
            st.info(f"**Directory:** {stats.get('persist_directory', 'N/A')}")
        except Exception as e:
            st.error(f"Failed to get regulation stats: {e}")
    
    with col2:
        st.markdown("### 💾 Cache Service")
        try:
            cache_service = st.session_state.factory.get_cache_service()
            cache_stats = cache_service.get_stats()
            
            st.metric("Cache Entries", cache_stats.get('valid_entries', 0))
            st.metric("Cache Size", f"{cache_stats.get('total_size_mb', 0)} MB")
            
            if st.button("🗑️ Clear Expired Cache"):
                deleted = cache_service.clear_expired()
                st.success(f"Cleared {deleted} expired entries")
                st.rerun()
        except Exception as e:
            st.error(f"Failed to get cache stats: {e}")
    
    st.markdown("---")
    
    # Query history stats
    st.markdown("### 📜 Query Statistics")
    if st.session_state.query_history:
        st.metric("Total Queries", len(st.session_state.query_history))
        
        # Recent queries
        st.markdown("**Recent Queries:**")
        for q in st.session_state.query_history[:5]:
            st.markdown(f"- {q['timestamp']}: {q['query'][:50]}...")
    else:
        st.info("No queries yet")


def show_history_page():
    """Show query history."""
    st.markdown("## 📜 Query History")
    
    if not st.session_state.query_history:
        st.info("No query history yet. Ask some questions to see them here!")
        return
    
    # Clear history button
    if st.button("🗑️ Clear All History"):
        st.session_state.query_history = []
        st.rerun()
    
    st.markdown("---")
    
    # Display history
    for idx, item in enumerate(st.session_state.query_history):
        with st.expander(f"{item['timestamp']} - {item['query'][:60]}..."):
            st.markdown(f"**Query:** {item['query']}")
            st.markdown(f"**Answer:** {item['answer'][:500]}...")
            
            if st.button("🔄 Rerun Query", key=f"rerun_{idx}"):
                st.session_state.current_answer = None
                # Would trigger a new query with same question
                st.info("Click 'Ask' button with this query to rerun")


if __name__ == "__main__":
    main()
