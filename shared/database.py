import sqlite3
import json
import os
from datetime import datetime
from shared.logger import get_logger

logger = get_logger("SQLiteDB")

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cife_demo.db"))

class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        logger.info(f"Initializing SQLite database at {self.db_path}")
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Users baseline table (SQLite uses TEXT for JSON)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_baselines (
                user_id TEXT PRIMARY KEY,
                behavioral_profile TEXT,
                device_registry TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Risk ledger table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS risk_ledger (
                event_id TEXT PRIMARY KEY,
                user_id TEXT,
                session_id TEXT,
                timestamp TIMESTAMP,
                event_trigger TEXT,
                composite_risk_score REAL,
                risk_tier TEXT,
                action TEXT,
                breakdown TEXT
            )
            """)
            conn.commit()

    def get_user_baseline(self, user_id: str) -> dict:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT behavioral_profile, device_registry FROM user_baselines WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            
            if not row:
                return {"profiles": {}, "registered_devices": []}
                
            behavioral_profile = json.loads(row[0]) if row[0] else {}
            device_registry = json.loads(row[1]) if row[1] else []
            
            return {
                "profiles": behavioral_profile,
                "registered_devices": device_registry
            }

    def save_user_baseline(self, user_id: str, baseline: dict):
        behavioral_profile = json.dumps(baseline.get("profiles", {}))
        device_registry = json.dumps(baseline.get("registered_devices", []))
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO user_baselines (user_id, behavioral_profile, device_registry, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                behavioral_profile = excluded.behavioral_profile,
                device_registry = excluded.device_registry,
                updated_at = CURRENT_TIMESTAMP
            """, (user_id, behavioral_profile, device_registry))
            conn.commit()

    def log_risk_event(self, event_data: dict):
        # We generate a simple UUID-like string since sqlite doesn't have uuid_generate_v4() built-in
        import uuid
        event_id = str(uuid.uuid4())
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO risk_ledger (event_id, user_id, session_id, timestamp, event_trigger, composite_risk_score, risk_tier, action, breakdown)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id,
                event_data.get("user_id"),
                event_data.get("session_id"),
                event_data.get("timestamp"),
                event_data.get("event_trigger"),
                event_data.get("composite_risk_score", 0.0),
                event_data.get("risk_tier", "UNKNOWN"),
                event_data.get("action", "ALLOW"),
                json.dumps(event_data.get("breakdown", {}))
            ))
            conn.commit()

# Create a singleton instance
db = Database()
