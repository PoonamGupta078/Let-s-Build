# Acceptance tests (definition of done)

| # | Test | Status |
|---|---|---|
| 1 | Worked example: ₹10L seed → B → C (holding ₹30L clean); C sends ₹20L → ₹5L tainted | passing |
| 2 | B→C earlier than A→B yields no taint on C | passing |
| 3 | Two-mule ring: holding both mules blocks ~100%; one blocks 50% | passing |
| 4 | Alert after the exits blocks 0% | passing |
| 5 | Later alerts never block more (curve monotone) | passing |
| 6 | Block-all finds `{M1, M2}` after the seed has paid out, and `{S}` before | passing |
| 7 | `plan()` reports minutes until exit and clean ₹ held | passing |
| 8 | Top paths run seed → exit; downstream exits sum to ₹10L | passing |
| 9 | Validation rejects negative amounts, src = dst and duplicate `txn_id`; counts shown | passing |
| 10 | Pseudonymised IDs differ with a different key; no raw account number in logs | to write |
| 11 | Detectors: ₹9L→₹5→₹3 not flagged; 200-day round trip not flagged | to write |
| 12 | Alerts exist at account, edge and ring level on the seeded case | to write |
| 13 | Copilot answer with an invented `txn_id` is rejected; a tool outside the allowlist is rejected | to write |
| 14 | STR JSON and PDF hashes verify; every narrative sentence has a `txn_id` | to write |
