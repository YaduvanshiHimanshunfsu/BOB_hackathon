# CIFE: Contextual Identity Fusion Engine
**Bank of Baroda Hackathon Demo Guide**

## 🎯 The Core Problem
Traditional authentication relies on what a user *knows* (passwords, OTPs). The problem? Fraudsters can steal passwords and intercept OTPs via SIM swapping or phishing. Once they bypass the login screen, the bank trusts them completely. 

**CIFE** flips this paradigm. Instead of verifying what the user knows, CIFE continuously verifies **who the user is** by monitoring their behavioral biometrics and hardware footprint in real-time.

---

## 🧠 The Mathematical Approach
Instead of relying on heavy Deep Learning models that suffer from the "Cold Start" problem (requiring thousands of data points) and high compute costs, CIFE utilizes statistical anomaly detection optimized for edge computing:

1. **Unbiased Variance Modeling (Behavioral):**
   CIFE tracks keystroke flight times, hold times, and mouse velocity. By calculating the variance against a user's historical baseline, we detect when a session is hijacked. If a hacker logs into your account, they won't type at your exact cadence.
   
2. **Weighted Jaccard Similarity (Device Footprint):**
   We extract hardware-level signals (Canvas Hash, WebGL Renderer, Audio Hash, hardware concurrency). These are heavily weighted during a user's first few sessions to build trust, before smoothly transitioning trust weight to behavioral metrics as the baseline matures.

3. **Composite Risk Score (CRS):**
   These metrics are mathematically fused into a single risk score (0-100). 
   - **Low Risk (0-34):** Frictionless access.
   - **High Risk (55-74):** Triggers a Step-Up Authentication (OTP).
   - **Critical Risk (75+):** Immediate session termination.

---

## 💻 The Architecture
The project has been pivoted into an easy-to-run Demo Mode:
- **API Gateway (FastAPI):** Handles telemetry ingestion and routes data to the ML processor via asynchronous background tasks.
- **Data Persistence (SQLite):** Replaced distributed Redis/PostgreSQL with a robust SQLite ledger (`cife_demo.db`) for zero-configuration hackathon deployment.
- **Admin Dashboard (Streamlit):** Real-time monitoring for bank admins to visualize live risk scores and investigate anomalies.
- **Banking UI (React/Vite):** A mocked Bank of Baroda frontend that collects silent telemetry in the background.

---

## 🚀 How to Run the Demonstration

We have set up a **Dual-Environment Demo** to clearly illustrate how the engine protects against stolen credentials.

### 1. Start the Backend Infrastructure
Open two terminals at the project root:
```bash
# Terminal 1: Start the Core API Engine
uvicorn api_gateway.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start the Admin Risk Dashboard
python -m streamlit run admin_dashboard/app.py
```

### 2. Pre-Load the ML Baselines
To avoid the ML "Cold Start" problem during the presentation, execute the seeder script. This mathematically pre-trains 5 users (e.g., `himanshu_real`) with mature historical baselines:
```bash
python scripts/seed_demo_data.py
```

### 3. Launch the Dual Frontends
We provide two separate UIs:
- **The Genuine Bank (Blue Theme):** `cd frontend_banking_mock` -> `npm run dev` (Runs on Port 5173).
- **The Attacker/Phishing Bank (Red Theme):** `cd frontend_attacker_mock` -> `npm run dev` (Runs on Port 5174).

*(Note: The Attacker UI has been deliberately configured to emit spoofed hardware hashes, simulating a fraudster halfway across the world).*

### 4. The Live Presentation Flow
1. **The Safe Scenario:** Log into the Blue Genuine Bank as `himanshu_real`. Type normally. The Streamlit Dashboard will register a **LOW RISK** score, proving frictionless access for genuine users.
2. **The Credential Stuffing Scenario:** Log into the Red Attacker Bank as `himanshu_real`. The hardware hashes will immediately mismatch. The Streamlit Dashboard will instantly flag a **HIGH RISK** score, simulating a blocked transaction.
3. **The Insider Threat:** Log into the Blue Genuine Bank, but smash the keyboard randomly and move the mouse erratically. The engine detects the behavioral variance and halts the session.
