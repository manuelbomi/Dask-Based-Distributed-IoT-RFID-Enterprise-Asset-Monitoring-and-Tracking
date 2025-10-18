import pandas as pd
import numpy as np
import dask.dataframe as dd
from dask.distributed import Client
import warnings
import streamlit as st
warnings.filterwarnings('ignore')

class RFIDAnalytics:
    def __init__(self, data_path):
        self.data_path = data_path
        self.df_pandas = None
        self.df_dask = None
        
    def load_data_pandas(self):
        """Load and process RFID data with Pandas"""
        try:
            self.df_pandas = pd.read_json(self.data_path, lines=True)
            
            # Check if tagInventoryEvent column exists
            if 'tagInventoryEvent' not in self.df_pandas.columns:
                st.warning(f"tagInventoryEvent column not found. Available columns: {self.df_pandas.columns.tolist()}")
                # Try to load as already flattened data
                if 'epc_number' in self.df_pandas.columns and 'timestamp' in self.df_pandas.columns:
                    self.df_pandas['timestamp'] = pd.to_datetime(self.df_pandas['timestamp'])
                    st.success("Loaded as flattened RFID data")
                    return self.df_pandas
                else:
                    st.error("Required columns (epc_number, timestamp) not found in RFID data")
                    return pd.DataFrame()
            
            # Flatten the nested JSON structure
            df_flat = pd.json_normalize(self.df_pandas['tagInventoryEvent'])
            df_flat['timestamp'] = pd.to_datetime(self.df_pandas['timestamp'])
            self.df_pandas = df_flat
            return self.df_pandas
        except Exception as e:
            st.error(f"Error loading RFID data: {e}")
            # Return empty dataframe with expected structure
            return pd.DataFrame(columns=['timestamp', 'epc_number', 'gateway_location', 'asset_type'])
    
    def load_data_dask(self):
        """Load and process RFID data with Dask"""
        try:
            self.df_dask = dd.read_json(self.data_path, lines=True)
            
            def flatten_rfid_partition(partition):
                import pandas as pd
                try:
                    flattened = pd.json_normalize(partition['tagInventoryEvent'])
                    flattened['timestamp'] = pd.to_datetime(partition['timestamp'].values)
                    return flattened
                except Exception as e:
                    st.error(f"Error flattening RFID partition: {e}")
                    return pd.DataFrame()
            
            self.df_dask = self.df_dask.map_partitions(flatten_rfid_partition)
            return self.df_dask
        except Exception as e:
            st.error(f"Error loading RFID data with Dask: {e}")
            return None
    
    def pandas_movement_analysis(self):
        """Analyze asset movement patterns using Pandas"""
        if self.df_pandas is None or len(self.df_pandas) == 0:
            st.warning("No RFID data available for movement analysis")
            return pd.DataFrame()
            
        try:
            movement_analysis = (
                self.df_pandas.sort_values(['epc_number', 'timestamp'])
                .groupby('epc_number')
                .agg({
                    'gateway_location': ['first', 'last', 'nunique', lambda x: x.iloc[-1] != x.iloc[0]],
                    'timestamp': ['min', 'max', lambda x: (x.max() - x.min()).total_seconds() / 3600],
                    'asset_type': 'first',
                    'gateway_ant_rssi': 'mean'
                })
            ).round(2)
            
            movement_analysis.columns = [
                'first_location', 'last_location', 'locations_visited', 'has_moved',
                'first_seen', 'last_seen', 'tracking_duration_hrs', 'asset_type', 'avg_rssi'
            ]
            
            movement_analysis['movement_rate'] = (
                movement_analysis['locations_visited'] / movement_analysis['tracking_duration_hrs']
            ).round(3)
            
            return movement_analysis
        except Exception as e:
            st.error(f"Error in movement analysis: {e}")
            return pd.DataFrame()
    
    def pandas_dwell_time_analysis(self):
        """Calculate dwell times and rolling statistics using Pandas"""
        if self.df_pandas is None or len(self.df_pandas) == 0:
            st.warning("No RFID data available for dwell time analysis")
            return pd.DataFrame()
            
        try:
            df_sorted = self.df_pandas.sort_values(['epc_number', 'timestamp']).copy()
            
            # Calculate time spent at each location
            df_sorted['next_timestamp'] = df_sorted.groupby('epc_number')['timestamp'].shift(-1)
            df_sorted['dwell_time_seconds'] = (
                (df_sorted['next_timestamp'] - df_sorted['timestamp']).dt.total_seconds()
            )
            
            df_sorted = df_sorted.dropna(subset=['dwell_time_seconds'])
            
            if len(df_sorted) == 0:
                st.warning("No valid dwell time data after processing")
                return pd.DataFrame()
            
            # Rolling average dwell time
            window_size = 10
            df_sorted['rolling_avg_dwell'] = (
                df_sorted.groupby('epc_number')['dwell_time_seconds']
                .rolling(window=window_size, min_periods=1)
                .mean()
                .reset_index(level=0, drop=True)
            )
            
            df_sorted['rolling_std_dwell'] = (
                df_sorted.groupby('epc_number')['dwell_time_seconds']
                .rolling(window=window_size, min_periods=1)
                .std()
                .reset_index(level=0, drop=True)
            )
            
            df_sorted['dwell_anomaly'] = (
                abs(df_sorted['dwell_time_seconds'] - df_sorted['rolling_avg_dwell']) > 
                (2 * df_sorted['rolling_std_dwell'])
            )
            
            return df_sorted
        except Exception as e:
            st.error(f"Error in dwell time analysis: {e}")
            return pd.DataFrame()
    
    def dask_movement_patterns(self):
        """Analyze movement patterns using Dask"""
        if self.df_dask is None:
            self.load_data_dask()
            
        if self.df_dask is None:
            st.warning("Dask data not available for movement patterns")
            return pd.DataFrame()
            
        try:
            self.df_dask = self.df_dask.set_index('timestamp')
            
            movement_patterns = (
                self.df_dask.groupby('epc_number')
                .agg({
                    'gateway_location': ['count', 'nunique'],
                    'gateway_ant_rssi': 'mean',
                    'asset_type': 'first'
                })
            )
            
            movement_results = movement_patterns.compute()
            movement_results.columns = ['total_reads', 'locations_visited', 'avg_rssi', 'asset_type']
            
            movement_results['movement_complexity'] = (
                movement_results['locations_visited'] / movement_results['total_reads']
            ).round(3)
            
            return movement_results
        except Exception as e:
            st.error(f"Error in Dask movement patterns: {e}")
            return pd.DataFrame()
    
    def get_summary_stats(self):
        """Get overall summary statistics"""
        if self.df_pandas is None or len(self.df_pandas) == 0:
            return {
                'total_events': 0,
                'unique_assets': 0,
                'unique_locations': 0,
                'date_range_start': None,
                'date_range_end': None,
                'asset_types': {},
                'avg_signal_strength': 0
            }
            
        summary = {
            'total_events': len(self.df_pandas),
            'unique_assets': self.df_pandas['epc_number'].nunique(),
            'unique_locations': self.df_pandas['gateway_location'].nunique(),
            'date_range_start': self.df_pandas['timestamp'].min(),
            'date_range_end': self.df_pandas['timestamp'].max(),
            'asset_types': self.df_pandas['asset_type'].value_counts().to_dict(),
            'avg_signal_strength': self.df_pandas['gateway_ant_rssi'].mean() if 'gateway_ant_rssi' in self.df_pandas.columns else 0
        }
        
        return summary