"""
Utility functions for IoT analytics modules
Common helper functions used across temperature and RFID analytics
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_timedelta(td):
    """Format timedelta to readable string"""
    if pd.isna(td):
        return "N/A"
    
    if isinstance(td, (int, float)):
        td = timedelta(seconds=td)
    
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def calculate_rolling_statistics(df, column, group_col, window='1H', min_periods=1):
    """
    Calculate rolling statistics for a column grouped by another column
    
    Parameters:
    - df: DataFrame
    - column: Column to calculate rolling stats for
    - group_col: Column to group by
    - window: Rolling window size
    - min_periods: Minimum periods required
    
    Returns:
    - DataFrame with rolling statistics
    """
    try:
        df_sorted = df.sort_values([group_col, 'timestamp'])
        
        # Calculate rolling statistics
        rolling_stats = df_sorted.groupby(group_col)[column].rolling(
            window=window, min_periods=min_periods
        ).agg(['mean', 'std', 'min', 'max']).reset_index()
        
        # Rename columns
        rolling_stats.columns = [group_col, 'level_1', 
                               f'{column}_rolling_avg', f'{column}_rolling_std',
                               f'{column}_rolling_min', f'{column}_rolling_max']
        
        # Merge back with original dataframe
        result = df_sorted.reset_index().merge(
            rolling_stats.drop(columns=['level_1']), 
            on=[group_col, 'index'], how='left'
        ).set_index('index')
        
        return result
        
    except Exception as e:
        logger.error(f"Error calculating rolling statistics: {e}")
        return df

def detect_anomalies_zscore(df, value_col, group_col=None, threshold=2):
    """
    Detect anomalies using Z-score method
    
    Parameters:
    - df: DataFrame
    - value_col: Column to check for anomalies
    - group_col: Optional column to group by
    - threshold: Z-score threshold for anomalies
    
    Returns:
    - DataFrame with anomaly flags
    """
    df_result = df.copy()
    
    try:
        if group_col:
            # Calculate mean and std per group
            stats = df_result.groupby(group_col)[value_col].agg(['mean', 'std']).reset_index()
            df_result = df_result.merge(stats, on=group_col, how='left')
            
            # Calculate Z-score
            df_result['z_score'] = (df_result[value_col] - df_result['mean']) / df_result['std']
        else:
            # Global statistics
            mean_val = df_result[value_col].mean()
            std_val = df_result[value_col].std()
            df_result['z_score'] = (df_result[value_col] - mean_val) / std_val
        
        # Flag anomalies
        df_result['is_anomaly'] = abs(df_result['z_score']) > threshold
        df_result['anomaly_score'] = abs(df_result['z_score'])
        
        # Clean up temporary columns
        if group_col:
            df_result = df_result.drop(columns=['mean', 'std'])
            
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        df_result['is_anomaly'] = False
        df_result['anomaly_score'] = 0
    
    return df_result

def calculate_dwell_times(df, asset_col, location_col, timestamp_col):
    """
    Calculate dwell times for assets at locations
    
    Parameters:
    - df: DataFrame with asset movement data
    - asset_col: Column containing asset identifiers
    - location_col: Column containing location information
    - timestamp_col: Column containing timestamps
    
    Returns:
    - DataFrame with dwell time calculations
    """
    try:
        df_sorted = df.sort_values([asset_col, timestamp_col]).copy()
        
        # Calculate time spent at each location
        df_sorted['next_timestamp'] = df_sorted.groupby(asset_col)[timestamp_col].shift(-1)
        df_sorted['dwell_time_seconds'] = (
            df_sorted['next_timestamp'] - df_sorted[timestamp_col]
        ).dt.total_seconds()
        
        # Remove last event for each asset (no next timestamp)
        df_sorted = df_sorted.dropna(subset=['dwell_time_seconds'])
        
        return df_sorted
        
    except Exception as e:
        logger.error(f"Error calculating dwell times: {e}")
        return df

def resample_time_series(df, value_col, freq='1H', agg_func='mean'):
    """
    Resample time series data to specified frequency
    
    Parameters:
    - df: DataFrame with datetime index
    - value_col: Column to resample
    - freq: Resampling frequency
    - agg_func: Aggregation function
    
    Returns:
    - Resampled DataFrame
    """
    try:
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame index must be datetime")
        
        resampled = df[value_col].resample(freq).agg(agg_func)
        return resampled.reset_index()
        
    except Exception as e:
        logger.error(f"Error resampling time series: {e}")
        return df

def calculate_movement_metrics(df, asset_col, location_col, timestamp_col):
    """
    Calculate comprehensive movement metrics for assets
    
    Parameters:
    - df: DataFrame with asset movement data
    - asset_col: Asset identifier column
    - location_col: Location column
    - timestamp_col: Timestamp column
    
    Returns:
    - DataFrame with movement metrics per asset
    """
    try:
        df_sorted = df.sort_values([asset_col, timestamp_col])
        
        movement_metrics = df_sorted.groupby(asset_col).agg({
            location_col: [
                'count',  # Total readings
                'nunique',  # Unique locations visited
                lambda x: x.iloc[0],  # First location
                lambda x: x.iloc[-1],  # Last location
                lambda x: (x != x.shift()).sum() - 1  # Number of moves
            ],
            timestamp_col: [
                'min',  # First seen
                'max',  # Last seen
                lambda x: (x.max() - x.min()).total_seconds() / 3600  # Tracking duration hours
            ]
        }).round(3)
        
        # Flatten column names
        movement_metrics.columns = [
            'total_readings', 'unique_locations', 'first_location', 
            'last_location', 'movement_count', 'first_seen', 'last_seen', 
            'tracking_duration_hrs'
        ]
        
        # Calculate derived metrics
        movement_metrics['movement_rate'] = (
            movement_metrics['movement_count'] / movement_metrics['tracking_duration_hrs']
        ).round(3)
        
        movement_metrics['reads_per_hour'] = (
            movement_metrics['total_readings'] / movement_metrics['tracking_duration_hrs']
        ).round(2)
        
        movement_metrics['has_moved'] = movement_metrics['movement_count'] > 0
        
        return movement_metrics.reset_index()
        
    except Exception as e:
        logger.error(f"Error calculating movement metrics: {e}")
        return pd.DataFrame()

def normalize_data(df, columns, method='minmax'):
    """
    Normalize data columns using specified method
    
    Parameters:
    - df: DataFrame
    - columns: List of columns to normalize
    - method: Normalization method ('minmax', 'zscore')
    
    Returns:
    - DataFrame with normalized columns
    """
    df_result = df.copy()
    
    try:
        for col in columns:
            if col not in df_result.columns:
                continue
                
            if method == 'minmax':
                min_val = df_result[col].min()
                max_val = df_result[col].max()
                if max_val > min_val:  # Avoid division by zero
                    df_result[f'{col}_normalized'] = (df_result[col] - min_val) / (max_val - min_val)
                    
            elif method == 'zscore':
                mean_val = df_result[col].mean()
                std_val = df_result[col].std()
                if std_val > 0:  # Avoid division by zero
                    df_result[f'{col}_normalized'] = (df_result[col] - mean_val) / std_val
                    
    except Exception as e:
        logger.error(f"Error normalizing data: {e}")
    
    return df_result

def calculate_percentile_ranks(df, value_col, group_col=None):
    """
    Calculate percentile ranks for values
    
    Parameters:
    - df: DataFrame
    - value_col: Column to calculate percentiles for
    - group_col: Optional grouping column
    
    Returns:
    - DataFrame with percentile ranks
    """
    df_result = df.copy()
    
    try:
        if group_col:
            df_result['percentile_rank'] = df_result.groupby(group_col)[value_col].rank(
                pct=True, method='average'
            )
        else:
            df_result['percentile_rank'] = df_result[value_col].rank(
                pct=True, method='average'
            )
            
    except Exception as e:
        logger.error(f"Error calculating percentile ranks: {e}")
        df_result['percentile_rank'] = 0.5
    
    return df_result

def create_time_based_features(df, timestamp_col):
    """
    Create time-based features from timestamp column
    
    Parameters:
    - df: DataFrame
    - timestamp_col: Timestamp column name
    
    Returns:
    - DataFrame with time-based features
    """
    df_result = df.copy()
    
    try:
        if timestamp_col in df_result.columns:
            df_result[timestamp_col] = pd.to_datetime(df_result[timestamp_col])
            
            # Extract time features
            df_result['hour'] = df_result[timestamp_col].dt.hour
            df_result['day_of_week'] = df_result[timestamp_col].dt.dayofweek
            df_result['day_of_month'] = df_result[timestamp_col].dt.day
            df_result['month'] = df_result[timestamp_col].dt.month
            df_result['is_weekend'] = df_result[timestamp_col].dt.dayofweek.isin([5, 6])
            df_result['time_of_day'] = pd.cut(
                df_result['hour'], 
                bins=[0, 6, 12, 18, 24], 
                labels=['Night', 'Morning', 'Afternoon', 'Evening'],
                include_lowest=True
            )
            
    except Exception as e:
        logger.error(f"Error creating time-based features: {e}")
    
    return df_result

def validate_dataframe(df, required_columns=None):
    """
    Validate DataFrame structure and required columns
    
    Parameters:
    - df: DataFrame to validate
    - required_columns: List of required column names
    
    Returns:
    - Tuple (is_valid, error_message)
    """
    if df is None:
        return False, "DataFrame is None"
    
    if df.empty:
        return False, "DataFrame is empty"
    
    if required_columns:
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Missing required columns: {missing_columns}"
    
    return True, "DataFrame is valid"

def save_analysis_results(results, filename, format='csv'):
    """
    Save analysis results to file
    
    Parameters:
    - results: Analysis results (DataFrame or dict)
    - filename: Output filename
    - format: Output format ('csv', 'json', 'parquet')
    """
    try:
        if isinstance(results, pd.DataFrame):
            if format == 'csv':
                results.to_csv(filename, index=False)
            elif format == 'json':
                results.to_json(filename, orient='records', indent=2)
            elif format == 'parquet':
                results.to_parquet(filename, index=False)
        elif isinstance(results, dict):
            import json
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
                
        logger.info(f"Results saved to {filename}")
        
    except Exception as e:
        logger.error(f"Error saving results: {e}")

def load_analysis_results(filename, format='csv'):
    """
    Load analysis results from file
    
    Parameters:
    - filename: Input filename
    - format: Input format ('csv', 'json', 'parquet')
    
    Returns:
    - Loaded data
    """
    try:
        if format == 'csv':
            return pd.read_csv(filename)
        elif format == 'json':
            return pd.read_json(filename)
        elif format == 'parquet':
            return pd.read_parquet(filename)
        else:
            raise ValueError(f"Unsupported format: {format}")
            
    except Exception as e:
        logger.error(f"Error loading results: {e}")
        return None

# Example usage and testing
if __name__ == "__main__":
    # Test the utility functions
    print("Testing utility functions...")
    
    # Create sample data for testing
    sample_data = pd.DataFrame({
        'asset_id': ['A1', 'A1', 'A2', 'A2', 'A1'],
        'temperature': [20.5, 21.0, 19.8, 22.5, 18.9],
        'timestamp': pd.date_range('2024-01-01', periods=5, freq='H')
    })
    
    print("Original data:")
    print(sample_data)
    
    print("\nWith rolling statistics:")
    rolling_data = calculate_rolling_statistics(sample_data, 'temperature', 'asset_id', window='2H')
    print(rolling_data[['asset_id', 'timestamp', 'temperature', 'temperature_rolling_avg']])
    
    print("\nWith anomaly detection:")
    anomaly_data = detect_anomalies_zscore(sample_data, 'temperature', 'asset_id')
    print(anomaly_data[['asset_id', 'temperature', 'is_anomaly', 'anomaly_score']])
    
    print("\nWith time-based features:")
    time_data = create_time_based_features(sample_data, 'timestamp')
    print(time_data[['timestamp', 'hour', 'day_of_week', 'time_of_day']])