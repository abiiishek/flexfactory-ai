import pandas as pd
import xgboost as xgb
import pickle

# Load dataset
df = pd.read_csv('factory_telemetry_data.csv')

# Features and Target
X = df[['production_rate_ppm', 'temperature_c']]
y = df['power_kw']

# Train XGBoost Regressor
model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=4)
model.fit(X, y)

# Save trained model
with open('energy_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("SUCCESS: XGBoost Energy Model Trained and saved as 'energy_model.pkl'!")