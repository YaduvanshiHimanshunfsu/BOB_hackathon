"""
ml_worker_daemon/policies/risk_policy.py
========================================
Policy engine that converts Composite Risk Scores into actionable decisions.
Uses the STANDARDIZED 4-tier threshold system (FIX 1).

Tiers:
  0-34   LOW      → ALLOW (silent pass-through, update baseline)
  35-54  MODERATE → CHALLENGE_SOFT (push notification, security question)
  55-74  HIGH     → CHALLENGE_HARD (SMS OTP, email verify, biometric)
  75-100 CRITICAL → DENY (session revoked, account locked, alert team)
"""

from shared.constants import RISK_TIERS, RISK_LOW_MAX, RISK_MODERATE_MAX, RISK_HIGH_MAX


class RiskPolicy:
    """
    Translates Composite Risk Scores into enforcement actions.
    Fully configurable via policy_config.yaml.
    """

    def __init__(self, custom_thresholds: dict = None):
        self.tiers = custom_thresholds or RISK_TIERS

    def evaluate(self, composite_risk_score: float) -> dict:
        """
        Evaluate a risk score and return the policy decision.

        Args:
            composite_risk_score: The fused CRS (0-100)

        Returns:
            Dict with tier, action, and enforcement details
        """
        score = round(composite_risk_score, 2)

        if score <= RISK_LOW_MAX:
            return {
                "tier": "LOW",
                "action": "ALLOW",
                "enforce": {
                    "block_session": False,
                    "require_mfa": False,
                    "notify_user": False,
                    "notify_admin": False,
                    "update_baseline": True,  # Safe to update
                    "log_level": "DEBUG",
                },
                "user_impact": "None — frictionless access",
                "score": score,
            }
        elif score <= RISK_MODERATE_MAX:
            return {
                "tier": "MODERATE",
                "action": "CHALLENGE_SOFT",
                "enforce": {
                    "block_session": False,
                    "require_mfa": False,
                    "require_push_confirm": True,
                    "require_security_question": True,
                    "notify_user": True,
                    "notify_admin": False,
                    "update_baseline": True,  # Still safe if challenge passes
                    "log_level": "INFO",
                },
                "user_impact": "Push notification confirmation or security question",
                "score": score,
            }
        elif score <= RISK_HIGH_MAX:
            return {
                "tier": "HIGH",
                "action": "CHALLENGE_HARD",
                "enforce": {
                    "block_session": False,
                    "require_mfa": True,
                    "mfa_methods": ["sms_otp", "email_verify", "biometric"],
                    "notify_user": True,
                    "notify_admin": True,
                    "update_baseline": False,  # Do NOT update on risky sessions
                    "log_level": "WARNING",
                },
                "user_impact": "SMS OTP, email verification, or biometric prompt required",
                "score": score,
            }
        else:
            return {
                "tier": "CRITICAL",
                "action": "DENY",
                "enforce": {
                    "block_session": True,
                    "revoke_token": True,
                    "lock_account_temp": True,
                    "lock_duration_minutes": 30,
                    "require_mfa": True,
                    "notify_user": True,
                    "notify_admin": True,
                    "alert_security_team": True,
                    "update_baseline": False,  # Absolutely never update
                    "create_incident": True,
                    "log_level": "CRITICAL",
                },
                "user_impact": "Session terminated, account temporarily locked, security team alerted",
                "score": score,
            }
