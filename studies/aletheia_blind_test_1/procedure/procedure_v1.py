"""Aletheia blind test 1 -- frozen procedure v1.

E1 (hidden kinds). From the laws alone:
  shadow  -> relations extracted from the laws (coefficients of every monomial in the
             universally quantified variables);
  molds   -> the freest algebra satisfying the relations in each family
             comm (all generators commute) < graded (Koszul signs from declared grades) < assoc;
  role    -> "no silent loss of the law's content": every syntactic subterm of the laws (as
             written) that is nonzero in the loosest mold (assoc) must stay nonzero;
  order   -> known rational values first (subsumption), then the most restrictive family
             whose mold is nontrivial and keeps all content alive.
E2 (law identity card). Dimensions, validated predictions, listed symmetries, state.

Also computes the pre-registered baselines B1/B2/B3 (E1) and C1/C2/C3 (E2).

Usage:  python procedure_v1.py run <worlds_dir> <out_json>
All constants below are pre-registered. Changing anything after sealing voids the test.
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
D_BY_NGENS = {1: 10, 2: 8, 3: 6, 4: 5}          # max word length of the truncated engine
RATIONAL_GRID = [Fraction(v) for v in (-3, -2, -1, 0, 1, 2, 3)] + [Fraction(-1, 2), Fraction(1, 2)]
PARAM_SAMPLES = [Fraction(v) for v in (-3, -2, -1, 0, 1, 2, 3)] + [Fraction(1, 2)]
MAX_PARAM_COMBOS = 64
PARAM_SEED = 2026
E2_SAMPLES = 20
E2_SEED = 12345
E2_REL_TOL = 1e-9
E2_ABS_TOL = 1e-12
E2_DEFAULT_RANGE = (Fraction(1, 2), Fraction(3))
FAMILY_ORDER = ("comm", "graded", "assoc")


class WorldError(Exception):
    pass


# ================================================================= E1: polynomials
# A "poly" is a dict {(varmono, word): Fraction}; varmono = exponent tuple of the
# universally quantified (commuting) variables, word = tuple of generator indices.

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
    relations, content = [], []
    seen = set()
    for law in world["laws"]:
        if law.count("=") != 1:
            raise WorldError("law must contain exactly one '=': %s" % law)
        lhs_s, rhs_s = law.split("=")
        lhs, rhs = ctx.parse(lhs_s), ctx.parse(rhs_s)
        resid = p_add(to_poly(lhs, ctx), to_poly(rhs, ctx), -1)
        for vm, nc in split_by_vm(resid).items():
            if nc:
                relations.append(nc)
        for side in (lhs, rhs):
            stack = [side]
            while stack:
                x = stack.pop()
                if has_gen(x, ctx):
                    p = to_poly(x, ctx)
                    key = frozenset(p.items())
                    if p and key not in seen:
                        seen.add(key)
                        content.append(p)
                stack.extend(x.args)
    return relations, content


# ================================================================= E1: molds

def words_of_len(n, L):
    return itertools.product(range(n), repeat=L)


class TruncMold:
    """Freest associative algebra on n generators modulo the two-sided ideal of `relations`,
    computed by linear algebra on words of length <= D (echelon form, deg-lex, longest first)."""

    def __init__(self, n, relations, D):
        self.n, self.D = n, D
        self.pivots = {}
        self.skipped = 0
        for r in relations:
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
                            self._add({a + w + b: c for w, c in r.items()})

    @staticmethod
    def _key(w):
        return (len(w), w)

    def _reduce(self, row):
        row = dict(row)
        while row:
            lead = max(row, key=self._key)
            piv = self.pivots.get(lead)
            if piv is None:
                return row, lead
            c = row[lead]
            for w, v in piv.items():
                nv = row.get(w, 0) - c * v
                if nv == 0:
                    row.pop(w, None)
                else:
                    row[w] = nv
        return row, None

    def _add(self, row):
        row, lead = self._reduce(row)
        if lead is None:
            return
        c = row[lead]
        self.pivots[lead] = {w: v / c for w, v in row.items()}

    def is_zero(self, nc):
        if any(len(w) > self.D for w in nc):
            return False
        return self._reduce(nc)[1] is None

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


def family_relations(fam, ctx, relations):
    n = len(ctx.gens)
    extra = []
    if fam == "graded":
        for i in range(n):
            for j in range(i, n):
                s = -1 if (ctx.grades[i] and ctx.grades[j]) else 1
                if i == j:
                    if s == -1:
                        extra.append({(i, i): Fraction(1)})
                else:
                    extra.append({(i, j): Fraction(1), (j, i): Fraction(-s)})
    return relations + extra


def build_mold(fam, ctx, relations, D):
    n = len(ctx.gens)
    if fam == "comm":
        return CommMold(n, relations)
    return TruncMold(n, family_relations(fam, ctx, relations), D)


def alive(mold, poly):
    return any(not mold.is_zero(nc) for nc in split_by_vm(poly).values() if nc)


def rational_solutions(relations, n):
    syms = sp.symbols("z0:%d" % n)
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


# ================================================================= E1: classifiers

def _prepare(world, param_values):
    ctx = Ctx(world, param_values)
    relations, content = parse_world_laws(world, ctx)
    n = len(ctx.gens)
    if n not in D_BY_NGENS:
        raise WorldError("budget: %d generators" % n)
    D = D_BY_NGENS[n]
    maxdeg = max([max(len(w) for w in r) for r in relations] + [0])
    if maxdeg > D - 1:
        raise WorldError("budget: relation degree %d > %d" % (maxdeg, D - 1))
    return ctx, relations, content, n, D


def classify_procedure(world, param_values=None):
    ctx, relations, content, n, D = _prepare(world, param_values)
    A = TruncMold(n, relations, D)
    A2 = TruncMold(n, relations, D - 1)
    if A.trivial():
        return {"label": "CONTRADICTION", "family": None, "dim": 0, "stable": True}
    live = [p for p in content if alive(A, p)]
    stable = (A2.trivial() == A.trivial()) and all(alive(A2, p) == alive(A, p) for p in content)
    sols = rational_solutions(relations, n)
    passing = [s for s in sols if all(nonzero_at(p, s) for p in live)]
    if passing:
        return {"label": "SUBSUMED", "family": None, "dim": 1, "stable": stable,
                "values": [[frac_str(v) for v in s] for s in passing]}
    for fam in FAMILY_ORDER:
        if fam == "graded" and not any(ctx.grades):
            continue
        M = build_mold(fam, ctx, relations, D)
        if M.trivial():
            continue
        if not all(alive(M, p) for p in live):
            continue
        dim = M.dim()
        if fam != "comm":
            M2 = build_mold(fam, ctx, relations, D - 1)
            stable = stable and (M2.trivial() == M.trivial()) and (M2.dim() == dim) and \
                all(alive(M2, p) == alive(M, p) for p in live)
        return {"label": "NEW_KIND", "family": fam, "dim": dim, "stable": stable}
    return {"label": "CONTRADICTION", "family": None, "dim": 0, "stable": stable}


def classify_B1(world, param_values=None):
    """Old rules always: known value if any rational solution, else commutative mold."""
    ctx, relations, content, n, D = _prepare(world, param_values)
    sols = rational_solutions(relations, n)
    if sols:
        return {"label": "SUBSUMED", "family": None, "dim": 1,
                "values": [[frac_str(v) for v in s] for s in sols]}
    M = CommMold(n, relations)
    if M.trivial():
        return {"label": "CONTRADICTION", "family": None, "dim": 0}
    return {"label": "NEW_KIND", "family": "comm", "dim": M.dim()}


def classify_B2(world, param_values=None):
    """Never impose rules: known value only if the assoc mold is 1-dimensional."""
    ctx, relations, content, n, D = _prepare(world, param_values)
    A = TruncMold(n, relations, D)
    if A.trivial():
        return {"label": "CONTRADICTION", "family": None, "dim": 0}
    d = A.dim()
    if d == 1:
        sols = rational_solutions(relations, n)
        return {"label": "SUBSUMED", "family": None, "dim": 1,
                "values": [[frac_str(v) for v in s] for s in sols]}
    return {"label": "NEW_KIND", "family": "assoc", "dim": d}


def classify_B3(world, param_values=None):
    """Relax only on loud collapse (1 = 0); no role check."""
    ctx, relations, content, n, D = _prepare(world, param_values)
    sols = rational_solutions(relations, n)
    if sols:
        return {"label": "SUBSUMED", "family": None, "dim": 1,
                "values": [[frac_str(v) for v in s] for s in sols]}
    for fam in FAMILY_ORDER:
        if fam == "graded" and not any(ctx.grades):
            continue
        M = build_mold(fam, ctx, relations, D)
        if not M.trivial():
            return {"label": "NEW_KIND", "family": fam, "dim": M.dim()}
    return {"label": "CONTRADICTION", "family": None, "dim": 0}


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
    sigs = {(r["label"], r.get("family"), str(r.get("dim"))) for r in results}
    if len(sigs) == 1:
        out = dict(results[0])
        out["open_parameters"] = params
        out.pop("values", None)
        return out
    return {"label": "UNDERDETERMINED", "family": None, "dim": None,
            "variants": sorted("%s/%s/%s" % s for s in sigs)}


def run_e1(world):
    out = {}
    for name, fn in (("procedure", classify_procedure), ("B1", classify_B1),
                     ("B2", classify_B2), ("B3", classify_B3)):
        try:
            out[name] = with_parameters(fn, world)
        except WorldError as ex:
            out[name] = {"label": "UNDETERMINED", "reason": str(ex)}
        except Exception as ex:  # pragma: no cover - recorded, not hidden
            out[name] = {"label": "ERROR", "reason": "%s: %s" % (type(ex).__name__, ex)}
    return out


# ================================================================= E2: identity card

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
            xf = to_frac(x)
            return d_norm({k: v * xf for k, v in dim_expr(b, qd).items()})
        if d_norm(dim_expr(b, qd)) or d_norm(dim_expr(x, qd)):
            raise DimError("dimensionful base/exponent with symbolic exponent")
        return {}
    if isinstance(e, sp.Function):
        for a in e.args:
            if d_norm(dim_expr(a, qd)):
                raise DimError("function of a dimensionful argument")
        return {}
    raise DimError("unsupported %s" % e)


def law_parts(law, local):
    if law.count("=") != 1:
        raise WorldError("law must contain exactly one '='")
    lhs, rhs = law.split("=")
    lhs = sp.sympify(lhs.strip(), locals=local)
    rhs = sp.sympify(rhs.strip(), locals=local)
    if not lhs.is_Symbol:
        raise WorldError("E2 laws must be explicit: Y = f(...)")
    return lhs, rhs


def dims_ok(law, qd, local):
    try:
        y, f = law_parts(law, local)
        return d_norm(dim_expr(y, qd)) == d_norm(dim_expr(f, qd))
    except DimError:
        return False


def num(v):
    return sp.Rational(v) if isinstance(v, str) else sp.nsimplify(v)


def evaluate(law, values, local):
    y, f = law_parts(law, local)
    subs = {local[k]: num(v) for k, v in values.items() if k in local}
    return y, complex(sp.N(f.subs(subs), 30))


def close(a, b, rel=E2_REL_TOL, absol=E2_ABS_TOL):
    return abs(a - b) <= max(absol, rel * max(abs(a), abs(b)))


def passes_point(law, point, local):
    try:
        y, val = evaluate(law, point["inputs"], local)
        return abs(val - complex(sp.N(num(point["output"]), 30))) <= float(sp.N(num(point.get("tol", "1e-9"))))
    except Exception:
        return False


def symmetric(law, sym, world, local, rng):
    y, f = law_parts(law, local)
    inputs = sorted(s.name for s in f.free_symbols)
    ranges = world.get("ranges", {})
    for _ in range(E2_SAMPLES):
        vals = {}
        for q in inputs:
            lo, hi = ranges.get(q, [str(E2_DEFAULT_RANGE[0]), str(E2_DEFAULT_RANGE[1])])
            vals[q] = sp.Rational(rng.randint(0, 10 ** 6), 10 ** 6) * (num(lo) - num(hi)) * -1 + num(lo)
        pvals = {}
        for p, (lo, hi) in sym.get("params", {}).items():
            pvals[p] = sp.Rational(rng.randint(0, 10 ** 6), 10 ** 6) * (num(hi) - num(lo)) + num(lo)
        yv = f.subs({local[k]: v for k, v in vals.items()})
        old = dict(vals)
        old[y.name] = yv
        env = {local[k]: v for k, v in old.items()}
        env.update({sp.Symbol(k): v for k, v in pvals.items()})
        new = dict(old)
        for q, expr in sym["map"].items():
            new[q] = sp.sympify(expr, locals=local).subs(env)
        lhs = complex(sp.N(new[y.name], 30))
        rhs = complex(sp.N(f.subs({local[k]: new[k] for k in inputs}), 30))
        if not close(lhs, rhs):
            return False
    return True


def run_e2(world):
    qd = {q: {k: Fraction(str(v)) for k, v in d.items()} for q, d in world["quantities"].items()}
    local = {q: sp.Symbol(q) for q in qd}
    for sym in world.get("symmetries", []):
        for p in sym.get("params", {}):
            local.setdefault(p, sp.Symbol(p))
    orig, filled = world["law_original"], world["filled_law"]
    rng = random.Random(E2_SEED)
    notes = []
    try:
        fills = passes_point(filled, world["deficit"], local)
        if not fills:
            proc = "NOT_A_FILL"
        elif not dims_ok(filled, qd, local):
            proc = "INVALID"
        else:
            changed = []
            for k, pt in enumerate(world.get("validated", [])):
                if passes_point(orig, pt, local) and not passes_point(filled, pt, local):
                    changed.append("validated[%d]" % k)
            for sym in world.get("symmetries", []):
                if symmetric(orig, sym, world, local, rng) and not symmetric(filled, sym, world, local, rng):
                    changed.append("symmetry:%s" % sym.get("name", "?"))
            notes = changed
            if changed:
                proc = "ANOTHER_LAW"
            elif set(world.get("state_filled", [])) > set(world.get("state_original", [])):
                proc = "SAME_LAW_NEW_STATE"
            else:
                proc = "SAME_CARD"
    except Exception as ex:
        proc = "ERROR"
        notes = ["%s: %s" % (type(ex).__name__, ex)]
    c3 = "INVALID" if not dims_ok(filled, qd, local) else "SAME_LAW_NEW_STATE"
    return {"procedure": {"label": proc, "changed": notes},
            "C1": {"label": "SAME_LAW_NEW_STATE"},
            "C2": {"label": "ANOTHER_LAW"},
            "C3": {"label": c3}}


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
            if world.get("experiment") == "E1":
                results[wid] = run_e1(world)
            elif world.get("experiment") == "E2":
                results[wid] = run_e2(world)
            else:
                results[wid] = {"error": "unknown experiment"}
        except Exception as ex:
            results[wid] = {"error": "%s: %s" % (type(ex).__name__, ex)}
        print(wid, json.dumps(results[wid].get("procedure", results[wid]), ensure_ascii=False))
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=1, sort_keys=True)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "run":
        run_dir(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
