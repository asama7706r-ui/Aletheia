"""Aletheia blind test 4 -- independent reference, shared by score_v4.py and validate_v4.py.

It never imports the procedure. It uses the sealed reader (../lang/reader_v0.py) for the form of files and
for parsing expressions, and computes everything else with its own code:
  - actions from kinds, meaning cards (derived ones through the definitions) and bodies;
  - invariance (protocol 2.3) by expanding the numerator of the difference;
  - F1 by exact Gaussian elimination over Fractions;
  - F3, intervals and ranges by an exact two-phase simplex (Bland's rule);
  - the validity rules V1-V13 (V13: every element of the group the catalog generates),
    the reference card, verdict, baselines, zero-effect report, proof checks, traps and composition.
"""
import copy
import hashlib
import itertools
import json
import os
import re
import sys
from fractions import Fraction

import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "lang"))
import reader_v0 as RD  # noqa: E402

REGISTRY_PATH = os.path.join(ROOT, "registry", "registry.json")
U = "?"
LIMIT = 10 ** 9
NAME_RE = re.compile(r"^[a-z][a-z0-9]{1,5}$")
NUM_RE = re.compile(r"^(-?)([0-9]+)(?:/([0-9]+))?$")
VERDICTS = ("SAME_LAW_NEW_STATE", "ANOTHER_LAW", "INVALID", "CONDITIONAL")
BASELINES = ("FIX", "DERIVE", "DIMS", "FORK_ALL")
DIMS_EXP = {"rev_t": "T", "refl_x": "L", "conj_c": "Q"}
ZERO_LABELS = ("absent", "zero_for_any_value", "below_precision", "visible", "n/a")
# SHA-256 fingerprints of the dev worlds (law and sorted filled laws), from dev/make_dev_hashes.py.
# Dev tools set ALLOW_DEV = True to score the dev worlds themselves.
ALLOW_DEV = False
DEV_HASHES = {
    "04bb9f8c9a0e6dc865dc3eeb20b9d54ddbf391f4d450f1dda14a353c5f7950b9",
    "14400f1aa0afb48d2365c82de100964cd47e81f94eb05c0e00f02b7d09430990",
    "25d985d770a84ef22bff9cc086863ed53212fd1d2782be059e84def6469f9675",
    "33da87b710abeecd78c2e91c22520fe34c9b95d296a2973e707e07a417b8b8ca",
    "3d03dabc47f170cea185c3734a8c951cc857575ecdbaf708873cb1dbc0117fff",
    "521b298264658bcea359ec6bba4bf379bb083a648cba7150eacc4a2c0abe3728",
    "593b8b3a2a86c6f8cb006b0e419b7893465ee7c250499ca03d3960fbb5b60d96",
    "63fcb12cfdd891561f7b0d31ad040f0fd204e2bf1eaf04e5c47e48516a368f52",
    "70b62b95ee5882ed2b7c39e153217191609c1f72e753b6e0f9593376780a2d93",
    "73633e23103ecf7df2cf8024b92dae81849f0bf3d7f1c3e5bec1413ed01c58ec",
    "75cb26e4623cd203fbbd05a062a2a04e9ca194dd648ce091b8c884ca9862bcdd",
    "75e30706762884fd3c0c8337acddecdea02c3362059e91b47a351f3c8a58e176",
    "7d427df3dba12e2ec1da39a2496856b84163977ec30ceb38ea426cb4b2efd9ff",
    "82e24df72e48d998b404781577a8c7fa12581e873a1edc17aa37d71f016ec98a",
    "8526ee512490a224e588354dd68c2d10079ac14fc3df169017339f27a43e4515",
    "92be771d4cd1da1702369663d6cdc6da9ac8af52e0b8959cabf7062e8db9c5ba",
    "aa098181dc6459237bdcae693f994b37b544598523cde86b6222a8d2b9d2783c",
    "ac44678fb5f31c0416b0722c029222eed950cfab1bd429c9b7b55d0bb7e1bf50",
    "afca87ee418a4e5719c5c532fab657a691ce6670080577f0d1f028f23a3d6e97",
    "b53874a7096f062f68c15deedc9d6453633f7755a7a6348a1a207cdf03ab838c",
    "b60c64cd25599179d3da7fa228317118a81aa5b7fa31eebd797519f65f96ff25",
    "bea01b791cac67b4c5f570aad0edc195573e4ec47b49cf8af5bdd0e6908fa875",
    "d3dc94bf0fa14efc34818ff1ae877f917ea9dd0cac8706899dd2f55ecce69ec1",
    "e591f776b2a891b4a528568723344d3b52ad3b93ad5145f574f0d9d37420f042",
}


class Invalid(Exception):
    pass


def num(x, what="number", limit=True):
    if isinstance(x, bool) or not isinstance(x, (int, str)):
        raise Invalid(f"{what} must be an exact rational: {x!r}")
    m = NUM_RE.match(str(x).strip())
    if not m:
        raise Invalid(f"{what} is not an exact rational: {x!r}")
    p, q = int(m.group(2)), int(m.group(3) or 1)
    if q == 0:
        raise Invalid(f"{what} has a zero denominator")
    if limit and (p > LIMIT or q > LIMIT):
        raise Invalid(f"{what} exceeds 10^9 in numerator or denominator")
    v = Fraction(p, q)
    return -v if m.group(1) else v


def s(v):
    v = Fraction(v)
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def rat(v):
    v = Fraction(v)
    return sp.Rational(v.numerator, v.denominator)


def frac_of(e):
    e = sp.sympify(e)
    if not e.is_Rational:
        raise Invalid(f"internal: not a rational: {e}")
    return Fraction(int(e.p), int(e.q))


# ================================================================= exact simplex

def _pivot(T, basis, r, c):
    pv = T[r][c]
    T[r] = [x / pv for x in T[r]]
    for i in range(len(T)):
        if i != r and T[i][c] != 0:
            f = T[i][c]
            T[i] = [a - f * b for a, b in zip(T[i], T[r])]
    basis[r] = c


def _simplex(T, basis, cost, ncols):
    m = len(T)
    while True:
        inb = set(basis)
        entering = None
        for j in range(ncols):
            if j in inb:
                continue
            rj = cost[j] - sum(cost[basis[i]] * T[i][j] for i in range(m))
            if rj < 0:
                entering = j
                break
        if entering is None:
            return "optimal"
        leave, best = None, None
        for i in range(m):
            if T[i][entering] > 0:
                ratio = T[i][-1] / T[i][entering]
                if best is None or ratio < best or (ratio == best and basis[i] < basis[leave]):
                    best, leave = ratio, i
        if leave is None:
            return "unbounded"
        _pivot(T, basis, leave, entering)


def lp(A, b, c):
    """minimize c.x subject to A x <= b with x free. Returns (status, value, x)."""
    m, n = len(A), len(c)
    if n == 0:
        if all(bi >= 0 for bi in b):
            return "optimal", Fraction(0), []
        return "infeasible", None, None
    ncol = 2 * n + m
    arts = [i for i in range(m) if b[i] < 0]
    total = ncol + len(arts)
    T, basis = [], []
    for i in range(m):
        row = [Fraction(0)] * total
        for j in range(n):
            row[j], row[n + j] = Fraction(A[i][j]), -Fraction(A[i][j])
        row[2 * n + i] = Fraction(1)
        rhs = Fraction(b[i])
        if rhs < 0:
            row, rhs = [-x for x in row], -rhs
            col = ncol + arts.index(i)
            row[col] = Fraction(1)
            basis.append(col)
        else:
            basis.append(2 * n + i)
        T.append(row + [rhs])
    if arts:
        cost1 = [Fraction(0)] * ncol + [Fraction(1)] * len(arts)
        _simplex(T, basis, cost1, total)
        if sum(cost1[basis[i]] * T[i][-1] for i in range(m)) > 0:
            return "infeasible", None, None
        for i in range(m):
            if basis[i] >= ncol:
                col = next((j for j in range(ncol) if T[i][j] != 0), None)
                if col is not None:
                    _pivot(T, basis, i, col)
        keep = [i for i in range(m) if basis[i] < ncol]
        T = [T[i][:ncol] + [T[i][-1]] for i in keep]
        basis = [basis[i] for i in keep]
    cost2 = [Fraction(cj) for cj in c] + [-Fraction(cj) for cj in c] + [Fraction(0)] * m
    if _simplex(T, basis, cost2, ncol) == "unbounded":
        return "unbounded", None, None
    x = [Fraction(0)] * ncol
    for i, bj in enumerate(basis):
        x[bj] = T[i][-1]
    xs = [x[j] - x[n + j] for j in range(n)]
    return "optimal", sum(Fraction(cj) * xj for cj, xj in zip(c, xs)), xs


class System:
    """Rows (coef dict, rhs, tag) meaning sum coef[v]*v <= rhs."""

    def __init__(self, variables, rows):
        self.vars, self.rows = list(variables), rows

    def matrix(self):
        return [[r[0].get(v, Fraction(0)) for v in self.vars] for r in self.rows], [r[1] for r in self.rows]

    def feasible(self):
        A, b = self.matrix()
        return lp(A, b, [Fraction(0)] * len(self.vars))[0] != "infeasible"

    def optimum(self, c0, coef, sense):
        A, b = self.matrix()
        sign = 1 if sense == "min" else -1
        st, val, _ = lp(A, b, [sign * coef.get(v, Fraction(0)) for v in self.vars])
        if st == "infeasible":
            raise Invalid("internal: optimum of an infeasible system")
        if st == "unbounded":
            return None
        return c0 + sign * val

    def range(self, c0, coef):
        return self.optimum(c0, coef, "min"), self.optimum(c0, coef, "max")

    def check_point(self, point):
        if not isinstance(point, dict) or set(point) != set(self.vars):
            return False
        try:
            x = {v: num(point[v], "point", limit=False) for v in self.vars}
        except Invalid:
            return False
        return all(sum((c * x[v] for v, c in coef.items()), Fraction(0)) <= rhs for coef, rhs, _ in self.rows)

    def check_farkas(self, cert):
        if not isinstance(cert, list) or not cert:
            return False
        tm = {r[2]: r for r in self.rows}
        acc, rhs, seen = {v: Fraction(0) for v in self.vars}, Fraction(0), set()
        for e in cert:
            if not isinstance(e, dict) or set(e) != {"obs", "k", "side", "y"}:
                return False
            tag = (e["obs"], e["k"], e["side"])
            if tag not in tm or tag in seen:
                return False
            seen.add(tag)
            try:
                y = num(e["y"], "multiplier", limit=False)
            except Invalid:
                return False
            if y <= 0:
                return False
            coef, b, _ = tm[tag]
            for v, c in coef.items():
                acc[v] += y * c
            rhs += y * b
        return all(v == 0 for v in acc.values()) and rhs < 0


# ================================================================= registry

class Reg:
    def __init__(self, path=REGISTRY_PATH):
        with open(path, encoding="utf-8") as fh:
            self.raw = json.load(fh)
        ctx, info = RD.check_registry(self.raw, path)
        if ctx.errors:
            raise SystemExit("registry rejected: " + "; ".join(ctx.errors))
        self.info, self.sha = info, RD.sha256_of(info["canon"])
        self.dims = list(self.raw["dimensions"])
        self.reads = {t["id"]: t["reads"] for t in self.raw["transformations"]}
        self.kinds = {k["id"]: k for k in self.raw["kinds"]}
        self.meanings = {m["id"]: m for m in self.raw["meanings"]}
        self.units = {i["id"]: i["unit"] for i in self.raw["instruments"]}
        self.defs = {d["id"]: RD.Parser(d["eq"]).relation({"="}) for d in self.raw["definitions"]}
        self.ids = set(info["ids"]) | set(self.dims)
        self.catalog = self.raw["catalog"]

    def ksize(self, kind):
        n = 1
        for x in self.kinds[kind]["shape"]:
            n *= x
        return n

    def mat(self, v, n):
        if v == U:
            return None
        if isinstance(v, list):
            return sp.Matrix(n, n, lambda i, j: rat(num(v[i][j], "action", limit=False)))
        return rat(num(v, "action", limit=False)) * sp.eye(n)

    def maction(self, m, t):
        v = self.meanings[m]["under"][t]
        n = self.ksize(self.meanings[m]["kind"])
        if isinstance(v, dict):
            rel = self.defs[v["derived"]]
            return self._act(rel[3], t)
        return self.mat(v, n)

    def _act(self, node, t):
        k = node[0]
        if k == "num":
            return sp.Matrix([[1]])
        if k == "name":
            return self.maction(node[1], t)
        if k == "neg":
            return self._act(node[1], t)
        if k == "pow":
            a = self._act(node[1], t)
            return None if a is None else sp.Matrix([[a[0, 0] ** node[2]]])
        if k == "D":
            a, b = self.maction(node[1], t), self.maction(node[2], t)
            return None if a is None or b is None else a * (1 / b[0, 0])
        a, b = self._act(node[2], t), self._act(node[3], t)
        if a is None or b is None:
            return None
        if node[1] == "*":
            return a[0, 0] * b if a.shape == (1, 1) else b[0, 0] * a
        if node[1] == "/":
            return a * (1 / b[0, 0])
        return a

    def mdims(self, m):
        anchor = self.meanings[m]["anchor"]
        if "instrument" in anchor:
            return {k: Fraction(v) for k, v in self.units[anchor["instrument"]].items()}
        if "derived" in anchor:
            return self._dims(self.defs[anchor["derived"]][3])
        return None

    def _dims(self, node):
        k = node[0]
        if k == "num":
            return {}
        if k == "name":
            return self.mdims(node[1])
        if k == "neg":
            return self._dims(node[1])
        if k == "pow":
            a = self._dims(node[1])
            return None if a is None else {x: v * node[2] for x, v in a.items()}
        if k == "D":
            a, b = self.mdims(node[1]), self.mdims(node[2])
            return None if a is None or b is None else dsum(a, b, -1)
        a, b = self._dims(node[2]), self._dims(node[3])
        if a is None or b is None:
            return None
        if node[1] == "*":
            return dsum(a, b, 1)
        if node[1] == "/":
            return dsum(a, b, -1)
        return a

    def instrument(self, m):
        return self.meanings[m]["anchor"].get("instrument", U)


def dsum(a, b, sg):
    out = {k: Fraction(v) for k, v in a.items()}
    for k, v in b.items():
        out[k] = out.get(k, Fraction(0)) + sg * Fraction(v)
    return {k: v for k, v in out.items() if v != 0}


def dclean(d):
    return {k: Fraction(v) for k, v in d.items() if v != 0}


# ================================================================= world

class Q:
    def __init__(self, qid, meaning, kind, owner, dims, names, value, new, raw):
        self.id, self.meaning, self.kind, self.owner, self.dims = qid, meaning, kind, owner, dims
        self.names, self.value, self.new, self.raw = names, value, new, raw

    @property
    def n(self):
        return len(self.names)


def ast_expr(node, syms, limits=True):
    k = node[0]
    if k == "num":
        if limits and node[1] > LIMIT:
            raise Invalid("an integer in an expression exceeds 10^9")
        return sp.Integer(node[1])
    if k == "name":
        if node[1] not in syms:
            raise Invalid(f"unknown name {node[1]}")
        return syms[node[1]]
    if k == "neg":
        return -ast_expr(node[1], syms, limits)
    if k == "pow":
        if not -3 <= node[2] <= 3:
            raise Invalid("a power outside -3..3 (protocol section 3)")
        return ast_expr(node[1], syms, limits) ** node[2]
    if k == "D":
        raise Invalid("V2: D() in a law or a filler")
    a, b = ast_expr(node[2], syms, limits), ast_expr(node[3], syms, limits)
    if node[1] == "+":
        return a + b
    if node[1] == "-":
        return a - b
    if node[1] == "*":
        return a * b
    return a / b


class RFiller:
    pass


class RWorld:
    """A world checked against V1-V9 (V10-V13 need the reference card; see world_problems)."""

    def __init__(self, raw, reg):
        self.raw, self.reg = raw, reg
        if not isinstance(raw, dict):
            raise Invalid("V1: not a JSON object")
        ctx, canon = RD.check_world(raw, reg.info, "world")
        if ctx.errors:
            raise Invalid("V1: " + "; ".join(ctx.errors[:3]))
        if raw["registry_sha256"] != reg.sha:
            raise Invalid("V1: the world names another registry")
        self.canon = canon
        self._budgets_and_names()
        self.bodies = {b["id"]: b["type"] for b in raw["bodies"]}
        self.q, self.nq = {}, {}
        for x in raw["quantities"]:
            kind = reg.meanings[x["meaning"]]["kind"]
            names = x["components"] or [x["id"]]
            if x["value"] == U:
                raise Invalid("V6: a world quantity with value '?'")
            val = x["value"]
            if val != "var":
                val = [num(v, "value") for v in (val if isinstance(val, list) else [val])]
            md = reg.mdims(x["meaning"])
            if md is not None and dclean(md) != dclean(x["dims"]):
                raise Invalid(f"V6: dims of {x['id']} differ from its meaning's")
            qq = Q(x["id"], x["meaning"], kind, x["owner"], dclean(x["dims"]), names, val, False, x)
            self.q[x["id"]] = qq
            for i, nm in enumerate(names):
                self.nq[nm] = (qq, i)
        self.syms = {nm: sp.Symbol(nm) for nm in self.nq}
        # V2: the law
        if len(raw["laws"]) != 1:
            raise Invalid("V2: exactly one law")
        law = raw["laws"][0]
        self.law_id, self.acc = law["id"], law["accepted_at"]
        rel = RD.Parser(law["eq"]).relation({"="})
        if rel[2][0] != "name" or rel[2][1] not in self.nq:
            raise Invalid("V2: the law's left side must be one world name")
        self.y = rel[2][1]
        self.Y = self.syms[self.y]
        self.law_ast = rel[3]
        self.law = ast_expr(rel[3], self.syms)
        if self.Y in self.law.free_symbols:
            raise Invalid("V2: y on the law's right side")
        self.law_text = RD.render(rel)
        # fillers
        self.fillers = []
        for fr in raw["fillers"]:
            F = RFiller()
            F.id, F.raw = fr["id"], fr
            if fr["of"] != self.law_id:
                raise Invalid("V2: a filler of another law")
            frel = RD.Parser(fr["eq"]).relation({"="})
            if frel[2] != ("name", self.y):
                raise Invalid("V2: a filler with another left side")
            F.text = RD.render(frel)
            F.new = []
            F.nq = dict(self.nq)
            for x in fr["new"]:
                if x["owner"] == U:
                    raise Invalid("V3: a new quantity with an unknown owner")
                if x["old_value"] == U:
                    raise Invalid("V3: old_value '?'")
                names = [x["id"]] if x["kind"] == U else (x["components"] or [x["id"]])
                dims = None if x["dims"] == U else dclean(x["dims"])
                qq = Q(x["id"], x["meaning"], x["kind"], x["owner"], dims, names, x["value"], True, x)
                F.new.append(qq)
                for i, nm in enumerate(names):
                    F.nq[nm] = (qq, i)
            F.syms = {nm: sp.Symbol(nm) for nm in F.nq}
            F.expr = ast_expr(frel[3], F.syms)
            F.ast = frel[3]
            if self.Y in F.expr.free_symbols:
                raise Invalid("V2: y on a filler's right side")
            F.qall = list(self.q.values()) + F.new
            self._affine(F)
            self.fillers.append(F)
        self._bodies_rule()
        self._observations()
        cast = [t for t, r in reg.reads.items() if r == "cast"]
        self.cast = cast[0] if cast else None
        ids = sorted(self.bodies)
        self.pairs = [(a, b) for i, a in enumerate(ids) for b in ids[i + 1:] if self.bodies[a] == self.bodies[b]]
        self.catalog = [t for t in ("rev_t", "refl_x", "conj_c", "rot_z") if t in reg.reads] + \
            [f"{self.cast}({a},{b})" for a, b in self.pairs]
        self._law_dims()

    # ---- budgets and names (protocol section 3)
    def _budgets_and_names(self):
        r = self.raw
        nb = len(r["bodies"])
        types = [b["type"] for b in r["bodies"]]
        checks = [(0 <= nb <= 4, "at most 4 bodies"),
                  (all(types.count(t) <= 2 for t in types), "at most 2 bodies of one type"),
                  (2 <= len(r["quantities"]) <= 9, "2 to 9 world quantities"),
                  (len(r["relations"]) == 0, "no relations"),
                  (1 <= len(r["observers"]) <= 3, "1 to 3 observers"),
                  (len(r["fillers"]) in (1, 2, 3), "1 to 3 fillers")]
        for f in r["fillers"]:
            checks.append((len(f["new"]) <= 3, "at most 3 new quantities per filler"))
            checks.append((len(f["new_bodies"]) <= 2, "at most 2 new bodies per filler"))
        for ok, what in checks:
            if not ok:
                raise Invalid("budget: " + what)
        names = [r["id"]]
        for key in ("bodies", "quantities", "laws", "observers", "observations", "fillers"):
            for x in r[key]:
                names.append(x["id"])
        for x in r["quantities"]:
            names += x["components"]
        for f in r["fillers"]:
            for b in f["new_bodies"]:
                names.append(b["id"])
            for x in f["new"]:
                names.append(x["id"])
                if isinstance(x["components"], list):
                    names += x["components"]
        local = []
        for f in r["fillers"]:
            for b in f["new_bodies"]:
                local.append(b["id"])
            for x in f["new"]:
                local.append(x["id"])
                if isinstance(x["components"], list):
                    local += x["components"]
        for nm in names:
            if not NAME_RE.match(nm):
                raise Invalid(f"names: '{nm}' is not 2 to 6 lowercase letters and digits")
            if nm in self.reg.ids:
                raise Invalid(f"names: '{nm}' reuses a registry id")
        glob = [nm for nm in names if nm not in local]
        if len(set(glob)) != len(glob):
            raise Invalid("names: a name is used twice")
        # numbers
        for x in r["quantities"]:
            if x["value"] not in ("var", U):
                for v in (x["value"] if isinstance(x["value"], list) else [x["value"]]):
                    num(v, "value")
        for o in r["observers"]:
            num(o["precision"], "precision")
        for o in r["observations"]:
            num(o["value"], "observed value")
            for v in o["state"].values():
                num(v, "state value")
        for f in r["fillers"]:
            for x in f["new"]:
                ov = x["old_value"]
                if ov not in ("same", U):
                    for v in (ov if isinstance(ov, list) else [ov]):
                        num(v, "old value")

    def _affine(self, F):
        newsyms = [F.syms[nm] for q in F.new for nm in q.names]
        e = sp.together(F.expr)
        numer, den = sp.fraction(e)
        if den.free_symbols & set(newsyms):
            raise Invalid("V5: a new quantity in a denominator")
        if newsyms and sp.Poly(sp.expand(numer), *newsyms).total_degree() > 1:
            raise Invalid("V5: the filled law is not affine in its new quantities")
        present = sp.expand(numer).free_symbols
        for q in F.new:
            if not any(F.syms[nm] in present for nm in q.names):
                raise Invalid(f"V5: new quantity {q.id} vanishes after expansion")
        F.present = {z.name for z in F.expr.free_symbols}

    def _bodies_rule(self):
        world_types = set(self.bodies.values())
        for F in self.fillers:
            for b in F.raw["new_bodies"]:
                if b["type"] in world_types:
                    raise Invalid("V7: a new body has a type of a world body")
            seen = set()
            for q in F.qall:
                if q.owner in ("world",):
                    continue
                key = (q.owner, q.meaning)
                if key in seen:
                    raise Invalid("V7: a body owns two quantities of one meaning")
                seen.add(key)
            paired = {}
            ids = sorted(self.bodies)
            for i, a in enumerate(ids):
                for b in ids[i + 1:]:
                    if self.bodies[a] == self.bodies[b]:
                        paired[a], paired[b] = b, a
            for a, b in paired.items():
                ma = {q.meaning for q in self.q.values() if q.owner == a}
                mb = {q.meaning for q in self.q.values() if q.owner == b}
                if ma != mb:
                    raise Invalid("V7: two same-type bodies own different meanings")
            for q in F.new:
                if q.owner in paired:
                    if q.meaning == U:
                        raise Invalid("V7: a new quantity of meaning '?' on a paired body")
                    other = paired[q.owner]
                    if not any(p.owner == other and p.meaning == q.meaning for p in F.qall):
                        raise Invalid("V7: a new quantity without a partner on the other body")

    def _observations(self):
        r = self.raw
        self.prec = {o["id"]: num(o["precision"], "precision") for o in r["observers"]}
        self.old, self.newobs = [], []
        consts = {nm for q in self.q.values() if q.value != "var" for nm in q.names}
        need = set()
        for e in [self.law] + [F.expr for F in self.fillers]:
            for z in e.free_symbols:
                if z.name in self.nq and z.name != self.y and z.name not in consts:
                    need.add(z.name)
        for o in r["observations"]:
            if o["of"] != self.y:
                raise Invalid("V8: an observation not of y")
            st = {k: num(v, "state") for k, v in o["state"].items()}
            for k in st:
                if k not in self.nq or k == self.y:
                    raise Invalid("V8: a state names something that is not a world variable")
                if k in consts:
                    raise Invalid("V8: a state gives a value to a constant")
            if not need <= set(st):
                raise Invalid("V8: a state misses a variable of the law or a filler")
            rec = {"id": o["id"], "state": st, "v": num(o["value"], "value"), "d": self.prec[o["observer"]],
                   "observer": o["observer"]}
            (self.old if o["epoch"] <= self.acc else self.newobs).append(rec)
        if not 1 <= len(self.old) <= 6 or not 1 <= len(self.newobs) <= 4:
            raise Invalid("budget: 1 to 6 old and 1 to 4 new observations")
        self.consts = {nm: rat(v) for q in self.q.values() if q.value != "var" for nm, v in zip(q.names, q.value)}
        # the law at every observation
        deficit = False
        for dom, lst in (("old", self.old), ("new", self.newobs)):
            for o in lst:
                vals = dict(self.consts)
                vals.update({k: rat(v) for k, v in o["state"].items()})
                val = self.law.xreplace({self.syms[k]: v for k, v in vals.items()})
                if val.has(sp.zoo, sp.nan) or not val.is_Rational:
                    raise Invalid("V8: the law is undefined at an observation")
                off = abs(frac_of(val) - o["v"])
                if dom == "old" and off > o["d"]:
                    raise Invalid("V8: the law does not fit an old observation")
                if dom == "new" and off > o["d"]:
                    deficit = True
                for F in self.fillers:
                    fv = F.expr.xreplace({F.syms[k]: v for k, v in vals.items()})
                    if fv.has(sp.zoo, sp.nan):
                        raise Invalid("V8: a filler is undefined at an observation")
        if not deficit:
            raise Invalid("V8: no real deficit")

    def _law_dims(self):
        dl = self.q[self.nq[self.y][0].id].dims
        ok, _ = dims_solve(self.reg, self.law_ast, dl, lambda nm: self.nq[nm][0].dims, [])
        if not ok:
            raise Invalid("V6: the law is dimensionally inconsistent")


# ================================================================= F1: Gaussian elimination

def dims_solve(reg, ast, ydims, dims_of_name, unknown_qs):
    """Linear equations in the unknown exponents (one unknown per (quantity, base dimension)).
    dims_of_name(nm) returns a dict or ('u', qid). Returns (consistent, solution dict or None)."""
    D = reg.dims
    var_index = {}
    for qid in unknown_qs:
        for d in D:
            var_index[(qid, d)] = len(var_index)
    nv = len(var_index)
    eqs = []

    def vec_of(nm):
        x = dims_of_name(nm)
        out = {d: [Fraction(0)] * (nv + 1) for d in D}
        if isinstance(x, tuple):
            for d in D:
                out[d][var_index[(x[1], d)]] = Fraction(1)
        else:
            for d, v in x.items():
                out[d][nv] = Fraction(v)
        return out

    def walk(node):
        k = node[0]
        if k == "num":
            return {d: [Fraction(0)] * (nv + 1) for d in D}
        if k == "name":
            return vec_of(node[1])
        if k == "neg":
            return walk(node[1])
        if k == "pow":
            a = walk(node[1])
            return {d: [c * node[2] for c in a[d]] for d in D}
        a, b = walk(node[2]), walk(node[3])
        if node[1] == "*":
            return {d: [x + y for x, y in zip(a[d], b[d])] for d in D}
        if node[1] == "/":
            return {d: [x - y for x, y in zip(a[d], b[d])] for d in D}
        for d in D:
            eqs.append([x - y for x, y in zip(a[d], b[d])])
        return a

    rhs = walk(ast)
    for d in D:
        lhs = [Fraction(0)] * nv + [Fraction(ydims.get(d, 0))]
        eqs.append([x - y for x, y in zip(lhs, rhs[d])])
    # rows: sum a_i x_i + c = 0  ->  sum a_i x_i = -c
    M = [row[:nv] + [-row[nv]] for row in eqs]
    piv_cols, r = [], 0
    for c in range(nv):
        p = next((i for i in range(r, len(M)) if M[i][c] != 0), None)
        if p is None:
            continue
        M[r], M[p] = M[p], M[r]
        pv = M[r][c]
        M[r] = [x / pv for x in M[r]]
        for i in range(len(M)):
            if i != r and M[i][c] != 0:
                f = M[i][c]
                M[i] = [x - f * y for x, y in zip(M[i], M[r])]
        piv_cols.append(c)
        r += 1
    for i in range(r, len(M)):
        if M[i][nv] != 0:
            return False, None
    sol = {}
    for i, c in enumerate(piv_cols):
        if all(M[i][j] == 0 for j in range(nv) if j != c):
            sol[c] = M[i][nv]
    out = {}
    for qid in unknown_qs:
        cols = [var_index[(qid, d)] for d in D]
        if all(c in sol for c in cols):
            out[qid] = {d: sol[var_index[(qid, d)]] for d in D if sol[var_index[(qid, d)]] != 0}
        else:
            out[qid] = "undetermined"
    return True, out


def ref_f1(rw, F):
    reg = rw.reg
    unknown, fixed = [], {}
    contradiction = False
    for q in F.new:
        md = reg.mdims(q.meaning) if q.meaning != U else None
        if q.dims is not None:
            if md is not None and dclean(md) != q.dims:
                contradiction = True
            fixed[q.id] = q.dims
        elif md is not None:
            fixed[q.id] = dclean(md)
        else:
            unknown.append(q.id)
    if contradiction:
        return {"consistent": False, "inferred_dims": {}}

    def dims_of_name(nm):
        q = F.nq[nm][0]
        if not q.new:
            return q.dims
        return fixed[q.id] if q.id in fixed else ("u", q.id)
    ok, sol = dims_solve(reg, F.ast, rw.q[rw.nq[rw.y][0].id].dims, dims_of_name, unknown)
    if not ok:
        return {"consistent": False, "inferred_dims": {}}
    return {"consistent": True, "inferred_dims": sol}


def norm_dims(m):
    if not isinstance(m, dict):
        return None
    out = {}
    try:
        for k, v in m.items():
            out[k] = v if v == "undetermined" else {d: s(Fraction(x)) for d, x in v.items() if Fraction(x) != 0}
    except (TypeError, ValueError, AttributeError):
        return None
    return out


def dims_json(d):
    if d == "undetermined":
        return d
    return {k: (int(v) if Fraction(v).denominator == 1 else s(v)) for k, v in sorted(d.items())}


# ================================================================= actions and invariance

def sign(qid, t):
    return sp.Symbol(f"{qid}:{t}")


def raw_action(rw, q, t, mode, dims_of=None):
    """Action matrix (entries may be sign symbols); mode in procedure, FIX, DERIVE, DIMS, FORK_ALL."""
    reg, n = rw.reg, q.n
    if q.new and mode == "FIX":
        return sp.eye(n)
    if reg.reads[t] == "meaning":
        if mode == "DIMS":
            e = Fraction((dims_of(q) or {}).get(DIMS_EXP[t], 0))
            e = int(e) if e.denominator == 1 else 0
            return (-1) ** e * sp.eye(n)
        if q.new and mode in ("FORK_ALL", "DERIVE"):
            if n == 1:
                return sp.Matrix([[sign(q.id, t)]])
            return sp.diag(*[sign(f"{q.id}[{i}]", t) for i in range(n)])
        v = q.raw["under"][t] if q.new else reg.meanings[q.meaning]["under"][t]
        a = reg.maction(q.meaning, t) if isinstance(v, dict) else reg.mat(v, n)
    else:
        a = None if q.kind == U else reg.mat(reg.kinds[q.kind]["under"][t], n)
    if a is None:
        if n != 1:
            raise Invalid(f"V4: an unknown action on the multi-component quantity {q.id}")
        if mode == "FIX":
            return sp.eye(1)
        return sp.Matrix([[sign(q.id, t)]])
    return a


def gen_map(rw, F, t, mode, dims_of=None):
    """Image of every name (world and the filler's) under one catalog transformation."""
    syms = F.syms
    img = {}
    if t in rw.reg.reads:
        for q in F.qall:
            a = raw_action(rw, q, t, mode, dims_of)
            v = [syms[nm] for nm in q.names]
            for i, nm in enumerate(q.names):
                img[syms[nm]] = sp.expand(sum((a[i, j] * v[j] for j in range(q.n)), sp.Integer(0)))
        return img
    b1, b2 = t[t.index("(") + 1:-1].split(",")
    for q in F.qall:
        img.update({syms[nm]: syms[nm] for nm in q.names})
    for q in F.qall:
        if q.owner not in (b1, b2) or (mode == "FIX" and q.new):
            continue
        other = b2 if q.owner == b1 else b1
        p = next((x for x in F.qall if x.owner == other and x.meaning == q.meaning), None)
        if p is None:
            raise Invalid("V7: no exchange partner")
        if mode == "FIX" and p.new:
            continue
        for nm, pn in zip(q.names, p.names):
            img[syms[nm]] = syms[pn]
    return img


def unchanged(Y, f, img):
    """Protocol 2.3, by expanding the numerator."""
    d = (img.get(Y, Y) - f.xreplace(img)).xreplace({Y: f})
    numer, _ = sp.fraction(sp.together(d))
    return sp.expand(numer) == 0


def witness_ok(Y, f, img, point):
    if not isinstance(point, dict):
        return False
    try:
        vals = {sp.Symbol(k): rat(num(v, "point", limit=False)) for k, v in point.items()}
    except Invalid:
        return False
    d = (img.get(Y, Y) - f.xreplace(img)).xreplace({Y: f})
    need = (d.free_symbols | f.free_symbols) - {Y}
    if not need <= set(vals):
        return False
    fv, dv = f.xreplace(vals), d.xreplace(vals)
    if fv.has(sp.zoo, sp.nan, sp.oo) or dv.has(sp.zoo, sp.nan, sp.oo):
        return False
    return fv.is_Rational and dv.is_Rational and dv != 0


def unknowns_of(rw, F, t, mode, dims_of=None):
    m = gen_map(rw, F, t, mode, dims_of)
    used = rw.law.free_symbols | F.expr.free_symbols | {rw.Y}
    found = set()
    for z in used:
        if z in m:
            found |= {x for x in m[z].free_symbols if ":" in x.name}
    return sorted(found, key=lambda z: z.name), m


def f2_ref(rw, F, t, mode="procedure", dims_of=None):
    unk, m = unknowns_of(rw, F, t, mode, dims_of)
    rows = []
    for sg in itertools.product((1, -1), repeat=len(unk)):
        sub = dict(zip(unk, (sp.Integer(v) for v in sg)))
        mm = {k: v.xreplace(sub) for k, v in m.items()}
        old = unchanged(rw.Y, rw.law, mm)
        new = unchanged(rw.Y, F.expr, mm)
        rows.append((dict(zip((u.name for u in unk), sg)), old, new, mm))
    ch = [o != n for _, o, n, _ in rows]
    status = "no_change" if not any(ch) else "changed" if all(ch) else "conditional"
    res = {"status": status, "unknowns": [u.name for u in unk], "rows": rows, "changed": ch}
    if status == "conditional":
        res["keeping"] = [sg for (sg, _, _, _), c in zip(rows, ch) if not c]
        look = {tuple(sorted(sg.items())): c for (sg, _, _, _), c in zip(rows, ch)}
        res["matters"] = sorted(u.name for u in unk
                                if any(look[tuple(sorted(sg.items()))] !=
                                       look[tuple(sorted(dict(sg, **{u.name: -sg[u.name]}).items()))]
                                       for sg, _, _, _ in rows))
    return res


def verdict(f1r, f2r, f3holds):
    if not f1r["consistent"]:
        return "INVALID", [("F1", None)]
    reason = [] if f3holds else [("F3", None)]
    reason += [("F2", t) for t, r in f2r.items() if r["status"] == "changed"]
    if reason:
        return "ANOTHER_LAW", reason
    cond = [("F2", t) for t, r in f2r.items() if r["status"] == "conditional"]
    if cond:
        return "CONDITIONAL", cond
    return "SAME_LAW_NEW_STATE", []


# ================================================================= F3 and the zero-effect report

def obs_values(rw, F, o, dom, k):
    sub = {F.syms[nm]: v for nm, v in rw.consts.items()}
    sub.update({F.syms[nm]: rat(v) for nm, v in o["state"].items()})
    unk = []
    for q in F.new:
        if not any(nm in F.present for nm in q.names):
            continue
        if dom == "old":
            ov = q.raw["old_value"]
            if ov == "same":
                for nm in q.names:
                    if nm in F.present:
                        sub[F.syms[nm]] = sp.Symbol(nm)
                        unk.append(nm)
            else:
                vals = ov if isinstance(ov, list) else [ov] * q.n
                for nm, v in zip(q.names, vals):
                    sub[F.syms[nm]] = rat(num(v, "old value"))
        else:
            for nm in q.names:
                if nm in F.present:
                    u = nm if q.value == U else f"{nm}@{k}"
                    sub[F.syms[nm]] = sp.Symbol(u)
                    unk.append(u)
    return sub, unk


def affine(e, unk):
    """(K, coef) of an expression affine in the unknown names (exact)."""
    e = sp.expand(e)
    if e.has(sp.zoo, sp.nan):
        raise Invalid("V8: division by zero at a state")
    us = [sp.Symbol(u) for u in unk]
    K = sp.sympify(e.xreplace({u: sp.Integer(0) for u in us}))
    coef = {}
    for u in us:
        c = sp.diff(e, u)
        if c.free_symbols:
            raise Invalid("V5/V8: not affine, or a name without a value")
        if c != 0:
            coef[u.name] = frac_of(c)
    if K.free_symbols:
        raise Invalid("V8: a name without a value")
    return frac_of(K), coef


def f3_ref(rw, F, only_new=False):
    rows, cvars, vvars = [], [], []
    for dom, lst in (("old", rw.old), ("new", rw.newobs)):
        if only_new and dom == "old":
            continue
        for k, o in enumerate(lst):
            sub, unk = obs_values(rw, F, o, dom, k)
            K, a = affine(F.expr.xreplace(sub), unk)
            for u in unk:
                (vvars if "@" in u else cvars).append(u)
            rows.append((dict(a), o["v"] + o["d"] - K, (dom, k, "upper")))
            rows.append(({u: -c for u, c in a.items()}, -(o["v"] - o["d"] - K), (dom, k, "lower")))
    variables = sorted(set(cvars)) + sorted(set(vvars))
    return System(variables, rows)


def zero_ref(rw, F, system, holds):
    sub_abs = {}
    for q in F.new:
        ov = q.raw["old_value"]
        if ov != "same":
            vals = ov if isinstance(ov, list) else [ov] * q.n
            for nm, v in zip(q.names, vals):
                sub_abs[F.syms[nm]] = rat(num(v, "old value"))
    numer, _ = sp.fraction(sp.together(F.expr.xreplace(sub_abs) - rw.law))
    absent = sp.expand(numer) == 0
    out = []
    for k, o in enumerate(rw.old):
        if absent:
            out.append("absent")
            continue
        sub, unk = obs_values(rw, F, o, "old", k)
        K, a = affine((F.expr - rw.law).xreplace(sub), unk)
        if K == 0 and not a:
            out.append("zero_for_any_value")
        elif not holds:
            out.append("n/a")
        else:
            lo, hi = system.range(K, a)
            out.append("below_precision" if lo is not None and hi is not None and -o["d"] <= lo and hi <= o["d"]
                       else "visible")
    return out


# ================================================================= the reference card of one filler

def instrument_of(rw, F, u):
    qid = u.rsplit(":", 1)[0]
    q = next((x for x in F.new if x.id == qid), None)
    if q is not None:
        return q.raw["route"]
    return rw.reg.instrument(rw.q[qid].meaning)


def ref_card(rw, F):
    f1r = ref_f1(rw, F)
    f2r = {t: f2_ref(rw, F, t) for t in rw.catalog}
    sysm = f3_ref(rw, F)
    holds = sysm.feasible()
    v, reason = verdict(f1r, f2r, holds)
    card = {"verdict": v, "reason": reason, "F1": f1r, "F2": f2r, "F3": holds, "system": sysm,
            "zero": zero_ref(rw, F, sysm, holds)}
    card["instruments"] = {t: {u: instrument_of(rw, F, u) for u in r["matters"]}
                           for t, r in f2r.items() if r["status"] == "conditional"}

    def dims_of(q):
        if not q.new:
            return q.dims
        if q.dims is not None:
            return q.dims
        if q.meaning != U and rw.reg.mdims(q.meaning) is not None:
            return rw.reg.mdims(q.meaning)
        x = f1r["inferred_dims"].get(q.id) if f1r["consistent"] else None
        return x if isinstance(x, dict) else {}
    base = {}
    for mode in BASELINES:
        st = {}
        for t in rw.catalog:
            if mode == "DERIVE":
                r = f2_ref(rw, F, t, "DERIVE")
                st[t] = {"status": "changed" if r["status"] == "changed" else "no_change"}
            else:
                st[t] = f2_ref(rw, F, t, mode, dims_of)
        base[mode] = {"verdict": verdict(f1r, st, holds)[0], "F2": {t: r["status"] for t, r in st.items()}}
    card["baselines"] = base
    return card


# ================================================================= V13: products of transformations

def map_key(m):
    return tuple(sorted((k.name, sp.srepr(sp.expand(v))) for k, v in m.items()))


def compose(g, h):
    """first h, then g"""
    return {k: sp.expand(v.xreplace(g)) for k, v in h.items()}


def v13_ok(rw, F, card):
    """The reference answer does not change when every product of catalog transformations is checked."""
    unk = sorted({u for r in card["F2"].values() for u in r["unknowns"]})
    for sg in itertools.product((1, -1), repeat=len(unk)):
        assign = dict(zip(unk, sg))
        keep_cat = True
        old_all = True
        gens = []
        for t, r in card["F2"].items():
            sub = {sp.Symbol(u): sp.Integer(assign[u]) for u in r["unknowns"]}
            idx = tuple(assign[u] for u in r["unknowns"])
            row = next(x for x in r["rows"] if tuple(x[0][u] for u in r["unknowns"]) == idx)
            if row[1] != row[2]:
                keep_cat = False
            if not row[1]:
                old_all = False
            gm = {k: v.xreplace(sub) for k, v in gen_map(rw, F, t, "procedure").items()}
            rest = {z: sp.Integer(1) for v in gm.values() for z in v.free_symbols if ":" in z.name}
            gens.append({k: sp.expand(v.xreplace(rest)) for k, v in gm.items()})
        if not keep_cat or old_all:
            continue   # outside the keeping set, or the law keeps every generator (products add nothing)
        seen = {map_key(g): g for g in gens}
        frontier = list(gens)
        while frontier:
            nxt = []
            for a in frontier:
                for g in gens:
                    c = compose(g, a)
                    kk = map_key(c)
                    if kk not in seen:
                        seen[kk] = c
                        nxt.append(c)
            frontier = nxt
            if len(seen) > 4096:
                raise Invalid("V13: the generated group is too large")
        for m in seen.values():
            if unchanged(rw.Y, rw.law, m) != unchanged(rw.Y, F.expr, m):
                return False
    return True


# ================================================================= several fillers

def needed_state_names(rw, fillers):
    out = set()
    for F in fillers:
        for z in F.expr.free_symbols:
            nm = z.name
            if nm in rw.nq and nm != rw.y and rw.nq[nm][0].value == "var":
                out.add(nm)
    return out


def interval_at(rw, F, card, state):
    sub = {F.syms[nm]: v for nm, v in rw.consts.items()}
    sub.update({F.syms[k]: rat(v) for k, v in state.items()})
    unk = []
    for q in F.new:
        for nm in q.names:
            if nm in F.present:
                sub[F.syms[nm]] = sp.Symbol(nm)
                unk.append(nm)
    K, a = affine(F.expr.xreplace(sub), unk)
    return card["system"].range(K, a)


def decisive_ok(rw, Fs, cards, entry, check_intervals=True):
    """protocol 8.2: a decisive state for a pair of kept fillers."""
    try:
        a, b = entry["pair"]
        st = {k: num(v, "state", limit=False) for k, v in entry["state"].items()}
        obsv = entry["observer"]
    except (KeyError, TypeError, ValueError, Invalid, AttributeError):
        return False
    if obsv not in rw.prec or a not in Fs or b not in Fs:
        return False
    need = needed_state_names(rw, [Fs[a], Fs[b]])
    if not need <= set(st) or any(k not in rw.nq or rw.nq[k][0].value != "var" or k == rw.y for k in st):
        return False
    try:
        I, J = interval_at(rw, Fs[a], cards[a], st), interval_at(rw, Fs[b], cards[b], st)
    except Invalid:
        return False
    if None in I or None in J:
        return False
    if check_intervals:
        try:
            ci = entry["intervals"]
            if [num(x, "i", False) for x in ci[a]] != list(I) or [num(x, "i", False) for x in ci[b]] != list(J):
                return False
        except (KeyError, TypeError, Invalid):
            return False
    g = J[0] - I[1] if I[1] < J[0] else I[0] - J[1] if J[1] < I[0] else Fraction(0)
    return g > 2 * rw.prec[obsv]


# ================================================================= the reference of a world, and validity

def fingerprint(rw):
    txt = rw.law_text + "|" + "|".join(sorted(F.text for F in rw.fillers))
    return hashlib.sha256(txt.encode("utf-8")).hexdigest()


def reference(raw, reg):
    """Return (rw, cards) or raise Invalid (V1-V11, V13). Key agreement (V12) is checked separately."""
    rw = RWorld(raw, reg)
    cards = {}
    for F in rw.fillers:
        if not f3_ref(rw, F, only_new=True).feasible():
            raise Invalid(f"V8: filler {F.id} does not fit the new observations")
        c = ref_card(rw, F)
        if c["verdict"] != "INVALID":
            for qid, d in c["F1"]["inferred_dims"].items():
                if d == "undetermined" or any(Fraction(v).denominator != 1 for v in d.values()):
                    raise Invalid(f"V9: the dimensions of {qid} are not determined integers")
        if sum(len(r["unknowns"]) for r in c["F2"].values()) > 2:
            raise Invalid("V4: more than 2 unknown signs in a filler")
        c["group_agrees"] = c["verdict"] == "INVALID" or v13_ok(rw, F, c)
        if c["verdict"] in ("SAME_LAW_NEW_STATE", "CONDITIONAL") and not c["group_agrees"]:
            raise Invalid(f"V13: a product of transformations changes the answer for filler {F.id}")
        cards[F.id] = c
    if len(rw.fillers) >= 2:
        if any(c["verdict"] == "CONDITIONAL" for c in cards.values()):
            raise Invalid("V10: a CONDITIONAL filler in a several-filler world")
        kept = [fid for fid, c in cards.items() if c["verdict"] == "SAME_LAW_NEW_STATE"]
        if len(kept) < 2:
            raise Invalid("V10: fewer than 2 kept fillers")
        for fid in kept:
            F = next(x for x in rw.fillers if x.id == fid)
            if any(q.value != U for q in F.new):
                raise Invalid("V10: a kept filler with a variable new quantity")
            for v in cards[fid]["system"].vars:
                lo, hi = cards[fid]["system"].range(Fraction(0), {v: Fraction(1)})
                if lo is None or hi is None:
                    raise Invalid("V10: an unbounded feasible set")
    if not ALLOW_DEV and fingerprint(rw) in DEV_HASHES:
        raise Invalid("V11: the world reproduces a dev world")
    return rw, cards


def kept_of(cards):
    return sorted(fid for fid, c in cards.items() if c["verdict"] == "SAME_LAW_NEW_STATE")


# ================================================================= traps

AXIAL_MEANINGS = ("m18", "m19", "m20")


def law_quantities(rw, F):
    names = {z.name for z in rw.law.free_symbols | F.expr.free_symbols} | {rw.y}
    return {F.nq[nm][0].id: F.nq[nm][0] for nm in names}


def nonscalar_matrix(rw, F, t, q):
    if t not in rw.reg.reads or rw.reg.reads[t] == "cast":
        return False
    try:
        a = raw_action(rw, q, t, "procedure")
    except Invalid:
        return False
    if a is None or a.shape == (1, 1):
        return False
    return any(a[i, j] != (a[0, 0] if i == j else 0) for i in range(a.shape[0]) for j in range(a.shape[1]))


def traps_of(rw, F, c):
    """Which trap conditions of protocol section 6 this filler meets (a set of labels)."""
    out = set()
    v, base = c["verdict"], c["baselines"]
    newm = {q.meaning for q in F.new}
    rtrans = [t for it, t in c["reason"] if it == "F2"]
    meaning_t = [t for t in rtrans if rw.reg.reads.get(t) == "meaning"]
    if v == "SAME_LAW_NEW_STATE" and base["FIX"]["verdict"] == "ANOTHER_LAW":
        if "m04" in newm and base["FIX"]["F2"].get("conj_c") == "changed":
            out.add("T1")
        if "m18" in newm and base["FIX"]["F2"].get("rev_t") == "changed":
            out.add("T3")
        if "m22" in newm and base["FIX"]["F2"].get("refl_x") == "changed":
            out.add("T4")
    if v == "ANOTHER_LAW" and meaning_t and base["DERIVE"]["verdict"] == "SAME_LAW_NEW_STATE" \
            and base["DIMS"]["verdict"] == "SAME_LAW_NEW_STATE":
        out.add("T2")
        if "m06" in newm and "rev_t" in meaning_t:
            out.add("T2:m06")
    for t, r in c["F2"].items():
        if r["status"] == "changed" and all((not o) and n for _, o, n, _ in r["rows"]):
            out.add("T5")
    if v == "ANOTHER_LAW" and rtrans and len(rtrans) == len(c["reason"]) and \
            all(rw.reg.reads.get(t) is None for t in rtrans):
        out.add("T6")
    if v == "CONDITIONAL":
        out.add("T7")
        for t, r in c["F2"].items():
            for u in r.get("matters", []):
                qid = u.rsplit(":", 1)[0]
                if qid in rw.q:
                    out.add("T7:card")
                else:
                    q = next(x for x in F.new if x.id == qid)
                    if q.meaning == U:
                        out.add("T7:meaning")
    qs = law_quantities(rw, F)
    for t in rtrans:
        for q in qs.values():
            if nonscalar_matrix(rw, F, t, q):
                out.add("T8")
                if q.meaning == "m23" and t == "rev_t":
                    out.add("T8:m23")
                if q.meaning in AXIAL_MEANINGS and t == "refl_x":
                    out.add("T8:axial")
    return out


def decided_types(rw, c):
    out = set()
    for it, t in c["reason"]:
        if it == "F2":
            out.add(rw.reg.reads.get(t, "cast"))
    return out


# ================================================================= checking the procedure's output (8.1, 8.2)

def check_filler_output(rw, F, c, out):
    """Return a list of problems (empty = correct by protocol 8.1)."""
    p = []
    if not isinstance(out, dict) or "error" in out:
        return ["no output"]
    if out.get("verdict") != c["verdict"]:
        p.append("verdict")
    try:
        reason = sorted(((x["item"], x.get("transformation")) for x in out.get("reason", [])),
                        key=lambda z: (z[0], z[1] or ""))
    except (TypeError, KeyError, AttributeError):
        reason = None
    if reason != sorted(c["reason"], key=lambda z: (z[0], z[1] or "")):
        p.append("reason")
    f1o = out.get("F1") or {}
    if f1o.get("consistent") != c["F1"]["consistent"]:
        p.append("F1 status")
    elif norm_dims(f1o.get("inferred_dims")) != norm_dims(c["F1"]["inferred_dims"]):
        p.append("F1 dims")
    f2o = out.get("F2") or {}
    for t, r in c["F2"].items():
        o = f2o.get(t)
        if not isinstance(o, dict):
            p.append(f"F2 {t} missing")
            continue
        if o.get("status") != r["status"]:
            p.append(f"F2 {t} status")
            continue
        if sorted(o.get("unknowns", [])) != sorted(r["unknowns"]):
            p.append(f"F2 {t} unknowns")
            continue
        asg = o.get("assignments")
        if not isinstance(asg, list) or len(asg) != len(r["rows"]):
            p.append(f"F2 {t} assignments")
            continue
        byk = {tuple(sorted(sg.items())): (old, new, mm) for sg, old, new, mm in r["rows"]}
        seen = set()
        for a in asg:
            try:
                key = tuple(sorted(a["signs"].items()))
            except (KeyError, AttributeError, TypeError):
                p.append(f"F2 {t} proof")
                break
            if key not in byk or key in seen:
                p.append(f"F2 {t} proof")
                break
            seen.add(key)
            old, new, mm = byk[key]
            for which, refv, expr in (("old", old, rw.law), ("new", new, F.expr)):
                claim = a.get(which)
                if claim == "unchanged":
                    if not refv:
                        p.append(f"F2 {t} {which} claim")
                elif isinstance(claim, dict) and "point" in claim:
                    if refv or not witness_ok(rw.Y, expr, mm, claim["point"]):
                        p.append(f"F2 {t} {which} witness")
                else:
                    p.append(f"F2 {t} {which} proof missing")
        if r["status"] == "conditional":
            try:
                kp = sorted(tuple(sorted(x.items())) for x in o.get("keeping", []))
            except (AttributeError, TypeError):
                kp = None
            if kp != sorted(tuple(sorted(x.items())) for x in r["keeping"]):
                p.append(f"F2 {t} keeping")
            if sorted(o.get("matters", [])) != r["matters"]:
                p.append(f"F2 {t} matters")
    if set(f2o) != set(c["F2"]):
        p.append("F2 catalog")
    f3o = out.get("F3") or {}
    if f3o.get("holds") != c["F3"]:
        p.append("F3 status")
    elif c["F3"]:
        if not c["system"].check_point(f3o.get("point")):
            p.append("F3 point")
    elif not c["system"].check_farkas(f3o.get("farkas")):
        p.append("F3 farkas")
    if c["verdict"] == "CONDITIONAL":
        dec = out.get("decisive")
        got = {}
        if isinstance(dec, list):
            for e in dec:
                try:
                    got[e["transformation"]] = {m["unknown"]: m["instrument"] for m in e["measure"]}
                except (KeyError, TypeError):
                    pass
        if got != c["instruments"]:
            p.append("decisive")
    return p


def zero_agree(c, out):
    z = out.get("zero_report") if isinstance(out, dict) else None
    return isinstance(z, list) and z == c["zero"]


def load_registry():
    return Reg()


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def world_files(d):
    return sorted(f for f in os.listdir(d) if f.endswith(".json"))


def deepcopy(x):
    return copy.deepcopy(x)
