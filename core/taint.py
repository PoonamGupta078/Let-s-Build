"""TRACE: time-respecting haircut taint propagation. O(E) over time-sorted transactions."""
from collections import defaultdict
import pandas as pd

def run_taint(txns: pd.DataFrame, seeds: dict, frozen: dict | None = None) -> dict:
    """txns: columns txn_id, ts, src, dst, amount.
    seeds:  {account: (seed_ts, tainted_amount)}   taint is injected when time reaches seed_ts
    frozen: {account: hold_ts}  outgoing transfers from account with ts >= hold_ts are blocked
    Returns edge taint per txn, final account taint/balance, blocked txn ids, provenance parents."""
    frozen = frozen or {}
    bal, tnt = defaultdict(float), defaultdict(float)
    pending = sorted((ts, a, amt) for a, (ts, amt) in seeds.items())
    pi, edge, blocked, parents, touched = 0, {}, [], defaultdict(list), set(seeds)
    for r in txns.sort_values(["ts", "txn_id"]).itertuples(index=False):
        while pi < len(pending) and pending[pi][0] <= r.ts:
            _, a, amt = pending[pi]; bal[a] += amt; tnt[a] += amt; pi += 1
        if r.src in frozen and r.ts >= frozen[r.src]:
            blocked.append(r.txn_id); continue
        eff = max(bal[r.src], r.amount)          # sender must have held at least what it sent
        t = min(tnt[r.src] / eff, 1.0) * r.amount if eff > 0 else 0.0
        tnt[r.src] -= t; bal[r.src] = max(bal[r.src] - r.amount, 0.0)
        bal[r.dst] += r.amount; tnt[r.dst] += t
        edge[r.txn_id] = t
        if t > 0:
            touched.add(r.dst); parents[r.dst].append((r.txn_id, r.src, t))
    while pi < len(pending):                                   # seeds with no later transactions
        _, a, amt = pending[pi]; bal[a] += amt; tnt[a] += amt; pi += 1
    return {"edge": edge, "tainted": dict(tnt), "balance": dict(bal),
            "blocked": blocked, "parents": dict(parents), "touched": touched}

def exit_taint(res: dict, txns: pd.DataFrame, exits: set) -> float:
    ex = txns[txns.dst.isin(exits)]
    return float(sum(res["edge"].get(t, 0.0) for t in ex.txn_id))


def downstream(res: dict, txns: pd.DataFrame, exits: set) -> dict:
    """Downstream tainted accounts and eventual exits (account -> tainted rupees that reached it)."""
    reached = {a: v for a, v in res["tainted"].items() if v > 1e-9}
    ex = txns[txns.dst.isin(exits)]
    exits_hit = {}
    for r in ex.itertuples():
        v = res["edge"].get(r.txn_id, 0.0)
        if v > 0: exits_hit[r.dst] = exits_hit.get(r.dst, 0.0) + v
    return {"accounts": reached, "exits": exits_hit}

def top_paths(res: dict, txns: pd.DataFrame, exits: set, k: int = 5) -> list:
    """Backward trace from each tainted exit txn along the largest earlier tainted inflow (provenance)."""
    row = {r.txn_id: r for r in txns.itertuples()}
    out = []
    for tid in txns[txns.dst.isin(exits)].txn_id:
        amt = res["edge"].get(tid, 0.0)
        if amt <= 0: continue
        path, cur = [tid], row[tid]
        while True:
            cands = [(t, s, v) for (t, s, v) in res["parents"].get(cur.src, []) if row[t].ts <= cur.ts and t not in path]
            if not cands: break
            t = max(cands, key=lambda c: c[2])[0]; path.append(t); cur = row[t]
        hops = [{"txn_id": t, "src": row[t].src, "dst": row[t].dst, "ts": str(row[t].ts),
                 "amount": row[t].amount, "tainted": res["edge"].get(t, 0.0)} for t in reversed(path)]
        out.append({"tainted_amount": amt, "hops": hops})
    return sorted(out, key=lambda p: -p["tainted_amount"])[:k]
