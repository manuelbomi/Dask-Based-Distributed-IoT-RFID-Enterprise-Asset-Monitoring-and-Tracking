import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.temperature_analytics import TemperatureAnalytics
from analytics.rfid_analytics import RFIDAnalytics
from data_generation.generate_temperature_data import save_temperature_data
from data_generation.generate_rfid_data import save_rfid_data

# Page configuration
st.set_page_config(
    page_title="IoT Asset Tracking Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
def load_css():
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
    .anomaly-alert {
        background-color: #ffcccc;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ff0000;
    }
    .compliance-good {
        background-color: #ccffcc;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #00cc00;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    load_css()
    
    st.markdown('<h1 class="main-header">🏭 IoT Asset Tracking & Cold Chain Monitoring</h1>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.selectbox(
        "Choose Analysis Mode",
        ["Home", "Cold Chain Monitoring", "Asset Tracking", "Data Generation"]
    )
    
    if app_mode == "Home":
        show_home()
    elif app_mode == "Cold Chain Monitoring":
        show_temperature_analytics()
    elif app_mode == "Asset Tracking":
        show_rfid_analytics()
    elif app_mode == "Data Generation":
        show_data_generation()

def show_home():
    st.markdown("""
    ## Welcome to the IoT Asset Tracking Dashboard
    
    This application provides comprehensive analytics for two critical IoT use cases:
    
    ### 1. Cold Chain Temperature Monitoring
    - Real-time temperature anomaly detection
    - Compliance monitoring across facilities
    - Rolling average calculations
    - Critical breach alerts
    
    ### 2. RFID Asset Tracking
    - Asset movement pattern analysis
    - Gateway performance monitoring
    - Dwell time analytics
    - Real-time location tracking
    
    ### Technology Stack
    - **Frontend**: Streamlit
    - **Analytics**: Pandas & Dask for distributed computing
    - **Visualization**: Plotly, Matplotlib, Seaborn
    - **Deployment**: Docker & Docker Compose
    
    Use the sidebar to navigate to specific analytics modules.
    """)
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Sample Temperature Records", "10,000")
    with col2:
        st.metric("Sample RFID Events", "15,000")
    with col3:
        st.metric("Unique Assets", "500")
    with col4:
        st.metric("Monitoring Facilities", "5")

def show_temperature_analytics():
    st.header("🌡️ Cold Chain Temperature Monitoring")
    
    # Initialize analytics
    temp_analytics = TemperatureAnalytics('data_generation/sample_data/temperature_logs.json')
    
    # Generate data if not exists
    if not os.path.exists('data_generation/sample_data/temperature_logs.json'):
        with st.spinner("Generating sample temperature data..."):
            try:
                save_temperature_data()
                st.success(" Temperature data generated successfully!")
            except Exception as e:
                st.error(f" Error generating temperature data: {e}")
                return
    
    # Load data with error handling
    try:
        with st.spinner("Loading temperature data..."):
            df_loaded = temp_analytics.load_data_pandas()
            
        if df_loaded is None or len(df_loaded) == 0:
            st.error("No temperature data loaded. Please check data generation.")
            return
            
        summary = temp_analytics.get_summary_stats()
        
        if summary['total_records'] == 0:
            st.error(" No temperature records found in the data.")
            return
            
    except Exception as e:
        st.error(f" Error loading temperature data: {e}")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Records", f"{summary['total_records']:,}")
    with col2:
        st.metric("Unique Sensors", summary['unique_sensors'])
    with col3:
        st.metric("Average Temperature", f"{summary['avg_temperature']:.1f}°C")
    with col4:
        date_range = f"{summary['date_range_start'].strftime('%Y-%m-%d')} to {summary['date_range_end'].strftime('%Y-%m-%d')}" if summary['date_range_start'] else "N/A"
        st.metric("Date Range", date_range)
    
    # Tabs for different analyses
    tab1, tab2, tab3, tab4 = st.tabs(["Critical Breaches", "Rolling Statistics", "Compliance Metrics", "Visualizations"])
    
    with tab1:
        st.subheader("Critical Temperature Breaches")
        breaches_df = temp_analytics.pandas_critical_breaches()
        
        if breaches_df.empty:
            st.success(" No critical temperature breaches detected!")
        else:
            st.dataframe(breaches_df, use_container_width=True)
            
            # Breach summary
            total_breaches = breaches_df['Breach_Count'].sum()
            st.metric("Total Critical Breaches", total_breaches)
            
            # Facility-wise breach chart
            fig = px.bar(breaches_df, x='Facility', y='Breach_Count', 
                        color='Facility_Type', title='Critical Breaches by Facility')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Rolling Statistics & Anomaly Detection")
        
        with st.spinner("Calculating rolling statistics..."):
            rolling_df = temp_analytics.pandas_rolling_statistics()
        
        if rolling_df.empty:
            st.warning("No rolling statistics available")
        else:
            anomalies_count = rolling_df['is_anomaly'].sum()
            anomaly_rate = (anomalies_count / len(rolling_df)) * 100
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Anomalies Detected", f"{anomalies_count:,}")
            with col2:
                st.metric("Anomaly Rate", f"{anomaly_rate:.2f}%")
            
            # Show sample rolling data
            st.subheader("Sample Rolling Statistics")
            sample_data = rolling_df[['timestamp', 'temperature', 'rolling_avg', 'rolling_std', 'is_anomaly']].head(10)
            st.dataframe(sample_data, use_container_width=True)
            
            # Anomaly distribution
            anomaly_by_facility = rolling_df.groupby('facility')['is_anomaly'].mean() * 100
            fig = px.bar(x=anomaly_by_facility.index, y=anomaly_by_facility.values,
                        title='Anomaly Rate by Facility (%)', labels={'x': 'Facility', 'y': 'Anomaly Rate %'})
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("Dask Compliance Metrics")
        
        with st.spinner("Calculating compliance metrics with Dask..."):
            compliance_df = temp_analytics.dask_compliance_metrics()
        
        if compliance_df.empty:
            st.warning("No compliance metrics available")
        else:
            st.dataframe(compliance_df.head(10), use_container_width=True)
            
            # Compliance summary
            compliance_summary = compliance_df['compliance_status'].value_counts()
            fig = px.pie(values=compliance_summary.values, names=compliance_summary.index,
                        title='Overall Compliance Status')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.subheader("Temperature Visualizations")
        
        if temp_analytics.df_pandas is not None and len(temp_analytics.df_pandas) > 0:
            # Temperature distribution
            fig = px.histogram(temp_analytics.df_pandas, x='temperature', color='facility',
                              title='Temperature Distribution by Facility')
            st.plotly_chart(fig, use_container_width=True)
            
            # Time series of temperatures
            sample_facility = st.selectbox("Select Facility", temp_analytics.df_pandas['facility'].unique())
            facility_data = temp_analytics.df_pandas[temp_analytics.df_pandas['facility'] == sample_facility]
            
            if len(facility_data) > 0:
                fig = px.line(facility_data.head(100), x='timestamp', y='temperature',
                             title=f'Temperature Timeline - {sample_facility}')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"No data available for {sample_facility}")
        else:
            st.warning("No data available for visualizations")

def show_rfid_analytics():
    st.header("📡 RFID Asset Tracking Analytics")
    
    # Initialize analytics
    rfid_analytics = RFIDAnalytics('data_generation/sample_data/rfid_events.json')
    
    # Generate data if not exists
    if not os.path.exists('data_generation/sample_data/rfid_events.json'):
        with st.spinner("Generating sample RFID data..."):
            try:
                save_rfid_data()
                st.success(" RFID data generated successfully!")
            except Exception as e:
                st.error(f" Error generating RFID data: {e}")
                return
    
    # Load data with error handling
    try:
        with st.spinner("Loading RFID data..."):
            df_loaded = rfid_analytics.load_data_pandas()
            
        if df_loaded is None or len(df_loaded) == 0:
            st.error(" No RFID data loaded. Please check data generation.")
            return
            
        summary = rfid_analytics.get_summary_stats()
        
        if summary['total_events'] == 0:
            st.error(" No RFID events found in the data.")
            return
            
    except Exception as e:
        st.error(f" Error loading RFID data: {e}")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Events", f"{summary['total_events']:,}")
    with col2:
        st.metric("Unique Assets", summary['unique_assets'])
    with col3:
        st.metric("Monitoring Locations", summary['unique_locations'])
    with col4:
        st.metric("Average RSSI", f"{summary['avg_signal_strength']:.0f}")
    
    # Tabs for different analyses
    tab1, tab2, tab3, tab4 = st.tabs(["Movement Analysis", "Dwell Times", "Gateway Performance", "Real-time Tracking"])
    
    with tab1:
        st.subheader("Asset Movement Analysis")
        
        with st.spinner("Analyzing movement patterns..."):
            movement_df = rfid_analytics.pandas_movement_analysis()
        
        if movement_df.empty:
            st.warning("No movement analysis data available")
        else:
            st.dataframe(movement_df.head(10), use_container_width=True)
            
            # Movement statistics by asset type
            movement_by_type = movement_df.groupby('asset_type').agg({
                'has_moved': 'mean',
                'locations_visited': 'mean',
                'movement_rate': 'mean'
            }).round(3)
            
            movement_by_type['has_moved'] = (movement_by_type['has_moved'] * 100).round(1)
            movement_by_type.columns = ['Move Rate %', 'Avg Locations', 'Avg Movement Rate']
            
            st.subheader("Movement Statistics by Asset Type")
            st.dataframe(movement_by_type, use_container_width=True)
            
            # Visualization
            fig = px.bar(movement_by_type.reset_index(), x='asset_type', y='Move Rate %',
                        title='Movement Rate by Asset Type (%)')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Dwell Time Analysis with Rolling Averages")
        
        with st.spinner("Calculating dwell times..."):
            dwell_df = rfid_analytics.pandas_dwell_time_analysis()
        
        if dwell_df.empty:
            st.warning("No dwell time data available")
        else:
            anomalies_count = dwell_df['dwell_anomaly'].sum()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Dwell Time Anomalies", f"{anomalies_count:,}")
            with col2:
                st.metric("Total Movements Analyzed", f"{len(dwell_df):,}")
            
            # Dwell time statistics by location
            dwell_by_location = dwell_df.groupby('gateway_location').agg({
                'dwell_time_seconds': ['mean', 'std', 'count'],
                'dwell_anomaly': 'sum'
            }).round(2)
            
            dwell_by_location.columns = ['avg_dwell_sec', 'std_dwell', 'movement_count', 'anomalies']
            dwell_by_location['anomaly_rate_pct'] = (dwell_by_location['anomalies'] / dwell_by_location['movement_count'] * 100).round(2)
            
            st.subheader("Dwell Time Statistics by Location")
            st.dataframe(dwell_by_location, use_container_width=True)
            
            # Sample rolling dwell times
            st.subheader("Sample Rolling Dwell Time Calculations")
            if len(dwell_df['epc_number'].unique()) > 0:
                sample_asset = st.selectbox("Select Asset", dwell_df['epc_number'].unique()[:5])
                asset_data = dwell_df[dwell_df['epc_number'] == sample_asset][['timestamp', 'gateway_location', 'dwell_time_seconds', 'rolling_avg_dwell', 'dwell_anomaly']].head(10)
                st.dataframe(asset_data, use_container_width=True)
            else:
                st.warning("No asset data available for display")
    
    with tab3:
        st.subheader("Gateway Performance Analysis")
        
        if rfid_analytics.df_pandas is not None and len(rfid_analytics.df_pandas) > 0:
            gateway_performance = rfid_analytics.df_pandas.groupby('gateway_location').agg({
                'gateway_ant_rssi': ['mean', 'std', 'count'],
                'gateway_xmit_power': 'mean',
                'epc_number': 'nunique'
            }).round(2)
            
            gateway_performance.columns = ['avg_rssi', 'std_rssi', 'read_count', 'avg_tx_power', 'unique_assets']
            gateway_performance['reads_per_asset'] = (gateway_performance['read_count'] / gateway_performance['unique_assets']).round(1)
            
            st.dataframe(gateway_performance, use_container_width=True)
            
            # Signal strength visualization
            fig = px.bar(gateway_performance.reset_index(), x='gateway_location', y='avg_rssi',
                        title='Average RSSI by Gateway Location')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No gateway performance data available")
    
    with tab4:
        st.subheader("Real-time Asset Distribution")
        
        if rfid_analytics.df_pandas is not None and len(rfid_analytics.df_pandas) > 0:
            # Current location of assets
            current_locations = (
                rfid_analytics.df_pandas.sort_values('timestamp')
                .groupby('epc_number')
                .last()
                .reset_index()
            )
            
            location_distribution = current_locations['gateway_location'].value_counts()
            
            fig = px.pie(values=location_distribution.values, names=location_distribution.index,
                        title='Current Asset Distribution Across Locations')
            st.plotly_chart(fig, use_container_width=True)
            
            # Asset type distribution by location
            asset_location_matrix = pd.crosstab(current_locations['gateway_location'], current_locations['asset_type'])
            st.subheader("Asset Type Distribution by Location")
            st.dataframe(asset_location_matrix, use_container_width=True)
        else:
            st.warning("No asset distribution data available")

def show_data_generation():
    st.header(" Data Generation")
    
    st.markdown("""
    This section allows you to generate new sample data for both use cases.
    The generated data will be used for all analytics in the dashboard.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Temperature Data")
        if st.button("Generate Temperature Data", key="temp_gen"):
            with st.spinner("Generating temperature data..."):
                try:
                    save_temperature_data()
                    st.success(" Temperature data generated successfully!")
                except Exception as e:
                    st.error(f" Error generating temperature data: {e}")
        
        st.info("""
        **Temperature Data Details:**
        - 10,000 temperature readings
        - 5 different facilities
        - 3 types of storage conditions
        - Realistic temperature patterns with anomalies
        """)
    
    with col2:
        st.subheader("RFID Asset Tracking Data")
        if st.button("Generate RFID Data", key="rfid_gen"):
            with st.spinner("Generating RFID data..."):
                try:
                    save_rfid_data()
                    st.success(" RFID data generated successfully!")
                except Exception as e:
                    st.error(f" Error generating RFID data: {e}")
        
        st.info("""
        **RFID Data Details:**
        - 15,000 RFID events
        - 500 unique assets
        - 5 gateway locations
        - 4 asset types with different movement patterns
        """)
    
    # Data preview section
    st.subheader("Data Preview")
    
    preview_tab1, preview_tab2 = st.tabs(["Temperature Data", "RFID Data"])
    
    with preview_tab1:
        if os.path.exists('data_generation/sample_data/temperature_logs.json'):
            try:
                temp_df = pd.read_json('data_generation/sample_data/temperature_logs.json', lines=True)
                st.dataframe(temp_df.head(10), use_container_width=True)
                st.success(f" Loaded {len(temp_df)} temperature records")
            except Exception as e:
                st.error(f" Error loading temperature data: {e}")
        else:
            st.warning("No temperature data available. Generate data first.")
    
    with preview_tab2:
        if os.path.exists('data_generation/sample_data/rfid_events.json'):
            try:
                rfid_df = pd.read_json('data_generation/sample_data/rfid_events.json', lines=True)
                st.dataframe(rfid_df.head(10), use_container_width=True)
                st.success(" RFID data loaded successfully")
            except Exception as e:
                st.error(f" Error loading RFID data: {e}")
        else:
            st.warning("No RFID data available. Generate data first.")

if __name__ == "__main__":
    main()