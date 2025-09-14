import streamlit as st
import pandas as pd
from datetime import datetime, date
from database.db_manager import DatabaseManager
from services.nlp_service import NLPService
from utils.file_handler import FileHandler
import json

# Page configuration
st.set_page_config(
    page_title="Tender Management - ACTMS",
    page_icon="📋",
    layout="wide"
)

# Initialize services
@st.cache_resource
def init_services():
    return DatabaseManager(), NLPService(), FileHandler()

def main():
    db, nlp_service, file_handler = init_services()
    
    st.title("📋 Tender Management")
    st.markdown("Upload, view, and manage tender documents with automated information extraction.")
    
    # Tabs for different functionalities
    tab1, tab2, tab3 = st.tabs(["📤 Upload New Tender", "📋 View Tenders", "📊 Tender Analytics"])
    
    with tab1:
        upload_tender_section(db, nlp_service, file_handler)
    
    with tab2:
        view_tenders_section(db, file_handler)
    
    with tab3:
        tender_analytics_section(db)

def upload_tender_section(db, nlp_service, file_handler):
    """Section for uploading new tenders"""
    st.header("📤 Upload New Tender")
    
    with st.form("tender_upload_form"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Basic tender information
            title = st.text_input("Tender Title *", help="Enter a descriptive title for the tender")
            description = st.text_area("Description *", height=100, help="Provide detailed description of the tender requirements")
            department = st.selectbox(
                "Department *",
                ["Select Department", "Infrastructure", "IT & Technology", "Healthcare", "Education", 
                 "Transportation", "Defense", "Energy", "Environment", "Finance", "Other"],
                help="Select the department issuing the tender"
            )
            
            col1_1, col1_2 = st.columns(2)
            with col1_1:
                estimated_value = st.number_input("Estimated Value ($)", min_value=0.0, step=1000.0, help="Estimated budget for the tender")
            with col1_2:
                deadline = st.date_input("Submission Deadline *", min_value=date.today(), help="Last date for bid submission")
        
        with col2:
            # File upload section
            st.subheader("📁 Document Upload")
            uploaded_file = file_handler.get_upload_widget(
                "Upload Tender Document (Optional)",
                help_text="Upload supporting documents (PDF, DOC, DOCX, TXT)",
                key="tender_document"
            )
        
        # Submit button
        submitted = st.form_submit_button("🚀 Submit Tender", width="stretch")
        
        if submitted:
            # Debug information
            st.write(f"Debug - Department value: '{department}'")
            
            # Validation
            errors = []
            if not title.strip():
                errors.append("Tender title is required")
            if not description.strip():
                errors.append("Description is required")
            if department == "Select Department" or department is None or department == "":
                errors.append("Please select a department")
            if not deadline:
                errors.append("Deadline is required")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                try:
                    # Process uploaded file if provided
                    file_path = None
                    extracted_info = None
                    
                    if uploaded_file:
                        with st.spinner("💾 Saving and processing document..."):
                            # Save file
                            file_path, save_errors = file_handler.save_file(uploaded_file, "tender")
                            
                            if save_errors:
                                for error in save_errors:
                                    st.error(f"❌ File Error: {error}")
                                return
                            
                            # Extract information from document
                            if file_path:
                                content, read_error = file_handler.read_file_content(file_path)
                                if content and not read_error:
                                    with st.spinner("🔍 Extracting information from document..."):
                                        extracted_info_dict = nlp_service.extract_tender_info(content)
                                        extracted_info = json.dumps(extracted_info_dict)
                                        
                                        # Show extraction results
                                        st.success("✅ Document processed successfully!")
                                        if extracted_info_dict:
                                            with st.expander("📄 Extracted Information Preview"):
                                                if extracted_info_dict.get('monetary_values'):
                                                    st.write("💰 **Monetary Values Found:**", extracted_info_dict['monetary_values'])
                                                if extracted_info_dict.get('dates'):
                                                    st.write("📅 **Dates Found:**", extracted_info_dict['dates'])
                                                if extracted_info_dict.get('requirements'):
                                                    st.write("📋 **Requirements Found:**", len(extracted_info_dict['requirements']), "items")
                                elif read_error:
                                    st.warning(f"⚠️ Could not extract text from document: {read_error}")
                    
                    # Save to database
                    with st.spinner("💾 Saving tender to database..."):
                        tender_id = db.insert_tender(
                            title=title,
                            description=description,
                            department=department,
                            estimated_value=estimated_value,
                            deadline=deadline.strftime('%Y-%m-%d'),
                            file_path=file_path,
                            extracted_info=extracted_info
                        )
                    
                    st.success(f"✅ Tender created successfully! Tender ID: {tender_id}")
                    
                    # Show summary
                    with st.expander("📋 Tender Summary"):
                        st.write(f"**Title:** {title}")
                        st.write(f"**Department:** {department}")
                        st.write(f"**Estimated Value:** ${estimated_value:,.2f}")
                        st.write(f"**Deadline:** {deadline.strftime('%B %d, %Y')}")
                        if file_path:
                            st.write(f"**Document:** {uploaded_file.name}")
                    
                    # Clear form by rerunning
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error creating tender: {str(e)}")

def view_tenders_section(db, file_handler):
    """Section for viewing existing tenders"""
    st.header("📋 View Tenders")
    
    # Filters
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "active", "closed", "cancelled"])
    
    with col2:
        search_term = st.text_input("🔍 Search Tenders", placeholder="Search by title or description...")
    
    with col3:
        refresh_button = st.button("🔄 Refresh", width="stretch")
    
    try:
        # Get tenders from database
        if status_filter == "All":
            tenders_df = db.get_tenders()
        else:
            tenders_df = db.get_tenders(status=status_filter)
        
        if len(tenders_df) == 0:
            st.info("📭 No tenders found. Create your first tender using the 'Upload New Tender' tab.")
            return
        
        # Apply search filter
        if search_term:
            mask = (
                tenders_df['title'].str.contains(search_term, case=False, na=False) |
                tenders_df['description'].str.contains(search_term, case=False, na=False)
            )
            tenders_df = tenders_df[mask]
        
        if len(tenders_df) == 0:
            st.warning(f"🔍 No tenders found matching '{search_term}'")
            return
        
        st.write(f"📊 **Found {len(tenders_df)} tender(s)**")
        
        # Display tenders
        for idx, tender in tenders_df.iterrows():
            with st.expander(f"📋 {tender['title']} (ID: {tender['id']})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Description:** {tender['description']}")
                    st.write(f"**Department:** {tender['department']}")
                    st.write(f"**Status:** {tender['status'].title()}")
                    
                    col1_1, col1_2 = st.columns(2)
                    with col1_1:
                        st.write(f"**Estimated Value:** ${tender['estimated_value']:,.2f}")
                    with col1_2:
                        deadline_date = pd.to_datetime(tender['deadline']).date()
                        days_left = (deadline_date - date.today()).days
                        if days_left > 0:
                            st.write(f"**Deadline:** {deadline_date} ({days_left} days left)")
                        else:
                            st.write(f"**Deadline:** {deadline_date} (⚠️ Expired)")
                    
                    st.write(f"**Created:** {pd.to_datetime(tender['created_at']).strftime('%B %d, %Y at %I:%M %p')}")
                
                with col2:
                    # Actions
                    st.write("**Actions:**")
                    
                    # View bids
                    bids_df = db.get_bids(tender_id=tender['id'])
                    bid_count = len(bids_df)
                    st.metric("Bids Received", bid_count)
                    
                    if st.button(f"👀 View Bids", key=f"view_bids_{tender['id']}"):
                        st.switch_page("pages/2_📝_Bid_Submission.py")
                    
                    # Download document if available
                    if tender['file_path'] and pd.notna(tender['file_path']):
                        file_info = file_handler.get_file_info(tender['file_path'])
                        if file_info:
                            file_handler.create_download_link(
                                tender['file_path'], 
                                f"tender_{tender['id']}_{file_info['filename']}"
                            )
                
                # Show extracted information if available
                if tender['extracted_info'] and pd.notna(tender['extracted_info']):
                    try:
                        extracted_data = json.loads(tender['extracted_info'])
                        if extracted_data:
                            with st.expander("🔍 Extracted Information"):
                                
                                if extracted_data.get('monetary_values'):
                                    st.write("💰 **Monetary Values:**")
                                    for value in extracted_data['monetary_values'][:5]:
                                        st.write(f"- {value}")
                                
                                if extracted_data.get('requirements'):
                                    st.write("📋 **Key Requirements:**")
                                    for req in extracted_data['requirements'][:3]:
                                        st.write(f"- {req}")
                                
                                if extracted_data.get('contact_info'):
                                    contact = extracted_data['contact_info']
                                    st.write("📞 **Contact Information:**")
                                    if contact.get('emails'):
                                        st.write(f"- Emails: {', '.join(contact['emails'][:2])}")
                                    if contact.get('phones'):
                                        st.write(f"- Phones: {', '.join(contact['phones'][:2])}")
                    except json.JSONDecodeError:
                        pass
    
    except Exception as e:
        st.error(f"❌ Error loading tenders: {str(e)}")

def tender_analytics_section(db):
    """Section for tender analytics"""
    st.header("📊 Tender Analytics")
    
    try:
        tenders_df = db.get_tenders()
        bids_df = db.get_bids()
        
        if len(tenders_df) == 0:
            st.info("📊 No data available for analytics. Create some tenders first.")
            return
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_tenders = len(tenders_df)
            st.metric("Total Tenders", total_tenders)
        
        with col2:
            active_tenders = len(tenders_df[tenders_df['status'] == 'active'])
            st.metric("Active Tenders", active_tenders)
        
        with col3:
            total_bids = len(bids_df)
            st.metric("Total Bids", total_bids)
        
        with col4:
            avg_bids_per_tender = total_bids / total_tenders if total_tenders > 0 else 0
            st.metric("Avg Bids/Tender", f"{avg_bids_per_tender:.1f}")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Tenders by department
            if len(tenders_df) > 0:
                dept_counts = tenders_df['department'].value_counts()
                st.subheader("📊 Tenders by Department")
                st.bar_chart(dept_counts)
        
        with col2:
            # Tender values distribution
            if len(tenders_df) > 0 and 'estimated_value' in tenders_df.columns:
                st.subheader("💰 Estimated Values Distribution")
                st.histogram_chart(tenders_df['estimated_value'].dropna())
        
        # Recent activity
        st.subheader("⏰ Recent Activity")
        if len(tenders_df) > 0:
            recent_tenders = tenders_df.head(5)[['title', 'department', 'estimated_value', 'created_at']]
            recent_tenders['estimated_value'] = recent_tenders['estimated_value'].apply(lambda x: f"${x:,.2f}")
            recent_tenders['created_at'] = pd.to_datetime(recent_tenders['created_at']).dt.strftime('%m/%d/%Y %I:%M %p')
            st.dataframe(recent_tenders, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error loading analytics: {str(e)}")

if __name__ == "__main__":
    main()
