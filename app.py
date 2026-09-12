import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# Import ML & Optimization functions directly
from main import predict_telemetry, run_optimization  # Adjust function names based on your main.py

# Page Config
st.set_page_config(page_title="FLEXFACTORY AI — Smart Control Room", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for Industrial Dark Theme
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    </style>
""", unsafe_allow_html=True)

st.title("🏭 FLEXFACTORY AI — Enterprise Energy & Production Control")
st.caption("Real-Time Telemetry Processing | XGBoost Power Prediction | Google CP-SAT Optimization")
st.markdown("---")

# Navigation Menu
selected = option_menu(
    menu_title=None,
    options=["Live Control Room", "AI Optimization Engine", "Analytics & Diagnostics"],
    icons=["speedometer", "cpu", "graph-up"],
    default_index=0,
    orientation="horizontal"
)

# ----------------------------------------------------
# TAB 1: LIVE CONTROL ROOM
# ----------------------------------------------------
if selected == "Live Control Room":
    st.subheader("📡 Live Telemetry & Health Monitoring")
    
    col_input, col_display = st.columns([1, 2])
    
    with col_input:
        st.write("### 🕹️ Machine Sensor Controls")
        machine_id = st.selectbox("Select Target Machine", ["Machine_A", "Machine_B", "Machine_C"])
        power = st.slider("Power Consumption (kW)", 1.0, 10.0, 4.2)
        production = st.slider("Production Rate (Units/Min)", 1, 20, 8)
        temp = st.slider("Motor Temperature (°C)", 20.0, 90.0, 62.0)
        
        analyze_btn = st.button("🔍 Run Real-Time AI Analysis", use_container_width=True)

    with col_display:
        if analyze_btn:
            try:
                # Direct python execution instead of HTTP request
                res = predict_telemetry(power, production, temp)
                
                # Metrics Row
                m1, m2, m3 = st.columns(3)
                m1.metric("Predicted Power", f"{res['predicted_power_kw']} kW")
                m2.metric("Actual Power", f"{power} kW", delta=round(power - res['predicted_power_kw'], 2), delta_color="inverse")
                
                if res['is_healthy']:
                    m3.metric("Machine Health Status", "NORMAL", delta="Healthy", delta_color="normal")
                    st.success(f"✅ System Status: {res['status']}")
                else:
                    m3.metric("Machine Health Status", "ANOMALY", delta="-ALERT-", delta_color="inverse")
                    st.error(f"🚨 System Status: {res['status']}")
                
                # Temperature Gauge Chart
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=temp,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Motor Temperature (°C)"},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "#ef4444" if temp > 55 else "#10b981"},
                        'steps': [
                            {'range': [0, 50], 'color': "#1f2937"},
                            {'range': [50, 70], 'color': "#374151"},
                            {'range': [70, 100], 'color': "#7f1d1d"}
                        ]
                    }
                ))
                fig_gauge.update_layout(height=250, margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fig_gauge, use_container_width=True)

            except Exception as e:
                st.error(f"Execution Error: {e}")

# ----------------------------------------------------
# TAB 2: AI OPTIMIZATION ENGINE
# ----------------------------------------------------
elif selected == "AI Optimization Engine":
    st.subheader("⚡ CP-SAT Workload Auto-Distribution")
    
    col_opt_in, col_opt_out = st.columns([1, 2])
    
    with col_opt_in:
        st.write("### 🎯 Production Objective")
        target_units = st.number_input("Target Total Output (Units)", min_value=100, max_value=5000, value=1200, step=100)
        
        st.write("### 🏗️ Factory Plant Status")
        st.info("Machine_A: Normal (SEC: 0.20)\nMachine_B: High Thermal Degrade (SEC: 0.38)\nMachine_C: Balanced (SEC: 0.24)")
        
        run_opt = st.button("🚀 Calculate Optimal Allocation", use_container_width=True)

    with col_opt_out:
        if run_opt:
            machines_status = {
                'Machine_A': {'capacity': 600, 'sec': 0.20, 'is_healthy': True},
                'Machine_B': {'capacity': 500, 'sec': 0.38, 'is_healthy': False},
                'Machine_C': {'capacity': 500, 'sec': 0.24, 'is_healthy': True}
            }
            
            try:
                # Direct python execution instead of HTTP request
                opt_res = run_optimization(target_units, machines_status)
                alloc = opt_res.get("optimized_allocation")
                
                if alloc:
                    df_alloc = pd.DataFrame(list(alloc.items()), columns=['Machine', 'Allocated Units'])
                    
                    fig_bar = px.bar(
                        df_alloc, x='Machine', y='Allocated Units', color='Machine',
                        text='Allocated Units', title="OR-Tools Load Allocation Result",
                        color_discrete_map={'Machine_A': '#10b981', 'Machine_B': '#ef4444', 'Machine_C': '#3b82f6'}
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                    
                    st.success("🎉 **Optimization Complete:** Workload shifted away from unhealthy Machine_B to prevent power surge and motor breakdown!")
            except Exception as e:
                st.error(f"Optimization Engine Error: {e}")

# ----------------------------------------------------
# TAB 3: ANALYTICS & DIAGNOSTICS
# ----------------------------------------------------
elif selected == "Analytics & Diagnostics":
    st.subheader("📊 Factory Historical Trend Analysis")
    
    try:
        df_hist = pd.read_csv('factory_telemetry_data.csv')
        df_hist['timestamp'] = pd.to_datetime(df_hist['timestamp'])
        
        fig_line = px.line(df_hist, x='timestamp', y='power_kw', color='machine_id', title="Historical Power Consumption (kW) Across Machines")
        st.plotly_chart(fig_line, use_container_width=True)
    except FileNotFoundError:
        st.warning("`factory_telemetry_data.csv` not found. Please run `dataset_generator.py` first.")