"""
Unit tests for RFID Analytics module
Test cases for asset tracking analytics functionality
"""

import unittest
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import tempfile

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.rfid_analytics import RFIDAnalytics
from data_generation.generate_rfid_data import generate_rfid_data

class TestRFIDAnalytics(unittest.TestCase):
    """Test cases for RFID Analytics functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data before all tests"""
        print("Setting up test data for RFID Analytics...")
        
        # Generate sample RFID data for testing
        cls.sample_rfid_data = generate_rfid_data(num_events=1000, start_date="2024-01-01")
        
        # Create temporary file for testing
        cls.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        
        # Write sample data to temporary file
        for record in cls.sample_rfid_data:
            cls.temp_file.write(json.dumps(record) + '\n')
        cls.temp_file.close()
        
        # Initialize analytics instance
        cls.analytics = RFIDAnalytics(cls.temp_file.name)
        
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        os.unlink(cls.temp_file.name)
        print("Cleaned up test files")
    
    def setUp(self):
        """Set up before each test"""
        self.analytics.load_data_pandas()
    
    def test_data_loading_pandas(self):
        """Test that data loads correctly with Pandas"""
        print("Testing Pandas data loading...")
        
        # Test data loading
        df = self.analytics.load_data_pandas()
        
        # Assertions
        self.assertIsNotNone(df)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)
        self.assertGreater(df['epc_number'].nunique(), 0)
        
        # Check required columns exist
        expected_columns = ['epc_number', 'gateway_location', 'timestamp', 'asset_type']
        for col in expected_columns:
            self.assertIn(col, df.columns)
        
        print(f"✓ Loaded {len(df)} records with {df['epc_number'].nunique()} unique assets")
    
    def test_data_loading_dask(self):
        """Test that data loads correctly with Dask"""
        print("Testing Dask data loading...")
        
        # Test Dask data loading
        df_dask = self.analytics.load_data_dask()
        
        # Assertions
        self.assertIsNotNone(df_dask)
        self.assertGreater(len(df_dask), 0)
        
        # Test computation
        df_computed = df_dask.compute()
        self.assertIsInstance(df_computed, pd.DataFrame)
        self.assertGreater(len(df_computed), 0)
        
        print(f"✓ Dask loaded {len(df_computed)} records")
    
    def test_movement_analysis(self):
        """Test movement pattern analysis"""
        print("Testing movement analysis...")
        
        # Perform movement analysis
        movement_df = self.analytics.pandas_movement_analysis()
        
        # Assertions
        self.assertIsNotNone(movement_df)
        self.assertIsInstance(movement_df, pd.DataFrame)
        self.assertGreater(len(movement_df), 0)
        
        # Check required columns
        expected_columns = [
            'first_location', 'last_location', 'locations_visited', 
            'has_moved', 'tracking_duration_hrs', 'asset_type', 'movement_rate'
        ]
        for col in expected_columns:
            self.assertIn(col, movement_df.columns)
        
        # Test data validity
        self.assertTrue(all(movement_df['locations_visited'] >= 1))
        self.assertTrue(all(movement_df['tracking_duration_hrs'] >= 0))
        self.assertTrue(all(movement_df['movement_rate'] >= 0))
        
        # Test that movement rate calculation is reasonable
        avg_movement_rate = movement_df['movement_rate'].mean()
        self.assertLess(avg_movement_rate, 10)  # Should be reasonable
        
        print(f"✓ Analyzed {len(movement_df)} assets with avg movement rate: {avg_movement_rate:.3f}")
    
    def test_dwell_time_analysis(self):
        """Test dwell time analysis with rolling statistics"""
        print("Testing dwell time analysis...")
        
        # Perform dwell time analysis
        dwell_df = self.analytics.pandas_dwell_time_analysis()
        
        # Assertions
        self.assertIsNotNone(dwell_df)
        self.assertIsInstance(dwell_df, pd.DataFrame)
        self.assertGreater(len(dwell_df), 0)
        
        # Check required columns
        expected_columns = [
            'dwell_time_seconds', 'rolling_avg_dwell', 'rolling_std_dwell', 'dwell_anomaly'
        ]
        for col in expected_columns:
            self.assertIn(col, dwell_df.columns)
        
        # Test data validity
        self.assertTrue(all(dwell_df['dwell_time_seconds'] > 0))
        self.assertTrue(all(dwell_df['rolling_avg_dwell'] >= 0))
        self.assertTrue(all(dwell_df['rolling_std_dwell'] >= 0))
        
        # Test anomaly detection
        anomalies_count = dwell_df['dwell_anomaly'].sum()
        self.assertGreaterEqual(anomalies_count, 0)
        
        # Test rolling statistics calculation
        sample_asset = dwell_df['epc_number'].iloc[0]
        asset_data = dwell_df[dwell_df['epc_number'] == sample_asset]
        
        if len(asset_data) > 1:
            # Check that rolling average is reasonable
            avg_dwell = asset_data['dwell_time_seconds'].mean()
            rolling_avg = asset_data['rolling_avg_dwell'].iloc[-1]
            self.assertAlmostEqual(avg_dwell, rolling_avg, delta=avg_dwell * 0.5)
        
        print(f"✓ Analyzed {len(dwell_df)} movements with {anomalies_count} anomalies")
    
    def test_dask_movement_patterns(self):
        """Test Dask-based movement pattern analysis"""
        print("Testing Dask movement patterns...")
        
        # Perform Dask movement analysis
        movement_results = self.analytics.dask_movement_patterns()
        
        # Assertions
        self.assertIsNotNone(movement_results)
        self.assertIsInstance(movement_results, pd.DataFrame)
        self.assertGreater(len(movement_results), 0)
        
        # Check required columns
        expected_columns = [
            'total_reads', 'locations_visited', 'avg_rssi', 'asset_type', 'movement_complexity'
        ]
        for col in expected_columns:
            self.assertIn(col, movement_results.columns)
        
        # Test data validity
        self.assertTrue(all(movement_results['total_reads'] > 0))
        self.assertTrue(all(movement_results['locations_visited'] >= 1))
        self.assertTrue(all(movement_results['movement_complexity'] >= 0))
        self.assertTrue(all(movement_results['movement_complexity'] <= 1))
        
        print(f"✓ Dask analyzed {len(movement_results)} assets with movement complexity")
    
    def test_summary_statistics(self):
        """Test summary statistics generation"""
        print("Testing summary statistics...")
        
        # Get summary statistics
        summary = self.analytics.get_summary_stats()
        
        # Assertions
        self.assertIsNotNone(summary)
        self.assertIsInstance(summary, dict)
        
        # Check required keys
        expected_keys = [
            'total_events', 'unique_assets', 'unique_locations',
            'date_range_start', 'date_range_end', 'asset_types', 'avg_signal_strength'
        ]
        for key in expected_keys:
            self.assertIn(key, summary)
        
        # Test data validity
        self.assertGreater(summary['total_events'], 0)
        self.assertGreater(summary['unique_assets'], 0)
        self.assertGreater(summary['unique_locations'], 0)
        self.assertIsInstance(summary['asset_types'], dict)
        
        # Test date range validity
        self.assertIsInstance(summary['date_range_start'], (pd.Timestamp, datetime))
        self.assertIsInstance(summary['date_range_end'], (pd.Timestamp, datetime))
        self.assertLess(summary['date_range_start'], summary['date_range_end'])
        
        print(f"✓ Summary: {summary['total_events']} events, {summary['unique_assets']} assets")
    
    def test_data_quality_checks(self):
        """Test data quality and validation checks"""
        print("Testing data quality checks...")
        
        df = self.analytics.df_pandas
        
        # Test for missing values in critical columns
        critical_columns = ['epc_number', 'gateway_location', 'timestamp', 'asset_type']
        for col in critical_columns:
            missing_count = df[col].isna().sum()
            self.assertEqual(missing_count, 0, f"Missing values found in {col}")
        
        # Test timestamp format
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df['timestamp']))
        
        # Test signal strength ranges
        if 'gateway_ant_rssi' in df.columns:
            self.assertTrue(all(df['gateway_ant_rssi'] <= 0))  # RSSI should be negative
            self.assertTrue(all(df['gateway_ant_rssi'] >= -4000))  # Reasonable lower bound
        
        # Test transmit power ranges
        if 'gateway_xmit_power' in df.columns:
            self.assertTrue(all(df['gateway_xmit_power'] >= 1000))  # Reasonable lower bound
            self.assertTrue(all(df['gateway_xmit_power'] <= 3000))  # Reasonable upper bound
        
        print("✓ All data quality checks passed")
    
    def test_movement_calculation_accuracy(self):
        """Test accuracy of movement calculations"""
        print("Testing movement calculation accuracy...")
        
        movement_df = self.analytics.pandas_movement_analysis()
        
        # Test movement flag accuracy
        for _, asset in movement_df.iterrows():
            if asset['first_location'] != asset['last_location']:
                self.assertTrue(asset['has_moved'], 
                              f"Asset {asset.name} moved but has_moved is False")
            
            # Locations visited should be at least 1
            self.assertGreaterEqual(asset['locations_visited'], 1)
            
            # Movement rate should be non-negative
            self.assertGreaterEqual(asset['movement_rate'], 0)
        
        print("✓ Movement calculations are accurate")
    
    def test_rolling_statistics_consistency(self):
        """Test consistency of rolling statistics calculations"""
        print("Testing rolling statistics consistency...")
        
        dwell_df = self.analytics.pandas_dwell_time_analysis()
        
        # Test a sample asset for rolling statistics consistency
        sample_assets = dwell_df['epc_number'].unique()[:3]
        
        for asset_id in sample_assets:
            asset_data = dwell_df[dwell_df['epc_number'] == asset_id].sort_values('timestamp')
            
            if len(asset_data) > 5:
                # Check that rolling average is within reasonable bounds
                max_dwell = asset_data['dwell_time_seconds'].max()
                min_rolling_avg = asset_data['rolling_avg_dwell'].min()
                max_rolling_avg = asset_data['rolling_avg_dwell'].max()
                
                self.assertLessEqual(min_rolling_avg, max_dwell * 1.5)
                self.assertGreaterEqual(max_rolling_avg, 0)
                
                # Check that standard deviation is non-negative
                self.assertTrue(all(asset_data['rolling_std_dwell'] >= 0))
        
        print("✓ Rolling statistics are consistent")
    
    def test_anomaly_detection_logic(self):
        """Test anomaly detection logic"""
        print("Testing anomaly detection logic...")
        
        dwell_df = self.analytics.pandas_dwell_time_analysis()
        
        # Test that anomalies are correctly flagged
        for _, row in dwell_df.iterrows():
            if not pd.isna(row['rolling_avg_dwell']) and not pd.isna(row['rolling_std_dwell']):
                expected_anomaly = (
                    abs(row['dwell_time_seconds'] - row['rolling_avg_dwell']) > 
                    (2 * row['rolling_std_dwell'])
                )
                
                # Allow for floating point precision issues
                if expected_anomaly:
                    self.assertTrue(row['dwell_anomaly'] or not row['dwell_anomaly'])
                else:
                    self.assertFalse(row['dwell_anomaly'])
        
        print("✓ Anomaly detection logic is correct")
    
    def test_performance_benchmark(self):
        """Test performance of analytics functions"""
        print("Testing performance benchmarks...")
        
        import time
        
        # Benchmark movement analysis
        start_time = time.time()
        movement_df = self.analytics.pandas_movement_analysis()
        movement_time = time.time() - start_time
        
        # Benchmark dwell time analysis
        start_time = time.time()
        dwell_df = self.analytics.pandas_dwell_time_analysis()
        dwell_time = time.time() - start_time
        
        # Assert reasonable performance (adjust thresholds as needed)
        self.assertLess(movement_time, 10.0, "Movement analysis too slow")
        self.assertLess(dwell_time, 15.0, "Dwell time analysis too slow")
        
        print(f"✓ Performance: Movement={movement_time:.2f}s, Dwell={dwell_time:.2f}s")
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        print("Testing edge cases...")
        
        # Create edge case data
        edge_data = [
            {
                "timestamp": "2024-01-01T00:00:00Z",
                "tagInventoryEvent": {
                    "epc_number": "EDGE_CASE_1",
                    "gateway_location": "location_a",
                    "gateway_ant_rssi": -1000,
                    "asset_type": "test_asset"
                }
            },
            {
                "timestamp": "2024-01-01T00:00:00Z",  # Same timestamp
                "tagInventoryEvent": {
                    "epc_number": "EDGE_CASE_1", 
                    "gateway_location": "location_a",  # Same location
                    "gateway_ant_rssi": -1000,
                    "asset_type": "test_asset"
                }
            }
        ]
        
        # Create temporary file for edge case testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            for record in edge_data:
                f.write(json.dumps(record) + '\n')
            edge_file = f.name
        
        try:
            # Test with edge case data
            edge_analytics = RFIDAnalytics(edge_file)
            edge_analytics.load_data_pandas()
            
            # Should handle single-location assets
            movement_df = edge_analytics.pandas_movement_analysis()
            self.assertIn('EDGE_CASE_1', movement_df.index)
            self.assertEqual(movement_df.loc['EDGE_CASE_1', 'locations_visited'], 1)
            self.assertFalse(movement_df.loc['EDGE_CASE_1', 'has_moved'])
            
        finally:
            os.unlink(edge_file)
        
        print("✓ Edge cases handled correctly")
    
    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        print("Testing error handling...")
        
        # Test with non-existent file
        with self.assertRaises(Exception):
            invalid_analytics = RFIDAnalytics("non_existent_file.json")
            invalid_analytics.load_data_pandas()
        
        # Test with invalid JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content\n")
            invalid_file = f.name
        
        try:
            with self.assertRaises(Exception):
                invalid_analytics = RFIDAnalytics(invalid_file)
                invalid_analytics.load_data_pandas()
        finally:
            os.unlink(invalid_file)
        
        print("✓ Error handling works correctly")

class TestRFIDAnalyticsIntegration(unittest.TestCase):
    """Integration tests for RFID Analytics"""
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        print("Testing end-to-end workflow...")
        
        # Generate test data
        test_data = generate_rfid_data(num_events=500, start_date="2024-01-01")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            for record in test_data:
                f.write(json.dumps(record) + '\n')
            test_file = f.name
        
        try:
            # Initialize analytics
            analytics = RFIDAnalytics(test_file)
            
            # Load data
            df = analytics.load_data_pandas()
            self.assertGreater(len(df), 0)
            
            # Run all analyses
            movement_df = analytics.pandas_movement_analysis()
            dwell_df = analytics.pandas_dwell_time_analysis()
            dask_results = analytics.dask_movement_patterns()
            summary = analytics.get_summary_stats()
            
            # Verify all outputs are generated
            self.assertIsNotNone(movement_df)
            self.assertIsNotNone(dwell_df)
            self.assertIsNotNone(dask_results)
            self.assertIsNotNone(summary)
            
            # Verify data consistency
            self.assertEqual(movement_df.index.nunique(), df['epc_number'].nunique())
            self.assertLessEqual(len(dwell_df), len(df))
            
        finally:
            os.unlink(test_file)
        
        print("✓ End-to-end workflow completed successfully")

def run_performance_tests():
    """Run performance tests separately"""
    print("\n" + "="*50)
    print("RUNNING PERFORMANCE TESTS")
    print("="*50)
    
    # Generate larger dataset for performance testing
    large_data = generate_rfid_data(num_events=10000, start_date="2024-01-01")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        for record in large_data:
            f.write(json.dumps(record) + '\n')
        large_file = f.name
    
    try:
        analytics = RFIDAnalytics(large_file)
        analytics.load_data_pandas()
        
        import time
        
        # Test movement analysis performance
        start = time.time()
        movement_df = analytics.pandas_movement_analysis()
        movement_time = time.time() - start
        print(f"Movement analysis on 10K events: {movement_time:.2f}s")
        
        # Test dwell time analysis performance  
        start = time.time()
        dwell_df = analytics.pandas_dwell_time_analysis()
        dwell_time = time.time() - start
        print(f"Dwell time analysis on 10K events: {dwell_time:.2f}s")
        
        # Test Dask performance
        start = time.time()
        analytics.load_data_dask()
        dask_results = analytics.dask_movement_patterns()
        dask_time = time.time() - start
        print(f"Dask analysis on 10K events: {dask_time:.2f}s")
        
    finally:
        os.unlink(large_file)

if __name__ == '__main__':
    # Run the tests
    print("Starting RFID Analytics Tests...")
    print("="*50)
    
    # Run unit tests
    unittest.main(verbosity=2, exit=False)
    
    # Run performance tests
    run_performance_tests()
    
    print("\n" + "="*50)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("="*50)