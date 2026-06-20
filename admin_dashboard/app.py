"""
admin_dashboard/app.py
======================
Main Streamlit application for the CIFE Admin Dashboard.
Allows bank admins/judges to monitor risk in real-time.
"""

import streamlit as st
import pandas as pd
import time

from utils.db_connector import fetch_risk_history, fetch_device_registry, fetch_user_risk_timeline
from components.risk_heatmap import render_risk_heatmap
from components.session_timeline import render_session_timeline
from components.device_registry import render_device_registry

# --- Page Config ---
st.set_page_config(
    page_title="CIFE Admin Dashboard | BOB Hackathon",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Styling ---
st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e2e;
        border-radius: 5px;
        padding: 15px;
        text-align: center;
        border-left: 4px solid #3498db;
    }
    .metric-value { font-size: 24px; font-weight: bold; color: #fff; }
    .metric-label { font-size: 12px; color: #a0a0b0; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Bank_of_Baroda_Logo.svg/512px-Bank_of_Baroda_Logo.svg.png", width=200)
    st.title("CIFE Command Center")
    st.markdown("Contextual Identity Fusion Engine")
    
    st.divider()
    
    auto_refresh = st.checkbox("Auto-refresh data (5s)", value=True)
    if st.button("Refresh Now 🔄"):
        st.cache_data.clear()
        
    st.divider()
    st.markdown("### User Search")
    search_user = st.text_input("Enter User ID to investigate:")

# --- Main Content ---
st.title("🛡️ Identity Risk Monitoring")

# Fetch Data
try:
    risk_df = fetch_risk_history(limit=500)
    devices_df = fetch_device_registry()
except Exception as e:
    st.error(f"Database connection failed. Ensure PostgreSQL is running. Error: {e}")
    st.stop()

# Auto-refresh logic
if auto_refresh:
    time.sleep(5)
    st.rerun()

# --- Top Metrics ---
col1, col2, col3, col4 = st.columns(4)

total_events = len(risk_df)
critical_events = len(risk_df[risk_df['risk_tier'] == 'CRITICAL']) if not risk_df.empty else 0
high_events = len(risk_df[risk_df['risk_tier'] == 'HIGH']) if not risk_df.empty else 0
total_devices = len(devices_df)

with col1:
    st.markdown(f"<div class='metric-card'><div class='metric-value'>{total_events}</div><div class='metric-label'>Events Monitored</div></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='metric-card' style='border-color: #c0392b;'><div class='metric-value'>{critical_events}</div><div class='metric-label'>Critical Blocks</div></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='metric-card' style='border-color: #e67e22;'><div class='metric-value'>{high_events}</div><div class='metric-label'>Step-up Challenges</div></div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div class='metric-card' style='border-color: #27ae60;'><div class='metric-value'>{total_devices}</div><div class='metric-label'>Registered Devices</div></div>", unsafe_allow_html=True)

st.write("") # Spacer

# --- Views ---
if search_user:
    st.markdown(f"### 🔍 Investigation Mode: `{search_user}`")
    user_timeline_df = fetch_user_risk_timeline(search_user)
    render_session_timeline(user_timeline_df, search_user)
    
    st.write("### Associated Devices")
    user_devices_df = fetch_device_registry(search_user)
    render_device_registry(user_devices_df)
    
    if st.button("← Back to Global View"):
        st.rerun()
else:
    tab1, tab2 = st.tabs(["Global Risk Heatmap", "Device Registry"])
    
    with tab1:
        render_risk_heatmap(risk_df)
        
    with tab2:
        render_device_registry(devices_df)
