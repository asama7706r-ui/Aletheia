#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The seven baselines of blind test 5b (protocol_v5b.md, Section 7; test 5's baselines_v5.py, reading ref_v5b).

Each baseline is a known wrong rule applied to the truth's classification of candidates, so it differs
from the truth only by its rule. Output: {"verdict", "branches": [{"drop", "status"}], "known"}.
"""
import itertools
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import certs_v5 as C  # noqa: E402
import ref_v5b as RF  # noqa: E402

NAMES = ["COUNT", "MAXCON", "ORDER", "ASSOC", "FIRST", "COARSE", "SPLIT_ORDER"]
FIRST_ORDER = ["q5", "q6", "q12", "q13", "q14"] + C.COPIES


def verdict_of(branches):
    if not branches:
        return "NO_ANSWER"
    if all(b["status"] == "no_witness" for b in branches):
        return "NO_WITNESS"
    return "NEW_KIND" if len(branches) == 1 else "BRANCHES"


def br(drop, status):
    return {"drop": sorted(drop), "status": "witnessed" if status in ("WITNESSED", "witnessed") else "no_witness"}


def family(rule, origin):
    """A rule with its copies (for k02)."""
    if origin != "k02":
        return {rule}
    if rule == "q5":
        return {"q5"} | {c for c in C.COPIES if c.startswith("q5[")}
    if rule == "q6":
        return {"q6", "q6[on]"}
    return {rule}


def minimal_in(cl, candidates):
    """Minimal non-refuted candidates within a family closed under the given list (top-down)."""
    cands = [frozenset(c) for c in candidates]
    live = [c for c in cands if cl.status(c) != "REFUTED"]
    mins = [c for c in live if not any(o < c for o in live)]
    return sorted((sorted(m) for m in set(mins)), key=lambda m: (len(m), m))


def gf2_branch(info, U):
    """MAXCON's characteristic-2 candidate {q2} | F2, or None (Section 7, item 2)."""
    import sympy as sp
    gens = info["generators"] + (["e1"] if info["origin"] == "k02" else [])
    syms = {g: sp.Symbol("v_" + g) for g in gens}

    class P:
        def const(self, q):
            if q.denominator % 2 == 0:
                raise C.CertError("even denominator")
            return sp.Integer(q.numerator * pow(q.denominator, -1, 2) % 2) if q.denominator != 1 else sp.Integer(q.numerator % 2)

        def name(self, g):
            return syms[g]

        def add(self, xs):
            return sp.Add(*xs)

        def neg(self, x):
            return -x

        def mul(self, x, y):
            return sp.expand(x * y)

        def inv(self, x):
            raise C.CertError("no inverse")
    eqs, neqs = [], []
    try:
        for op, l, r in info["atoms"]:
            d = sp.expand(C.evaluate(l, P(), []) - C.evaluate(r, P(), []))
            (eqs if op == "=" else neqs).append(d)
    except C.CertError:
        return None
    if info["origin"] == "k02":
        eqs.append(syms["e1"] ** 2 + 1)
    vs = list(syms.values())
    eqs = [e for e in eqs if sp.Poly(e, *vs, modulus=2).as_expr() != 0]
    if not eqs:
        return None
    G = sp.groebner(eqs, *vs, order="grevlex", modulus=2)
    if list(G.exprs) == [1] or not G.is_zero_dimensional:
        return None
    lms = [sp.Poly(g, *vs, modulus=2).monoms(order="grevlex")[0] for g in G.exprs]
    bound = [min(m[i] for m in lms if m[i] > 0 and all(m[j] == 0 for j in range(len(vs)) if j != i))
             for i in range(len(vs))]
    basis = [ex for ex in itertools.product(*[range(b) for b in bound])
             if not any(all(e >= l for e, l in zip(ex, lm)) for lm in lms)]
    n = len(basis)
    if n > C.BOUNDS["P3"] or n > 8:
        return None
    idx = {ex: i for i, ex in enumerate(basis)}
    mono = [sp.Mul(*[v ** e for v, e in zip(vs, ex)]) for ex in basis]

    def vec(expr):
        _, r = G.reduce(sp.expand(expr))
        out = [0] * n
        for m, c in sp.Poly(r, *vs, modulus=2).terms():
            out[idx[m]] = int(c) % 2
        return out
    for d in neqs:
        if not any(vec(d)):
            return None                      # an inequation fails mod 2
    table = [[vec(mono[i] * mono[j]) for j in range(n)] for i in range(n)]

    def mul(a, b):
        out = [0] * n
        for i in range(n):
            if a[i]:
                for j in range(n):
                    if b[j]:
                        out = [(x + y) % 2 for x, y in zip(out, table[i][j])]
        return out
    elems = [list(t) for t in itertools.product((0, 1), repeat=n) if any(t)]
    one = vec(sp.Integer(1))
    zd = any(not any(mul(a, b)) for a in elems for b in elems)
    noninv = any(all(mul(a, b) != one for b in elems) for a in elems)
    F2 = set()
    if zd and "q12" in U:
        F2.add("q12")
    if noninv and "q13" in U:
        F2.add("q13")
    if "q14" in U:
        F2.add("q14")
    return sorted({"q2"} | F2)


def run_all(world, truth, cl, info, pool):
    """The seven baselines' outputs for one world."""
    out = {}
    v = truth["verdict"]
    origin = info["origin"]
    no_ineq = all(op == "=" for op, _, _ in info["atoms"])
    if v in ("FREEDOM", "IMPOSSIBLE", "KNOWN_SUFFICES"):
        base = {"verdict": v, "branches": [], "known": truth.get("known")}
        for n in NAMES:
            out[n] = dict(base)
        if v == "FREEDOM":
            out["FIRST"] = {"verdict": "KNOWN_SUFFICES", "branches": [], "known": {"kind": origin}}
        if no_ineq and v != "FREEDOM":
            out["MAXCON"] = {"verdict": "BRANCHES", "branches": [br([], "WITNESSED"), br(["q1", "q2"], "WITNESSED")],
                             "known": truth.get("known")}
        return out
    U = cl.U
    mins = cl.minimal()
    st = {tuple(m): cl.status(m) for m in mins}
    # COUNT
    k = min(len(m) for m in mins)
    cb = [br(m, st[tuple(m)]) for m in mins if len(m) == k]
    out["COUNT"] = {"verdict": verdict_of(cb), "branches": cb, "known": None}
    # MAXCON
    extra = []
    if no_ineq:
        extra.append(["q1", "q2"])
    g2 = gf2_branch(info, U)
    if g2 is not None:
        extra.append(g2)
    allc = [(sorted(m), st[tuple(m)]) for m in mins] + [(sorted(e), "WITNESSED") for e in extra]
    mx = [br(d, s) for d, s in allc if not any(set(o) < set(d) for o, _ in allc)]
    mx = [dict(t) for t in {tuple(sorted((k2, tuple(v2) if isinstance(v2, list) else v2) for k2, v2 in b.items())): b
                            for b in mx}.values()]
    out["MAXCON"] = {"verdict": verdict_of(mx), "branches": sorted(mx, key=lambda b: b["drop"]), "known": None}
    # ORDER
    seq = (["q14"] if "q14" in U else []) + ["q6", "q5", "q12", "q13"]
    seq = [r for r in seq if r in U]
    prefix, answer = set(), None
    for r in seq:
        prefix |= family(r, origin) & set(U)
        if cl.status(frozenset(prefix)) == "WITNESSED":
            answer = sorted(prefix)
            break
    if answer is None:
        answer = sorted(U)
    out["ORDER"] = {"verdict": "NEW_KIND", "branches": [br(answer, "WITNESSED")], "known": None}
    # ASSOC
    q5f = C.Q5_FAMILY & set(U)
    if q5f:
        rest = [x for x in U if x not in q5f]
        cands = [set(c) for k2 in range(len(rest) + 1) for c in itertools.combinations(rest, k2)]
        am = minimal_in(cl, cands)
        ab = [br(m, cl.status(m)) for m in am]
        out["ASSOC"] = {"verdict": verdict_of(ab), "branches": ab, "known": None}
    else:
        out["ASSOC"] = {"verdict": truth["verdict"], "branches": [br(b["drop"], b["status"]) for b in truth["branches"]],
                        "known": None}
    # FIRST
    order = {u: i for i, u in enumerate(FIRST_ORDER)}
    fails = sorted({tuple(sorted(f)) for f in cl.fails}, key=lambda f: (len(f), sorted(order[u] for u in f)))
    first = list(fails[0]) if fails else sorted(U)
    out["FIRST"] = {"verdict": "NEW_KIND", "branches": [br(first, "WITNESSED")], "known": None}
    # COARSE
    if origin == "k02":
        rules = [r for r in ["q5", "q6", "q12", "q13"] if r in U]
        cands = []
        for k2 in range(len(rules) + 1):
            for c in itertools.combinations(rules, k2):
                d = set()
                for r in c:
                    d |= family(r, origin) & set(U)
                cands.append(d)
        cm = minimal_in(cl, cands)
        cbr = [br(m, cl.status(m)) for m in cm]
        out["COARSE"] = {"verdict": verdict_of(cbr), "branches": cbr, "known": None}
    else:
        out["COARSE"] = {"verdict": truth["verdict"], "branches": [br(b["drop"], b["status"]) for b in truth["branches"]],
                         "known": None}
    # SPLIT_ORDER
    sb = []
    for b in truth["branches"]:
        if "q14" in b["drop"]:
            rest = [x for x in b["drop"] if x != "q14"]
            for part in ("q14.tot", "q14.sum", "q14.prod"):
                sb.append(br(rest + [part], b["status"]))
        else:
            sb.append(br(b["drop"], b["status"]))
    out["SPLIT_ORDER"] = {"verdict": verdict_of(sb), "branches": sb, "known": None}
    return out
