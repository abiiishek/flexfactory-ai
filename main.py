from fastapi import FastAPI
import pickle
import pandas as pd
import os
from optimizer import optimize_production

app = FastAPI(title="Flex Factory AI Engine")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

anomaly_model = None
energy_model = None

# Safe Model Loading
try:
    with open(os.path.join(BASE_DIR, 'anomaly_model.pkl'), 'rb') as f:
        anomaly_model = pickle.load(f)
except Exception as e:
    print(f"Warning: anomaly_model.pkl loading failed: {e}")

try:
    with open(os.path.join(BASE_DIR, 'energy_model.pkl'), 'rb') as f:
        energy_model = pickle.load(f)
except Exception as e:
    print(f"Warning: energy_model.pkl loading failed: {e}")


@app.get("/")
def home():
    return {"status": "Flex Factory AI Core Online"}

@app.post("/api/telemetry")
def analyze_telemetry(data: dict):
    df_input = pd.DataFrame([data])
    
    # 1. Anomaly Detection Fallback Logic
    if anomaly_model and hasattr(anomaly_model, 'predict'):
        try:
            is_anomaly_pred = anomaly_model.predict(df_input[['power_kw', 'production_rate_ppm', 'temperature_c']])[0]
            is_healthy = True if is_anomaly_pred == 1 else False
        except Exception:
            is_healthy = True if data.get('temperature_c', 0) < 70 else False
    else:
        # Rules-based Fallback if ML model binary is missing
        is_healthy = True if data.get('temperature_c', 0) < 70 and data.get('power_kw', 0) < 8 else False

    # 2. Predicted Power Fallback Logic
    if energy_model and hasattr(energy_model, 'predict'):
        try:
            predicted_power = float(energy_model.predict(df_input[['production_rate_ppm', 'temperature_c']])[0])
        except Exception:
            predicted_power = round(data.get('production_rate_ppm', 1) * 0.45 + 1.2, 2)
    else:
        predicted_power = round(data.get('production_rate_ppm', 1) * 0.45 + 1.2, 2)
    
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