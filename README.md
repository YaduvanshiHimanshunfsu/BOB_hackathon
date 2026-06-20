# CIFE - Contextual Identity Fusion Engine
**Bank of Baroda Hackathon Submission**

## 🎯 Goal
Design a privacy-first, risk-based Identity Trust framework that continuously validates customer and enterprise identities across digital channels. CIFE detects high-risk events such as anomalous behavior, new device usage, and account takeover attempts, triggering real-time verification only when risk levels are elevated. The result: reduced fraud, frictionless access for legitimate users, and comprehensive auditability.

## 💡 The Solution: Behavioral Biometrics + Device Trust
Instead of relying solely on static passwords or annoying OTPs, CIFE operates invisibly in the background. It learns *how* a user types, how they move their mouse, and exactly what hardware they use. 

When a user logs in, CIFE calculates a **Composite Risk Score (0-100)** in real-time. If the score is LOW, the user passes through frictionlessly. If the score spikes (e.g. a bot is typing at inhuman speeds, or a fraudster is using a spoofed device), CIFE intercepts the transaction and forces a step-up challenge (MFA/OTP).

### Key Differentiators
1. **Explainable AI**: We use statistically grounded EWMA and Z-Score mathematics instead of "black-box" Deep Learning. This ensures that every security decision is fully explainable for banking regulatory compliance.
2. **Cold-Start Resilience**: Uses a dynamic weight schedule. In sessions 1-3, device fingerprinting dominates. By session 11+, behavioral biometrics lead.
3. **Poisoning Defense**: The baseline learning model automatically halts updates during suspicious sessions to prevent attackers from slowly training the system to accept their behavior.

## 🏗️ Technical Stack
* **Frontend Mock**: React, Vite, TailwindCSS (Digital Banking Portal Mockup)
* **Telemetry Engine**: Vanilla JavaScript (Embedded tracker)
* **API Gateway**: FastAPI, Pydantic (High-throughput ingestion)
* **Message Broker**: Redis Streams (Decouples ingestion from processing)
* **ML Worker Daemon**: Python, NumPy (Math processing engine)
* **Database**: PostgreSQL (EWMA baseline storage & risk ledger)
* **Admin Dashboard**: Streamlit, Plotly (Real-time fraud command center)
* **Infrastructure**: Docker Compose (Containerized orchestration)

## ⚙️ How It Works (The Flow)
1. **Passive Telemetry**: `telemetry.js` passively collects keystroke dynamics (hold/flight times) and device hardware hashes (Canvas, WebGL), securely sending them to the API via TLS 1.3 every 30 seconds.
2. **Ingestion**: The FastAPI gateway validates the schema and rapidly drops the payload into a Redis Stream queue (<5ms response).
3. **Scoring**: The ML Worker daemon pulls from Redis, fetches the user's historical baseline from PostgreSQL, and calculates the behavioral deviation (Z-score) and device similarity (Weighted Jaccard).
4. **Policy Evaluation**: The fused score is checked against a standardized 4-Tier Policy:
   * **LOW (0-34)**: ALLOW
   * **MODERATE (35-54)**: CHALLENGE_SOFT (Security Question)
   * **HIGH (55-74)**: CHALLENGE_HARD (OTP)
   * **CRITICAL (75-100)**: DENY (Lock Session)
5. **Action**: The frontend polls the risk API and intercepts the transaction if a challenge is required.

## 📁 Repository Structure
```text
.
├── admin_dashboard/       # Streamlit visual command center
├── api_gateway/           # FastAPI ingestion endpoints
├── docs/                  # Architecture & Math documentation
├── frontend_banking_mock/ # React Vite banking portal UI
├── ml_worker_daemon/      # Background risk calculation engine
├── shared/                # Shared constants, thresholds, and loggers
└── docker-compose.yml     # Orchestration
```

## 🚀 Getting Started

### Prerequisites
* Docker and Docker Compose installed.

### Run the Full Stack
1. Clone the repository.
2. Spin up the architecture:
   ```bash
   docker-compose up --build
   ```
3. Access the services:
   * **Digital Banking Frontend**: `http://localhost:5173`
   * **Admin Dashboard**: `http://localhost:8501`
   * **API Swagger Docs**: `http://localhost:8000/docs`

## 📖 Further Reading
Please see the `docs/` folder for deep dives into the system design:
* [Architecture Guide](docs/architecture.md)
* [Mathematical Foundations](docs/math_foundations.md)
