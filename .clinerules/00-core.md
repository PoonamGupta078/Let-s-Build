# SecureTrace rules (loaded on every request)

## Always do first
- Read docs/PROJECT_BRIEF.md and docs/acceptance_tests.md before planning any task.
- Work on ONE task at a time. Propose a short plan and wait for approval before editing.

## Non-negotiable product rules
- Every traversal or replay is time-respecting: process transactions in timestamp order only.
- Never put labels (is_laundering or similar) in graph edges or model features.
- Features are computed as of a cutoff time; no future data.
- Every alert, answer and STR sentence cites txn_ids that a tool returned.
- No tool, endpoint or UI action may execute a freeze. The system only RECOMMENDS; a human decides.
- Pseudonymise account IDs with keyed HMAC; never log raw account numbers or secrets.

## How to change code
- Smallest diff that solves the task. Do not refactor or rename unrelated files.
- Write or update the test first, then the code, then run `python -m pytest -q`.
- NEVER edit or weaken an existing test to make it pass. If a test looks wrong, stop and tell me.
- Do not add dependencies without asking. Do not touch files outside the task's folders.
- vendor/tracex is read-only reference. Adapt code into our own folders; never import from vendor.
- Type hints and short docstrings on public functions. No dead code, no TODO left behind.

## Definition of done
- Tests pass, the change is described in 3 lines, and a line is appended to docs/cline_log.md
  (what I asked, what you produced, what I changed).
