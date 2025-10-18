import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.temperature_analytics import TemperatureAnalytics
from data_generation.generate_temperature_data import save_temperature_data

class TestTemperatureAnalytics(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Generate sample data for testing
        save_temperature_data()
        cls.analytics = TemperatureAnalytics('data_generation/sample_data/temperature_logs.json')
        cls.analytics.load_data_pandas()
    
    def test_data_loading(self):
        self.assertIsNotNone(self.analytics.df_pandas)
        self.assertGreater(len(self.analytics.df_pandas), 0)
    
    def test_critical_breaches(self):
        breaches_df = self.analytics.pandas_critical_breaches()
        self.assertIsInstance(breaches_df, type(pd.DataFrame()))
    
    def test_rolling_statistics(self):
        rolling_df = self.analytics.pandas_rolling_statistics()
        self.assertIn('rolling_avg', rolling_df.columns)
        self.assertIn('is_anomaly', rolling_df.columns)

if __name__ == '__main__':
    unittest.main()