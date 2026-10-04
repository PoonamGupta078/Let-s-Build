# SecureTrace (SecureLedger × TraceX)

An **AML investigation prototype**: graph-based fund-flow analysis for anti-money-laundering
investigators. Follow the rupee, cut the ring. It combines explainable suspicious-activity
detection (SEE), estimated suspicious-fund propagation (TRACE), intervention recommendations
(CUT), and preliminary machine-learning experiments.

**Recommendation only — a human decides.** SecureTrace never executes a freeze. Traced amounts
are *estimates* (fungible money cannot be traced exactly). The project is not production-ready,
not regulatory-compliant, and does not claim proven fraud-detection effectiveness.

## Run
    python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    python -m pytest -q                                   # full suite: 186 passing

## Demo (one command)

    python scripts/run_demo.py

Runs the synthetic SEE → TRACE → CUT workflow end-to-end (S → M1/M2 → CASH). Requires no
Neo4j, API server, frontend dependencies, credentials, or the full 4.5M-row dataset.

Frontend (mock-data UI — not yet connected to the backend):

    cd frontend && npm install && npm run dev      # http://localhost:3000

### Demo limitations
- The demo uses a **synthetic case**, not a claim of real-world fraud-detection accuracy.
- The **frontend** currently uses mock data and is **not connected** to the backend.
- The **API** and **copilot** are **not implemented**.
- **ML experiments** remain preliminary and severely class-imbalanced (PR-AUC < 0.02).
- The current experiment JSON files contain the **100k-sample** run; the documented earlier
  full-data baseline results are not present in the current artifacts.
- **Not production-ready or regulatory-compliant.** Fund propagation is estimated; money is
  fungible; recommendations are advisory and a human decides.

## Backend API (FastAPI, demo)

The frontend connects to a small read-only FastAPI backend that wraps the SEE / TRACE / CUT
engines and serves the synthetic demo case. Run it alongside the frontend:

    python -m uvicorn api.main:app --reload --port 8000

Endpoints: `/api/health`, `/api/overview`, `/api/alerts` (SEE), `/api/graph`,
`/api/trace`, `/api/cut`.
See `docs/api_contract.md`. Set `NEXT_PUBLIC_API_URL` if the backend is not on
`http://localhost:8000`. Data is synthetic; no freeze is executed.

## Frontend (Next.js dashboard)

Launch (run the backend first):

    cd frontend && npm install && npm run dev   # http://localhost:3000

Connected to the API (real synthetic-demo data):
- `/dashboard` — account/transaction/alert counts, rule distribution, recent alerts, graph preview
- `/graph` — Graph Explorer (Cytoscape.js: pan/zoom/fit, layout switch, evidence + TRACE highlighting)
- `/alerts` — SEE alert queue (rule, score, account, explanation, evidence) with search/filter/sort
- `/investigations/[id]` — investigation workspace (graph centre + SEE/TRACE/CUT panels)

Not yet connected (placeholder pages): `/data`, `/model-status`, `/evidence`, `/audit-log`.

Frontend dependencies added: `cytoscape`, `@types/cytoscape`, `clsx`.

## Neo4j setup (optional)
- Prerequisites: Neo4j 4.4+ or 5.x server, reachable from this machine.
- Copy `.env.example` to `.env` and set:
  - NEO4J_URI (e.g. bolt://localhost:7687)
  - NEO4J_USER (e.g. neo4j)
  - NEO4J_PASSWORD
  - NEO4J_DATABASE (optional; defaults to server default)
- Start your Neo4j instance however you prefer (desktop, Docker, service).
  This project does not start, stop, or delete containers for you.
- Run the connectivity and sample-load check:
      python scripts/neo4j_check.py
  If the environment is not configured, the script reports that clearly.
- Load the synthetic demo case into Neo4j (optional — enables the Neo4j-backed graph):
      python scripts/load_demo_neo4j.py
- Run unit tests (mocked driver, no live database required):
      python -m pytest tests/test_neo4j_integration.py -q
  Live integration tests are marked separately and skipped automatically
  when Neo4j is not configured.
- Troubleshooting:
  - ConnectionRefused: verify Neo4j is running and NEO4J_URI matches.
  - AuthError: verify NEO4J_USER / NEO4J_PASSWORD.
  - ImportError: run pip install neo4j.

## Layout
core/ (TRACE + CUT, done) · ingestion/ graph/ see/ (SEE detection, done) ·
neo4j/ (integration, done) · trace/ cut/ (wrappers, done) · models/ (ML baseline + GNN, experimental) ·
frontend/ (dashboard, alerts, workspace — connected to demo API) ·
api/ (FastAPI demo endpoints) · detect/ fusion/ alerts/ evidence/ copilot/ (not started) ·
scripts/ · docs/ · vendor/tracex (read-only reference) · .clinerules/

## Reused vs built
- **vendor/tracex** is a read-only reference (TraceX-FinTech code) intended for detect/, evidence/
  and ingestion/. It has known defects (see its README) and has **not** been imported or adapted yet.
- Everything implemented so far — ingestion, graph, SEE rules, TRACE/CUT wrappers, Neo4j
  integration, ML baseline + GNN, and the frontend — was written during the hackathon.

## Machine-learning status (experimental)
`models/` holds a first-pass tabular baseline (Dummy / Logistic Regression / HistGradientBoosting)
and a numpy-based 2-layer GCN. On the highly imbalanced IBM AML dataset (~0.1% positive), the
models are honest but weak:

| Model | Test PR-AUC | Test ROC-AUC |
|---|---|---|
| Dummy | 0.0029 | 0.5000 |
| Logistic Regression | 0.0067 | 0.7865 |
| HistGradientBoosting | 0.0133 | 0.5695 |
| GNN (100k sample) | 0.0107 | 0.7606 |

The GNN ranks above random (ROC-AUC ≈ 0.76) but its validation-selected threshold detected
**0** of the 28 positive test examples (only 7 positive validation examples). These results are
preliminary and do **not** prove practical fraud-detection effectiveness. See `docs/ml_baseline.md`.
