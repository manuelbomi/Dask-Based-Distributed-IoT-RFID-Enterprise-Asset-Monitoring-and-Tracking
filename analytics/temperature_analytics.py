import pandas as pd
import numpy as np
import dask.dataframe as dd
from dask.distributed import Client
import warnings
import streamlit as st
warnings.filterwarnings('ignore')

class TemperatureAnalytics:
    def __init__(self, data_path):
        self.data_path = data_path
        self.df_pandas = None
        self.df_dask = None
        
    def load_data_pandas(self):
        """Load and process data with Pandas"""
        try:
            self.df_pandas = pd.read_json(self.data_path, lines=True)
            
            # Check if timestamp column exists
            if 'timestamp' not in self.df_pandas.columns:
                st.error(f"Timestamp column not found in data. Available columns: {self.df_pandas.columns.tolist()}")
                # Return empty dataframe with expected structure
                return pd.DataFrame(columns=['timestamp', 'temperature', 'facility', 'epc', 'sensor_zone'])
                
            self.df_pandas['timestamp'] = pd.to_datetime(self.df_pandas['timestamp'])
            return self.df_pandas
        except Exception as e:
            st.error(f"Error loading temperature data: {e}")
            # Return empty dataframe with expected structure
            return pd.DataFrame(columns=['timestamp', 'temperature', 'facility', 'epc', 'sensor_zone'])
    
    def load_data_dask(self):
        """Load and process data with Dask"""
        try:
            self.df_dask = dd.read_json(self.data_path, lines=True)
            self.df_dask['timestamp'] = dd.to_datetime(self.df_dask['timestamp'])
            return self.df_dask
        except Exception as e:
            st.error(f"Error loading temperature data with Dask: {e}")
            return None
    
    def pandas_critical_breaches(self):
        """Analyze critical temperature breaches using Pandas"""
        if self.df_pandas is None or len(self.df_pandas) == 0:
            st.warning("No temperature data available for breach analysis")
            return pd.DataFrame()
            
        facility_critical_thresholds = {
            'cold_storage': (-25, -15),
            'refrigerated_transport': (2, 8),
            'room_temp_storage': (15, 25)
        }
        
        critical_breaches = []
        for facility in self.df_pandas['facility'].unique():
            facility_type = 'cold_storage' if 'cold' in facility else 'refrigerated_transport' if 'transport' in facility else 'room_temp_storage'
            min_temp, max_temp = facility_critical_thresholds[facility_type]
            
            facility_data = self.df_pandas[self.df_pandas['facility'] == facility]
            breaches = facility_data[
                (facility_data['temperature'] < min_temp) | 
                (facility_data['temperature'] > max_temp)
            ]
            
            if len(breaches) > 0:
                critical_breaches.append({
                    'Facility': facility,
                    'Facility_Type': facility_type,
                    'Breach_Count': len(breaches),
                    'Min_Temp_Found': breaches['temperature'].min(),
                    'Max_Temp_Found': breaches['temperature'].max(),
                    'Breach_Rate_Pct': (len(breaches) / len(facility_data)) * 100
                })
        
        return pd.DataFrame(critical_breaches)
    
    def pandas_rolling_statistics(self):
        """Calculate rolling statistics using Pandas"""
        if self.df_pandas is None or len(self.df_pandas) == 0:
            st.warning("No temperature data available for rolling statistics")
            return pd.DataFrame()
            
        try:
            df_temp = self.df_pandas.sort_values(['epc', 'timestamp']).copy()
            window_config = '6H'
            
            # Calculate rolling statistics
            df_temp['rolling_avg'] = (
                df_temp.groupby('epc')['temperature']
                .rolling(window=window_config, min_periods=1)
                .mean()
                .reset_index(level=0, drop=True)
            )
            
            df_temp['rolling_std'] = (
                df_temp.groupby('epc')['temperature']
                .rolling(window=window_config, min_periods=1)
                .std()
                .reset_index(level=0, drop=True)
            )
            
            df_temp['is_anomaly'] = (
                abs(df_temp['temperature'] - df_temp['rolling_avg']) > (2 * df_temp['rolling_std'])
            )
            
            df_temp['rolling_std'] = df_temp['rolling_std'].fillna(0)
            df_temp['is_anomaly'] = df_temp['is_anomaly'].fillna(False)
            
            return df_temp
        except Exception as e:
            st.error(f"Error calculating rolling statistics: {e}")
            return self.df_pandas
    
    def dask_compliance_metrics(self):
        """Calculate compliance metrics using Dask"""
        if self.df_dask is None:
            self.load_data_dask()
            
        if self.df_dask is None:
            st.warning("Dask data not available for compliance metrics")
            return pd.DataFrame()
            
        facility_thresholds = {
            'cold_storage': (-25, -15),
            'refrigerated_transport': (2, 8),
            'room_temp_storage': (15, 25)
        }
        
        def monitor_temperature_thresholds(partition):
            import pandas as pd
            
            def get_facility_type(facility_name):
                if 'cold' in facility_name.lower():
                    return 'cold_storage'
                elif 'transport' in facility_name.lower():
                    return 'refrigerated_transport'
                else:
                    return 'room_temp_storage'
            
            partition['facility_type'] = partition['facility'].apply(get_facility_type)
            
            def check_thresholds(row):
                min_temp, max_temp = facility_thresholds.get(row['facility_type'], (0, 30))
                return not (min_temp <= row['temperature'] <= max_temp)
            
            partition['threshold_breach'] = partition.apply(check_thresholds, axis=1)
            return partition
        
        try:
            df_monitored = self.df_dask.map_partitions(monitor_temperature_thresholds)
            df_monitored = df_monitored.set_index('timestamp')
            
            compliance_metrics = (
                df_monitored.groupby(['facility_type', 'epc'])
                .rolling('24H')
                .agg({
                    'threshold_breach': 'mean',
                    'temperature': ['mean', 'std', 'min', 'max']
                })
            )
            
            compliance_results = compliance_metrics.compute()
            compliance_results.columns = ['breach_rate', 'mean_temp', 'std_temp', 'min_temp', 'max_temp']
            compliance_results = compliance_results.reset_index()
            
            compliance_results['compliance_status'] = compliance_results['breach_rate'].apply(
                lambda x: 'COMPLIANT' if x < 0.05 else 'WARNING' if x < 0.1 else 'CRITICAL'
            )
            
            return compliance_results
        except Exception as e:
            st.error(f"Error calculating Dask compliance metrics: {e}")
            return pd.DataFrame()
    
    def get_summary_stats(self):
        """Get overall summary statistics"""
        if self.df_pandas is None or len(self.df_pandas) == 0:
            return {
                'total_records': 0,
                'unique_sensors': 0,
                'unique_facilities': 0,
                'date_range_start': None,
                'date_range_end': None,
                'avg_temperature': 0,
                'temperature_std': 0
            }
            
        summary = {
            'total_records': len(self.df_pandas),
            'unique_sensors': self.df_pandas['epc'].nunique(),
            'unique_facilities': self.df_pandas['facility'].nunique(),
            'date_range_start': self.df_pandas['timestamp'].min(),
            'date_range_end': self.df_pandas['timestamp'].max(),
            'avg_temperature': self.df_pandas['temperature'].mean(),
            'temperature_std': self.df_pandas['temperature'].std()
        }
        
        return summary