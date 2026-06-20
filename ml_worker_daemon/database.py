"""
ml_worker_daemon/database.py
============================
PostgreSQL database connection and CRUD operations for the ML Worker.
Handles storing/retrieving user baselines and writing the risk audit ledger.
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import time
from shared.logger import get_logger

logger = get_logger("ml_worker.db")

class Database:
    def __init__(self):
        self.host = os.getenv("POSTGRES_HOST", "localhost")
        self.port = os.getenv("POSTGRES_PORT", "5432")
        self.db = os.getenv("POSTGRES_DB", "cife_db")
        self.user = os.getenv("POSTGRES_USER", "cife_user")
        self.password = os.getenv("POSTGRES_PASSWORD", "changeme_strong_password")
        self.conn = None

    def connect(self):
        """Establish connection to PostgreSQL, with retries."""
        retries = 5
        for i in range(retries):
            try:
                self.conn = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    dbname=self.db,
                    user=self.user,
                    password=self.password,
                    cursor_factory=RealDictCursor
                )
                self.conn.autocommit = True
                logger.info("Connected to PostgreSQL")
                self.init_schema()
                return
            except psycopg2.OperationalError as e:
                logger.warning(f"DB connection failed, retrying ({i+1}/{retries}): {e}")
                time.sleep(2)
        raise Exception("Could not connect to PostgreSQL after multiple retries")

    def init_schema(self):
        """Initialize required tables if they don't exist."""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS user_baselines (
                user_id VARCHAR(128) PRIMARY KEY,
                behavioral_profile JSONB NOT NULL,
                session_count INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS device_registry (
                device_id VARCHAR(128) PRIMARY KEY,
                user_id VARCHAR(128) NOT NULL,
                fingerprint_hash VARCHAR(64) NOT NULL,
                attributes JSONB NOT NULL,
                trust_level VARCHAR(32) DEFAULT 'new',
                session_count INTEGER DEFAULT 1,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (user_id, fingerprint_hash)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS risk_ledger (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(128) NOT NULL,
                session_id VARCHAR(64),
                composite_score FLOAT NOT NULL,
                risk_tier VARCHAR(32) NOT NULL,
                action_taken VARCHAR(64) NOT NULL,
                breakdown JSONB NOT NULL,
                context_factors JSONB,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        ]
        with self.conn.cursor() as cur:
            for q in queries:
                cur.execute(q)
        logger.info("Database schema initialized.")

    def get_user_baseline(self, user_id: str) -> dict:
        """Fetch a user's behavioral baseline."""
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT behavioral_profile, session_count FROM user_baselines WHERE user_id = %s",
                (user_id,)
            )
            res = cur.fetchone()
            if res:
                return {
                    "profiles": res["behavioral_profile"],
                    "session_count": res["session_count"]
                }
            return {}

    def save_user_baseline(self, user_id: str, baseline_dict: dict):
        """Upsert a user's behavioral baseline."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_baselines (user_id, behavioral_profile, session_count, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET
                    behavioral_profile = EXCLUDED.behavioral_profile,
                    session_count = EXCLUDED.session_count,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (user_id, json.dumps(baseline_dict["profiles"]), baseline_dict.get("session_count", 0))
            )

    def get_user_devices(self, user_id: str) -> list[dict]:
        """Fetch all registered devices for a user."""
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM device_registry WHERE user_id = %s",
                (user_id,)
            )
            return cur.fetchall()

    def register_device(self, user_id: str, device_data: dict, trust_level: str):
        """Register a new device or update last_seen for an existing one."""
        fp_hash = device_data["fingerprint_hash"]
        attrs = json.dumps(device_data.get("attributes", {}))
        device_id = f"{user_id}_{fp_hash[:16]}"
        
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO device_registry (device_id, user_id, fingerprint_hash, attributes, trust_level, session_count)
                VALUES (%s, %s, %s, %s, %s, 1)
                ON CONFLICT (user_id, fingerprint_hash) DO UPDATE SET
                    last_seen = CURRENT_TIMESTAMP,
                    session_count = device_registry.session_count + 1;
                """,
                (device_id, user_id, fp_hash, attrs, trust_level)
            )

    def log_risk_event(self, event: dict):
        """Write an evaluation result to the risk ledger."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO risk_ledger (user_id, session_id, composite_score, risk_tier, action_taken, breakdown, context_factors)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    event["user_id"],
                    event.get("session_id"),
                    event["composite_risk_score"],
                    event["risk_tier"],
                    event["action"],
                    json.dumps(event.get("breakdown", {})),
                    json.dumps(event.get("context_factors", []))
                )
            )
