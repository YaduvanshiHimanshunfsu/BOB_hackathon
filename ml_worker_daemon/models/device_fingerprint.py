"""
ml_worker_daemon/models/device_fingerprint.py
=============================================
Device Trust Score computation using Weighted Jaccard Similarity.

Mathematical Foundation:
- Jaccard Similarity: J(A,B) = |A∩B| / |A∪B|
- Weighted Jaccard: J_w = Σ(w_i · 𝟙(f_i_current = f_i_baseline)) / Σ(w_i)
- Device Score: DeviceScore = (1 - J_weighted) × 100

Where attribute weights reflect signal reliability:
  Canvas Hash:    0.25 (GPU-specific, near-impossible to spoof)
  WebGL Renderer: 0.20 (hardware-bound)
  Audio Hash:     0.15 (audio stack fingerprint)
  Screen:         0.10 (moderately stable)
  Fonts Hash:     0.10 (system-specific)
  Timezone:       0.08 (easily changed but relevant)
  User Agent:     0.07 (easily spoofed, low weight)
  Language:       0.05 (soft signal)

Research References:
- FingerprintJS open-source library (fingerprintjs/fingerprintjs)
- Jaccard Similarity for Device Fingerprint Matching (London Met University)
- ThumbmarkJS — Privacy-conscious browser fingerprinting (MIT license)
"""

import hashlib
from typing import Optional
from shared.constants import DEVICE_ATTRIBUTE_WEIGHTS


class DeviceFingerprint:
    """Represents a single device's fingerprint."""

    def __init__(self, attributes: dict[str, str]):
        self.attributes = attributes
        self._fingerprint_hash = None

    @property
    def fingerprint_hash(self) -> str:
        """Generate a composite hash of all device attributes."""
        if self._fingerprint_hash is None:
            sorted_attrs = sorted(self.attributes.items())
            combined = "|".join(f"{k}={v}" for k, v in sorted_attrs)
            self._fingerprint_hash = hashlib.sha256(combined.encode()).hexdigest()[:32]
        return self._fingerprint_hash

    def to_dict(self) -> dict:
        return {
            "attributes": self.attributes,
            "fingerprint_hash": self.fingerprint_hash,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DeviceFingerprint":
        return cls(attributes=data.get("attributes", {}))


class DeviceFingerprintMatcher:
    """
    Computes Device Trust Score by comparing current device fingerprint
    against registered devices using Weighted Jaccard Similarity.

    A score of 0 = perfect match (trusted device).
    A score of 100 = zero overlap (completely unknown device).
    """

    def __init__(self, weights: dict[str, float] = None):
        self.weights = weights or DEVICE_ATTRIBUTE_WEIGHTS

    def weighted_jaccard_similarity(
        self, current: DeviceFingerprint, baseline: DeviceFingerprint
    ) -> float:
        """
        Compute Weighted Jaccard Similarity between two fingerprints.

        J_weighted = Σ(w_i · 𝟙(f_i^current = f_i^baseline)) / Σ(w_i)

        Unlike plain Jaccard (which treats all attributes equally), we
        assign higher weights to hardware-bound signals (canvas, WebGL)
        that are harder to spoof, and lower weights to easily-changed
        attributes (user agent, language).

        Returns:
            Float 0.0–1.0 where 1.0 = perfect match
        """
        total_weight = 0.0
        matched_weight = 0.0

        for attribute, weight in self.weights.items():
            total_weight += weight

            current_value = current.attributes.get(attribute, "")
            baseline_value = baseline.attributes.get(attribute, "")

            if current_value and baseline_value and current_value == baseline_value:
                matched_weight += weight

        return matched_weight / total_weight if total_weight > 0 else 0.0

    def compute_device_score(
        self,
        current_device: dict,
        registered_devices: list[dict],
    ) -> dict:
        """
        Compute Device Trust Score for a current device fingerprint.

        Logic:
        1. If user has no registered devices → score = 50 (first-time penalty)
        2. Compare against all registered devices
        3. Use the BEST match (highest Jaccard similarity)
        4. Convert to score: DeviceScore = (1 - J_weighted) × 100

        Args:
            current_device: Dict with device attribute values
            registered_devices: List of previously registered device dicts

        Returns:
            Dict with device_score, jaccard_similarity, is_new_device, etc.
        """
        current_fp = DeviceFingerprint(current_device)

        # Case 1: No registered devices (first-time user)
        if not registered_devices:
            return {
                "device_score": 50.0,  # Moderate penalty, not maximum
                "jaccard_similarity": 0.0,
                "is_new_device": True,
                "matched_device_hash": None,
                "trust_level": "new",
                "current_fingerprint_hash": current_fp.fingerprint_hash,
                "detail": "No registered devices. First-time penalty applied.",
            }

        # Case 2: Compare against all registered devices, find best match
        best_similarity = 0.0
        best_match_hash = None

        for reg_device_data in registered_devices:
            reg_fp = DeviceFingerprint(
                reg_device_data.get("attributes", reg_device_data)
            )
            similarity = self.weighted_jaccard_similarity(current_fp, reg_fp)

            if similarity > best_similarity:
                best_similarity = similarity
                best_match_hash = reg_fp.fingerprint_hash

        # Convert similarity to risk score
        device_score = (1.0 - best_similarity) * 100.0

        # Determine trust level and new device status
        if best_similarity >= 0.85:
            trust_level = "trusted"
            is_new = False
            detail = "Device matches registered fingerprint (minor drift acceptable)."
        elif best_similarity >= 0.50:
            trust_level = "known"
            is_new = False
            detail = "Partial match — possible browser/OS update on known device."
        else:
            trust_level = "new"
            is_new = True
            detail = "Device fingerprint does not match any registered device."

        return {
            "device_score": round(device_score, 2),
            "jaccard_similarity": round(best_similarity, 4),
            "is_new_device": is_new,
            "matched_device_hash": best_match_hash,
            "trust_level": trust_level,
            "current_fingerprint_hash": current_fp.fingerprint_hash,
            "detail": detail,
        }

    def should_register_device(
        self, device_score: float, auth_passed: bool
    ) -> bool:
        """
        Determine if a new device should be registered after successful auth.

        A device is registered only if:
        1. It's a new device (score >= 50)
        2. The user passed step-up authentication successfully
        """
        return device_score >= 50.0 and auth_passed
