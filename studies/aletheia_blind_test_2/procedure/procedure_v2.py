"""Aletheia blind test 2 -- frozen procedure v2.

Part A (primary): decide-or-fork. From the laws plus observations of nonzero quantities (demands):
  levels     -> SUBSUMED (rational values) < comm < graded (only with odd generators) < assoc;
  viable     -> an admissible algebra exists at the level (demands stay nonzero);
  F_occ      -> the first viable level (conservatism: keep the known rules unless a given forces);
  F_role     -> the first viable level that also keeps every live mention (subterm of the laws
                that is nonzero in the assoc mold) nonzero;
  answer     -> DETERMINED(F) if F_occ = F_role = F; otherwise FORK over the viable levels from
                F_occ to F_role, each non-last branch with a decisive set of mentions (observing
                all of them nonzero excludes the branch) and ideal-membership certificates.
Part B (secondary): grades of zero for a candidate term with exact interval observations.

Usage:  python procedure_v2.py run <worlds_dir> <out_json>
"""
import json
import os
import sys
import random
import itertools
from fractions import Fraction

import sympy as sp
from sympy.parsing.sympy_parser import parse_expr

# ----------------------------------------------------------------- pre-registered constants
D_BY_NGENS = {1: 10, 2: 8, 3: 6, 4: 5}
RATIONAL_GRID = [Fraction(v) for v in (-3, -2, -1, 0, 1, 2, 3)] + [Fraction(-1, 2), Fraction(1, 2)]
PARAM_SAMPLES = [Fraction(v) for v in (-3, -2, -1, 0, 1, 2, 3)] + [Fraction(1, 2)]
MAX_PARAM_COMBOS = 64
PARAM_SEED = 2026
FAMILY_ORDER = ("comm", "graded", "assoc")


class WorldError(Exception):
    pass


# ================================================================= polynomials
# A "poly" is a dict {(varmono, word): Fraction}; varmono = exponent tuple of the universally
# quantified (commuting) variables, word = tuple of generator indices.

def p_add(p, q, s=1):
    r = dict(p)
    for k, v in q.items():
        nv = r.get(k, 0) + s * v
        if nv == 0:
            r.pop(k, None)
        else:
            r[k] = nv
    return r


def p_mul(p, q):
    r = {}
    for (vm1, w1), c1 in p.items():
        for (vm2, w2), c2 in q.items():
            k = (tuple(a + b for a, b in zip(vm1, vm2)), w1 + w2)
            nv = r.get(k, 0) + c1 * c2
            if nv == 0:
                r.pop(k, None)
            else:
                r[k] = nv
    return r


def to_frac(x):
    if not isinstance(x, sp.Rational):
        raise WorldError("non-rational number %s" % x)
    return Fraction(int(x.p), int(x.q))


class Ctx:
    def __init__(self, world, param_values=None):
        self.gens = [g["name"] for g in world["generators"]]
        self.grades = [int(g.get("grade", 0)) % 2 for g in world["generators"]]
        self.vars = list(world.get("variables", []))
        self.params = list(world.get("parameters", []))
        self.gen_index = {n: i for i, n in enumerate(self.gens)}
        self.var_index = {n: i for i, n in enumerate(self.vars)}
        self.param_values = dict(param_values or {})
        self.local = {}
        for n in self.gens:
            self.local[n] = sp.Symbol(n, commutative=False)
        for n in self.vars + self.params:
            self.local[n] = sp.Symbol(n, commutative=True)
        self.zero_vm = (0,) * len(self.vars)

    def one(self):
        return {(self.zero_vm, ()): Fraction(1)}

    def parse(self, s):
        return parse_expr(s, local_dict=self.local, evaluate=False)

    def word_str(self, w):
        return "*".join(self.gens[i] for i in w) if w else "1"


def to_poly(e, ctx):
    if e.is_Number:
        v = to_frac(e)
        return {} if v == 0 else {(ctx.zero_vm, ()): v}
    if e.is_Symbol:
        n = e.name
        if n in ctx.gen_index:
            return {(ctx.zero_vm, (ctx.gen_index[n],)): Fraction(1)}
        if n in ctx.var_index:
            vm = [0] * len(ctx.vars)
            vm[ctx.var_index[n]] = 1
            return {(tuple(vm), ()): Fraction(1)}
        if n in ctx.param_values:
            v = ctx.param_values[n]
            return {} if v == 0 else {(ctx.zero_vm, ()): v}
        raise WorldError("unknown symbol %s" % n)
    if e.is_Add:
        r = {}
        for a in e.args:
            r = p_add(r, to_poly(a, ctx))
        return r
    if e.is_Mul:
        r = ctx.one()
        for a in e.args:
            r = p_mul(r, to_poly(a, ctx))
        return r
    if e.is_Pow:
        b, x = e.args
        if not x.is_Integer:
            raise WorldError("non-integer power")
        k = int(x)
        bp = to_poly(b, ctx)
        if k < 0:
            if len(bp) == 1 and list(bp.keys())[0] == (ctx.zero_vm, ()):
                c = list(bp.values())[0]
                return {(ctx.zero_vm, ()): c ** k}
            raise WorldError("negative power of a non-constant")
        r = ctx.one()
        for _ in range(k):
            r = p_mul(r, bp)
        return r
    raise WorldError("unsupported expression %s" % e)


def split_by_vm(poly):
    groups = {}
    for (vm, w), c in poly.items():
        groups.setdefault(vm, {})[w] = c
    return groups


def has_gen(e, ctx):
    return any(getattr(s, "name", None) in ctx.gen_index for s in e.free_symbols)


def parse_world_laws(world, ctx):
    """relations (noncommutative polys, one per variable monomial of each law's residual),
    their sources [(law_index, varmono)], and the mentions [(text, poly)]."""
    relations, sources, content = [], [], []
    seen = set()
    for li, law in enumerate(world["laws"]):
        if law.count("=") != 1:
            raise WorldError("law must contain exactly one '=': %s" % law)
        lhs_s, rhs_s = law.split("=")
        lhs, rhs = ctx.parse(lhs_s), ctx.parse(rhs_s)
        resid = p_add(to_poly(lhs, ctx), to_poly(rhs, ctx), -1)
        for vm, nc in sorted(split_by_vm(resid).items()):
            if nc:
                relations.append(nc)
                sources.append(("law", li, list(vm)))
        for side in (lhs, rhs):
            stack = [side]
            while stack:
                x = stack.pop()
                if has_gen(x, ctx):
                    p = to_poly(x, ctx)
                    key = frozenset(p.items())
                    if p and key not in seen:
                        seen.add(key)
                        content.append((str(x), p))
                stack.extend(x.args)
    return relations, sources, content


def parse_demands(world, ctx):
    out = []
    for o in world.get("observations", []):
        if o.get("status") != "nonzero":
            raise WorldError("Part A observations must have status 'nonzero'")
        p = to_poly(ctx.parse(o["expr"]), ctx)
        out.append((o["expr"], p))
    return out


# ================================================================= molds

def words_of_len(n, L):
    return itertools.product(range(n), repeat=L)


class TruncMold:
    """Freest associative algebra on n generators modulo the two-sided ideal of `relations`,
    by linear algebra on words of length <= D (echelon form, deg-lex, longest first).
    With track=True every pivot row remembers how it was built from the rows u*r*v, so a
    reduction to zero yields an ideal-membership certificate."""

    def __init__(self, n, relations, D, track=False):
        self.n, self.D, self.track = n, D, track
        self.pivots = {}
        self.origins = {}
        self.skipped = 0
        for k, r in enumerate(relations):
            if not r:
                continue
            deg = max(len(w) for w in r)
            if deg > D:
                self.skipped += 1
                continue
            for la in range(D - deg + 1):
                for lb in range(D - deg - la + 1):
                    for a in words_of_len(n, la):
                        for b in words_of_len(n, lb):
                            row = {a + w + b: c for w, c in r.items()}
                            org = {(a, k, b): Fraction(1)} if track else None
                            self._add(row, org)

    @staticmethod
    def _key(w):
        return (len(w), w)

    def _reduce(self, row, org=None):
        row = dict(row)
        org = dict(org) if org is not None else None
        while row:
            lead = max(row, key=self._key)
            piv = self.pivots.get(lead)
            if piv is None:
                return row, lead, org
            c = row[lead]
            for w, v in piv.items():
                nv = row.get(w, 0) - c * v
                if nv == 0:
                    row.pop(w, None)
                else:
                    row[w] = nv
            if org is not None:
                for t, v in self.origins[lead].items():
                    nv = org.get(t, 0) - c * v
                    if nv == 0:
                        org.pop(t, None)
                    else:
                        org[t] = nv
        return row, None, org

    def _add(self, row, org=None):
        row, lead, org = self._reduce(row, org)
        if lead is None:
            return
        c = row[lead]
        self.pivots[lead] = {w: v / c for w, v in row.items()}
        if self.track:
            self.origins[lead] = {t: v / c for t, v in org.items()}

    def is_zero(self, nc):
        if any(len(w) > self.D for w in nc):
            return False
        return self._reduce(nc)[1] is None

    def certificate(self, nc):
        """If nc reduces to zero: {(u, k, v): coef} with nc = sum coef * u * rel_k * v."""
        if not self.track or any(len(w) > self.D for w in nc):
            return None
        row, lead, org = self._reduce(nc, {})
        if lead is not None:
            return None
        return {t: -v for t, v in org.items()}

    def trivial(self):
        return self.is_zero({(): Fraction(1)})

    def dim(self):
        if self.trivial():
            return 0
        counts = []
        for L in range(self.D + 1):
            counts.append(sum(1 for w in words_of_len(self.n, L) if w not in self.pivots))
        for L in range(1, self.D + 1):
            if counts[L] == 0:
                return sum(counts[:L])
        return "inf"


class CommMold:
    """Exact commutative mold via a Groebner basis over QQ."""

    def __init__(self, n, relations):
        self.n = n
        self.syms = sp.symbols("z0:%d" % n)
        polys = [p for p in (self.to_comm(r) for r in relations) if p != 0]
        self.G = sp.groebner(polys, *self.syms, order="grevlex", domain="QQ") if polys else None

    def to_comm(self, nc):
        expr = sp.Integer(0)
        for w, c in nc.items():
            t = sp.Rational(c.numerator, c.denominator)
            for i in w:
                t = t * self.syms[i]
            expr += t
        return sp.expand(expr)

    def trivial(self):
        return self.G is not None and list(self.G.exprs) == [1]

    def is_zero(self, nc):
        p = self.to_comm(nc)
        if p == 0:
            return True
        if self.G is None:
            return False
        return self.G.reduce(p)[1] == 0

    def dim(self):
        if self.trivial():
            return 0
        if self.G is None or not self.G.is_zero_dimensional:
            return "inf"
        lms = [sp.Poly(g, *self.syms).monoms(order="grevlex")[0] for g in self.G.exprs]

        def divisible(m):
            return any(all(m[i] >= l[i] for i in range(self.n)) for l in lms)

        start = (0,) * self.n
        if divisible(start):
            return 0
        seen, frontier, count = {start}, [start], 0
        while frontier:
            m = frontier.pop()
            count += 1
            if count > 100000:
                return "inf"
            for i in range(self.n):
                m2 = list(m)
                m2[i] += 1
                m2 = tuple(m2)
                if m2 not in seen and not divisible(m2):
                    seen.add(m2)
                    frontier.append(m2)
        return count


def family_rules(fam, ctx):
    """Extra relations of a family, with their sources."""
    n = len(ctx.gens)
    rules, srcs = [], []
    if fam == "graded":
        for i in range(n):
            for j in range(i, n):
                s = -1 if (ctx.grades[i] and ctx.grades[j]) else 1
                if i == j:
                    if s == -1:
                        rules.append({(i, i): Fraction(1)})
                        srcs.append(("graded", ctx.gens[i], ctx.gens[i]))
                else:
                    rules.append({(i, j): Fraction(1), (j, i): Fraction(-s)})
                    srcs.append(("graded", ctx.gens[i], ctx.gens[j]))
    return rules, srcs


def build_mold(fam, ctx, relations, D, track=False):
    n = len(ctx.gens)
    if fam == "comm":
        return CommMold(n, relations)
    rules, _ = family_rules(fam, ctx)
    return TruncMold(n, relations + rules, D, track=track)


def alive(mold, poly):
    return any(not mold.is_zero(nc) for nc in split_by_vm(poly).values() if nc)


def rational_solutions(relations, n):
    cm = CommMold(n, relations)
    if cm.trivial():
        return []
    if cm.G is None:
        return [tuple(v) for v in itertools.product(RATIONAL_GRID, repeat=n)]
    sols = []
    if cm.G.is_zero_dimensional:
        try:
            raw = sp.solve(list(cm.G.exprs), list(cm.syms), dict=True)
            for d in raw:
                vals, ok = [], True
                for s in cm.syms:
                    v = d.get(s)
                    if v is None or not v.is_Rational:
                        ok = False
                        break
                    vals.append(to_frac(v))
                if ok:
                    sols.append(tuple(vals))
            return sols
        except Exception:
            pass
    for vals in itertools.product(RATIONAL_GRID, repeat=n):
        subs = {cm.syms[i]: sp.Rational(vals[i].numerator, vals[i].denominator) for i in range(n)}
        if all(sp.expand(g.subs(subs)) == 0 for g in cm.G.exprs):
            sols.append(vals)
    return sols


def nonzero_at(poly, vals):
    groups = {}
    for (vm, w), c in poly.items():
        t = c
        for i in w:
            t *= vals[i]
        groups[vm] = groups.get(vm, 0) + t
    return any(v != 0 for v in groups.values())


def frac_str(v):
    return str(v.numerator) if v.denominator == 1 else "%d/%d" % (v.numerator, v.denominator)


# ================================================================= Part A: levels

def _prepare(world, param_values):
    ctx = Ctx(world, param_values)
    relations, sources, content = parse_world_laws(world, ctx)
    n = len(ctx.gens)
    if n not in D_BY_NGENS:
        raise WorldError("budget: %d generators" % n)
    D = D_BY_NGENS[n]
    maxdeg = max([max(len(w) for w in r) for r in relations] + [0])
    if maxdeg > D - 1:
        raise WorldError("budget: relation degree %d > %d" % (maxdeg, D - 1))
    demands = parse_demands(world, ctx)
    return ctx, relations, sources, content, demands, n, D


def analyse_levels(world, param_values=None):
    """The shared analysis behind the procedure and its baselines."""
    ctx, relations, sources, content, demands, n, D = _prepare(world, param_values)
    A = TruncMold(n, relations, D)
    res = {"ctx": ctx, "relations": relations, "sources": sources, "D": D, "n": n,
           "demands": demands, "levels": []}
    if A.trivial():
        res["contradiction"] = "1 = 0 in the assoc mold"
        return res
    dead = [s for s, p in demands if not alive(A, p)]
    if dead:
        res["contradiction"] = "the laws force observed quantities to zero: %s" % ", ".join(dead)
        return res
    live = [(s, p) for s, p in content if alive(A, p)]
    res["live"] = live
    sols = rational_solutions(relations, n)
    viable_sols = [s for s in sols if all(nonzero_at(p, s) for _, p in demands)]
    if viable_sols:
        kills = [[m for m, p in live if not nonzero_at(p, s)] for s in viable_sols]
        passing = [s for s, k in zip(viable_sols, kills) if not k]
        res["levels"].append({"level": "SUBSUMED", "keeps_all": bool(passing), "passing": passing,
                              "viable_sols": viable_sols, "kills": kills, "dim": 1})
    for fam in FAMILY_ORDER:
        if fam == "graded" and not any(ctx.grades):
            continue
        M = build_mold(fam, ctx, relations, D)
        if M.trivial() or not all(alive(M, p) for _, p in demands):
            continue
        killed = [(s, p) for s, p in live if not alive(M, p)]
        res["levels"].append({"level": fam, "keeps_all": not killed, "killed": killed, "mold": M})
    return res


def _det(lv, stable=None):
    out = {"label": "DETERMINED", "level": lv["level"]}
    if lv["level"] == "SUBSUMED":
        out["values"] = [[frac_str(v) for v in s] for s in lv["passing"]]
        out["dim"] = 1
    else:
        out["dim"] = lv["mold"].dim()
    return out


def _hitting_set(kills):
    """Greedy: a small set of mentions such that every solution kills at least one of them."""
    remaining = [set(k) for k in kills]
    chosen = []
    order = []
    for k in kills:
        for m in k:
            if m not in order:
                order.append(m)
    while any(remaining):
        best = max(order, key=lambda m: sum(1 for r in remaining if m in r))
        if not any(best in r for r in remaining):
            return None
        chosen.append(best)
        remaining = [r for r in remaining if best not in r]
    return chosen


def _poly_json(poly, ctx):
    out = []
    for (vm, w), c in sorted(poly.items()):
        out.append([dict(zip(ctx.vars, vm)) if ctx.vars else {}, [ctx.gens[i] for i in w], frac_str(c)])
    return out


def _ref(src, ctx):
    """Protocol reference to a relation: a law's variable-monomial coefficient, or a family rule."""
    if src[0] == "law":
        return {"law": src[1], "varmono": dict(zip(ctx.vars, src[2]))}
    return {"rule": src[0], "pair": [src[1], src[2]]}


def _certificates(lv, mentions, res):
    """Ideal-membership certificates for mentions killed at a graded branch:
    for every variable-monomial group g of the mention, g = sum coef * left * relation * right."""
    ctx, relations, sources, D = res["ctx"], res["relations"], res["sources"], res["D"]
    rules, rsrc = family_rules(lv["level"], ctx)
    allrels, allsrc = relations + rules, sources + rsrc
    T = TruncMold(res["n"], allrels, D, track=True)
    certs = []
    polys = dict(res["live"])
    for m in mentions:
        groups = []
        for vm, nc in sorted(split_by_vm(polys[m]).items()):
            cert = T.certificate(nc)
            if cert is None:
                return None
            groups.append({"varmono": dict(zip(ctx.vars, vm)),
                           "terms": [[frac_str(c), [ctx.gens[i] for i in u], _ref(allsrc[k], ctx),
                                      [ctx.gens[i] for i in v]]
                                     for (u, k, v), c in sorted(cert.items())]})
        certs.append({"mention": m, "level": lv["level"], "groups": groups})
    return certs


def classify_v2(world, param_values=None, certificates=True):
    res = analyse_levels(world, param_values)
    if "contradiction" in res:
        return {"label": "CONTRADICTION", "reason": res["contradiction"]}
    levels = res["levels"]
    occ = 0
    role = next(i for i, lv in enumerate(levels) if lv["keeps_all"])
    if role == occ:
        return _det(levels[occ])
    branches, decisive, certs = [], [], []
    for lv in levels[occ:role]:
        if lv["level"] == "SUBSUMED":
            q = _hitting_set(lv["kills"])
            branches.append({"level": "SUBSUMED", "killed": sorted({m for k in lv["kills"] for m in k}),
                             "values": [[frac_str(v) for v in s] for s in lv["viable_sols"]]})
        else:
            q = [lv["killed"][0][0]]
            branches.append({"level": lv["level"], "killed": [m for m, _ in lv["killed"]]})
            if certificates and lv["level"] == "graded":
                c = _certificates(lv, q, res)
                if c is None:
                    return {"label": "ERROR", "reason": "no certificate for %s" % q}
                certs.extend(c)
        decisive.append(q)
    branches.append({"level": levels[role]["level"]})
    return {"label": "FORK", "branches": branches, "decisive": decisive, "certificates": certs}


def classify_V1D(world, param_values=None):
    """Baseline: role rule v1 with demands (mentions treated as demands) -> DETERMINED(F_role)."""
    res = analyse_levels(world, param_values)
    if "contradiction" in res:
        return {"label": "CONTRADICTION"}
    return _det(next(lv for lv in res["levels"] if lv["keeps_all"]))


def classify_OCC(world, param_values=None):
    """Baseline: conservative, ignores mentions -> DETERMINED(F_occ)."""
    res = analyse_levels(world, param_values)
    if "contradiction" in res:
        return {"label": "CONTRADICTION"}
    lv = res["levels"][0]
    out = _det(lv)
    if lv["level"] == "SUBSUMED":
        out["values"] = [[frac_str(v) for v in s] for s in lv["viable_sols"]]
    return out


def classify_FORKALL(world, param_values=None):
    """Baseline: fork from F_occ straight to assoc whenever F_occ != assoc."""
    res = analyse_levels(world, param_values)
    if "contradiction" in res:
        return {"label": "CONTRADICTION"}
    lv = res["levels"][0]
    if lv["level"] == "assoc":
        return _det(lv)
    if lv["level"] == "SUBSUMED":
        q = _hitting_set(lv["kills"]) if any(lv["kills"]) else []
    else:
        q = [lv["killed"][0][0]] if lv["killed"] else []
    return {"label": "FORK", "branches": [{"level": lv["level"]}, {"level": "assoc"}], "decisive": [q or []]}


def signature(r):
    if r["label"] == "DETERMINED":
        return ("DETERMINED", r["level"], str(r.get("dim")))
    if r["label"] == "FORK":
        return ("FORK", "|".join(b["level"] for b in r["branches"]))
    return (r["label"],)


def with_parameters(classifier, world):
    params = list(world.get("parameters", []))
    if not params:
        return classifier(world)
    combos = list(itertools.product(PARAM_SAMPLES, repeat=len(params)))
    if len(combos) > MAX_PARAM_COMBOS:
        rng = random.Random(PARAM_SEED)
        combos = rng.sample(combos, MAX_PARAM_COMBOS)
    results = []
    for combo in combos:
        pv = dict(zip(params, combo))
        try:
            r = classifier(world, pv)
        except WorldError as ex:
            r = {"label": "UNDETERMINED", "reason": str(ex)}
        results.append(r)
    sigs = {signature(r) for r in results}
    if len(sigs) == 1:
        out = dict(results[0])
        out["open_parameters"] = params
        out.pop("values", None)
        return out
    return {"label": "UNDERDETERMINED", "variants": sorted("/".join(s) for s in sigs)}


def run_a(world):
    out = {}
    for name, fn in (("procedure", classify_v2), ("V1D", classify_V1D),
                     ("OCC", classify_OCC), ("FORKALL", classify_FORKALL)):
        try:
            out[name] = with_parameters(fn, world)
        except WorldError as ex:
            out[name] = {"label": "UNDETERMINED", "reason": str(ex)}
        except Exception as ex:  # pragma: no cover - recorded, not hidden
            out[name] = {"label": "ERROR", "reason": "%s: %s" % (type(ex).__name__, ex)}
    return out


# ================================================================= Part B: grades of zero

class BWorld:
    """A law y = f(inputs) with a candidate term unknown * h(inputs), exact rationals only."""

    def __init__(self, world):
        self.w = world
        self.qd = {q: {k: Fraction(str(v)) for k, v in d.items()} for q, d in world["quantities"].items()}
        self.consts = world.get("constants", {})
        self.cd = {c: {k: Fraction(str(v)) for k, v in spec.get("dims", {}).items()} for c, spec in self.consts.items()}
        self.params = {p: sp.Rational(v) for p, v in world.get("parameters", {}).items()}
        self.unknown_name = world["term"]["unknown"]
        names = list(self.qd) + list(self.consts) + list(self.params) + [self.unknown_name]
        for s in world.get("symmetries", []):
            names += list(s.get("params", {}))
        self.sym = {n: sp.Symbol(n) for n in names}
        lhs, rhs = world["law"].split("=")
        self.y = sp.sympify(lhs.strip(), locals=self.sym)
        if not self.y.is_Symbol or self.y.name not in self.qd:
            raise WorldError("Part B law must be explicit: y = f(...)")
        self.f = sp.sympify(rhs.strip(), locals=self.sym)
        term = sp.sympify(world["term"]["expr"], locals=self.sym)
        lam = self.sym[self.unknown_name]
        if sp.simplify(term.subs(lam, 0)) != 0 or sp.simplify(sp.diff(term, lam, 2)) != 0:
            raise WorldError("the term must be linear in the unknown")
        self.lam = lam
        self.h = sp.simplify(sp.diff(term, lam))
        self.form = world.get("coefficient_form", "free")

    def values(self, inputs):
        env = {self.sym[k]: sp.Rational(v) for k, v in inputs.items()}
        env.update({self.sym[c]: sp.Rational(spec["value"]) for c, spec in self.consts.items()})
        env.update({self.sym[p]: v for p, v in self.params.items()})
        fv = sp.nsimplify(self.f.xreplace(env))
        hv = sp.nsimplify(self.h.xreplace(env))
        if not (fv.is_Rational and hv.is_Rational):
            raise WorldError("observation does not evaluate to an exact rational")
        return Fraction(int(fv.p), int(fv.q)), Fraction(int(hv.p), int(hv.q))

    def dims_of(self, e):
        table = dict(self.qd)
        table.update(self.cd)
        table.update({p: {} for p in self.params})
        return d_norm(dim_expr(e, table))

    def type_check(self):
        """None if the coefficient can be built from the declared constants (or is free);
        otherwise the needed dimension that no product of constant powers reaches."""
        if self.form != "constants":
            return None, None
        need = d_add(self.dims_of(self.y), {k: -v for k, v in self.dims_of(self.h).items()})
        if not need:
            return None, {}
        base = sorted(set(need) | {k for d in self.cd.values() for k in d})
        names = sorted(self.cd)
        if not names:
            return need, None
        V = sp.Matrix([[sp.Rational(self.cd[c].get(b, 0)) for c in names] for b in base])
        t = sp.Matrix([sp.Rational(need.get(b, 0)) for b in base])
        if V.rank() != V.row_join(t).rank():
            return need, None
        sol, params = V.gauss_jordan_solve(t)
        sol = sol.subs({p: 0 for p in params})
        return None, {c: str(sol[i]) for i, c in enumerate(names) if sol[i] != 0}

    def symmetry_forces_zero(self):
        forced = []
        F = self.f + self.lam * self.h
        for s in self.w.get("symmetries", []):
            new = {self.sym[q]: sp.sympify(e, locals=self.sym) for q, e in s["map"].items()}
            y_new = new.get(self.y, self.y).xreplace({self.y: F})
            rhs_new = F.xreplace({k: v for k, v in new.items() if k != self.y})
            E = sp.simplify(sp.together(y_new - rhs_new))
            if sp.simplify(E.subs(self.lam, 0)) != 0:
                raise WorldError("declared symmetry %s is not a symmetry of the base law" % s.get("name"))
            if sp.simplify(sp.diff(E, self.lam)) != 0:
                forced.append(s.get("name", "?"))
        return forced

    def incidental(self):
        if not self.params:
            return False
        at = sp.simplify(self.h.xreplace({self.sym[p]: v for p, v in self.params.items()}))
        return at == 0 and sp.simplify(self.h) != 0

    def feasible(self):
        """Exact feasible interval of the unknown: ('conflict', why) | ('none',) | ('interval', lo, hi)."""
        lo, hi, constrained = None, None, False
        for k, ob in enumerate(self.w.get("observations", [])):
            fv, hv = self.values(ob["inputs"])
            r = Fraction(sp.Rational(ob["output"]).p, sp.Rational(ob["output"]).q) - fv
            d = Fraction(sp.Rational(ob["resolution"]).p, sp.Rational(ob["resolution"]).q)
            if hv == 0:
                if abs(r) > d:
                    return ("conflict", "observation %d misses the base law by more than its resolution" % k)
                continue
            a, b = sorted(((r - d) / hv, (r + d) / hv))
            lo = a if lo is None else max(lo, a)
            hi = b if hi is None else min(hi, b)
            constrained = True
        if not constrained:
            return ("none",)
        if lo > hi:
            return ("conflict", "no value of the unknown fits all observations")
        return ("interval", lo, hi)


def _interval_class(fz):
    if fz[0] == "conflict":
        return {"label": "CONFLICT", "reason": fz[1]}
    if fz[0] == "none":
        return {"label": "UNCONSTRAINED"}
    lo, hi = fz[1], fz[2]
    if lo > 0 or hi < 0:
        return {"label": "ACTIVE", "interval": [frac_str(lo), frac_str(hi)]}
    return {"label": "BOUNDED", "bound": frac_str(max(abs(lo), abs(hi))),
            "interval": [frac_str(lo), frac_str(hi)]}


def classify_B(world):
    bw = BWorld(world)
    fz = bw.feasible()
    need, bridge = bw.type_check()
    reasons = []
    if need is not None:
        reasons.append(("TYPE_IMPOSSIBLE", "no product of declared constants has dimension %s" % need))
    forced = bw.symmetry_forces_zero()
    if forced:
        reasons.append(("SYMMETRY_ZERO", "forbidden by %s" % ", ".join(forced)))
    if bw.incidental():
        reasons.append(("INCIDENTAL", "the term vanishes at the given parameter values"))
    if fz[0] == "conflict":
        return {"label": "CONFLICT", "reason": fz[1]}
    if reasons:
        detected = fz[0] == "interval" and (fz[1] > 0 or fz[2] < 0)
        if detected:
            return {"label": "CONFLICT", "reason": "detected although %s" % reasons[0][1]}
        out = {"label": reasons[0][0], "reason": reasons[0][1]}
        if len(reasons) > 1:
            out["also"] = [r[0] for r in reasons[1:]]
        return out
    out = _interval_class(fz)
    if bridge:
        out["bridge"] = bridge
    return out


def classify_B_THRESH(world):
    """Baseline: anything not detected is dead (false death); ignores type, symmetry, parameters."""
    bw = BWorld(world)
    out = _interval_class(bw.feasible())
    if out["label"] in ("BOUNDED", "UNCONSTRAINED"):
        return {"label": "ZERO"}
    return out


def classify_B_MENTION(world):
    """Baseline: a mentioned term is real unless dimensionally impossible (role rule v1 style)."""
    bw = BWorld(world)
    need, _ = bw.type_check()
    return {"label": "TYPE_IMPOSSIBLE"} if need is not None else {"label": "ACTIVE"}


def classify_B_NOSYM(world):
    """Baseline: the procedure without symmetry and parameter reasoning."""
    bw = BWorld(world)
    fz = bw.feasible()
    need, _ = bw.type_check()
    if fz[0] == "conflict":
        return {"label": "CONFLICT", "reason": fz[1]}
    if need is not None:
        detected = fz[0] == "interval" and (fz[1] > 0 or fz[2] < 0)
        return {"label": "CONFLICT"} if detected else {"label": "TYPE_IMPOSSIBLE"}
    return _interval_class(fz)


def run_b(world):
    out = {}
    for name, fn in (("procedure", classify_B), ("THRESH", classify_B_THRESH),
                     ("MENTION", classify_B_MENTION), ("NOSYM", classify_B_NOSYM)):
        try:
            out[name] = fn(world)
        except WorldError as ex:
            out[name] = {"label": "UNDETERMINED", "reason": str(ex)}
        except Exception as ex:  # pragma: no cover - recorded, not hidden
            out[name] = {"label": "ERROR", "reason": "%s: %s" % (type(ex).__name__, ex)}
    return out


# ----------------------------------------------------------------- dimensions (as in v1, E2)

class DimError(Exception):
    pass


def d_norm(d):
    return {k: v for k, v in d.items() if v != 0}


def d_add(a, b):
    r = dict(a)
    for k, v in b.items():
        r[k] = r.get(k, 0) + v
    return d_norm(r)


def dim_expr(e, qd):
    if e.is_Number:
        return {}
    if e.is_Symbol:
        if e.name not in qd:
            raise DimError("undeclared symbol %s" % e.name)
        return dict(qd[e.name])
    if e.is_Add:
        ds = [d_norm(dim_expr(a, qd)) for a in e.args]
        for d in ds[1:]:
            if d != ds[0]:
                raise DimError("sum of different dimensions")
        return ds[0]
    if e.is_Mul:
        r = {}
        for a in e.args:
            r = d_add(r, dim_expr(a, qd))
        return r
    if e.is_Pow:
        b, x = e.args
        if x.is_Rational:
            xf = Fraction(int(x.p), int(x.q))
            return d_norm({k: v * xf for k, v in dim_expr(b, qd).items()})
        if d_norm(dim_expr(b, qd)) or d_norm(dim_expr(x, qd)):
            raise DimError("dimensionful base/exponent with symbolic exponent")
        return {}
    raise DimError("unsupported %s" % e)


# ================================================================= runner

def run_dir(worlds_dir, out_path):
    results = {}
    for fn in sorted(os.listdir(worlds_dir)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(worlds_dir, fn), encoding="utf-8") as fh:
            world = json.load(fh)
        wid = world.get("id", fn)
        try:
            if world.get("experiment") == "A":
                results[wid] = run_a(world)
            elif world.get("experiment") == "B":
                results[wid] = run_b(world)
            else:
                results[wid] = {"error": "unknown experiment"}
        except Exception as ex:
            results[wid] = {"error": "%s: %s" % (type(ex).__name__, ex)}
        proc = results[wid].get("procedure", results[wid])
        print(wid, json.dumps({k: v for k, v in proc.items() if k != "certificates"}, ensure_ascii=False))
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=1, sort_keys=True)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "run":
        run_dir(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
