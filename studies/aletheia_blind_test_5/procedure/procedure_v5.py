#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The procedure of blind test 5: build a new kind by the smallest relaxation (protocol_v5.md, Section 2).

For each world it decides FREEDOM, IMPOSSIBLE, KNOWN_SUFFICES, or the branches of the smallest
relaxation by containment, with marks, proofs of every forced fall, and witnesses it builds itself.
Its search: rewriting systems (Groebner-Shirshov bases) in the free algebra of the kept laws,
templates from their normal forms, norms by the quadratic-algebra method, and case splits.
It imports the v0.5 reader, and scorer/certs_v5.py only to check its own certificates before
writing them. It never reads keys, the seed notes, or anything of the scorer's reference.
Usage: python procedure_v5.py run WORLDS_DIR OUT.json
"""
import itertools
import json
import os
import sys
import time
from fractions import Fraction as Fr

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "lang"))
sys.path.insert(0, os.path.join(ROOT, "scorer"))
import reader_v0 as R  # noqa: E402
import certs_v5 as CHK  # noqa: E402   (used only to check this procedure's own certificates)

P2, P3, S = CHK.BOUNDS["P2"], CHK.BOUNDS["P3"], CHK.BOUNDS["S"]
COPIES = ["q5[onn]", "q5[non]", "q5[nno]", "q5[oon]", "q5[ono]", "q5[noo]", "q6[on]"]
UNITS = {"k01": ["q5", "q6", "q12", "q13", "q14"], "k02": ["q5", "q6", "q12", "q13"] + COPIES}
Q5F = {"q5"} | {c for c in COPIES if c.startswith("q5[")}
EQUATIONAL = {"q5", "q6"} | set(COPIES)
MIRROR = {"q5[onn]": "q5[nno]", "q5[nno]": "q5[onn]", "q5[oon]": "q5[noo]", "q5[noo]": "q5[oon]"}
DMAX_ASSOC = 2 * P2
DMAX_TREE = 2 * P2 - 2
TIME_PER_WORLD = 3600


def fs(f):
    f = Fr(f)
    return str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"


# ================================================================ words of the free algebras
class Words:
    """Words of the free unital algebra modulo the kept global laws among q5 and q6.
    assoc: tuples of names (sorted when also commutative); trees: "1", a name, or (l, r)."""

    def __init__(self, assoc, comm):
        self.assoc, self.comm = assoc, comm
        self.unit = () if assoc else "1"

    def gen(self, g):
        return (g,) if self.assoc else g

    def length(self, w):
        if self.assoc:
            return len(w)
        if w == "1":
            return 0
        if isinstance(w, str):
            return 1
        return self.length(w[0]) + self.length(w[1])

    def okey(self, w):
        """An admissible order key: length first, then a structural comparison."""
        if self.assoc:
            return (len(w), w)
        return (self.length(w), self._tkey(w))

    def _tkey(self, w):
        if w == "1":
            return (0,)
        if isinstance(w, str):
            return (1, w)
        a, b = self._tkey(w[0]), self._tkey(w[1])
        if self.comm and a < b:
            a, b = b, a
        return (2, self.length(w), a, b)

    def mul(self, a, b):
        if a == self.unit:
            return b
        if b == self.unit:
            return a
        if self.assoc:
            w = a + b
            return tuple(sorted(w)) if self.comm else w
        if self.comm and self._tkey(a) < self._tkey(b):
            a, b = b, a
        return (a, b)

    def occurrences(self, lead, w):
        """Every way to write w = context(lead): a list of paths (lists of (side, word) steps,
        applied in order from lead outwards)."""
        out = []
        if self.assoc:
            if self.comm:
                rest = list(w)
                for g in lead:
                    if g in rest:
                        rest.remove(g)
                    else:
                        return []
                return [[("L", tuple(rest))]] if rest else [[]]
            n, k = len(w), len(lead)
            for i in range(n - k + 1):
                if w[i:i + k] == lead:
                    path = []
                    if i:
                        path.append(("L", w[:i]))
                    if i + k < n:
                        path.append(("R", w[i + k:]))
                    out.append(path)
            return out

        def walk(x, outer):
            if x == lead:
                out.append(list(outer))
            if isinstance(x, tuple):
                l, r = x
                # x = (l, r): l sits under a right multiplication by r, r under a left one by l
                walk(l, [("R", r)] + outer)
                walk(r, [("L", l)] + outer)
        walk(w, [])
        return out

    def json(self, w):
        if self.assoc:
            if not w:
                return "1"
            j = w[0]
            for g in w[1:]:
                j = [j, g]
            return j
        if w == "1" or isinstance(w, str):
            return w
        return [self.json(w[0]), self.json(w[1])]


class Alg:
    """Elements: dict word -> Fraction. Provenance: dict (spec, path) -> Fraction, where path is a
    tuple of (side, word) steps: the element equals the sum of coef * path(spec)."""

    def __init__(self, words):
        self.W = words

    def mul(self, a, b):
        out = {}
        for w1, c1 in a.items():
            for w2, c2 in b.items():
                w = self.W.mul(w1, w2)
                out[w] = out.get(w, 0) + c1 * c2
        return {w: c for w, c in out.items() if c}

    def add(self, a, b, s=1):
        out = dict(a)
        for w, c in b.items():
            out[w] = out.get(w, 0) + s * c
        return {w: c for w, c in out.items() if c}

    def lead(self, a):
        return max(a, key=self.W.okey)

    def apply_path(self, el, path):
        for side, w in path:
            el = self.mul({w: Fr(1)}, el) if side == "L" else self.mul(el, {w: Fr(1)})
        return el


def prov_add(p, q, s=1):
    out = dict(p)
    for k, c in q.items():
        out[k] = out.get(k, 0) + s * c
    return {k: c for k, c in out.items() if c}


def prov_path(p, path):
    if not path:
        return dict(p)
    return {(spec, pth + tuple(path)): c for (spec, pth), c in p.items()}


# ================================================================ rewriting systems
class Rewriter:
    """A truncated Groebner-Shirshov basis of the ideal generated by relators, with provenance."""

    def __init__(self, alg, relators, dmax, t_end):
        self.A, self.W, self.dmax, self.t_end = alg, alg.W, dmax, t_end
        self.rules = []                     # (lead word, poly with lead coef 1, provenance)
        self.incomplete = False
        pending = [(r, p) for r, p in relators if r]
        while pending:
            if time.time() > self.t_end:
                self.incomplete = True
                break
            poly, prov = pending.pop(0)
            poly, prov = self.reduce(poly, prov)
            if not poly:
                continue
            ld = self.A.lead(poly)
            c = poly[ld]
            poly = {w: x / c for w, x in poly.items()}
            prov = {k: x / c for k, x in prov.items()}
            if self.W.length(ld) > self.dmax:
                self.incomplete = True
                continue
            new = (ld, poly, prov)
            # rules whose lead now reduces are re-queued (inter-reduction)
            keep = []
            for r in self.rules:
                if self.W.occurrences(ld, r[0]):
                    pending.append((r[1], r[2]))
                else:
                    keep.append(r)
            self.rules = keep + [new]
            pending.extend(self.compositions(new))
        # tails fully reduced for normal forms
        self.rules.sort(key=lambda r: self.W.okey(r[0]))

    def compositions(self, new):
        """Overlap compositions of the new rule with every rule (associative ambients only:
        in tree ambients two leads meet only by inclusion, handled by inter-reduction)."""
        out = []
        if not self.W.assoc:
            return out
        l1, p1, v1 = new
        for l2, p2, v2 in self.rules:
            if self.W.comm:
                # lcm of commutative monomials
                rest1, rest2 = list(l2), list(l1)
                for g in l1:
                    if g in rest1:
                        rest1.remove(g)
                for g in l2:
                    if g in rest2:
                        rest2.remove(g)
                if len(l1) + len(rest1) > self.dmax or len(rest1) == len(l2):
                    continue                # coprime leads give no new element
                m1, m2 = tuple(sorted(rest1)), tuple(sorted(rest2))
                s = self.A.add(self.A.mul({m1: Fr(1)}, p1), self.A.mul({m2: Fr(1)}, p2), -1)
                sp = prov_add(prov_path(v1, [("L", m1)] if m1 else []), prov_path(v2, [("L", m2)] if m2 else []), -1)
                out.append((s, sp))
                continue
            for a, b, pa, pb, va, vb in ((l1, l2, p1, p2, v1, v2), (l2, l1, p2, p1, v2, v1)):
                for k in range(1, min(len(a), len(b))):
                    if a[-k:] == b[:k]:
                        u, v = a[:-k], b[k:]
                        if len(a) + len(v) > self.dmax:
                            continue
                        # a*v and u*b are the same word
                        s = self.A.add(self.A.mul(pa, {v: Fr(1)}), self.A.mul({u: Fr(1)}, pb), -1)
                        sp = prov_add(prov_path(va, [("R", v)]), prov_path(vb, [("L", u)]), -1)
                        out.append((s, sp))
        return out

    def reduce(self, poly, prov=None):
        """Full reduction to normal form; returns (normal form, provenance of the reduction).
        The provenance returned is that of `poly - normal form` added to the given one, so that
        poly = nf + (ideal element whose provenance is prov_out - prov_in)."""
        poly = dict(poly)
        prov = dict(prov) if prov is not None else {}
        changed = True
        while changed:
            changed = False
            for w in sorted(poly, key=self.W.okey, reverse=True):
                for ld, rp, rv in self.rules:
                    occ = self.W.occurrences(ld, w)
                    if occ:
                        path = occ[0]
                        c = poly[w]
                        poly = self.A.add(poly, self.A.apply_path(rp, path), -c)
                        prov = prov_add(prov, prov_path(rv, path), -c)
                        changed = True
                        break
                if changed:
                    break
        return poly, prov

    def member(self, target):
        """Provenance (certificate terms) of target as an ideal element, or None."""
        nf, prov = self.reduce(target, {})
        if nf:
            return None
        return {k: -c for k, c in prov.items()}

    def nf(self, poly):
        return self.reduce(poly, {})[0]

    def reducible(self, w):
        return any(self.W.occurrences(ld, w) for ld, _, _ in self.rules)


# ================================================================ terms of a role
def bracketings(vals, mul):
    memo = {}

    def go(lo, hi):
        if (lo, hi) in memo:
            return memo[(lo, hi)]
        if hi - lo == 1:
            res = [vals[lo]]
        else:
            res = [mul(a, b) for k in range(lo + 1, hi) for a in go(lo, k) for b in go(k, hi)]
        memo[(lo, hi)] = res
        return res
    return go(0, len(vals))


def term(ast, alg, agree):
    t = ast[0]
    W = alg.W
    if t == "num":
        return {W.unit: Fr(ast[1])} if ast[1] else {}
    if t == "frac":
        return {W.unit: Fr(ast[1], ast[2])}
    if t == "name":
        return {W.gen(ast[1]): Fr(1)}
    if t == "neg":
        return {w: -c for w, c in term(ast[1], alg, agree).items()}
    if t == "sum":
        out = {}
        for x in ast[1]:
            out = alg.add(out, term(x, alg, agree))
        return out
    if t == "prod":
        vals = [term(x, alg, agree) for x in ast[1]]
        if len(vals) == 2:
            return alg.mul(vals[0], vals[1])
        brs = bracketings(vals, alg.mul)
        for b in brs[1:]:
            agree.append((brs[0], b))
        return brs[0]
    raise ValueError("^-1 has no reading here")


def read_role(build):
    atoms = []
    for s in build["role"]:
        ast, _, _ = R.parse_sentence(s)
        _, prem, concl = ast
        _, op, lhs, rhs = concl[0]
        atoms.append((op, lhs, rhs))
    return atoms


def has_inv(ast):
    t = ast[0]
    if t == "inv":
        return True
    if t in ("prod", "sum"):
        return any(has_inv(x) for x in ast[1])
    if t == "neg":
        return has_inv(ast[1])
    return False


# ================================================================ IMPOSSIBLE: own congruence closure
def impossible(info):
    k02 = info["origin"] == "k02"
    terms_ = {}
    parent = {}
    val = {}

    def node(key):
        if key not in terms_:
            terms_[key] = len(terms_)
            parent[terms_[key]] = terms_[key]
            if key[0] == "c":
                val[terms_[key]] = key[1]
        return terms_[key]

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def build(ast, agree):
        t = ast[0]
        if t in ("num", "frac"):
            q = Fr(ast[1]) if t == "num" else Fr(ast[1], ast[2])
            return node(("c", (q, Fr(0)) if k02 else q))
        if t == "name":
            if ast[1] == "e1":
                return node(("c", (Fr(0), Fr(1))))
            return node(("n", ast[1]))
        if t == "neg":
            return node(("neg", build(ast[1], agree)))
        if t == "sum":
            return node(("add", tuple(build(x, agree) for x in ast[1])))
        if t == "prod":
            vs = [build(x, agree) for x in ast[1]]
            if len(vs) == 2:
                return node(("mul", (vs[0], vs[1])))
            brs = bracketings(vs, lambda a, b: node(("mul", (a, b))))
            for b in brs[1:]:
                agree.append((brs[0], b))
            return brs[0]
        raise ValueError("no ^-1 here")
    eqs, neqs = [], []
    for op, l, r in info["atoms"]:
        ag = []
        a, b = build(l, ag), build(r, ag)
        eqs += ag
        (eqs if op == "=" else neqs).append((a, b))
    bad = []

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return False
        if ra in val and rb in val and val[ra] != val[rb]:
            bad.append(1)
        if ra not in val and rb in val:
            val[ra] = val[rb]
        parent[rb] = ra
        return True

    def calc(op, vs):
        if op == "add":
            return (sum(v[0] for v in vs), sum(v[1] for v in vs)) if k02 else sum(vs, Fr(0))
        if op == "neg":
            return (-vs[0][0], -vs[0][1]) if k02 else -vs[0]
        a, b = vs
        return (a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0]) if k02 else a * b
    for a, b in eqs:
        union(a, b)
    for _ in range(200):
        if bad:
            break
        changed = False
        sig = {}
        for key, i in list(terms_.items()):
            if key[0] in ("c", "n"):
                continue
            kids = key[1] if key[0] in ("add", "mul") else (key[1],)
            s = (key[0],) + tuple(find(k) for k in kids)
            if s in sig and find(sig[s]) != find(i):
                changed |= union(sig[s], i)
            sig.setdefault(s, i)
            if all(find(k) in val for k in kids):
                v = calc(key[0], [val[find(k)] for k in kids])
                changed |= union(node(("c", v)), i)
        if not changed:
            break
    if bad:
        return "values"
    for a, b in neqs:
        if find(a) == find(b):
            return "inequation"
    return None


# ================================================================ known kinds (sympy)
def known(info):
    """A known-kind certificate: the smallest tower kind with a solution, or None."""
    import sympy as sp
    k02_origin = info["origin"] == "k02"
    order = ["k02"] if k02_origin else ["k01", "k02"]
    for kind in order:
        cert = solve_in(info, kind)
        if cert is not None:
            return cert
    return None


def solve_in(info, kind):
    import sympy as sp
    gens = info["generators"]
    if kind == "k01":
        xs = {g: sp.Symbol(f"x_{g}", real=True) for g in gens}
        vals = {g: xs[g] for g in gens}
        I = None
    else:
        re = {g: sp.Symbol(f"a_{g}", real=True) for g in gens}
        im = {g: sp.Symbol(f"b_{g}", real=True) for g in gens}
        vals = {g: re[g] + sp.I * im[g] for g in gens}
        I = sp.I
    if info["origin"] == "k02":
        vals["e1"] = sp.I

    class Ops:
        def ev(self, ast):
            t = ast[0]
            if t == "num":
                return sp.Integer(ast[1])
            if t == "frac":
                return sp.Rational(ast[1], ast[2])
            if t == "name":
                return vals[ast[1]]
            if t == "neg":
                return -self.ev(ast[1])
            if t == "sum":
                return sp.Add(*[self.ev(x) for x in ast[1]])
            if t == "prod":
                return sp.Mul(*[self.ev(x) for x in ast[1]])
            raise ValueError
    ops = Ops()
    eqs, neqs = [], []
    for op, l, r in info["atoms"]:
        d = sp.expand(ops.ev(l) - ops.ev(r))
        if I is not None:
            parts = [sp.re(d), sp.im(d)]
        else:
            parts = [d]
        if op == "=":
            eqs += [sp.expand(p) for p in parts if sp.expand(p) != 0]
        else:
            neqs.append(d)
    unknowns = list(xs.values()) if kind == "k01" else [s for g in gens for s in (re[g], im[g])]
    # each inequation d != 0 enters as z*|d|^2 - 1 = 0 with a new real z (Rabinowitsch), so that fixing
    # a free variable never breaks it; the z are dropped from the solution
    zs = []
    for k, d in enumerate(neqs):
        z = sp.Symbol(f"z_{k}", real=True)
        zs.append(z)
        n2 = sp.expand(sp.re(d) ** 2 + sp.im(d) ** 2) if I is not None else d
        eqs.append(sp.expand(z * n2 - 1))
    sols = [{k: v for k, v in sol.items() if k not in zs} for sol in real_points(eqs, unknowns + zs)]
    for sol in sols:
        ok = True
        for d in neqs:
            v = sp.simplify(d.subs(sol))
            if v == 0:
                ok = False
                break
        if ok:
            cert = encode(sol, gens, kind, xs if kind == "k01" else (re, im))
            if cert is not None and CHK.safe(CHK.check_known, cert, info)[0]:
                return cert
    return None


def real_points(eqs, unknowns, max_tries=120):
    """A few real solutions of a polynomial system, as dicts symbol -> algebraic number.
    A positive-dimensional system is cut down by fixing variables to small integers while it stays
    solvable over the complex numbers; when the finitely many points left have no real one, the search
    backtracks to another choice (at most max_tries Groebner bases)."""
    import sympy as sp
    if not eqs:
        return [{u: sp.Integer(1) for u in unknowns}]
    tries = [0]

    def gb(es, vs):
        es = [e for e in es if e != 0]
        if not es:
            return None
        tries[0] += 1
        try:
            return sp.groebner(es, *vs, order="lex")
        except Exception:
            return None

    def leaf(fixes, G):
        rest = [u for u in unknowns if u not in fixes]
        exprs = [sp.expand(e.subs(fixes)) for e in eqs]
        if any(e.is_number and e != 0 for e in exprs):
            return []
        exprs = [e for e in exprs if e != 0]
        if not rest or not exprs:
            sols = [tuple(sp.Integer(1) for _ in rest)]
        else:
            try:
                sols = sp.solve_poly_system(exprs, *rest)
            except Exception:
                sols = None
        out = []
        for sol in sols or []:
            d = dict(zip(rest, sol))
            d = {k: (fixes[k] if k in fixes else d[k]) for k in unknowns if k in fixes or k in d}
            if all(sp.im(sp.nsimplify(x)) == 0 for x in d.values()):
                out.append(d)
        return out

    def free_vars(fixes):
        """The variables not tied to finitely many values: no polynomial of the elimination ideal
        (lex order with the variable last) involves that variable alone."""
        rest = [u for u in unknowns if u not in fixes]
        es = [sp.expand(e.subs(fixes)) for e in eqs]
        out = []
        for v in rest:
            order = [u for u in rest if u != v] + [v]
            G = gb(es, order)
            if G is None:
                continue
            if not any(p.free_symbols == {v} for p in G.exprs):
                out.append(v)
        return out

    def go(fixes, G):
        if G is None or list(G.exprs) == [1]:
            return []
        if G.is_zero_dimensional:
            return leaf(fixes, G)
        for v in free_vars(fixes) or [u for u in unknowns if u not in fixes]:
            if v in fixes:
                continue
            for c in (0, 1, -1, 2, 3):
                if tries[0] >= max_tries:
                    return []
                f2 = dict(fixes)
                f2[v] = sp.Integer(c)
                rest = [u for u in unknowns if u not in f2]
                trial = [sp.expand(e.subs(f2)) for e in eqs]
                if any(e.is_number and e != 0 for e in trial):
                    continue
                G2 = gb(trial, rest) if rest else None
                if not rest:
                    if all(e == 0 for e in trial):
                        return [f2]
                    continue
                if G2 is None:
                    out = leaf(f2, G2)
                else:
                    out = go(f2, G2)
                if out:
                    return out
            # no value of this variable leads to a real point: try fixing another variable instead
        return []
    return go({}, gb(eqs, unknowns))


def encode(sol, gens, kind, syms):
    """Write the values of a solution in one field Q(theta) (a primitive element)."""
    import sympy as sp
    from sympy.polys.numberfields import primitive_element
    numbers = []
    if kind == "k01":
        for g in gens:
            numbers.append(sp.nsimplify(sol[syms[g]]))
    else:
        re, im = syms
        for g in gens:
            numbers += [sp.nsimplify(sol[re[g]]), sp.nsimplify(sol[im[g]])]

    def q(c):
        c = sp.Rational(c)
        return Fr(int(c.p), int(c.q))
    irr = []
    for n in numbers:
        if not n.is_rational and n not in irr:
            irr.append(n)
    if not irr:
        vals = [fs(q(n)) for n in numbers]
        theta = None
    else:
        x = sp.Symbol("x")
        try:
            f, coeffs, reps = primitive_element(irr, x, ex=True)
        except Exception:
            return None
        poly = sp.Poly(f, x)
        d = poly.degree()
        tv = sp.N(sum(sp.Integer(c) * e for c, e in zip(coeffs, irr)), 60)
        lo = hi = None
        for (a, b), _ in poly.intervals():
            if a != b and sp.Rational(a) <= tv <= sp.Rational(b):
                lo, hi = q(a), q(b)
                break
        if lo is None:
            return None
        rep = {}
        for e, r in zip(irr, reps):
            cs = [q(c) for c in reversed(list(r))]
            cs += [Fr(0)] * (d - len(cs))
            rep[e] = [fs(c) for c in cs]
        vals = []
        for n in numbers:
            vals.append(rep[n] if n in rep else [fs(q(n))] + ["0"] * (d - 1))
        theta = {"poly": [fs(q(c)) for c in reversed(poly.all_coeffs())], "lo": fs(lo), "hi": fs(hi)}
    if kind == "k01":
        values = {g: vals[i] for i, g in enumerate(gens)}
    else:
        values = {g: [vals[2 * i], vals[2 * i + 1]] for i, g in enumerate(gens)}
    return {"kind": kind, "theta": theta, "values": values}


# ================================================================ the classification of candidates
class World:
    def __init__(self, world, t_end):
        b = world["builds"][0]
        self.origin, self.frames = b["origin"], list(b["frames"])
        self.gens = sorted(b["generators"])
        self.atoms = read_role(b)
        self.info = {"origin": self.origin, "generators": self.gens, "frames": self.frames,
                     "atoms": self.atoms, "role": list(b["role"])}
        self.U = [u for u in UNITS[self.origin] if not ("f03" in self.frames and u in Q5F)]
        self.names = set(self.gens) | ({"e1"} if self.origin == "k02" else set())
        self.t_end = t_end
        self.wit_cache = {}
        self.ref_cache = {}
        self.status = {}
        self.witness_of = {}
        self.proof_of = {}

    # ---- ambient of a candidate
    def ambient(self, kept):
        assoc = "f03" in self.frames or "q5" in kept
        comm = "q6" in kept
        return Alg(Words(assoc, comm))

    def context(self, alg):
        rels, ineqs = [], []
        for op, l, r in self.atoms:
            ag = []
            a = term(l, alg, ag)
            b = term(r, alg, ag)
            for x, y in ag:
                rels.append(alg.add(x, y, -1))
            d = alg.add(a, b, -1)
            if op == "=":
                rels.append(d)
            else:
                ineqs.append(d)
        if self.origin == "k02":
            e = {alg.W.gen("e1"): Fr(1)}
            rels.append(alg.add(alg.mul(e, e), {alg.W.unit: Fr(1)}))
        return rels, ineqs

    def copy_instances(self, alg, kept, names, maxlen=1):
        """Instances of kept copies (k02, non-associative ambients), arguments of length <= maxlen."""
        out = []
        if alg.W.assoc:
            return out
        e = {alg.W.gen("e1"): Fr(1)}
        args = [g for g in sorted(names)]
        m = alg.mul
        for u in sorted(kept & set(COPIES)):
            spec_vars = {"q5[onn]": "bc", "q5[non]": "ac", "q5[nno]": "ab", "q5[oon]": "c", "q5[ono]": "b",
                         "q5[noo]": "a", "q6[on]": "b"}[u]
            for combo in itertools.product(args, repeat=len(spec_vars)):
                v = {k: {alg.W.gen(g): Fr(1)} for k, g in zip(spec_vars, combo)}
                if u == "q5[onn]":
                    x, y = m(m(e, v["b"]), v["c"]), m(e, m(v["b"], v["c"]))
                elif u == "q5[non]":
                    x, y = m(m(v["a"], e), v["c"]), m(v["a"], m(e, v["c"]))
                elif u == "q5[nno]":
                    x, y = m(m(v["a"], v["b"]), e), m(v["a"], m(v["b"], e))
                elif u == "q5[oon]":
                    x, y = m(m(e, e), v["c"]), m(e, m(e, v["c"]))
                elif u == "q5[ono]":
                    x, y = m(m(e, v["b"]), e), m(e, m(v["b"], e))
                elif u == "q5[noo]":
                    x, y = m(m(v["a"], e), e), m(v["a"], m(e, e))
                else:
                    x, y = m(e, v["b"]), m(v["b"], e)
                d = alg.add(x, y, -1)
                if d:
                    out.append((("unit", u, tuple(zip(spec_vars, combo))), d))
        return out

    def rewriter(self, kept, extra=(), names=None):
        names = names or self.names
        alg = self.ambient(kept)
        ck = (getattr(self, "th_c", None), alg.W.assoc, alg.W.comm,
              frozenset(kept & set(COPIES)) if not alg.W.assoc else frozenset(),
              tuple(repr(sorted(e.items(), key=repr)) for e in extra), frozenset(names))
        if not hasattr(self, "rw_cache"):
            self.rw_cache = {}
        if ck in self.rw_cache:
            return self.rw_cache[ck]
        res = self._rewriter(kept, extra, names, alg)
        self.rw_cache[ck] = res
        return res

    def _rewriter(self, kept, extra, names, alg):
        rels, ineqs = self.context(alg)
        relators = [(r, {(("ctx", i), ()): Fr(1)}) for i, r in enumerate(rels)]
        for j, e in enumerate(extra):
            relators.append((e, {(("ctx", len(rels) + j), ()): Fr(1)}))
        rels = rels + list(extra)
        relators += [(d, {(spec, ()): Fr(1)}) for spec, d in self.copy_instances(alg, kept, names)]
        dmax = DMAX_ASSOC if alg.W.assoc else DMAX_TREE
        rw = Rewriter(alg, relators, dmax, self.t_end)
        return alg, rw, rels, ineqs

    # ---- templates and witnesses
    def template(self, kept, extra=()):
        """The template: normal-form words as a basis, if it closes within P3 (a table), else None."""
        alg, rw, rels, ineqs = self.rewriter(kept, extra)
        W = alg.W
        gens = sorted(self.names)
        levels = {0: [W.unit]}
        basis = [W.unit]
        closed_at = None
        for n in range(1, (DMAX_ASSOC if W.assoc else DMAX_TREE) + 1):
            cand = set()
            if W.assoc:
                for w in levels[n - 1]:
                    for g in gens:
                        cand.add(W.mul(w, (g,)))
            else:
                if n == 1:
                    cand = {g for g in gens}
                else:
                    for i in range(1, n):
                        for a in levels.get(i, []):
                            for b in levels.get(n - i, []):
                                cand.add(W.mul(a, b))
            lv = sorted((w for w in cand if not rw.reducible(w)), key=W.okey)
            levels[n] = lv
            basis += lv
            if len(basis) > P3:
                return None
            if W.assoc and not lv:
                closed_at = n
                break
            if not W.assoc and n >= 2 and all(not levels.get(k) for k in range((n + 2) // 2, n + 1)):
                closed_at = n
                break
        if closed_at is None or rw.incomplete:
            return None
        idx = {w: i for i, w in enumerate(basis)}
        n = len(basis)
        table = {}
        for i in range(1, n):
            for j in range(1, n):
                prod = rw.nf({W.mul(basis[i], basis[j]): Fr(1)})
                for w, c in prod.items():
                    if w not in idx:
                        return None
                    table[(i, j, idx[w])] = c
        gensv = {}
        for g in self.names:
            nf = rw.nf({W.gen(g): Fr(1)})
            v = [Fr(0)] * n
            for w, c in nf.items():
                if w not in idx:
                    return None
                v[idx[w]] = c
            gensv[g] = v
        return {"n": n, "table": table, "gens": gensv, "basis": basis}

    def witness_cert(self, tpl, drop):
        n = tpl["n"]
        w = {"dim": n, "table": [[i, j, k, fs(c)] for (i, j, k), c in sorted(tpl["table"].items())],
             "theta": None, "gens": {g: [fs(x) for x in tpl["gens"][g]] for g in self.gens},
             "q12": None, "q13": None}
        if self.origin == "k02":
            w["E"] = [fs(x) for x in tpl["gens"]["e1"]]
        kept = set(self.U) - set(drop)
        if n > 1 and ("q12" in kept or "q13" in kept):
            cert = quadratic_norm(tpl)
            if cert is None:
                return None
            if "q12" in kept:
                w["q12"] = cert
            else:
                w["q13"] = cert
        ok, _ = CHK.safe(CHK.check_witness, w, self.info, sorted(drop))
        return w if ok else None

    def find_witness(self, drop):
        """A witness of the candidate, from the template of its kept equations (and quotients)."""
        kept = set(self.U) - set(drop)
        if "q14" in kept:
            return None                      # only dimension 1, and that is a known kind
        eq_kept = frozenset(kept & EQUATIONAL)
        key = (eq_kept, frozenset(kept & {"q12", "q13"}))
        if key in self.wit_cache:
            return self.wit_cache[key]
        found = None
        tries = [()] + self.guesses(eq_kept)
        seen = set()
        while tries and found is None and time.time() < self.t_end:
            extra = tries.pop(0)
            if len(extra) > 6:
                continue
            tpl = self.template(eq_kept | (kept & {"q12", "q13"}), extra)
            if tpl is None:
                continue
            w = self.witness_cert(tpl, drop)
            if w is not None:
                found = w
                break
            if "q12" in kept or "q13" in kept:
                # quotients by zero divisors (decision 5; trap 14)
                for a in zero_divisor_elements(tpl):
                    k = repr(sorted(a.items(), key=repr))
                    if k not in seen:
                        seen.add(k)
                        tries.append(extra + (self.basis_element(tpl, a, eq_kept),))
        self.wit_cache[key] = found
        return found

    def guesses(self, kept):
        """Extra relations to try when the template of the request alone does not close: e1 commuting or
        anticommuting with each new generator (origin k02), then pairs of new generators doing so. Any
        witness found this way is checked like every other; the guesses only steer the search."""
        alg = self.ambient(kept)
        W = alg.W
        out = []

        def rel(x, y, sign):
            gx, gy = {W.gen(x): Fr(1)}, {W.gen(y): Fr(1)}
            return alg.add(alg.mul(gx, gy), alg.mul(gy, gx), -sign)
        if self.origin == "k02":
            for signs in itertools.product((1, -1), repeat=len(self.gens)):
                rs = tuple(r for r in (rel("e1", g, sg) for g, sg in zip(self.gens, signs)) if r)
                if rs:
                    out.append(rs)
        pairs = list(itertools.combinations(self.gens, 2))
        if pairs:
            for signs in itertools.product((1, -1), repeat=len(pairs)):
                rs = tuple(r for r in (rel(x, y, sg) for (x, y), sg in zip(pairs, signs)) if r)
                if rs:
                    out.append(rs)
        if self.origin == "k02" and pairs:
            base = list(out)
            for a in base[:2 ** len(self.gens)]:
                for b in base[2 ** len(self.gens):]:
                    out.append(a + b)
        return out[:96]

    def basis_element(self, tpl, coords, kept):
        alg = self.ambient(kept)
        return {tpl["basis"][i]: c for i, c in coords.items() if c}

    # ---- refutations
    def refute(self, drop):
        key = frozenset(drop)
        if key in self.ref_cache:
            return self.ref_cache[key]
        kept = set(self.U) - set(drop)
        self.th_c = None
        tree = self.search(kept, [], self.names, 0)
        if tree is None:
            # over Q(sqrt c) for each c > 0, not a square, that the role makes the square of a generator
            alg, rw, _, _ = self.rewriter(kept)
            for g in sorted(self.names):
                gv = {alg.W.gen(g): Fr(1)}
                r = rw.nf(alg.mul(gv, gv))
                if set(r) == {alg.W.unit} and r[alg.W.unit] > 0 and not square(r[alg.W.unit]):
                    self.th_c = r[alg.W.unit]
                    tree = self.search(kept, [], self.names, 0)
                    if tree is not None:
                        break
            if tree is None:
                self.th_c = None
        cert = None
        if tree is not None:
            theta = None
            if self.th_c is not None:
                c = self.th_c
                theta = {"poly": [fs(-c), "0", "1"], "lo": "0", "hi": fs(c + 1)}
            cert = {"theta": theta, "tree": tree}
            ok, why = CHK.safe(CHK.check_refutation, cert, self.info, sorted(drop))
            if not ok:
                cert = None
        self.ref_cache[key] = cert
        return cert

    def search(self, kept, extra, names, depth):
        if time.time() > self.t_end:
            return None
        alg, rw, rels, ineqs = self.rewriter(kept, extra, names)
        W = alg.W
        one = {W.unit: Fr(1)}
        m = rw.member(one)
        if m is not None:
            return {"node": "close", "target": {"const": "1"}, "terms": terms_json(m, W)}
        for k, t in enumerate(ineqs):
            m = rw.member(t)
            if m is not None:
                return {"node": "close", "target": {"ineq": k}, "terms": terms_json(m, W)}
        forms = small_forms(alg, names, Surd(0, 1, self.th_c) if getattr(self, "th_c", None) else None)
        if "q14" in kept:
            for t in forms:
                tt = alg.mul(t, t)
                r = rw.nf(tt)
                if set(r) <= {W.unit} and r.get(W.unit, 0) < 0:
                    c = -r[W.unit]
                    m = rw.member(alg.add(tt, {W.unit: c}))
                    if m is not None:
                        return {"node": "positive", "t": [el_json(t, W)], "c": cj(c), "terms": terms_json(m, W)}
        if depth >= S:
            return None
        splitter = "q12" if "q12" in kept else ("q14" if "q14" in kept else None)
        inverse = "q13" in kept and W.assoc and splitter is None
        if not splitter and not inverse:
            return None
        pairs = []
        for a in forms:
            if not rw.nf(a):
                continue
            for b in forms:
                if not rw.nf(b):
                    continue
                ab = alg.mul(a, b)
                if not rw.nf(ab):
                    pairs.append((a, b, ab))
            if len(pairs) >= 8:
                break
        for a, b, ab in pairs[:8]:
            if splitter:
                k0 = self.search(kept, extra + [a], names, depth + 1)
                if k0 is None:
                    continue
                k1 = self.search(kept, extra + [b], names, depth + 1)
                if k1 is None:
                    continue
                return {"node": "split", "by": splitter, "a": el_json(a, W), "b": el_json(b, W),
                        "proof_ab": terms_json(rw.member(ab), W), "children": [k0, k1]}
            v = next(f"w{i}" for i in range(1, 99) if f"w{i}" not in names)
            k0 = self.search(kept, extra + [a], names, depth + 1)
            if k0 is None:
                continue
            vv = {W.gen(v): Fr(1)}
            av = alg.add(alg.mul(a, vv), {W.unit: Fr(1)}, -1)
            va = alg.add(alg.mul(vv, a), {W.unit: Fr(1)}, -1)
            k1 = self.search(kept, extra + [av, va], names | {v}, depth + 1)
            if k1 is None:
                continue
            return {"node": "inverse", "a": el_json(a, W), "v": v, "children": [k0, k1]}
        return None

    # ---- statuses
    def get_status(self, drop):
        d = frozenset(drop)
        if d in self.status:
            return self.status[d]
        for (k, w) in list(self.witness_of.items()):
            if w is not None and k <= d:
                self.status[d] = "WITNESSED"
                return "WITNESSED"
        for k in list(self.proof_of):
            if d <= k and self.proof_of[k] is not None:
                self.status[d] = "REFUTED"
                return "REFUTED"
        w = self.find_witness(d)
        if w is not None:
            self.witness_of[frozenset(CHK.witness_fail_units(w, self.info))] = w
            self.witness_of.setdefault(d, w)
            self.status[d] = "WITNESSED"
            return "WITNESSED"
        cert = self.refute(d)
        if cert is not None:
            self.proof_of[d] = cert
            self.status[d] = "REFUTED"
            return "REFUTED"
        self.status[d] = "UNDECIDED"
        return "UNDECIDED"

    def proof_for(self, drop):
        """A refutation of the candidate: any proof of a larger candidate also refutes it."""
        d = frozenset(drop)
        for k, p in self.proof_of.items():
            if p is not None and d <= k:
                cert = {"theta": p.get("theta"), "tree": p["tree"]}
                if CHK.safe(CHK.check_refutation, cert, self.info, sorted(d))[0]:
                    return cert
        return self.refute(d)

    def witness_for(self, drop):
        d = frozenset(drop)
        for k, w in self.witness_of.items():
            if w is not None and k <= d and CHK.safe(CHK.check_witness, w, self.info, sorted(d))[0]:
                return w
        return self.find_witness(d)

    def minimal(self):
        top = frozenset(self.U)
        seen, mins = set(), set()
        stack = [top]
        while stack:
            d = stack.pop()
            if d in seen:
                continue
            seen.add(d)
            if self.get_status(d) == "REFUTED":
                continue
            live = [d - {u} for u in sorted(d) if self.get_status(d - {u}) != "REFUTED"]
            if not live:
                mins.add(d)
            stack.extend(live)
        return sorted((sorted(m) for m in mins), key=lambda m: (len(m), m))


class Surd:
    """a + b*sqrt(c), a and b rational, for one c > 0 that is not a square; mixes with Fractions."""
    __slots__ = ("a", "b", "c")

    def __init__(self, a, b=0, c=None):
        self.a, self.b, self.c = Fr(a), Fr(b), c

    def _co(self, o):
        return o if isinstance(o, Surd) else Surd(o, 0, self.c)

    def __add__(self, o):
        o = self._co(o)
        return Surd(self.a + o.a, self.b + o.b, self.c or o.c)
    __radd__ = __add__

    def __neg__(self):
        return Surd(-self.a, -self.b, self.c)

    def __sub__(self, o):
        return self + (-self._co(o))

    def __rsub__(self, o):
        return self._co(o) - self

    def __mul__(self, o):
        o = self._co(o)
        c = self.c or o.c
        return Surd(self.a * o.a + (self.b * o.b * c if self.b and o.b else 0), self.a * o.b + self.b * o.a, c)
    __rmul__ = __mul__

    def __truediv__(self, o):
        o = self._co(o)
        c = self.c or o.c
        den = o.a * o.a - (o.b * o.b * c if o.b else 0)
        n = self * Surd(o.a, -o.b, c)
        return Surd(n.a / den, n.b / den, c)

    def __rtruediv__(self, o):
        return self._co(o) / self

    def __eq__(self, o):
        o = self._co(o)
        return self.a == o.a and self.b == o.b

    def __hash__(self):
        return hash((self.a, self.b))

    def __bool__(self):
        return bool(self.a) or bool(self.b)

    def sign(self):
        if not self.b:
            return (self.a > 0) - (self.a < 0)
        if not self.a:
            return 1 if self.b > 0 else -1
        if (self.a > 0) == (self.b > 0):
            return 1 if self.a > 0 else -1
        return (1 if self.a > 0 else -1) if self.a * self.a > self.b * self.b * self.c else (1 if self.b > 0 else -1)

    def __lt__(self, o):
        return (self - o).sign() < 0

    def __gt__(self, o):
        return (self - o).sign() > 0

    def json(self):
        return fs(self.a) if not self.b else [fs(self.a), fs(self.b)]

    def __repr__(self):
        return f"Surd({self.a},{self.b},{self.c})"


def square(q):
    from math import isqrt
    q = Fr(q)
    return q >= 0 and isqrt(q.numerator) ** 2 == q.numerator and isqrt(q.denominator) ** 2 == q.denominator


def small_forms(alg, names, th=None):
    W = alg.W
    gens = sorted(n for n in names)[:4]
    out = []
    for coefs in itertools.product((-1, 0, 1), repeat=len(gens)):
        if not any(coefs):
            continue
        consts = [0, 1, -1] + ([th, -th] if th is not None and sum(map(abs, coefs)) == 1 else [])
        for c0 in consts:
            v = {W.unit: c0 if isinstance(c0, Surd) else Fr(c0)} if c0 else {}
            for g, k in zip(gens, coefs):
                if k:
                    v[W.gen(g)] = Fr(k)
            out.append(v)
    out.sort(key=lambda v: (len(v), repr(sorted(v.items(), key=repr))))
    return out


def cj(c):
    return c.json() if isinstance(c, Surd) else fs(c)


def el_json(el, W):
    return [[cj(c), W.json(w)] for w, c in sorted(el.items(), key=lambda kv: W.okey(kv[0]))]


def terms_json(prov, W):
    out = []
    for (spec, path), c in sorted(prov.items(), key=lambda kv: repr(kv[0])):
        if spec[0] == "ctx":
            sj = {"ctx": spec[1]}
        else:
            sj = {"unit": spec[1], "args": {k: [["1", g]] for k, g in spec[2]}}
        steps = [[side, [["1", W.json(w)]]] for side, w in path]
        out.append([cj(c), sj, steps])
    return out


def zero_divisor_elements(tpl):
    """Elements a of the template with a singular left multiplication: a*b = 0 for some b != 0."""
    import sympy as sp
    n, T = tpl["n"], tpl["table"]

    def left_matrix(a):
        M = [[Fr(0)] * n for _ in range(n)]
        for j in range(n):
            # column j: a * b_j
            for i, ai in a.items():
                if not ai:
                    continue
                if i == 0:
                    M[j][j] += ai
                elif j == 0:
                    M[i][j] += ai
                else:
                    for k in range(n):
                        c = T.get((i, j, k))
                        if c:
                            M[k][j] += ai * c
        return M
    cands = []
    for i in range(1, n):
        cands.append({i: Fr(1)})
        cands.append({0: Fr(1), i: Fr(1)})
        cands.append({0: Fr(1), i: Fr(-1)})
    for i in range(1, n):
        for j in range(i + 1, n):
            cands.append({i: Fr(1), j: Fr(1)})
            cands.append({i: Fr(1), j: Fr(-1)})
    out = []
    for a in cands:
        M = sp.Matrix(left_matrix(a))
        if M.det() == 0:
            out.append(a)
        if len(out) >= 6:
            break
    return out


def quadratic_norm(tpl):
    """The quadratic-algebra method: solve x*x - t(x) x + n(x) 1 = 0 for a linear t and a quadratic n;
    then N = n and C(x) = t(x) 1 - x. Returns a NORM-shaped certificate or None (the checker decides
    whether it is multiplicative and positive definite)."""
    import sympy as sp
    n, T = tpl["n"], tpl["table"]

    def prod(i, j):
        v = [Fr(0)] * n
        if i == 0:
            v[j] += 1
        elif j == 0:
            v[i] += 1
        else:
            for k in range(n):
                c = T.get((i, j, k))
                if c:
                    v[k] += c
        return v
    ts = sp.symbols(f"t0:{n}")
    ns = {(i, j): sp.Symbol(f"n_{i}_{j}") for i in range(n) for j in range(i, n)}
    eqs = []
    for i in range(n):
        for j in range(i, n):
            if i == j:
                v = prod(i, i)
                for k in range(n):
                    e = sp.Rational(v[k].numerator, v[k].denominator) - (ts[i] if k == i else 0)
                    if k == 0:
                        e += ns[(i, i)]
                    eqs.append(e)
            else:
                v1, v2 = prod(i, j), prod(j, i)
                for k in range(n):
                    e = sp.Rational((v1[k] + v2[k]).numerator, (v1[k] + v2[k]).denominator)
                    e -= (ts[i] if k == j else 0) + (ts[j] if k == i else 0)
                    if k == 0:
                        e += 2 * ns[(i, j)]
                    eqs.append(e)
    sol = sp.solve(eqs, list(ts) + list(ns.values()), dict=True)
    if not sol:
        return None
    s = sol[0]
    if any(v not in s for v in list(ts) + list(ns.values())):
        return None

    def q(x):
        x = sp.Rational(x)
        return fs(Fr(int(x.p), int(x.q)))
    N = [[q(s[ns[(min(i, j), max(i, j))]]) for j in range(n)] for i in range(n)]
    Cm = [[q((s[ts[j]] if i == 0 else 0) - (1 if i == j else 0)) for j in range(n)] for i in range(n)]
    return {"N": N, "C": Cm}


# ================================================================ one world
def solve_world(world, budget=TIME_PER_WORLD):
    t_end = time.time() + budget
    b = world["builds"][0]
    atoms = read_role(b)
    info_simple = {"origin": b["origin"], "generators": sorted(b["generators"]), "frames": list(b["frames"]),
                   "atoms": atoms, "role": list(b["role"])}
    out = {"verdict": None, "freedom": None, "impossible": None, "known": None, "branches": [],
           "deciders": [], "refutations": [], "bounds": {"P2": P2, "P3": P3, "S": S, "list": "1"}}
    if any(has_inv(l) or has_inv(r) for _, l, r in atoms):
        out.update(verdict="FREEDOM", freedom={"slot": "0^-1", "fate": "undecided"})
        return out
    imp = impossible(info_simple)
    if imp is not None:
        out.update(verdict="IMPOSSIBLE", impossible={"kind": imp, "detail": []})
        return out
    kc = known(info_simple)
    if kc is not None:
        out.update(verdict="KNOWN_SUFFICES", known=kc)
        return out
    w = World(world, t_end)
    mins = w.minimal()
    perms = []
    if w.origin == "k02":
        for p in itertools.permutations(w.gens):
            perm = dict(zip(w.gens, p))
            if CHK.mirror_invariant(w.atoms, perm):
                perms.append(perm)
    used = set()
    branches = []
    for d in mins:
        if tuple(d) in used:
            continue
        used.add(tuple(d))
        mirror = None
        twin = sorted(MIRROR.get(u, u) for u in d)
        if perms and twin != d and twin in mins:
            used.add(tuple(twin))
            mirror = {"twin": twin, "perm": perms[0]}
        st = w.get_status(frozenset(d))
        wit = w.witness_for(d) if st == "WITNESSED" else None
        marks, proofs = {}, {}
        for u in ["q1", "q2"]:
            marks[u] = "PROTECTED"
        for u in ["q3", "q4", "q7", "q8", "q9", "q10", "q11"]:
            marks[u] = "WORKSHOP"
        if w.origin == "k01":
            for u in COPIES:
                marks[u] = "WORKSHOP"
        for u in UNITS[w.origin]:
            if u not in w.U:
                marks[u] = "FRAME"
            elif u in d:
                marks[u] = "FORCED"
                p = w.proof_for([x for x in d if x != u])
                if p is not None:
                    proofs[u] = p
            else:
                marks[u] = "ASSUMED"
        branches.append({"drop": d, "status": "witnessed" if wit is not None else "no_witness", "witness": wit,
                         "marks": marks, "proofs": proofs, "mirror": mirror})
    if all(x["status"] == "no_witness" for x in branches):
        verdict = "NO_WITNESS"
    elif len(branches) == 1:
        verdict = "NEW_KIND"
    else:
        verdict = "BRANCHES"
    U = set(w.U)
    for i, j in itertools.combinations(range(len(branches)), 2):
        ki, kj = U - set(branches[i]["drop"]), U - set(branches[j]["drop"])
        out["deciders"].append({"pair": [i, j], "only_kept_by_i": sorted(ki - kj), "only_kept_by_j": sorted(kj - ki)})
    out.update(verdict=verdict, branches=branches)
    return out


def run(worlds_dir, out_path):
    res = {}
    names = sorted(f for f in os.listdir(worlds_dir) if f.endswith(".json"))
    for f in names:
        with open(os.path.join(worlds_dir, f), encoding="utf-8") as fh:
            world = json.load(fh)
        t0 = time.time()
        try:
            o = solve_world(world)
        except Exception as e:  # a crash is an answer of its own, recorded as such
            o = {"verdict": "ERROR", "error": f"{type(e).__name__}: {e}"}
        res[f[:-5]] = {"procedure": o}
        print(f"{f}: {o['verdict']} ({time.time() - t0:.1f}s)", flush=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, sort_keys=True)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "run":
        run(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
        sys.exit(2)
