# Mathematical Foundations of CIFE

This document outlines the core algorithms that power the Contextual Identity Fusion Engine. We explicitly avoid "black-box" Deep Learning models (LSTMs, Transformers) in favor of statistically grounded, highly explainable mathematical models.

## Why Not Deep Learning?
* **Cold-Start Problem**: Neural networks require 10,000+ samples per user to establish a reliable baseline. Our EWMA model establishes a baseline in 3-5 sessions and reaches full maturity in 10 sessions.
* **Explainability**: If a Neural Network flags a session, the explanation is "hidden layer weights shifted." If CIFE flags a session, the explanation is exactly: "User's keystroke flight time was 4.2 standard deviations slower than their 30-day baseline." This explainability is crucial for regulatory compliance in banking.

---

## 1. Behavioral Anomaly Detection (EWMA + Z-Score)

We track physiological interaction metrics (e.g., mean keystroke hold time). Let $x_t$ be the current observation of a feature.

### Exponentially Weighted Moving Average (EWMA) Baseline
The user's normal behavior profile is tracked using an EWMA, which adapts to gradual changes in behavior (e.g., getting a new keyboard) while filtering out noise.

$$ S_t = \alpha \cdot x_t + (1 - \alpha) \cdot S_{t-1} $$
$$ \sigma^2_t = \alpha \cdot (x_t - S_t)^2 + (1 - \alpha) \cdot \sigma^2_{t-1} $$

Where:
* $S_t$ is the smoothed mean baseline.
* $\sigma^2_t$ is the smoothed variance baseline.
* $\alpha = 0.1$ is the smoothing factor (gives 10% weight to current session, 90% to historical).

### Feature Z-Scoring
We determine how abnormal the current interaction is by calculating its Z-score against the EWMA baseline:

$$ Z_i = \frac{|x_{current} - S_t|}{\sigma_t} $$

### Aggregation & Scoring
We aggregate the Z-scores of all $N$ features using Root Mean Square (RMS) to ensure that a single extreme anomaly dominates the score:

$$ Z_{aggregate} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} Z_i^2} $$

The raw aggregate Z-score is mapped to a Behavioral Trust Score (BTS) on a 0-100 scale using an explicit formula with a ceiling of $Z=5.0$:

$$ \text{BehavioralScore} = \min\left(100, \left(\frac{Z_{aggregate}}{5.0}\right) \times 100\right) $$

---

## 2. Device Fingerprinting (Weighted Jaccard Similarity)

To detect device spoofing and emulator usage, we compare the current browser fingerprint against the registered device profile.

Standard Jaccard Similarity treats all attributes equally. We use **Weighted Jaccard Similarity** to assign higher importance to hardware-bound attributes that are difficult to spoof (e.g., GPU Canvas Hash) and lower importance to easily changed attributes (e.g., User Agent).

$$ J_{weighted}(A, B) = \frac{\sum w_i \cdot \mathbb{I}(f_i^A = f_i^B)}{\sum w_i} $$

Where:
* $w_i$ is the reliability weight of feature $i$ (e.g., Canvas_Hash $w=0.25$, User_Agent $w=0.07$).
* $\mathbb{I}$ is the indicator function (1 if match, 0 if mismatch).

The final Device Score maps similarity inversely to risk:

$$ \text{DeviceScore} = (1 - J_{weighted}) \times 100 $$

---

## 3. Score Fusion Engine

The final Composite Risk Score (CRS) is a weighted fusion of the component scores, plus any additive contextual risk penalties (e.g., impossible travel, off-hours access).

$$ \text{CRS} = (W_{behavioral} \cdot \text{BehavioralScore}) + (W_{device} \cdot \text{DeviceScore}) + \text{ContextBonus} $$

### Cold-Start Weight Schedule
During a new user's first few sessions, the behavioral baseline is incomplete. The system dynamically shifts weights to rely on device trust first, before transitioning to the full behavioral model.

| Sessions | Behavioral Weight | Device Weight | Dominant Signal |
|----------|-------------------|---------------|-----------------|
| 1-3      | 0.10              | 0.80          | Device          |
| 4-6      | 0.20              | 0.65          | Mixed           |
| 7-10     | 0.40              | 0.45          | Mixed           |
| 11+      | 0.55              | 0.35          | Behavioral      |

---

## Security Mitigations: Baseline Poisoning
**Attack**: An attacker slowly shifts their behavior over many sessions to manipulate the EWMA baseline into accepting them.
**Defense**: The system implements a strict conditional update rule. The baseline is **never updated** if the session's CRS is $\ge 30$. Abnormal sessions are discarded from the learning set.
