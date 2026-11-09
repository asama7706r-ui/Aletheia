#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The reference of blind test 5b: the truth of a world (protocol_v5b.md, Sections 2 and 8.1).

The truth is computed from the world, a pool of certificates (from the key and, when scoring,
from the procedure's output), and this module's own bounded search for refutations. It never
searches for witnesses: witnesses come from the certificates. It never imports the procedure.
Changes from test 5's ref_v5.py (protocol_v5b.md, Section 16):
1. A kept q6[on] gives instances in associative ambients too (test 5 audit, correction 1: a code error).
2. Copy instances may take as one argument a product of two names written in the role (correction 1: an
   undeclared limit). Only in non-associative ambients; with associativity the single names suffice.
3. Every valid refutation in the pool is offered to every candidate the classifier examines, not only to the
   candidate it is attached to and the candidates that keep more (workshop page, 10.9, fix 2).
"""
import itertools
import os
import sys
from fractions import Fraction as Fr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import certs_v5 as C  # noqa: E402

R = C.R

# the reference's own search (part of the truth's definition; Section 2.1 bounds)
SEARCH = {"L_nonassoc": C.BOUNDS["P2"], "L_assoc": C.BOUNDS["P2"] + 1,
          "max_split_tries": 8, "max_rows": 1500, "max_nodes": 60, "max_products": 40000,
          "L_fresh": 4, "max_inverse_tries": 4}


# ---------------------------------------------------------------- words and lengths
def wlen(w):
    if w == "1" or w == ():
        return 0
    if isinstance(w, str):
        return 1
    if isinstance(w, tuple) and all(isinstance(x, str) for x in w):
        return len(w)                   # associative word
    return wlen(w[0]) + wlen(w[1])


def wjson(w, amb):
    """A canonical word back to the JSON word form of the certificates."""
    if amb.assoc:
        if not w:
            return "1"
        j = w[0]
        for g in w[1:]:
            j = [j, g]
        return j
    if w == "1" or isinstance(w, str):
        return w
    return [wjson(w[0], amb), wjson(w[1], amb)]


def all_words(amb, names, L):
    """Every canonical word of length 1..L over names."""
    names = sorted(names)
    by_len = {1: [amb.name_word(g) for g in names]}
    for k in range(2, L + 1):
        if amb.assoc:
            prev = by_len[k - 1]
            ws = {amb.mulw(w, (g,)) for w in prev for g in names}
        else:
            ws = set()
            for i in range(1, k):
                for a in by_len[i]:
                    for b in by_len[k - i]:
                        ws.add(amb.mulw(a, b))
        by_len[k] = sorted(ws, key=amb.key)
    return by_len


def wkey(amb, w):
    return (wlen(w), amb.key(w))


# ---------------------------------------------------------------- the truncated ideal with provenance
class Ideal:
    """The span of the relators' multiples by words, up to total length L, with, for every row,
    its expression as a sum of coef * path(relator): the certificate terms."""

    def __init__(self, amb, names, rel_specs, L):
        self.amb, self.names, self.L = amb, names, L
        self.words = all_words(amb, names, L)
        self.rows = {}                   # pivot word -> (vec, prov)
        self.overflow = False
        queue = []
        for item in rel_specs:
            if len(item) == 3 and item[0] == "prov":
                _, prov, vec = item              # a relator given with its own provenance
            else:
                spec, vec = item
                prov = {(spec, ()): Fr(1)}
            if vec and max(wlen(w) for w in vec) <= L:
                r = self.insert(vec, dict(prov))
                if r is not None:
                    queue.append(r)
        products = 0
        while queue:
            if len(self.rows) > SEARCH["max_rows"] or products > SEARCH["max_products"]:
                self.overflow = True
                break
            vec, prov = queue.pop()
            top = max(wlen(w) for w in vec)
            for k in range(1, L - top + 1):
                for w in self.words[k]:
                    sides = ("L",) if amb.comm else ("L", "R")
                    for side in sides:
                        products += 1
                        nv = {}
                        for x, c in vec.items():
                            y = amb.mulw(w, x) if side == "L" else amb.mulw(x, w)
                            nv[y] = nv.get(y, 0) + c
                        nv = {x: c for x, c in nv.items() if c}
                        if not nv:
                            continue
                        step = (side, w)
                        np_ = {}
                        for (spec, path), c in prov.items():
                            np_[(spec, path + (step,))] = c
                        r = self.insert(nv, np_)
                        if r is not None:
                            queue.append(r)

    def reduce(self, vec, prov=None):
        vec = dict(vec)
        prov = dict(prov) if prov is not None else {}
        while True:
            cands = [w for w in vec if w in self.rows]
            if not cands:
                return vec, prov
            w = max(cands, key=lambda x: wkey(self.amb, x))
            c = vec[w]
            rv, rp = self.rows[w]
            for x, d in rv.items():
                vec[x] = vec.get(x, 0) - c * d
                if vec[x] == 0:
                    del vec[x]
            for a, d in rp.items():
                prov[a] = prov.get(a, 0) - c * d
                if prov[a] == 0:
                    del prov[a]

    def insert(self, vec, prov):
        vec, prov = self.reduce(vec, prov)
        if not vec:
            return None
        piv = max(vec, key=lambda x: wkey(self.amb, x))
        c = vec[piv]
        vec = {x: d / c for x, d in vec.items()}
        prov = {a: d / c for a, d in prov.items()}
        self.rows[piv] = (vec, prov)
        return vec, prov

    def member(self, target):
        """Certificate terms expressing target as an ideal element, or None."""
        rest, minus = self.reduce(target, {})
        if rest:
            return None
        # target - sum(c_i row_i) = 0 with the combination recorded negated in `minus`
        return {a: -d for a, d in minus.items() if d}

    def nf(self, vec):
        return self.reduce(vec, {})[0]


def terms_json(prov, amb, specs_json):
    out = []
    for (spec, path), c in sorted(prov.items(), key=lambda kv: repr(kv[0])):
        steps = [[side, [["1", wjson(w, amb)]]] for side, w in path]
        out.append([C.coef_json(c), specs_json[spec], steps])
    return out


def is_square(q):
    from math import isqrt
    q = Fr(q)
    if q < 0:
        return False
    a, b = q.numerator, q.denominator
    return isqrt(a) ** 2 == a and isqrt(b) ** 2 == b


def role_products(atoms):
    """The products of exactly two names written in the role, in order of first appearance (change 2)."""
    out = []

    def walk(ast):
        if ast[0] == "prod" and len(ast[1]) == 2 and all(x[0] == "name" for x in ast[1]):
            p = (ast[1][0][1], ast[1][1][1])
            if p not in out:
                out.append(p)
        if ast[0] in ("prod", "sum"):
            for x in ast[1]:
                walk(x)
        elif ast[0] in ("neg", "inv"):
            walk(ast[1])
    for _op, l, r in atoms:
        walk(l)
        walk(r)
    return out


def cited_units(node):
    """The units a refutation tree cites: copy and rule instances, split units, inverse (q13), positive (q14).
    A candidate that drops one of them cannot accept the tree, so the classifier skips it without a check."""
    out = set()
    if isinstance(node, dict):
        if "unit" in node and isinstance(node["unit"], str):
            out.add(node["unit"])
        kind = node.get("node")
        if kind == "split":
            out.add(node.get("by"))
        elif kind == "inverse":
            out.add("q13")
        elif kind == "positive":
            out.add("q14")
        for v in node.values():
            out |= cited_units(v)
    elif isinstance(node, list):
        for v in node:
            out |= cited_units(v)
    return out


# ---------------------------------------------------------------- the refutation search
class Searcher:
    def __init__(self, info, drop, shared=None, c=None):
        self.info = info
        self.c = c                        # search over Q(sqrt c) when c is given (c > 0, not a square)
        self.th = C.Qs(0, 1, c) if c is not None else None
        self.shared = shared if shared is not None else {}
        self.nodes = 0
        U = C.judged_units(info["origin"], info["frames"])
        self.kept = set(U) - set(drop)
        frame = "f03" in info["frames"]
        self.assoc = frame or "q5" in self.kept
        self.comm = "q6" in self.kept
        self.amb = C.Ambient(C.Field(None), self.assoc, self.comm)
        self.L = SEARCH["L_assoc"] if self.assoc else SEARCH["L_nonassoc"]
        self.base_names = set(info["generators"]) | ({"e1"} if info["origin"] == "k02" else set())
        rels, ineqs = C.role_context(info["atoms"], self.amb, self.base_names, info["origin"])
        self.rels0 = [self.q(r) for r in rels]
        self.ineqs = [self.q(r) for r in ineqs]
        self.copies = [u for u in sorted(self.kept) if u in C.COPIES and (not self.assoc or u == "q6[on]")]
        self.pairs = role_products(info["atoms"])

    @staticmethod
    def q(el):
        return {w: c[0] for w, c in el.items()}

    def elq(self, vec):
        return {w: (c,) for w, c in vec.items()}

    def instance_specs(self, names):
        """Instances of the kept copies with small arguments: names, and (non-associative ambients only) one
        argument that is a product of two names written in the role."""
        out = []
        if not self.copies:
            return out
        args1 = [g for g in sorted(names) if g != "e1"] + (["e1"] if "e1" in names else [])
        pairs = [] if self.assoc else [p for p in self.pairs if p[0] in names and p[1] in names]
        for u in self.copies:
            vars_ = {"q5[onn]": "bc", "q5[non]": "ac", "q5[nno]": "ab", "q5[oon]": "c", "q5[ono]": "b",
                     "q5[noo]": "a", "q6[on]": "b"}[u]
            combos = list(itertools.product(args1, repeat=len(vars_)))
            for pos in range(len(vars_)):                    # exactly one argument is a product of two names
                combos += list(itertools.product(*[pairs if k == pos else args1 for k in range(len(vars_))]))
            for combo in combos:
                args = {v: [["1", list(g) if isinstance(g, tuple) else g]] for v, g in zip(vars_, combo)}
                vec = self.q(C.copy_instance(self.amb, u, args, names))
                if vec:
                    out.append((("unit", u, tuple(sorted(zip(vars_, combo)))), vec))
        return out

    def ideal(self, extra, names):
        key = (self.c, self.assoc, self.comm, tuple(self.copies),
               tuple(repr(sorted(e.items(), key=repr)) for e in extra), tuple(sorted(names)))
        if key in self.shared:
            return self.shared[key]
        specs = [(("ctx", i), r) for i, r in enumerate(self.rels0)]
        for j, e in enumerate(extra):
            specs.append((("ctx", len(self.rels0) + j), e))
        specs += self.instance_specs(names)
        L = min(self.L, SEARCH["L_fresh"]) if names != self.base_names else self.L
        I = Ideal(self.amb, names, specs, L)
        self.shared[key] = I
        return I

    def spec_json(self, spec):
        if spec[0] == "ctx":
            return {"ctx": spec[1]}
        _, u, args = spec
        return {"unit": u, "args": {k: [["1", list(g) if isinstance(g, tuple) else g]] for k, g in args}}

    def close(self, I, extra):
        """A close node, or None."""
        one = {self.amb.unit: Fr(1)}
        m = I.member(one)
        if m is not None:
            return {"node": "close", "target": {"const": "1"}, "terms": self.tj(m)}
        for k, t in enumerate(self.ineqs):
            m = I.member(t)
            if m is not None:
                return {"node": "close", "target": {"ineq": k}, "terms": self.tj(m)}
        return None

    def tj(self, prov):
        specs = {}
        for (spec, _path) in prov:
            specs[spec] = self.spec_json(spec)
        return terms_json(prov, self.amb, specs)

    def linear_forms(self, names):
        gens = sorted(n for n in names if n != "e1") + (["e1"] if "e1" in names else [])
        gens = gens[:4]
        out = []
        for coefs in itertools.product((-1, 0, 1), repeat=len(gens)):
            if not any(coefs):
                continue
            consts = [0, 1, -1] + ([self.th, -self.th] if self.th is not None and sum(map(abs, coefs)) == 1 else [])
            for c0 in consts:
                v = {self.amb.unit: c0 if isinstance(c0, C.Qs) else Fr(c0)} if c0 else {}
                for g, k in zip(gens, coefs):
                    if k:
                        v[self.amb.name_word(g)] = Fr(k)
                out.append(v)
        out.sort(key=lambda v: (len(v), repr(sorted(v.items(), key=repr))))
        return out

    def mul(self, a, b):
        return self.q(self.amb.mul(self.elq(a), self.elq(b)))

    def ej(self, vec):
        return [[C.coef_json(c), wjson(w, self.amb)] for w, c in sorted(vec.items(), key=lambda kv: wkey(self.amb, kv[0]))]

    def refute(self, extra=(), names=None, depth=0):
        names = names or self.base_names
        extra = list(extra)
        self.nodes += 1
        if self.nodes > SEARCH["max_nodes"]:
            return None
        I = self.ideal(extra, names)
        nd = self.close(I, extra)
        if nd is not None:
            return nd
        if I.overflow:
            return None
        forms = self.linear_forms(names)
        # positivity (q14 kept): t*t + c with c > 0 in the ideal
        if "q14" in self.kept:
            for t in forms:
                r = I.nf(self.mul(t, t))
                if set(r) <= {self.amb.unit} and r.get(self.amb.unit, 0) < 0:
                    c = -r[self.amb.unit]
                    target = dict(self.mul(t, t))
                    target[self.amb.unit] = target.get(self.amb.unit, 0) + c
                    target = {w: x for w, x in target.items() if x}
                    m = I.member(target)
                    if m is not None:
                        return {"node": "positive", "t": [self.ej(t)], "c": C.coef_json(c), "terms": self.tj(m)}
        if depth >= C.BOUNDS["S"]:
            return None
        splitter = "q12" if "q12" in self.kept else ("q14" if "q14" in self.kept else None)
        pairs = []
        if splitter or ("q13" in self.kept and self.assoc):
            for a, b in itertools.combinations_with_replacement(forms, 2):
                if I.nf(a) == {} or I.nf(b) == {}:
                    continue
                ab = self.mul(a, b)
                if I.nf(ab) == {}:
                    pairs.append((a, b, ab))
                elif not self.comm:
                    ba = self.mul(b, a)
                    if I.nf(ba) == {}:
                        pairs.append((b, a, ba))
                if len(pairs) >= SEARCH["max_split_tries"]:
                    break
        if self.th is not None:
            # over Q(sqrt c), try first the pairs that use sqrt(c)
            pairs.sort(key=lambda p: not any(isinstance(x, C.Qs) and x.b for x in list(p[0].values()) + list(p[1].values())))
        inverse_tries = 0
        for a, b, ab in pairs:
            if splitter:
                k0 = self.refute(extra + [a], names, depth + 1)
                if k0 is None:
                    continue
                k1 = self.refute(extra + [b], names, depth + 1)
                if k1 is None:
                    continue
                return {"node": "split", "by": splitter, "a": self.ej(a), "b": self.ej(b),
                        "proof_ab": self.tj(I.member(ab)), "children": [k0, k1]}
            if "q13" in self.kept and self.assoc:
                inverse_tries += 1
                if inverse_tries > SEARCH["max_inverse_tries"]:
                    break
                v = next(f"v{i}" for i in range(1, 99) if f"v{i}" not in names)
                k0 = self.refute(extra + [a], names, depth + 1)
                if k0 is None:
                    continue
                vw = {self.amb.name_word(v): Fr(1)}
                av = self.mul(a, vw)
                av[self.amb.unit] = av.get(self.amb.unit, 0) - 1
                va = self.mul(vw, a)
                va[self.amb.unit] = va.get(self.amb.unit, 0) - 1
                k1 = self.refute(extra + [{w: c for w, c in av.items() if c}, {w: c for w, c in va.items() if c}],
                                 names | {v}, depth + 1)
                if k1 is None:
                    continue
                return {"node": "inverse", "a": self.ej(a), "v": v, "children": [k0, k1]}
        return None


def square_roots_needed(info, drop, shared):
    """The c > 0, not squares, with g*g = c for a generator g in the role's ideal (over Q)."""
    s = Searcher(info, drop, shared)
    I = s.ideal([], s.base_names)
    out = []
    for g in sorted(s.base_names):
        gw = {s.amb.name_word(g): Fr(1)}
        r = I.nf(s.mul(gw, gw))
        if set(r) == {s.amb.unit}:
            c = r[s.amb.unit]
            if c > 0 and not is_square(c) and c not in out:
                out.append(c)
    return out[:2]


def search_refutation(info, drop, shared=None):
    """A refutation certificate of the candidate `drop`, found by the reference's bounded search, or None.
    The search runs over Q, then, if needed, over Q(sqrt c) for each c that the role makes a square."""
    shared = shared if shared is not None else {}
    tree, c = Searcher(info, drop, shared).refute(), None
    if tree is None:
        for cc in square_roots_needed(info, drop, shared):
            tree = Searcher(info, drop, shared, cc).refute()
            if tree is not None:
                c = cc
                break
    if tree is None:
        return None
    theta = {"poly": [C.fstr(-c), "0", "1"], "lo": "0", "hi": C.fstr(c + 1)} if c is not None else None
    cert = {"theta": theta, "tree": tree}
    ok, why = C.safe(C.check_refutation, cert, info, drop)
    if not ok:
        raise RuntimeError(f"the reference built an invalid refutation ({why}) for {drop}")
    return cert


# ---------------------------------------------------------------- known kinds (2.8)
def role_polys(info, with_e1):
    import sympy as sp
    gens = info["generators"]
    syms = {g: sp.Symbol("g_" + g) for g in gens}
    if with_e1:
        syms["e1"] = sp.Symbol("e_1")

    class P:
        def const(self, q):
            return sp.Rational(q.numerator, q.denominator)

        def name(self, g):
            C.need(g in syms, f"name {g} has no polynomial variable")
            return syms[g]

        def add(self, xs):
            return sp.Add(*xs)

        def neg(self, x):
            return -x

        def mul(self, x, y):
            return sp.expand(x * y)

        def inv(self, x):
            raise C.CertError("^-1 has no polynomial reading")
    eqs, zs = [], []
    for k, (op, lhs, rhs) in enumerate(info["atoms"]):
        a = C.evaluate(lhs, P(), [])
        b = C.evaluate(rhs, P(), [])
        d = sp.expand(a - b)
        if op == "=":
            eqs.append(d)
        else:
            z = sp.Symbol(f"z_{k}")
            zs.append(z)
            eqs.append(sp.expand(1 - z * d))
    if with_e1:
        eqs.append(syms["e1"] ** 2 + 1)
    return eqs, list(syms.values()) + zs


def complex_solvable(info, with_e1):
    import sympy as sp
    eqs, vs = role_polys(info, with_e1)
    eqs = [e for e in eqs if e != 0]
    if not eqs:
        return True
    G = sp.groebner(eqs, *vs, order="grevlex")
    return list(G.exprs) != [1]


def real_solution_count(info):
    """Number of distinct real solutions of the role read in the reals (Hermite's quadratic form),
    or None when the solution set is not zero-dimensional."""
    import sympy as sp
    eqs, vs = role_polys(info, False)
    eqs = [e for e in eqs if e != 0]
    G = sp.groebner(eqs, *vs, order="grevlex")
    if list(G.exprs) == [1]:
        return 0
    if not G.is_zero_dimensional:
        return None
    lms = [sp.Poly(g, *vs).monoms(order="grevlex")[0] for g in G.exprs]
    maxdeg = [min(m[i] for m in lms if m[i] > 0 and all(m[j] == 0 for j in range(len(vs)) if j != i))
              for i in range(len(vs))]
    basis = []
    for exps in itertools.product(*[range(d) for d in maxdeg]):
        if not any(all(e >= l for e, l in zip(exps, lm)) for lm in lms):
            basis.append(exps)
    mono = [sp.Mul(*[v ** e for v, e in zip(vs, ex)]) for ex in basis]
    idx = {ex: i for i, ex in enumerate(basis)}

    def coords(expr):
        _, r = G.reduce(sp.expand(expr))
        p = sp.Poly(r, *vs)
        out = [sp.Integer(0)] * len(basis)
        for m, c in p.terms():
            out[idx[m]] = c
        return out

    def trace(f):
        return sum(coords(f * mono[k])[k] for k in range(len(basis)))
    n = len(basis)
    H = sp.zeros(n, n)
    for i in range(n):
        for j in range(i, n):
            H[i, j] = H[j, i] = trace(mono[i] * mono[j])
    x = sp.Symbol("x")
    cp = sp.Poly(H.charpoly(x).as_expr(), x)

    def descartes(p):
        cs = [c for c in p.all_coeffs() if c != 0]
        return sum(1 for a, b in zip(cs, cs[1:]) if (a > 0) != (b > 0))
    pos = descartes(cp)
    neg = descartes(sp.Poly(cp.as_expr().subs(x, -x), x))
    return pos - neg


def known_truth(info, pool):
    """The smallest tower kind holding a solution of the role: 'k01', 'k02', None (no solution),
    or 'undetermined' (a complex solution, and realness not decidable here)."""
    for c in pool.get("known", []):
        if c.get("kind") == "k01" and info["origin"] == "k01" and C.safe(C.check_known, c, info)[0]:
            return "k01"
    if info["origin"] == "k02":
        return "k02" if complex_solvable(info, True) else None
    if not complex_solvable(info, False):
        return None
    n = real_solution_count(info)
    if n is None:
        return "undetermined"
    return "k01" if n > 0 else "k02"


# ---------------------------------------------------------------- the truth
def has_free_slot(info):
    return any(C.contains_inv(l) or C.contains_inv(r) for _, l, r in info["atoms"])


def marks_of(info, drop):
    origin, frames = info["origin"], info["frames"]
    U = C.judged_units(origin, frames)
    out = {u: "PROTECTED" for u in C.PROTECTED}
    out.update({u: "WORKSHOP" for u in C.WORKSHOP})
    if origin == "k01":
        out.update({u: "WORKSHOP" for u in C.COPIES})
    for u in C.UNITS[origin]:
        if u not in U:
            out[u] = "FRAME"
        elif u in drop:
            out[u] = "FORCED"
        else:
            out[u] = "ASSUMED"
    return out


class Classifier:
    """Statuses of candidates from certificates and the reference's search (2.4)."""

    def __init__(self, info, witnesses, refutations, search=True, log=None, certs=None):
        self.info = info
        self.U = C.judged_units(info["origin"], info["frames"])
        self.fails = [frozenset(f) for f in witnesses]
        self.refuted = [frozenset(r) for r in refutations]
        self.search = search
        self.status_cache = {}
        self.found = []                  # refutations found by the search: (drop, cert)
        self.log = log if log is not None else []
        self.perms = self.mirror_perms()
        self.shared = {}
        # change 3: the pool's valid refutations, each offered to every candidate examined
        self.certs = [(frozenset(cited_units(cert)), cert) for _drop, cert in (certs or [])]
        self.cert_fails = [[] for _ in self.certs]   # kept sets a certificate was checked and rejected for
        self.reused = []                 # (drop, index of the certificate) refuted by reuse

    def reuse(self, d):
        """True when a pool certificate, offered to the candidate d (or its mirror), is accepted by the checker.
        Rejections are remembered: a certificate rejected while K is kept is rejected while less is kept."""
        for s in sorted(self.sym(d), key=sorted):
            kept = frozenset(self.U) - s
            for i, (need, cert) in enumerate(self.certs):
                if not need <= kept or any(kept <= k for k in self.cert_fails[i]):
                    continue
                if C.safe(C.check_refutation, cert, self.info, sorted(s))[0]:
                    self.refuted.append(s)
                    self.reused.append((sorted(s), i))
                    return True
                self.cert_fails[i].append(kept)
        return False

    def mirror_perms(self):
        if self.info["origin"] != "k02":
            return []
        gens = self.info["generators"]
        out = []
        for p in itertools.permutations(gens):
            perm = dict(zip(gens, p))
            if C.mirror_invariant(self.info["atoms"], perm):
                out.append(perm)
        return out

    def sym(self, d):
        """The candidate and, when the role is mirror-invariant, its mirror (same status by symmetry)."""
        out = {frozenset(d)}
        if self.perms:
            out.add(frozenset(C.mirror_set(d)))
        return out

    def witnessed(self, d):
        return any(f <= s for f in self.fails for s in self.sym(d))

    def refuted_known(self, d):
        return any(s <= r for r in self.refuted for s in self.sym(d))

    def status(self, d):
        d = frozenset(d)
        if d in self.status_cache:
            return self.status_cache[d]
        if self.witnessed(d):
            st = "WITNESSED"
        elif self.refuted_known(d):
            st = "REFUTED"
        elif self.reuse(d):
            st = "REFUTED"
        elif self.search:
            cert = None
            for s in sorted(self.sym(d), key=sorted):
                cert = search_refutation(self.info, sorted(s), self.shared)
                if cert is not None:
                    self.refuted.append(s)
                    self.found.append((sorted(s), cert))
                    break
            st = "REFUTED" if cert is not None else "UNDECIDED"
        else:
            st = "UNDECIDED"
        self.status_cache[d] = st
        return st

    def minimal(self):
        """The minimal non-refuted candidates, top-down from U (V8 guarantees U is witnessed)."""
        top = frozenset(self.U)
        seen, mins = set(), set()
        stack = [top]
        while stack:
            d = stack.pop()
            if d in seen:
                continue
            seen.add(d)
            if self.status(d) == "REFUTED":
                continue
            children = [d - {u} for u in sorted(d)]
            live = [c for c in children if self.status(c) != "REFUTED"]
            if not live:
                mins.add(d)
            stack.extend(live)
        return sorted((sorted(m) for m in mins), key=lambda m: (len(m), m))


def merge_mirrors(branches, info, perms):
    """Section 2.7: pair each branch with its mirror twin when the role is mirror-invariant."""
    if not perms:
        return [{"drop": b, "mirror": None} for b in branches]
    out, used = [], set()
    for b in branches:
        if tuple(b) in used:
            continue
        twin = C.mirror_set(b)
        if twin != sorted(b) and twin in branches:
            used.add(tuple(twin))
            used.add(tuple(b))
            out.append({"drop": b, "mirror": {"twin": twin, "perm": perms[0]}})
        else:
            used.add(tuple(b))
            out.append({"drop": b, "mirror": None})
    return out


def truth(world, pool, search=True):
    """The truth of a world from a certificate pool:
    pool = {"witness": [(drop, cert)], "refutation": [(drop, cert)], "known": [cert]}.
    Invalid certificates are ignored here (the validator and the scorer report them)."""
    return truth_full(world, pool, search)[0]


def truth_full(world, pool, search=True):
    """(truth, classifier or None). The classifier answers the baselines' questions on candidates."""
    info = C.world_info(world)
    if has_free_slot(info):
        return {"verdict": "FREEDOM", "freedom": {"slot": "0^-1", "fate": "undecided"}}, None
    cc = C.congruence_contradiction(info)
    if cc is not None:
        return {"verdict": "IMPOSSIBLE", "impossible": {"kind": cc[0]}}, None
    k = known_truth(info, pool)
    if k == "undetermined":
        return {"verdict": "UNDETERMINED", "why": "a complex solution exists, and realness is not decidable (V14)"}, None
    if k is not None:
        return {"verdict": "KNOWN_SUFFICES", "known": {"kind": k}}, None
    fails = []
    for drop, w in pool.get("witness", []):
        if C.safe(C.check_witness, w, info, drop)[0]:
            fails.append(C.witness_fail_units(w, info))
    valid = [(drop, r) for drop, r in pool.get("refutation", []) if C.safe(C.check_refutation, r, info, drop)[0]]
    cl = Classifier(info, fails, [drop for drop, _ in valid], search=search, certs=valid)
    U = cl.U
    if cl.status(frozenset(U)) != "WITNESSED":
        return {"verdict": "OUTSIDE_W", "why": "no witness of the largest candidate (V8)"}, cl
    mins = cl.minimal()
    statuses = {tuple(m): cl.status(m) for m in mins}
    merged = merge_mirrors(mins, info, cl.perms)
    branches = []
    for b in merged:
        st = statuses[tuple(b["drop"])]
        branches.append({"drop": b["drop"], "status": "witnessed" if st == "WITNESSED" else "no_witness",
                         "mirror": b["mirror"], "marks": marks_of(info, b["drop"])})
    if all(b["status"] == "no_witness" for b in branches):
        verdict = "NO_WITNESS"
    elif len(branches) == 1:
        verdict = "NEW_KIND"
    else:
        verdict = "BRANCHES"
    return {"verdict": verdict, "branches": branches, "found_refutations": cl.found, "reused": cl.reused,
            "statuses": {",".join(sorted(k)) or "-": v for k, v in cl.status_cache.items()}}, cl
