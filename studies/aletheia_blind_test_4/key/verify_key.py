#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Blind test 4: the world generator's own check of its worlds and its key.

Written from protocol_v4.md alone (Sections 2-7), with the registry and the v0.4 reader, BEFORE the sealed
validator is run. It never imports or reads the procedure or the scorer.

    python key/verify_key.py worlds key/key.json

For every world and every filler it recomputes:
  * F1 (dimensions, Section 2.5), F2 (symmetry, Sections 2.2-2.4), F3 (old observations, Section 2.6, by exact
    Fourier-Motzkin elimination over the rationals), the verdict and its reason (Section 2.7);
  * the four baselines of Section 7 (FIX, DERIVE, DIMS, FORK_ALL);
  * the validity rules V1-V10 and V13 of Section 3 (V11 cannot be checked here: the dev fingerprints are sealed
    inside the validator, and the generator never opened dev/);
  * the trap conditions and the composition of Section 6;
  * the key entries (V12), the decisive states of several-filler worlds included (Sections 2.8 and 5).
It prints one report and ends with "VERIFY: OK" or the list of problems.
"""
import glob
import itertools
import json
import os
import random
import re
import sys
from fractions import Fraction as Fr

import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "lang"))
import reader_v0 as R  # noqa: E402

MEANING_T = ("rev_t", "refl_x", "conj_c")
BASE = ("L", "M", "Q", "T")
DIM_OF_T = {"rev_t": "T", "refl_x": "L", "conj_c": "Q"}
SAME, ANOTHER, INVALID, COND = "SAME_LAW_NEW_STATE", "ANOTHER_LAW", "INVALID", "CONDITIONAL"
LIMIT = 10 ** 9
NAME_OK = re.compile(r"[a-z][a-z0-9]{1,5}\Z")
RNG = random.Random(4)


# ----------------------------------------------------------------- small helpers

def rat(s):
    return sp.Rational(s)


def tofr(x):
    x = sp.nsimplify(x) if not isinstance(x, sp.Basic) else x
    if not x.is_Rational:
        raise ValueError(f"not a rational number: {x}")
    return Fr(int(x.p), int(x.q))


def frs(x):
    return str(Fr(x))


def parse_action(v):
    if isinstance(v, list):
        return sp.Matrix([[sp.Rational(e) for e in row] for row in v])
    return sp.Rational(v)


def is_matrix(a):
    return isinstance(a, sp.MatrixBase)


def inv(a):
    return a.inv() if is_matrix(a) else a ** -1


def norm_dims(d):
    return {k: Fr(v) for k, v in sorted(d.items()) if Fr(v) != 0}


def dims_str(d):
    if d == "undetermined":
        return d
    return "{" + ", ".join(f"{k}: {v}" for k, v in sorted(d.items())) + "}"


def tlabel(T):
    return T if isinstance(T, str) else f"exch({T[1]},{T[2]})"


def ttype(T):
    if isinstance(T, tuple):
        return "cast"
    return "kind" if T == "rot_z" else "meaning"


def is_sign(s):
    return ":" in s.name


_ZERO = {}


def is_zero(e):
    """Exact test that a rational function is identically zero (random points first, then expansion)."""
    e = sp.sympify(e)
    if e == 0:
        return True
    key = sp.srepr(e)
    if key in _ZERO:
        return _ZERO[key]
    syms = sorted(e.free_symbols, key=lambda s: s.name)
    for _ in range(3):
        pt = {s: sp.Rational(RNG.randint(-99991, 99991), RNG.randint(1, 997)) for s in syms}
        v = e.xreplace(pt)
        if v.is_Rational and v != 0:
            _ZERO[key] = False
            return False
    num, _den = sp.fraction(sp.together(e))
    out = sp.expand(num) == 0
    _ZERO[key] = out
    return out


def witness(e):
    """A point where e is defined and not zero (e is known not to be identically zero)."""
    syms = sorted(e.free_symbols, key=lambda s: s.name)
    for _ in range(200):
        pt = {s: sp.Rational(RNG.randint(-9, 9), RNG.randint(1, 3)) for s in syms}
        v = e.xreplace(pt)
        if v.is_Rational and v != 0:
            return {s.name: str(val) for s, val in pt.items()}
    return None


# ----------------------------------------------------------------- registry

class Registry:
    def __init__(self):
        self.doc = R.load(os.path.join(ROOT, "registry", "registry.json"))
        ctx, info = R.check_registry(self.doc)
        if ctx.errors:
            raise SystemExit("registry rejected by the reader:\n" + "\n".join(ctx.errors))
        self.info = info
        self.sha = R.sha256_of(info["canon"])
        self.meanings = {m["id"]: m for m in self.doc["meanings"]}
        self.kinds = {k["id"]: k for k in self.doc["kinds"]}
        self.instruments = {i["id"]: i for i in self.doc["instruments"]}
        self.defs = {d["id"]: d for d in self.doc["definitions"]}
        self.ids = set(info["ids"])

    def size(self, kind):
        n = 1
        for d in self.kinds[kind]["shape"]:
            n *= d
        return n

    def definition_rhs(self, did, mid):
        rel = R.Parser(self.defs[did]["eq"]).relation({"="})
        assert rel[2] == ("name", mid), "definitions are written 'meaning = expression'"
        return rel[3]

    def meaning_action(self, mid, T):
        """Action of a meaning-reading T on a meaning: a Rational, a Matrix, or None for '?'."""
        v = self.meanings[mid]["under"][T]
        if v == "?":
            return None
        if isinstance(v, dict):
            return self._def_action(self.definition_rhs(v["derived"], mid), T)
        return parse_action(v)

    def _def_action(self, node, T):
        t = node[0]
        if t == "num":
            return sp.Integer(1)
        if t == "name":
            return self.meaning_action(node[1], T)
        if t == "neg":
            return self._def_action(node[1], T)
        if t == "pow":
            a = self._def_action(node[1], T)
            return None if a is None else a ** node[2]
        if t == "D":
            a, b = self.meaning_action(node[1], T), self.meaning_action(node[2], T)
            return None if a is None or b is None else a * inv(b)
        a, b = self._def_action(node[2], T), self._def_action(node[3], T)
        if a is None or b is None:
            return None
        if node[1] == "*":
            return a * b
        if node[1] == "/":
            return a * inv(b)
        if a != b:
            raise ValueError("a sum of terms that act differently")
        return a

    def meaning_dims(self, mid):
        """Dimensions of a meaning: the anchor instrument's unit, or derived through the definitions; else None."""
        a = self.meanings[mid]["anchor"]
        if "instrument" in a:
            return norm_dims(self.instruments[a["instrument"]]["unit"])
        if "derived" in a:
            return self._def_dims(self.definition_rhs(a["derived"], mid))
        return None

    def _def_dims(self, node):
        t = node[0]
        if t == "num":
            return {}
        if t == "name":
            return self.meaning_dims(node[1])
        if t == "neg":
            return self._def_dims(node[1])
        if t == "pow":
            a = self._def_dims(node[1])
            return None if a is None else norm_dims({k: v * node[2] for k, v in a.items()})
        if t == "D":
            a, b = self.meaning_dims(node[1]), self.meaning_dims(node[2])
            return None if a is None or b is None else dsub(a, b)
        a, b = self._def_dims(node[2]), self._def_dims(node[3])
        if a is None or b is None:
            return None
        if node[1] == "*":
            return dadd(a, b)
        if node[1] == "/":
            return dsub(a, b)
        return a if a == b else None


def dadd(a, b):
    return norm_dims({k: Fr(a.get(k, 0)) + Fr(b.get(k, 0)) for k in set(a) | set(b)})


def dsub(a, b):
    return norm_dims({k: Fr(a.get(k, 0)) - Fr(b.get(k, 0)) for k in set(a) | set(b)})


# ----------------------------------------------------------------- expressions

def parse_eq(s):
    rel = R.Parser(s).relation({"="})
    return rel[2], rel[3]


def to_sp(node):
    t = node[0]
    if t == "num":
        return sp.Integer(node[1])
    if t == "name":
        return sp.Symbol(node[1])
    if t == "neg":
        return -to_sp(node[1])
    if t == "pow":
        return to_sp(node[1]) ** node[2]
    if t == "bin":
        a, b = to_sp(node[2]), to_sp(node[3])
        if node[1] == "+":
            return a + b
        if node[1] == "-":
            return a - b
        if node[1] == "*":
            return a * b
        return a / b
    raise ValueError(f"not allowed in a test-4 law: {node[0]}")


def ast_walk(node):
    yield node
    if node[0] in ("neg",):
        yield from ast_walk(node[1])
    elif node[0] == "pow":
        yield from ast_walk(node[1])
    elif node[0] == "bin":
        yield from ast_walk(node[2])
        yield from ast_walk(node[3])


# ----------------------------------------------------------------- world model

class Rec:
    """A quantity of the world or a new quantity of a filler."""

    def __init__(self, **kw):
        self.__dict__.update(kw)

    @property
    def syms(self):
        return [sp.Symbol(c) for c in self.comps]


class Filler:
    pass


class World:
    def __init__(self, reg, doc, path):
        self.reg, self.doc, self.path = reg, doc, path
        self.id = doc["id"]
        self.bodies = doc["bodies"]
        self.recs = []
        for q in doc["quantities"]:
            kind = reg.meanings[q["meaning"]]["kind"]
            n = reg.size(kind)
            self.recs.append(Rec(id=q["id"], meaning=q["meaning"], owner=q["owner"], kind=kind, n=n,
                                 comps=list(q["components"]) if n > 1 else [q["id"]], dims=q["dims"],
                                 value=q["value"], new=False, under=None, old_value=None, route=None))
        self.law = doc["laws"][0]
        lhs, rhs = parse_eq(self.law["eq"])
        self.law_lhs, self.law_ast = lhs, rhs
        self.y = sp.Symbol(lhs[1]) if lhs[0] == "name" else None
        self.f = to_sp(rhs)
        self.law_syms = self.f.free_symbols | {self.y}
        self.observers = {o["id"]: o for o in doc["observers"]}
        acc = self.law["accepted_at"]
        self.old = [o for o in doc["observations"] if o["epoch"] <= acc]
        self.new = [o for o in doc["observations"] if o["epoch"] > acc]
        self.fillers = []
        for fd in doc["fillers"]:
            F = Filler()
            F.id, F.doc = fd["id"], fd
            F.lhs, F.ast = parse_eq(fd["eq"])
            F.f = to_sp(F.ast)
            F.syms = F.f.free_symbols | {self.y}
            F.new_bodies = fd["new_bodies"]
            F.new = []
            for nq in fd["new"]:
                kind = nq["kind"]
                n = 1 if kind == "?" else reg.size(kind)
                comps = [nq["id"]] if n == 1 else list(nq["components"])
                F.new.append(Rec(id=nq["id"], meaning=nq["meaning"], owner=nq["owner"], kind=kind, n=n, comps=comps,
                                 dims=nq["dims"], value=nq["value"], new=True, under=nq["under"],
                                 old_value=nq["old_value"], route=nq["route"]))
            F.new_names = {c for r in F.new for c in r.comps}
            self.fillers.append(F)
        types = {}
        for b in self.bodies:
            types.setdefault(b["type"], []).append(b["id"])
        self.pairs = [("exch", g[i], g[j]) for g in types.values() for i in range(len(g)) for j in range(i + 1, len(g))]
        self.catalog = ["rev_t", "refl_x", "conj_c", "rot_z"] + self.pairs
        self.world_names = {c for r in self.recs for c in r.comps}
        self.var_names = {c for r in self.recs if r.value == "var" for c in r.comps}

    def all_recs(self, F):
        return self.recs + (F.new if F is not None else [])

    def state_subs(self, state):
        subs = {}
        for r in self.recs:
            if r.value == "var":
                for c in r.comps:
                    if c in state:
                        subs[sp.Symbol(c)] = rat(state[c])
            else:
                vals = r.value if isinstance(r.value, list) else [r.value]
                for c, v in zip(r.comps, vals):
                    subs[sp.Symbol(c)] = rat(v)
        return subs


# ----------------------------------------------------------------- actions (Section 2.2)

def rec_action(W, r, T, mode, choice=None, dims_of=None):
    """Action of transformation T on quantity r. mode: proc | fix | dims | fork | choice (DERIVE)."""
    reg = W.reg
    if T == "rot_z":
        if r.new and mode == "fix":
            return sp.Integer(1)
        if r.kind == "?":
            name = f"{r.id}:rot_z"
            if mode == "choice":
                return sp.Integer(choice.get(name, 1))
            return sp.Symbol(name)
        v = reg.kinds[r.kind]["under"]["rot_z"]
        return sp.Symbol(f"{r.id}:rot_z") if v == "?" else parse_action(v)
    if mode == "dims":
        e = dims_of(r).get(DIM_OF_T[T], 0)
        e = int(e) if Fr(e).denominator == 1 else 0
        return sp.Integer(-1) if e % 2 else sp.Integer(1)
    if r.new:
        if mode == "fix":
            return sp.Integer(1)
        if mode == "fork":
            if r.n == 1:
                return sp.Symbol(f"{r.id}:{T}")
            return sp.diag(*[sp.Symbol(f"{r.id}[{i}]:{T}") for i in range(r.n)])
        if mode == "choice":
            return choice[f"{r.id}:{T}"]
        v = r.under[T]
        if isinstance(v, dict):
            return reg.meaning_action(r.meaning, T)
    else:
        v = reg.meanings[r.meaning]["under"][T]
        if isinstance(v, dict):
            return reg.meaning_action(r.meaning, T)
    if v == "?":
        name = f"{r.id}:{T}"
        if mode == "fix":
            return sp.Integer(1)
        if mode == "choice":
            return sp.Integer(choice.get(name, 1))
        return sp.Symbol(name)
    return parse_action(v)


def image(r, a):
    syms = r.syms
    if is_matrix(a):
        v = a * sp.Matrix(syms)
        return {s: v[i] for i, s in enumerate(syms)}
    return {s: a * s for s in syms}


def exch_subs(recs, b1, b2, mode):
    subs = {}
    pool = [r for r in recs if not (mode == "fix" and r.new)]
    for r in pool:
        if r.owner not in (b1, b2):
            continue
        other = b2 if r.owner == b1 else b1
        partners = [p for p in pool if p.owner == other and p.meaning == r.meaning]
        if len(partners) != 1:
            if mode == "fix":
                continue
            raise ValueError(f"V7: quantity {r.id} of {r.owner} has {len(partners)} partners on {other}")
        for c, pc in zip(r.comps, partners[0].comps):
            subs[sp.Symbol(c)] = sp.Symbol(pc)
    return subs


def subs_for(W, F, T, mode="proc", choice=None, dims_of=None):
    recs = W.all_recs(F)
    if isinstance(T, tuple):
        return exch_subs(recs, T[1], T[2], mode)
    out = {}
    for r in recs:
        out.update(image(r, rec_action(W, r, T, mode, choice, dims_of)))
    return out


# ----------------------------------------------------------------- invariance (Section 2.3)

def eq_diff(y, f, subs):
    iy = subs.get(y, y)
    return (iy - f.xreplace(subs)).xreplace({y: f})


def unchanged(y, f, subs):
    return is_zero(eq_diff(y, f, subs))


def f2_transform(W, F, T, mode="proc", dims_of=None):
    subs = subs_for(W, F, T, mode, dims_of=dims_of)
    names = W.law_syms | F.syms
    U = sorted({s for n in names for s in subs.get(n, n).free_symbols if is_sign(s)}, key=lambda s: s.name)
    rows = []
    for vals in itertools.product((1, -1), repeat=len(U)):
        a = {u: sp.Integer(v) for u, v in zip(U, vals)}
        s = {k: v.xreplace(a) for k, v in subs.items()} if a else subs
        old = unchanged(W.y, W.f, s)
        new = unchanged(W.y, F.f, s)
        rows.append((tuple(vals), old, new))
    ch = {vals: (o != n) for vals, o, n in rows}
    if not any(ch.values()):
        status = "no_change"
    elif all(ch.values()):
        status = "changed"
    else:
        status = "conditional"
    keeping = [dict(zip([u.name for u in U], v)) for v, c in ch.items() if not c]
    matters = []
    for i, u in enumerate(U):
        for vals in ch:
            flipped = tuple(-v if j == i else v for j, v in enumerate(vals))
            if ch[vals] != ch[flipped]:
                matters.append(u.name)
                break
    return {"status": status, "unknowns": [u.name for u in U], "rows": rows, "keeping": keeping,
            "matters": matters}


def diag_options(n):
    return [sp.diag(*signs) for signs in itertools.product((1, -1), repeat=n)]


def f2_derive(W, F, T):
    """DERIVE: whatever can be chosen is chosen to keep the card (Section 7)."""
    if isinstance(T, tuple):
        return f2_transform(W, F, T)["status"]
    names = W.law_syms | F.syms
    free = []
    if T in MEANING_T:
        for r in F.new:
            free.append((f"{r.id}:{T}", [sp.Integer(1), sp.Integer(-1)] if r.n == 1 else diag_options(r.n)))
        for r in W.recs:
            if W.reg.meanings[r.meaning]["under"][T] == "?" and any(sp.Symbol(c) in names for c in r.comps):
                free.append((f"{r.id}:{T}", [1, -1]))
    else:
        for r in F.new:
            if r.kind == "?":
                free.append((f"{r.id}:rot_z", [1, -1]))
    keys = [k for k, _ in free]
    for combo in itertools.product(*[o for _, o in free]):
        choice = dict(zip(keys, combo))
        s = subs_for(W, F, T, "choice", choice=choice)
        if unchanged(W.y, W.f, s) == unchanged(W.y, F.f, s):
            return "no_change"
    return "changed"


# ----------------------------------------------------------------- F1 (Section 2.5)

def f1(W, F):
    reg = W.reg
    unknown, dimsym = {}, {}
    bad_written = []
    for r in F.new:
        md = reg.meaning_dims(r.meaning) if r.meaning != "?" else None
        if r.dims != "?":
            vec = {D: sp.Integer(r.dims.get(D, 0)) for D in BASE}
            if md is not None and norm_dims(md) != norm_dims(r.dims):
                bad_written.append(r.id)
        elif md is not None:
            vec = {D: sp.Rational(str(md.get(D, 0))) for D in BASE}
        else:
            vec = {D: sp.Symbol(f"&{r.id}&{D}") for D in BASE}
            unknown[r.id] = vec
        for c in r.comps:
            dimsym[c] = vec
    for r in W.recs:
        vec = {D: sp.Integer(r.dims.get(D, 0)) for D in BASE}
        for c in r.comps:
            dimsym[c] = vec
    eqs = []

    def walk(node):
        t = node[0]
        if t == "num":
            return {D: sp.Integer(0) for D in BASE}
        if t == "name":
            return dimsym[node[1]]
        if t == "neg":
            return walk(node[1])
        if t == "pow":
            a = walk(node[1])
            return {D: a[D] * node[2] for D in BASE}
        a, b = walk(node[2]), walk(node[3])
        if node[1] == "*":
            return {D: a[D] + b[D] for D in BASE}
        if node[1] == "/":
            return {D: a[D] - b[D] for D in BASE}
        eqs.extend(sp.expand(a[D] - b[D]) for D in BASE)
        return a

    rhs = walk(F.ast)
    lhs = dimsym[F.lhs[1]]
    eqs.extend(sp.expand(lhs[D] - rhs[D]) for D in BASE)
    eqs = [e for e in eqs if e != 0]
    syms = [s for v in unknown.values() for s in v.values()]
    inferred = {}
    if not syms:
        solvable = not eqs
        sol = {}
    elif not eqs:
        solvable, sol = True, {s: s for s in syms}
    else:
        res = sp.linsolve(eqs, syms)
        if res == sp.S.EmptySet or len(res) == 0:
            solvable, sol = False, {}
        else:
            (tup,) = list(res)
            solvable, sol = True, dict(zip(syms, tup))
    consistent = solvable and not bad_written
    if solvable:
        for qid, vec in unknown.items():
            vals = [sol.get(vec[D], vec[D]) for D in BASE]
            if any(v.free_symbols for v in vals):
                inferred[qid] = "undetermined"
            else:
                inferred[qid] = norm_dims({D: tofr(v) for D, v in zip(BASE, vals)})
    return {"consistent": consistent, "inferred": inferred, "bad_written": bad_written}


def dims_of_factory(W, F, f1res):
    reg = W.reg

    def dims_of(r):
        if not r.new:
            return norm_dims(r.dims)
        if r.dims != "?":
            return norm_dims(r.dims)
        md = reg.meaning_dims(r.meaning) if r.meaning != "?" else None
        if md is not None:
            return md
        inf = f1res["inferred"].get(r.id, "undetermined")
        return inf if isinstance(inf, dict) else {}
    return dims_of


def law_dims_consistent(W):
    """V6: the law alone, with the world's dims."""
    G = Filler()
    G.lhs, G.ast, G.new = W.law_lhs, W.law_ast, []
    return f1(W, G)["consistent"]


# ----------------------------------------------------------------- F3 (Section 2.6), exact Fourier-Motzkin

def fm_simplify(cons):
    best = {}
    for a, b in cons:
        a = {k: v for k, v in a.items() if v != 0}
        if not a:
            if b < 0:
                return None
            continue
        keys = sorted(a)
        s = abs(a[keys[0]])
        key = tuple((k, a[k] / s) for k in keys)
        bb = b / s
        if key not in best or bb < best[key]:
            best[key] = bb
    return [(dict(k), b) for k, b in best.items()]


def fm_eliminate(cons, v):
    pos, neg, rest = [], [], []
    for a, b in cons:
        c = a.get(v, 0)
        if c > 0:
            pos.append((a, b, c))
        elif c < 0:
            neg.append((a, b, c))
        else:
            rest.append((a, b))
    for ap, bp, cp in pos:
        for an, bn, cn in neg:
            new = {}
            for k in set(ap) | set(an):
                if k == v:
                    continue
                val = ap.get(k, 0) / cp + an.get(k, 0) / (-cn)
                if val != 0:
                    new[k] = val
            rest.append((new, bp / cp + bn / (-cn)))
    return fm_simplify(rest)


def fm_reduce(cons, vars_):
    cons = fm_simplify(cons)
    if cons is None:
        return None
    left = list(vars_)
    while left:
        def cost(v):
            p = sum(1 for a, _ in cons if a.get(v, 0) > 0)
            n = sum(1 for a, _ in cons if a.get(v, 0) < 0)
            return p * n - p - n
        v = min(left, key=cost)
        left.remove(v)
        cons = fm_eliminate(cons, v)
        if cons is None:
            return None
    return cons


def fm_feasible(cons, vars_):
    return fm_reduce(cons, vars_) is not None


def fm_range(cons, vars_, obj, const):
    """Exact [lo, hi] of const + sum obj[v]*v over the feasible set (None = unbounded); 'infeasible' if empty."""
    z = "\x00z"
    extra = [({z: Fr(1), **{v: -c for v, c in obj.items()}}, const),
             ({z: Fr(-1), **{v: c for v, c in obj.items()}}, -const)]
    red = fm_reduce(cons + extra, [v for v in vars_ if v != z])
    if red is None:
        return "infeasible"
    lo, hi = None, None
    for a, b in red:
        c = a.get(z, 0)
        if set(a) - {z}:
            raise ValueError("elimination left a variable")
        if c > 0:
            hi = b / c if hi is None else min(hi, b / c)
        elif c < 0:
            lo = b / c if lo is None else max(lo, b / c)
    return lo, hi


def f3_constraints(W, F, which=("old", "new")):
    cons, unknowns = [], set()
    for kind in which:
        lst = W.old if kind == "old" else W.new
        for k, ob in enumerate(lst):
            subs = W.state_subs(ob["state"])
            for r in F.new:
                if kind == "old":
                    ov = r.old_value
                    if ov == "same":
                        vals = [sp.Symbol(f"${c}") for c in r.comps]
                    else:
                        vals = [rat(x) for x in (ov if isinstance(ov, list) else [ov])]
                elif r.value == "?":
                    vals = [sp.Symbol(f"${c}") for c in r.comps]
                else:
                    vals = [sp.Symbol(f"${c}@{k}") for c in r.comps]
                for c, v in zip(r.comps, vals):
                    subs[sp.Symbol(c)] = v
            e = sp.expand(sp.together(F.f.xreplace(subs)))
            e = sp.expand(e)
            X = sorted(e.free_symbols, key=lambda s: s.name)
            if any(not x.name.startswith("$") for x in X):
                raise ValueError(f"observation {ob['id']}: names left without a value: {X}")
            K = tofr(e.xreplace({x: 0 for x in X}))
            a = {}
            for x in X:
                c = sp.diff(e, x)
                if c.free_symbols:
                    raise ValueError(f"filler {F.id} is not affine in {x}")
                a[x.name] = tofr(c)
                unknowns.add(x.name)
            v, d = Fr(ob["value"]), Fr(W.observers[ob["observer"]]["precision"])
            cons.append((dict(a), v + d - K))
            cons.append(({x: -c for x, c in a.items()}, -(v - d - K)))
    return cons, sorted(unknowns)


def f3(W, F):
    cons, X = f3_constraints(W, F)
    return fm_feasible(cons, X)


def predicted_interval(W, F, state):
    cons, X = f3_constraints(W, F)
    subs = W.state_subs(state)
    for r in F.new:
        for c in r.comps:
            subs[sp.Symbol(c)] = sp.Symbol(f"${c}")
    e = sp.expand(sp.together(F.f.xreplace(subs)))
    Y = sorted(e.free_symbols, key=lambda s: s.name)
    if any(not y.name.startswith("$") for y in Y):
        raise ValueError(f"decisive state misses names: {Y}")
    const = tofr(e.xreplace({y: 0 for y in Y}))
    obj = {y.name: tofr(sp.diff(e, y)) for y in Y}
    return fm_range(cons, sorted(set(X) | set(obj)), obj, const)


# ----------------------------------------------------------------- the card and the verdict (Sections 2.4-2.7)

def verdict_of(f1ok, statuses, f3ok):
    if not f1ok:
        return INVALID, [{"item": "F1"}]
    reason = []
    if not f3ok:
        reason.append({"item": "F3"})
    reason += [{"item": "F2", "transformation": t} for t, s in statuses.items() if s == "changed"]
    if reason:
        return ANOTHER, reason
    reason = [{"item": "F2", "transformation": t} for t, s in statuses.items() if s == "conditional"]
    if reason:
        return COND, reason
    return SAME, []


def reason_ts(reason):
    return [r["transformation"] for r in reason if r["item"] == "F2"]


def analyze_filler(W, F):
    out = {"id": F.id}
    out["F1"] = f1(W, F)
    dims_of = dims_of_factory(W, F, out["F1"])
    out["F2"] = {tlabel(T): f2_transform(W, F, T) for T in W.catalog}
    out["F3"] = f3(W, F)
    st = {k: v["status"] for k, v in out["F2"].items()}
    out["verdict"], out["reason"] = verdict_of(out["F1"]["consistent"], st, out["F3"])
    base = {}
    for name, mode in (("FIX", "fix"), ("DIMS", "dims"), ("FORK_ALL", "fork")):
        s = {tlabel(T): f2_transform(W, F, T, mode, dims_of)["status"] for T in W.catalog}
        v, rs = verdict_of(out["F1"]["consistent"], s, out["F3"])
        base[name] = {"verdict": v, "reason": rs, "F2": s}
    s = {tlabel(T): f2_derive(W, F, T) for T in W.catalog}
    v, rs = verdict_of(out["F1"]["consistent"], s, out["F3"])
    base["DERIVE"] = {"verdict": v, "reason": rs, "F2": s}
    out["baselines"] = base
    return out


# ----------------------------------------------------------------- V13: the group the catalog generates

def group_check(W, F, cat):
    gens = [(T, 4 if T == "rot_z" else 2) for T in W.catalog]
    subs_g = {tlabel(T): subs_for(W, F, T) for T in W.catalog}
    names_all = [s for r in W.all_recs(F) for s in r.syms]
    rel = W.law_syms | F.syms
    U = sorted({s for sg in subs_g.values() for n in rel for s in sg.get(n, n).free_symbols if is_sign(s)},
               key=lambda s: s.name)
    k_cat, k_grp, extra = set(), set(), []
    for vals in itertools.product((1, -1), repeat=len(U)):
        a = {u: sp.Integer(v) for u, v in zip(U, vals)}
        num = {k: {n: e.xreplace(a) for n, e in sg.items()} for k, sg in subs_g.items()}
        cat_changed, grp_changed = False, False
        for exps in itertools.product(*[range(o) for _, o in gens]):
            if not any(exps):
                continue
            comp = {}
            for n in names_all:
                e = n
                for (T, _), k in zip(gens, exps):
                    for _ in range(k):
                        e = e.xreplace(num[tlabel(T)])
                comp[n] = e
            ch = unchanged(W.y, W.f, comp) != unchanged(W.y, F.f, comp)
            single = sum(exps) == 1
            if ch:
                grp_changed = True
                if single:
                    cat_changed = True
                else:
                    extra.append((vals, exps))
        if not cat_changed:
            k_cat.add(vals)
        if not grp_changed:
            k_grp.add(vals)
    words = []
    for vals, exps in extra:
        w = "*".join(f"{tlabel(T)}^{k}" if k > 1 else tlabel(T) for (T, _), k in zip(gens, exps) if k)
        words.append((dict(zip([u.name for u in U], vals)), w))
    return {"unknowns": [u.name for u in U], "k_cat": k_cat, "k_grp": k_grp, "products_changed": words}


def law_changed_by_catalog(W):
    G = Filler()
    G.f, G.syms, G.new = W.f, W.law_syms, []
    out = {}
    for T in W.catalog:
        subs = subs_for(W, None, T)
        U = sorted({s for n in W.law_syms for s in subs.get(n, n).free_symbols if is_sign(s)}, key=lambda s: s.name)
        res = []
        for vals in itertools.product((1, -1), repeat=len(U)):
            a = {u: sp.Integer(v) for u, v in zip(U, vals)}
            s = {k: v.xreplace(a) for k, v in subs.items()}
            res.append(unchanged(W.y, W.f, s))
        out[tlabel(T)] = res
    return out


# ----------------------------------------------------------------- validity (Section 3)

def all_numbers(obj, path=""):
    """Yield (path, fraction string) for every number field of a world."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("value", "precision", "old_value", "under", "state"):
                yield from _nums(v, f"{path}.{k}")
            elif isinstance(v, (dict, list)):
                yield from all_numbers(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from all_numbers(v, f"{path}[{i}]")


def _nums(v, path):
    if isinstance(v, str):
        if v not in ("var", "?", "same"):
            yield path, v
    elif isinstance(v, list):
        for i, e in enumerate(v):
            yield from _nums(e, f"{path}[{i}]")
    elif isinstance(v, dict):
        for k, e in v.items():
            if k != "derived":
                yield from _nums(e, f"{path}.{k}")


def world_ids(doc):
    ids = []
    for key in ("bodies", "quantities", "laws", "observers", "observations", "fillers"):
        for st in doc[key]:
            ids.append(st["id"])
    for q in doc["quantities"]:
        ids += q["components"]
    for f in doc["fillers"]:
        ids += [b["id"] for b in f["new_bodies"]]
        for nq in f["new"]:
            ids.append(nq["id"])
            if isinstance(nq["components"], list):
                ids += nq["components"]
    return ids


def check_validity(reg, W, cards):
    """Returns a list of problems (V2-V10, budgets, names, numbers)."""
    P = []
    doc = W.doc
    # budgets
    if not 0 <= len(doc["bodies"]) <= 4:
        P.append("budget: bodies")
    types = {}
    for b in doc["bodies"]:
        types[b["type"]] = types.get(b["type"], 0) + 1
    if any(c > 2 for c in types.values()):
        P.append("budget: more than 2 bodies of one type")
    if not 2 <= len(doc["quantities"]) <= 9:
        P.append("budget: world quantities")
    if len(doc["laws"]) != 1:
        P.append("budget: exactly one law")
    if doc["relations"] != []:
        P.append("budget: relations must be []")
    if not 1 <= len(doc["observers"]) <= 3:
        P.append("budget: observers")
    if not 1 <= len(W.old) <= 6:
        P.append(f"budget: old observations {len(W.old)}")
    if not 1 <= len(W.new) <= 4:
        P.append(f"budget: new observations {len(W.new)}")
    if not 1 <= len(doc["fillers"]) <= 3:
        P.append("budget: fillers")
    for F in W.fillers:
        if not 0 <= len(F.new) <= 3:
            P.append(f"budget: new quantities of {F.id}")
        if not 0 <= len(F.new_bodies) <= 2:
            P.append(f"budget: new bodies of {F.id}")
    # names
    ids = world_ids(doc)
    for n in ids:
        if not NAME_OK.match(n):
            P.append(f"name rule: {n!r}")
        if n in reg.ids:
            P.append(f"name {n!r} is a registry id")
    dup = {n for n in ids if ids.count(n) > 1}
    if dup:
        P.append(f"names not distinct: {sorted(dup)}")
    # numbers
    for path, s in all_numbers(doc):
        fr = Fr(s)
        if abs(fr.numerator) > LIMIT or fr.denominator > LIMIT:
            P.append(f"number too large at {path}: {s}")
    # expressions: powers, D, integer literals
    for label, ast in [("law", W.law_ast)] + [(F.id, F.ast) for F in W.fillers]:
        for node in ast_walk(ast):
            if node[0] == "pow" and not -3 <= node[2] <= 3:
                P.append(f"{label}: power {node[2]} outside -3..3")
            if node[0] == "D":
                P.append(f"{label}: D() is not allowed")
            if node[0] == "num" and node[1] > LIMIT:
                P.append(f"{label}: number {node[1]} too large")
    # V2
    if W.law_lhs[0] != "name" or W.y is None:
        P.append("V2: the law's left side is not a single name")
        return P
    yname = W.y.name
    if yname not in W.world_names:
        P.append("V2: y is not a world quantity or component")
    if W.y in W.f.free_symbols:
        P.append("V2: y on the right side of the law")
    if "accepted_at" not in W.law:
        P.append("V2: law without accepted_at")
    for F in W.fillers:
        if F.doc["of"] != W.law["id"]:
            P.append(f"V2: {F.id} is not of the law")
        if F.lhs != ("name", yname):
            P.append(f"V2: {F.id} has another left side")
        if W.y in F.f.free_symbols:
            P.append(f"V2: y on the right side of {F.id}")
    # V3
    for F in W.fillers:
        for r in F.new:
            if r.owner == "?":
                P.append(f"V3: {F.id}.{r.id} has an unknown owner")
            if r.old_value == "?":
                P.append(f"V3: {F.id}.{r.id} has old_value '?'")
    # V4
    for F in W.fillers:
        names = W.law_syms | F.syms
        signs = set()
        for T in W.catalog:
            if isinstance(T, tuple):
                continue
            subs = subs_for(W, F, T)
            for n in names:
                signs |= {s.name for s in subs.get(n, n).free_symbols if is_sign(s)}
        for r in F.new:
            if r.n > 1 and any(v == "?" for v in r.under.values()):
                P.append(f"V4: unknown action on the multi-component {F.id}.{r.id}")
        if len(signs) > 2:
            P.append(f"V4: {F.id} has {len(signs)} unknown signs: {sorted(signs)}")
    # V5
    for F in W.fillers:
        newsyms = [sp.Symbol(c) for c in F.new_names]
        for node in ast_walk(F.ast):
            if node[0] == "pow" and node[1][0] == "name" and node[1][1] in F.new_names and node[2] != 1:
                P.append(f"V5: {F.id} has a power of a new quantity")
        num, den = sp.fraction(sp.together(F.f))
        if any(s in den.free_symbols for s in newsyms):
            P.append(f"V5: {F.id} has a new quantity in a denominator")
        ex = sp.expand(num)
        if newsyms:
            poly = sp.Poly(ex, *newsyms)
            if poly.total_degree() > 1:
                P.append(f"V5: {F.id} is not affine in its new quantities")
        for r in F.new:
            if not any(sp.Symbol(c) in ex.free_symbols for c in r.comps):
                P.append(f"V5: {F.id}.{r.id} disappears after expansion")
    # V6
    for r in W.recs:
        if r.value == "?":
            P.append(f"V6: {r.id} has value '?'")
        md = reg.meaning_dims(r.meaning)
        if md is not None and norm_dims(md) != norm_dims(r.dims):
            P.append(f"V6: dims of {r.id} differ from its meaning's")
    if not law_dims_consistent(W):
        P.append("V6: the law is not dimensionally consistent")
    # V7
    body_type = {b["id"]: b["type"] for b in doc["bodies"]}
    for F in [None] + W.fillers:
        recs = W.all_recs(F)
        for b in body_type:
            ms = [r.meaning for r in recs if r.owner == b]
            if len(ms) != len(set(ms)):
                P.append(f"V7: body {b} owns two quantities of one meaning ({F.id if F else 'world'})")
    for _, b1, b2 in W.pairs:
        m1 = sorted(r.meaning for r in W.recs if r.owner == b1)
        m2 = sorted(r.meaning for r in W.recs if r.owner == b2)
        if m1 != m2:
            P.append(f"V7: same-type bodies {b1}, {b2} own different meanings")
    for F in W.fillers:
        for r in F.new:
            for _, b1, b2 in W.pairs:
                if r.owner in (b1, b2):
                    other = b2 if r.owner == b1 else b1
                    if r.meaning == "?":
                        P.append(f"V7: {F.id}.{r.id} on a same-type body has an unknown meaning")
                    elif not any(p.owner == other and p.meaning == r.meaning for p in W.all_recs(F)):
                        P.append(f"V7: {F.id}.{r.id} has no partner on {other}")
        for nb in F.new_bodies:
            if nb["type"] in body_type.values():
                P.append(f"V7: new body {nb['id']} has a type that a world body has")
    # V8
    law_vars = {s.name for s in W.f.free_symbols} & W.var_names
    fill_vars = set()
    for F in W.fillers:
        fill_vars |= {s.name for s in F.f.free_symbols} & W.var_names
    need = (law_vars | fill_vars) - {yname}
    consts = W.world_names - W.var_names
    for ob in doc["observations"]:
        if ob["of"] != yname:
            P.append(f"V8: {ob['id']} is not of y")
        st = set(ob["state"])
        if need - st:
            P.append(f"V8: {ob['id']} misses {sorted(need - st)}")
        if st & consts:
            P.append(f"V8: {ob['id']} fixes constants {sorted(st & consts)}")
        if st - need - consts:
            P.append(f"V8 (note): {ob['id']} fixes names outside the laws: {sorted(st - need)}")
        subs = W.state_subs(ob["state"])
        for label, f in [("law", W.f)] + [(F.id, F.f) for F in W.fillers]:
            _n, den = sp.fraction(sp.together(f))
            dv = den.xreplace(subs)
            if dv.is_Rational and dv == 0:
                P.append(f"V8: division by zero in {label} at {ob['id']}")
    for ob in W.old:
        pred = tofr(W.f.xreplace(W.state_subs(ob["state"])))
        d = Fr(W.observers[ob["observer"]]["precision"])
        if abs(Fr(ob["value"]) - pred) > d:
            P.append(f"V8: the law misses old observation {ob['id']}")
    dev = []
    for ob in W.new:
        pred = tofr(W.f.xreplace(W.state_subs(ob["state"])))
        d = Fr(W.observers[ob["observer"]]["precision"])
        dev.append(abs(Fr(ob["value"]) - pred) > d)
    if not any(dev):
        P.append("V8: no real deficit")
    for F in W.fillers:
        cons, X = f3_constraints(W, F, which=("new",))
        if not fm_feasible(cons, X):
            P.append(f"V8: {F.id} alone does not fit the new observations")
    # V9
    for F in W.fillers:
        c = cards[F.id]
        if c["verdict"] == INVALID:
            continue
        for qid, d in c["F1"]["inferred"].items():
            if d == "undetermined":
                P.append(f"V9: dims of {F.id}.{qid} undetermined")
            elif any(Fr(v).denominator != 1 for v in d.values()):
                P.append(f"V9: dims of {F.id}.{qid} not integers")
    # V10
    if len(W.fillers) > 1:
        kept = [F for F in W.fillers if cards[F.id]["verdict"] == SAME]
        if any(cards[F.id]["verdict"] == COND for F in W.fillers):
            P.append("V10: a CONDITIONAL filler in a several-filler world")
        if len(kept) < 2:
            P.append("V10: fewer than 2 SAME_LAW_NEW_STATE fillers")
        for F in kept:
            if any(r.value != "?" for r in F.new):
                P.append(f"V10: kept filler {F.id} has a variable new quantity")
            cons, X = f3_constraints(W, F)
            for x in X:
                rng = fm_range(cons, X, {x: Fr(1)}, Fr(0))
                if rng == "infeasible" or rng[0] is None or rng[1] is None:
                    P.append(f"V10: feasible set of {F.id} unbounded in {x}")
    return P


# ----------------------------------------------------------------- traps (Section 6)

def has_meaning(F, m):
    return any(r.meaning == m for r in F.new)


AXIAL_MEANINGS = ("m18", "m19", "m20")


def matrix_quantities(W, F, T, where):
    """Quantities appearing in the law ('law'), the filled law ('filled') that T acts on by a non-scalar matrix."""
    if isinstance(T, tuple):
        return []
    names = {s.name for s in (W.f.free_symbols if where == "law" else F.f.free_symbols)} | {W.y.name}
    out = []
    for r in W.all_recs(F):
        if not set(r.comps) & names:
            continue
        a = rec_action(W, r, T, "proc")
        if is_matrix(a) and not (a.is_diagonal() and len(set(a[i, i] for i in range(a.rows))) == 1):
            out.append(r)
    return out


def trap_flags(W, F, card, gcheck):
    flags = {}
    v = card["verdict"]
    B = card["baselines"]
    rts = reason_ts(card["reason"])
    if v == SAME and has_meaning(F, "m04") and B["FIX"]["verdict"] == ANOTHER and "conj_c" in reason_ts(B["FIX"]["reason"]):
        flags["T1"] = True
    if v == ANOTHER and any(t in MEANING_T for t in rts) and B["DERIVE"]["verdict"] == SAME and B["DIMS"]["verdict"] == SAME:
        flags["T2"] = "m06/rev_t" if (has_meaning(F, "m06") and "rev_t" in rts) else True
    if v == SAME and has_meaning(F, "m18") and B["FIX"]["verdict"] == ANOTHER and "rev_t" in reason_ts(B["FIX"]["reason"]):
        flags["T3"] = True
    if v == SAME and has_meaning(F, "m22") and B["FIX"]["verdict"] == ANOTHER and "refl_x" in reason_ts(B["FIX"]["reason"]):
        flags["T4"] = True
    for t, res in card["F2"].items():
        if res["status"] == "changed" and all((not o) and n for _, o, n in res["rows"]):
            flags["T5"] = t
    changed = [t for t, res in card["F2"].items() if res["status"] == "changed"]
    if changed and all(t.startswith("exch(") for t in changed) and card["F1"]["consistent"] and card["F3"]:
        flags["T6"] = changed
    if v == COND:
        src_m, src_u = set(), set()
        recs = {r.id: r for r in W.all_recs(F)}
        for t in rts:
            res = card["F2"][t]
            for which, names in (("matters", res["matters"]), ("unknowns", res["unknowns"])):
                for u in names:
                    qid = u.split(":")[0]
                    r = recs[qid]
                    reg_card = (not r.new) or (r.meaning != "?")
                    tag = "registry" if reg_card else "new?"
                    (src_m if which == "matters" else src_u).add(tag)
        flags["T7"] = {"matters": sorted(src_m), "unknowns": sorted(src_u)}
    t8 = []
    for t in rts:
        T = t if not t.startswith("exch(") else None
        if T is None:
            continue
        for where in ("law", "filled"):
            for r in matrix_quantities(W, F, T, where):
                tag = "generic"
                if r.meaning == "m23" and T == "rev_t":
                    tag = "m23/rev_t"
                elif r.meaning in AXIAL_MEANINGS and T == "refl_x":
                    tag = "axial/refl_x"
                t8.append((where, t, r.id, tag))
    if t8:
        flags["T8"] = t8
    if len(W.fillers) > 1:
        flags["T9"] = True
    return flags


# ----------------------------------------------------------------- decisive states (Sections 2.8, 5)

def check_decisive(W, kept, entries):
    P = []
    seen = set()
    yname = W.y.name
    for ent in entries or []:
        a, b = ent["pair"]
        seen.add(frozenset((a, b)))
        Fa = next(F for F in W.fillers if F.id == a)
        Fb = next(F for F in W.fillers if F.id == b)
        need = set()
        for F in (Fa, Fb):
            need |= {s.name for s in F.f.free_symbols} & W.var_names
        need -= {yname}
        if set(ent["state"]) != need:
            P.append(f"decisive {a},{b}: state names {sorted(ent['state'])} != {sorted(need)}")
            continue
        obs = W.observers.get(ent["observer"])
        if obs is None:
            P.append(f"decisive {a},{b}: unknown observer")
            continue
        d = Fr(obs["precision"])
        ia = predicted_interval(W, Fa, ent["state"])
        ib = predicted_interval(W, Fb, ent["state"])
        if "infeasible" in (ia, ib) or None in ia or None in ib:
            P.append(f"decisive {a},{b}: unbounded interval {ia} {ib}")
            continue
        gap = max(ib[0] - ia[1], ia[0] - ib[1])
        if not gap > 2 * d:
            P.append(f"decisive {a},{b}: gap {gap} not above 2*{d}")
    for i in range(len(kept)):
        for j in range(i + 1, len(kept)):
            if frozenset((kept[i], kept[j])) not in seen:
                P.append(f"decisive: no state for the pair {kept[i]}, {kept[j]}")
    return P


# ----------------------------------------------------------------- main

def analyze_world(reg, doc, path, with_group=True):
    W = World(reg, doc, path)
    cards = {F.id: analyze_filler(W, F) for F in W.fillers}
    groups = {}
    if with_group:
        for F in W.fillers:
            groups[F.id] = group_check(W, F, cards[F.id])
    return W, cards, groups


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    wdir, key_path = argv[1], argv[2]
    reg = Registry()
    out = []
    problems = []
    pr = out.append
    pr(f"registry canonical sha256 {reg.sha}")
    files = sorted(glob.glob(os.path.join(wdir, "W-*.json")))
    if len(files) != 30:
        problems.append(f"expected 30 world files, found {len(files)}")
    key = json.load(open(key_path, encoding="utf-8"))
    key_by = {e["id"]: e for e in key}
    summary = {}
    for path in files:
        wid = os.path.basename(path)[:-5]
        doc = json.load(open(path, encoding="utf-8"))
        ctx, canon = R.check_world(doc, reg.info, path)
        wp = []
        if ctx.errors:
            wp += ["V1: " + e for e in ctx.errors]
            problems += [f"{wid}: {p}" for p in wp]
            pr(f"\n=== {wid}: rejected by the reader")
            continue
        if doc["id"] != "w" + wid[2:]:
            wp.append("id inside differs from the file name")
        if doc["registry"] != "test4_registry" or doc["registry_sha256"] != reg.sha:
            wp.append("registry id or sha256")
        W, cards, groups = analyze_world(reg, doc, path)
        wp += check_validity(reg, W, cards)
        lawch = law_changed_by_catalog(W)
        pr(f"\n=== {wid} ({doc['id']})  law: {W.law['eq']}   law unchanged by catalog: "
           + ", ".join(f"{t}={'/'.join('u' if x else 'C' for x in v)}" for t, v in lawch.items()))
        flags_w = {}
        for F in W.fillers:
            c, g = cards[F.id], groups[F.id]
            pr(f"  {F.id}: {F.doc['eq']}")
            pr(f"    verdict {c['verdict']}  reason {[r.get('transformation', r['item']) for r in c['reason']]}")
            inf = {k: dims_str(v) for k, v in c['F1']['inferred'].items()}
            pr(f"    F1 consistent={c['F1']['consistent']} inferred={inf} bad_written={c['F1']['bad_written']}")
            for t, res in c["F2"].items():
                extra = ""
                if res["status"] == "conditional":
                    extra = f" keeping={res['keeping']} matters={res['matters']}"
                rows = " ".join(f"{dict(zip(res['unknowns'], v)) if res['unknowns'] else ''}"
                                f"[old={'u' if o else 'C'},new={'u' if n else 'C'}]" for v, o, n in res["rows"])
                pr(f"    F2 {t}: {res['status']} unknowns={res['unknowns']} {rows}{extra}")
            pr(f"    F3 holds={c['F3']}")
            pr("    baselines: " + ", ".join(f"{b}={c['baselines'][b]['verdict']}" for b in ("FIX", "DERIVE", "DIMS", "FORK_ALL")))
            # V13
            v = c["verdict"]
            if v == SAME and len(g["k_grp"]) != 2 ** len(g["unknowns"]):
                wp.append(f"V13: {F.id} SAME changes under products {g['products_changed'][:4]}")
            if v == COND and g["k_cat"] != g["k_grp"]:
                wp.append(f"V13: {F.id} CONDITIONAL keeping set changes under products {g['products_changed'][:4]}")
            f3alone = (v == ANOTHER and c["F1"]["consistent"] and not c["F3"]
                       and all(res["status"] == "no_change" for res in c["F2"].values()))
            if f3alone and g["products_changed"]:
                wp.append(f"V13: {F.id} decided by F3 alone but a product changes it")
            c["f3alone"] = f3alone and not g["products_changed"]
            if g["products_changed"]:
                pr(f"    products changing it: {g['products_changed'][:6]}")
            fl = trap_flags(W, F, c, g)
            c["traps"] = fl
            for t in fl:
                flags_w.setdefault(t, []).append(F.id)
            pr(f"    traps: {fl}")
        # key
        ke = key_by.get(wid)
        if ke is None:
            wp.append("V12: no key entry")
        else:
            for F in W.fillers:
                kf = ke["fillers"].get(F.id)
                if kf is None:
                    wp.append(f"V12: key misses {F.id}")
                    continue
                if kf["verdict"] != cards[F.id]["verdict"]:
                    wp.append(f"V12: key verdict of {F.id} {kf['verdict']} != {cards[F.id]['verdict']}")
                for t, s in kf.get("F2", {}).items():
                    if t not in cards[F.id]["F2"] or cards[F.id]["F2"][t]["status"] != s:
                        wp.append(f"V12: key F2 {F.id} {t} {s}")
            if set(ke["fillers"]) != {F.id for F in W.fillers}:
                wp.append("V12: key fillers differ from the world's")
            kept = [F.id for F in W.fillers if cards[F.id]["verdict"] == SAME]
            if len(W.fillers) > 1:
                if sorted(ke.get("kept") or []) != sorted(kept):
                    wp.append(f"V12: kept {ke.get('kept')} != {kept}")
                wp += check_decisive(W, kept, ke.get("decisive"))
                pr(f"  kept {kept}; decisive states:")
                for ent in ke.get("decisive") or []:
                    Fa = next(F for F in W.fillers if F.id == ent["pair"][0])
                    Fb = next(F for F in W.fillers if F.id == ent["pair"][1])
                    ia, ib = predicted_interval(W, Fa, ent["state"]), predicted_interval(W, Fb, ent["state"])
                    pr(f"    {ent['pair']} at {ent['state']} by {ent['observer']}: "
                       f"{[str(x) for x in ia]} vs {[str(x) for x in ib]}")
            else:
                if ke.get("kept") is not None or ke.get("decisive") is not None:
                    wp.append("key: kept/decisive must be null in a single-filler world")
            for t in ke.get("traps", []):
                if t not in flags_w:
                    wp.append(f"trap {t} declared but its condition does not hold")
        for p in wp:
            pr(f"  PROBLEM {p}")
        problems += [f"{wid}: {p}" for p in wp if not p.startswith("V8 (note)")]
        summary[wid] = {"W": W, "cards": cards, "flags": flags_w, "key": ke}

    # ---- composition (Section 6)
    pr("\n=== composition")
    single = {w: s for w, s in summary.items() if len(s["W"].fillers) == 1}
    multi = {w: s for w, s in summary.items() if len(s["W"].fillers) > 1}
    counts = {}
    for w, s in single.items():
        (c,) = s["cards"].values()
        counts[c["verdict"]] = counts.get(c["verdict"], 0) + 1
    f3a = [w for w, s in single.items() if list(s["cards"].values())[0].get("f3alone")]
    pr(f"single-filler worlds {len(single)}: {counts}; decided by F3 alone: {f3a}")
    want = {SAME: 7, ANOTHER: 8, INVALID: 3, COND: 7}
    if len(single) != 25 or counts != want:
        problems.append(f"composition: single-filler verdicts {counts} != {want}")
    if len(f3a) < 2:
        problems.append("composition: fewer than 2 ANOTHER_LAW worlds decided by F3 alone")
    third = [w for w, s in multi.items()
             if any(c["verdict"] in (ANOTHER, INVALID) for c in s["cards"].values())]
    pr(f"several-filler worlds {len(multi)}: " + ", ".join(
        f"{w}={[c['verdict'][:4] for c in s['cards'].values()]}" for w, s in multi.items()) + f"; with a third ANOTHER/INVALID: {third}")
    if len(multi) != 5:
        problems.append("composition: need 5 several-filler worlds")
    if len(third) < 2:
        problems.append("composition: fewer than 2 several-filler worlds with an ANOTHER/INVALID filler")
    for w, s in multi.items():
        if not 2 <= len(s["W"].fillers) <= 3:
            problems.append(f"composition: {w} has {len(s['W'].fillers)} fillers")
    # traps
    trap_worlds = {}
    for w, s in summary.items():
        for t in s["flags"]:
            trap_worlds.setdefault(t, []).append(w)
    for t in ("T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9"):
        ws = trap_worlds.get(t, [])
        pr(f"trap {t}: {ws}")
        if len(ws) < 2:
            problems.append(f"trap {t} appears in fewer than 2 worlds")
    m06 = [w for w, s in summary.items() for c in s["cards"].values() if c["traps"].get("T2") == "m06/rev_t"]
    pr(f"  T2 with m06 under rev_t: {m06}")
    if not m06:
        problems.append("T2 needs one filler with m06 under rev_t")
    t7m = {"registry": [], "new?": []}
    t7u = {"registry": [], "new?": []}
    for w, s in summary.items():
        for c in s["cards"].values():
            t7 = c["traps"].get("T7")
            if t7:
                for k in t7["matters"]:
                    t7m[k].append(w)
                for k in t7["unknowns"]:
                    t7u[k].append(w)
    pr(f"  T7 sources by unknowns that matter: {t7m}; by unknowns: {t7u}")
    for k in ("registry", "new?"):
        if len(set(t7m[k])) < 2:
            problems.append(f"T7: fewer than 2 CONDITIONAL fillers through {k} (by unknowns that matter)")
    t8tags = {}
    for w, s in summary.items():
        for c in s["cards"].values():
            for where, t, q, tag in c["traps"].get("T8", []):
                t8tags.setdefault((tag, where), set()).add(w)
    pr(f"  T8 tags: { {f'{k[0]}@{k[1]}': sorted(v) for k, v in t8tags.items()} }")
    for tag in ("m23/rev_t", "axial/refl_x"):
        if not (t8tags.get((tag, "law")) and t8tags.get((tag, "filled"))):
            problems.append(f"T8: no filler with {tag} in both the law and the filled law")
    # types that decide
    decide = {"kind": set(), "meaning": set(), "cast": set()}
    for w, s in summary.items():
        for c in s["cards"].values():
            for t in reason_ts(c["reason"]):
                decide["cast" if t.startswith("exch(") else "kind" if t == "rot_z" else "meaning"].add(w)
    pr(f"transformation types that decide: { {k: sorted(v) for k, v in decide.items()} }")
    for k, v in decide.items():
        if len(v) < 2:
            problems.append(f"type {k} decides fewer than 2 worlds")
    # baseline sensitivity
    for b in ("FIX", "DERIVE", "DIMS", "FORK_ALL"):
        diff = [(w, fid) for w, s in summary.items() for fid, c in s["cards"].items()
                if c["baselines"][b]["verdict"] != c["verdict"]]
        pr(f"baseline {b}: differs from the reference on {len(diff)} fillers: {diff}")
        if len(diff) < 8:
            problems.append(f"baseline {b} differs on fewer than 8 fillers")
    nf = sum(len(s["cards"]) for s in summary.values())
    pr(f"fillers in total: {nf}")
    # diversity
    sigs = {}
    for w, s in summary.items():
        sig = (s["W"].law["eq"], tuple(sorted(F.doc["eq"] for F in s["W"].fillers)))
        sigs.setdefault(sig, []).append(w)
    for sig, ws in sigs.items():
        if len(ws) > 1:
            problems.append(f"diversity: {ws} share the law and filled laws")
    pr("\n=== result")
    if problems:
        for p in problems:
            pr("PROBLEM " + p)
        pr(f"VERIFY: {len(problems)} PROBLEMS")
    else:
        pr("VERIFY: OK")
    print("\n".join(out))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
