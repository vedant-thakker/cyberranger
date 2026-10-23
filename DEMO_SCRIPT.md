# CyberRanger — Live Demonstration Script (5-Minute Flow)

This guide provides an academic presentation flow for demonstrating CyberRanger to faculty evaluators and peers.

---

## Time Allocation Overview

| Minute | Phase | Focus |
| :--- | :--- | :--- |
| **0:00 – 1:00** | Problem Statement & Motivation | Limitations of static signature wordlists and static detection |
| **1:00 – 2:00** | Architecture & Constraints | Red Generator (BNF Grammars/MAP-Elites/Bandit) vs Blue Detector |
| **2:00 – 3:30** | Live Execution Demonstration | Running `make demo` or interacting with the React 19 Dashboard |
| **3:30 – 4:15** | Learning & Human-in-the-Loop | Retraining cadence, versioned Random Forest, triage verification |
| **4:15 – 5:00** | Empirical Results & Limitations | Genuine measured metrics, regression archive, next research stages |

---

## Detailed Script & Talking Points

### Minute 0:00 – 1:00: The Problem Being Solved
- *"Good morning/afternoon. Today I am presenting CyberRanger, an autonomous co-evolutionary laboratory platform for defensive cybersecurity research."*
- *"Traditional security detection suffers from a fundamental asymmetry: defenders write static rules based on known attacks, while adversaries continuously mutate structures to bypass them."*
- *"Static testing tools rely on hardcoded wordlists or static datasets, and naive LLM-based fuzzing often generates invalid syntax or hallucinated commands. Our goal was to answer: Can an automated intrusion detection agent measurably learn and improve its accuracy over repeated exposure to structurally varied, synthetically generated test cases in a strictly contained environment?"*

### Minute 1:00 – 2:00: Architecture & Non-Negotiable Constraints
- *"CyberRanger operates under strict academic and ethical boundaries:"*
  1. **Strict Local Containment**: *"Our custom Network Guard enforces that 100% of network traffic is pinned to our local Docker container (DVWA on 127.0.0.1:8080). Any external call immediately throws a hard SecurityBoundaryViolation."*
  2. **No Wordlists & No LLM Payloads**: *"The Red Agent cannot read from a payload dictionary or ask an LLM to write payloads. Instead, it uses formal BNF grammars for the 4 core vulnerability classes (SQLi, XSS, Command Injection, and Path Traversal), recombining them via AST mutation, genetic crossover, and combinatorial transforms."*
  3. **Novelty Search via MAP-Elites & Bandit**: *"A UCB1 multi-armed bandit dynamically selects which generation strategy to favor, while a MAP-Elites archive rewards discovering novel behavioral niches."*
  4. **Human-in-the-Loop Triage**: *"The system never self-certifies findings. Only human-reviewed and confirmed test cases ever enter the blue agent's retraining dataset."*

### Minute 2:00 – 3:30: Live 20-Round Demonstration
- **Action**: Run the demo command in your terminal or click "Run Autonomous Session" on the web dashboard:
  ```bash
  make demo SEED=42
  ```
- **Speaking while the demo runs**:
  - *"Watch the live engagement telemetry streaming on screen."*
  - *"Each round, the Red Agent generates a structural candidate, validates containment through the Network Guard, and executes it against the local practice application."*
  - *"Notice the dual independent scoring: the Referee records whether DVWA exhibited vulnerable behavior (e.g., retrieving database records or reflecting unescaped tags) and independently evaluates whether the Blue Agent flagged the input."*
  - *"Notice Round 4 and 5: our human triage queue confirms valid attacks, and at Round 5, our fixed cadence triggers model retraining."*
  - *"Observe the model version tag advancing from rule-only baseline to `rf-v1.0`, `rf-v2.0`, and onward."*
  - *"In later rounds (e.g. Round 14 and 19), notice that the newly trained Random Forest classifier directly intercepts complex attack mutations that bypassed simple heuristic rules!"*

### Minute 3:30 – 4:15: Human-in-the-Loop Verification & Learning Curve
- **Action**: Switch to the React 19 Dashboard (or show the Detector Learning Curve chart):
  - *"On the dashboard's Detector Learning Curve, green vertical reference lines explicitly mark each retraining snapshot."*
  - *"Unlike systems that retrain after every single sample (causing catastrophic forgetting), CyberRanger retrains on a fixed cadence with a strict 80/20 train/validation split."*
  - *"At Round 10 and 20, our Regression Archive automatically replays the new model against all historical red elites and benign test baselines to ensure the blue agent has not suffered a performance backslide."*

### Minute 4:15 – 5:00: Empirical Results & Future Stages
- **Action**: Highlight the final summary panel:
  - *"In this 20-round run, the session completed in 3.6 seconds (averaging 0.18s per round)."*
  - *"Out of 20 generated tests, the Blue Agent achieved a verified 95.0% detection rate, discovering 11 unique behavioral niches in the MAP-Elites matrix."*
  - *"Crucially, every single number you see is genuine: persisted in SQLite and traced to a real HTTP request and response from DVWA."*
  - *"Current limitations: our practice target is currently DVWA; future stages will expand to multi-service microservice topologies, reinforcement learning policies, and broader vulnerability classes."*
  - *"Thank you. I am happy to take questions."*

---

## Fallback Plan (What to Do If Something Fails Mid-Demo)

Even with robust code, live demos can face runtime hiccups (e.g., accidental port collisions, Docker daemon sleep).

### Failure Scenario 1: Port 8080 Connection Refused
- **Diagnosis**: OrbStack was put to sleep or the DVWA container was stopped.
- **Immediate Fix**:
  ```bash
  make start-target
  ```
  Wait 5 seconds, then re-run `make demo`.

### Failure Scenario 2: Frontend Dev Server Not Loading
- **Diagnosis**: Port 5173 occupied or Vite stopped.
- **Immediate Fix**: Use the terminal CLI demo:
  ```bash
  make demo SEED=42
  ```
  The terminal CLI output uses Rich with full tables, color-coded status badges, and cadence alerts, providing a complete standalone presentation experience.

### Failure Scenario 3: Need to Replay a Documented Previous Run
- **Diagnosis**: Docker engine unavailable on evaluator machine.
- **Immediate Fix**: Show the persisted SQLite experiment records using our export tool:
  ```bash
  .tools/uv run --directory backend python3 -c "from app.storage.database import Database; db = Database('cyberranger_demo.db'); print(f'Persisted Rounds: {len(db.get_rounds(\"demo-run\"))}')"
  ```
  State honestly: *"This demonstrates our stored run replay from the SQLite persistence engine."*
