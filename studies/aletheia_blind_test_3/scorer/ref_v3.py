"""Aletheia blind test 3 -- independent reference, shared by score_v3.py and validate_v3.py.

It never imports the procedure. Expressions are parsed with Python's ast module and evaluated with
exact Fractions; linear systems are solved with an exact two-phase simplex (Bland's rule). It
implements: world validity (W1-W10), the reference answer of every world (verdict, sufficient set,
reason sets, intervals, ranges), proof checking (points and Farkas certificates), the composition
counts of protocol section 6, and the Part B reference (rules R1-R3, item validity and categories).
"""
import ast
import copy
import hashlib
import json
import re
from fractions import Fraction

import sympy as sp

REASONS = ("TYPE", "SYMMETRY", "SCOPE", "SHAPE", "BOUND")
RESERVED = set("re im ln pi oo li lam mu nan zoo sin cos tan cot sec csc exp log abs max min sqrt "
               "sign floor root beta gamma zeta erf".split())
NAME_RE = re.compile(r"^[a-z][a-z0-9]{1,5}$")
CAND_RE = re.compile(r"^R[1-9][0-9]*$")
NUM_RE = re.compile(r"^(-?)([0-9]+)(?:/([0-9]+))?$")
LIMIT = 10 ** 9
# SHA-256 of the canonical (base law, sorted candidate terms) of the dev worlds and the format example.
DEV_HASHES = {
    "095d89a5aa60633aa18f46aadbd4e96fb9a77ca09ee966d12c73c2885c39d66b",
    "4247524c53323f73f90660e04d31e31db9abb369f3277d905ccd0a5a9345cb53",
    "5345bdc868e026d0802cd4ffc9bebfd61d502418a2b93f63347de2f39edef084",
    "5aae192a9044e2c2bcc0e46ff7aa80b0ec48b9e4b647a0911dc4cd634d2df263",
    "6108a021f643c20091dfdd27961d14208084f3f11c048f5c745a1340b95dceba",
    "a48bb6416d9b008e32e7ea9683001de30c0bc6f00f0c92314bc9585f8feaf8d8",
    "a4ece2bb75c1af762150389596294f743de54a7a3ea7deb404448fddbd9ec9d0",
    "b1d90c44f227ca0c47b4c719ad564d8bc818e9da7196329f125b6c0beadca072",
    "be5b5ec574b2671374f16fb39539b80230b7b386ac80b30f597a099a2e384d6f",
    "bf24b2e6e6d01f99c20b231f62b6281aa60a3a8c928062173bb77e9ef4fd5dda",
    "d34a044c5872be33a0b31d908cf5f0a8898603b98696c2ced1a900be9adceba6"}


class Invalid(Exception):
    pass


# ================================================================= numbers

def num(x, what="number", limit=True):
    """Exact rational. limit=True enforces the 10^9 budget of protocol section 3 (world data only)."""
    if isinstance(x, bool) or not isinstance(x, (int, str)):
        raise Invalid("%s must be an exact rational written as an integer or a string 'p/q': %r" % (what, x))
    m = NUM_RE.match(str(x).strip())
    if not m:
        raise Invalid("%s is not an exact rational: %r" % (what, x))
    p, q = int(m.group(2)), int(m.group(3) or 1)
    if q == 0:
        raise Invalid("%s has a zero denominator" % what)
    if limit and (p > LIMIT or q > LIMIT):
        raise Invalid("%s exceeds 10^9 in numerator or denominator" % what)
    v = Fraction(p, q)
    return -v if m.group(1) else v


def s(v):
    if v is None:
        return None
    v = Fraction(v)
    return str(v.numerator) if v.denominator == 1 else "%d/%d" % (v.numerator, v.denominator)


def parse_interval(x):
    if not isinstance(x, list) or len(x) != 2:
        raise Invalid("interval must be a list [lo, hi]")
    return tuple(None if e is None else num(e, "interval end", limit=False) for e in x)


# ================================================================= expressions (ast)

class Expr:
    def __init__(self, src, names):
        if not isinstance(src, str):
            raise Invalid("expression must be a string")
        try:
            tree = ast.parse(src.strip(), mode="eval")
        except SyntaxError:
            raise Invalid("syntax error in %r" % src)
        self.src, self.node, self.names = src, tree.body, set()
        self._check(self.node, names)

    @staticmethod
    def _exponent(n):
        sign = 1
        while isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
            if isinstance(n.op, ast.USub):
                sign = -sign
            n = n.operand
        if isinstance(n, ast.Constant) and type(n.value) is int:
            return sign * n.value
        return None

    def _check(self, n, names):
        if isinstance(n, ast.BinOp):
            if not isinstance(n.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)):
                raise Invalid("operation not allowed in %r" % self.src)
            self._check(n.left, names)
            if isinstance(n.op, ast.Pow):
                k = self._exponent(n.right)
                if k is None or abs(k) > 3:
                    raise Invalid("powers must be integers from -3 to 3 in %r" % self.src)
            else:
                self._check(n.right, names)
        elif isinstance(n, ast.UnaryOp):
            if not isinstance(n.op, (ast.USub, ast.UAdd)):
                raise Invalid("operation not allowed in %r" % self.src)
            self._check(n.operand, names)
        elif isinstance(n, ast.Constant):
            if type(n.value) is not int:
                raise Invalid("only integer literals are allowed (write 1/2, never 0.5) in %r" % self.src)
            if abs(n.value) > LIMIT:
                raise Invalid("literal above 10^9 in %r" % self.src)
        elif isinstance(n, ast.Name):
            if n.id not in names:
                raise Invalid("undeclared name %s in %r" % (n.id, self.src))
            self.names.add(n.id)
        else:
            raise Invalid("syntax not allowed in %r" % self.src)

    def ev(self, env):
        return self._ev(self.node, env)

    def _ev(self, n, env):
        if isinstance(n, ast.BinOp):
            a = self._ev(n.left, env)
            if isinstance(n.op, ast.Pow):
                k = self._exponent(n.right)
                if a == 0 and k < 0:
                    raise Invalid("division by zero in %r" % self.src)
                return a ** k
            b = self._ev(n.right, env)
            if isinstance(n.op, ast.Add):
                return a + b
            if isinstance(n.op, ast.Sub):
                return a - b
            if isinstance(n.op, ast.Mult):
                return a * b
            if b == 0:
                raise Invalid("division by zero in %r" % self.src)
            return a / b
        if isinstance(n, ast.UnaryOp):
            v = self._ev(n.operand, env)
            return -v if isinstance(n.op, ast.USub) else v
        if isinstance(n, ast.Constant):
            return Fraction(n.value)
        return env[n.id]

    def dims(self, table):
        return self._dims(self.node, table)

    def _dims(self, n, table):
        if isinstance(n, ast.BinOp):
            a = self._dims(n.left, table)
            if isinstance(n.op, ast.Pow):
                k = self._exponent(n.right)
                return {u: v * k for u, v in a.items() if v * k != 0}
            b = self._dims(n.right, table)
            if isinstance(n.op, (ast.Add, ast.Sub)):
                if a != b:
                    raise Invalid("sum of different dimensions in %r" % self.src)
                return a
            sign = 1 if isinstance(n.op, ast.Mult) else -1
            r = dict(a)
            for u, v in b.items():
                r[u] = r.get(u, 0) + sign * v
            return {u: v for u, v in r.items() if v != 0}
        if isinstance(n, ast.UnaryOp):
            return self._dims(n.operand, table)
        if isinstance(n, ast.Constant):
            return {}
        return dict(table[n.id])

    def sym(self, smap):
        return self._sym(self.node, smap)

    def _sym(self, n, smap):
        if isinstance(n, ast.BinOp):
            a = self._sym(n.left, smap)
            if isinstance(n.op, ast.Pow):
                return a ** sp.Integer(self._exponent(n.right))
            b = self._sym(n.right, smap)
            return {ast.Add: lambda: a + b, ast.Sub: lambda: a - b, ast.Mult: lambda: a * b,
                    ast.Div: lambda: a / b}[type(n.op)]()
        if isinstance(n, ast.UnaryOp):
            v = self._sym(n.operand, smap)
            return -v if isinstance(n.op, ast.USub) else v
        if isinstance(n, ast.Constant):
            return sp.Integer(n.value)
        return smap[n.id]


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
    """Rows  sum(coef[v] * v) <= rhs  with tags (dom, k, side)."""

    def __init__(self, variables, rows):
        self.vars, self.rows = list(variables), rows

    def matrix(self):
        return ([[r[0].get(v, Fraction(0)) for v in self.vars] for r in self.rows], [r[1] for r in self.rows])

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

    def interval(self, var):
        return self.range(Fraction(0), {var: Fraction(1)})


# ================================================================= world loading (W1, W2)

def _dims_map(d, what):
    if not isinstance(d, dict):
        raise Invalid("%s dimensions must be a map" % what)
    out = {}
    for k, v in d.items():
        if not isinstance(k, str) or not k:
            raise Invalid("bad dimension name in %s" % what)
        val = num(v, "dimension exponent")
        if val != 0:
            out[k] = val
    return out


def _check_name(n, what):
    if not isinstance(n, str) or not NAME_RE.match(n) or n in RESERVED:
        raise Invalid("%s name %r is not allowed (2-6 lowercase letters/digits, starting with a letter, not reserved)" % (what, n))


class RWorld:
    def __init__(self, w):
        if not isinstance(w, dict) or w.get("experiment") != "A":
            raise Invalid("not a Part A world")
        req = ["id", "observable", "quantities", "observers", "base_law", "ledger", "old_observations",
               "new_observations", "possible_observations"]
        for k in req:
            if k not in w:
                raise Invalid("missing field %s" % k)
        allowed = set(req) | {"experiment", "constants", "visible", "symmetries"}
        extra = set(w) - allowed
        if extra:
            raise Invalid("unexpected fields %s" % sorted(extra))
        self.raw, self.id = w, w["id"]
        self.y = w["observable"]
        if not isinstance(w["quantities"], dict):
            raise Invalid("quantities must be a map")
        for q in w["quantities"]:
            _check_name(q, "quantity")
        if self.y not in w["quantities"]:
            raise Invalid("the observable must be a declared quantity")
        self.qd = {q: _dims_map(d, q) for q, d in w["quantities"].items()}
        self.state_q = sorted(q for q in self.qd if q != self.y)
        if not 1 <= len(self.state_q) <= 4:
            raise Invalid("1 to 4 state quantities are required")
        consts = w.get("constants") or {}
        if not isinstance(consts, dict) or len(consts) > 4:
            raise Invalid("at most 4 constants")
        self.cval, self.cd = {}, {}
        for c, spec in consts.items():
            _check_name(c, "constant")
            if not isinstance(spec, dict) or set(spec) - {"value", "dims"} or "value" not in spec:
                raise Invalid("constant %s must be {value, dims}" % c)
            self.cval[c] = num(spec["value"], "constant value")
            if self.cval[c] == 0:
                raise Invalid("constant %s must be nonzero" % c)
            self.cd[c] = _dims_map(spec.get("dims", {}), c)
        obs = w["observers"]
        if not isinstance(obs, dict) or not 1 <= len(obs) <= 3:
            raise Invalid("1 to 3 observers are required")
        self.prec = {}
        for o, p in obs.items():
            _check_name(o, "observer")
            self.prec[o] = num(p, "precision")
            if self.prec[o] < 0:
                raise Invalid("precision must be >= 0")
        led = w["ledger"]
        if not isinstance(led, list) or not 2 <= len(led) <= 5:
            raise Invalid("2 to 5 candidates are required")
        objects = set()
        for c in led:
            _check_name(c.get("object"), "object")
            objects.add(c["object"])
        vis = w.get("visible")
        if vis is not None:
            _check_name(vis.get("object"), "object")
            objects.add(vis["object"])
        names = list(self.qd) + list(self.cval) + list(self.prec)
        if len(set(names)) != len(names) or objects & set(names):
            raise Invalid("names of quantities, constants, observers and objects must be distinct")
        expr_names = set(self.state_q) | set(self.cval)
        self.table = dict(self.qd)
        self.table.update(self.cd)
        bl = w["base_law"]
        if not isinstance(bl, str) or bl.count("=") != 1:
            raise Invalid("base law must read  observable = expression")
        lhs, rhs = bl.split("=")
        if lhs.strip() != self.y:
            raise Invalid("base law must read  observable = expression")
        self.f = Expr(rhs, expr_names)
        if self.f.dims(self.table) != self.qd[self.y]:
            raise Invalid("base law has the wrong dimensions")
        self.vis = None
        if vis is not None:
            if not isinstance(vis, dict) or set(vis) != {"id", "object", "term"} or vis["id"] != "V1":
                raise Invalid("visible relation must be {id: V1, object, term}")
            self.vis = Expr(vis["term"], expr_names)
            self.vis.dims(self.table)
        self.cands, ids = [], set()
        for c in led:
            if not isinstance(c, dict) or set(c) - {"id", "object", "term", "coefficient", "coverage"}:
                raise Invalid("candidate fields must be id, object, term, coefficient, coverage")
            if not CAND_RE.match(str(c.get("id"))) or c["id"] in ids:
                raise Invalid("candidate ids must be unique R1, R2, ...")
            ids.add(c["id"])
            self.cands.append(self._cand(c, expr_names))
        syms = w.get("symmetries") or []
        if not isinstance(syms, list) or len(syms) > 2:
            raise Invalid("at most 2 symmetries")
        self.syms = []
        for sy in syms:
            if not isinstance(sy, dict) or "map" not in sy or not isinstance(sy["map"], dict):
                raise Invalid("symmetry must be {name, map}")
            mp = {}
            for q, e in sy["map"].items():
                if q not in self.qd:
                    raise Invalid("symmetry maps an undeclared quantity %s" % q)
                mp[q] = Expr(e, set(self.qd))
            self.syms.append((str(sy.get("name", "?")), mp))
        self.old = [self._obs(o, True) for o in self._list(w["old_observations"], 1, 6, "old observations")]
        self.new = [self._obs(o, True) for o in self._list(w["new_observations"], 1, 4, "new observations")]
        self.possible = [self._obs(o, False) for o in
                         self._list(w["possible_observations"], 2, 6, "possible observations")]
        self._w2()

    @staticmethod
    def _list(x, lo, hi, what):
        if not isinstance(x, list) or not lo <= len(x) <= hi:
            raise Invalid("%d to %d %s are required" % (lo, hi, what))
        return x

    def _cand(self, c, names):
        R = {"id": c["id"], "object": c["object"], "h": Expr(c["term"], names)}
        R["h"].dims(self.table)
        co = c.get("coefficient", "unknown")
        if co == "unknown":
            R["exact"] = None
        elif isinstance(co, dict) and set(co) == {"exact"}:
            R["exact"] = num(co["exact"], "exact coefficient")
        else:
            raise Invalid("coefficient must be \"unknown\" or {exact: value}")
        cov = c.get("coverage")
        R["cov"] = None
        if cov is not None:
            if not isinstance(cov, dict) or set(cov) - {"ratio", "factor", "summary"} or "ratio" not in cov \
                    or "factor" not in cov:
                raise Invalid("coverage must be {ratio, factor, summary?}")
            ratio = Expr(cov["ratio"], names)
            if ratio.dims(self.table):
                raise Invalid("coverage ratio of %s is not dimensionless" % c["id"])
            fac = cov["factor"]
            if not isinstance(fac, dict) or fac.get("type") not in ("dimmer", "switch"):
                raise Invalid("factor type must be dimmer or switch")
            if fac["type"] == "dimmer":
                if set(fac) != {"type", "expr"}:
                    raise Invalid("dimmer must be {type, expr}")
                R["cov"] = {"ratio": ratio, "type": "dimmer", "g": Expr(fac["expr"], {"r"})}
            else:
                if set(fac) != {"type", "on", "threshold"} or fac["on"] not in ("<", ">"):
                    raise Invalid("switch must be {type, on: < or >, threshold}")
                t = num(fac["threshold"], "threshold")
                if t <= 0:
                    raise Invalid("switch threshold must be positive")
                R["cov"] = {"ratio": ratio, "type": "switch", "on": fac["on"], "t": t}
        return R

    def _obs(self, o, reading):
        keys = {"state", "observer"} | ({"value"} if reading else set())
        if not isinstance(o, dict) or set(o) != keys:
            raise Invalid("observation fields must be %s" % sorted(keys))
        st = o["state"]
        if not isinstance(st, dict) or set(st) != set(self.state_q):
            raise Invalid("a state must give exactly the state quantities")
        if o["observer"] not in self.prec:
            raise Invalid("unknown observer %s" % o["observer"])
        return {"state": {q: num(st[q], "state value") for q in self.state_q},
                "value": num(o["value"], "reading") if reading else None,
                "observer": o["observer"], "d": self.prec[o["observer"]]}

    def env(self, state):
        e = dict(self.cval)
        e.update(state)
        return e

    def all_states(self):
        return [o["state"] for o in self.old + self.new + self.possible]

    def _w2(self):
        for st in self.all_states():
            env = self.env(st)
            self.f.ev(env)
            if self.vis is not None:
                self.vis.ev(env)
            for R in self.cands:
                R["h"].ev(env)
                if R["cov"] is not None:
                    rho = R["cov"]["ratio"].ev(env)
                    if R["cov"]["type"] == "dimmer":
                        g = R["cov"]["g"].ev({"r": rho})
                        if not 0 <= g <= 1:
                            raise Invalid("dimmer of %s leaves [0, 1] at a listed state" % R["id"])
                    elif rho == R["cov"]["t"]:
                        raise Invalid("a listed state sits on the switch threshold of %s" % R["id"])

    def factor(self, R, env, coverage=True):
        if not coverage or R["cov"] is None:
            return Fraction(1)
        rho = R["cov"]["ratio"].ev(env)
        if R["cov"]["type"] == "dimmer":
            return R["cov"]["g"].ev({"r": rho})
        if R["cov"]["on"] == "<":
            return Fraction(1) if rho < R["cov"]["t"] else Fraction(0)
        return Fraction(1) if rho > R["cov"]["t"] else Fraction(0)

    def cand(self, rid):
        return next(R for R in self.cands if R["id"] == rid)


# ================================================================= systems

class Opt:
    """Analysis options: coverage on/off, visible strength fixed."""

    def __init__(self, coverage=True, mu_fixed=None):
        self.coverage, self.mu_fixed = coverage, mu_fixed


def build(rw, R, mode, opt=None, only_old=False):
    """System Z, A, C or S for candidate R (rows tagged (dom, k, side))."""
    opt = opt or Opt()
    variables = []
    if rw.vis is not None and opt.mu_fixed is None:
        variables.append("mu")
    lam_free = R is not None and mode != "Z" and (R["exact"] is None or mode == "S")
    if lam_free:
        variables.append("lam")
    rows = []
    groups = [("old", rw.old)] if only_old else [("old", rw.old), ("new", rw.new)]
    for dom, lst in groups:
        for k, o in enumerate(lst):
            env = rw.env(o["state"])
            known = rw.f.ev(env)
            coef = {}
            if rw.vis is not None:
                hv = rw.vis.ev(env)
                if opt.mu_fixed is None:
                    coef["mu"] = hv
                else:
                    known += opt.mu_fixed * hv
            if R is not None and mode != "Z" and not (mode == "S" and dom == "old"):
                if mode in ("C", "S") and dom == "new":
                    fac = Fraction(1)
                else:
                    fac = rw.factor(R, env, opt.coverage)
                term = R["h"].ev(env) * fac
                if lam_free:
                    coef["lam"] = coef.get("lam", Fraction(0)) + term
                else:
                    known += R["exact"] * term
            up = o["value"] + o["d"] - known
            lo = o["value"] - o["d"] - known
            rows.append((dict(coef), up, (dom, k, "upper")))
            rows.append(({v: -c for v, c in coef.items()}, -lo, (dom, k, "lower")))
    return System(variables, rows)


def predicted(rw, R, state, opt=None):
    """Predicted y at a state with actual factors: (constant, coefficients)."""
    opt = opt or Opt()
    env = rw.env(state)
    c0, coef = rw.f.ev(env), {}
    if rw.vis is not None:
        if opt.mu_fixed is None:
            coef["mu"] = rw.vis.ev(env)
        else:
            c0 += opt.mu_fixed * rw.vis.ev(env)
    if R is not None:
        term = R["h"].ev(env) * rw.factor(R, env, opt.coverage)
        if R["exact"] is None:
            coef["lam"] = term
        else:
            c0 += R["exact"] * term
    return c0, coef


def joint_feasible(rw, cands):
    """W8: is there a combination of the given candidates (and mu) that fits every reading?"""
    exact = [R for R in cands if R["exact"] is not None]
    free = [R for R in cands if R["exact"] is None]
    for mask in range(1 << len(exact)):
        on = [exact[i] for i in range(len(exact)) if mask >> i & 1]
        variables = (["mu"] if rw.vis is not None else []) + ["l_" + R["id"] for R in free]
        rows = []
        for o in rw.old + rw.new:
            env = rw.env(o["state"])
            known = rw.f.ev(env) + sum((R["exact"] * R["h"].ev(env) * rw.factor(R, env) for R in on), Fraction(0))
            coef = {}
            if rw.vis is not None:
                coef["mu"] = rw.vis.ev(env)
            for R in free:
                coef["l_" + R["id"]] = R["h"].ev(env) * rw.factor(R, env)
            rows.append((dict(coef), o["value"] + o["d"] - known, None))
            rows.append(({v: -c for v, c in coef.items()}, -(o["value"] - o["d"] - known), None))
        if System(variables, rows).feasible():
            return True
    return False


# ================================================================= theory: TYPE and SYMMETRY

def _rank(M):
    M = [list(r) for r in M]
    rank, cols = 0, len(M[0]) if M else 0
    for c in range(cols):
        piv = next((i for i in range(rank, len(M)) if M[i][c] != 0), None)
        if piv is None:
            continue
        M[rank], M[piv] = M[piv], M[rank]
        for i in range(len(M)):
            if i != rank and M[i][c] != 0:
                f = M[i][c] / M[rank][c]
                M[i] = [a - f * b for a, b in zip(M[i], M[rank])]
        rank += 1
    return rank


def type_impossible(rw, h):
    need = dict(rw.qd[rw.y])
    for u, v in h.dims(rw.table).items():
        need[u] = need.get(u, 0) - v
    need = {u: v for u, v in need.items() if v != 0}
    if not need:
        return False
    consts = sorted(rw.cd)
    if not consts:
        return True
    units = sorted(set(need) | {u for d in rw.cd.values() for u in d})
    V = [[rw.cd[c].get(u, Fraction(0)) for c in consts] for u in units]
    Vt = [row + [need.get(u, Fraction(0))] for row, u in zip(V, units)]
    return _rank(V) != _rank(Vt)


def _sym_setup(rw):
    smap = {n: sp.Symbol(n) for n in list(rw.qd) + list(rw.cval)}
    out = []
    for name, mp in rw.syms:
        cy, sub = sp.Integer(1), {}
        for q, e in mp.items():
            se = e.sym(smap)
            fs = se.free_symbols
            if len(fs) != 1:
                raise Invalid("symmetry %s must send %s to a rational multiple of one quantity" % (name, q))
            q2 = next(iter(fs))
            ratio = sp.cancel(se / q2)
            if not ratio.is_Rational or ratio == 0:
                raise Invalid("symmetry %s must send %s to a rational multiple of a quantity" % (name, q))
            if q == rw.y:
                if q2.name != rw.y:
                    raise Invalid("symmetry %s must send the observable to a multiple of itself" % name)
                cy = ratio
            else:
                if q2.name == rw.y:
                    raise Invalid("symmetry %s sends a state quantity to the observable" % name)
                sub[smap[q]] = se
        out.append((name, cy, sub))
    return smap, out


def symmetry_check(rw):
    """W5, and the set of candidates forbidden by a declared symmetry."""
    smap, syms = _sym_setup(rw)
    f = rw.f.sym(smap)
    hv = rw.vis.sym(smap) if rw.vis is not None else sp.Integer(0)
    forbidden = set()
    for name, cy, sub in syms:
        if sp.cancel(cy * f - f.xreplace(sub)) != 0 or sp.cancel(cy * hv - hv.xreplace(sub)) != 0:
            raise Invalid("symmetry %s does not map the established law to itself" % name)
        for R in rw.cands:
            if R["cov"] is not None:
                rho = R["cov"]["ratio"].sym(smap)
                if sp.cancel(rho.xreplace(sub) - rho) != 0:
                    raise Invalid("symmetry %s changes the coverage ratio of %s" % (name, R["id"]))
            h = R["h"].sym(smap)
            if sp.cancel(cy * h - h.xreplace(sub)) != 0:
                forbidden.add(R["id"])
    return forbidden


# ================================================================= reference analysis

def answer_of(a):
    out = {"verdict": a["verdict"]}
    if a["verdict"] == "KNOWN":
        out["relation"] = a["relation"]
    if a["verdict"] == "FORK":
        out["branches"] = list(a["branches"])
    return out


def analyse(rw, opt=None, full=True):
    opt = opt or Opt()
    a = {"reasons": {}, "explanations": {}, "suff": [], "type": {}, "sym": set()}
    Z = build(rw, None, "Z", opt)
    if Z.feasible():
        a["verdict"] = "NO_DEFICIT"
        if full:
            a["explanations"]["BASE"] = _explanation(rw, None, Z, opt)
        return a
    forb = symmetry_check(rw)
    a["sym"] = forb
    for R in rw.cands:
        t = type_impossible(rw, R["h"])
        a["type"][R["id"]] = t
        A = build(rw, R, "A", opt)
        fa = A.feasible()
        if fa and not t and R["id"] not in forb:
            a["suff"].append(R["id"])
            if full:
                a["explanations"][R["id"]] = _explanation(rw, R, A, opt)
            continue
        rs = set()
        if t:
            rs.add("TYPE")
        if R["id"] in forb:
            rs.add("SYMMETRY")
        if not fa:
            fc = build(rw, R, "C", opt).feasible()
            fs = build(rw, R, "S", opt).feasible()
            if R["cov"] is not None and opt.coverage and fc:
                rs.add("SCOPE")
            if not fs:
                rs.add("SHAPE")
            if fs and not fc:
                rs.add("BOUND")
        a["reasons"][R["id"]] = rs
    if not a["suff"]:
        a["verdict"] = "NEW"
    elif len(a["suff"]) == 1:
        a["verdict"], a["relation"] = "KNOWN", a["suff"][0]
    else:
        a["verdict"], a["branches"] = "FORK", sorted(a["suff"])
    return a


def _explanation(rw, R, system, opt):
    e = {"intervals": {"lam": system.interval("lam") if "lam" in system.vars else None,
                       "mu": system.interval("mu") if "mu" in system.vars else None},
         "ranges": []}
    for p in rw.possible:
        c0, coef = predicted(rw, R, p["state"], opt)
        e["ranges"].append(system.range(c0, coef))
    return e


def gap(I, J):
    if None in I or None in J:
        return None
    return max(J[0] - I[1], I[0] - J[1])


def separable_pairs(rw, a):
    """For a FORK analysis: {pair: [possible indices that separate it]}."""
    br = a.get("branches", [])
    out = {}
    for i, x in enumerate(br):
        for y in br[i + 1:]:
            ks = []
            for k, p in enumerate(rw.possible):
                g = gap(a["explanations"][x]["ranges"][k], a["explanations"][y]["ranges"][k])
                if g is not None and g > 2 * p["d"]:
                    ks.append(k)
            out[(x, y)] = ks
    return out


def used(rw, verdict):
    consts = set(rw.f.names & set(rw.cval))
    if rw.vis is not None:
        consts |= rw.vis.names & set(rw.cval)
    if verdict != "NO_DEFICIT":
        for R in rw.cands:
            consts |= R["h"].names & set(rw.cval)
            if R["cov"] is not None:
                consts |= R["cov"]["ratio"].names & set(rw.cval)
    observers = {o["observer"] for o in rw.old + rw.new}
    if verdict == "FORK":
        observers |= {p["observer"] for p in rw.possible}
    return consts, observers


def m_old(rw):
    Zo = build(rw, None, "Z", only_old=True)
    if not Zo.feasible():
        return None
    return Zo.interval("mu")


# ================================================================= validity W3-W8, W10

def canonical_hash(raw):
    terms = sorted(str(c.get("term", "")).replace(" ", "") for c in raw.get("ledger", []))
    body = json.dumps({"base": str(raw.get("base_law", "")).replace(" ", ""), "terms": terms}, sort_keys=True)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def world_problems(rw, a):
    """W3-W8 and W10 for a loaded world with its reference analysis."""
    p = []
    try:
        symmetry_check(rw)
    except Invalid as ex:
        p.append("W5: %s" % ex)
    if rw.vis is not None:
        if type_impossible(rw, rw.vis):
            p.append("W3: the visible relation is dimensionally impossible")
        mi = m_old(rw)
        if mi is None:
            p.append("W3/W4: no visible strength fits the old observations")
        elif None in mi:
            p.append("W3: the visible strength is not bounded by the old observations")
        elif mi[0] <= 0 <= mi[1]:
            p.append("W3: the visible relation is not visible (0 fits the old observations)")
    elif not build(rw, None, "Z", only_old=True).feasible():
        p.append("W4: the base law misses an old observation beyond its precision")
    allobs = rw.old + rw.new
    for i, x in enumerate(allobs):
        for y in allobs[i + 1:]:
            if x["state"] == y["state"] and (x["value"] + x["d"] < y["value"] - y["d"]
                                             or y["value"] + y["d"] < x["value"] - x["d"]):
                p.append("W4: two readings at the same state contradict each other")
    answer_ids = set(a.get("suff", []))
    if not any(not type_impossible(rw, R["h"]) and R["id"] not in answer_ids for R in rw.cands):
        p.append("W6: no distractor with the right dimensions")
    if len(a.get("suff", [])) > 3:
        p.append("W7: more than three sufficient candidates")
    if a["verdict"] == "FORK":
        for pair, ks in separable_pairs(rw, a).items():
            if not ks:
                p.append("W7: branches %s and %s are not decisively separable" % pair)
    for key, e in a["explanations"].items():
        for v in ("lam", "mu"):
            iv = e["intervals"].get(v)
            if iv is not None and None in iv:
                p.append("W7: unbounded %s for %s" % (v, key))
    if a["verdict"] == "NEW":
        cands = [R for R in rw.cands if not a["type"].get(R["id"]) and R["id"] not in a["sym"]]
        if joint_feasible(rw, cands):
            p.append("W8: a combination of candidates explains the observations")
    if canonical_hash(rw.raw) in DEV_HASHES:
        p.append("W10: the world reproduces a dev world")
    return p


def load_and_check(raw):
    """(RWorld, analysis, problems). Raises nothing: problems collect every failure."""
    try:
        rw = RWorld(raw)
        a = analyse(rw)
    except Invalid as ex:
        return None, None, [str(ex)]
    except Exception as ex:  # pragma: no cover
        return None, None, ["error: %s: %s" % (type(ex).__name__, ex)]
    try:
        return rw, a, world_problems(rw, a)
    except Invalid as ex:
        return rw, a, [str(ex)]


def cross_world_problems(worlds):
    """W9 over all raw worlds: {world id: [problems]}."""
    p = {}
    shared_keys = ("quantities", "constants", "base_law", "visible", "ledger", "symmetries", "observers",
                   "old_observations")
    by_obs = {}
    for wid, w in worlds.items():
        by_obs.setdefault(w.get("observable"), []).append(wid)
    for obs, ids in by_obs.items():
        ref = worlds[ids[0]]
        for wid in ids[1:]:
            for k in shared_keys:
                if json.dumps(worlds[wid].get(k), sort_keys=True) != json.dumps(ref.get(k), sort_keys=True):
                    p.setdefault(wid, []).append("W9: shares observable %s with %s but differs in %s" % (obs, ids[0], k))
            if json.dumps(worlds[wid].get("new_observations"), sort_keys=True) == \
                    json.dumps(ref.get("new_observations"), sort_keys=True):
                p.setdefault(wid, []).append("diversity: same new observations as %s" % ids[0])
    seen_c, seen_o = {}, {}
    for wid, w in sorted(worlds.items()):
        for c, spec in (w.get("constants") or {}).items():
            key = json.dumps(spec, sort_keys=True)
            if c in seen_c and seen_c[c][1] != key:
                p.setdefault(wid, []).append("W9: constant %s differs from world %s" % (c, seen_c[c][0]))
            seen_c.setdefault(c, (wid, key))
        for o, prec in (w.get("observers") or {}).items():
            if o in seen_o and str(seen_o[o][1]) != str(prec):
                p.setdefault(wid, []).append("W9: observer %s differs from world %s" % (o, seen_o[o][0]))
            seen_o.setdefault(o, (wid, prec))
    return p


# ================================================================= proof checking

def _tagmap(system):
    return {r[2]: r for r in system.rows}


def check_point(system, point):
    if not isinstance(point, dict) or set(point) != set(system.vars):
        return False
    try:
        x = {v: num(point[v], "point", limit=False) for v in system.vars}
    except Invalid:
        return False
    return all(sum((c * x[v] for v, c in coef.items()), Fraction(0)) <= rhs for coef, rhs, _ in system.rows)


def check_farkas(system, cert):
    if not isinstance(cert, list) or not cert:
        return False
    tm = _tagmap(system)
    acc, rhs, seen = {v: Fraction(0) for v in system.vars}, Fraction(0), set()
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


def interval_equal(claimed, ref):
    try:
        c = parse_interval(claimed)
    except Invalid:
        return False
    return c == tuple(ref)


def check_world_output(rw, a, out):
    """Proof-checked correctness of a procedure output against the reference analysis.
    Returns (correct, problems, listed reasons {cand: set})."""
    probs, listed = [], {}
    if not isinstance(out, dict) or out.get("verdict") != a["verdict"]:
        return False, ["verdict %s, reference %s" % (out.get("verdict") if isinstance(out, dict) else None,
                                                     a["verdict"])], listed
    v = a["verdict"]
    if v == "KNOWN" and out.get("relation") != a["relation"]:
        probs.append("relation %s, reference %s" % (out.get("relation"), a["relation"]))
    if v == "FORK" and sorted(out.get("branches") or []) != a["branches"]:
        probs.append("branches %s, reference %s" % (out.get("branches"), a["branches"]))
    if probs:
        return False, probs, listed
    step0 = out.get("step0") or {}
    Z = build(rw, None, "Z")
    if v == "NO_DEFICIT":
        if step0.get("deficit") is not False or not check_point(Z, step0.get("certificate")):
            probs.append("step 0: invalid point certificate")
    elif step0.get("deficit") is not True or not check_farkas(Z, step0.get("certificate")):
        probs.append("step 0: invalid Farkas certificate")
    exps = out.get("explanations") or {}
    keys = ["BASE"] if v == "NO_DEFICIT" else a["suff"]
    for key in keys:
        e = exps.get(key)
        ref = a["explanations"][key]
        if not isinstance(e, dict):
            probs.append("missing explanation for %s" % key)
            continue
        R = None if key == "BASE" else rw.cand(key)
        system = build(rw, R, "Z" if R is None else "A")
        if not check_point(system, e.get("point")):
            probs.append("invalid point for %s" % key)
        iv = e.get("intervals") or {}
        for var in ("lam", "mu"):
            if ref["intervals"][var] is None:
                if iv.get(var) is not None:
                    probs.append("interval %s given for %s but the unknown is absent" % (var, key))
            elif not interval_equal(iv.get(var), ref["intervals"][var]):
                probs.append("wrong %s interval for %s" % (var, key))
        rg = e.get("ranges")
        if not isinstance(rg, list) or len(rg) != len(ref["ranges"]) or \
                not all(interval_equal(x, y) for x, y in zip(rg, ref["ranges"])):
            probs.append("wrong ranges (quarantine note) for %s" % key)
    if v == "FORK":
        dec = out.get("decisive")
        sep = separable_pairs(rw, a)
        if not isinstance(dec, list) or not all(isinstance(k, int) and 0 <= k < len(rw.possible) for k in dec):
            probs.append("invalid decisive set")
        else:
            for pair, ks in sep.items():
                if not set(ks) & set(dec):
                    probs.append("decisive set does not separate %s and %s" % pair)
    if v != "NO_DEFICIT":
        ex = out.get("excluded") or {}
        for R in rw.cands:
            if R["id"] in a["suff"]:
                continue
            entry = ex.get(R["id"])
            if not isinstance(entry, dict) or not isinstance(entry.get("reasons"), list):
                probs.append("no reasons for %s" % R["id"])
                continue
            rs = [x for x in entry["reasons"] if x in REASONS]
            listed[R["id"]] = set(rs)
            if not rs or len(rs) != len(entry["reasons"]):
                probs.append("no valid reason list for %s" % R["id"])
            certs = entry.get("certificates") or {}
            for reason in rs:
                if reason not in a["reasons"][R["id"]]:
                    probs.append("false reason %s for %s" % (reason, R["id"]))
                    continue
                c = certs.get(reason) or {}
                if reason == "SCOPE" and not (check_farkas(build(rw, R, "A"), c.get("A"))
                                              and check_point(build(rw, R, "C"), c.get("C"))):
                    probs.append("invalid SCOPE certificate for %s" % R["id"])
                if reason == "SHAPE" and not check_farkas(build(rw, R, "S"), c.get("S")):
                    probs.append("invalid SHAPE certificate for %s" % R["id"])
                if reason == "BOUND" and not (check_point(build(rw, R, "S"), c.get("S"))
                                              and check_farkas(build(rw, R, "C"), c.get("C"))):
                    probs.append("invalid BOUND certificate for %s" % R["id"])
    return not probs, probs, listed


# ================================================================= composition (protocol section 6)

def composition(valid):
    """valid: {wid: (rw, analysis)}. Returns counts and the list of unmet requirements."""
    c = {"verdicts": {"KNOWN": 0, "NEW": 0, "FORK": 0, "NO_DEFICIT": 0}, "scope_sensitive": [],
         "nebulium_dimmer": [], "nebulium_switch": [], "sole": {r: [] for r in REASONS},
         "visible_matters": [], "fork3": [], "planet_x": [], "shared_observable_with_nd": []}
    by_obs = {}
    for wid, (rw, a) in sorted(valid.items()):
        c["verdicts"][a["verdict"]] += 1
        by_obs.setdefault(rw.y, []).append(a["verdict"])
        ns = answer_of(analyse(rw, Opt(coverage=False), full=False))
        sens = ns != answer_of(a)
        if sens:
            c["scope_sensitive"].append(wid)
        if sens and a["verdict"] == "KNOWN":
            R = rw.cand(a["relation"])
            if R["cov"] is not None:
                c["nebulium_" + R["cov"]["type"]].append(wid)
        if a["verdict"] == "NEW":
            for rid, rs in a["reasons"].items():
                if len(rs) == 1:
                    c["sole"][next(iter(rs))].append("%s:%s" % (wid, rid))
        if rw.vis is not None:
            mi = m_old(rw)
            if mi is not None and None not in mi:
                fixed = answer_of(analyse(rw, Opt(mu_fixed=(mi[0] + mi[1]) / 2), full=False))
                if fixed != answer_of(a):
                    c["visible_matters"].append(wid)
        if a["verdict"] == "FORK" and len(a["branches"]) == 3:
            c["fork3"].append(wid)
        if a["verdict"] == "NO_DEFICIT":
            forb = symmetry_check(rw)
            for R in rw.cands:
                if not type_impossible(rw, R["h"]) and R["id"] not in forb and build(rw, R, "A").feasible():
                    c["planet_x"].append("%s:%s" % (wid, R["id"]))
                    break
    for obs, vs in by_obs.items():
        if len(vs) >= 3 and "NO_DEFICIT" in vs:
            c["shared_observable_with_nd"].append(obs)
    sens = set(c["scope_sensitive"])
    newsens = [w for w in sens if valid[w][1]["verdict"] == "NEW"]
    forksens = [w for w in sens if valid[w][1]["verdict"] == "FORK"]
    need = []
    for k, n in (("KNOWN", 9), ("NEW", 9), ("FORK", 6), ("NO_DEFICIT", 3)):
        if c["verdicts"][k] != n:
            need.append("%s worlds: %d, required %d" % (k, c["verdicts"][k], n))
    if len(sens) < 8:
        need.append("scope-sensitive worlds: %d, required >= 8" % len(sens))
    if len(c["nebulium_dimmer"]) + len(c["nebulium_switch"]) < 5:
        need.append("nebulium-type KNOWN worlds: %d, required >= 5"
                    % (len(c["nebulium_dimmer"]) + len(c["nebulium_switch"])))
    if len(c["nebulium_dimmer"]) < 3:
        need.append("nebulium-type with a dimmer: %d, required >= 3" % len(c["nebulium_dimmer"]))
    if len(c["nebulium_switch"]) < 2:
        need.append("nebulium-type with a switch: %d, required >= 2" % len(c["nebulium_switch"]))
    if len(newsens) < 2:
        need.append("scope-sensitive NEW worlds: %d, required >= 2" % len(newsens))
    if len(forksens) < 1:
        need.append("scope-sensitive FORK worlds: %d, required >= 1" % len(forksens))
    for r in REASONS:
        if not c["sole"][r]:
            need.append("no NEW-world candidate with %s as its only reason" % r)
    if len(c["visible_matters"]) < 3:
        need.append("worlds where the visible relation matters: %d, required >= 3" % len(c["visible_matters"]))
    if not c["fork3"]:
        need.append("no FORK with three branches")
    if not c["planet_x"]:
        need.append("no NO_DEFICIT world with a planet-X trap")
    if not c["shared_observable_with_nd"]:
        need.append("no observable shared by three worlds including a NO_DEFICIT one")
    c["scope_sensitive_new"], c["scope_sensitive_fork"] = sorted(newsens), sorted(forksens)
    return c, need


# ================================================================= Part B reference

ITEM_TYPES = {"obs_flip": "observation", "obs_inside": "observation", "obs_fork": "observation",
              "rel_new_known": "relation", "rel_known_fork": "relation", "rel_unchanged": "relation",
              "rel_none": "relation", "root_vanish": "root", "root_revive": "root", "root_unchanged": "root",
              "root_none": "root"}
ITEM_COUNTS = {"obs_flip": 2, "obs_inside": 2, "obs_fork": 2, "rel_new_known": 2, "rel_known_fork": 2,
               "rel_unchanged": 2, "rel_none": 2, "root_vanish": 1, "root_revive": 1, "root_unchanged": 1,
               "root_none": 1}


def apply_item(raw, item):
    w = copy.deepcopy(raw)
    t = item["type"]
    changed = False
    if t == "observation" and w["id"] == item["world"]:
        w["new_observations"].append({"state": item["state"], "value": item["value"], "observer": item["observer"]})
        changed = True
    elif t == "relation" and w["observable"] == item["observable"]:
        w["ledger"].append(copy.deepcopy(item["relation"]))
        changed = True
    elif t == "root":
        if "constant" in item and item["constant"] in (w.get("constants") or {}):
            w["constants"][item["constant"]]["value"] = item["new_value"]
            changed = True
        if "observer" in item and item["observer"] in w["observers"]:
            w["observers"][item["observer"]] = item["new_precision"]
            changed = True
    return w, changed


def _item_format(item, worlds):
    if not isinstance(item, dict) or item.get("experiment") != "B":
        raise Invalid("not a Part B item")
    t = item.get("type")
    if t == "observation":
        if set(item) != {"id", "experiment", "type", "world", "state", "observer", "value"}:
            raise Invalid("observation item fields")
        if item["world"] not in worlds:
            raise Invalid("unknown world %s" % item["world"])
        num(item["value"], "reading")
    elif t == "relation":
        if set(item) - {"id", "experiment", "type", "observable", "relation", "observable_dims"} or \
                not {"id", "experiment", "type", "observable", "relation"} <= set(item):
            raise Invalid("relation item fields")
        objects = {c.get("object") for w in worlds.values() for c in w.get("ledger", [])}
        if item["relation"].get("object") not in objects:
            raise Invalid("the new relation's object is not a known object")
        users = [w for w in worlds.values() if w["observable"] == item["observable"]]
        if users:
            if item["relation"].get("id") in {c["id"] for c in users[0]["ledger"]}:
                raise Invalid("the new relation's id already exists in that ledger")
        elif "observable_dims" not in item:
            raise Invalid("an observable no world uses needs observable_dims")
        else:
            _check_name(item["observable"], "observable")
            _dims_map(item["observable_dims"], "observable")
            if not CAND_RE.match(str(item["relation"].get("id"))):
                raise Invalid("candidate id")
    elif t == "root":
        keys = set(item) - {"id", "experiment", "type"}
        if keys == {"constant", "new_value"}:
            if not any(item["constant"] in (w.get("constants") or {}) for w in worlds.values()):
                raise Invalid("the constant appears in no world")
            if num(item["new_value"], "new value") == 0:
                raise Invalid("constant values must be nonzero")
        elif keys == {"observer", "new_precision"}:
            if not any(item["observer"] in w["observers"] for w in worlds.values()):
                raise Invalid("the observer appears in no world")
            if num(item["new_precision"], "new precision") < 0:
                raise Invalid("precision must be >= 0")
        else:
            raise Invalid("root item must give constant/new_value or observer/new_precision")
    else:
        raise Invalid("unknown item type %r" % t)


def ref_reopen(item, worlds, ref):
    """Rules R1-R3 on the reference Part A answers. ref: {wid: (rw, analysis)}."""
    t = item["type"]
    if t == "observation":
        wid = item["world"]
        rw, a = ref[wid]
        if a["verdict"] == "NEW":
            return []
        st = {q: num(item["state"][q], "state value") for q in rw.state_q} \
            if isinstance(item["state"], dict) and set(item["state"]) == set(rw.state_q) else None
        if st is None:
            raise Invalid("the reading's state must give exactly the state quantities")
        idx = next((k for k, p in enumerate(rw.possible) if p["state"] == st and p["observer"] == item["observer"]),
                   None)
        if idx is None:
            raise Invalid("the reading is not at a listed possible state with that observer")
        d = rw.prec[item["observer"]]
        v = num(item["value"], "reading")
        keys = ["BASE"] if a["verdict"] == "NO_DEFICIT" else a["suff"]
        for key in keys:
            lo, hi = a["explanations"][key]["ranges"][idx]
            if (hi is not None and v - d > hi) or (lo is not None and v + d < lo):
                return [wid]
        return []
    if t == "relation":
        return sorted(wid for wid, (rw, a) in ref.items()
                      if rw.y == item["observable"] and a["verdict"] != "NO_DEFICIT")
    out = []
    for wid, (rw, a) in ref.items():
        consts, observers = used(rw, a["verdict"])
        if ("constant" in item and item["constant"] in consts) or ("observer" in item and item["observer"] in observers):
            out.append(wid)
    return sorted(out)


def check_item(item, worlds, ref):
    """Reference outcome of a Part B item: (problems, reopened, finals {wid: (rw', analysis')}, category facts)."""
    try:
        _item_format(item, worlds)
        rl = ref_reopen(item, worlds, ref)
    except Invalid as ex:
        return [str(ex)], None, None, None
    probs, finals, after = [], {}, {}
    for wid, raw in worlds.items():
        new_raw, changed = apply_item(raw, item)
        if not changed:
            continue
        rw2, a2, p2 = load_and_check(new_raw)
        if p2:
            probs.extend("after the datum, %s: %s" % (wid, x) for x in p2)
            continue
        after[wid] = (rw2, a2)
    if probs:
        return probs, rl, None, None
    for wid in after:
        if wid not in rl and answer_of(after[wid][1]) != answer_of(ref[wid][1]):
            probs.append("rule gap: %s changes its verdict but the rules do not reopen it" % wid)
    for wid in rl:
        finals[wid] = after.get(wid, ref[wid])
    facts = item_facts(item, rl, ref, finals)
    return probs, rl, finals, facts


def item_facts(item, rl, ref, finals):
    t = item["type"]
    before = {w: ref[w][1] for w in rl}
    after = {w: finals[w][1] for w in rl}
    changed = [w for w in rl if answer_of(before[w]) != answer_of(after[w])]
    f = set()
    if t == "observation":
        wid = item["world"]
        v = ref[wid][1]["verdict"]
        if not rl:
            f.add("obs_inside")
            if v == "KNOWN":
                f.add("obs_inside@KNOWN")
        elif v in ("KNOWN", "NO_DEFICIT"):
            f.add("obs_flip")
            if v == "KNOWN":
                f.add("obs_flip@KNOWN")
        elif v == "FORK":
            f.add("obs_fork")
    elif t == "relation":
        rid = item["relation"]["id"]
        if not rl:
            f.add("rel_none")
        elif not changed:
            f.add("rel_unchanged")
        for w in rl:
            if before[w]["verdict"] == "NEW" and after[w]["verdict"] == "KNOWN" and after[w]["relation"] == rid:
                f.add("rel_new_known")
            if before[w]["verdict"] == "KNOWN" and after[w]["verdict"] == "FORK" and rid in after[w]["branches"]:
                f.add("rel_known_fork")
        if len(rl) >= 2:
            f.add("rel_multi")
        if any(rw.y == item["observable"] and a["verdict"] == "NO_DEFICIT" for rw, a in ref.values()):
            f.add("rel_with_nd")
    else:
        if not rl:
            f.add("root_none")
        elif not changed:
            f.add("root_unchanged")
        for w in rl:
            if before[w]["verdict"] != "NO_DEFICIT" and after[w]["verdict"] == "NO_DEFICIT":
                f.add("root_vanish")
            if before[w]["verdict"] != "NO_DEFICIT" and \
                    any(rid not in before[w].get("suff", []) for rid in after[w].get("suff", [])):
                f.add("root_revive")
        if len(rl) >= 2:
            f.add("root_multi")
    return f


def norm_answer(d):
    if not isinstance(d, dict):
        return {"verdict": None}
    out = {"verdict": d.get("verdict")}
    if out["verdict"] == "KNOWN":
        out["relation"] = d.get("relation")
    if out["verdict"] == "FORK":
        out["branches"] = sorted(d.get("branches") or [])
    return out


def key_problems_A(a, k):
    if not isinstance(k, dict):
        return ["no key entry"]
    p = []
    if norm_answer(k) != answer_of(a):
        p.append("key answer %s differs from the reference %s" % (norm_answer(k), answer_of(a)))
    rs = k.get("reasons")
    if rs is not None:
        if not isinstance(rs, dict):
            p.append("key reasons must be a map")
        else:
            for rid, lst in rs.items():
                if not isinstance(lst, list) or set(lst) != a["reasons"].get(rid, None):
                    p.append("key reasons for %s are %s, reference %s"
                             % (rid, lst, sorted(a["reasons"].get(rid, set())) if rid in a["reasons"] else "sufficient/none"))
    return p


def hidden_truth_ok(rw, ht):
    """True / False if the generator's hidden truth reproduces every reading within precision; None if absent."""
    if not isinstance(ht, dict):
        return None
    try:
        vc = num(ht.get("visible_coefficient", "0"), "visible coefficient")
        terms = []
        for t in ht.get("terms", []):
            c = num(t["coefficient"], "coefficient")
            if "candidate" in t:
                terms.append(("cand", rw.cand(t["candidate"]), c))
            else:
                terms.append(("expr", Expr(t["expr"], set(rw.state_q) | set(rw.cval)), c))
        for o in rw.old + rw.new:
            env = rw.env(o["state"])
            yv = rw.f.ev(env) + (vc * rw.vis.ev(env) if rw.vis is not None else 0)
            for kind, obj, c in terms:
                yv += c * (obj["h"].ev(env) * rw.factor(obj, env) if kind == "cand" else obj.ev(env))
            if abs(yv - o["value"]) > o["d"]:
                return False
        return True
    except (Invalid, KeyError, StopIteration, TypeError):
        return False


def key_problems_B(item, rl, finals, facts, k):
    if not isinstance(k, dict):
        return ["no key entry"]
    p = []
    cat = k.get("type")
    if cat not in ITEM_TYPES:
        p.append("unknown category %r" % cat)
    elif ITEM_TYPES[cat] != item["type"]:
        p.append("category %s does not fit an item of type %s" % (cat, item["type"]))
    elif cat not in facts:
        p.append("declared category %s does not hold (reference facts: %s)" % (cat, sorted(facts)))
    if sorted(k.get("reopened") or []) != rl:
        p.append("key reopened %s, reference %s" % (k.get("reopened"), rl))
    fin = k.get("final") or {}
    if not isinstance(fin, dict) or set(fin) != set(rl):
        p.append("key final verdicts must be given exactly for the reopened files")
    else:
        for w in rl:
            if norm_answer(fin[w]) != answer_of(finals[w][1]):
                p.append("key final verdict of %s is %s, reference %s" % (w, norm_answer(fin[w]), answer_of(finals[w][1])))
    return p


def touched(item, worlds):
    """World ids whose content the datum changes."""
    out = set()
    for wid, raw in worlds.items():
        try:
            if apply_item(raw, item)[1]:
                out.add(wid)
        except (KeyError, TypeError):
            pass
    return out


def item_composition(cats):
    """cats: {item id: (declared category, facts)} for valid items."""
    counts = {k: 0 for k in ITEM_COUNTS}
    for cat, facts in cats.values():
        if cat in counts:
            counts[cat] += 1
    need = []
    for k, n in ITEM_COUNTS.items():
        if counts[k] != n:
            need.append("%s items: %d, required %d" % (k, counts[k], n))
    facts = [f for _, f in cats.values()]
    if sum("rel_multi" in f for f in facts) < 2:
        need.append("relation items with 2 or more reopened files: required >= 2")
    if not any("rel_with_nd" in f for f in facts):
        need.append("no relation item whose observable has a NO_DEFICIT file")
    if not any("root_multi" in f for f in facts):
        need.append("no root item with 2 or more reopened files")
    if not any("obs_flip@KNOWN" in f for f in facts):
        need.append("no obs_flip item on a KNOWN file")
    if not any("obs_inside@KNOWN" in f for f in facts):
        need.append("no obs_inside item on a KNOWN file")
    return counts, need
