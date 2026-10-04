# SecureTrace: project brief

## What it is
Given a confirmed-bad account, show where its money went (TRACE), which few accounts to hold to stop most of
it (CUT), and draft an evidence-backed report. A Cline-powered copilot answers an investigator's questions using
read-only tools. The investigator always decides.

## Layers
SEE = detection (GraphSAGE, Node2Vec, Isolation Forest, 5 rule detectors, fusion 0-100, account/edge/ring alerts)
TRACE = time-respecting haircut taint propagation (core/taint.py: DONE, tested)
CUT = block-all vertex cut + greedy hold planner (core/freeze.py: DONE, tested)
Evidence = STR-style PDF + JSON, SHA-256 of both, linked txn_ids
Copilot = 5 read-only tools: get_graph, trace_taint, plan_intervention, find_evidence, draft_str

## Data
data/make_case.py builds a deterministic seeded ring (seed=42) + IBM background transactions.
Columns: txn_id, ts, src, dst, amount, type, channel, ext_bank. Exits are accounts flagged exit.

## Folders and owners
A (engine): data, ingestion, graph, models, detect, fusion, alerts, core, evidence
B (experience): api, copilot, frontend, scripts, docs
vendor/tracex = read-only TraceX reference code to adapt.

## Constraints
6 hours, 2 people, depth D1 (thin but working). Demo runs from a clean clone offline except the copilot's model call.

## Current status (update after each task)
- core/taint.py, core/freeze.py, tests/test_core.py: done, 8 tests passing.
- ingestion (schema, validation, IBM loader, reproducible sample) + tests/test_ingestion.py: done.
  Full suite: 21 passing. Raw IBM files live in data/ (gitignored); processed outputs in data/processed/.
- graph/build.py (MultiDiGraph construction, missing-account detection) +
  graph/views.py (asof cutoff, case subgraph) + tests/test_graph.py: done.
- SEE detection engine (see/rules.py, see/run.py, see/models.py) + tests/test_see.py: done.
  Three rules (rapid pass-through, high activity, fan-in/fan-out), all thresholds configurable.
- TRACE module (trace/run.py, trace/models.py, trace/config.py) + tests/test_trace.py: done.
  Wraps core/taint.py unchanged; per-currency mode, SEE alert adapter, exit reporting,
  greedy provenance paths, full validation (NaT/duplicates/negative/NaN).
- CUT module (cut/run.py, cut/models.py, cut/config.py) + tests/test_cut.py: done.
  Wraps core.freeze.plan() and core.freeze.block_all() unchanged; greedy ranked
  recommendations + block_all unranked cut-set; per-currency safety;
  advisory-only output with structured evidence, rationale, and disclaimers.
  38 tests (greedy/block_all, ranking, validation, serialization, regression).
  Full suite: 151 passing.
- ML baseline + GNN (models/config.py, features.py, train.py, evaluate.py, gnn.py):
  done.  Tabular baseline (Dummy, Logistic, HGB) and numpy-based 2-layer GCN.
  Full 4.5M-row baseline and 200k-sample GNN completed.
  16 new tests. Full suite: 174 passing.
  Known limitation: chronological split produces tiny val/test with near-zero
  negatives; metrics not yet meaningful for model comparison.
- Frontend prompt 1 (foundation + dashboard), prompt 2 (Alerts & Cases queue) and
  prompt 3 (Investigation Workspace): done. Frontend only; lint + build clean.
- Everything else (graph visualisation via Cytoscape, evidence generation, API, copilot): not started.

## Glossary
tainted rupees = estimated rupees traceable to confirmed-bad funds. hold = recommendation to freeze an account
(never executed by us). exit = cash-out / other-bank / outside the bank's view.
