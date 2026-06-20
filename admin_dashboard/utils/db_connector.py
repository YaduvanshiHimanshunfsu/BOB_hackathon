"""
admin_dashboard/utils/db_connector.py
=====================================
Database connector for the Streamlit Admin Dashboard.
Fetches risk history, device registries, and active sessions from SQLite.
"""

import sqlite3
import pandas as pd
import os
import json
from shared.logger import get_logger

logger = get_logger("DBConnector")
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "cife_demo.db"))

def get_db_connection():
    try:
        return sqlite3.connect(DB_PATH)
    except sqlite3.Error as e:
        logger.error(f"Failed to connect to SQLite: {e}")
        return None

def fetch_risk_history(limit: int = 100) -> pd.DataFrame:
    """Fetch the latest risk evaluations as a Pandas DataFrame."""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    query = """
        SELECT timestamp, user_id, session_id, event_trigger, composite_risk_score, risk_tier, action, breakdown
        FROM risk_ledger 
        ORDER BY timestamp DESC 
        LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=(limit,))
    conn.close()
    return df

def fetch_device_registry(user_id: str = None) -> pd.DataFrame:
    """Fetch registered devices, optionally filtered by user."""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
        
    try:
        query = "SELECT user_id, device_registry FROM user_baselines"
        df = pd.read_sql_query(query, conn)
        
        # Flatten the JSON device registry into a list of dictionaries for the DataFrame
        devices_list = []
        for _, row in df.iterrows():
            current_user_id = row['user_id']
            if user_id and current_user_id != user_id:
                continue
                
            try:
                registry = json.loads(row['device_registry']) if row['device_registry'] else []
                for device in registry:
                    device['user_id'] = current_user_id
                    devices_list.append(device)
            except Exception:
                pass
                
        return pd.DataFrame(devices_list)
    finally:
        conn.close()

def fetch_user_risk_timeline(user_id: str, limit: int = 50) -> pd.DataFrame:
    """Fetch detailed risk history for a specific user."""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
        
    query = """
        SELECT timestamp, composite_risk_score as composite_score, risk_tier, action as action_taken, breakdown
        FROM risk_ledger 
        WHERE user_id = ? 
        ORDER BY timestamp ASC 
        LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=(user_id, limit))
    conn.close()
    return df
