"""
admin_dashboard/components/risk_heatmap.py
==========================================
Streamlit component for rendering a scatter/heatmap of recent risk events.
"""

import streamlit as st
import plotly.express as px
import pandas as pd

def render_risk_heatmap(df: pd.DataFrame):
    """Render a scatter plot of recent risk scores over time."""
    st.subheader("Real-Time Risk Events Matrix")
    
    if df.empty:
        st.info("No risk events found in the database. Awaiting telemetry...")
        return

    # Color mapping for risk tiers
    color_map = {
        "LOW": "#27ae60",       # Green
        "MODERATE": "#f1c40f",  # Yellow
        "HIGH": "#e67e22",      # Orange
        "CRITICAL": "#c0392b"   # Red
    }

    fig = px.scatter(
        df, 
        x="timestamp", 
        y="composite_score", 
        color="risk_tier",
        hover_data=["user_id", "session_id", "action_taken"],
        color_discrete_map=color_map,
        labels={
            "timestamp": "Time",
            "composite_score": "Composite Risk Score (0-100)",
            "risk_tier": "Risk Tier"
        },
        title="Live Transaction Risk Analysis"
    )
    
    # Add threshold lines
    fig.add_hline(y=34, line_dash="dash", line_color="#27ae60", annotation_text="Low (34)")
    fig.add_hline(y=54, line_dash="dash", line_color="#f1c40f", annotation_text="Moderate (54)")
    fig.add_hline(y=74, line_dash="dash", line_color="#e67e22", annotation_text="High (74)")

    fig.update_layout(yaxis_range=[0, 100], height=400)
    st.plotly_chart(fig, use_container_width=True)
