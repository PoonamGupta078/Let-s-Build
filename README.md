# SecureTrace (SecureLedger × TraceX)
Follow the rupee, cut the ring: graph-based fund-flow tracking, rupee-level taint tracing (TRACE),
hold recommendations (CUT) and a Cline-powered investigator copilot. Recommendation only: a human decides.

## Run
    python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    python -m pytest -q                                   # full suite: 99 passing

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
neo4j/ (integration, done) · models/ detect/ fusion/ alerts/ evidence/ (to build) ·
api/ copilot/ frontend/ scripts/ · docs/ · vendor/tracex (read-only reference) · .clinerules/

## Reused vs built
Fill in at the end: what comes from TraceX / SecureLedger and what was built during the hackathon.
