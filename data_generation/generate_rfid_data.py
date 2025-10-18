import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import os

def generate_rfid_data(num_events=15000, start_date="2024-07-11"):
    """Generate realistic RFID asset tracking data"""
    np.random.seed(42)
    
    facilities = {
        'warehouse_entrance': {'type': 'entry_point', 'zones': ['inbound_dock', 'security_check']},
        'warehouse_exit': {'type': 'exit_point', 'zones': ['outbound_dock', 'shipping_area']},
        'cold_storage_alpha': {'type': 'storage', 'zones': ['freezer_1', 'freezer_2', 'loading_area']},
        'manufacturing_line_1': {'type': 'production', 'zones': ['assembly_line', 'quality_check']},
        'high_value_storage': {'type': 'secure_storage', 'zones': ['vault_entrance', 'vault_interior']}
    }
    
    asset_types = {
        'perishable_goods': {'movement_rate': 0.8, 'typical_locations': ['cold_storage_alpha', 'warehouse_entrance']},
        'high_value_items': {'movement_rate': 0.3, 'typical_locations': ['high_value_storage', 'warehouse_entrance']},
        'raw_materials': {'movement_rate': 0.6, 'typical_locations': ['manufacturing_line_1', 'warehouse_entrance']},
        'finished_goods': {'movement_rate': 0.7, 'typical_locations': ['warehouse_exit', 'manufacturing_line_1']}
    }
    
    epc_prefixes = ['ABAB7234567890A5A5A5A5A5', 'CDCD8234567890B6B6B6B6B6', 'EFEF9234567890C7C7C7C7C7']
    
    data = []
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    
    # Generate assets with consistent patterns
    assets = []
    for i in range(500):
        asset_type = np.random.choice(list(asset_types.keys()))
        assets.append({
            'epc_number': f"{np.random.choice(epc_prefixes)}{i:08X}",
            'asset_type': asset_type,
            'movement_rate': asset_types[asset_type]['movement_rate']
        })
    
    current_locations = {asset['epc_number']: np.random.choice(asset_types[asset['asset_type']]['typical_locations']) 
                        for asset in assets}
    
    for i in range(num_events):
        asset = np.random.choice(assets)
        epc_number = asset['epc_number']
        asset_type = asset['asset_type']
        
        # Determine if asset moves based on its movement rate
        if np.random.random() < asset['movement_rate'] * 0.1:
            current_location = current_locations[epc_number]
            possible_moves = [loc for loc in facilities.keys() if loc != current_location]
            if possible_moves:
                new_location = np.random.choice(possible_moves)
                current_locations[epc_number] = new_location
        else:
            new_location = current_locations[epc_number]
        
        facility_info = facilities[new_location]
        zone = np.random.choice(facility_info['zones'])
        
        # Generate realistic RFID signal parameters
        event = {
            "timestamp": (start_dt + timedelta(seconds=30*i)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "tagInventoryEvent": {
                "epc_number": epc_number,
                "gateway_location": new_location,
                "gateway_zone": zone,
                "gateway_xmit_power": np.random.randint(2000, 2500),
                "gateway_ph_ang": np.random.randint(0, 360),
                "gateway_ant_port": np.random.randint(1, 9),
                "gateway_ant_rssi": np.random.randint(-3000, -1500),
                "gateway_freq": np.random.randint(8800000, 9200000),
                "asset_type": asset_type
            }
        }
        data.append(event)
    
    return data

def save_rfid_data():
    """Generate and save RFID data"""
    data = generate_rfid_data(15000)
    os.makedirs('data_generation/sample_data', exist_ok=True)
    
    with open('data_generation/sample_data/rfid_events.json', 'w') as f:
        for record in data:
            f.write(json.dumps(record) + '\n')
    
    print(f"Generated {len(data)} RFID events")
    return data

if __name__ == "__main__":
    save_rfid_data()