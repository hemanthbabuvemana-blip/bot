import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database.db_manager import DatabaseManager
from services.ml_service import MLService
import numpy as np

# Page configuration
st.set_page_config(
    page_title="AI Analysis - ACTMS",
    page_icon="🔍",
    layout="wide"
)

# Initialize services
@st.cache_resource
def init_services():
    return DatabaseManager(), MLService()

def main():
    db, ml_service = init_services()
    
    st.title("🔍 AI Analysis & Anomaly Detection")
    st.markdown("Advanced AI-powered analysis for detecting suspicious patterns and anomalies in tender and bidding activities.")
    
    # Tabs for different analysis views
    tab1, tab2, tab3, tab4 = st.tabs(["🚨 Real-time Alerts", "📊 Anomaly Dashboard", "🤖 Model Training", "📈 Pattern Analysis"])
    
    with tab1:
        alerts_section(db)
    
    with tab2:
        anomaly_dashboard_section(db, ml_service)
    
    with tab3:
        model_training_section(db, ml_service)
    
    with tab4:
        pattern_analysis_section(db, ml_service)

def alerts_section(db):
    """Real-time alerts section"""
    st.header("🚨 Real-time Alerts")
    
    # Alert filters
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        severity_filter = st.selectbox("Filter by Severity", ["All", "high", "medium", "low"])
    
    with col2:
        alert_type_filter = st.selectbox("Filter by Type", ["All", "Suspicious Bid", "Unusual Pattern", "System Alert"])
    
    with col3:
        if st.button("🔄 Refresh Alerts", width="stretch"):
            st.rerun()
    
    try:
        # Get alerts from database
        alerts_df = db.get_ai_alerts()
        
        if len(alerts_df) == 0:
            st.info("✅ No active alerts. System is running normally.")
            return
        
        # Apply filters
        filtered_alerts = alerts_df.copy()
        
        if severity_filter != "All":
            filtered_alerts = filtered_alerts[filtered_alerts['severity'] == severity_filter]
        
        if alert_type_filter != "All":
            filtered_alerts = filtered_alerts[filtered_alerts['alert_type'] == alert_type_filter]
        
        if len(filtered_alerts) == 0:
            st.warning(f"No alerts found matching the selected criteria.")
            return
        
        st.write(f"🚨 **{len(filtered_alerts)} active alert(s) found**")
        
        # Display alerts
        for idx, alert in filtered_alerts.iterrows():
            # Determine alert color based on severity
            if alert['severity'] == 'high':
                alert_color = "🔴"
                container_type = st.error
            elif alert['severity'] == 'medium':
                alert_color = "🟡"
                container_type = st.warning
            else:
                alert_color = "🟢"
                container_type = st.info
            
            with st.expander(f"{alert_color} {alert['alert_type']} - {alert['severity'].upper()} (ID: {alert['id']})"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Message:** {alert['message']}")
                    st.write(f"**Type:** {alert['alert_type']}")
                    st.write(f"**Severity:** {alert['severity'].upper()}")
                    st.write(f"**Created:** {pd.to_datetime(alert['created_at']).strftime('%B %d, %Y at %I:%M %p')}")
                    
                    if alert['related_entity_type'] and pd.notna(alert['related_entity_type']):
                        st.write(f"**Related:** {alert['related_entity_type'].title()} ID {alert['related_entity_id']}")
                
                with col2:
                    # Actions
                    if st.button(f"🔍 Investigate", key=f"investigate_{alert['id']}"):
                        investigate_alert(db, alert, ml_service)
                    
                    if st.button(f"✅ Mark Resolved", key=f"resolve_{alert['id']}"):
                        # Update alert status
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE ai_alerts SET status = 'resolved' WHERE id = ?", (alert['id'],))
                        conn.commit()
                        conn.close()
                        st.success("Alert marked as resolved!")
                        st.rerun()
        
        # Alert statistics
        st.markdown("---")
        st.subheader("📊 Alert Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            high_severity = len(alerts_df[alerts_df['severity'] == 'high'])
            st.metric("High Severity", high_severity, delta=None, delta_color="inverse")
        
        with col2:
            medium_severity = len(alerts_df[alerts_df['severity'] == 'medium'])
            st.metric("Medium Severity", medium_severity)
        
        with col3:
            low_severity = len(alerts_df[alerts_df['severity'] == 'low'])
            st.metric("Low Severity", low_severity)
        
        with col4:
            total_alerts = len(alerts_df)
            st.metric("Total Alerts", total_alerts)
        
    except Exception as e:
        st.error(f"❌ Error loading alerts: {str(e)}")

def investigate_alert(db, alert, ml_service):
    """Investigate a specific alert"""
    st.subheader(f"🔍 Investigation: {alert['alert_type']}")
    
    if alert['related_entity_type'] == 'bid' and pd.notna(alert['related_entity_id']):
        # Get bid details
        bids_df = db.get_bids()
        related_bid = bids_df[bids_df['id'] == alert['related_entity_id']]
        
        if not related_bid.empty:
            bid = related_bid.iloc[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Bid Information:**")
                st.write(f"- Company: {bid['company_name']}")
                st.write(f"- Tender: {bid['tender_title']}")
                st.write(f"- Amount: ${bid['bid_amount']:,.2f}")
                st.write(f"- Submitted: {pd.to_datetime(bid['submitted_at']).strftime('%B %d, %Y at %I:%M %p')}")
                
                if pd.notna(bid['anomaly_score']):
                    st.write(f"- Anomaly Score: {bid['anomaly_score']:.3f}")
            
            with col2:
                st.write("**Analysis Details:**")
                if ml_service.is_trained:
                    bid_data = {
                        'company_name': bid['company_name'],
                        'bid_amount': bid['bid_amount'],
                        'proposal': bid['proposal'],
                        'submitted_at': bid['submitted_at']
                    }
                    
                    explanations = ml_service.get_anomaly_explanation(bid_data, bid['anomaly_score'])
                    if explanations:
                        st.write("**Possible Issues:**")
                        for explanation in explanations:
                            st.write(f"- {explanation}")
                    else:
                        st.write("No specific issues identified.")
            
            # Show proposal if available
            if bid['proposal']:
                with st.expander("📄 View Full Proposal"):
                    st.write(bid['proposal'])

def anomaly_dashboard_section(db, ml_service):
    """Anomaly detection dashboard"""
    st.header("📊 Anomaly Detection Dashboard")
    
    try:
        bids_df = db.get_bids()
        
        if len(bids_df) == 0:
            st.info("📊 No bid data available for anomaly analysis.")
            return
        
        # Check if ML model is trained
        if not ml_service.is_trained:
            st.warning("⚠️ ML model is not trained yet. Please train the model first in the 'Model Training' tab.")
        
        # Anomaly analysis summary
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate metrics
        total_bids = len(bids_df)
        suspicious_bids = len(bids_df[bids_df['is_suspicious'] == True]) if 'is_suspicious' in bids_df.columns else 0
        normal_bids = total_bids - suspicious_bids
        suspicion_rate = (suspicious_bids / total_bids * 100) if total_bids > 0 else 0
        
        with col1:
            st.metric("Total Bids Analyzed", total_bids)
        
        with col2:
            st.metric("Suspicious Bids", suspicious_bids, delta=f"{suspicion_rate:.1f}%")
        
        with col3:
            st.metric("Normal Bids", normal_bids)
        
        with col4:
            avg_anomaly_score = bids_df['anomaly_score'].mean() if 'anomaly_score' in bids_df.columns and not bids_df['anomaly_score'].isna().all() else 0
            st.metric("Avg Anomaly Score", f"{avg_anomaly_score:.3f}")
        
        # Visualizations
        if 'anomaly_score' in bids_df.columns and not bids_df['anomaly_score'].isna().all():
            # Anomaly score distribution
            st.subheader("📈 Anomaly Score Distribution")
            
            fig = px.histogram(
                bids_df.dropna(subset=['anomaly_score']),
                x='anomaly_score',
                nbins=20,
                title="Distribution of Anomaly Scores",
                color_discrete_sequence=['#1f77b4']
            )
            fig.update_layout(
                xaxis_title="Anomaly Score",
                yaxis_title="Number of Bids",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Anomaly scores over time
            st.subheader("⏰ Anomaly Scores Over Time")
            
            bids_with_time = bids_df.dropna(subset=['anomaly_score']).copy()
            bids_with_time['submitted_at'] = pd.to_datetime(bids_with_time['submitted_at'])
            bids_with_time = bids_with_time.sort_values('submitted_at')
            
            fig = px.scatter(
                bids_with_time,
                x='submitted_at',
                y='anomaly_score',
                color='is_suspicious',
                title="Anomaly Scores Timeline",
                hover_data=['company_name', 'bid_amount'],
                color_discrete_map={True: 'red', False: 'blue'}
            )
            fig.update_layout(
                xaxis_title="Submission Date",
                yaxis_title="Anomaly Score"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Suspicious bids analysis
        if suspicious_bids > 0:
            st.subheader("⚠️ Suspicious Bids Analysis")
            
            suspicious_df = bids_df[bids_df['is_suspicious'] == True]
            
            # Group by company
            company_suspicious = suspicious_df.groupby('company_name').size().reset_index(name='suspicious_count')
            company_suspicious = company_suspicious.sort_values('suspicious_count', ascending=False)
            
            if len(company_suspicious) > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Companies with Most Suspicious Bids:**")
                    st.dataframe(company_suspicious.head(10), use_container_width=True)
                
                with col2:
                    # Pie chart of suspicious vs normal
                    fig = px.pie(
                        values=[normal_bids, suspicious_bids],
                        names=['Normal', 'Suspicious'],
                        title="Bid Classification",
                        color_discrete_sequence=['#2ecc71', '#e74c3c']
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        # Bid amount analysis
        st.subheader("💰 Bid Amount Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Box plot of bid amounts by suspicious status
            if 'is_suspicious' in bids_df.columns:
                fig = px.box(
                    bids_df,
                    x='is_suspicious',
                    y='bid_amount',
                    title="Bid Amount Distribution by Classification",
                    color='is_suspicious',
                    color_discrete_map={True: 'red', False: 'blue'}
                )
                fig.update_layout(
                    xaxis_title="Is Suspicious",
                    yaxis_title="Bid Amount ($)"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Scatter plot of bid amount vs anomaly score
            if 'anomaly_score' in bids_df.columns:
                fig = px.scatter(
                    bids_df.dropna(subset=['anomaly_score']),
                    x='bid_amount',
                    y='anomaly_score',
                    color='is_suspicious',
                    title="Bid Amount vs Anomaly Score",
                    hover_data=['company_name'],
                    color_discrete_map={True: 'red', False: 'blue'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error loading anomaly dashboard: {str(e)}")

def model_training_section(db, ml_service):
    """ML model training section"""
    st.header("🤖 Machine Learning Model Training")
    
    try:
        # Model status
        model_info = ml_service.get_model_info()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Model Status")
            st.write(f"**Status:** {'✅ Trained' if model_info['is_trained'] else '❌ Not Trained'}")
            st.write(f"**Model Type:** {model_info['model_type']}")
            st.write(f"**Contamination Rate:** {model_info['contamination_rate']}")
            st.write(f"**Number of Estimators:** {model_info['n_estimators']}")
        
        with col2:
            st.subheader("📋 Features Used")
            for feature in model_info['features_used']:
                st.write(f"- {feature}")
        
        # Training data information
        bids_df = db.get_bids()
        st.subheader("📈 Training Data")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Bids Available", len(bids_df))
        
        with col2:
            min_required = 10
            st.metric("Minimum Required", min_required)
        
        with col3:
            can_train = len(bids_df) >= min_required
            st.metric("Training Ready", "✅ Yes" if can_train else "❌ No")
        
        # Training controls
        st.subheader("🎯 Model Training Controls")
        
        if len(bids_df) < 10:
            st.warning(f"⚠️ Need at least 10 bids to train the model. Currently have {len(bids_df)} bids.")
            st.info("💡 Submit more bids through the 'Bid Submission' page to enable model training.")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🚀 Train/Retrain Model", width="stretch"):
                    with st.spinner("🤖 Training machine learning model..."):
                        success = ml_service.train_model(bids_df)
                        
                        if success:
                            st.success("✅ Model trained successfully!")
                            
                            # Run analysis on all existing bids
                            with st.spinner("🔍 Analyzing all existing bids..."):
                                anomaly_scores, is_anomaly = ml_service.detect_anomalies(bids_df)
                                
                                if len(anomaly_scores) > 0:
                                    # Update all bids with new scores
                                    for idx, (_, bid) in enumerate(bids_df.iterrows()):
                                        db.update_bid_anomaly_score(
                                            bid['id'], 
                                            float(anomaly_scores[idx]), 
                                            bool(is_anomaly[idx])
                                        )
                                        
                                        # Create alerts for newly detected suspicious bids
                                        if is_anomaly[idx]:
                                            db.create_ai_alert(
                                                alert_type="Suspicious Bid",
                                                severity="medium",
                                                message=f"Suspicious bid detected during retraining for bid ID {bid['id']}",
                                                related_entity_type="bid",
                                                related_entity_id=bid['id']
                                            )
                                    
                                    st.success(f"✅ Analyzed {len(bids_df)} bids. Found {sum(is_anomaly)} suspicious patterns.")
                            
                            st.rerun()
                        else:
                            st.error("❌ Failed to train model. Please check the data and try again.")
            
            with col2:
                if ml_service.is_trained:
                    if st.button("🔍 Test Model Performance", width="stretch"):
                        test_model_performance(ml_service, bids_df)
        
        # Model performance metrics
        if ml_service.is_trained and len(bids_df) > 0:
            st.subheader("📊 Model Performance Metrics")
            
            try:
                # Calculate current performance
                anomaly_scores, is_anomaly = ml_service.detect_anomalies(bids_df)
                
                if len(anomaly_scores) > 0:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        suspicious_count = sum(is_anomaly)
                        suspicious_percentage = (suspicious_count / len(bids_df)) * 100
                        st.metric("Suspicious Bids Detected", f"{suspicious_count}/{len(bids_df)}", f"{suspicious_percentage:.1f}%")
                    
                    with col2:
                        avg_score = np.mean(anomaly_scores)
                        st.metric("Average Anomaly Score", f"{avg_score:.3f}")
                    
                    with col3:
                        score_std = np.std(anomaly_scores)
                        st.metric("Score Standard Deviation", f"{score_std:.3f}")
                    
                    # Visualize score distribution
                    fig = px.histogram(
                        x=anomaly_scores,
                        nbins=20,
                        title="Current Model - Anomaly Score Distribution",
                        color_discrete_sequence=['#3498db']
                    )
                    fig.update_layout(
                        xaxis_title="Anomaly Score",
                        yaxis_title="Frequency"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.warning(f"⚠️ Could not calculate performance metrics: {str(e)}")
        
    except Exception as e:
        st.error(f"❌ Error in model training section: {str(e)}")

def test_model_performance(ml_service, bids_df):
    """Test and display model performance"""
    st.subheader("🧪 Model Performance Test")
    
    try:
        with st.spinner("Testing model performance..."):
            # Run predictions on all data
            anomaly_scores, is_anomaly = ml_service.detect_anomalies(bids_df)
            
            if len(anomaly_scores) > 0:
                # Performance metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    total_predictions = len(anomaly_scores)
                    st.metric("Total Predictions", total_predictions)
                
                with col2:
                    anomalies_detected = sum(is_anomaly)
                    detection_rate = (anomalies_detected / total_predictions) * 100
                    st.metric("Anomalies Detected", f"{anomalies_detected} ({detection_rate:.1f}%)")
                
                with col3:
                    score_range = f"{min(anomaly_scores):.3f} to {max(anomaly_scores):.3f}"
                    st.metric("Score Range", score_range)
                
                # Feature importance (simplified)
                st.subheader("📊 Feature Analysis")
                
                # Analyze which features contribute most to anomalies
                suspicious_bids = bids_df[np.array(is_anomaly)]
                normal_bids = bids_df[~np.array(is_anomaly)]
                
                if len(suspicious_bids) > 0 and len(normal_bids) > 0:
                    feature_analysis = {
                        'Feature': ['Avg Bid Amount', 'Avg Proposal Length', 'Submission Timing'],
                        'Suspicious Average': [
                            suspicious_bids['bid_amount'].mean(),
                            suspicious_bids['proposal'].str.len().mean() if 'proposal' in suspicious_bids.columns else 0,
                            0  # Placeholder for timing analysis
                        ],
                        'Normal Average': [
                            normal_bids['bid_amount'].mean(),
                            normal_bids['proposal'].str.len().mean() if 'proposal' in normal_bids.columns else 0,
                            0  # Placeholder for timing analysis
                        ]
                    }
                    
                    feature_df = pd.DataFrame(feature_analysis)
                    st.dataframe(feature_df, use_container_width=True)
                
                st.success("✅ Model performance test completed!")
            else:
                st.error("❌ Could not run performance test.")
                
    except Exception as e:
        st.error(f"❌ Error testing model performance: {str(e)}")

def pattern_analysis_section(db, ml_service):
    """Advanced pattern analysis section"""
    st.header("📈 Pattern Analysis")
    
    try:
        bids_df = db.get_bids()
        tenders_df = db.get_tenders()
        
        if len(bids_df) == 0:
            st.info("📊 No data available for pattern analysis.")
            return
        
        # Time-based patterns
        st.subheader("⏰ Temporal Patterns")
        
        # Convert submission times
        bids_df['submitted_at'] = pd.to_datetime(bids_df['submitted_at'])
        bids_df['hour'] = bids_df['submitted_at'].dt.hour
        bids_df['day_of_week'] = bids_df['submitted_at'].dt.day_name()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Submissions by hour
            hourly_submissions = bids_df['hour'].value_counts().sort_index()
            fig = px.bar(
                x=hourly_submissions.index,
                y=hourly_submissions.values,
                title="Bid Submissions by Hour of Day",
                labels={'x': 'Hour of Day', 'y': 'Number of Submissions'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Submissions by day of week
            daily_submissions = bids_df['day_of_week'].value_counts()
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            daily_submissions = daily_submissions.reindex(day_order, fill_value=0)
            
            fig = px.bar(
                x=daily_submissions.index,
                y=daily_submissions.values,
                title="Bid Submissions by Day of Week",
                labels={'x': 'Day of Week', 'y': 'Number of Submissions'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Company behavior patterns
        st.subheader("🏢 Company Behavior Patterns")
        
        # Company statistics
        company_stats = bids_df.groupby('company_name').agg({
            'id': 'count',
            'bid_amount': ['mean', 'std', 'min', 'max'],
            'submitted_at': ['min', 'max']
        }).round(2)
        
        company_stats.columns = ['Total Bids', 'Avg Amount', 'Amount StdDev', 'Min Amount', 'Max Amount', 'First Bid', 'Last Bid']
        company_stats = company_stats.sort_values('Total Bids', ascending=False)
        
        # Identify patterns
        st.subheader("🔍 Identified Patterns")
        
        patterns_found = []
        
        # Pattern 1: Companies with unusually consistent bid amounts
        for company in company_stats.index:
            if company_stats.loc[company, 'Total Bids'] >= 3:
                std_dev = company_stats.loc[company, 'Amount StdDev']
                avg_amount = company_stats.loc[company, 'Avg Amount']
                coefficient_variation = std_dev / avg_amount if avg_amount > 0 else 0
                
                if coefficient_variation < 0.05:  # Very low variation
                    patterns_found.append(f"🔍 **{company}**: Unusually consistent bid amounts (CV: {coefficient_variation:.3f})")
        
        # Pattern 2: Companies bidding outside business hours frequently
        if 'hour' in bids_df.columns:
            for company in bids_df['company_name'].unique():
                company_bids = bids_df[bids_df['company_name'] == company]
                if len(company_bids) >= 3:
                    after_hours = len(company_bids[(company_bids['hour'] < 8) | (company_bids['hour'] > 18)])
                    after_hours_rate = after_hours / len(company_bids)
                    
                    if after_hours_rate > 0.5:
                        patterns_found.append(f"⏰ **{company}**: {after_hours_rate:.1%} of bids submitted outside business hours")
        
        # Pattern 3: Rapid-fire submissions
        bids_df_sorted = bids_df.sort_values('submitted_at')
        for company in bids_df['company_name'].unique():
            company_bids = bids_df_sorted[bids_df_sorted['company_name'] == company]
            if len(company_bids) >= 2:
                time_diffs = company_bids['submitted_at'].diff().dt.total_seconds() / 60  # in minutes
                quick_submissions = (time_diffs < 10).sum()  # Less than 10 minutes apart
                
                if quick_submissions > 0:
                    patterns_found.append(f"⚡ **{company}**: {quick_submissions} rapid submissions (< 10 minutes apart)")
        
        if patterns_found:
            st.write("**Detected behavioral patterns:**")
            for pattern in patterns_found[:10]:  # Show top 10
                st.write(pattern)
        else:
            st.success("✅ No unusual behavioral patterns detected.")
        
        # Company details table
        st.subheader("📊 Company Statistics")
        st.dataframe(company_stats.head(15), use_container_width=True)
        
        # Bid amount analysis
        st.subheader("💰 Bid Amount Patterns")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribution of bid amounts
            fig = px.histogram(
                bids_df,
                x='bid_amount',
                nbins=20,
                title="Distribution of Bid Amounts",
                color_discrete_sequence=['#2ecc71']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Box plot by tender
            if len(tenders_df) > 0:
                # Merge with tender data to get tender titles
                merged_df = bids_df.merge(tenders_df[['id', 'title']], left_on='tender_id', right_on='id', suffixes=('_bid', '_tender'))
                
                fig = px.box(
                    merged_df,
                    x='title',
                    y='bid_amount',
                    title="Bid Amount Distribution by Tender"
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error in pattern analysis: {str(e)}")

if __name__ == "__main__":
    main()
