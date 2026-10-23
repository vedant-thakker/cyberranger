# CyberRanger — Autonomous Cybersecurity Research Platform

CyberRanger is an educational co-evolutionary laboratory platform that empirically investigates how adaptive intrusion detection systems learn to recognize novel attack structures over repeated exposure.

Operating strictly within a local loopback environment, CyberRanger coordinates two learning agents:
1. **Red Test Generator Agent**: Dynamically generates synthetically diverse security test cases across four vulnerability classes without relying on static payload wordlists or direct LLM payload generation.
2. **Blue Detection Agent**: Evaluates every test input using a hybrid heuristic rule engine and a versioned Random Forest classifier retrained on a fixed cadence exclusively from human-confirmed findings.

---

## Non-Negotiable Security Boundaries

CyberRanger is built strictly for authorized defensive security research and academic education:
- **Loopback-Only Containment**: The only permitted target is a locally hosted Damn Vulnerable Web Application (DVWA) container running on `http://127.0.0.1:8080`.
- **Hardware-Enforced Network Guard**: Outbound network requests to external domains, non-loopback IP addresses, unauthorized ports, or unapproved endpoints are strictly blocked and raise a `SecurityBoundaryViolation`.
- **Zero Persistence or Exploitation**: Generates harmless synthetic test probes only. Never implements persistence, privilege escalation, credential theft, data exfiltration, or destructive commands.
- **Human-in-the-Loop Triage**: The system never self-certifies findings. Only findings verified by a human reviewer enter the supervised model retraining dataset.

---

## System Architecture

```text
               ┌────────────────────────────────────────────────────────┐
               │                  Red Generator Agent                   │
               │  BNF Grammars  •  Mutation  •  Genetic Crossover       │
               │  Combinatorial Transforms  •  UCB1 Bandit  •  Archive  │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                  [Harmless Probes]
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │           Hardware Network Containment Guard           │
               │      (Enforces 127.0.0.1:8080 Loopback-Only Policy)     │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │          Local Practice Target: DVWA Container         │
               │     (SQLi, XSS, Command Injection, Path Traversal)     │
               └───────────────────────────┬────────────────────────────┘
                                           │
                               [Target HTTP Response]
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │                   Referee Engine                       │
               │  Independent Signals: Compromise & Detection Scores    │
               │   MAP-Elites Novelty Matrix  •  SQLite Audit Log       │
               └───────────────┬────────────────────────┬───────────────┘
                               │                        │
                    [Raw Input & Evidence]      [Completed Rounds]
                               ▼                        ▼
               ┌───────────────────────────┐   ┌────────────────────────┐
               │   Blue Detection Agent    │   │     Live Dashboard     │
               │  Explainable Rule Engine  │   │ React 19 + Recharts    │
               │  Random Forest Classifier │   │ Real-Time SSE Stream   │
               └───────────────┬───────────┘   └────────────────────────┘
                               │
                      [Pending Findings]
                               ▼
               ┌───────────────────────────┐
               │ Human-in-the-Loop Triage  │
               │  (Confirmed / Rejected)   │
               └───────────────┬───────────┘
                               │
                     [Confirmed Labels Only]
                               ▼
               ┌───────────────────────────┐
               │ Versioned Model Retrain   │
               │  (Fixed 5-Round Cadence)  │
               └───────────────────────────┘
```

---

## Prerequisites (Apple Silicon macOS)

- **OS**: macOS 14+ (Sonoma) on Apple Silicon (M1/M2/M3)
- **Container Runtime**: [OrbStack](https://orbstack.dev) (Fast, native Docker-compatible engine for Apple Silicon)
- **Python**: 3.10+ (managed via `uv`)
- **Node.js**: v20+ & npm

### OrbStack Setup

Install and launch OrbStack once to complete the one-time VM initialization:

```bash
brew install --cask orbstack
open -a OrbStack
```

Verify Docker engine connectivity:

```bash
docker ps
```

---

## Quickstart (One-Command Setup & Run)

### 1. Launch Local Target Container (DVWA)

```bash
make start-target
```

*Note: Runs DVWA on loopback port 8080 (`http://127.0.0.1:8080`) with `--platform linux/amd64`.*

### 2. Run the 20-Round Autonomous Demonstration

```bash
make demo
```

To run with an exact reproducible random seed:

```bash
make demo SEED=42
```

To run with the optional schema-validated structural LLM proposer enabled:

```bash
uv run scripts/demo.py --rounds 20 --seed 42 --enable-llm
```

---

## Running the Web Dashboard

### 1. Start the FastAPI Backend (Port 8000)

```bash
make backend
```

API documentation will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 2. Start the React Frontend Dev Server (Port 5173)

In a separate terminal:

```bash
make frontend
```

Open your browser to [http://127.0.0.1:5173](http://127.0.0.1:5173) to view the live command center dashboard.

---

## Running the Automated Test Suite

CyberRanger includes 31 automated tests covering network guard containment, grammar expansion, mutations, genetic crossover, transforms, UCB1 bandit, MAP-Elites archive, detection rules, feature extraction, model retraining, and REST/SSE endpoints:

```bash
make test
```

---

## Troubleshooting

| Symptom | Cause | Solution |
| :--- | :--- | :--- |
| `DVWA Target Unreachable on 127.0.0.1:8080` | Container is stopped or OrbStack is closed | Run `open -a OrbStack` followed by `make start-target` |
| `SecurityBoundaryViolation: Target IP is non-local` | Attempted call outside loopback | Check destination URL; only `http://127.0.0.1:8080` is whitelisted |
| `Permission denied connecting to docker.sock` | OrbStack socket path not initialized | Open OrbStack application from `/Applications` |
| Port 8080 already in use | Another service is using port 8080 | Stop conflicting container: `docker rm -f dvwa` |
