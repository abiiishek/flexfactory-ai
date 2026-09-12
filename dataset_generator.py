import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Parameters
np.random.seed(42)
num_samples = 1000
start_time = datetime.now()

machines = ['Machine_A', 'Machine_B', 'Machine_C']
data = []

for i in range(num_samples):
    timestamp = start_time + timedelta(minutes=i)
    
    for machine in machines:
        # Base machine behavior
        if machine == 'Machine_A':
            power = np.random.normal(loc=2.1, scale=0.1)     # Fast & Efficient
            production_rate = np.random.randint(9, 12)
            temp = np.random.normal(loc=38, scale=1.5)
        elif machine == 'Machine_B':
            power = np.random.normal(loc=3.8, scale=0.3)     # High Power Usage
            production_rate = np.random.randint(8, 11)
            temp = np.random.normal(loc=48, scale=2.0)
        else: # Machine C
            power = np.random.normal(loc=2.4, scale=0.15)    # Balanced
            production_rate = np.random.randint(7, 10)
            temp = np.random.normal(loc=40, scale=1.0)

        # Introduce intentional anomaly (10% chance for Machine B)
        is_anomaly = 0
        if machine == 'Machine_B' and np.random.rand() < 0.10:
            power += np.random.uniform(1.5, 2.5)  # Spike in power
            temp += np.random.uniform(10, 15)     # Spike in temp
            is_anomaly = 1

        # Specific Energy Consumption (SEC) calculation
        sec = power / (production_rate / 60) if production_rate > 0 else 0

        data.append({
            'timestamp': timestamp,
            'machine_id': machine,
            'power_kw': round(power, 2),
            'production_rate_ppm': production_rate,
            'temperature_c': round(temp, 1),
            'sec_kwh_per_unit': round(sec, 3),
            'is_anomaly': is_anomaly
        })

df = pd.DataFrame(data)
df.to_csv('factory_telemetry_data.csv', index=False)
print("SUCCESS: 'factory_telemetry_data.csv' successfully generated with 3000 readings!")