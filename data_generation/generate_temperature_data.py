import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import os

def generate_temperature_data(num_records=10000, start_date="2024-01-01"):
    """Generate realistic temperature sensor data for cold chain monitoring"""
    np.random.seed(42)
    
    facilities = {
        'cold_storage_alpha': {'type': 'cold_storage', 'base_temp': -18, 'variance': 3},
        'cold_storage_beta': {'type': 'cold_storage', 'base_temp': -22, 'variance': 2},
        'refrigerated_transport_1': {'type': 'refrigerated_transport', 'base_temp': 4, 'variance': 2},
        'refrigerated_transport_2': {'type': 'refrigerated_transport', 'base_temp': 6, 'variance': 3},
        'room_temp_warehouse': {'type': 'room_temp_storage', 'base_temp': 20, 'variance': 5}
    }
    
    sensor_zones = ['freezer_unit_1', 'freezer_unit_2', 'loading_dock', 'storage_area', 'transit_zone']
    epc_prefixes = ['3014B2C3D4E5', '3014B2C3D4F6', '3014B2C3D4G7']
    
    data = []
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    
    for i in range(num_records):
        facility = np.random.choice(list(facilities.keys()))
        facility_info = facilities[facility]
        
        # Generate realistic temperature with some anomalies
        base_temp = facility_info['base_temp']
        variance = facility_info['variance']
        
        # 5% chance of anomalous reading
        if np.random.random() < 0.05:
            if facility_info['type'] == 'cold_storage':
                temperature = np.random.uniform(-5, 5)  # Dangerous warm spike
            elif facility_info['type'] == 'refrigerated_transport':
                temperature = np.random.uniform(15, 25)  # Dangerous warm spike
            else:
                temperature = np.random.uniform(-10, 0)  # Dangerous cold spike
        else:
            temperature = np.random.normal(base_temp, variance)
        
        event = {
            "event": "temperature_read",
            "epc": f"{np.random.choice(epc_prefixes)}{i:06X}",
            "temperature": round(temperature, 2),
            "unit": "C",
            "timestamp": (start_dt + timedelta(minutes=15*i)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "facility": facility,
            "sensor_zone": np.random.choice(sensor_zones)
        }
        data.append(event)
    
    return data

def save_temperature_data():
    """Generate and save temperature data"""
    data = generate_temperature_data(10000)
    os.makedirs('data_generation/sample_data', exist_ok=True)
    
    with open('data_generation/sample_data/temperature_logs.json', 'w') as f:
        for record in data:
            f.write(json.dumps(record) + '\n')
    
    print(f"Generated {len(data)} temperature records")
    return data

if __name__ == "__main__":
    save_temperature_data()