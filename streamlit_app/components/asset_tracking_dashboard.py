"""
Asset Tracking Dashboard Components
Reusable components for RFID asset tracking analytics
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
import networkx as nx

def display_asset_summary(analytics):
    """Display asset tracking summary metrics"""
    summary = analytics.get_summary_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Events", f"{summary['total_events']:,}")
    with col2:
        st.metric("Unique Assets", summary['unique_assets'])
    with col3:
        st.metric("Monitoring Locations", summary['unique_locations'])
    with col4:
        st.metric("Average RSSI", f"{summary['avg_signal_strength']:.0f}")

def create_movement_heatmap(movement_df, facility_locations):
    """
    Create a heatmap of asset movements between locations
    
    Parameters:
    - movement_df: DataFrame with movement data
    - facility_locations: List of facility locations
    
    Returns:
    - Plotly figure
    """
    try:
        # Create movement matrix
        movement_matrix = pd.DataFrame(0, index=facility_locations, columns=facility_locations)
        
        # Count movements between locations
        for i in range(len(movement_df) - 1):
            current_loc = movement_df.iloc[i]['gateway_location']
            next_loc = movement_df.iloc[i + 1]['gateway_location']
            if current_loc != next_loc:
                movement_matrix.loc[current_loc, next_loc] += 1
        
        # Create heatmap
        fig = px.imshow(
            movement_matrix,
            title="Asset Movement Heatmap Between Locations",
            color_continuous_scale="Blues",
            aspect="auto"
        )
        
        fig.update_layout(
            xaxis_title="To Location",
            yaxis_title="From Location",
            height=500
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating movement heatmap: {e}")
        return None

def create_asset_movement_network(movement_df, top_n_assets=10):
    """
    Create a network graph of asset movements
    
    Parameters:
    - movement_df: DataFrame with movement data
    - top_n_assets: Number of top assets to include
    
    Returns:
    - Plotly figure
    """
    try:
        # Get top moving assets
        asset_movements = movement_df.groupby('epc_number').size().nlargest(top_n_assets)
        top_assets = asset_movements.index.tolist()
        
        # Filter data for top assets
        filtered_df = movement_df[movement_df['epc_number'].isin(top_assets)]
        
        # Create network graph
        G = nx.DiGraph()
        
        # Add nodes and edges
        for asset in top_assets:
            asset_data = filtered_df[filtered_df['epc_number'] == asset].sort_values('timestamp')
            locations = asset_data['gateway_location'].tolist()
            
            for i in range(len(locations) - 1):
                source = locations[i]
                target = locations[i + 1]
                
                if source != target:
                    if G.has_edge(source, target):
                        G[source][target]['weight'] += 1
                    else:
                        G.add_edge(source, target, weight=1)
        
        # Create plotly network graph
        pos = nx.spring_layout(G, k=1, iterations=50)
        
        edge_x = []
        edge_y = []
        edge_weights = []
        
        for edge in G.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_weights.append(edge[2]['weight'])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=2, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        node_x = []
        node_y = []
        node_text = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition="middle center",
            marker=dict(
                size=20,
                color='lightblue',
                line=dict(width=2, color='darkblue')
            )
        )
        
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title='Asset Movement Network',
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           annotations=[ dict(
                               text="Node size represents location importance",
                               showarrow=False,
                               xref="paper", yref="paper",
                               x=0.005, y=-0.002 ) ],
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                       )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating movement network: {e}")
        return None

def display_dwell_time_analysis(dwell_df):
    """
    Display comprehensive dwell time analysis
    
    Parameters:
    - dwell_df: DataFrame with dwell time calculations
    """
    try:
        col1, col2 = st.columns(2)
        
        with col1:
            # Dwell time distribution
            fig = px.histogram(
                dwell_df, 
                x='dwell_time_seconds',
                title='Dwell Time Distribution',
                nbins=50,
                color_discrete_sequence=['#1f77b4']
            )
            fig.update_layout(
                xaxis_title="Dwell Time (seconds)",
                yaxis_title="Frequency"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Dwell time by location
            dwell_by_location = dwell_df.groupby('gateway_location').agg({
                'dwell_time_seconds': 'mean'
            }).reset_index()
            
            fig = px.bar(
                dwell_by_location,
                x='gateway_location',
                y='dwell_time_seconds',
                title='Average Dwell Time by Location',
                color='dwell_time_seconds',
                color_continuous_scale='Viridis'
            )
            fig.update_layout(
                xaxis_title="Location",
                yaxis_title="Average Dwell Time (seconds)"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Rolling dwell time trends
        st.subheader("Rolling Dwell Time Trends")
        
        # Sample a few assets for demonstration
        sample_assets = dwell_df['epc_number'].unique()[:3]
        
        for asset in sample_assets:
            asset_data = dwell_df[dwell_df['epc_number'] == asset]
            if len(asset_data) > 5:
                fig = px.line(
                    asset_data.head(20),
                    x='timestamp',
                    y=['dwell_time_seconds', 'rolling_avg_dwell'],
                    title=f'Dwell Time Trends - {asset}',
                    labels={'value': 'Time (seconds)', 'variable': 'Metric'}
                )
                fig.update_layout(
                    xaxis_title="Timestamp",
                    yaxis_title="Dwell Time (seconds)"
                )
                st.plotly_chart(fig, use_container_width=True)
                
    except Exception as e:
        st.error(f"Error displaying dwell time analysis: {e}")

def create_gateway_performance_dashboard(gateway_data):
    """
    Create comprehensive gateway performance dashboard
    
    Parameters:
    - gateway_data: DataFrame with gateway performance metrics
    """
    try:
        st.subheader("Gateway Performance Overview")
        
        # Create subplots for gateway metrics
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Average RSSI by Gateway',
                'Transmit Power Distribution',
                'Read Count by Gateway', 
                'Signal Quality Distribution'
            )
        )
        
        # RSSI by Gateway
        fig.add_trace(
            go.Bar(
                x=gateway_data.index,
                y=gateway_data['avg_rssi'],
                name='Avg RSSI',
                marker_color='lightcoral'
            ),
            row=1, col=1
        )
        
        # Transmit Power
        fig.add_trace(
            go.Box(
                y=gateway_data['avg_tx_power'],
                name='TX Power',
                marker_color='lightgreen'
            ),
            row=1, col=2
        )
        
        # Read Count
        fig.add_trace(
            go.Bar(
                x=gateway_data.index,
                y=gateway_data['read_count'],
                name='Read Count',
                marker_color='lightsalmon'
            ),
            row=2, col=1
        )
        
        # Signal Quality (calculated from RSSI)
        signal_quality = gateway_data['avg_rssi'].apply(
            lambda x: 'Excellent' if x > -1800 else 'Good' if x > -2200 else 'Poor' if x > -2600 else 'Very Poor'
        )
        quality_counts = signal_quality.value_counts()
        
        fig.add_trace(
            go.Pie(
                labels=quality_counts.index,
                values=quality_counts.values,
                name='Signal Quality',
                hole=0.4
            ),
            row=2, col=2
        )
        
        fig.update_layout(height=600, showlegend=False, title_text="Gateway Performance Metrics")
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating gateway performance dashboard: {e}")

def display_real_time_asset_locations(current_locations, facility_data):
    """
    Display real-time asset location tracking
    
    Parameters:
    - current_locations: DataFrame with current asset positions
    - facility_data: DataFrame with facility information
    """
    try:
        st.subheader(" Real-time Asset Location Tracking")
        
        # Current asset distribution
        location_distribution = current_locations['gateway_location'].value_counts()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Location map (simulated)
            fig = px.treemap(
                names=location_distribution.index,
                parents=[''] * len(location_distribution),
                values=location_distribution.values,
                title='Current Asset Distribution Across Facilities'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Quick stats
            st.metric("Assets in Transit", 
                     len(current_locations[current_locations['gateway_location'].str.contains('transport')]))
            st.metric("Assets in Storage", 
                     len(current_locations[current_locations['gateway_location'].str.contains('storage')]))
            st.metric("Assets at Entry/Exit", 
                     len(current_locations[current_locations['gateway_location'].str.contains('entrance|exit')]))
        
        # Asset type distribution by location
        st.subheader("Asset Type Distribution by Location")
        asset_location_matrix = pd.crosstab(
            current_locations['gateway_location'], 
            current_locations['asset_type']
        )
        
        fig = px.imshow(
            asset_location_matrix,
            title="Asset Type Distribution Matrix",
            color_continuous_scale="Blues",
            aspect="auto"
        )
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error displaying real-time locations: {e}")

def create_movement_pattern_analysis(movement_df):
    """
    Analyze and visualize movement patterns
    
    Parameters:
    - movement_df: DataFrame with movement analysis
    """
    try:
        st.subheader("Movement Pattern Analysis")
        
        # Movement complexity by asset type
        movement_complexity = movement_df.groupby('asset_type').agg({
            'movement_rate': ['mean', 'std'],
            'locations_visited': 'mean',
            'has_moved': 'mean'
        }).round(3)
        
        # Flatten columns
        movement_complexity.columns = [
            'avg_movement_rate', 'std_movement_rate',
            'avg_locations', 'move_probability'
        ]
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Movement rate by asset type
            fig = px.bar(
                movement_complexity.reset_index(),
                x='asset_type',
                y='avg_movement_rate',
                title='Average Movement Rate by Asset Type',
                color='avg_movement_rate',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Movement probability
            fig = px.pie(
                movement_complexity.reset_index(),
                names='asset_type',
                values='move_probability',
                title='Movement Probability by Asset Type'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Time-based movement patterns
        st.subheader("Time-based Movement Patterns")
        
        # Extract hour from timestamps for sample data
        if 'timestamp' in movement_df.columns:
            movement_df['hour'] = pd.to_datetime(movement_df['timestamp']).dt.hour
            
            hourly_movements = movement_df.groupby('hour').size()
            
            fig = px.line(
                x=hourly_movements.index,
                y=hourly_movements.values,
                title='Movement Frequency by Hour of Day',
                labels={'x': 'Hour of Day', 'y': 'Number of Movements'}
            )
            fig.update_traces(line=dict(color='red', width=3))
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error creating movement pattern analysis: {e}")

def display_anomaly_detection_results(dwell_df, movement_df):
    """
    Display anomaly detection results for asset tracking
    
    Parameters:
    - dwell_df: DataFrame with dwell time anomalies
    - movement_df: DataFrame with movement analysis
    """
    try:
        st.subheader(" Anomaly Detection Results")
        
        # Dwell time anomalies
        dwell_anomalies = dwell_df[dwell_df['dwell_anomaly'] == True]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Dwell Time Anomalies", len(dwell_anomalies))
        
        with col2:
            # Rapid movements (dwell time < 5 minutes)
            rapid_movements = len(dwell_df[dwell_df['dwell_time_seconds'] < 300])
            st.metric("Rapid Movements", rapid_movements)
        
        with col3:
            # Extended stationary (dwell time > 24 hours)
            extended_stationary = len(dwell_df[dwell_df['dwell_time_seconds'] > 86400])
            st.metric("Extended Stationary", extended_stationary)
        
        if len(dwell_anomalies) > 0:
            # Anomaly details
            st.subheader("Anomaly Details")
            
            anomaly_summary = dwell_anomalies.groupby('gateway_location').agg({
                'epc_number': 'count',
                'dwell_time_seconds': ['min', 'max', 'mean']
            }).round(2)
            
            # Flatten column names
            anomaly_summary.columns = ['anomaly_count', 'min_dwell', 'max_dwell', 'mean_dwell']
            st.dataframe(anomaly_summary, use_container_width=True)
            
            # Anomaly timeline
            fig = px.scatter(
                dwell_anomalies.head(50),
                x='timestamp',
                y='dwell_time_seconds',
                color='gateway_location',
                size='dwell_time_seconds',
                title='Dwell Time Anomalies Timeline',
                hover_data=['epc_number', 'gateway_location']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Movement anomalies
        if 'movement_rate' in movement_df.columns:
            movement_anomalies = movement_df[
                (movement_df['movement_rate'] > movement_df['movement_rate'].quantile(0.95)) |
                (movement_df['movement_rate'] < movement_df['movement_rate'].quantile(0.05))
            ]
            
            if len(movement_anomalies) > 0:
                st.subheader("Movement Rate Anomalies")
                st.dataframe(movement_anomalies[['epc_number', 'asset_type', 'movement_rate', 'locations_visited']].head(10), 
                           use_container_width=True)
                
    except Exception as e:
        st.error(f"Error displaying anomaly detection: {e}")

def create_asset_health_scoreboard(movement_df, dwell_df):
    """
    Create a health scoreboard for assets
    
    Parameters:
    - movement_df: Movement analysis DataFrame
    - dwell_df: Dwell time analysis DataFrame
    """
    try:
        st.subheader(" Asset Health Scoreboard")
        
        # Calculate health scores
        health_metrics = movement_df.copy()
        
        # Normalize metrics for scoring (0-100 scale)
        if 'movement_rate' in health_metrics.columns:
            health_metrics['movement_score'] = (
                (health_metrics['movement_rate'] - health_metrics['movement_rate'].min()) /
                (health_metrics['movement_rate'].max() - health_metrics['movement_rate'].min()) * 100
            )
        
        if 'locations_visited' in health_metrics.columns:
            health_metrics['coverage_score'] = (
                health_metrics['locations_visited'] / health_metrics['locations_visited'].max() * 100
            )
        
        # Calculate overall health score
        if 'movement_score' in health_metrics.columns and 'coverage_score' in health_metrics.columns:
            health_metrics['health_score'] = (
                health_metrics['movement_score'] * 0.6 + health_metrics['coverage_score'] * 0.4
            )
            
            # Categorize health status
            def categorize_health(score):
                if score >= 80:
                    return 'Excellent'
                elif score >= 60:
                    return 'Good'
                elif score >= 40:
                    return 'Fair'
                else:
                    return 'Poor'
            
            health_metrics['health_status'] = health_metrics['health_score'].apply(categorize_health)
            
            # Display health score distribution
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.histogram(
                    health_metrics,
                    x='health_score',
                    title='Asset Health Score Distribution',
                    nbins=20,
                    color_discrete_sequence=['green']
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                status_counts = health_metrics['health_status'].value_counts()
                fig = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title='Asset Health Status Distribution'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Top and bottom performers
            st.subheader("Asset Performance Ranking")
            
            top_performers = health_metrics.nlargest(5, 'health_score')[
                ['epc_number', 'asset_type', 'health_score', 'health_status']
            ]
            bottom_performers = health_metrics.nsmallest(5, 'health_score')[
                ['epc_number', 'asset_type', 'health_score', 'health_status']
            ]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(" Top Performers")
                st.dataframe(top_performers, use_container_width=True)
            
            with col2:
                st.write(" Needs Attention")
                st.dataframe(bottom_performers, use_container_width=True)
                
    except Exception as e:
        st.error(f"Error creating health scoreboard: {e}")

def export_asset_analytics(movement_df, dwell_df, gateway_performance):
    """
    Export asset analytics data for reporting
    
    Parameters:
    - movement_df: Movement analysis data
    - dwell_df: Dwell time data
    - gateway_performance: Gateway performance data
    """
    try:
        st.subheader(" Export Analytics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Export Movement Analysis"):
                movement_df.to_csv('asset_movement_analysis.csv', index=False)
                st.success("Movement analysis exported to CSV")
        
        with col2:
            if st.button("Export Dwell Time Data"):
                dwell_df.to_csv('asset_dwell_times.csv', index=False)
                st.success("Dwell time data exported to CSV")
        
        with col3:
            if st.button("Export Gateway Performance"):
                gateway_performance.to_csv('gateway_performance.csv', index=False)
                st.success("Gateway performance exported to CSV")
        
        # Summary report
        if st.button("Generate Summary Report"):
            report_data = {
                'total_assets': movement_df['epc_number'].nunique(),
                'total_movements': len(dwell_df),
                'avg_movement_rate': movement_df['movement_rate'].mean(),
                'anomaly_count': len(dwell_df[dwell_df['dwell_anomaly'] == True]),
                'report_generated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            import json
            with open('asset_tracking_report.json', 'w') as f:
                json.dump(report_data, f, indent=2)
            
            st.success("Summary report generated!")
            
    except Exception as e:
        st.error(f"Error exporting analytics: {e}")

# Utility function for the component
def format_duration(seconds):
    """Format duration in seconds to readable string"""
    if pd.isna(seconds):
        return "N/A"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{int(hours)}h {int(minutes)}m"
    elif minutes > 0:
        return f"{int(minutes)}m {int(secs)}s"
    else:
        return f"{int(secs)}s"