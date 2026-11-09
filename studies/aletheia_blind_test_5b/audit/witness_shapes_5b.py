"""Audit (not pre-registered): what do the missing witnesses look like?
For every output branch marked no_witness that the truth witnesses (the scorer's reported_only list), find the key
witnesses that the sealed checker accepts for that branch, and describe each: its dimension, its field (theta),
the condition certificates it carries (q12 norm, q13 conjugation), the coefficients in its table, and whether its
table is associative and commutative (computed here, rational tables only).
Only the sealed checker runs here (no search), so this is fast.
Usage (from aletheia_blind_test_5b/): python -I audit/witness_shapes_5b.py"""
import json
import os
import sys
from fractions import Fraction as Fr

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scorer"))
import certs_v5 as C  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")


def table(w):
    n = w["dim"]
    T = [[[Fr(0)] * n for _ in range(n)] for _ in range(n)]
    for i in range(n):
        T[0][i][i] = Fr(1)
        T[i][0][i] = Fr(1)
    for i, j, k, c in w["table"]:
        T[i][j][k] = Fr(c)
    return n, T


def mul(n, T, x, y):
    out = [Fr(0)] * n
    for i in range(n):
        if x[i]:
            for j in range(n):
                if y[j]:
                    for k in range(n):
                        if T[i][j][k]:
                            out[k] += x[i] * y[j] * T[i][j][k]
    return out


def basis(n, i):
    v = [Fr(0)] * n
    v[i] = Fr(1)
    return v


def props(w):
    if w.get("theta"):
        return "over Q(theta): associativity not computed here"
    n, T = table(w)
    B = [basis(n, i) for i in range(n)]
    assoc = all(mul(n, T, mul(n, T, B[i], B[j]), B[k]) == mul(n, T, B[i], mul(n, T, B[j], B[k]))
                for i in range(n) for j in range(n) for k in range(n))
    comm = all(mul(n, T, B[i], B[j]) == mul(n, T, B[j], B[i]) for i in range(n) for j in range(n))
    return f"{'associative' if assoc else 'not associative'}, {'commutative' if comm else 'not commutative'}"


def main():
    for batch in "AB":
        rep = json.load(open(os.path.join(ROOT, "results", f"report_{batch}.json"), encoding="utf-8"))["worlds"]
        key = {e["id"]: e for e in json.load(open(os.path.join(ROOT, f"batch_{batch}", "key", "key.json"),
                                                  encoding="utf-8"))}
        for wid in sorted(rep):
            missed = rep[wid]["reported"]["no_witness_branches_the_truth_witnesses"]
            if not missed:
                continue
            path = os.path.join(ROOT, f"batch_{batch}", "worlds", f"{wid}.json")
            winfo = C.world_info(C.R.load(path))
            e = key[wid]
            ws = [("branch " + json.dumps(b["drop"]), b["witness"]) for b in e.get("branches") or []
                  if b.get("witness")]
            ws += [("top_witness", e["top_witness"])] if e.get("top_witness") else []
            for d in missed:
                print(f"{batch} {wid}: output branch {d} is no_witness")
                hits = 0
                for where, w in ws:
                    if not C.safe(C.check_witness, w, winfo, d)[0]:
                        continue
                    hits += 1
                    vals = sorted({c for _i, _j, _k, c in w["table"]}, key=lambda s: (len(s), s))
                    conds = [c for c in ("q12", "q13", "q14") if c in w]
                    print(f"  key witness ({where}): dim {w['dim']}, theta {w.get('theta')}, "
                          f"condition certificates {conds or 'none'}, {len(w['table'])} table entries")
                    print(f"    coefficients {', '.join(vals[:12])}{' ...' if len(vals) > 12 else ''}")
                    print(f"    {props(w)}")
                if not hits:
                    print("  no key witness is accepted for it (the truth witnesses it by another route)")


if __name__ == "__main__":
    main()
