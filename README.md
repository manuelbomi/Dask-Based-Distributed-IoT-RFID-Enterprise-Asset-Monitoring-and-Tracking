# 🌐 Dask-Based Distributed IoT/RFID Enterprise Asset Tracking

### **(Distributed Analytics and Monitoring for IoT and RFID Asset Tracking using Dask, Docker and Streamlit)**

## Overview

##### This repository demonstrates how **Dask** can scale traditional data processing frameworks like **Pandas** to handle **large-scale IoT and RFID sensor data** in enterprise environments.  

##### The project simulates **asset tracking**, **temperature monitoring**, and **sensor analytics** using a distributed compute cluster powered by **Dask** and an interactive **Streamlit dashboard** for visualization.

##### Use this project to:
- Generate realistic IoT and RFID datasets (temperature sensors, cold-chain assets, etc.)
- Perform distributed ETL and analytics using Dask
- Visualize insights interactively with Streamlit dashboards
- Understand how Dask scales Pandas workflows for enterprise IoT use cases

---

##  Project Structure

```python
iot_enterprise_RIFD_IoT_use_cases_emm_oye/
│
├── Dockerfile
├── docker-compose.yaml
├── requirements.txt
│
├── data_generation/
│   ├── __init__.py
│   ├── generate_temperature_data.py
│   ├── generate_rfid_data.py
│   └── sample_data/
│       ├── temperature_logs.json
│       └── rfid_events.json
│
├── analytics/
│   ├── __init__.py
│   ├── temperature_analytics.py
│   ├── rfid_analytics.py
│   └── utils.py
│
├── streamlit_app/
│   ├── __init__.py
│   ├── app.py
│   ├── components/
│   │   ├── __init__.py
│   │   ├── temperature_dashboard.py
│   │   └── asset_tracking_dashboard.py
│   └── assets/
│       └── style.css
│
└── tests/
    ├── __init__.py
    ├── test_temperature_analytics.py
    └── test_rfid_analytics.py
```

---

## Streamlit Frontend Outputs

#### Below are examples of the types of detailed analytics that could be obatined from the project by either uploading your company's proprietary datasets or using the project to generate realistic IoT sensor or RFID inventory datasets of the form:

#### <Temperature Sensor>:

```python
{
  "event": "temperature_read",
  "epc": "3014B2C3D4E5F6",
  "temperature": 22.5,
  "unit": "C",
  "timestamp": "2024-01-15T10:00:00Z"
}
```

#### <RFID Inventory Events>:
```python

{
  "timestamp": "2024-07-11T18:55:05.119283747Z",
  "tagInventoryEvent": {
    "epc_number": "ABAB7234567890A5A5A5A5A501000012",
    "gateway_location": abc10,
    "gateway_xmit_power": 2200,
    "gateway_ph_ang": 91
    "gateway_ant_port" : 8,
    "gateway_ant_rssi": -2250,
    "gateway_freq"": 8897300 
   
  }
}

```



      
