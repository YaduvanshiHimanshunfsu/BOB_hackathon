# CIFE - Contextual Identity Fusion Engine
**Bank of Baroda Hackathon Submission**

## 🎯 The Problem We Are Solving
In the digital banking world, traditional security relies heavily on passwords and One-Time Passwords (OTPs). However, these can be stolen, shared, or bypassed by scammers. This leads to three major problems:
1. **Account Takeover (ATO):** Hackers logging into a customer's account.
2. **KYC Fraud:** Scammers using stolen or synthetic identities to open accounts.
3. **High User Friction:** Making legitimate customers type OTPs for every small action ruins their banking experience.

## 💡 Our Solution: CIFE
**CIFE (Contextual Identity Fusion Engine)** is an invisible security guard that works in the background while the user is banking. Instead of asking for passwords repeatedly, it looks at *how* the person interacts with the bank.

It watches two main things:
1. **Behavioral Biometrics:** How fast do they type? How do they move their mouse? Is their scrolling smooth or jerky?
2. **Device Fingerprinting:** What exact hardware and browser are they using? (Down to the level of how their computer's graphics card draws an image).

When a user logs in or tries to transfer money, CIFE instantly gives them a **Composite Risk Score (from 0 to 100)**. 
- If the score is **LOW**, the user does their banking smoothly with no extra steps.
- If the score is **HIGH** (e.g., a hacker is typing 10 times faster than the real user, or using an unknown computer), CIFE stops the transaction and asks for a strict OTP or face scan.

---

## ⭐ Why CIFE is Built to Win (Key Features)

We built CIFE to be enterprise-ready. It solves the biggest problems that other AI systems fail at:

1. **Clear Math, Not Black-Box AI:** We use proven statistics (Z-Scores and Moving Averages) instead of complex Deep Learning. If the bank asks, "Why did you block this user?", CIFE can answer exactly: *"Because their keystroke speed was 3.5 times slower than normal."* This explainability is required for banking regulations.
2. **Smart Cold-Start:** When a user is brand new, we don't know how they type yet. CIFE smartly relies 80% on their Device hardware to secure them for the first 3 sessions, then slowly shifts to relying on their typing behavior as it learns their habits.
3. **Poisoning Defense:** What if a hacker tries to slowly change how they type so the AI accepts them? CIFE has a built-in block: if a session is marked as risky, the AI refuses to learn from it. The baseline stays safe.
4. **Battery and Privacy Friendly:** CIFE only collects data silently every 30 seconds, so it won't drain mobile batteries. But the moment a user clicks "Transfer Funds," it instantly sends an alert to check if they are safe.
5. **Real Security:** We don't pretend to encrypt data in the browser (which hackers can easily break). We rely entirely on the gold standard: TLS 1.3 network security.

---

## 🏗️ How We Built It (Technical Stack)

We split the project into specialized microservices to handle thousands of users without slowing down the bank.

* **Frontend Banking Portal (React, Vite, Tailwind):** A beautiful, mock digital bank where users can log in and transfer funds.
* **The "Spy" Script (Vanilla JavaScript):** A tiny `telemetry.js` file embedded in the frontend that silently watches keystrokes and mouse movements.
* **The API Gateway (Python, FastAPI):** The front door. It receives the data from the user's browser in less than 5 milliseconds.
* **The Waiting Room (Redis Streams):** A super-fast message queue. It holds the data so the API doesn't get jammed during high traffic.
* **The Brain (Python ML Worker):** A background worker that pulls data from Redis, crunches the complex math, and calculates the final Risk Score.
* **The Memory Bank (PostgreSQL):** A secure database that remembers how every user normally behaves.
* **The Command Center (Streamlit, Plotly):** A live dashboard for bank security teams to watch risk heatmaps and see exactly which devices are acting suspiciously.

---

## ⚙️ The Four-Tier Policy Engine
Once the Brain calculates the Risk Score (0-100), it takes immediate action based on our strict bank policy:

* 🟢 **LOW Risk (0 to 34):** `ALLOW` - User is trusted. Frictionless experience.
* 🟡 **MODERATE Risk (35 to 54):** `CHALLENGE_SOFT` - Ask a security question.
* 🟠 **HIGH Risk (55 to 74):** `CHALLENGE_HARD` - Force an SMS OTP or email verification.
* 🔴 **CRITICAL Risk (75 to 100):** `DENY` - Block the session instantly and alert the security team.

---

## 📁 What's Inside This Repository?
```text
.
├── admin_dashboard/       # The live security team command center
├── api_gateway/           # The fast API that receives user data
├── docs/                  # Deep-dive explanations of the Math and Architecture
├── frontend_banking_mock/ # The fake Bank of Baroda website for demoing
├── ml_worker_daemon/      # The background AI brain calculating the math
├── shared/                # Code shared across all parts of the system
└── docker-compose.yml     # The blueprint to start the whole system at once
```

---

## 🚀 How to Run It (For Judges and Developers)

You need **Docker** installed on your computer.

1. **Download the code:** Clone this repository to your computer.
2. **Start the engines:** Open your terminal in this folder and run:
   ```bash
   docker-compose up --build
   ```
3. **Open the Apps:**
   * **The Bank Website:** Go to `http://localhost:5173`
   * **The Security Dashboard:** Go to `http://localhost:8501`
   * **The Developer API:** Go to `http://localhost:8000/docs`

### 📖 Want to learn more?
Check out the `docs/` folder!
* Read [Architecture Guide](docs/architecture.md) to see a diagram of how data flows.
* Read [Mathematical Foundations](docs/math_foundations.md) to see the exact formulas we use to catch hackers.
