"""
ml_worker_daemon/models/behavioral_scorer.py
=============================================
Behavioral Anomaly Detection Engine using Z-Score + EWMA.

Mathematical Foundation:
- EWMA Baseline: S_t = α · x_t + (1-α) · S_{t-1}
- EWMA Std Dev: σ_t = sqrt(α · (x_t - S_t)² + (1-α) · σ_{t-1}²)
- Z-Score: Z = |x_current - S_t| / σ_t
- Aggregation: Z_agg = sqrt(mean(Z_i²)) — RMS of feature Z-scores
- BTS Formula: BehavioralScore = min(100, (Z_agg / Z_CEILING) × 100)

FIX 3 APPLIED: Explicit Z-to-Score mapping formula using Z_CEILING = 5.0
FIX 5 APPLIED: Baseline update blocked when session CRS ≥ 30

Research References:
- BioCatch 2024 Digital Banking Fraud Trends in India
- FraudLens: Behavior Metrics–Based Fraud Detection (2026, IJSRSET)
- EWMA Control Charts for Statistical Process Control
"""

import math
import numpy as np
from typing import Optional
from shared.constants import (
    EWMA_ALPHA,
    Z_CEILING,
    BEHAVIORAL_FEATURES,
    BASELINE_UPDATE_BLOCK_THRESHOLD,
)


class BehavioralBaseline:
    """
    Stores the EWMA baseline for a single user's behavioral profile.

    Each behavioral feature has:
    - mean: EWMA-smoothed mean value
    - variance: EWMA-smoothed variance
    - session_count: number of sessions contributing to this baseline
    """

    def __init__(self, features: list[str] = None):
        self.features = features or BEHAVIORAL_FEATURES
        self.profiles = {}
        self.session_count = 0

        for feature in self.features:
            self.profiles[feature] = {
                "mean": 0.0,
                "variance": 1.0,  # Start with variance=1 to avoid division by zero
                "sample_count": 0,
            }

    def to_dict(self) -> dict:
        """Serialize baseline to dictionary for storage."""
        return {
            "profiles": self.profiles,
            "session_count": self.session_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BehavioralBaseline":
        """Deserialize baseline from stored dictionary."""
        baseline = cls()
        baseline.profiles = data.get("profiles", baseline.profiles)
        baseline.session_count = data.get("session_count", 0)
        return baseline


class BehavioralScorer:
    """
    Computes the Behavioral Trust Score (BTS) for a telemetry payload
    by comparing current behavioral features against the user's EWMA baseline.

    Scoring Pipeline:
    1. Extract features from raw telemetry
    2. Compute per-feature Z-scores against EWMA baseline
    3. Aggregate Z-scores using RMS (Root Mean Square)
    4. Map Z_aggregate to BehavioralScore using explicit formula

    FIX 3: BehavioralScore = min(100, (Z_aggregate / 5.0) × 100)
    """

    def __init__(self, alpha: float = EWMA_ALPHA):
        self.alpha = alpha

    def extract_features(self, behavioral_data: dict) -> dict[str, float]:
        """
        Extract numerical features from raw behavioral telemetry.

        Args:
            behavioral_data: Dict with 'keystrokes', 'mouse_events', etc.

        Returns:
            Dict mapping feature names to computed values
        """
        features = {}

        # --- Keystroke features ---
        keystrokes = behavioral_data.get("keystrokes", [])
        if keystrokes:
            hold_times = [k.get("hold_ms", 0) for k in keystrokes if k.get("hold_ms", 0) > 0]
            flight_times = [k.get("flight_ms", 0) for k in keystrokes if k.get("flight_ms", 0) > 0]

            features["mean_hold_time_ms"] = np.mean(hold_times) if hold_times else 0.0
            features["mean_flight_time_ms"] = np.mean(flight_times) if flight_times else 0.0
            features["keystroke_variance"] = np.std(hold_times) if len(hold_times) > 1 else 0.0
        else:
            features["mean_hold_time_ms"] = 0.0
            features["mean_flight_time_ms"] = 0.0
            features["keystroke_variance"] = 0.0

        # --- Mouse features ---
        mouse_events = behavioral_data.get("mouse_events", [])
        if mouse_events:
            velocities = [m.get("velocity", 0) for m in mouse_events if m.get("velocity", 0) > 0]
            features["mean_mouse_velocity"] = np.mean(velocities) if velocities else 0.0

            # Curvature ratio: compute path deviation from straight line
            if len(mouse_events) >= 2:
                actual_path = 0.0
                for i in range(1, len(mouse_events)):
                    dx = mouse_events[i].get("x", 0) - mouse_events[i-1].get("x", 0)
                    dy = mouse_events[i].get("y", 0) - mouse_events[i-1].get("y", 0)
                    actual_path += math.sqrt(dx**2 + dy**2)

                # Straight-line distance (first to last point)
                dx_total = mouse_events[-1].get("x", 0) - mouse_events[0].get("x", 0)
                dy_total = mouse_events[-1].get("y", 0) - mouse_events[0].get("y", 0)
                straight_line = math.sqrt(dx_total**2 + dy_total**2)

                features["mouse_curvature_ratio"] = (
                    actual_path / straight_line if straight_line > 0 else 1.0
                )
            else:
                features["mouse_curvature_ratio"] = 1.0
        else:
            features["mean_mouse_velocity"] = 0.0
            features["mouse_curvature_ratio"] = 1.0

        # --- Scroll features ---
        scroll_deltas = behavioral_data.get("scroll_delta_y", [])
        if scroll_deltas and len(scroll_deltas) > 1:
            # Shannon entropy of scroll pattern
            abs_deltas = [abs(d) for d in scroll_deltas if d != 0]
            if abs_deltas:
                total = sum(abs_deltas)
                probs = [d / total for d in abs_deltas]
                features["scroll_entropy"] = -sum(
                    p * math.log2(p) for p in probs if p > 0
                )
            else:
                features["scroll_entropy"] = 0.0
        else:
            features["scroll_entropy"] = 0.0

        return features

    def compute_z_scores(
        self, features: dict[str, float], baseline: BehavioralBaseline
    ) -> dict[str, float]:
        """
        Compute Z-score for each feature against the EWMA baseline.

        Z_i = |x_current - μ_EWMA| / σ_EWMA

        Args:
            features: Current session's extracted features
            baseline: User's EWMA baseline profile

        Returns:
            Dict mapping feature names to their Z-scores
        """
        z_scores = {}

        for feature_name in BEHAVIORAL_FEATURES:
            current_value = features.get(feature_name, 0.0)
            profile = baseline.profiles.get(feature_name, {"mean": 0, "variance": 1})

            mean = profile["mean"]
            std_dev = math.sqrt(max(profile["variance"], 1e-6))  # Avoid /0

            # Z-score: how many standard deviations away from baseline
            z = abs(current_value - mean) / std_dev if std_dev > 0 else 0.0
            z_scores[feature_name] = z

        return z_scores

    def aggregate_z_scores(self, z_scores: dict[str, float]) -> float:
        """
        Aggregate individual Z-scores using Root Mean Square (RMS).

        Z_aggregate = sqrt(mean(Z_i²))

        RMS preserves outliers better than arithmetic mean — a single
        extreme Z-score will dominate the aggregate, which is desired
        behavior for anomaly detection.
        """
        values = list(z_scores.values())
        if not values:
            return 0.0

        sum_of_squares = sum(z**2 for z in values)
        return math.sqrt(sum_of_squares / len(values))

    def z_to_behavioral_score(self, z_aggregate: float) -> float:
        """
        FIX 3: Explicit Z-to-BehavioralScore conversion formula.

        BehavioralScore = min(100, (Z_aggregate / Z_CEILING) × 100)

        Where Z_CEILING = 5.0, meaning:
            Z=0.0 → Score=0    (identical to baseline)
            Z=1.0 → Score=20   (normal variation)
            Z=2.0 → Score=40   (notable deviation)
            Z=3.0 → Score=60   (strong anomaly)
            Z=4.0 → Score=80   (likely different user)
            Z=5.0 → Score=100  (extreme — bot or attacker)
        """
        return min(100.0, (z_aggregate / Z_CEILING) * 100.0)

    def update_baseline(
        self,
        baseline: BehavioralBaseline,
        features: dict[str, float],
        session_risk_score: float,
    ) -> BehavioralBaseline:
        """
        Update the EWMA baseline with new observations.

        FIX 5: NEVER update the baseline if the session's Composite Risk
        Score (CRS) was ≥ BASELINE_UPDATE_BLOCK_THRESHOLD (default: 30).
        This prevents baseline poisoning attacks where an attacker gradually
        shifts the baseline to accept their behavior.

        EWMA Update Formulas:
            S_t = α · x_t + (1-α) · S_{t-1}
            σ²_t = α · (x_t - S_t)² + (1-α) · σ²_{t-1}
        """
        # FIX 5: Block baseline update on flagged sessions
        if session_risk_score >= BASELINE_UPDATE_BLOCK_THRESHOLD:
            return baseline  # Return unchanged baseline

        for feature_name in BEHAVIORAL_FEATURES:
            current_value = features.get(feature_name, 0.0)
            profile = baseline.profiles.get(
                feature_name, {"mean": 0, "variance": 1, "sample_count": 0}
            )

            old_mean = profile["mean"]
            old_variance = profile["variance"]

            if profile["sample_count"] < 3:
                # During first 3 samples, use simple averaging (not enough data for EWMA)
                n = profile["sample_count"] + 1
                new_mean = old_mean + (current_value - old_mean) / n
                new_variance = (
                    old_variance + (current_value - old_mean) * (current_value - new_mean)
                ) / (n - 1) if n > 1 else 1.0
            else:
                # EWMA update
                new_mean = self.alpha * current_value + (1 - self.alpha) * old_mean
                new_variance = (
                    self.alpha * (current_value - new_mean) ** 2
                    + (1 - self.alpha) * old_variance
                )

            baseline.profiles[feature_name] = {
                "mean": new_mean,
                "variance": max(new_variance, 1e-6),  # Floor to prevent zero variance
                "sample_count": profile["sample_count"] + 1,
            }

        baseline.session_count += 1
        return baseline

    def score(
        self, behavioral_data: dict, baseline: BehavioralBaseline
    ) -> dict:
        """
        Full scoring pipeline: extract → Z-score → aggregate → convert.

        Returns:
            Dict with behavioral_score, z_aggregate, z_scores, and features
        """
        # Step 1: Extract features from raw telemetry
        features = self.extract_features(behavioral_data)

        # Step 2: Compute per-feature Z-scores
        z_scores = self.compute_z_scores(features, baseline)

        # Step 3: Aggregate Z-scores (RMS)
        z_aggregate = self.aggregate_z_scores(z_scores)

        # Step 4: Convert to BehavioralScore (0-100)
        behavioral_score = self.z_to_behavioral_score(z_aggregate)

        return {
            "behavioral_score": round(behavioral_score, 2),
            "z_aggregate": round(z_aggregate, 4),
            "z_scores": {k: round(v, 4) for k, v in z_scores.items()},
            "features": {k: round(v, 4) for k, v in features.items()},
        }
