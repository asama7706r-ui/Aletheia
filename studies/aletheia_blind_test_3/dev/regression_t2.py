"""Regression check (development only; not evidence), protocol section 13.

The 18 Part B worlds of blind test 2 are converted to the test-3 model (the law as base law, the
candidate term as a ledger candidate, the observations as old observations). The coefficient interval
computed by the frozen test-3 procedure must equal the feasible set of the sealed test-2 procedure:
same interval, or unconstrained, or empty (conflict).

Usage:  python regression_t2.py <path to studies/aletheia_blind_test_2>
"""
import json
import os
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "procedure"))
import procedure_v3 as P  # noqa: E402


def convert(w2, sp):
    """test-2 Part B world -> (test-3 world dict, candidate id)."""
    lhs, rhs = w2["law"].split("=")
    y = lhs.strip()
    consts = dict(w2.get("constants", {}))
    for p, v in w2.get("parameters", {}).items():
        consts[p] = {"value": v, "dims": {}}
    lam = sp.Symbol(w2["term"]["unknown"])
    names = list(w2["quantities"]) + list(consts) + [w2["term"]["unknown"]]
    syms = {n: sp.Symbol(n) for n in names}
    h = sp.simplify(sp.sympify(w2["term"]["expr"], locals=syms) / lam)
    observers, obs = {}, []
    for o in w2["observations"]:
        name = observers.setdefault(o["resolution"], "o%d" % (len(observers) + 1))
        obs.append({"state": {q: v for q, v in o["inputs"].items()}, "value": o["output"], "observer": name})
    qs = list(w2["quantities"])
    for o in obs:
        for q in qs:
            if q != y:
                o["state"].setdefault(q, "0")
    w3 = {"id": w2["id"], "experiment": "A", "observable": y, "quantities": w2["quantities"], "constants": consts,
          "observers": {v: k for k, v in observers.items()}, "base_law": "%s = %s" % (y, rhs.strip()),
          "visible": None, "ledger": [{"id": "R1", "object": "ob1", "term": str(h), "coefficient": "unknown", "coverage": None}],
          "symmetries": [], "old_observations": obs, "new_observations": [], "possible_observations": []}
    return w3


def main(t2):
    sys.path.insert(0, os.path.join(t2, "procedure"))
    import procedure_v2 as P2
    import sympy as sp
    wd = os.path.join(t2, "worlds")
    agree, total = 0, 0
    for fn in sorted(os.listdir(wd)):
        if not fn.startswith("B-"):
            continue
        w2 = json.load(open(os.path.join(wd, fn), encoding="utf-8"))
        fz = P2.BWorld(w2).feasible()
        W = P.World(convert(w2, sp))
        R = W.cands[0]
        rows, variables = W.rows(R, "A"), W.unknowns(R, "A")
        ok, _ = P.fm_feasible(rows, variables)
        if not ok:
            mine = ("conflict",)
        else:
            lo, hi = P.fm_interval(rows, variables, "lam")
            mine = ("none",) if lo is None and hi is None else ("interval", lo, hi)
        theirs = ("conflict",) if fz[0] == "conflict" else (("none",) if fz[0] == "none" else ("interval", fz[1], fz[2]))
        total += 1
        same = mine == theirs
        agree += same
        print(w2["id"], "test-2:", [str(x) for x in theirs], " test-3:", [str(x) for x in mine], "OK" if same else "DIFFERENT")
    print("agree %d of %d" % (agree, total))
    return agree == total


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1] if len(sys.argv) > 1 else
                       r"D:\work_app\MyOwnAi\studies\aletheia_blind_test_2") else 1)
