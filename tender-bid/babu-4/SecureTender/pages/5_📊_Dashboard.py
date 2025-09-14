import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, date, timedelta
from database.db_manager import DatabaseManager

# Page configuration
st.set_page_config(
    page_title="Dashboard - ACTMS",
    page_icon="📊",
    layout="wide"
)

# Initialize services
@st.cache_resource
def init_services():
    return DatabaseManager()

def main():
    db = init_services()
    
    st.title("📊 ACTMS Dashboard")
    st.markdown("Comprehensive analytics and insights for the Anti-Corruption Tender Management System.")
    
    # Tabs for different dashboard views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Overview", "💰 Financial Analysis", "🔍 Security Insights", "📋 Operational Metrics", "⚙️ System Admin"])
    
    with tab1:
        overview_dashboard(db)
    
    with tab2:
        financial_analysis_dashboard(db)
    
    with tab3:
        security_insights_dashboard(db)
    
    with tab4:
        operational_metrics_dashboard(db)
    
    with tab5:
        system_admin_dashboard(db)

def overview_dashboard(db):
    """Main overview dashboard"""
    st.header("📈 System Overview")
    
    try:
        # Load data
        tenders_df = db.get_tenders()
        bids_df = db.get_bids()
        alerts_df = db.get_ai_alerts()
        
        # Key Performance Indicators
        st.subheader("🎯 Key Performance Indicators")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_tenders = len(tenders_df)
            st.metric("Total Tenders", total_tenders)
        
        with col2:
            active_tenders = len(tenders_df[tenders_df['status'] == 'active']) if len(tenders_df) > 0 else 0
            st.metric("Active Tenders", active_tenders)
        
        with col3:
            total_bids = len(bids_df)
            avg_bids_per_tender = total_bids / total_tenders if total_tenders > 0 else 0
            st.metric("Total Bids", total_bids, f"Avg: {avg_bids_per_tender:.1f}")
        
        with col4:
            suspicious_bids = len(bids_df[bids_df['is_suspicious'] == True]) if len(bids_df) > 0 and 'is_suspicious' in bids_df.columns else 0
            suspicion_rate = (suspicious_bids / total_bids * 100) if total_bids > 0 else 0
            st.metric("Suspicious Bids", suspicious_bids, f"{suspicion_rate:.1f}%")
        
        with col5:
            active_alerts = len(alerts_df[alerts_df['status'] == 'active']) if len(alerts_df) > 0 else 0
            st.metric("Active Alerts", active_alerts, delta_color="inverse")
        
        # Charts section
        if len(tenders_df) > 0 or len(bids_df) > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                # Tender activity over time
                st.subheader("📅 Tender Activity Timeline")
                if len(tenders_df) > 0:
                    tenders_df['created_at'] = pd.to_datetime(tenders_df['created_at'])
                    daily_tenders = tenders_df.groupby(tenders_df['created_at'].dt.date).size().reset_index()
                    daily_tenders.columns = ['Date', 'Count']
                    
                    fig = px.line(
                        daily_tenders,
                        x='Date',
                        y='Count',
                        title="Daily Tender Submissions",
                        markers=True
                    )
                    fig.update_layout(
                        xaxis_title="Date",
                        yaxis_title="Number of Tenders"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No tender data available")
            
            with col2:
                # Bid activity over time
                st.subheader("📝 Bid Activity Timeline")
                if len(bids_df) > 0:
                    bids_df['submitted_at'] = pd.to_datetime(bids_df['submitted_at'])
                    daily_bids = bids_df.groupby(bids_df['submitted_at'].dt.date).size().reset_index()
                    daily_bids.columns = ['Date', 'Count']
                    
                    fig = px.line(
                        daily_bids,
                        x='Date',
                        y='Count',
                        title="Daily Bid Submissions",
                        markers=True,
                        color_discrete_sequence=['#2ecc71']
                    )
                    fig.update_layout(
                        xaxis_title="Date",
                        yaxis_title="Number of Bids"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No bid data available")
        
        # Department analysis
        if len(tenders_df) > 0:
            st.subheader("🏢 Department Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Tenders by department
                dept_counts = tenders_df['department'].value_counts()
                fig = px.pie(
                    values=dept_counts.values,
                    names=dept_counts.index,
                    title="Tenders by Department"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Average estimated value by department
                if 'estimated_value' in tenders_df.columns:
                    dept_values = tenders_df.groupby('department')['estimated_value'].mean().sort_values(ascending=False)
                    fig = px.bar(
                        x=dept_values.index,
                        y=dept_values.values,
                        title="Average Estimated Value by Department",
                        labels={'x': 'Department', 'y': 'Average Value ($)'}
                    )
                    fig.update_xaxes(tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)
        
        # Recent activity
        st.subheader("⏰ Recent Activity")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Latest Tenders**")
            if len(tenders_df) > 0:
                recent_tenders = tenders_df.nlargest(5, 'created_at')[['title', 'department', 'status', 'created_at']]
                recent_tenders['created_at'] = pd.to_datetime(recent_tenders['created_at']).dt.strftime('%m/%d/%Y')
                st.dataframe(recent_tenders, use_container_width=True, hide_index=True)
            else:
                st.info("No tenders yet")
        
        with col2:
            st.write("**Latest Bids**")
            if len(bids_df) > 0:
                recent_bids = bids_df.nlargest(5, 'submitted_at')[['company_name', 'bid_amount', 'is_suspicious', 'submitted_at']]
                recent_bids['submitted_at'] = pd.to_datetime(recent_bids['submitted_at']).dt.strftime('%m/%d/%Y')
                recent_bids['bid_amount'] = recent_bids['bid_amount'].apply(lambda x: f"${x:,.0f}")
                st.dataframe(recent_bids, use_container_width=True, hide_index=True)
            else:
                st.info("No bids yet")
        
    except Exception as e:
        st.error(f"❌ Error loading overview dashboard: {str(e)}")

def financial_analysis_dashboard(db):
    """Financial analysis dashboard"""
    st.header("💰 Financial Analysis")
    
    try:
        tenders_df = db.get_tenders()
        bids_df = db.get_bids()
        
        if len(tenders_df) == 0 and len(bids_df) == 0:
            st.info("📊 No financial data available for analysis.")
            return
        
        # Financial KPIs
        st.subheader("💼 Financial Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate financial metrics
        total_tender_value = tenders_df['estimated_value'].sum() if len(tenders_df) > 0 and 'estimated_value' in tenders_df.columns else 0
        total_bid_value = bids_df['bid_amount'].sum() if len(bids_df) > 0 else 0
        avg_tender_value = tenders_df['estimated_value'].mean() if len(tenders_df) > 0 and 'estimated_value' in tenders_df.columns else 0
        avg_bid_value = bids_df['bid_amount'].mean() if len(bids_df) > 0 else 0
        
        with col1:
            st.metric("Total Tender Value", f"${total_tender_value:,.0f}")
        
        with col2:
            st.metric("Total Bid Value", f"${total_bid_value:,.0f}")
        
        with col3:
            st.metric("Avg Tender Value", f"${avg_tender_value:,.0f}")
        
        with col4:
            st.metric("Avg Bid Value", f"${avg_bid_value:,.0f}")
        
        # Bid vs Tender Value Analysis
        if len(tenders_df) > 0 and len(bids_df) > 0:
            st.subheader("📊 Bid vs Tender Value Analysis")
            
            # Merge data for analysis
            merged_df = bids_df.merge(tenders_df[['id', 'estimated_value']], left_on='tender_id', right_on='id', suffixes=('_bid', '_tender'))
            
            if len(merged_df) > 0:
                # Calculate bid ratio (bid amount / estimated value)
                merged_df['bid_ratio'] = merged_df['bid_amount'] / merged_df['estimated_value']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Bid ratio distribution
                    fig = px.histogram(
                        merged_df,
                        x='bid_ratio',
                        nbins=20,
                        title="Bid to Estimated Value Ratio Distribution",
                        labels={'bid_ratio': 'Bid/Estimated Ratio', 'count': 'Number of Bids'}
                    )
                    fig.add_vline(x=1.0, line_dash="dash", line_color="red", annotation_text="Estimated Value")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Scatter plot of bid amount vs estimated value
                    color_map = {True: 'red', False: 'blue'} if 'is_suspicious' in merged_df.columns else None
                    
                    fig = px.scatter(
                        merged_df,
                        x='estimated_value',
                        y='bid_amount',
                        color='is_suspicious' if 'is_suspicious' in merged_df.columns else None,
                        title="Bid Amount vs Estimated Value",
                        labels={'estimated_value': 'Estimated Value ($)', 'bid_amount': 'Bid Amount ($)'},
                        color_discrete_map=color_map,
                        hover_data=['company_name'] if 'company_name' in merged_df.columns else None
                    )
                    # Add diagonal line for reference
                    max_val = max(merged_df['estimated_value'].max(), merged_df['bid_amount'].max())
                    fig.add_trace(go.Scatter(x=[0, max_val], y=[0, max_val], mode='lines', name='Perfect Match', line=dict(dash='dash', color='gray')))
                    st.plotly_chart(fig, use_container_width=True)
        
        # Value distribution by department
        if len(tenders_df) > 0 and 'estimated_value' in tenders_df.columns:
            st.subheader("🏢 Value Distribution by Department")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Box plot of tender values by department
                fig = px.box(
                    tenders_df,
                    x='department',
                    y='estimated_value',
                    title="Tender Value Distribution by Department"
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Total value by department
                dept_values = tenders_df.groupby('department')['estimated_value'].sum().sort_values(ascending=False)
                fig = px.bar(
                    x=dept_values.index,
                    y=dept_values.values,
                    title="Total Value by Department",
                    labels={'x': 'Department', 'y': 'Total Value ($)'}
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
        
        # Competitive analysis
        if len(bids_df) > 0:
            st.subheader("🏆 Competitive Analysis")
            
            # Company bidding statistics
            company_stats = bids_df.groupby('company_name').agg({
                'bid_amount': ['count', 'sum', 'mean', 'std'],
                'is_suspicious': lambda x: x.sum() if x.dtype == bool else 0
            }).round(2)
            
            company_stats.columns = ['Total Bids', 'Total Value', 'Avg Bid', 'Std Dev', 'Suspicious Count']
            company_stats = company_stats.sort_values('Total Value', ascending=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Top Companies by Total Bid Value**")
                top_companies = company_stats.head(10)
                top_companies['Total Value'] = top_companies['Total Value'].apply(lambda x: f"${x:,.0f}")
                top_companies['Avg Bid'] = top_companies['Avg Bid'].apply(lambda x: f"${x:,.0f}")
                st.dataframe(top_companies, use_container_width=True)
            
            with col2:
                # Company competition visualization
                top_10_companies = company_stats.head(10)
                fig = px.treemap(
                    values=top_10_companies['Total Value'].astype(float),
                    names=top_10_companies.index,
                    title="Market Share by Total Bid Value"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Financial trends
        if len(bids_df) > 0:
            st.subheader("📈 Financial Trends")
            
            # Monthly bid value trends
            bids_df['submitted_at'] = pd.to_datetime(bids_df['submitted_at'])
            monthly_values = bids_df.groupby(bids_df['submitted_at'].dt.to_period('M')).agg({
                'bid_amount': ['sum', 'mean', 'count']
            }).round(2)
            
            monthly_values.columns = ['Total Value', 'Avg Value', 'Bid Count']
            monthly_values.index = monthly_values.index.astype(str)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.line(
                    x=monthly_values.index,
                    y=monthly_values['Total Value'],
                    title="Monthly Total Bid Value",
                    markers=True
                )
                fig.update_layout(
                    xaxis_title="Month",
                    yaxis_title="Total Value ($)"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.line(
                    x=monthly_values.index,
                    y=monthly_values['Avg Value'],
                    title="Monthly Average Bid Value",
                    markers=True,
                    color_discrete_sequence=['#e74c3c']
                )
                fig.update_layout(
                    xaxis_title="Month",
                    yaxis_title="Average Value ($)"
                )
                st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error loading financial analysis: {str(e)}")

def security_insights_dashboard(db):
    """Security and fraud detection insights"""
    st.header("🔍 Security & Fraud Detection Insights")
    
    try:
        bids_df = db.get_bids()
        alerts_df = db.get_ai_alerts()
        
        if len(bids_df) == 0:
            st.info("🔍 No bid data available for security analysis.")
            return
        
        # Security KPIs
        st.subheader("🛡️ Security Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        total_bids = len(bids_df)
        suspicious_bids = len(bids_df[bids_df['is_suspicious'] == True]) if 'is_suspicious' in bids_df.columns else 0
        normal_bids = total_bids - suspicious_bids
        detection_rate = (suspicious_bids / total_bids * 100) if total_bids > 0 else 0
        
        with col1:
            st.metric("Total Analyzed", total_bids)
        
        with col2:
            st.metric("Suspicious Detected", suspicious_bids, f"{detection_rate:.1f}%")
        
        with col3:
            st.metric("Clean Bids", normal_bids)
        
        with col4:
            active_alerts = len(alerts_df[alerts_df['status'] == 'active']) if len(alerts_df) > 0 else 0
            st.metric("Active Alerts", active_alerts, delta_color="inverse")
        
        # Security visualizations
        if 'is_suspicious' in bids_df.columns and 'anomaly_score' in bids_df.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                # Anomaly score distribution
                st.subheader("📊 Anomaly Score Distribution")
                
                fig = px.histogram(
                    bids_df.dropna(subset=['anomaly_score']),
                    x='anomaly_score',
                    color='is_suspicious',
                    nbins=30,
                    title="Distribution of Anomaly Scores",
                    color_discrete_map={True: '#e74c3c', False: '#3498db'},
                    barmode='overlay'
                )
                fig.update_layout(
                    xaxis_title="Anomaly Score",
                    yaxis_title="Count"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Security status pie chart
                st.subheader("🔍 Detection Results")
                
                security_data = {
                    'Status': ['Clean', 'Suspicious'],
                    'Count': [normal_bids, suspicious_bids]
                }
                
                fig = px.pie(
                    values=security_data['Count'],
                    names=security_data['Status'],
                    title="Bid Security Classification",
                    color_discrete_sequence=['#2ecc71', '#e74c3c']
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Threat timeline
        if len(alerts_df) > 0:
            st.subheader("⏰ Security Alert Timeline")
            
            alerts_df['created_at'] = pd.to_datetime(alerts_df['created_at'])
            daily_alerts = alerts_df.groupby([alerts_df['created_at'].dt.date, 'severity']).size().reset_index()
            daily_alerts.columns = ['Date', 'Severity', 'Count']
            
            fig = px.bar(
                daily_alerts,
                x='Date',
                y='Count',
                color='Severity',
                title="Daily Security Alerts by Severity",
                color_discrete_map={'high': '#e74c3c', 'medium': '#f39c12', 'low': '#95a5a6'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Company risk analysis
        if 'is_suspicious' in bids_df.columns:
            st.subheader("🏢 Company Risk Analysis")
            
            company_risk = bids_df.groupby('company_name').agg({
                'id': 'count',
                'is_suspicious': 'sum',
                'anomaly_score': 'mean' if 'anomaly_score' in bids_df.columns else lambda x: 0
            }).round(3)
            
            company_risk.columns = ['Total Bids', 'Suspicious Bids', 'Avg Anomaly Score']
            company_risk['Risk Score'] = (company_risk['Suspicious Bids'] / company_risk['Total Bids'] * 100).round(1)
            company_risk = company_risk[company_risk['Total Bids'] >= 2]  # Only companies with 2+ bids
            
            # High-risk companies
            high_risk = company_risk[company_risk['Risk Score'] >= 50].sort_values('Risk Score', ascending=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if len(high_risk) > 0:
                    st.write("**⚠️ High-Risk Companies (≥50% suspicious rate)**")
                    st.dataframe(high_risk.head(10), use_container_width=True)
                else:
                    st.success("✅ No high-risk companies detected")
            
            with col2:
                # Risk score distribution
                if len(company_risk) > 0:
                    fig = px.histogram(
                        company_risk,
                        x='Risk Score',
                        nbins=20,
                        title="Company Risk Score Distribution",
                        labels={'Risk Score': 'Risk Score (%)', 'count': 'Number of Companies'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        # Pattern detection insights
        st.subheader("🔍 Detected Patterns")
        
        patterns_detected = []
        
        # Time-based patterns
        if len(bids_df) > 0:
            bids_df['submitted_at'] = pd.to_datetime(bids_df['submitted_at'])
            bids_df['hour'] = bids_df['submitted_at'].dt.hour
            
            # After-hours submissions
            after_hours = len(bids_df[(bids_df['hour'] < 8) | (bids_df['hour'] > 18)])
            after_hours_rate = (after_hours / len(bids_df)) * 100
            
            if after_hours_rate > 30:
                patterns_detected.append(f"🕐 High after-hours activity: {after_hours_rate:.1f}% of bids submitted outside business hours")
            
            # Weekend submissions
            weekend_bids = len(bids_df[bids_df['submitted_at'].dt.weekday >= 5])
            weekend_rate = (weekend_bids / len(bids_df)) * 100
            
            if weekend_rate > 20:
                patterns_detected.append(f"📅 High weekend activity: {weekend_rate:.1f}% of bids submitted on weekends")
        
        # Amount-based patterns
        if 'bid_amount' in bids_df.columns and len(bids_df) > 10:
            # Round number bias
            round_amounts = len(bids_df[bids_df['bid_amount'] % 1000 == 0])
            round_rate = (round_amounts / len(bids_df)) * 100
            
            if round_rate > 60:
                patterns_detected.append(f"💰 High round number bias: {round_rate:.1f}% of bids are round thousands")
        
        if patterns_detected:
            st.warning("⚠️ **Detected Suspicious Patterns:**")
            for pattern in patterns_detected:
                st.write(f"- {pattern}")
        else:
            st.success("✅ No suspicious patterns detected in current data")
        
        # Alert details
        if len(alerts_df) > 0:
            st.subheader("🚨 Recent Security Alerts")
            
            recent_alerts = alerts_df.nlargest(10, 'created_at')[['alert_type', 'severity', 'message', 'created_at']]
            recent_alerts['created_at'] = pd.to_datetime(recent_alerts['created_at']).dt.strftime('%m/%d/%Y %H:%M')
            st.dataframe(recent_alerts, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"❌ Error loading security insights: {str(e)}")

def operational_metrics_dashboard(db):
    """Operational metrics and system performance"""
    st.header("📋 Operational Metrics")
    
    try:
        tenders_df = db.get_tenders()
        bids_df = db.get_bids()
        
        # System performance metrics
        st.subheader("⚙️ System Performance")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate operational metrics
        total_tenders = len(tenders_df)
        active_tenders = len(tenders_df[tenders_df['status'] == 'active']) if len(tenders_df) > 0 else 0
        total_bids = len(bids_df)
        unique_companies = bids_df['company_name'].nunique() if len(bids_df) > 0 else 0
        
        with col1:
            st.metric("System Utilization", f"{(active_tenders/max(total_tenders,1)*100):.1f}%")
        
        with col2:
            participation_rate = unique_companies / max(total_tenders, 1)
            st.metric("Avg Companies/Tender", f"{participation_rate:.1f}")
        
        with col3:
            processing_efficiency = (total_bids / max(total_tenders, 1)) if total_tenders > 0 else 0
            st.metric("Bids per Tender", f"{processing_efficiency:.1f}")
        
        with col4:
            # Calculate average response time (days from tender creation to first bid)
            if len(tenders_df) > 0 and len(bids_df) > 0:
                merged = bids_df.merge(tenders_df[['id', 'created_at']], left_on='tender_id', right_on='id', suffixes=('_bid', '_tender'))
                merged['created_at_tender'] = pd.to_datetime(merged['created_at_tender'])
                merged['submitted_at'] = pd.to_datetime(merged['submitted_at'])
                merged['response_time'] = (merged['submitted_at'] - merged['created_at_tender']).dt.days
                avg_response_time = merged['response_time'].mean()
                st.metric("Avg Response Time", f"{avg_response_time:.1f} days")
            else:
                st.metric("Avg Response Time", "N/A")
        
        # Activity patterns
        if len(bids_df) > 0:
            st.subheader("📊 Activity Patterns")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Hourly activity heatmap
                bids_df['submitted_at'] = pd.to_datetime(bids_df['submitted_at'])
                bids_df['hour'] = bids_df['submitted_at'].dt.hour
                bids_df['day_of_week'] = bids_df['submitted_at'].dt.day_name()
                
                # Create hourly distribution
                hourly_activity = bids_df['hour'].value_counts().sort_index()
                
                fig = px.bar(
                    x=hourly_activity.index,
                    y=hourly_activity.values,
                    title="Bid Submissions by Hour",
                    labels={'x': 'Hour of Day', 'y': 'Number of Bids'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Daily activity
                daily_activity = bids_df['day_of_week'].value_counts()
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                daily_activity = daily_activity.reindex(day_order, fill_value=0)
                
                fig = px.bar(
                    x=daily_activity.index,
                    y=daily_activity.values,
                    title="Bid Submissions by Day of Week",
                    labels={'x': 'Day of Week', 'y': 'Number of Bids'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Tender lifecycle analysis
        if len(tenders_df) > 0:
            st.subheader("🔄 Tender Lifecycle Analysis")
            
            # Calculate tender duration (deadline - creation)
            tenders_df['created_at'] = pd.to_datetime(tenders_df['created_at'])
            tenders_df['deadline'] = pd.to_datetime(tenders_df['deadline'])
            tenders_df['duration_days'] = (tenders_df['deadline'] - tenders_df['created_at']).dt.days
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Tender duration distribution
                fig = px.histogram(
                    tenders_df,
                    x='duration_days',
                    nbins=20,
                    title="Tender Duration Distribution",
                    labels={'duration_days': 'Duration (Days)', 'count': 'Number of Tenders'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Status distribution
                status_counts = tenders_df['status'].value_counts()
                fig = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title="Tender Status Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Performance trends
        st.subheader("📈 Performance Trends")
        
        if len(bids_df) > 0:
            # Weekly performance metrics
            bids_df['week'] = bids_df['submitted_at'].dt.to_period('W')
            weekly_metrics = bids_df.groupby('week').agg({
                'id': 'count',
                'company_name': 'nunique',
                'bid_amount': 'mean'
            }).round(2)
            
            weekly_metrics.columns = ['Total Bids', 'Unique Companies', 'Avg Bid Amount']
            weekly_metrics.index = weekly_metrics.index.astype(str)
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Weekly Bid Volume', 'Weekly Company Participation', 'Average Bid Amount', 'System Load'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Bid volume
            fig.add_trace(
                go.Scatter(x=weekly_metrics.index, y=weekly_metrics['Total Bids'], name='Bid Volume'),
                row=1, col=1
            )
            
            # Company participation
            fig.add_trace(
                go.Scatter(x=weekly_metrics.index, y=weekly_metrics['Unique Companies'], name='Companies', line=dict(color='orange')),
                row=1, col=2
            )
            
            # Average bid amount
            fig.add_trace(
                go.Scatter(x=weekly_metrics.index, y=weekly_metrics['Avg Bid Amount'], name='Avg Amount', line=dict(color='green')),
                row=2, col=1
            )
            
            # System load (bids per day)
            daily_load = bids_df.groupby(bids_df['submitted_at'].dt.date).size()
            fig.add_trace(
                go.Scatter(x=[str(d) for d in daily_load.index], y=daily_load.values, name='Daily Load', line=dict(color='red')),
                row=2, col=2
            )
            
            fig.update_layout(height=600, showlegend=False, title_text="System Performance Trends")
            st.plotly_chart(fig, use_container_width=True)
        
        # Quality metrics
        if len(bids_df) > 0:
            st.subheader("✅ Quality Metrics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Data completeness
                required_fields = ['company_name', 'contact_email', 'bid_amount', 'proposal']
                completeness_scores = []
                
                for field in required_fields:
                    if field in bids_df.columns:
                        non_null_rate = (bids_df[field].notna().sum() / len(bids_df)) * 100
                        completeness_scores.append(non_null_rate)
                
                avg_completeness = np.mean(completeness_scores) if completeness_scores else 0
                st.metric("Data Completeness", f"{avg_completeness:.1f}%")
            
            with col2:
                # Proposal quality (based on length)
                if 'proposal' in bids_df.columns:
                    avg_proposal_length = bids_df['proposal'].str.len().mean()
                    quality_score = min(100, (avg_proposal_length / 500) * 100)  # 500 chars = 100%
                    st.metric("Proposal Quality", f"{quality_score:.0f}/100")
                else:
                    st.metric("Proposal Quality", "N/A")
            
            with col3:
                # Response rate (unique companies vs total tenders)
                if len(tenders_df) > 0:
                    response_rate = (unique_companies / len(tenders_df)) * 100
                    st.metric("Market Response", f"{response_rate:.1f}%")
                else:
                    st.metric("Market Response", "N/A")
        
    except Exception as e:
        st.error(f"❌ Error loading operational metrics: {str(e)}")

def system_admin_dashboard(db):
    """System administration dashboard with data management options"""
    st.header("⚙️ System Administration")
    
    st.warning("⚠️ **Administrator Functions** - These actions are irreversible!")
    
    # Clear Data Section
    st.subheader("🗑️ Clear Data Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Clear Individual Tables")
        st.info("Remove data from specific tables while keeping others intact.")
        
        # Individual table clearing
        table_options = {
            'tenders': 'Clear all tender data',
            'bids': 'Clear all bid data', 
            'ai_alerts': 'Clear all AI alerts',
            'audit_logs': 'Clear audit logs (except this action)'
        }
        
        for table, description in table_options.items():
            with st.expander(f"🗂️ {table.title()}"):
                st.write(description)
                
                # Show current count
                try:
                    if table == 'tenders':
                        count = len(db.get_tenders())
                    elif table == 'bids':
                        count = len(db.get_bids())
                    elif table == 'ai_alerts':
                        count = len(db.get_ai_alerts())
                    elif table == 'audit_logs':
                        count = len(db.get_audit_logs())
                    
                    st.metric(f"Current {table} count", count)
                    
                    if st.button(f"Clear {table}", 
                                key=f"clear_{table}",
                                type="secondary"):
                        with st.spinner(f"Clearing {table}..."):
                            success, message = db.clear_table_data(table)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                                
                except Exception as e:
                    st.error(f"Error getting {table} count: {str(e)}")
    
    with col2:
        st.markdown("### Clear All Data")
        st.error("⛔ **DANGER ZONE** - This will remove ALL system data!")
        
        # System overview before clearing
        try:
            tenders_count = len(db.get_tenders())
            bids_count = len(db.get_bids())
            alerts_count = len(db.get_ai_alerts())
            
            st.markdown("**Current System Data:**")
            st.write(f"• Tenders: {tenders_count}")
            st.write(f"• Bids: {bids_count}")
            st.write(f"• AI Alerts: {alerts_count}")
            
            # Confirmation checkbox
            confirm_clear = st.checkbox(
                "I understand this will permanently delete all system data",
                key="confirm_clear_all"
            )
            
            if confirm_clear:
                if st.button("🚨 CLEAR ALL DATA", 
                            key="clear_all_data",
                            type="primary"):
                    with st.spinner("Clearing all system data..."):
                        success, message = db.clear_all_data()
                        if success:
                            st.success(message)
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(message)
            else:
                st.button("🚨 CLEAR ALL DATA", 
                         disabled=True,
                         help="Check the confirmation box above to enable")
                         
        except Exception as e:
            st.error(f"Error loading system overview: {str(e)}")
    
    st.markdown("---")
    
    # Database Information
    st.subheader("📊 Database Information")
    
    try:
        # Get database file info
        import os
        db_path = db.db_path
        
        if os.path.exists(db_path):
            db_size = os.path.getsize(db_path)
            db_size_mb = db_size / (1024 * 1024)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Database Size", f"{db_size_mb:.2f} MB")
            
            with col2:
                st.metric("Database Path", db_path.split('/')[-1])
            
            with col3:
                modified_time = datetime.fromtimestamp(os.path.getmtime(db_path))
                st.metric("Last Modified", modified_time.strftime("%Y-%m-%d %H:%M"))
        else:
            st.error("Database file not found!")
            
    except Exception as e:
        st.error(f"Error getting database info: {str(e)}")

if __name__ == "__main__":
    main()
