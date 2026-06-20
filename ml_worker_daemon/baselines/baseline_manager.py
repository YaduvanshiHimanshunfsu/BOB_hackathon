"""
ml_worker_daemon/baselines/baseline_manager.py
==============================================
Manages retrieval and storage of Behavioral Baseline objects.
Bridges the gap between raw DB dictionaries and the BehavioralBaseline class.
"""

from ml_worker_daemon.models.behavioral_scorer import BehavioralBaseline
from ml_worker_daemon.database import Database

class BaselineManager:
    def __init__(self, db: Database):
        self.db = db

    def get_baseline(self, user_id: str) -> BehavioralBaseline:
        """
        Fetch user's baseline from DB and convert to object.
        If user doesn't exist, returns a fresh, empty baseline.
        """
        raw_data = self.db.get_user_baseline(user_id)
        if not raw_data:
            return BehavioralBaseline()
        
        return BehavioralBaseline.from_dict(raw_data)

    def save_baseline(self, user_id: str, baseline: BehavioralBaseline):
        """
        Convert BehavioralBaseline object to dict and save to DB.
        """
        self.db.save_user_baseline(user_id, baseline.to_dict())
