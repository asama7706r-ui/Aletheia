"""Audit diagnostic (not pre-registered; spent worlds; the sealed result stands): does the direction lie inside what
the procedure already knows? Asked after the owner's question of 2026-11-04.
For each branch the output added where a key proof decides (12 worlds), on a copy of the 5b procedure:
1. KEY PAIR. Take the key's split (a, b). Does the procedure's own rewriter for that candidate already reduce a*b to
   0 (it "knows" a*b = 0)? Does its own search then close both cases, given a and b?
2. DERIVED PAIRS. A small proposer that reads only the world and the rewriter, not the key:
   - L = the names (not e1), and the subterms of the role that are products of names, as written;
   - zero products: x*y for x, y in L, kept when the rewriter reduces it to 0 and neither factor to 0;
   - one-word polynomials: for w in L, the powers 1, w, w*w, (w*w)*w, w*(w*w) under the rewriter; a linear relation
     among them (and their e1 multiples in k02) gives a polynomial, factored over Q and, in k02, over Q(i) with
     i read as e1; each factorization f*g is kept when the rewriter reduces f(w)*g(w) to 0.
   Then: does the procedure's own search close both cases for some derived pair? Does the sealed checker accept the
   whole refutation? How many pairs were proposed?
Compare: the sealed search scans products of up to 240 x 240 linear forms for its pairs.
Usage (from aletheia_blind_test_5b/): python -I audit/diag_direction_5b.py [SECONDS_PER_WORLD]"""
import itertools
import json
import os
import sys
import time
from fractions import Fraction as Fr

import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "procedure"))
sys.path.insert(0, os.path.join(ROOT, "scorer"))
import procedure_v5b as PB  # noqa: E402
import certs_v5 as C  # noqa: E402

P = PB.P
sys.stdout.reconfigure(encoding="utf-8")


def word_el(j, alg):
    W = alg.W
    if j == "1":
        return {W.unit: Fr(1)}
    if isinstance(j, str):
        return {W.gen(j): Fr(1)}
    return alg.mul(word_el(j[0], alg), word_el(j[1], alg))


def coef(c, W):
    if isinstance(c, list):
        return P.Surd(Fr(c[0]), Fr(c[1]), W.th_c)
    return Fr(c)


def el_of(j, alg, W):
    out = {}
    for c, w in j:
        k = coef(c, W)
        out = alg.add(out, {u: k * x for u, x in word_el(w, alg).items()})
    return out


def role_words(atoms):
    """Subterms of the role that are products of names, as written."""
    out = []

    def is_word(a):
        return a[0] == "name" or (a[0] == "prod" and all(is_word(x) for x in a[1]))

    def walk(a):
        if a[0] == "prod" and is_word(a) and a not in out:
            out.append(a)
        if a[0] in ("prod", "sum"):
            for x in a[1]:
                walk(x)
        elif a[0] == "neg":
            walk(a[1])
    for _op, l, r in atoms:
        walk(l)
        walk(r)
    return out


def word_list(W, alg):
    L = [{alg.W.gen(g): Fr(1)} for g in W.gens]
    for a in role_words(W.atoms):
        v = P.term(a, alg, [])
        if v not in L:
            L.append(v)
    return L


def relation(vectors):
    """A rational linear relation among the vectors (dicts), with a nonzero last coefficient, or None."""
    keys = sorted({k for v in vectors for k in v}, key=repr)
    if not keys:
        return None
    M = sp.Matrix([[sp.Rational(v.get(k, Fr(0)).numerator, v.get(k, Fr(0)).denominator) for v in vectors]
                   for k in keys])
    for v in M.nullspace():
        if v[len(vectors) - 1] != 0:
            return [v[i] for i in range(len(vectors))]
    return None


def poly_pairs(W, alg, rw, w):
    """Factorizations f*g of a one-word polynomial relation of w, as element pairs that reduce to 0."""
    t = sp.Symbol("t")
    A = alg.W
    has_e = W.origin == "k02"
    e = {A.gen("e1"): Fr(1)} if has_e else None
    one = {A.unit: Fr(1)}
    ww = alg.mul(w, w)
    tails = [[one, w, ww]]
    www = [alg.mul(ww, w), alg.mul(w, ww)]
    tails += [[one, w, ww, x] for x in www]
    out = []

    def power(k, tail):
        return tail[k]

    def elem(poly, tail):
        v = {}
        for (i,), c in sp.Poly(poly, t, extension=[sp.I] if has_e else None).terms():
            re_, im_ = sp.re(c), sp.im(c)
            x = power(i, tail)
            if re_ != 0:
                v = alg.add(v, {u: Fr(int(re_.p), int(re_.q)) * y for u, y in x.items()})
            if im_ != 0:
                ex = alg.mul(e, x)
                v = alg.add(v, {u: Fr(int(im_.p), int(im_.q)) * y for u, y in ex.items()})
        return v

    for tail in tails:
        for d in range(1, len(tail)):
            powers = tail[:d + 1]
            nfs = [rw.nf(x) for x in powers]
            basis = list(nfs)
            if has_e:
                basis_e = [rw.nf(alg.mul(e, x)) for x in powers]
                rel = relation(basis_e + basis)
                if rel is None:
                    continue
                n = d + 1
                expr = sum((rel[i + n] + sp.I * rel[i]) * t ** i for i in range(n))
            else:
                rel = relation(basis)
                if rel is None:
                    continue
                expr = sum(rel[i] * t ** i for i in range(d + 1))
            if sp.Poly(expr, t, extension=[sp.I] if has_e else None).degree() < 2:
                break
            _, facs = sp.factor_list(expr, t, gaussian=True) if has_e else sp.factor_list(expr, t)
            parts = [f ** k for f, k in facs]
            if len(parts) == 1 and facs[0][1] >= 2:
                parts = [facs[0][0], facs[0][0] ** (facs[0][1] - 1)]
            for i, f in enumerate(parts):
                g = sp.prod(parts[:i] + parts[i + 1:])
                if g == 1:
                    continue
                a, b = elem(f, tail), elem(g, tail)
                for x, y in ((a, b), (b, a)):
                    if rw.nf(x) and rw.nf(y) and not rw.nf(alg.mul(x, y)):
                        if (x, y) not in out:
                            out.append((x, y))
            break
    return out


def derived_pairs(W, kept):
    alg, rw, _rels, _ineqs = W.rewriter(kept)
    L = word_list(W, alg)
    pairs = []
    for x, y in itertools.product(L, repeat=2):
        if rw.nf(x) and rw.nf(y) and not rw.nf(alg.mul(x, y)):
            pairs.append((x, y))
    for w in L:
        for p in poly_pairs(W, alg, rw, w):
            if p not in pairs:
                pairs.append(p)
    return pairs


def closes(W, kept, a, b):
    """The two case trees of the procedure's own search, or None."""
    k0 = W.search(kept, [a], W.names, 1)
    if k0 is None:
        return None
    k1 = W.search(kept, [b], W.names, 1)
    return None if k1 is None else (k0, k1)


def sealed_check(W, kept, d, winfo, a, b, kids):
    """The whole refutation, given to the sealed checker."""
    alg, rw, _r, _i = W.rewriter(kept)
    by = "q12" if "q12" in kept else "q14"
    tree = {"node": "split", "by": by, "a": P.el_json(a, alg.W), "b": P.el_json(b, alg.W),
            "proof_ab": P.terms_json(rw.member(alg.mul(a, b)), alg.W), "children": list(kids)}
    return C.safe(C.check_refutation, {"theta": None, "tree": tree}, winfo, d)[0]


def check(batch, wid, d, key_entry, secs):
    path = os.path.join(ROOT, f"batch_{batch}", "worlds", f"{wid}.json")
    world = json.load(open(path, encoding="utf-8"))
    winfo = C.world_info(C.R.load(path))
    W = P.World(world, time.time() + secs)
    W.th_c = None
    kept = set(W.U) - set(d)
    rep = f"{batch} {wid} drop {d}:"
    cert = None
    for r in key_entry.get("refutations") or []:
        if r["proof"]["tree"]["node"] == "split" and C.safe(C.check_refutation, r["proof"], winfo, d)[0]:
            cert = r["proof"]
            break
    if cert is None:
        print(rep, "no split-rooted key proof accepted", flush=True)
        return
    t0 = time.time()
    if cert.get("theta"):
        W.th_c = -Fr(cert["theta"]["poly"][0])
    alg, rw, _r, _i = W.rewriter(kept)
    a, b = el_of(cert["tree"]["a"], alg, W), el_of(cert["tree"]["b"], alg, W)
    knows = not rw.nf(alg.mul(a, b))
    key_closes = (closes(W, kept, a, b) is not None) if knows else None
    W.th_c = None
    pairs = derived_pairs(W, kept)
    hit, accepted = None, None
    for i, (x, y) in enumerate(pairs):
        if time.time() > W.t_end:
            break
        kids = closes(W, kept, x, y)
        if kids is not None:
            hit = i
            accepted = sealed_check(W, kept, d, winfo, x, y, kids)
            break
    print(f"{rep} rewriter reduces the key's a*b to 0: {knows}; search closes both key cases: {key_closes}; "
          f"derived pairs {len(pairs)}; a derived pair closes: "
          f"{'no' if hit is None else 'yes, pair ' + str(hit + 1) + ' = ' + repr(P.el_json(pairs[hit][0], alg.W)) + ' * ' + repr(P.el_json(pairs[hit][1], alg.W))}"
          f"; sealed checker accepts it: {accepted}; {time.time() - t0:.1f} s", flush=True)


def main():
    secs = int(sys.argv[1]) if len(sys.argv) > 1 else 240
    for batch in "AB":
        rep = json.load(open(os.path.join(ROOT, "results", f"report_{batch}.json"), encoding="utf-8"))["worlds"]
        key = {e["id"]: e for e in json.load(open(os.path.join(ROOT, f"batch_{batch}", "key", "key.json"),
                                                  encoding="utf-8"))}
        for wid in sorted(rep):
            for d in rep[wid]["reported"]["branches_added_where_a_proof_decides"]:
                try:
                    check(batch, wid, d, key[wid], secs)
                except Exception as ex:  # a diagnostic: report and go on
                    print(f"{batch} {wid} drop {d}: ERROR {type(ex).__name__}: {ex}", flush=True)


if __name__ == "__main__":
    main()
