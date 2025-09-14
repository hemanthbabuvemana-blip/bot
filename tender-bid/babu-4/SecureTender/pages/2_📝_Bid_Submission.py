import streamlit as st
import pandas as pd
from datetime import datetime, date
from database.db_manager import DatabaseManager
from services.ml_service import MLService
from services.nlp_service import NLPService
import re

# Page configuration
st.set_page_config(
    page_title="Bid Submission - ACTMS",
    page_icon="📝",
    layout="wide"
)

# Initialize services
@st.cache_resource
def init_services():
    return DatabaseManager(), MLService(), NLPService()

def main():
    db, ml_service, nlp_service = init_services()
    
    st.title("📝 Bid Submission")
    st.markdown("Submit bids for active tenders with automated validation and AI analysis.")
    
    # Tabs for different functionalities
    tab1, tab2, tab3 = st.tabs(["📝 Submit New Bid", "📋 View Bids", "🔍 Bid Analysis"])
    
    with tab1:
        submit_bid_section(db, ml_service, nlp_service)
    
    with tab2:
        view_bids_section(db)
    
    with tab3:
        bid_analysis_section(db, ml_service)

def submit_bid_section(db, ml_service, nlp_service):
    """Section for submitting new bids"""
    st.header("📝 Submit New Bid")
    
    # Get active tenders
    try:
        tenders_df = db.get_tenders(status='active')
        
        if len(tenders_df) == 0:
            st.warning("⚠️ No active tenders available for bidding.")
            return
        
        # Create tender selection options
        tender_options = {}
        for _, tender in tenders_df.iterrows():
            deadline_date = pd.to_datetime(tender['deadline']).date()
            days_left = (deadline_date - date.today()).days
            
            if days_left >= 0:  # Only show non-expired tenders
                option_text = f"{tender['title']} (ID: {tender['id']}) - Est: ${tender['estimated_value']:,.0f} - Deadline: {deadline_date}"
                tender_options[option_text] = tender['id']
        
        if not tender_options:
            st.warning("⚠️ All active tenders have expired. No tenders available for bidding.")
            return
        
        with st.form("bid_submission_form"):
            # Tender selection
            selected_tender_option = st.selectbox(
                "Select Tender *",
                ["Select a tender..."] + list(tender_options.keys()),
                help="Choose the tender you want to bid on"
            )
            
            if selected_tender_option != "Select a tender...":
                selected_tender_id = tender_options[selected_tender_option]
                selected_tender = tenders_df[tenders_df['id'] == selected_tender_id].iloc[0]
                
                # Show tender details
                with st.expander("📋 Tender Details"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Title:** {selected_tender['title']}")
                        st.write(f"**Department:** {selected_tender['department']}")
                        st.write(f"**Description:** {selected_tender['description']}")
                    with col2:
                        st.write(f"**Estimated Value:** ${selected_tender['estimated_value']:,.2f}")
                        deadline_date = pd.to_datetime(selected_tender['deadline']).date()
                        days_left = (deadline_date - date.today()).days
                        st.write(f"**Deadline:** {deadline_date} ({days_left} days left)")
                        
                        # Show existing bids count
                        existing_bids = db.get_bids(tender_id=selected_tender_id)
                        st.metric("Existing Bids", len(existing_bids))
            
            st.markdown("---")
            
            # Bidder information
            st.subheader("🏢 Company Information")
            col1, col2 = st.columns(2)
            
            with col1:
                company_name = st.text_input("Company Name *", help="Enter your company or organization name")
                contact_email = st.text_input("Contact Email *", help="Primary contact email address")
            
            with col2:
                contact_person = st.text_input("Contact Person", help="Name of primary contact person (optional)")
                phone_number = st.text_input("Phone Number", help="Contact phone number (optional)")
            
            # Bid details
            st.subheader("💰 Bid Information")
            col1, col2 = st.columns([1, 2])
            
            with col1:
                bid_amount = st.number_input(
                    "Bid Amount ($) *",
                    min_value=0.01,
                    step=1000.0,
                    help="Enter your bid amount in USD"
                )
                
                # Show comparison with estimated value if tender is selected
                if selected_tender_option != "Select a tender...":
                    estimated_value = selected_tender['estimated_value']
                    if bid_amount > 0:
                        percentage_diff = ((bid_amount - estimated_value) / estimated_value) * 100
                        if percentage_diff > 20:
                            st.warning(f"⚠️ Bid is {percentage_diff:.1f}% above estimated value")
                        elif percentage_diff < -20:
                            st.warning(f"⚠️ Bid is {abs(percentage_diff):.1f}% below estimated value")
                        else:
                            st.success(f"✅ Bid is {percentage_diff:.1f}% of estimated value")
            
            with col2:
                # Proposal text
                proposal = st.text_area(
                    "Detailed Proposal *",
                    height=200,
                    help="Provide a detailed proposal explaining your approach, timeline, team, and qualifications",
                    placeholder="Describe your approach, experience, timeline, team qualifications, and why you're the best choice for this tender..."
                )
                
                # Real-time proposal analysis
                if proposal.strip():
                    proposal_analysis = nlp_service.analyze_bid_proposal(proposal)
                    
                    col2_1, col2_2 = st.columns(2)
                    with col2_1:
                        st.metric("Proposal Quality Score", f"{proposal_analysis['quality_score']}/100")
                    with col2_2:
                        st.metric("Word Count", proposal_analysis['word_count'])
                    
                    if proposal_analysis['issues']:
                        st.warning("⚠️ **Proposal Issues:**")
                        for issue in proposal_analysis['issues'][:3]:
                            st.write(f"- {issue}")
                    
                    if proposal_analysis['strengths']:
                        st.success("✅ **Proposal Strengths:**")
                        for strength in proposal_analysis['strengths'][:3]:
                            st.write(f"- {strength}")
            
            # Additional information
            with st.expander("📄 Additional Information (Optional)"):
                col1, col2 = st.columns(2)
                with col1:
                    years_experience = st.number_input("Years of Experience", min_value=0, max_value=100, step=1)
                    team_size = st.number_input("Team Size", min_value=1, max_value=1000, step=1)
                
                with col2:
                    certifications = st.text_area("Relevant Certifications", help="List any relevant certifications or qualifications")
                    previous_work = st.text_area("Previous Similar Work", help="Describe previous similar projects or experience")
            
            # Submit button
            submitted = st.form_submit_button("🚀 Submit Bid", width="stretch")
            
            if submitted:
                # Validation
                errors = []
                
                if selected_tender_option == "Select a tender...":
                    errors.append("Please select a tender")
                if not company_name.strip():
                    errors.append("Company name is required")
                if not contact_email.strip():
                    errors.append("Contact email is required")
                elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', contact_email):
                    errors.append("Invalid email format")
                if bid_amount <= 0:
                    errors.append("Bid amount must be greater than 0")
                if not proposal.strip():
                    errors.append("Proposal is required")
                elif len(proposal.strip()) < 50:
                    errors.append("Proposal must be at least 50 characters long")
                
                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                else:
                    try:
                        with st.spinner("💾 Submitting bid..."):
                            # Insert bid into database
                            bid_id = db.insert_bid(
                                tender_id=selected_tender_id,
                                company_name=company_name,
                                contact_email=contact_email,
                                bid_amount=bid_amount,
                                proposal=proposal
                            )
                        
                        # Prepare bid data for AI analysis
                        bid_data = {
                            'tender_id': selected_tender_id,
                            'company_name': company_name,
                            'contact_email': contact_email,
                            'bid_amount': bid_amount,
                            'proposal': proposal,
                            'submitted_at': datetime.now().isoformat()
                        }
                        
                        # Run AI analysis
                        with st.spinner("🤖 Running AI analysis..."):
                            anomaly_score, is_suspicious = ml_service.analyze_single_bid(bid_data)
                            
                            # Update bid with analysis results
                            db.update_bid_anomaly_score(bid_id, anomaly_score, is_suspicious)
                            
                            # Create alert if suspicious
                            if is_suspicious:
                                db.create_ai_alert(
                                    alert_type="Suspicious Bid",
                                    severity="medium",
                                    message=f"Suspicious bid detected for tender {selected_tender_id} by {company_name}",
                                    related_entity_type="bid",
                                    related_entity_id=bid_id
                                )
                        
                        st.success(f"✅ Bid submitted successfully! Bid ID: {bid_id}")
                        
                        # Show AI analysis results
                        col1, col2 = st.columns(2)
                        with col1:
                            if is_suspicious:
                                st.warning(f"⚠️ **AI Analysis:** This bid has been flagged for review (Anomaly Score: {anomaly_score:.3f})")
                            else:
                                st.success(f"✅ **AI Analysis:** No suspicious patterns detected (Anomaly Score: {anomaly_score:.3f})")
                        
                        with col2:
                            if is_suspicious and ml_service.is_trained:
                                explanations = ml_service.get_anomaly_explanation(bid_data, anomaly_score)
                                if explanations:
                                    st.write("**Possible reasons:**")
                                    for explanation in explanations[:3]:
                                        st.write(f"- {explanation}")
                        
                        # Show submission summary
                        with st.expander("📋 Submission Summary"):
                            st.write(f"**Tender:** {selected_tender['title']}")
                            st.write(f"**Company:** {company_name}")
                            st.write(f"**Bid Amount:** ${bid_amount:,.2f}")
                            st.write(f"**Contact:** {contact_email}")
                            st.write(f"**Submitted:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
                        
                        # Clear form
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error submitting bid: {str(e)}")
                        
    except Exception as e:
        st.error(f"❌ Error loading tenders: {str(e)}")

def view_bids_section(db):
    """Section for viewing submitted bids"""
    st.header("📋 View Bids")
    
    # Filters
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        tenders_df = db.get_tenders()
        if len(tenders_df) > 0:
            tender_options = ["All Tenders"] + [f"{row['title']} (ID: {row['id']})" for _, row in tenders_df.iterrows()]
            selected_tender_filter = st.selectbox("Filter by Tender", tender_options)
        else:
            selected_tender_filter = "All Tenders"
    
    with col2:
        company_search = st.text_input("🔍 Search by Company", placeholder="Enter company name...")
    
    with col3:
        st.button("🔄 Refresh", width="stretch")
    
    try:
        # Get bids based on filter
        if selected_tender_filter == "All Tenders":
            bids_df = db.get_bids()
        else:
            tender_id = int(selected_tender_filter.split("ID: ")[1].split(")")[0])
            bids_df = db.get_bids(tender_id=tender_id)
        
        if len(bids_df) == 0:
            st.info("📭 No bids found. Submit your first bid using the 'Submit New Bid' tab.")
            return
        
        # Apply company search filter
        if company_search:
            mask = bids_df['company_name'].str.contains(company_search, case=False, na=False)
            bids_df = bids_df[mask]
        
        if len(bids_df) == 0:
            st.warning(f"🔍 No bids found matching '{company_search}'")
            return
        
        st.write(f"📊 **Found {len(bids_df)} bid(s)**")
        
        # Sort by submission date (most recent first)
        bids_df = bids_df.sort_values('submitted_at', ascending=False)
        
        # Display bids
        for idx, bid in bids_df.iterrows():
            with st.expander(f"📝 {bid['company_name']} - ${bid['bid_amount']:,.2f} (ID: {bid['id']})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Tender:** {bid['tender_title']}")
                    st.write(f"**Company:** {bid['company_name']}")
                    st.write(f"**Contact:** {bid['contact_email']}")
                    st.write(f"**Bid Amount:** ${bid['bid_amount']:,.2f}")
                    st.write(f"**Status:** {bid['status'].title()}")
                    st.write(f"**Submitted:** {pd.to_datetime(bid['submitted_at']).strftime('%B %d, %Y at %I:%M %p')}")
                    
                    # Show proposal
                    if bid['proposal']:
                        with st.expander("📄 View Proposal"):
                            st.write(bid['proposal'])
                
                with col2:
                    # AI Analysis results
                    st.write("**🤖 AI Analysis:**")
                    
                    if pd.notna(bid['anomaly_score']):
                        anomaly_score = float(bid['anomaly_score'])
                        is_suspicious = bool(bid['is_suspicious'])
                        
                        if is_suspicious:
                            st.error(f"⚠️ **Flagged as Suspicious**")
                            st.write(f"Anomaly Score: {anomaly_score:.3f}")
                        else:
                            st.success(f"✅ **No Issues Detected**")
                            st.write(f"Anomaly Score: {anomaly_score:.3f}")
                        
                        # Create progress bar for anomaly score (normalized)
                        normalized_score = max(0, min(1, (anomaly_score + 1) / 2))  # Convert from [-1,1] to [0,1]
                        st.progress(normalized_score)
                    else:
                        st.info("Not analyzed yet")
        
    except Exception as e:
        st.error(f"❌ Error loading bids: {str(e)}")

def bid_analysis_section(db, ml_service):
    """Section for bid analysis and insights"""
    st.header("🔍 Bid Analysis")
    
    try:
        bids_df = db.get_bids()
        
        if len(bids_df) == 0:
            st.info("📊 No bid data available for analysis.")
            return
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_bids = len(bids_df)
            st.metric("Total Bids", total_bids)
        
        with col2:
            suspicious_bids = len(bids_df[bids_df['is_suspicious'] == True]) if 'is_suspicious' in bids_df.columns else 0
            st.metric("Suspicious Bids", suspicious_bids)
        
        with col3:
            avg_bid_amount = bids_df['bid_amount'].mean() if len(bids_df) > 0 else 0
            st.metric("Avg Bid Amount", f"${avg_bid_amount:,.0f}")
        
        with col4:
            unique_companies = bids_df['company_name'].nunique()
            st.metric("Unique Companies", unique_companies)
        
        # Charts and analysis
        col1, col2 = st.columns(2)
        
        with col1:
            # Bid amounts distribution
            st.subheader("💰 Bid Amounts Distribution")
            if len(bids_df) > 0:
                st.bar_chart(bids_df['bid_amount'])
        
        with col2:
            # Suspicious vs Normal bids
            st.subheader("🔍 AI Analysis Results")
            if 'is_suspicious' in bids_df.columns:
                analysis_counts = bids_df['is_suspicious'].value_counts()
                analysis_data = {
                    'Normal': analysis_counts.get(False, 0),
                    'Suspicious': analysis_counts.get(True, 0)
                }
                st.bar_chart(analysis_data)
            else:
                st.info("No AI analysis data available")
        
        # Suspicious bids details
        if 'is_suspicious' in bids_df.columns:
            suspicious_df = bids_df[bids_df['is_suspicious'] == True]
            
            if len(suspicious_df) > 0:
                st.subheader("⚠️ Suspicious Bids Details")
                
                display_cols = ['company_name', 'tender_title', 'bid_amount', 'anomaly_score', 'submitted_at']
                display_df = suspicious_df[display_cols].copy()
                display_df['bid_amount'] = display_df['bid_amount'].apply(lambda x: f"${x:,.2f}")
                display_df['anomaly_score'] = display_df['anomaly_score'].apply(lambda x: f"{x:.3f}")
                display_df['submitted_at'] = pd.to_datetime(display_df['submitted_at']).dt.strftime('%m/%d/%Y %I:%M %p')
                
                st.dataframe(display_df, use_container_width=True)
        
        # Company analysis
        st.subheader("🏢 Company Bidding Patterns")
        company_stats = bids_df.groupby('company_name').agg({
            'id': 'count',
            'bid_amount': ['mean', 'sum'],
            'is_suspicious': lambda x: x.sum() if x.dtype == bool else 0
        }).round(2)
        
        company_stats.columns = ['Total Bids', 'Avg Bid Amount', 'Total Bid Value', 'Suspicious Bids']
        company_stats = company_stats.sort_values('Total Bids', ascending=False)
        
        st.dataframe(company_stats.head(10), use_container_width=True)
        
        # Model information
        if ml_service.is_trained:
            st.subheader("🤖 AI Model Information")
            model_info = ml_service.get_model_info()
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Model Type:** {model_info['model_type']}")
                st.write(f"**Training Status:** {'Trained' if model_info['is_trained'] else 'Not Trained'}")
            
            with col2:
                st.write(f"**Contamination Rate:** {model_info['contamination_rate']}")
                st.write(f"**Estimators:** {model_info['n_estimators']}")
            
            with st.expander("📊 Features Used"):
                for feature in model_info['features_used']:
                    st.write(f"- {feature}")
        
    except Exception as e:
        st.error(f"❌ Error loading bid analysis: {str(e)}")

if __name__ == "__main__":
    main()
