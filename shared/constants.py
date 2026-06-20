"""
shared/constants.py
===================
Central configuration constants for the Contextual Identity Fusion Engine (CIFE).

ALL 5 CRITICAL FIXES FROM REVIEW ARE APPLIED HERE:
  Fix 1: Single 4-tier policy threshold (standardized)
  Fix 2: No client-side AES claim — TLS 1.3 only
  Fix 3: Explicit BTS formula (Z-score → BehavioralScore)
  Fix 4: Telemetry frequency: 30s passive + event-triggered
  Fix 5: Conditional baseline update rule (no update on flagged sessions)
"""

# =============================================================================
# FIX 1: STANDARDIZED 4-TIER RISK POLICY THRESHOLDS
# Used consistently across ALL modules — API, Worker, Dashboard, Frontend
# =============================================================================
RISK_TIERS = {
    "LOW":      {"min": 0,  "max": 34,  "action": "ALLOW",     "label": "Low Risk"},
    "MODERATE": {"min": 35, "max": 54,  "action": "CHALLENGE_SOFT", "label": "Moderate Risk"},
    "HIGH":     {"min": 55, "max": 74,  "action": "CHALLENGE_HARD", "label": "High Risk"},
    "CRITICAL": {"min": 75, "max": 100, "action": "DENY",      "label": "Critical Risk"},
}

# Flattened thresholds for quick comparisons
RISK_LOW_MAX = 34
RISK_MODERATE_MAX = 54
RISK_HIGH_MAX = 74
# Anything above 74 is CRITICAL


# =============================================================================
# FIX 3: EXPLICIT BTS (Behavioral Trust Score) FORMULA
# Converts Z_aggregate → BehavioralScore (0–100)
#
# Formula:  BehavioralScore = min(100, (Z_aggregate / Z_CEILING) × 100)
#
# Where Z_CEILING = 5.0 (a Z-score of 5.0+ maps to maximum risk = 100)
# This means:
#   Z=0.0 → Score=0,   Z=1.0 → Score=20,  Z=2.0 → Score=40
#   Z=3.0 → Score=60,  Z=4.0 → Score=80,  Z=5.0+ → Score=100
# =============================================================================
Z_CEILING = 5.0  # Z-score at which BehavioralScore saturates to 100


# =============================================================================
# FIX 4: TELEMETRY FREQUENCY
# Passive: every 30 seconds (battery-friendly, privacy-respecting)
# Event-triggered: immediately on critical actions
# =============================================================================
TELEMETRY_PASSIVE_INTERVAL_SEC = 30  # Background collection interval
TELEMETRY_CRITICAL_EVENTS = [
    "login",
    "fund_transfer_initiate",
    "beneficiary_add",
    "password_change",
    "otp_page_load",
    "profile_update",
    "logout",
]


# =============================================================================
# FIX 5: CONDITIONAL BASELINE UPDATE RULE
# NEVER update the EWMA baseline if the session's Composite Risk Score (CRS)
# was ≥ this threshold. Prevents baseline poisoning attacks.
# =============================================================================
BASELINE_UPDATE_BLOCK_THRESHOLD = 30  # Don't update baseline if CRS ≥ 30
BASELINE_MIN_SESSIONS_FOR_FULL_MODEL = 10  # Sessions needed before full model trust


# =============================================================================
# EWMA (Exponentially Weighted Moving Average) PARAMETERS
# =============================================================================
EWMA_ALPHA = 0.1  # Smoothing factor — lower = slower adaptation, more stable
# α = 0.1 means: 10% weight to new observation, 90% to historical baseline
# Effective memory: ~1/α = 10 sessions


# =============================================================================
# COLD-START WEIGHT SCHEDULE
# During early sessions, device score dominates; behavioral gradually ramps up
# =============================================================================
COLD_START_WEIGHTS = {
    # session_count: (behavioral_weight, device_weight, context_weight)
    1:  (0.10, 0.80, 0.10),  # Session 1-3: Device dominates (new user)
    2:  (0.10, 0.80, 0.10),
    3:  (0.10, 0.80, 0.10),
    4:  (0.20, 0.65, 0.15),  # Session 4-6: Behavioral ramps up
    5:  (0.25, 0.60, 0.15),
    6:  (0.30, 0.55, 0.15),
    7:  (0.35, 0.50, 0.15),  # Session 7-10: Approaching full model
    8:  (0.40, 0.45, 0.15),
    9:  (0.45, 0.40, 0.15),
    10: (0.50, 0.38, 0.12),
}
# Session 11+: Full model weights below
FULL_MODEL_WEIGHTS = {
    "behavioral": 0.55,
    "device": 0.35,
    "context": 0.10,
}


# =============================================================================
# DEVICE FINGERPRINT — WEIGHTED JACCARD ATTRIBUTE WEIGHTS
# Higher weight = harder to spoof, more reliable signal
# =============================================================================
DEVICE_ATTRIBUTE_WEIGHTS = {
    "canvas_hash":    0.25,  # GPU-specific rendering — near-impossible to spoof
    "webgl_renderer": 0.20,  # Hardware-bound GPU string
    "audio_hash":     0.15,  # Audio stack fingerprint
    "screen":         0.10,  # Resolution + color depth
    "fonts_hash":     0.10,  # System-installed fonts
    "timezone":       0.08,  # Timezone (easily changed but still signal)
    "user_agent":     0.07,  # Browser UA — easily spoofed, low weight
    "language":       0.05,  # Browser language preference
}


# =============================================================================
# BEHAVIORAL FEATURES TRACKED
# =============================================================================
BEHAVIORAL_FEATURES = [
    "mean_hold_time_ms",       # Average key press duration
    "mean_flight_time_ms",     # Average gap between keystrokes
    "keystroke_variance",      # Consistency of typing rhythm
    "mean_mouse_velocity",     # Average cursor speed (px/ms)
    "mouse_curvature_ratio",   # Deviation from straight-line paths
    "scroll_entropy",          # Randomness in scroll behavior
]


# =============================================================================
# CONTEXTUAL BONUS FACTORS (additive to final risk score)
# =============================================================================
CONTEXT_BONUSES = {
    "off_hours":           8,   # Login between 1 AM – 5 AM local time
    "geo_velocity":        15,  # Impossible travel speed detected
    "high_value_txn":      5,   # Transaction > ₹50,000
    "rapid_logins":        10,  # > 3 logins in 10 minutes
    "vpn_proxy_detected":  7,   # IP flagged as datacenter/proxy
}


# =============================================================================
# REDIS STREAM CONFIGURATION
# =============================================================================
REDIS_STREAM_KEY = "telemetry_stream"
REDIS_CONSUMER_GROUP = "ml_workers"
REDIS_CONSUMER_NAME_PREFIX = "worker"


# =============================================================================
# API RATE LIMITING
# =============================================================================
RATE_LIMIT_PER_MINUTE = 60  # Max telemetry payloads per user per minute


# =============================================================================
# FIX 2: TRANSPORT SECURITY STATEMENT
# No client-side AES encryption. All telemetry transmitted over TLS 1.3.
# Client-side encryption with JS-embedded keys provides zero actual security
# (key extractable via DevTools). TLS provides authenticated encryption in
# transit. At rest, PostgreSQL encryption handles data protection.
# =============================================================================
TRANSPORT_SECURITY = "TLS 1.3"  # All HTTP endpoints must enforce HTTPS
