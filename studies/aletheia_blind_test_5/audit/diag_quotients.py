"""Audit diagnostic (not pre-registered; the sealed result stands): do the witnesses the procedure missed
in quotient worlds come from its narrow zero-divisor list? procedure_v5.zero_divisor_elements tries only
b_i, 1 + b_i, 1 - b_i and b_i + b_j, b_i - b_j. Here a copy of the procedure (the sealed file is not
changed) also tries c + b_i and c + b_i + d*b_j for small rational c, d. Each witness it finds is checked by
the sealed checker, as in the procedure. Prints, for each world and candidate, the result before and after.
Usage (from aletheia_blind_test_5/): python -I audit/diag_quotients.py"""
import json
import os
import sys
import time
from fractions import Fraction as Fr

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "procedure"))
import procedure_v5 as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
CASES = [("B", "W-18", ["q14", "q6"]), ("B", "W-19", ["q14", "q6"]),
         ("A", "W-04", ["q14", "q6"]), ("A", "W-06", ["q6", "q6[on]"])]
SMALL = sorted({Fr(s * p, q) for p in range(1, 10) for q in (1, 2, 3) for s in (1, -1)})
ORIGINAL = P.zero_divisor_elements


def wider(tpl):
    """The sealed list first, then c + b_i and c + b_i + d*b_j, for c in SMALL u {0} and d in SMALL."""
    import sympy as sp
    out = list(ORIGINAL(tpl))
    n, T = tpl["n"], tpl["table"]

    def singular(a):
        M = [[Fr(0)] * n for _ in range(n)]
        for j in range(n):
            for i, ai in a.items():
                if i == 0:
                    M[j][j] += ai
                elif j == 0:
                    M[i][j] += ai
                else:
                    for k in range(n):
                        c = T.get((i, j, k))
                        if c:
                            M[k][j] += ai * c
        return sp.Matrix(M).det() == 0
    seen = {repr(sorted(a.items())) for a in out}
    for i in range(1, n):
        for c in SMALL:
            a = {0: c, i: Fr(1)}
            if repr(sorted(a.items())) not in seen and singular(a):
                out.append(a)
                seen.add(repr(sorted(a.items())))
    for i in range(1, n):
        for j in range(1, n):
            if j == i:
                continue
            for c in [Fr(0)] + SMALL:
                for d in SMALL:
                    a = {i: Fr(1), j: d} if not c else {0: c, i: Fr(1), j: d}
                    k = repr(sorted(a.items()))
                    if k not in seen and singular(a):
                        out.append(a)
                        seen.add(k)
                if len(out) >= 40:
                    return out
    return out


def run(batch, wid, drop, zfun):
    P.zero_divisor_elements = zfun
    world = json.load(open(os.path.join(ROOT, f"batch_{batch}", "worlds", f"{wid}.json"), encoding="utf-8"))
    W = P.World(world, time.time() + 900)
    t0 = time.time()
    w = W.find_witness(drop)
    return w, time.time() - t0


if __name__ == "__main__":
    for batch, wid, drop in CASES:
        w0, t0 = run(batch, wid, drop, ORIGINAL)
        w1, t1 = run(batch, wid, drop, wider)
        print(f"{batch} {wid} {drop}: sealed list -> {'witness dim ' + str(w0['dim']) if w0 else 'none'} "
              f"({t0:.1f} s); wider list -> {'witness dim ' + str(w1['dim']) if w1 else 'none'} ({t1:.1f} s)",
              flush=True)
