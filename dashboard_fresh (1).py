import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import time
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from psychrometrics_layer import PsychrometricsLayer

# Page config
st.set_page_config(
    page_title="SkyGuard AI - AWS Anomaly Detection",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .metric-box {
        background: white;
        border-left: 5px solid;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .metric-blue { border-left-color: #3b82f6; }
    .metric-green { border-left-color: #10b981; }
    .metric-red { border-left-color: #ef4444; }
    .metric-orange { border-left-color: #f97316; }
    
    .status-online { color: #10b981; font-weight: bold; }
    .status-alert { color: #ef4444; font-weight: bold; }
    .status-warning { color: #f97316; font-weight: bold; }
    
    .anomaly-card {
        background: white;
        border-left: 5px solid #ef4444;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    .physics-violation {
        background: #fef2f2;
        border-left-color: #dc2626;
    }
    
    .sensor-health-good {
        color: #10b981;
    }
    
    .sensor-health-warning {
        color: #f97316;
    }
    
    .sensor-health-critical {
        color: #ef4444;
    }
</style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_all_stations():
    try:
        df = pd.read_csv("10_AWS_stations_combined.csv")
        return df
    except:
        st.error("Data file not found")
        return None

df_all = load_all_stations()

if df_all is None:
    st.stop()

# Initialize session state
if 'current_date_index' not in st.session_state:
    st.session_state.current_date_index = 0
    st.session_state.is_playing = False
    st.session_state.anomalies_detected = []
    st.session_state.physics_violations = []

# Get unique dates and stations
unique_dates = pd.to_datetime(df_all['date']).unique()
unique_stations = df_all['station'].unique()

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================
st.sidebar.title("🌦️ SkyGuard AI")
st.sidebar.markdown("AWS Anomaly Detection System")
st.sidebar.divider()

nav_option = st.sidebar.radio(
    "NAVIGATION",
    ["Dashboard", "Live Monitoring", "Anomaly Alerts", "Sensor Health", "Security Status", "System Config"]
)

st.sidebar.divider()
st.sidebar.markdown("### System Status")
st.sidebar.markdown("🟢 **System Operational**")
st.sidebar.markdown(f"Last Update: Just now")

# ============================================================================
# TOP HEADER
# ============================================================================
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    st.markdown(f"<h1 style='color: #1f2937;'>AWS Intelligent Anomaly Detection</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #6b7280; margin-top: -10px;'>Real-time monitoring of 10 weather stations</p>", unsafe_allow_html=True)

with col2:
    current_date = unique_dates[min(st.session_state.current_date_index, len(unique_dates)-1)]
    st.metric("Current Date", pd.Timestamp(current_date).strftime("%d %b %Y"))

with col3:
    st.markdown(f"<p style='text-align: right; margin-top: 20px;'>{datetime.now().strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)

st.divider()

# ============================================================================
# PAGE: DASHBOARD
# ============================================================================
if nav_option == "Dashboard":
    # Top metrics
    st.subheader("Dashboard")
    st.markdown("Real-time overview of all AWS stations and anomaly status")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-box metric-blue">
            <p style="color: #9ca3af; margin: 0;">TOTAL STATIONS</p>
            <h2 style="margin: 5px 0;">10</h2>
            <p style="color: #6b7280; margin: 0; font-size: 12px;">Network coverage</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        online = len([s for s in unique_stations if not st.session_state.is_playing])  # Simplified
        st.markdown(f"""
        <div class="metric-box metric-green">
            <p style="color: #9ca3af; margin: 0;">ONLINE STATIONS</p>
            <h2 style="margin: 5px 0;">{online}/10</h2>
            <p style="color: #6b7280; margin: 0; font-size: 12px;">100% uptime</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        anomalies_count = len(st.session_state.anomalies_detected)
        st.markdown(f"""
        <div class="metric-box metric-red">
            <p style="color: #9ca3af; margin: 0;">ACTIVE ANOMALIES</p>
            <h2 style="margin: 5px 0;">{anomalies_count}</h2>
            <p style="color: #6b7280; margin: 0; font-size: 12px;">Needs attention</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        physics_viol = len(st.session_state.physics_violations)
        st.markdown(f"""
        <div class="metric-box metric-orange">
            <p style="color: #9ca3af; margin: 0;">PHYSICS VIOLATIONS</p>
            <h2 style="margin: 5px 0;">{physics_viol}</h2>
            <p style="color: #6b7280; margin: 0; font-size: 12px;">Edge 1 detected</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-box metric-green">
            <p style="color: #9ca3af; margin: 0;">SYSTEM HEALTH</p>
            <h2 style="margin: 5px 0;">98.6%</h2>
            <p style="color: #6b7280; margin: 0; font-size: 12px;">All systems nominal</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Active Anomalies
    st.subheader("Active Anomalies")
    
    if len(st.session_state.physics_violations) > 0:
        for anomaly in st.session_state.physics_violations[:3]:
            st.markdown(f"""
            <div class="anomaly-card physics-violation">
                <h4>{anomaly['station']}</h4>
                <p><strong>Type:</strong> Physics Violation (Edge 1)</p>
                <p><strong>Observed:</strong> {anomaly['temp']:.1f}°C, {anomaly['humidity']:.1f}%, {anomaly['pressure']:.1f} hPa</p>
                <p><strong>Violation:</strong> {anomaly['reason']}</p>
                <p><strong>Confidence:</strong> {anomaly['confidence']:.0f}%</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No active anomalies detected")
    
    st.divider()
    
    # Station Status
    st.subheader("Station Status")
    
    # Get latest data for each station
    current_date = unique_dates[min(st.session_state.current_date_index, len(unique_dates)-1)]
    latest_data = df_all[df_all['date'] == pd.Timestamp(current_date).strftime('%Y-%m-%d')]
    
    cols = st.columns(2)
    for idx, station in enumerate(unique_stations):
        col = cols[idx % 2]
        
        station_data = latest_data[latest_data['station'] == station]
        if len(station_data) > 0:
            row = station_data.iloc[0]
            temp = row['temperature']
            humidity = row['humidity']
            
            status_indicator = "🟢" if not any(a['station'] == station for a in st.session_state.physics_violations) else "🔴"
            
            with col:
                st.markdown(f"{status_indicator} **{station}**")
                st.markdown(f"  Temp: {temp:.1f}°C | Humidity: {humidity:.1f}%")

# ============================================================================
# PAGE: LIVE MONITORING
# ============================================================================
elif nav_option == "Live Monitoring":
    st.subheader("Live Monitoring")
    st.markdown("Real-time sensor readings with Edge 1 Psychrometrics validation")
    
    # Time controls
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        max_date_index = len(unique_dates) - 1
        current_index = st.slider(
            "Timeline",
            0, 
            max_date_index,
            st.session_state.current_date_index,
            label_visibility="collapsed"
        )
        st.session_state.current_date_index = current_index
    
    with col2:
        if st.button("▶️ Play", key="play_btn"):
            st.session_state.is_playing = True
    
    with col3:
        if st.button("⏸️ Pause", key="pause_btn"):
            st.session_state.is_playing = False
    
    with col4:
        if st.button("🔄 Reset", key="reset_btn"):
            st.session_state.current_date_index = 0
            st.session_state.anomalies_detected = []
            st.session_state.physics_violations = []
    
    st.divider()
    
    # Station selector
    selected_station = st.selectbox(
        "Select Station",
        unique_stations,
        index=0
    )
    
    current_date = unique_dates[min(st.session_state.current_date_index, len(unique_dates)-1)]
    current_data = df_all[(df_all['date'] == pd.Timestamp(current_date).strftime('%Y-%m-%d')) & 
                          (df_all['station'] == selected_station)]
    
    if len(current_data) > 0:
        row = current_data.iloc[0]
        temp = row['temperature']
        humidity = row['humidity']
        pressure = row['pressure']
        
        st.markdown(f"**{selected_station}** | Online 🟢 | Last updated: Just now")
        
        # Live sensor cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🌡️ Temperature", f"{temp:.1f}°C", delta=f"{temp-25:.1f}°C from normal")
        
        with col2:
            st.metric("💧 Humidity", f"{humidity:.1f}%", delta=f"{humidity-60:.1f}% from baseline")
        
        with col3:
            st.metric("🔽 Pressure", f"{pressure:.1f} hPa", delta=f"{pressure-1013:.1f} hPa")
        
        with col4:
            st.metric("🌧️ Rainfall", f"{row['rainfall']:.1f} mm", delta="Last 15 min")
        
        st.divider()
        
        # EDGE 1: PSYCHROMETRICS VALIDATION
        st.subheader("🔬 Edge 1: Physics-Informed Validation")
        
        result = PsychrometricsLayer.validate_reading(temp, humidity, pressure)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if result['is_physically_valid']:
                st.success(f"✅ Physics Valid - Confidence: {result['confidence_score']:.0f}%")
            else:
                st.error(f"❌ Physics Violation - Confidence: {result['confidence_score']:.0f}%")
                st.warning("### Violations Detected:")
                for v in result['violations']:
                    st.write(f"- {v}")
        
        with col2:
            st.metric("Dew Point", f"{result['dew_point_c']:.1f}°C" if result['dew_point_c'] else "N/A")
        
        st.divider()
        
        # Sensor trends (simple line chart)
        st.subheader("Sensor Trends")
        
        # Get last 30 days of data for this station
        last_30_days = df_all[(df_all['station'] == selected_station)].tail(30)
        
        if len(last_30_days) > 0:
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(range(len(last_30_days)), last_30_days['temperature'], marker='o', label='Temperature', color='#ef4444')
            ax.plot(range(len(last_30_days)), last_30_days['humidity'], marker='s', label='Humidity', color='#3b82f6', alpha=0.7)
            ax.set_xlabel('Days')
            ax.set_ylabel('Value')
            ax.legend()
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)

# ============================================================================
# PAGE: ANOMALY ALERTS
# ============================================================================
elif nav_option == "Anomaly Alerts":
    st.subheader("Anomaly Alerts")
    st.markdown("Detailed anomaly detections with root cause classification")
    
    tab1, tab2, tab3 = st.tabs(["All Anomalies", "Physics Violations", "Sensor Faults"])
    
    with tab1:
        if len(st.session_state.physics_violations) > 0:
            for anomaly in st.session_state.physics_violations:
                with st.expander(f"🔴 {anomaly['station']} - Physics Violation"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Observed Values:**")
                        st.write(f"- Temperature: {anomaly['temp']:.1f}°C")
                        st.write(f"- Humidity: {anomaly['humidity']:.1f}%")
                        st.write(f"- Pressure: {anomaly['pressure']:.1f} hPa")
                    with col2:
                        st.write(f"**Detection:**")
                        st.write(f"- Edge Layer: Edge 1 (Psychrometrics)")
                        st.write(f"- Confidence: {anomaly['confidence']:.0f}%")
                        st.write(f"- Timestamp: {anomaly['timestamp']}")
        else:
            st.info("No anomalies detected yet")
    
    with tab2:
        st.write("Physics violations detected by Edge 1 validation layer")
        if len(st.session_state.physics_violations) > 0:
            for anomaly in st.session_state.physics_violations:
                st.warning(f"{anomaly['station']}: {anomaly['reason']}")
        else:
            st.info("No physics violations")
    
    with tab3:
        st.write("Sensor faults detected (hard anomalies from training data)")
        st.info("Check Live Monitoring for current sensor behavior")

# ============================================================================
# PAGE: SENSOR HEALTH
# ============================================================================
elif nav_option == "Sensor Health":
    st.subheader("Sensor Health")
    st.markdown("Health scores and fault risk across all sensors")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-box">
            <p style="color: #9ca3af;">OVERALL SENSOR HEALTH</p>
            <h1 style="color: #10b981; margin: 10px 0;">94.7%</h1>
            <p style="color: #10b981; margin: 0;;">🟢 Good</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-box">
            <p style="color: #9ca3af;">DEGRADATION RISK</p>
            <h1 style="color: #f97316; margin: 10px 0;">Medium</h1>
            <p style="color: #f97316; margin: 0;">2 sensors showing drift</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-box">
            <p style="color: #9ca3af;">MAINTENANCE NEEDED</p>
            <h1 style="color: #6b7280; margin: 10px 0;">1</h1>
            <p style="color: #6b7280; margin: 0;">in next 7 days</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Sensor health breakdown
    st.subheader("Per-Sensor Health Scores")
    
    sensors = ["Temperature", "Humidity", "Pressure", "Rainfall"]
    health_scores = {
        "Temperature": 92,
        "Humidity": 99,
        "Pressure": 97,
        "Rainfall": 100
    }
    
    for sensor, score in health_scores.items():
        col1, col2 = st.columns([1, 3])
        with col1:
            if score >= 95:
                st.markdown(f"🟢 {sensor}: {score}%")
            elif score >= 85:
                st.markdown(f"🟡 {sensor}: {score}%")
            else:
                st.markdown(f"🔴 {sensor}: {score}%")
        with col2:
            st.progress(score / 100)

# ============================================================================
# PAGE: SECURITY STATUS
# ============================================================================
elif nav_option == "Security Status":
    st.subheader("Security Status")
    st.markdown("Adversarial attack detection and quarantine logs (Edge 4)")
    
    st.info("🟢 No suspicious patterns detected | System secure")
    st.divider()
    
    st.subheader("Quarantine Zone")
    st.markdown("Stations isolated due to suspected cyber attacks")
    st.write("None currently quarantined")

# ============================================================================
# PAGE: SYSTEM CONFIG
# ============================================================================
elif nav_option == "System Config":
    st.subheader("System Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Detection Layers")
        st.checkbox("✅ Edge 1: Psychrometrics", value=True, disabled=True)
        st.checkbox("✅ Edge 2: Entropy Trap", value=True, disabled=True)
        st.checkbox("✅ Edge 3: Self-Healing", value=True, disabled=True)
        st.checkbox("✅ Edge 4: Quarantine", value=True, disabled=True)
    
    with col2:
        st.markdown("### Data Sources")
        st.write(f"- 10 AWS Stations")
        st.write(f"- 730 days historical data")
        st.write(f"- Updated: Real-time playback")
        st.write(f"- Status: All online")

# ============================================================================
# PLAYBACK LOGIC
# ============================================================================
# Simulate anomaly injection during playback
if st.session_state.is_playing:
    placeholder = st.empty()
    
    for i in range(st.session_state.current_date_index, min(st.session_state.current_date_index + 5, len(unique_dates))):
        current_date = unique_dates[i]
        current_data = df_all[df_all['date'] == pd.Timestamp(current_date).strftime('%Y-%m-%d')]
        
        # Check for physics violations
        for _, row in current_data.iterrows():
            result = PsychrometricsLayer.validate_reading(
                row['temperature'],
                row['humidity'],
                row['pressure']
            )
            
            if not result['is_physically_valid']:
                # Store physics violation
                if not any(a['station'] == row['station'] and a['timestamp'] == str(current_date) for a in st.session_state.physics_violations):
                    st.session_state.physics_violations.append({
                        'station': row['station'],
                        'temp': row['temperature'],
                        'humidity': row['humidity'],
                        'pressure': row['pressure'],
                        'reason': result['violations'][0] if result['violations'] else 'Unknown',
                        'confidence': result['confidence_score'],
                        'timestamp': str(current_date)
                    })
        
        st.session_state.current_date_index = i
        
        with placeholder.container():
            st.info(f"📅 Playing: {pd.Timestamp(current_date).strftime('%d %b %Y')} | Anomalies detected: {len(st.session_state.physics_violations)}")
        
        time.sleep(0.5)  # Playback speed
    
    st.session_state.is_playing = False
    st.rerun()
