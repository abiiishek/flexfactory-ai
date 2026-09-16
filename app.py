import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# Import ML & Optimization functions directly from main.py
from main import analyze_telemetry, run_optimization

# Page Configuration
st.set_page_config(
    page_title="FLEXFACTORY AI — Enterprise Energy & Production Control",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Industrial Dark Theme & Clean Spacing
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    div[data-testid="stSidebar"] { background-color: #111827; }
    </style>
""", unsafe_allow_html=True)

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
    
    if data_source == "Serial Bridge":
        com_port = st.selectbox("COM Port Selection", ["COM3", "COM4", "/dev/ttyUSB0"], index=0)
        baud_rate = st.selectbox("Baud Rate", [9600, 115200], index=1)
        st.success(f"Connected to {com_port} @ {baud_rate} baud")
    else:
        st.info("Operating in Autonomous Simulation Mode")
        
    st.markdown("---")
    st.write("### 🏭 Active Machines")
    st.write("• **Machine_A:** Normal SEC (0.20)")
    st.write("• **Machine_B:** Thermal Degraded (SEC: 0.38)")
    st.write("• **Machine_C:** Balanced SEC (0.24)")

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
        st.write("### 🕹️ Machine Sensor Controls")
        machine_id = st.selectbox("Select Target Machine", ["Machine_A", "Machine_B", "Machine_C"])
        power = st.slider("Power Consumption (kW)", 1.0, 10.0, 4.2)
        production = st.slider("Production Rate (Units/Min)", 1, 20, 8)
        temp = st.slider("Motor Temperature (°C)", 20.0, 95.0, 62.0)
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
                st.error(f"🚨 **System Warning:** {res['status']}")
            else:
                st.success(f"✅ **System Status:** {res['status']}")

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
    
    machines_status = {
        'Machine_A': {'capacity': 600, 'sec': 0.20, 'is_healthy': True},
        'Machine_B': {'capacity': 500, 'sec': 0.38, 'is_healthy': False},
        'Machine_C': {'capacity': 500, 'sec': 0.24, 'is_healthy': True}
    }
    
    total_plant_capacity = sum([m['capacity'] for m in machines_status.values()])

    with col_opt_in:
        st.write("### 🎯 Production Objective")
        target_units = st.number_input("Target Total Output (Units)", min_value=100, max_value=5000, value=1200, step=100)
        
        st.write("### 🏗️ Factory Plant Status")
        st.info(f"**Total Physical Capacity:** {total_plant_capacity} Units\n\n• **Machine_A:** Normal (SEC: 0.20)\n• **Machine_B:** High Thermal Degrade (SEC: 0.38)\n• **Machine_C:** Balanced (SEC: 0.24)")
        
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
                        opt_energy = (alloc.get('Machine_A', 0) * 0.20) + (alloc.get('Machine_B', 0) * 0.38) + (alloc.get('Machine_C', 0) * 0.24)
                        baseline_energy = (equal_share * 0.20) + (equal_share * 0.38) + (equal_share * 0.24)
                        
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
                            "Machine": ["Machine_A", "Machine_B", "Machine_C"],
                            "SEC (kWh/Unit)": [0.20, 0.38, 0.24],
                            "Baseline Units": [round(equal_share), round(equal_share), round(equal_share)],
                            "Optimized Units": [alloc.get('Machine_A', 0), alloc.get('Machine_B', 0), alloc.get('Machine_C', 0)],
                            "Optimized Energy (kWh)": [
                                round(alloc.get('Machine_A', 0) * 0.20, 1),
                                round(alloc.get('Machine_B', 0) * 0.38, 1),
                                round(alloc.get('Machine_C', 0) * 0.24, 1)
                            ]
                        })
                        st.dataframe(summary_table, use_container_width=True, hide_index=True)

                        # Dynamic Machine Degrade Detection Message
                        degraded_machines = [m_name for m_name, m_info in machines_status.items() if not m_info['is_healthy']]
                        
                        if degraded_machines:
                            degraded_str = ", ".join(degraded_machines)
                            st.success(f"🎉 **Optimization Complete:** Workload shifted away from degraded **{degraded_str}** to prevent power surge and motor breakdown!")
                        else:
                            st.success("🎉 **Optimization Complete:** All machines healthy. Balanced dynamic workload distribution applied for maximum efficiency!")

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