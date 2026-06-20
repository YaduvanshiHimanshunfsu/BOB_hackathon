"""
ml_worker_daemon/worker.py
==========================
Main polling loop for the ML Worker Daemon.
Reads telemetry batches from Redis Streams, scores them,
updates PostgreSQL, and writes the final risk score back to Redis.
"""

import os
import time
import json
import redis
from shared.logger import get_logger
from shared.constants import REDIS_STREAM_KEY, REDIS_CONSUMER_GROUP, REDIS_CONSUMER_NAME_PREFIX
from ml_worker_daemon.database import Database
from ml_worker_daemon.baselines.baseline_manager import BaselineManager
from ml_worker_daemon.models.behavioral_scorer import BehavioralScorer
from ml_worker_daemon.models.device_fingerprint import DeviceFingerprintMatcher
from ml_worker_daemon.models.fusion_engine import FusionEngine
from ml_worker_daemon.policies.risk_policy import RiskPolicy

logger = get_logger("ml_worker")

class MLWorker:
    def __init__(self):
        # Redis
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db = int(os.getenv("REDIS_DB", "0"))
        self.redis_password = os.getenv("REDIS_PASSWORD", "")
        self.redis = redis.Redis(
            host=self.redis_host, port=self.redis_port, db=self.redis_db,
            password=self.redis_password or None, decode_responses=True
        )
        
        # Worker Config
        self.batch_size = int(os.getenv("WORKER_BATCH_SIZE", "50"))
        self.poll_interval = int(os.getenv("WORKER_POLL_INTERVAL_MS", "500")) / 1000.0
        self.consumer_name = f"{REDIS_CONSUMER_NAME_PREFIX}-{os.getpid()}"
        
        # Components
        self.db = Database()
        self.baseline_manager = BaselineManager(self.db)
        self.behavioral_scorer = BehavioralScorer()
        self.device_matcher = DeviceFingerprintMatcher()
        self.fusion_engine = FusionEngine()
        self.policy_engine = RiskPolicy()

    def setup(self):
        """Ensure DB is connected and Redis consumer group exists."""
        self.db.connect()
        try:
            self.redis.xgroup_create(REDIS_STREAM_KEY, REDIS_CONSUMER_GROUP, id="0", mkstream=True)
            logger.info(f"Created Redis consumer group '{REDIS_CONSUMER_GROUP}'")
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"Consumer group '{REDIS_CONSUMER_GROUP}' already exists.")
            else:
                raise e

    def process_payload(self, payload: dict) -> dict:
        """Core scoring pipeline for a single telemetry payload."""
        user_id = payload.get("user_id")
        session_id = payload.get("session_id")
        
        # Parse nested JSON strings from Redis
        behavioral_data = json.loads(payload.get("behavioral", "{}"))
        device_data = json.loads(payload.get("device", "{}"))
        
        # 1. Fetch historical context
        baseline = self.baseline_manager.get_baseline(user_id)
        registered_devices = self.db.get_user_devices(user_id)
        
        # 2. Score Behavioral
        behav_result = self.behavioral_scorer.score(behavioral_data, baseline)
        
        # 3. Score Device
        device_result = self.device_matcher.compute_device_score(device_data, registered_devices)
        
        # 4. Fuse Scores
        fusion_result = self.fusion_engine.fuse(
            behavioral_score=behav_result["behavioral_score"],
            device_score=device_result["device_score"],
            session_count=baseline.session_count,
            context={"local_hour": time.localtime().tm_hour} # Basic context for demo
        )
        
        # 5. Evaluate Policy
        policy_decision = self.policy_engine.evaluate(fusion_result["composite_risk_score"])
        
        # Compile full event
        full_event = {
            "user_id": user_id,
            "session_id": session_id,
            **fusion_result,
            **policy_decision
        }
        
        # 6. Apply Actions (Update baseline, register device, log to ledger)
        enforce = policy_decision.get("enforce", {})
        
        if enforce.get("update_baseline", False):
            updated_baseline = self.behavioral_scorer.update_baseline(
                baseline=baseline,
                features=behav_result["features"],
                session_risk_score=fusion_result["composite_risk_score"]
            )
            self.baseline_manager.save_baseline(user_id, updated_baseline)
            
        if self.device_matcher.should_register_device(device_result["device_score"], auth_passed=True):
            # In a real system, we wait for step-up auth to pass before registering.
            # For the pipeline flow, we register if allowed.
            pass # Simplification: Frontend handles registration trigger
            
        self.db.log_risk_event(full_event)
        
        # Cache the latest score in Redis for quick API reads
        cache_data = {
            k: str(v) if isinstance(v, (dict, list)) else v
            for k, v in full_event.items()
        }
        self.redis.hset(f"risk:{user_id}", mapping=cache_data)
        
        logger.info(
            f"Evaluated {user_id}: CRS={full_event['composite_risk_score']} "
            f"Tier={full_event['risk_tier']} Action={full_event['action']}",
            extra={"user_id": user_id, "risk_score": full_event['composite_risk_score'], "action": full_event['action']}
        )
        
        return full_event

    def run(self):
        """Main polling loop."""
        self.setup()
        logger.info(f"Worker {self.consumer_name} starting polling loop...")
        
        while True:
            try:
                # Read from Redis Stream (blocking for poll_interval)
                messages = self.redis.xreadgroup(
                    groupname=REDIS_CONSUMER_GROUP,
                    consumername=self.consumer_name,
                    streams={REDIS_STREAM_KEY: ">"},
                    count=self.batch_size,
                    block=int(self.poll_interval * 1000)
                )
                
                if not messages:
                    continue
                    
                for stream, records in messages:
                    for message_id, payload in records:
                        try:
                            self.process_payload(payload)
                            # Acknowledge message processing
                            self.redis.xack(REDIS_STREAM_KEY, REDIS_CONSUMER_GROUP, message_id)
                        except Exception as e:
                            logger.error(f"Error processing message {message_id}: {e}", exc_info=True)
                            
            except Exception as e:
                logger.error(f"Redis polling error: {e}", exc_info=True)
                time.sleep(1)

if __name__ == "__main__":
    worker = MLWorker()
    worker.run()
