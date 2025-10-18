# 🌐 Dask-Based Distributed IoT/RFID Enterprise Asset Tracking

### **(Distributed Analytics and Monitoring for IoT and RFID Asset Tracking using Dask, Docker and Streamlit)**

## Overview

##### This repository demonstrates how **Dask** can scale traditional data processing frameworks like **Pandas** to handle **large-scale IoT and RFID sensor data** in enterprise environments.  

##### The project simulates **asset tracking**, **temperature monitoring**, and **sensor analytics** using a distributed compute cluster powered by **Dask** and an interactive **Streamlit dashboard** for visualization. The project is sequel to another project that comprehensively discusses how dask can be used to scale up enterprise RFID/IoT. The first project is available here:  

##### You can use this project to:
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

#### <ins>Temperature Sensor</ins>:

```python
{
  "event": "temperature_read",
  "epc": "3014B2C3D4E5F6",
  "temperature": 22.5,
  "unit": "C",
  "timestamp": "2024-01-15T10:00:00Z"
}
```

#### <ins>RFID Inventory Events</ins>:

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


<img width="1280" height="720" alt="Image" src="https://github.com/user-attachments/assets/6544148a-caf5-46f3-b95c-7007233f636a" />

<img width="1280" height="720" alt="Image" src="https://github.com/user-attachments/assets/fd33daba-7dea-4c2a-a92e-c942b47e9d3c" />

<img width="1280" height="720" alt="Image" src="https://github.com/user-attachments/assets/0ac594cd-30a6-424f-894d-1e7705f15879" />

<img width="1280" height="720" alt="Image" src="https://github.com/user-attachments/assets/610d8387-cd8b-4e11-bd2e-dd24d4e025c4" />

<img width="1280" height="720" alt="Image" src="https://github.com/user-attachments/assets/abb0f31e-c256-4cbd-b078-fe4e22fce2a7" />

<img width="1280" height="720" alt="Image" src="https://github.com/user-attachments/assets/5dfc7952-6223-4aef-aee1-9c3eea54c776" />

<img width="1280" height="720" alt="Image" src="https://github.com/user-attachments/assets/9dfd4a16-d9b1-4df2-b1a0-5344ab2ac19e" />

<img width="1280" height="720" alt="Image" src="https://github.com/user-attachments/assets/53a5982c-af3a-4bb4-9fdb-301a92dd58de" />



---

##  Getting Started

### 1️. Clone the Repository

```bash
git clone https://github.com/manuelbomi/Dask-Based-Distributed-IoT-RFID-Enterprise-Asset-Tracking.git
cd enterprise-iot-dask-asset-tracking
```

### 2️. Build and Run with Docker Compose

This setup launches:

A Streamlit web app for visualization

A Dask scheduler + workers for distributed computation

```bash
docker-compose up --build
```

> [!NOTE]
> Please ensure that you have Docker running on your system before the **docker-compose up --build** command

--- 

## Generating IoT and RFID Data

#### The project includes realistic data generators to simulate industrial IoT sensors and RFID events.

- To generate RFID and IoT sensors data, click on the data generatiing buttons on teh Streamlit front end.


<img width="1280" height="720" alt="Image" src="https://github.com/user-attachments/assets/dc1826cf-de7e-44a9-895e-996b26cc9bdd" />


<img width="1280" height="720" alt="Image" src="https://github.com/user-attachments/assets/dde95ddd-cdea-446a-b2e7-aa7c2b9f5708" />

- You can also manually generate data by using appropriate commands at the nack end through your VSCode terminal

Example: Generate temperature sensor data

```python
python -m data_generation.generate_temperature_data
```

#### This will create a JSON file in:

```python
data_generation/sample_data/temperature_logs.json
```
      
