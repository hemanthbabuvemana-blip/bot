import streamlit as st
import sqlite3
from database.db_manager import DatabaseManager
import os

# Page configuration
st.set_page_config(
    page_title="ACTMS - Anti-Corruption Tender Management System",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
@st.cache_resource
def init_database():
    return DatabaseManager()

def main():
    # Initialize database
    db = init_database()
    
    # Main header
    st.title("🏛️ Anti-Corruption Tender Management System (ACTMS)")
    st.markdown("---")
    
    # Welcome section
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        ### Welcome to ACTMS
        
        A comprehensive system for transparent and corruption-free tender management with AI-powered detection capabilities.
        
        **Key Features:**
        - 📋 **Tender Management**: Upload and manage tender documents
        - 📝 **Bid Submission**: Submit bids with automated validation
        - 🔍 **AI Analysis**: Detect suspicious patterns and anomalies
        - 💬 **Chatbot**: Get instant help and guidance
        - 📊 **Dashboard**: View analytics and reports
        """)
    
    # Navigation guidance
    st.markdown("---")
    st.markdown("### 🧭 Navigation")
    st.markdown("Use the sidebar to navigate between different sections of the system.")
    
    # System status
    st.markdown("---")
    st.markdown("### 📊 System Status")
    
    # Get database statistics
    try:
        tender_count = db.get_tender_count()
        bid_count = db.get_bid_count()
        alert_count = db.get_alert_count()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Active Tenders", tender_count)
        
        with col2:
            st.metric("Total Bids", bid_count)
        
        with col3:
            st.metric("AI Alerts", alert_count)
        
        with col4:
            st.metric("System Status", "🟢 Online")
            
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
    
    # Quick actions
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Manage Tenders", key="manage_tenders_btn", type="primary"):
            st.switch_page("pages/1_📋_Tender_Management.py")
    
    with col2:
        if st.button("📝 Submit Bid", key="submit_bid_btn", type="secondary"):
            st.switch_page("pages/2_📝_Bid_Submission.py")
    
    with col3:
        if st.button("🔍 View Analysis", key="view_analysis_btn", type="secondary"):
            st.switch_page("pages/3_🔍_AI_Analysis.py")

if __name__ == "__main__":
    main()
