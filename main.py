from fastapi import FastAPI
import pickle
import pandas as pd
import os
from optimizer import optimize_production

app = FastAPI(title="Flex Factory AI Engine")

# Get absolute path for relative model loading in Cloud
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, 'anomaly_model.pkl'), 'rb') as f:
    anomaly_model = pickle.load(f)

with open(os.path.join(BASE_DIR, 'energy_model.pkl'), 'rb') as f:
    energy_model = pickle.load(f)

@app.get("/")
def home():
    return {"status": "Flex Factory AI Core Online"}

@app.post("/api/telemetry")
def analyze_telemetry(data: dict):
    df_input = pd.DataFrame([data])
    
    # 1. Anomaly Detection
    is_anomaly_pred = anomaly_model.predict(df_input[['power_kw', 'production_rate_ppm', 'temperature_c']])[0]
    is_healthy = True if is_anomaly_pred == 1 else False
    
    # 2. Predicted Power
    predicted_power = float(energy_model.predict(df_input[['production_rate_ppm', 'temperature_c']])[0])
    
    return {
        "is_healthy": is_healthy,
        "predicted_power_kw": round(predicted_power, 2),
        "status": "Healthy" if is_healthy else "Anomaly Detected! Optimization recommended."
    }

@app.post("/api/optimize")
def run_optimization(req: dict):
    target = req.get("target_units", 1000)
    machines = req.get("machines_status", {})
    
    allocation = optimize_production(target, machines)
    return {"optimized_allocation": allocation}