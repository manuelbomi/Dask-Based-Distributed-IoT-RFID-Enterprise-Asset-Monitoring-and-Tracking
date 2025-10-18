"""
Temperature Dashboard Components
Reusable components for cold chain temperature monitoring analytics
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def display_temperature_summary(analytics):
    """Display temperature monitoring summary metrics"""
    summary = analytics.get_summary_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Records", f"{summary['total_records']:,}")
    with col2:
        st.metric("Unique Sensors", summary['unique_sensors'])
    with col3:
        st.metric("Average Temperature", f"{summary['avg_temperature']:.1f}°C")
    with col4:
        st.metric("Date Range", 
                 f"{summary['date_range_start'].strftime('%m/%d')} - {summary['date_range_end'].strftime('%m/%d')}")

def create_temperature_distribution_chart(df, facility_col='facility', temp_col='temperature'):
    """
    Create temperature distribution visualization
    
    Parameters:
    - df: DataFrame with temperature data
    - facility_col: Column containing facility names
    - temp_col: Column containing temperature values
    
    Returns:
    - Plotly figure
    """
    try:
        fig = px.box(
            df, 
            x=facility_col, 
            y=temp_col,
            title='Temperature Distribution by Facility',
            color=facility_col,
            points='all'
        )
        
        fig.update_layout(
            xaxis_title="Facility",
            yaxis_title="Temperature (°C)",
            showlegend=False,
            height=500
        )
        
        # Add threshold lines for different facility types
        fig.add_hline(y=-15, line_dash="dash", line_color="red", 
                     annotation_text="Cold Storage Max", annotation_position="bottom right")
        fig.add_hline(y=-25, line_dash="dash", line_color="blue",
                     annotation_text="Cold Storage Min", annotation_position="bottom right")
        fig.add_hline(y=8, line_dash="dash", line_color="orange",
                     annotation_text="Refrigerated Max", annotation_position="top right")
        fig.add_hline(y=2, line_dash="dash", line_color="green",
                     annotation_text="Refrigerated Min", annotation_position="top right")
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating temperature distribution chart: {e}")
        return None

def create_temperature_timeline(df, facility_filter=None, sample_size=200):
    """
    Create interactive temperature timeline
    
    Parameters:
    - df: DataFrame with temperature data
    - facility_filter: Specific facility to filter by
    - sample_size: Number of points to display
    
    Returns:
    - Plotly figure
    """
    try:
        if facility_filter:
            plot_df = df[df['facility'] == facility_filter].head(sample_size)
            title = f'Temperature Timeline - {facility_filter}'
        else:
            plot_df = df.head(sample_size)
            title = 'Temperature Timeline (Sample)'
        
        fig = px.line(
            plot_df,
            x='timestamp',
            y='temperature',
            color='facility',
            title=title,
            hover_data=['sensor_zone', 'epc']
        )
        
        fig.update_layout(
            xaxis_title="Timestamp",
            yaxis_title="Temperature (°C)",
            height=400
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating temperature timeline: {e}")
        return None

def display_critical_breaches_analysis(breaches_df):
    """
    Display critical temperature breaches analysis
    
    Parameters:
    - breaches_df: DataFrame with breach analysis
    """
    try:
        if breaches_df.empty:
            st.success(" No critical temperature breaches detected!")
            return
        
        st.subheader(" Critical Temperature Breaches")
        
        # Summary metrics
        total_breaches = breaches_df['Breach_Count'].sum()
        max_breach_rate = breaches_df['Breach_Rate_Pct'].max()
        worst_facility = breaches_df.loc[breaches_df['Breach_Rate_Pct'].idxmax(), 'Facility']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Critical Breaches", total_breaches)
        with col2:
            st.metric("Highest Breach Rate", f"{max_breach_rate:.1f}%")
        with col3:
            st.metric("Most Affected Facility", worst_facility)
        
        # Breaches by facility
        fig = px.bar(
            breaches_df,
            x='Facility',
            y='Breach_Count',
            color='Facility_Type',
            title='Critical Breaches by Facility',
            hover_data=['Breach_Rate_Pct', 'Min_Temp_Found', 'Max_Temp_Found']
        )
        
        fig.update_layout(
            xaxis_title="Facility",
            yaxis_title="Number of Breaches",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Breach details table
        st.subheader("Breach Details")
        display_df = breaches_df.copy()
        display_df['Breach_Rate_Pct'] = display_df['Breach_Rate_Pct'].round(2)
        display_df['Min_Temp_Found'] = display_df['Min_Temp_Found'].round(2)
        display_df['Max_Temp_Found'] = display_df['Max_Temp_Found'].round(2)
        
        st.dataframe(display_df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error displaying breaches analysis: {e}")

def create_rolling_statistics_dashboard(rolling_df):
    """
    Create comprehensive rolling statistics dashboard
    
    Parameters:
    - rolling_df: DataFrame with rolling statistics
    """
    try:
        st.subheader("📊 Rolling Statistics Dashboard")
        
        # Key metrics
        anomalies_count = rolling_df['is_anomaly'].sum()
        anomaly_rate = (anomalies_count / len(rolling_df)) * 100
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Anomalies Detected", f"{anomalies_count:,}")
        with col2:
            st.metric("Anomaly Rate", f"{anomaly_rate:.2f}%")
        with col3:
            avg_rolling_std = rolling_df['rolling_std'].mean()
            st.metric("Avg Rolling Std", f"{avg_rolling_std:.2f}°C")
        with col4:
            max_deviation = (rolling_df['temperature'] - rolling_df['rolling_avg']).abs().max()
            st.metric("Max Deviation", f"{max_deviation:.2f}°C")
        
        # Sample rolling statistics table
        st.subheader("Sample Rolling Statistics")
        sample_data = rolling_df[['timestamp', 'facility', 'temperature', 'rolling_avg', 'rolling_std', 'is_anomaly']].head(10)
        sample_data['temperature'] = sample_data['temperature'].round(2)
        sample_data['rolling_avg'] = sample_data['rolling_avg'].round(2)
        sample_data['rolling_std'] = sample_data['rolling_std'].round(2)
        sample_data['timestamp'] = sample_data['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
        
        st.dataframe(sample_data, use_container_width=True)
        
        # Rolling statistics visualization
        st.subheader("Rolling Average vs Actual Temperature")
        
        # Select a sample sensor for detailed view
        sample_sensors = rolling_df['epc'].unique()[:3]
        
        for sensor in sample_sensors:
            sensor_data = rolling_df[rolling_df['epc'] == sensor].head(50)
            
            fig = go.Figure()
            
            # Actual temperature
            fig.add_trace(go.Scatter(
                x=sensor_data['timestamp'],
                y=sensor_data['temperature'],
                mode='lines+markers',
                name='Actual Temperature',
                line=dict(color='blue', width=2)
            ))
            
            # Rolling average
            fig.add_trace(go.Scatter(
                x=sensor_data['timestamp'],
                y=sensor_data['rolling_avg'],
                mode='lines',
                name='6-Hour Rolling Average',
                line=dict(color='red', width=3, dash='dash')
            ))
            
            # Anomalies
            anomalies = sensor_data[sensor_data['is_anomaly'] == True]
            if not anomalies.empty:
                fig.add_trace(go.Scatter(
                    x=anomalies['timestamp'],
                    y=anomalies['temperature'],
                    mode='markers',
                    name='Anomalies',
                    marker=dict(color='red', size=10, symbol='x')
                ))
            
            fig.update_layout(
                title=f'Temperature Trends - Sensor {sensor}',
                xaxis_title="Timestamp",
                yaxis_title="Temperature (°C)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Anomaly distribution by facility
        st.subheader("Anomaly Distribution")
        
        anomaly_by_facility = rolling_df.groupby('facility').agg({
            'is_anomaly': ['sum', 'count']
        }).round(3)
        anomaly_by_facility.columns = ['anomalies', 'total_readings']
        anomaly_by_facility['anomaly_rate'] = (anomaly_by_facility['anomalies'] / anomaly_by_facility['total_readings'] * 100).round(2)
        anomaly_by_facility = anomaly_by_facility.reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                anomaly_by_facility,
                x='facility',
                y='anomaly_rate',
                title='Anomaly Rate by Facility (%)',
                color='anomaly_rate',
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.pie(
                anomaly_by_facility,
                values='anomalies',
                names='facility',
                title='Anomaly Distribution by Facility'
            )
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error creating rolling statistics dashboard: {e}")

def create_compliance_metrics_dashboard(compliance_df):
    """
    Create compliance metrics dashboard
    
    Parameters:
    - compliance_df: DataFrame with compliance metrics
    """
    try:
        st.subheader("📈 Compliance Metrics Dashboard")
        
        # Compliance summary
        compliance_summary = compliance_df['compliance_status'].value_counts()
        total_sensors = len(compliance_df)
        compliant_sensors = compliance_summary.get('COMPLIANT', 0)
        compliance_rate = (compliant_sensors / total_sensors * 100) if total_sensors > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Sensors", total_sensors)
        with col2:
            st.metric("Compliant Sensors", compliant_sensors)
        with col3:
            st.metric("Compliance Rate", f"{compliance_rate:.1f}%")
        with col4:
            critical_sensors = compliance_summary.get('CRITICAL', 0)
            st.metric("Critical Alerts", critical_sensors)
        
        # Compliance status distribution
        fig = px.pie(
            values=compliance_summary.values,
            names=compliance_summary.index,
            title='Overall Compliance Status Distribution',
            color=compliance_summary.index,
            color_discrete_map={
                'COMPLIANT': '#2ca02c',
                'WARNING': '#ff7f0e', 
                'CRITICAL': '#d62728'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Compliance by facility type
        st.subheader("Compliance by Facility Type")
        
        compliance_by_type = compliance_df.groupby('facility_type').agg({
            'compliance_status': lambda x: (x == 'COMPLIANT').mean(),
            'breach_rate': 'mean',
            'mean_temp': 'mean'
        }).round(3)
        
        compliance_by_type.columns = ['compliance_rate', 'avg_breach_rate', 'avg_temperature']
        compliance_by_type['compliance_rate_pct'] = (compliance_by_type['compliance_rate'] * 100).round(1)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                compliance_by_type.reset_index(),
                x='facility_type',
                y='compliance_rate_pct',
                title='Compliance Rate by Facility Type (%)',
                color='compliance_rate_pct',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.scatter(
                compliance_by_type.reset_index(),
                x='avg_temperature',
                y='compliance_rate_pct',
                size='avg_breach_rate',
                color='facility_type',
                title='Temperature vs Compliance Rate',
                hover_data=['avg_breach_rate']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed compliance table
        st.subheader("Detailed Compliance Metrics")
        
        display_compliance = compliance_df[['facility_type', 'epc', 'breach_rate', 'mean_temp', 'std_temp', 'compliance_status']].copy()
        display_compliance['breach_rate_pct'] = (display_compliance['breach_rate'] * 100).round(2)
        display_compliance['mean_temp'] = display_compliance['mean_temp'].round(2)
        display_compliance['std_temp'] = display_compliance['std_temp'].round(2)
        
        st.dataframe(display_compliance.head(15), use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating compliance metrics dashboard: {e}")

def create_temperature_heatmap(df, time_resolution='H'):
    """
    Create temperature heatmap by time and facility
    
    Parameters:
    - df: DataFrame with temperature data
    - time_resolution: Time resolution for heatmap ('H', 'D', 'W')
    
    Returns:
    - Plotly figure
    """
    try:
        # Prepare data for heatmap
        df_heatmap = df.copy()
        df_heatmap['hour'] = df_heatmap['timestamp'].dt.hour
        df_heatmap['date'] = df_heatmap['timestamp'].dt.date
        
        # Aggregate data
        heatmap_data = df_heatmap.groupby(['date', 'hour'])['temperature'].mean().unstack()
        
        fig = px.imshow(
            heatmap_data,
            title='Temperature Heatmap (Time vs Date)',
            color_continuous_scale='RdBu_r',
            aspect='auto',
            labels=dict(x="Hour of Day", y="Date", color="Temperature (°C)")
        )
        
        fig.update_layout(height=500)
        return fig
        
    except Exception as e:
        st.error(f"Error creating temperature heatmap: {e}")
        return None

def create_facility_comparison_dashboard(df):
    """
    Create facility comparison dashboard
    
    Parameters:
    - df: DataFrame with temperature data
    """
    try:
        st.subheader(" Facility Performance Comparison")
        
        # Calculate facility statistics
        facility_stats = df.groupby('facility').agg({
            'temperature': ['mean', 'std', 'min', 'max', 'count'],
            'epc': 'nunique'
        }).round(2)
        
        facility_stats.columns = ['avg_temp', 'std_temp', 'min_temp', 'max_temp', 'readings_count', 'sensor_count']
        facility_stats = facility_stats.reset_index()
        
        # Facility performance metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            best_facility = facility_stats.loc[facility_stats['std_temp'].idxmin(), 'facility']
            st.metric("Most Stable Facility", best_facility, 
                     delta=f"{facility_stats['std_temp'].min():.2f}°C std")
        
        with col2:
            worst_facility = facility_stats.loc[facility_stats['std_temp'].idxmax(), 'facility']
            st.metric("Least Stable Facility", worst_facility,
                     delta=f"{facility_stats['std_temp'].max():.2f}°C std", delta_color="inverse")
        
        with col3:
            avg_sensors = facility_stats['sensor_count'].mean()
            st.metric("Average Sensors per Facility", f"{avg_sensors:.1f}")
        
        # Facility comparison charts
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                facility_stats,
                x='facility',
                y='avg_temp',
                error_y='std_temp',
                title='Average Temperature by Facility with Std Dev',
                color='avg_temp',
                color_continuous_scale='RdYlBu_r'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.scatter(
                facility_stats,
                x='avg_temp',
                y='std_temp',
                size='sensor_count',
                color='facility',
                title='Temperature Stability vs Average',
                hover_data=['min_temp', 'max_temp']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed facility statistics table
        st.subheader("Facility Performance Details")
        st.dataframe(facility_stats, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating facility comparison dashboard: {e}")

def create_alert_system_dashboard(rolling_df, compliance_df):
    """
    Create alert system dashboard for temperature monitoring
    
    Parameters:
    - rolling_df: DataFrame with rolling statistics
    - compliance_df: DataFrame with compliance metrics
    """
    try:
        st.subheader(" Real-time Alert System")
        
        # Current alerts
        current_time = pd.Timestamp.now()
        recent_anomalies = rolling_df[
            (rolling_df['is_anomaly'] == True) & 
            (rolling_df['timestamp'] > (current_time - timedelta(hours=24)))
        ]
        
        critical_sensors = compliance_df[compliance_df['compliance_status'] == 'CRITICAL']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Recent Anomalies (24h)", len(recent_anomalies))
        
        with col2:
            st.metric("Critical Sensors", len(critical_sensors))
        
        with col3:
            warning_sensors = compliance_df[compliance_df['compliance_status'] == 'WARNING']
            st.metric("Warning Sensors", len(warning_sensors))
        
        # Recent anomalies table
        if not recent_anomalies.empty:
            st.subheader("Recent Temperature Anomalies")
            
            alert_df = recent_anomalies[['timestamp', 'facility', 'epc', 'temperature', 'rolling_avg', 'rolling_std']].copy()
            alert_df['deviation'] = (alert_df['temperature'] - alert_df['rolling_avg']).abs()
            alert_df['severity'] = alert_df['deviation'] / alert_df['rolling_std']
            alert_df = alert_df.sort_values('severity', ascending=False)
            
            # Color code by severity
            def get_alert_color(severity):
                if severity > 3:
                    return ' CRITICAL'
                elif severity > 2:
                    return ' HIGH'
                else:
                    return ' MEDIUM'
            
            alert_df['alert_level'] = alert_df['severity'].apply(get_alert_color)
            
            st.dataframe(alert_df.head(10), use_container_width=True)
        
        # Critical sensors alert
        if not critical_sensors.empty:
            st.subheader(" Critical Compliance Alerts")
            
            for _, sensor in critical_sensors.head(5).iterrows():
                st.error(
                    f"**{sensor['epc']}** at {sensor['facility_type']} - "
                    f"Breach Rate: {sensor['breach_rate']*100:.1f}%, "
                    f"Avg Temp: {sensor['mean_temp']:.1f}°C"
                )
        
        # Alert history timeline
        st.subheader("Alert History Timeline")
        
        if not recent_anomalies.empty:
            fig = px.scatter(
                recent_anomalies,
                x='timestamp',
                y='temperature',
                color='facility',
                size='rolling_std',
                title='Temperature Anomalies Timeline (Last 24 Hours)',
                hover_data=['epc', 'rolling_avg']
            )
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error creating alert system dashboard: {e}")

def create_export_panel(df, rolling_df, compliance_df, breaches_df):
    """
    Create data export panel for temperature analytics
    
    Parameters:
    - df: Original temperature data
    - rolling_df: Rolling statistics data
    - compliance_df: Compliance metrics data
    - breaches_df: Breach analysis data
    """
    try:
        st.subheader(" Export Analytics Data")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("Export Raw Data"):
                df.to_csv('temperature_raw_data.csv', index=False)
                st.success("Raw data exported!")
        
        with col2:
            if st.button("Export Rolling Stats"):
                rolling_df.to_csv('temperature_rolling_stats.csv', index=False)
                st.success("Rolling stats exported!")
        
        with col3:
            if st.button("Export Compliance Data"):
                compliance_df.to_csv('temperature_compliance.csv', index=False)
                st.success("Compliance data exported!")
        
        with col4:
            if st.button("Export Breach Analysis"):
                breaches_df.to_csv('temperature_breaches.csv', index=False)
                st.success("Breach analysis exported!")
        
        # Generate summary report
        if st.button("Generate Comprehensive Report"):
            report_data = {
                'report_generated': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'total_records': len(df),
                'unique_sensors': df['epc'].nunique(),
                'unique_facilities': df['facility'].nunique(),
                'avg_temperature': df['temperature'].mean(),
                'total_anomalies': rolling_df['is_anomaly'].sum(),
                'anomaly_rate': (rolling_df['is_anomaly'].sum() / len(rolling_df)) * 100,
                'total_breaches': breaches_df['Breach_Count'].sum() if not breaches_df.empty else 0,
                'compliance_rate': (compliance_df['compliance_status'] == 'COMPLIANT').mean() * 100
            }
            
            import json
            with open('temperature_analytics_report.json', 'w') as f:
                json.dump(report_data, f, indent=2)
            
            st.success("Comprehensive report generated!")
            
    except Exception as e:
        st.error(f"Error creating export panel: {e}")

def create_prediction_insights(df, horizon_hours=24):
    """
    Create temperature prediction insights (simulated)
    
    Parameters:
    - df: Temperature data for prediction
    - horizon_hours: Prediction horizon in hours
    """
    try:
        st.subheader(" Predictive Insights")
        
        # Simulate prediction (in real scenario, use ML model)
        latest_data = df.sort_values('timestamp').tail(100)
        
        # Simple trend analysis
        if len(latest_data) > 10:
            recent_trend = latest_data['temperature'].tail(10).mean() - latest_data['temperature'].head(10).mean()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if recent_trend > 0.5:
                    st.warning(" Warming Trend Detected")
                    st.metric("Trend Direction", "Increasing", f"+{recent_trend:.2f}°C")
                elif recent_trend < -0.5:
                    st.info(" Cooling Trend Detected") 
                    st.metric("Trend Direction", "Decreasing", f"{recent_trend:.2f}°C")
                else:
                    st.success(" Stable Trend")
                    st.metric("Trend Direction", "Stable", f"{recent_trend:.2f}°C")
            
            with col2:
                # Variability prediction
                current_std = latest_data['temperature'].std()
                if current_std > 3:
                    st.error(" High Variability")
                    st.metric("Stability", "Low", f"{current_std:.2f}°C std")
                elif current_std > 1.5:
                    st.warning(" Moderate Variability")
                    st.metric("Stability", "Medium", f"{current_std:.2f}°C std")
                else:
                    st.success(" Good Stability")
                    st.metric("Stability", "High", f"{current_std:.2f}°C std")
            
            with col3:
                # Risk assessment
                breach_risk = len(df[df['temperature'] > 8]) / len(df) * 100
                if breach_risk > 5:
                    st.error("High Breach Risk")
                    st.metric("Breach Risk", f"{breach_risk:.1f}%")
                elif breach_risk > 2:
                    st.warning(" Medium Breach Risk")
                    st.metric("Breach Risk", f"{breach_risk:.1f}%")
                else:
                    st.success("Low Breach Risk")
                    st.metric("Breach Risk", f"{breach_risk:.1f}%")
        
        # Seasonal patterns (simulated)
        st.subheader("Seasonal Pattern Analysis")
        
        # Extract month for seasonal analysis
        df_seasonal = df.copy()
        df_seasonal['month'] = df_seasonal['timestamp'].dt.month
        
        monthly_stats = df_seasonal.groupby('month').agg({
            'temperature': ['mean', 'std', 'count']
        }).round(2)
        monthly_stats.columns = ['avg_temp', 'std_temp', 'readings_count']
        monthly_stats = monthly_stats.reset_index()
        
        fig = px.line(
            monthly_stats,
            x='month',
            y='avg_temp',
            error_y='std_temp',
            title='Monthly Temperature Patterns',
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating prediction insights: {e}")

# Utility functions
def categorize_temperature_risk(temp, facility_type):
    """Categorize temperature risk level"""
    if facility_type == 'cold_storage':
        if temp > -15:
            return 'HIGH'
        elif temp > -20:
            return 'MEDIUM'
        else:
            return 'LOW'
    elif facility_type == 'refrigerated_transport':
        if temp > 8 or temp < 2:
            return 'HIGH'
        elif temp > 6 or temp < 4:
            return 'MEDIUM'
        else:
            return 'LOW'
    else:
        if temp > 25 or temp < 15:
            return 'HIGH'
        elif temp > 22 or temp < 18:
            return 'MEDIUM'
        else:
            return 'LOW'

def calculate_compliance_score(breach_rate, temp_stability, anomaly_rate):
    """Calculate overall compliance score (0-100)"""
    breach_score = max(0, 100 - (breach_rate * 1000))  # Penalize breaches heavily
    stability_score = max(0, 100 - (temp_stability * 10))  # Penalize instability
    anomaly_score = max(0, 100 - (anomaly_rate * 100))  # Penalize anomalies
    
    return (breach_score * 0.5 + stability_score * 0.3 + anomaly_score * 0.2)