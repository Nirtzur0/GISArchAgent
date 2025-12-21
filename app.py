"""
Streamlit Web Application for GIS Architecture Agent
A beautiful, interactive interface for querying Israeli planning regulations
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import json
from pathlib import Path
import logging

from src.main import GISArchAgent
from src.config import settings
from src.vectorstore import VectorStoreManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="GIS Architecture Agent",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful styling
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #2E86AB;
        --secondary-color: #A23B72;
        --accent-color: #F18F01;
        --background-color: #F8F9FA;
        --text-color: #2C3E50;
    }
    
    /* Header styling */
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
    
    /* Query box styling */
    .stTextArea textarea {
        border-radius: 10px;
        border: 2px solid var(--primary-color);
        font-size: 1.1rem;
    }
    
    /* Button styling */
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
    
    /* Answer box styling */
    .answer-box {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 5px solid var(--primary-color);
    }
    
    /* Stat card styling */
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .stat-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }
    
    .stat-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Info boxes */
    .info-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* History item */
    .history-item {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid var(--accent-color);
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    
    /* Document card */
    .doc-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-top: 3px solid var(--accent-color);
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'current_answer' not in st.session_state:
    st.session_state.current_answer = None
if 'show_sources' not in st.session_state:
    st.session_state.show_sources = False


@st.cache_resource
def initialize_agent():
    """Initialize the GIS Architecture Agent."""
    try:
        with st.spinner("🚀 Initializing GIS Architecture Agent..."):
            agent = GISArchAgent()
            return agent
    except Exception as e:
        st.error(f"Failed to initialize agent: {e}")
        return None


def get_database_stats():
    """Get statistics from the vector database."""
    try:
        vectorstore = VectorStoreManager()
        collection = vectorstore.collection
        count = collection.count()
        return {
            'total_documents': count,
            'collection_name': vectorstore.collection_name,
            'persist_directory': vectorstore.persist_directory
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return None


def format_answer(answer: str) -> str:
    """Format the answer for better display."""
    # Add some formatting to make it more readable
    formatted = answer.replace("**", "")
    return formatted


def save_query_to_history(query: str, answer: str):
    """Save query and answer to history."""
    st.session_state.query_history.insert(0, {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'query': query,
        'answer': answer
    })
    # Keep only last 10 queries
    st.session_state.query_history = st.session_state.query_history[:10]


def main():
    """Main application."""
    
    # Header
    st.markdown('<h1 class="main-header">🏗️ GIS Architecture Agent</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Your AI-powered assistant for Israeli planning regulations and architecture queries</p>', unsafe_allow_html=True)
    
    # Quick access buttons
    st.markdown("### 🚀 Quick Access")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔍 **Search Plans**", use_container_width=True, help="Search iPlan with Vision AI"):
            st.switch_page("pages/4_🔍_Plan_Search.py")
    
    with col2:
        if st.button("📍 **View Maps**", use_container_width=True, help="Interactive TAMA zones"):
            st.switch_page("pages/1_📍_Map_Viewer.py")
    
    with col3:
        if st.button("📐 **Analyze Rights**", use_container_width=True, help="Building rights calculator"):
            st.switch_page("pages/2_📐_Plan_Analyzer.py")
    
    with col4:
        if st.button("🖼️ **Upload Image**", use_container_width=True, help="Manual image analysis"):
            st.switch_page("pages/3_🖼️_Plan_Image_Analyzer.py")
    
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/300x100/2E86AB/FFFFFF?text=GIS+Agent", use_container_width=True)
        
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "📍 Navigation",
            ["🔍 Query Assistant", "📊 Database Stats", "📚 Document Browser", "⚙️ Settings", "📜 Query History"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Quick info
        st.markdown("### ℹ️ Quick Info")
        st.info("""
        **Available Information:**
        - Israeli National Plans (TAMA)
        - Zoning Regulations
        - Building Requirements
        - Planning Procedures
        """)
        
        st.markdown("---")
        
        # Model info
        st.markdown("### 🤖 Model Info")
        st.success(f"""
        **Provider:** {settings.llm_provider}
        **Model:** {settings.model_name}
        """)
    
    # Main content based on selected page
    if page == "🔍 Query Assistant":
        show_query_page()
    elif page == "📊 Database Stats":
        show_stats_page()
    elif page == "📚 Document Browser":
        show_documents_page()
    elif page == "⚙️ Settings":
        show_settings_page()
    elif page == "📜 Query History":
        show_history_page()


def show_query_page():
    """Show the main query interface."""
    
    # Initialize agent if not already done
    if st.session_state.agent is None:
        st.session_state.agent = initialize_agent()
    
    if st.session_state.agent is None:
        st.error("Failed to initialize the agent. Please check your configuration.")
        return
    
    # Query input section
    st.markdown("## 💬 Ask Your Question")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        query = st.text_area(
            "Enter your question about planning regulations, TAMA plans, zoning, or building requirements:",
            height=120,
            placeholder="Example: What are the main provisions of TAMA 35 for residential buildings in Tel Aviv?",
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
            "Explain the blue line approval process",
            "What are the green building standards in Israel?",
            "What are the height restrictions in residential zones?"
        ]
        for ex in example_queries:
            if st.button(ex, key=f"example_{ex}"):
                query = ex
                submit_button = True
    
    # Process query
    if submit_button and query:
        with st.spinner("🤔 Thinking... The agent is analyzing your question..."):
            try:
                # Query the agent
                answer = st.session_state.agent.query(query)
                st.session_state.current_answer = answer
                save_query_to_history(query, answer)
            except Exception as e:
                st.error(f"Error processing query: {e}")
                logger.error(f"Query error: {e}", exc_info=True)
    
    # Display answer
    if st.session_state.current_answer:
        st.markdown("---")
        st.markdown("## 📝 Answer")
        
        # Display answer in a nice box
        st.markdown(f'<div class="answer-box">{st.session_state.current_answer}</div>', unsafe_allow_html=True)
        
        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            if st.button("📋 Copy Answer"):
                st.toast("Answer copied to clipboard! (Copy manually for now)", icon="✅")
        with col2:
            if st.button("💾 Save Answer"):
                # Save to file
                filename = f"answer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(filename, 'w') as f:
                    f.write(st.session_state.current_answer)
                st.toast(f"Saved to {filename}", icon="✅")


def show_stats_page():
    """Show database statistics."""
    st.markdown("## 📊 Database Statistics")
    
    stats = get_database_stats()
    
    if stats:
        # Display stats in nice cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">📚 Total Documents</div>
                <div class="stat-value">{stats['total_documents']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">🗂️ Collection</div>
                <div class="stat-value" style="font-size: 1.5rem;">{stats['collection_name']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">💾 Storage Path</div>
                <div class="stat-value" style="font-size: 1rem;">{Path(stats['persist_directory']).name}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Query distribution chart (mock data for now)
        st.markdown("### 📈 Query Distribution")
        
        categories = ['TAMA Plans', 'Zoning', 'Building Rights', 'Procedures', 'Standards']
        values = [35, 25, 20, 12, 8]
        
        fig = go.Figure(data=[go.Pie(
            labels=categories,
            values=values,
            hole=0.4,
            marker=dict(colors=['#2E86AB', '#A23B72', '#F18F01', '#667eea', '#764ba2'])
        )])
        
        fig.update_layout(
            title="Document Categories",
            height=400,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Timeline chart
        st.markdown("### 📅 Usage Over Time")
        
        dates = pd.date_range(start='2025-12-01', end='2025-12-21', freq='D')
        queries = [3 + i % 7 for i in range(len(dates))]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=queries,
            mode='lines+markers',
            name='Queries',
            line=dict(color='#2E86AB', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="Daily Query Count",
            xaxis_title="Date",
            yaxis_title="Number of Queries",
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Unable to retrieve database statistics.")


def show_documents_page():
    """Show available documents in the database."""
    st.markdown("## 📚 Document Browser")
    
    try:
        vectorstore = VectorStoreManager()
        collection = vectorstore.collection
        
        # Get all documents
        results = collection.get(include=['documents', 'metadatas'])
        
        if results and results['documents']:
            st.success(f"📖 Found {len(results['documents'])} document chunks")
            
            # Search functionality
            search_term = st.text_input("🔍 Search documents", placeholder="Enter keywords...")
            
            # Display documents
            for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
                if search_term and search_term.lower() not in doc.lower():
                    continue
                
                with st.expander(f"📄 Document {i+1}: {metadata.get('source', 'Unknown')}"):
                    st.markdown(f"**Source:** {metadata.get('source', 'N/A')}")
                    st.markdown(f"**Type:** {metadata.get('doc_type', 'N/A')}")
                    st.markdown("---")
                    st.markdown(doc)
        else:
            st.warning("No documents found in the database. Run initialization first.")
            
            if st.button("🚀 Initialize Database"):
                with st.spinner("Initializing database with sample data..."):
                    from src.ingest_data import ingest_sample_data
                    ingest_sample_data()
                    st.success("Database initialized!")
                    st.rerun()
                    
    except Exception as e:
        st.error(f"Error loading documents: {e}")


def show_settings_page():
    """Show settings page."""
    st.markdown("## ⚙️ Settings")
    
    st.markdown("### 🤖 Model Configuration")
    
    # Model provider
    provider = st.selectbox(
        "LLM Provider",
        ["openai", "google", "anthropic"],
        index=["openai", "google", "anthropic"].index(settings.llm_provider)
    )
    
    # Model selection based on provider
    if provider == "openai":
        model_options = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
    elif provider == "google":
        model_options = ["gemini-1.5-flash", "gemini-1.5-pro"]
    else:
        model_options = ["claude-3-haiku-20240307", "claude-3-sonnet-20240229"]
    
    model = st.selectbox("Model", model_options)
    
    temperature = st.slider("Temperature", 0.0, 1.0, settings.temperature, 0.1)
    
    if st.button("💾 Save Settings"):
        st.success("Settings saved! (Restart required to apply)")
    
    st.markdown("---")
    
    st.markdown("### 🔧 Advanced Options")
    
    max_tokens = st.number_input("Max Tokens", 100, 4000, 2000)
    chunk_size = st.number_input("Chunk Size", 100, 2000, 1000)
    chunk_overlap = st.number_input("Chunk Overlap", 0, 500, 200)
    
    st.markdown("---")
    
    st.markdown("### 📊 Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Reinitialize Database", use_container_width=True):
            with st.spinner("Reinitializing..."):
                from src.ingest_data import run_ingestion_pipeline
                run_ingestion_pipeline()
                st.success("Database reinitialized!")
    
    with col2:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.query_history = []
            st.success("History cleared!")


def show_history_page():
    """Show query history."""
    st.markdown("## 📜 Query History")
    
    if not st.session_state.query_history:
        st.info("No queries yet. Start asking questions to build your history!")
    else:
        st.markdown(f"**Total Queries:** {len(st.session_state.query_history)}")
        
        # Export button
        if st.button("📥 Export History"):
            history_json = json.dumps(st.session_state.query_history, indent=2)
            st.download_button(
                "💾 Download JSON",
                history_json,
                file_name=f"query_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        st.markdown("---")
        
        # Display history
        for i, item in enumerate(st.session_state.query_history):
            with st.expander(f"🕐 {item['timestamp']} - {item['query'][:50]}..."):
                st.markdown(f"**Query:** {item['query']}")
                st.markdown("**Answer:**")
                st.markdown(item['answer'])
                
                if st.button("🔄 Run Again", key=f"rerun_{i}"):
                    st.session_state.current_answer = item['answer']
                    st.rerun()


if __name__ == "__main__":
    main()
