"""
admin_dashboard/components/session_timeline.py
==============================================
Streamlit component to visualize the risk evolution of a single user session.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import json

def render_session_timeline(df: pd.DataFrame, user_id: str):
    """Render a line chart tracking a user's risk score over their session history."""
    st.subheader(f"Session Timeline: {user_id}")
    
    if df.empty:
        st.warning(f"No history found for user '{user_id}'.")
        return

    # Extract behavioral and device scores from JSON breakdown
    df['behavioral_score'] = df['breakdown'].apply(lambda x: x.get('behavioral_score', 0) if isinstance(x, dict) else 0)
    df['device_score'] = df['breakdown'].apply(lambda x: x.get('device_score', 0) if isinstance(x, dict) else 0)

    fig = go.Figure()

    # Total composite score
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['composite_score'],
        mode='lines+markers', name='Composite Risk',
        line=dict(color='purple', width=3)
    ))

    # Behavioral component
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['behavioral_score'],
        mode='lines', name='Behavioral Score',
        line=dict(color='blue', width=1, dash='dot')
    ))

    # Device component
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['device_score'],
        mode='lines', name='Device Score',
        line=dict(color='orange', width=1, dash='dot')
    ))

    fig.update_layout(
        title="Risk Score Evolution",
        xaxis_title="Time",
        yaxis_title="Risk Score (0-100)",
        yaxis_range=[0, 100],
        height=350,
        margin=dict(l=0, r=0, t=40, b=0)
    )

    st.plotly_chart(fig, use_container_width=True)
    
    # Show data table
    with st.expander("View Raw Audit Data"):
        display_df = df[['timestamp', 'composite_score', 'risk_tier', 'action_taken']]
        st.dataframe(display_df, use_container_width=True)
