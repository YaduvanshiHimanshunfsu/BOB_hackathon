"""
api_gateway/processor.py
========================
Replaces ml_worker_daemon/worker.py for Demo Mode.
Runs synchronously in a BackgroundTask.
"""

from datetime import datetime
import json
from shared.database import db
from ml_worker_daemon.models.behavioral_scorer import BehavioralScorer, BehavioralBaseline
from ml_worker_daemon.models.device_fingerprint import DeviceFingerprintMatcher
from ml_worker_daemon.models.fusion_engine import FusionEngine
from ml_worker_daemon.policies.risk_policy import RiskPolicy
from api_gateway.cache import risk_cache
from shared.logger import get_logger

logger = get_logger("SyncProcessor")

# We create instances once
behavioral_scorer = BehavioralScorer()
device_matcher = DeviceFingerprintMatcher()
fusion_engine = FusionEngine()
policy_engine = RiskPolicy()

def process_telemetry_payload(payload: dict):
    user_id = payload.get("user_id")
    session_id = payload.get("session_id")
    
    # Payload elements are already dicts coming from Pydantic schema
    behavioral_data = payload.get("behavioral", {})
    device_data = payload.get("device", {})
    
    logger.info(f"Processing telemetry for {user_id} (session: {session_id})")
    
    # 1. Fetch historical context from our SQLite DB
    raw_baseline = db.get_user_baseline(user_id)
    
    behavioral_baseline = BehavioralBaseline.from_dict(raw_baseline)
    registered_devices = raw_baseline.get("registered_devices", [])
    session_count = behavioral_baseline.session_count
    
    # 2. Compute individual scores
    # .score() returns a dict with 'behavioral_score', etc.
    behavioral_result = behavioral_scorer.score(
        behavioral_data, 
        behavioral_baseline
    )
    
    device_result = device_matcher.compute_similarity(
        device_data, 
        registered_devices
    )
    
    # 3. Fuse scores
    fusion_result = fusion_engine.fuse(
        behavioral_score=behavioral_result["behavioral_score"],
        device_score=device_result["device_score"],
        session_count=session_count,
        context={"event_trigger": payload.get("event_trigger")}
    )
    
    crs = fusion_result["composite_risk_score"]
    
    # 4. Policy evaluation
    policy_result = policy_engine.evaluate(crs)
    
    # 5. Build final record
    full_event = {
        "user_id": user_id,
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "event_trigger": payload.get("event_trigger"),
        "composite_risk_score": crs,
        "risk_tier": policy_result["tier"],
        "action": policy_result["action"],
        "breakdown": fusion_result["breakdown"]
    }
    
    # 6. Store in Database Ledger
    db.log_risk_event(full_event)
    
    # 7. Update Baseline (Only if not critical risk)
    # Get updated baseline object
    updated_baseline = behavioral_scorer.update_baseline(
        behavioral_baseline, 
        behavioral_result["features"], 
        crs
    )
    
    # In a real app we'd only register devices after explicit MFA auth success.
    # For the demo, we'll auto-register low-risk devices.
    if device_result["device_score"] >= 80.0:
        is_new = True
        for registered in registered_devices:
            if registered.get("canvas_hash") == device_data.get("canvas_hash"):
                is_new = False
                break
        if is_new:
            device_data["last_seen"] = datetime.utcnow().isoformat()
            registered_devices.append(device_data)
            
    # Serialize to save back to SQLite
    save_data = {
        "profiles": updated_baseline.profiles,
        "session_count": updated_baseline.session_count,
        "registered_devices": registered_devices
    }
    db.save_user_baseline(user_id, save_data)

    # 8. Cache for instant API reads
    risk_cache.set(f"risk:{user_id}", full_event)
    logger.info(f"Completed processing for {user_id}. Score: {crs:.1f} -> {policy_result['action']}")
