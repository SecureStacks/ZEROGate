# ZERO GATE — Zero Trust Network Access (ZTNA) Simulator

> **Hackathon Track: PS-12 — Network & Perimeter Security**  
> A Next.js and FastAPI platform simulating continuous, context-aware, least-privilege Zero Trust Network Access (ZTNA) adhering to NIST SP 800-207.

---

## 1. The Problem
Traditional Virtual Private Networks (VPNs) and perimeter-based security models grant broad, implicit network trust. Once an entity authenticates and crosses the perimeter, they are trusted to move laterally across the network. If credentials are stolen or a device is compromised, this implicit trust leads to devastating data breaches.

## 2. The Solution
ZeroGate provides continuous, context-aware, least-privilege application access. Instead of granting network access, ZeroGate acts as a secure broker that evaluates every single access request based on identity, device posture, location, and risk signals before granting access to a specific protected resource.

## 3. Core Architecture
The ZeroGate authorization pipeline operates as follows:

```
User / Device
     ↓
Access Request
     ↓
PEP / ZTNA Gateway
     ↓
Context + Risk Engine (Evaluates signals, scores 0-100)
     ↓
PDP / Policy Engine (ALLOW / MFA_REQUIRED / DENY)
     ↓
[If MFA_REQUIRED] → Adaptive MFA Challenge → Verified
     ↓
[If Verified] → PDP Re-evaluation
     ↓
Microsegmentation Engine (Validates East-West Traffic)
     ↓
[Final Enforcement] → PEP (Access Granted / Blocked)
     ↓
Protected Resource
     ↓
Audit Event Logged
```

## 4. Core Features
- **Context-aware authorization:** Validates user role, device posture, network type, and geographic location dynamically.
- **Risk scoring:** Deterministic risk engine scoring requests from 0 to 100 based on threat anomalies.
- **Policy Decision Point (PDP):** Determines authorization based on strict priority-based rules.
- **Policy Enforcement Point (PEP):** Strictly enforces PDP decisions.
- **Adaptive MFA:** Dynamically challenges users if risk is elevated, triggering a PDP re-evaluation.
- **Microsegmentation:** Enforces granular lateral movement restrictions regardless of identity.
- **Defense-in-depth:** Overlapping security mechanisms ensuring no single point of failure.
- **Policy Console:** Manage and simulate policies without impacting live traffic.
- **Live Topology:** Backend-driven enforcement graph visualization.
- **Audit Logs:** Deep visibility into granular enforcement event contexts.
- **Dashboard & Access Simulator:** Interactive UI to demonstrate real-time dynamic policy evaluation.

## 5. Technology Stack
- **Backend:** FastAPI, Python 3.12, SQLAlchemy, SQLite/PostgreSQL, Pytest.
- **Frontend:** Next.js 14, React, Tailwind CSS, Lucide React.
- **Infrastructure:** Docker, Docker Compose.

## 6. Project Structure
- `/backend`: Core FastAPI application, database models, policies, risk engine, and test suite.
- `/frontend`: Next.js web application for the Dashboard and Simulator.
- `/docs`: Demo script and presentation content.
- `docker-compose.yml`: Containerized setup.

## 7. Local Setup
### Prerequisites
- Node.js v18+ and npm v9+
- Python 3.11+

### 8. How to run Backend
```bash
cd backend
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*API runs at http://localhost:8000 (Swagger UI at `/docs`)*

### 9. How to run Frontend
```bash
cd frontend
npm install
npm run dev
```
*Frontend runs at http://localhost:3000*

### 10. Docker Setup
To run the entire stack in containers (with PostgreSQL):
```bash
docker compose up --build
```

### 11. How to run Tests
```bash
# Backend
cd backend
pytest -v

# Frontend
cd frontend
npm test
npm run build
```

## 12. Demo Scenarios
Navigate to `http://localhost:3000/simulator` to run interactive scenarios:
1. **Scenario A (Normal Access):** Developer -> Healthy Device -> Low Risk -> **ACCESS GRANTED**.
2. **Scenario B (Adaptive MFA):** Elevated Risk -> Step-Up MFA Challenge -> Verified -> PDP Re-evaluates -> **ACCESS GRANTED**.
3. **Scenario C (Compromised Device):** High Risk Compromised Device -> PDP issues hard **DENY** -> **ACCESS BLOCKED**.
4. **Scenario D (Lateral Movement):** Successful MFA -> PDP allows -> Microsegmentation blocks East-West movement -> **ACCESS BLOCKED** (Defense-in-Depth).

## 13. Security Invariants
ZeroGate strictly enforces the following security properties:
- **MFA cannot bypass PDP DENY:** If a hard block is issued, MFA cannot override it.
- **MFA cannot bypass segmentation:** Network segments are authoritative.
- **Compromised devices remain blocked:** Immediate containment.
- **Malicious IPs remain blocked.**
- **Disabled users/resources remain blocked.**
- **Default deny remains active:** If no policy matches, access is blocked.
- **Policy priority remains deterministic:** Lowest integer has highest precedence.
- **Frontend does not independently authorize requests:** All decisions are cryptographically enforced on the backend.

## 14. Phase 9 Validation
End-to-End integration testing was strictly enforced using `pytest`.
- **72 / 72 Backend Tests Passed (100%)**
- Validated complete integration flow from Request -> PEP -> Risk -> PDP -> MFA -> Segmentation.
