# SecureTrace (SecureLedger × TraceX)
Follow the rupee, cut the ring: graph-based fund-flow tracking, rupee-level taint tracing (TRACE),
hold recommendations (CUT) and a Cline-powered investigator copilot. Recommendation only: a human decides.

## Run
    python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    python -m pytest -q                                   # core: 8 passing

## Layout
core/ (TRACE + CUT, done) · ingestion/ graph/ models/ detect/ fusion/ alerts/ evidence/ (to build) ·
api/ copilot/ frontend/ scripts/ · docs/ · vendor/tracex (read-only reference) · .clinerules/

## Reused vs built
Fill in at the end: what comes from TraceX / SecureLedger and what was built during the hackathon.
