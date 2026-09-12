import pandas as pd
from sklearn.ensemble import IsolationForest
import pickle

# Load dataset
df = pd.read_csv('factory_telemetry_data.csv')

# Features for anomaly detection
features = ['power_kw', 'production_rate_ppm', 'temperature_c']
X = df[features]

# Train Isolation Forest model
model = IsolationForest(contamination=0.05, random_state=42)
model.fit(X)

# Save trained model
with open('anomaly_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("SUCCESS: Anomaly Detection Model Trained and saved as 'anomaly_model.pkl'!")