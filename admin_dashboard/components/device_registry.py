"""
admin_dashboard/components/device_registry.py
=============================================
Streamlit component for viewing known devices and their trust status.
"""

import streamlit as st
import pandas as pd
import json

def render_device_registry(df: pd.DataFrame):
    """Render a table of registered devices with their attributes."""
    st.subheader("Device Registry & Trust Manager")
    
    if df.empty:
        st.info("No devices registered yet.")
        return

    # Format the dataframe for display
    display_df = df.copy()
    
    # Extract key attributes from JSON for easier viewing
    display_df['os_browser'] = display_df['attributes'].apply(
        lambda x: f"{x.get('user_agent', 'Unknown')[:30]}..." if isinstance(x, dict) else "Unknown"
    )
    
    cols_to_show = ['user_id', 'fingerprint_hash', 'trust_level', 'session_count', 'last_seen', 'os_browser']
    
    st.dataframe(
        display_df[cols_to_show], 
        use_container_width=True,
        hide_index=True,
        column_config={
            "trust_level": st.column_config.TextColumn("Trust Level"),
            "session_count": st.column_config.NumberColumn("Sessions", format="%d"),
            "last_seen": st.column_config.DatetimeColumn("Last Seen", format="D MMM YYYY, h:mm a"),
        }
    )
