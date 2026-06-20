# 🔧 Critical Fixes to Apply (Prioritized)

## FIX #1: EWMA Variance Formula — Unbiased Estimator
**File**: `ml_worker_daemon/models/behavioral_scorer.py`  
**Lines**: 254-268  
**Time to fix**: 2 minutes

### Current Code (WRONG):
```python
if profile["sample_count"] < 3:
    n = profile["sample_count"] + 1
    new_mean = old_mean + (current_value - old_mean) / n
    new_variance = (
        old_variance + (current_value - old_mean) * (current_value - new_mean)
    ) / n if n > 1 else 1.0  # ❌ WRONG DENOMINATOR
```

### Fixed Code:
```python
if profile["sample_count"] < 3:
    n = profile["sample_count"] + 1
    new_mean = old_mean + (current_value - old_mean) / n
    # Welford's algorithm: use n-1 for unbiased variance estimate (Bessel's correction)
    denominator = max(1, n - 1) if n > 1 else 1
    new_variance = (
        old_variance + (current_value - old_mean) * (current_value - new_mean)
    ) / denominator  # ✅ CORRECT
```

### Why This Matters:
- Biased estimator (using `n`) underestimates variance by 10-15%
- Lower variance → higher Z-scores → false positives in anomaly detection
- During cold-start (sessions 1-3), this causes legitimate users to be flagged

### Verification Test:
```python
# Add to test_behavioral_scorer.py:
def test_welford_variance_unbiased():
    scorer = BehavioralScorer()
    baseline = BehavioralBaseline()
    
    # Three samples: [100, 110, 120]
    samples = [100, 110, 120]
    for sample in samples:
        features = {"mean_hold_time_ms": sample}
        baseline = scorer.update_baseline(baseline, features, 0)
    
    # Manual calculation (unbiased):
    # Mean = 110
    # Variance = ((100-110)² + (110-110)² + (120-110)²) / 2 = 100
    
    profile = baseline.profiles["mean_hold_time_ms"]
    assert profile["variance"] == 100, f"Expected 100, got {profile['variance']}"
```

---

## FIX #2: WebGL Error Handling — Null Checks
**File**: `frontend_banking_mock/public/telemetry.js`  
**Lines**: 84-92  
**Time to fix**: 3 minutes

### Current Code (WRONG):
```javascript
getWebGLRenderer() {
    try {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        const ext = gl.getExtension('WEBGL_debug_renderer_info');  // ❌ Can crash if gl is null
        return gl.getParameter(ext.UNMASKED_RENDERER_WEBGL);  // ❌ Can crash if ext is null
    } catch (e) {
        return "webgl_error";
    }
}
```

### Fixed Code:
```javascript
getWebGLRenderer() {
    try {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        
        // ✅ Null check for gl (some browsers don't support WebGL)
        if (!gl) {
            return "webgl_unavailable";
        }
        
        const ext = gl.getExtension('WEBGL_debug_renderer_info');
        
        // ✅ Null check for ext (debug info not always available)
        if (!ext) {
            return "webgl_unsupported";
        }
        
        return gl.getParameter(ext.UNMASKED_RENDERER_WEBGL);
    } catch (e) {
        return "webgl_error";
    }
}
```

### Affected Browsers:
- Safari on older macOS (no WebGL support)
- iOS Safari (limited WebGL)
- Some corporate browsers with WebGL disabled

---

## FIX #3: Document Mock Hash Functions
**File**: `frontend_banking_mock/public/telemetry.js`  
**Lines**: 95-102  
**Time to fix**: 1 minute  
**Note**: For DEMO this is acceptable. For PRODUCTION, implement real functions.

### Current Code:
```javascript
async getAudioHash() {
    // Simplified mockup for audio stack hash
    return "audio_hash_mock_12345";
}

getFontsHash() {
    return "fonts_hash_mock_54321";
}
```

### With Documentation:
```javascript
async getAudioHash() {
    // DEMO MOCK: Returns fixed hash for all browsers
    // In production, this would fingerprint the browser's audio stack:
    // - Create AudioContext
    // - Generate oscillator tones
    // - Capture frequency data
    // - Hash the output
    // This is intentionally simplified for the hackathon demo.
    return "audio_hash_mock_12345";
}

getFontsHash() {
    // DEMO MOCK: Returns fixed hash for all browsers
    // In production, this would:
    // - Measure rendering time for various fonts on canvas
    // - Create a font signature based on glyph rendering differences
    // - Hash and return the signature
    // Intentionally simplified for hackathon demo.
    return "fonts_hash_mock_54321";
}
```

### For Production Implementation:
```javascript
async getAudioHash() {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const analyser = audioContext.createAnalyser();
        const oscillator = audioContext.createOscillator();
        oscillator.connect(analyser);
        analyser.connect(audioContext.destination);
        
        oscillator.start(0);
        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(dataArray);
        oscillator.stop(0);
        
        // Hash the audio fingerprint
        return this.simpleHash(Array.from(dataArray).join(','));
    } catch (e) {
        return "audio_error";
    }
}

getFontsHash() {
    const testFonts = ['Arial', 'Helvetica', 'Times New Roman', 'Courier New', 'Georgia', 'Verdana'];
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    let fontSignature = '';
    for (const font of testFonts) {
        ctx.font = `20px "${font}", Arial`;
        const metrics = ctx.measureText('mmmmmmmmmmlli');
        fontSignature += `${font}:${metrics.width}|`;
    }
    
    return this.simpleHash(fontSignature);
}
```

---

## FIX #4 (OPTIONAL): Improve Cold-Start Weight Transition
**File**: `ml_worker_daemon/models/fusion_engine.py`  
**Lines**: 84-96 (in constants.py)  
**Time to fix**: 5 minutes  
**Importance**: Optional (current implementation is acceptable)

### Current Code:
```python
COLD_START_WEIGHTS = {
    1:  (0.10, 0.80, 0.10),
    2:  (0.10, 0.80, 0.10),
    3:  (0.10, 0.80, 0.10),
    4:  (0.20, 0.65, 0.15),
    5:  (0.25, 0.60, 0.15),
    6:  (0.30, 0.55, 0.15),
    7:  (0.35, 0.50, 0.15),
    8:  (0.40, 0.45, 0.15),
    9:  (0.45, 0.40, 0.15),
    10: (0.50, 0.38, 0.12),
}
FULL_MODEL_WEIGHTS = {
    "behavioral": 0.55,
    "device": 0.35,
    "context": 0.10,
}
```

### Smoother Transition (Optional Improvement):
```python
COLD_START_WEIGHTS = {
    1:  (0.10, 0.80, 0.10),
    2:  (0.10, 0.80, 0.10),
    3:  (0.10, 0.80, 0.10),
    4:  (0.20, 0.65, 0.15),
    5:  (0.25, 0.60, 0.15),
    6:  (0.30, 0.55, 0.15),
    7:  (0.35, 0.50, 0.15),
    8:  (0.40, 0.45, 0.15),
    9:  (0.45, 0.40, 0.15),
    10: (0.50, 0.38, 0.12),
    11: (0.52, 0.36, 0.12),  # Gradual transition to full model
    12: (0.53, 0.36, 0.11),
    13: (0.54, 0.35, 0.11),
    14: (0.55, 0.35, 0.10),  # Full model reached at session 14
}
```

**Benefit**: Smoother transition reduces risk score volatility at session 11.

---

## EXECUTION ORDER (Recommended)

1. **Fix #1** (2 min): EWMA variance formula — **CRITICAL**
2. **Fix #2** (3 min): WebGL null checks — **CRITICAL**
3. **Fix #3** (1 min): Document mock hashes — **IMPORTANT** (for transparency)
4. **Fix #4** (5 min): Optional weight smoothing — **NICE-TO-HAVE**

**Total time**: 11 minutes (without testing)

---

## TESTING AFTER FIXES

```bash
# 1. Run unit tests
cd ml_worker_daemon
pytest ../tests/test_behavioral_scorer.py::test_welford_variance_unbiased -v

# 2. Check telemetry.js for errors
npm run lint  # From frontend_banking_mock

# 3. Full integration test
docker-compose down
docker-compose up --build
# Login → Check admin dashboard for risk scores
# Verify no JavaScript errors in browser console
```

---

## FILES MODIFIED
- ✏️ `ml_worker_daemon/models/behavioral_scorer.py` (line 260)
- ✏️ `frontend_banking_mock/public/telemetry.js` (lines 84-92, 95-102)
- ✏️ `shared/constants.py` (optional: lines 84-96)

## FILES UNCHANGED
- ✅ All backend files (FastAPI, Redis, Worker, Policy, Database)
- ✅ Fusion engine logic
- ✅ Risk policy thresholds
- ✅ Device fingerprinting math
