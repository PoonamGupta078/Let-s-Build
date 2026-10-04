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
- Frontend prompt 1 (foundation + dashboard) and prompt 2 (Alerts & Cases queue, /investigations/[id] stub): done.
  Frontend only; lint + build clean. Graph/SEE, fusion, alerts, evidence, API, copilot: not started.

## Glossary
tainted rupees = estimated rupees traceable to confirmed-bad funds. hold = recommendation to freeze an account
(never executed by us). exit = cash-out / other-bank / outside the bank's view.
