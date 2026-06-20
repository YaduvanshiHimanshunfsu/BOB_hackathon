import os
import sys
import json
from datetime import datetime, timedelta

# Add parent dir to path to import shared
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.database import db

DEMO_USERS = [
    "himanshu_real",
    "alice_retail",
    "bob_corporate",
    "admin_deepak",
    "testuser123"
]

def seed_database():
    print("Seeding SQLite Database with mature ML Baselines for demo purposes...")
    
    # 1. Clear existing data to ensure a clean demo slate
    conn = db._get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_baselines")
    cursor.execute("DELETE FROM risk_ledger")
    conn.commit()
    conn.close()

    # 2. Forge perfect baselines for the 5 users
    for user_id in DEMO_USERS:
        # A fully mature baseline (Session count > 10)
        profiles = {
            "sample_count": 15,
            "flight_time_mean": 120.5,
            "flight_time_variance": 400.0,
            "hold_time_mean": 65.2,
            "hold_time_variance": 100.0,
            "mouse_velocity_mean": 1.2,
            "mouse_velocity_variance": 0.5,
            "last_updated": datetime.utcnow().isoformat()
        }

        # A "genuine" device footprint (Matching the Blue BOB Frontend)
        registered_devices = [
            {
                "canvas_hash": "2a64c4c2", # Hardcoded from real frontend
                "webgl_renderer": "Intel(R) UHD Graphics", # Standard
                "audio_hash": "3f8b9e1",
                "screen": "1920x1080x24",
                "timezone": "Asia/Calcutta",
                "language": "en-US",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "fonts_hash": "1111111111",
                "last_seen": (datetime.utcnow() - timedelta(hours=1)).isoformat()
            }
        ]

        save_data = {
            "profiles": profiles,
            "session_count": 15,
            "registered_devices": registered_devices
        }

        db.save_user_baseline(user_id, save_data)
        
        # 3. Add a couple of historical risk logs to make the dashboard look alive
        db.log_risk_event({
            "user_id": user_id,
            "session_id": "sess_historic_1",
            "timestamp": (datetime.utcnow() - timedelta(minutes=45)).isoformat(),
            "event_trigger": "login",
            "composite_risk_score": 12.4,
            "risk_tier": "LOW",
            "action": "ALLOW",
            "breakdown": {
                "behavioral_score": 10.1,
                "device_score": 5.2,
                "context_bonus": 0.0
            }
        })
        
        print(f"Pre-trained baselines injected for: {user_id}")

    print("\nDatabase fully seeded! You can now start the demo without worrying about the ML cold-start problem.")

if __name__ == "__main__":
    seed_database()
