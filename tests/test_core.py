import pandas as pd
from core.taint import run_taint, exit_taint, downstream, top_paths
from core.freeze import plan, replay_curve, block_all
T0 = pd.Timestamp("2026-01-01 10:00"); m = lambda x: T0 + pd.Timedelta(minutes=x)
def df(rows): return pd.DataFrame(rows, columns=["txn_id", "ts", "src", "dst", "amount"])

def test_worked_example_5L():
    tx = df([("x", m(0), "X", "C", 3_000_000), ("ab", m(10), "A", "B", 1_000_000),
             ("bc", m(20), "B", "C", 1_000_000), ("cd", m(30), "C", "D", 2_000_000)])
    r = run_taint(tx, {"A": (m(0), 1_000_000)})
    assert abs(r["edge"]["cd"] - 500_000) < 1e-6

def test_out_of_order_not_traced():
    tx = df([("bc", m(0), "B", "C", 100), ("ab", m(60), "A", "B", 100)])   # B->C happened BEFORE A->B
    r = run_taint(tx, {"A": (m(0), 100)})
    assert r["edge"]["bc"] == 0 and r["tainted"].get("C", 0) == 0

RING = df([("s1", m(10), "S", "M1", 500_000), ("s2", m(10), "S", "M2", 500_000),
           ("e1", m(40), "M1", "CASH", 500_000), ("e2", m(40), "M2", "CASH", 500_000)])
SEEDS = {"S": (m(0), 1_000_000)}

def test_freeze_blocks_exits():
    p = plan(RING, SEEDS, {"CASH"}, t_alert=m(20), k=2)
    assert p["pct_blocked"] > 99 and len(p["holds"]) == 2
    assert plan(RING, SEEDS, {"CASH"}, m(20), k=1)["pct_blocked"] == 50.0

def test_late_alert_blocks_nothing():
    assert plan(RING, SEEDS, {"CASH"}, t_alert=m(50), k=2)["pct_blocked"] == 0.0

def test_replay_curve_monotone_down():
    c = [p for _, p in replay_curve(RING, SEEDS, {"CASH"}, m(0), [0, 20, 60], k=2)]
    assert c[0] >= c[1] >= c[2]

def test_block_all_cut_points():
    assert set(block_all(RING, SEEDS, {"CASH"}, m(20))["holds"]) == {"M1", "M2"}   # after S already paid out
    assert block_all(RING, SEEDS, {"CASH"}, m(0))["holds"] == ["S"]                # single choke point earlier

def test_plan_reports_eta_and_clean_cost():
    p = plan(RING, SEEDS, {"CASH"}, t_alert=m(20), k=2)
    assert p["holds"][0]["minutes_until_exit"] == 20 and p["holds"][0]["clean_held"] == 0

def test_paths_and_downstream():
    r = run_taint(RING, SEEDS)
    paths = top_paths(r, RING, {"CASH"})
    assert paths[0]["hops"][0]["src"] == "S" and paths[0]["hops"][-1]["dst"] == "CASH"
    d = downstream(r, RING, {"CASH"})
    assert abs(d["exits"]["CASH"] - 1_000_000) < 1e-6
