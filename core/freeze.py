"""CUT: greedy marginal-gain hold planner using counterfactual replay of the taint engine.
Approximation: recorded transactions are replayed with held accounts' outgoing transfers removed."""
import pandas as pd
from .taint import run_taint, exit_taint

def plan(txns, seeds, exits, t_alert, k=3, hold_cost=0.0, min_gain=1.0):
    amt = dict(zip(txns.txn_id, txns.amount))
    base = run_taint(txns, seeds); base_exit = exit_taint(base, txns, exits)
    cands = [a for a in base["touched"] if a not in exits]
    ts_of = dict(zip(txns.txn_id, txns.ts)); exit_ids = set(txns[txns.dst.isin(exits)].txn_id)
    chosen, steps, cur_exit, cur_blocked, cur_edge = {}, [], base_exit, set(), base["edge"]
    for _ in range(k):
        best = None
        for a in cands:
            if a in chosen: continue
            f = {**chosen, a: t_alert}
            res = run_taint(txns, seeds, f)
            gain = cur_exit - exit_taint(res, txns, exits)
            new_b = set(res["blocked"]) - cur_blocked
            clean = sum(amt[t] - base["edge"].get(t, 0.0) for t in new_b)
            score = gain / (clean + hold_cost + 1.0)
            if gain >= min_gain and (best is None or score > best[0]):
                best = (score, a, gain, clean, res)
        if not best: break
        _, a, gain, clean, res = best
        dec = [t for t in exit_ids if res["edge"].get(t, 0.0) < cur_edge.get(t, 0.0) - 1e-9]
        eta = (min(ts_of[t] for t in dec) - t_alert).total_seconds() / 60 if dec else None
        chosen[a] = t_alert; cur_exit -= gain; cur_blocked = set(res["blocked"]); cur_edge = res["edge"]
        steps.append({"account": a, "tainted_blocked": gain, "clean_held": clean,
                      "exit_taint_remaining": cur_exit, "minutes_until_exit": eta})
    return {"holds": steps, "baseline_exit_taint": base_exit,
            "blocked_total": base_exit - cur_exit,
            "pct_blocked": 100 * (base_exit - cur_exit) / base_exit if base_exit else 0.0}

def replay_curve(txns, seeds, exits, t_first, latencies, **kw):
    """% of exit taint blocked as a function of alert latency (the headline chart)."""
    return [(lat, plan(txns, seeds, exits, t_first + pd.Timedelta(minutes=lat), **kw)["pct_blocked"]) for lat in latencies]


def block_all(txns, seeds, exits, t_alert, hold_cost=1.0):
    """'Block-all' strategy: weighted minimum vertex cut on the post-alert tainted-flow graph.
    Node capacity = clean rupees passing through the account after t_alert + hold_cost."""
    import networkx as nx
    from collections import defaultdict
    BIG = 1e18
    base = run_taint(txns, seeds)
    sub = txns[(txns.ts >= t_alert) & txns.txn_id.map(lambda t: base["edge"].get(t, 0.0) > 0)]
    if sub.empty: return {"holds": [], "clean_held": 0.0}
    G, clean = nx.DiGraph(), defaultdict(float)
    for r in sub.itertuples():
        clean[r.src] += r.amount - base["edge"][r.txn_id]
        G.add_edge((r.src, "out"), (r.dst, "in"), capacity=BIG)
    for a in set(sub.src) | set(sub.dst):
        if a in exits: G.add_edge((a, "in"), "SINK", capacity=BIG)
        else: G.add_edge((a, "in"), (a, "out"), capacity=clean[a] + hold_cost)
    pre = run_taint(txns[txns.ts < t_alert], {a: v for a, v in seeds.items() if v[0] <= t_alert})            # who holds taint at alert time
    for s, v in pre["tainted"].items():
        if v > 1e-9 and (s, "in") in G: G.add_edge("SRC", (s, "in"), capacity=BIG)
    if "SRC" not in G or "SINK" not in G: return {"holds": [], "clean_held": 0.0}
    val, (S, _) = nx.minimum_cut(G, "SRC", "SINK")
    holds = sorted(a for a in set(sub.src) | set(sub.dst)
                   if a not in exits and (a, "in") in S and (a, "out") not in S)
    return {"holds": holds, "clean_held": float(sum(clean[a] for a in holds))}
