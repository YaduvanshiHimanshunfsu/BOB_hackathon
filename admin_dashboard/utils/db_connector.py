"""
admin_dashboard/utils/db_connector.py
=====================================
Database connector for the Streamlit Admin Dashboard.
Fetches risk history, device registries, and active sessions from PostgreSQL.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import streamlit as st

@st.cache_resource
def get_db_connection():
    """Create a cached database connection for Streamlit."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "cife_db"),
        user=os.getenv("POSTGRES_USER", "cife_user"),
        password=os.getenv("POSTGRES_PASSWORD", "changeme_strong_password"),
        cursor_factory=RealDictCursor
    )

def fetch_risk_history(limit: int = 100) -> pd.DataFrame:
    """Fetch the latest risk evaluations as a Pandas DataFrame."""
    conn = get_db_connection()
    query = """
        SELECT id, user_id, session_id, composite_score, risk_tier, action_taken, timestamp 
        FROM risk_ledger 
        ORDER BY timestamp DESC 
        LIMIT %s
    """
    df = pd.read_sql_query(query, conn, params=(limit,))
    return df

def fetch_device_registry(user_id: str = None) -> pd.DataFrame:
    """Fetch registered devices, optionally filtered by user."""
    conn = get_db_connection()
    if user_id:
        query = "SELECT * FROM device_registry WHERE user_id = %s ORDER BY last_seen DESC"
        params = (user_id,)
    else:
        query = "SELECT * FROM device_registry ORDER BY last_seen DESC LIMIT 50"
        params = ()
        
    df = pd.read_sql_query(query, conn, params=params)
    return df

def fetch_user_risk_timeline(user_id: str, limit: int = 50) -> pd.DataFrame:
    """Fetch detailed risk history for a specific user."""
    conn = get_db_connection()
    query = """
        SELECT timestamp, composite_score, risk_tier, action_taken, breakdown, context_factors
        FROM risk_ledger 
        WHERE user_id = %s 
        ORDER BY timestamp ASC 
        LIMIT %s
    """
    df = pd.read_sql_query(query, conn, params=(user_id, limit))
    return df
