"""Audit diagnostic (not pre-registered; spent worlds; written after reading these two worlds): the two refutations
that diag_direction_5b.py did not derive. Can they be built with no key and no list of guesses?
For A W-07 and A W-21, on a copy of the 5b procedure, from the candidate's own rewriter only:
1. every normal word up to length P2 over the names (a word the rewriter cannot reduce), not only the role's words;
2. each word's one-word polynomial relation, as in diag_direction_5b.py, factored over Q and Q(i);
3. when a degree-2 relation does not factor there, its exact roots: if their real and imaginary parts lie in some
   Q(sqrt c), the split (w - r1)*(w - r2) with i read as e1, over that field.
Then the procedure's own search on the two cases, and the sealed checker on the whole refutation.
Usage (from aletheia_blind_test_5b/): python -I audit/diag_build_5b.py"""
import itertools
import json
import os
import sys
import time
from fractions import Fraction as Fr

import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import diag_direction_5b as D  # noqa: E402

P, C = D.P, D.C
ROOT = D.ROOT
sys.stdout.reconfigure(encoding="utf-8")
CASES = [("A", "W-07", ["q14", "q6"]), ("A", "W-21", ["q6"])]


def normal_words(W, alg, rw, maxlen):
    A = alg.W
    names = sorted(W.names)
    if A.assoc:
        words = []
        for k in range(1, maxlen + 1):
            seen = set()
            for p in itertools.product(names, repeat=k):
                w = tuple(sorted(p)) if A.comm else p
                if w not in seen:
                    seen.add(w)
                    words.append(w)
    else:
        by_len = {1: list(names)}
        for k in range(2, maxlen + 1):
            by_len[k] = [A.mul(x, y) for i in range(1, k) for x in by_len[i] for y in by_len[k - i]]
        words = [w for k in sorted(by_len) for w in by_len[k]]
    return [w for w in words if not rw.reducible(w)]


def surd_of(v):
    """(a, b, c) when the real sympy number v = a + b*sqrt(c), else None."""
    v = sp.nsimplify(sp.simplify(v))
    a, rest = v.as_coeff_Add()
    if rest == 0:
        return Fr(int(a.p), int(a.q)), Fr(0), None
    b, rad = rest.as_coeff_Mul()
    if rad.is_Pow and rad.exp == sp.Rational(1, 2) and rad.base.is_Rational:
        c = rad.base
        return Fr(int(a.p), int(a.q)), Fr(int(b.p), int(b.q)), Fr(int(c.p), int(c.q))
    return None


def degree2_relation(W, alg, rw, w):
    A = alg.W
    t = sp.Symbol("t")
    has_e = W.origin == "k02"
    powers = [{A.unit: Fr(1)}, w, alg.mul(w, w)]
    nfs = [rw.nf(x) for x in powers]
    if has_e:
        e = {A.gen("e1"): Fr(1)}
        rel = D.relation([rw.nf(alg.mul(e, x)) for x in powers] + nfs)
        if rel is None:
            return None
        return sum((rel[i + 3] + sp.I * rel[i]) * t ** i for i in range(3))
    rel = D.relation(nfs)
    return None if rel is None else sum(rel[i] * t ** i for i in range(3))


def root_pair(W, kept, word):
    """The split on the two exact roots of word's degree-2 relation, with W.th_c set, or None."""
    alg, rw, _r, _i = W.rewriter(kept)
    expr = degree2_relation(W, alg, rw, {word: Fr(1)})
    if expr is None or sp.degree(expr, sp.Symbol("t")) != 2:
        return None
    t = sp.Symbol("t")
    roots = list(sp.roots(sp.Poly(expr, t, extension=True), t))
    if len(roots) != 2:
        return None
    parts = [(surd_of(sp.re(r)), surd_of(sp.im(r))) for r in roots]
    if any(x is None for p in parts for x in p):
        return None
    cs = {x[2] for p in parts for x in p if x[2] is not None}
    if len(cs) != 1:
        return None
    W.th_c = cs.pop()
    alg, rw, _r, _i = W.rewriter(kept)
    A = alg.W
    els = []
    for re_, im_ in parts:
        v = {word: Fr(1)}
        k = P.Surd(-re_[0], -re_[1], W.th_c)
        if re_[0] or re_[1]:
            v[A.unit] = k
        if im_[0] or im_[1]:
            v[A.gen("e1")] = P.Surd(-im_[0], -im_[1], W.th_c)
        els.append(v)
    a, b = els
    return (a, b) if not rw.nf(alg.mul(a, b)) else None


def check(batch, wid, d):
    path = os.path.join(ROOT, f"batch_{batch}", "worlds", f"{wid}.json")
    world = json.load(open(path, encoding="utf-8"))
    winfo = C.world_info(C.R.load(path))
    W = P.World(world, time.time() + 300)
    W.th_c = None
    kept = set(W.U) - set(d)
    t0 = time.time()
    alg, rw, _r, _i = W.rewriter(kept)
    words = normal_words(W, alg, rw, P.P2)
    print(f"{batch} {wid} drop {d}: {len(words)} normal words up to length {P.P2}", flush=True)
    pairs = []
    for w in words:
        for p in D.poly_pairs(W, alg, rw, {w: Fr(1)}):
            if p not in pairs:
                pairs.append(p)
    print(f"  factored one-word relations give {len(pairs)} pairs", flush=True)
    for i, (x, y) in enumerate(pairs):
        kids = D.closes(W, kept, x, y)
        if kids is not None:
            print(f"  pair {i + 1} closes: {P.el_json(x, alg.W)} * {P.el_json(y, alg.W)}; sealed checker accepts: "
                  f"{D.sealed_check(W, kept, d, winfo, x, y, kids)}; {time.time() - t0:.1f} s", flush=True)
            return
    print("  no factored pair closes; trying exact roots", flush=True)
    for w in words:
        W.th_c = None
        p = root_pair(W, kept, w)
        if p is None:
            continue
        x, y = p
        kids = D.closes(W, kept, x, y)
        if kids is None:
            continue
        c = W.th_c
        alg2, rw2, _r2, _i2 = W.rewriter(kept)
        by = "q12" if "q12" in kept else "q14"
        tree = {"node": "split", "by": by, "a": P.el_json(x, alg2.W), "b": P.el_json(y, alg2.W),
                "proof_ab": P.terms_json(rw2.member(alg2.mul(x, y)), alg2.W), "children": list(kids)}
        theta = {"poly": [P.fs(-c), "0", "1"], "lo": "0", "hi": P.fs(c + 1)}
        ok = C.safe(C.check_refutation, {"theta": theta, "tree": tree}, winfo, d)
        print(f"  roots of word {w} over Q(sqrt {c}) close: {tree['a']} * {tree['b']}; sealed checker accepts: {ok}; "
              f"{time.time() - t0:.1f} s", flush=True)
        return
    print(f"  nothing closes; {time.time() - t0:.1f} s", flush=True)


if __name__ == "__main__":
    for case in CASES:
        check(*case)
