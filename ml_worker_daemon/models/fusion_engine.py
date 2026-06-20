"""
ml_worker_daemon/models/fusion_engine.py
========================================
Score Fusion Engine — combines Behavioral Score, Device Score,
and Contextual Bonuses into a single Composite Risk Score (CRS).

Fusion Formula:
  CRS = w_b × BehavioralScore + w_d × DeviceScore + ContextBonus

Cold-Start Weight Schedule (addresses reviewer's cold-start concern):
  Sessions 1-3:  (0.10, 0.80, 0.10) — Device dominates
  Sessions 4-6:  (0.20-0.30, 0.55-0.65, 0.15)
  Sessions 7-10: (0.35-0.50, 0.38-0.50, 0.12-0.15)
  Session 11+:   (0.55, 0.35, 0.10) — Full model (behavioral leads)

This gradual ramp addresses the reviewer's concern:
"First 3 sessions, device risk dominates (0.75 weight on DTS);
sessions 4-10, gradual shift; session 11+, full model."
"""

import time
from shared.constants import (
    COLD_START_WEIGHTS,
    FULL_MODEL_WEIGHTS,
    BASELINE_MIN_SESSIONS_FOR_FULL_MODEL,
    CONTEXT_BONUSES,
)


class FusionEngine:
    """
    Fuses behavioral anomaly score and device trust score into
    a single Composite Risk Score (CRS) between 0–100.
    """

    def get_weights(self, session_count: int) -> tuple[float, float, float]:
        """
        Get the fusion weights based on user's session history.

        During cold-start (sessions 1-10), device score dominates because
        behavioral baseline is still being established. As more sessions
        accumulate, behavioral weight increases.

        Args:
            session_count: Number of completed sessions for this user

        Returns:
            Tuple of (behavioral_weight, device_weight, context_weight)
        """
        if session_count >= BASELINE_MIN_SESSIONS_FOR_FULL_MODEL:
            return (
                FULL_MODEL_WEIGHTS["behavioral"],
                FULL_MODEL_WEIGHTS["device"],
                FULL_MODEL_WEIGHTS["context"],
            )

        # Use cold-start schedule
        return COLD_START_WEIGHTS.get(
            max(1, session_count),
            (0.10, 0.80, 0.10),  # Default for unknown session count
        )

    def compute_context_bonus(self, context: dict) -> tuple[float, list[str]]:
        """
        Compute contextual risk bonus based on environmental signals.

        Each factor adds a fixed number of points to the CRS if triggered.
        Multiple factors can stack.

        Args:
            context: Dict with contextual signals (time, geo, transaction, etc.)

        Returns:
            Tuple of (total_bonus_points, list_of_triggered_factors)
        """
        total_bonus = 0.0
        triggered = []

        # Off-hours access (1 AM – 5 AM local time)
        hour = context.get("local_hour")
        if hour is not None and (1 <= hour <= 5):
            total_bonus += CONTEXT_BONUSES["off_hours"]
            triggered.append("off_hours_access")

        # Geo-velocity violation (impossible travel)
        if context.get("geo_velocity_violation", False):
            total_bonus += CONTEXT_BONUSES["geo_velocity"]
            triggered.append("geo_velocity_violation")

        # High-value transaction (> ₹50,000)
        txn_amount = context.get("transaction_amount", 0)
        if txn_amount > 50000:
            total_bonus += CONTEXT_BONUSES["high_value_txn"]
            triggered.append("high_value_transaction")

        # Rapid successive logins (> 3 in 10 min)
        if context.get("rapid_logins", False):
            total_bonus += CONTEXT_BONUSES["rapid_logins"]
            triggered.append("rapid_successive_logins")

        # VPN/Proxy detected
        if context.get("vpn_proxy_detected", False):
            total_bonus += CONTEXT_BONUSES["vpn_proxy_detected"]
            triggered.append("vpn_proxy_detected")

        return total_bonus, triggered

    def fuse(
        self,
        behavioral_score: float,
        device_score: float,
        session_count: int,
        context: dict = None,
    ) -> dict:
        """
        Fuse all scores into the final Composite Risk Score (CRS).

        Formula:
          CRS = w_b × BehavioralScore + w_d × DeviceScore + ContextBonus
          CRS = clamp(CRS, 0, 100)

        Args:
            behavioral_score: Score from BehavioralScorer (0-100)
            device_score: Score from DeviceFingerprintMatcher (0-100)
            session_count: User's total session count (for weight selection)
            context: Optional contextual signals dict

        Returns:
            Dict with composite_risk_score, tier, action, weight breakdown
        """
        context = context or {}

        # Get session-appropriate weights
        w_b, w_d, w_c = self.get_weights(session_count)

        # Compute context bonus
        context_bonus, triggered_factors = self.compute_context_bonus(context)

        # Weighted fusion
        weighted_behavioral = w_b * behavioral_score
        weighted_device = w_d * device_score
        # Context bonus is additive (not weighted — it's a flat risk adjustment)
        composite = weighted_behavioral + weighted_device + context_bonus

        # Clamp to 0-100
        composite = max(0.0, min(100.0, composite))

        # Determine risk tier and action (FIX 1: standardized 4-tier)
        if composite <= 34:
            tier = "LOW"
            action = "ALLOW"
        elif composite <= 54:
            tier = "MODERATE"
            action = "CHALLENGE_SOFT"
        elif composite <= 74:
            tier = "HIGH"
            action = "CHALLENGE_HARD"
        else:
            tier = "CRITICAL"
            action = "DENY"

        return {
            "composite_risk_score": round(composite, 2),
            "risk_tier": tier,
            "action": action,
            "breakdown": {
                "behavioral_score": round(behavioral_score, 2),
                "device_score": round(device_score, 2),
                "context_bonus": round(context_bonus, 2),
                "weighted_behavioral": round(weighted_behavioral, 2),
                "weighted_device": round(weighted_device, 2),
            },
            "weights_used": {
                "behavioral": w_b,
                "device": w_d,
                "context": w_c,
                "session_count": session_count,
                "is_cold_start": session_count < BASELINE_MIN_SESSIONS_FOR_FULL_MODEL,
            },
            "context_factors": triggered_factors,
            "timestamp": time.time(),
        }
