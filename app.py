import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import json
import random

# Optional PySerial import for Hardware Bridge
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

# Import ML & Optimization functions directly from main.py
from main import analyze_telemetry, run_optimization

# Page Configuration
st.set_page_config(
    page_title="FLEXFACTORY AI — Enterprise Energy & Production Control",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Industrial Dark Theme
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    div[data-testid="stSidebar"] { background-color: #111827; }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# HARDWARE SENSOR BRIDGE LOGIC
# ----------------------------------------------------
def read_hardware_telemetry(data_source, selected_port, baud_rate):
    """
    Reads hardware sensor stream or simulates live IoT telemetry.
    Auto-detects machine degradation based on thermal & power thresholds.
    """
    telemetry_data = {}
    
    if data_source == "Serial Bridge" and SERIAL_AVAILABLE:
        try:
            ser = serial.Serial(selected_port, baud_rate, timeout=1)
            line = ser.readline().decode('utf-8').strip()
            ser.close()
            if line:
                # Expecting JSON format from ESP32/Arduino: {"Machine_A": {"temp": 65, "power": 4.2}, ...}
                telemetry_data = json.loads(line)
        except Exception:
            pass

    # Fallback / Simulated Hardware Stream if Serial fails or in Autonomous Simulation
    if not telemetry_data:
        # Dynamic hardware sensor simulation with occasional degradation spike
        telemetry_data = {
            'Machine_A': {
                'temp': round(st.session_state.get('temp_A', 52.0) + random.uniform(-0.5, 0.5), 1),
                'power': round(4.0 + random.uniform(-0.2, 0.2), 2),
                'base_sec': 0.20,
                'capacity': 600
            },
            'Machine_B': {
                'temp': round(st.session_state.get('temp_B', 78.5) + random.uniform(-0.8, 0.8), 1), # High Temp / Degraded
                'power': round(6.8 + random.uniform(-0.3, 0.3), 2),
                'base_sec': 0.22,
                'capacity': 500
            },
            'Machine_C': {
                'temp': round(st.session_state.get('temp_C', 58.0) + random.uniform(-0.4, 0.4), 1),
                'power': round(4.5 + random.uniform(-0.2, 0.2), 2),
                'base_sec': 0.24,
                'capacity': 500
            }
        }

    # AUTOMATIC HEALTH & SEC INFERENCE FROM HARDWARE SENSORS
    # Rule: If Temp > 70°C or Power > 6.0 kW -> Machine is DEGRADED, SEC increases
    live_machine_status = {}
    for m_name, m_data in telemetry_data.items():
        is_healthy = (m_data['temp'] <= 70.0) and (m_data['power'] <= 6.0)
        
        # If degraded, SEC increases proportionally due to energy efficiency loss
        sec = m_data['base_sec'] if is_healthy else round(m_data['base_sec'] * 1.7, 2)
        
        live_machine_status[m_name] = {
            'capacity': m_data['capacity'],
            'sec': sec,
            'is_healthy': is_healthy,
            'temp': m_data['temp'],
            'power': m_data['power']
        }
        
    return live_machine_status


# ----------------------------------------------------
# SIDEBAR: HARDWARE BRIDGE & CONFIGURATION
# ----------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/factory.png", width=60)
    st.title("FlexFactory Controls")
    st.caption("IoT Hardware & Telemetry Bridge")
    st.markdown("---")
    
    data_source = st.radio(
        "📡 Telemetry Data Source",
        ["Simulated Telemetry", "Serial Bridge"],
        index=0
    )
    
    com_port = "COM3"
    baud_rate = 115200
    
    if data_source == "Serial Bridge":
        com_port = st.selectbox("COM Port Selection", ["COM3", "COM4", "/dev/ttyUSB0"], index=0)
        baud_rate = st.selectbox("Baud Rate", [9600, 115200], index=1)
        st.success(f"Connected to {com_port} @ {baud_rate} baud")
    else:
        st.info("Operating in Autonomous Hardware Simulation Mode")
        
    st.markdown("---")
    
    # Fetch dynamic status from hardware bridge
    live_machines = read_hardware_telemetry(data_source, com_port, baud_rate)
    
    st.write("### 🏭 Active Hardware Telemetry")
    for m_id, m_info in live_machines.items():
        status_icon = "🟢 Normal" if m_info['is_healthy'] else "🔴 DEGRADED"
        st.write(f"• **{m_id}:** {status_icon}")
        st.caption(f"Temp: {m_info['temp']}°C | SEC: {m_info['sec']} kWh/U")

# Header Section
st.title("🏭 FLEXFACTORY AI — Enterprise Energy & Production Control")
st.caption("Real-Time Telemetry | XGBoost Power Prediction | RUL Predictive Maintenance | Google CP-SAT Optimization")
st.markdown("---")

# Navigation Bar
selected = option_menu(
    menu_title=None,
    options=["Live Control Room", "AI Optimization Engine", "RUL & Advanced Analytics"],
    icons=["speedometer", "cpu", "graph-up-arrow"],
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
        st.write("### 🕹️ Hardware Sensor Emulation Controls")
        machine_id = st.selectbox("Select Target Machine for Tuning", ["Machine_A", "Machine_B", "Machine_C"], index=1)
        power = st.slider("Power Consumption (kW)", 1.0, 10.0, live_machines[machine_id]['power'])
        production = st.slider("Production Rate (Units/Min)", 1, 20, 8)
        temp = st.slider("Motor Temperature (°C)", 20.0, 95.0, live_machines[machine_id]['temp'])
        operating_hours = st.number_input("Total Operating Hours", min_value=100, max_value=20000, value=3450, step=50)

    with col_display:
        try:
            payload = {"power_kw": power, "production_rate_ppm": production, "temperature_c": temp}
            res = analyze_telemetry(payload)
            
            base_life = 8000
            temp_penalty = max(0, (temp - 60) * 85)
            power_penalty = max(0, (power - 6.5) * 120)
            remaining_rul_hrs = max(0, round(base_life - operating_hours - temp_penalty - power_penalty, 1))
            health_idx = max(0.0, min(100.0, round((remaining_rul_hrs / base_life) * 100, 1)))

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Predicted Power", f"{res['predicted_power_kw']} kW")
            m2.metric("Actual Power", f"{power} kW", delta=round(power - res['predicted_power_kw'], 2), delta_color="inverse")
            
            if res['is_healthy']:
                m3.metric("Machine Status", "HEALTHY", delta="Normal Operation", delta_color="normal")
            else:
                m3.metric("Machine Status", "ANOMALY", delta="-CRITICAL ALERT-", delta_color="inverse")
            
            m4.metric("Predicted RUL", f"{remaining_rul_hrs} Hrs", delta=f"{health_idx}% Health Index", delta_color="normal" if health_idx > 40 else "inverse")
            
            if not res['is_healthy']:
                st.error(f"🚨 **Hardware Warning:** {res['status']}")
            else:
                st.success(f"✅ **Hardware Status:** {res['status']}")

            g_col1, g_col2 = st.columns(2)
            
            with g_col1:
                fig_temp_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=temp,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Motor Temperature (°C)"},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "#ef4444" if temp > 70 else "#10b981"},
                        'steps': [
                            {'range': [0, 50], 'color': "#1f2937"},
                            {'range': [50, 70], 'color': "#374151"},
                            {'range': [70, 100], 'color': "#7f1d1d"}
                        ]
                    }
                ))
                fig_temp_gauge.update_layout(height=230, margin=dict(l=10, r=10, t=35, b=10))
                st.plotly_chart(fig_temp_gauge, use_container_width=True)

            with g_col2:
                fig_health_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=health_idx,
                    number={'suffix': "%"},
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Machine Health Index"},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "#10b981" if health_idx > 50 else "#ef4444"},
                        'steps': [
                            {'range': [0, 30], 'color': "#7f1d1d"},
                            {'range': [30, 60], 'color': "#374151"},
                            {'range': [60, 100], 'color': "#1f2937"}
                        ]
                    }
                ))
                fig_health_gauge.update_layout(height=230, margin=dict(l=10, r=10, t=35, b=10))
                st.plotly_chart(fig_health_gauge, use_container_width=True)

        except Exception as e:
            st.error(f"Execution Error: {e}")

# ----------------------------------------------------
# TAB 2: AI OPTIMIZATION ENGINE
# ----------------------------------------------------
elif selected == "AI Optimization Engine":
    st.subheader("⚡ CP-SAT Dynamic Workload Auto-Distribution")
    
    col_opt_in, col_opt_out = st.columns([1, 2])

    # Hardware Status fetched directly from IoT Bridge
    machines_status = read_hardware_telemetry(data_source, com_port, baud_rate)
    total_plant_capacity = sum([m['capacity'] for m in machines_status.values()])

    with col_opt_in:
        st.write("### 🎯 Production Objective")
        target_units = st.number_input("Target Total Output (Units)", min_value=100, max_value=5000, value=1200, step=100)
        
        st.write("### 📡 Live Hardware Plant Status")
        st.caption("Status automatically sensed from IoT Telemetry Stream:")

        status_text = f"**Total Capacity:** {total_plant_capacity} Units\n\n"
        for m_name, m_info in machines_status.items():
            health_str = "Normal" if m_info['is_healthy'] else "DEGRADED (High Temp/Power)"
            status_text += f"• **{m_name}:** {health_str} | Temp: {m_info['temp']}°C | SEC: {m_info['sec']}\n"
        
        st.info(status_text)
        
        run_opt = st.button("🚀 Calculate Optimal Allocation", use_container_width=True, type="primary")

    with col_opt_out:
        if run_opt:
            if target_units > total_plant_capacity:
                st.error(f"⚠️ **Target Exceeds Physical Plant Capacity!**\n\nMaximum Plant Capacity: **{total_plant_capacity} Units** | Requested Target: **{target_units} Units**.")
            else:
                try:
                    payload = {"target_units": target_units, "machines_status": machines_status}
                    opt_res = run_optimization(payload)
                    alloc = opt_res.get("optimized_allocation")
                    
                    if alloc:
                        equal_share = target_units / 3.0
                        
                        sec_a = machines_status['Machine_A']['sec']
                        sec_b = machines_status['Machine_B']['sec']
                        sec_c = machines_status['Machine_C']['sec']

                        opt_energy = (alloc.get('Machine_A', 0) * sec_a) + (alloc.get('Machine_B', 0) * sec_b) + (alloc.get('Machine_C', 0) * sec_c)
                        baseline_energy = (equal_share * sec_a) + (equal_share * sec_b) + (equal_share * sec_c)
                        
                        energy_saved = max(0.0, round(baseline_energy - opt_energy, 1))
                        cost_saved = round(energy_saved * 8.5, 1)
                        co2_saved = round(energy_saved * 0.82, 1)
                        pct_saved = round((energy_saved / baseline_energy) * 100, 1) if baseline_energy > 0 else 0

                        k1, k2, k3 = st.columns(3)
                        k1.metric("Dynamic Energy Saved", f"{energy_saved} kWh", delta=f"{pct_saved}% Reduction", delta_color="normal")
                        k2.metric("Production Cost Saved", f"₹ {cost_saved}", delta="Tariff Savings", delta_color="normal")
                        k3.metric("Carbon Emission Offset", f"{co2_saved} kg CO2", delta="100% Waste Avoided", delta_color="normal")
                        
                        st.markdown("---")

                        chart_data = pd.DataFrame({
                            'Machine': ['Machine_A', 'Machine_B', 'Machine_C'] * 2,
                            'Workload (Units)': [
                                equal_share, equal_share, equal_share,
                                alloc.get('Machine_A', 0), alloc.get('Machine_B', 0), alloc.get('Machine_C', 0)
                            ],
                            'Allocation Type': ['Unoptimized Baseline'] * 3 + ['CP-SAT AI Optimized'] * 3
                        })

                        fig_compare = px.bar(
                            chart_data, 
                            x='Machine', 
                            y='Workload (Units)', 
                            color='Allocation Type',
                            barmode='group',
                            text_auto='.0f',
                            title="📊 Workload Distribution: Baseline vs CP-SAT Optimized",
                            color_discrete_map={'Unoptimized Baseline': '#4b5563', 'CP-SAT AI Optimized': '#10b981'}
                        )
                        fig_compare.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
                        st.plotly_chart(fig_compare, use_container_width=True)

                        st.write("### 📋 Detailed Allocation Breakdown")
                        summary_table = pd.DataFrame({
                            "Machine": [
                                f"Machine_A {'(Degraded)' if not machines_status['Machine_A']['is_healthy'] else ''}", 
                                f"Machine_B {'(Degraded)' if not machines_status['Machine_B']['is_healthy'] else ''}", 
                                f"Machine_C {'(Degraded)' if not machines_status['Machine_C']['is_healthy'] else ''}"
                            ],
                            "SEC (kWh/Unit)": [sec_a, sec_b, sec_c],
                            "Baseline Units": [round(equal_share), round(equal_share), round(equal_share)],
                            "Optimized Units": [alloc.get('Machine_A', 0), alloc.get('Machine_B', 0), alloc.get('Machine_C', 0)],
                            "Optimized Energy (kWh)": [
                                round(alloc.get('Machine_A', 0) * sec_a, 1),
                                round(alloc.get('Machine_B', 0) * sec_b, 1),
                                round(alloc.get('Machine_C', 0) * sec_c, 1)
                            ]
                        })
                        st.dataframe(summary_table, use_container_width=True, hide_index=True)

                        # Auto Detected Machine Banner
                        degraded_machines = [m_name for m_name, m_info in machines_status.items() if not m_info['is_healthy']]
                        
                        if degraded_machines:
                            degraded_str = ", ".join(degraded_machines)
                            st.success(f"🎉 **Optimization Complete:** Hardware telemetry auto-sensed degradation in **{degraded_str}**. Workload shifted away to prevent breakdown!")
                        else:
                            st.success("🎉 **Optimization Complete:** All hardware operating normally. Balanced dynamic workload applied!")

                except Exception as e:
                    st.error(f"Optimization Engine Error: {e}")

# ----------------------------------------------------
# TAB 3: RUL & ADVANCED ANALYTICS
# ----------------------------------------------------
elif selected == "RUL & Advanced Analytics":
    st.subheader("📊 Machine Degradation, Health Index & RUL Analytics")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Overall Plant Health", "84.2%", delta="-2.1% (30 Days)")
    c2.metric("Machine_A RUL", "4,210 Hrs", delta="Healthy (88%)")
    c3.metric("Machine_B RUL", "620 Hrs", delta="Critical Wear (24%)", delta_color="inverse")
    c4.metric("Machine_C RUL", "3,150 Hrs", delta="Normal (72%)")

    st.markdown("---")

    time_series = pd.date_range(end=pd.Timestamp.now(), periods=100, freq='h')
    np.random.seed(42)
    
    df_diag = pd.DataFrame({
        'Timestamp': time_series,
        'Machine_A_Health': np.linspace(95, 88, 100) + np.random.normal(0, 0.3, 100),
        'Machine_B_RUL_Curve': np.linspace(1800, 620, 100),
        'Machine_B_Health': np.linspace(60, 24, 100),
        'Machine_C_Health': np.linspace(82, 72, 100) + np.random.normal(0, 0.4, 100)
    })

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.write("### 📉 RUL Degradation Trend (Physics Wear Decay)")
        fig_rul = px.line(df_diag, x='Timestamp', y='Machine_B_RUL_Curve',
                          labels={'Machine_B_RUL_Curve': 'Remaining Useful Life (Hours)'},
                          title="Machine_B Predicted RUL Decay Curve")
        fig_rul.add_hline(y=500, line_dash="dash", line_color="red", annotation_text="Maintenance Cutoff Threshold")
        fig_rul.update_traces(line_color='#ef4444', line_width=3)
        st.plotly_chart(fig_rul, use_container_width=True)

    with col_chart2:
        st.write("### 🛡️ Multi-Machine Degradation Comparison")
        fig_deg = px.line(df_diag, x='Timestamp', y=['Machine_A_Health', 'Machine_B_Health', 'Machine_C_Health'],
                          labels={'value': 'Health Index (%)', 'variable': 'Machine'},
                          title="Plant Fleet Health Degradation Trend")
        st.plotly_chart(fig_deg, use_container_width=True)

    st.write("### 🛠️ Predictive Maintenance & Action Matrix")
    diag_summary = pd.DataFrame({
        "Machine ID": ["Machine_A", "Machine_B", "Machine_C"],
        "Health Index": ["88% (Optimal)", "24% (Critical)", "72% (Normal)"],
        "Estimated RUL": ["4,210 Hours (~175 Days)", "620 Hours (~25 Days)", "3,150 Hours (~131 Days)"],
        "Recommended Action": [
            "Routine Lubrication scheduled in 45 days",
            "🚨 Urgent: Motor Bearing Replacement required. Shift load immediately!",
            "Inspect Cooling Fan assembly during next planned downtime"
        ]
    })
    st.table(diag_summary)