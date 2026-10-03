"""Aletheia blind test 3 -- frozen procedure v3.

Part A (primary): the nebulium check. A world has one observable, an established explanation (base law
plus at most one visible relation of uncertain strength mu), a ledger of candidate relations (each with
an optional coverage factor: dimmer or switch), and old / new / possible observations.
  step 0      -> NO_DEFICIT if the established explanation fits every reading within precision;
  sufficiency -> R suffices if it is dimensionally possible (TYPE), not forbidden by a symmetry, and the
                 actual system A_R (all readings, R with its actual coverage factor) is feasible;
  verdict     -> NEW (none), KNOWN (one: coefficient intervals + quarantine note), FORK (two or three:
                 ranges + decisive set);
  reasons     -> every applicable reason (TYPE, SYMMETRY, SCOPE, SHAPE, BOUND) for each excluded
                 candidate, with point / Farkas certificates.
  Linear systems are solved exactly with Fourier-Motzkin elimination over Fractions.
Part B (secondary): reopening of the Part A verdict files after one datum (rules R1-R3).

Usage:  python procedure_v3.py run <worlds_dir> <data_dir> <out_json>
"""
import copy
import json
import os
import sys
from fractions import Fraction

import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations

REASON_ORDER = ("TYPE", "SYMMETRY", "SCOPE", "SHAPE", "BOUND")
VAR_ORDER = ("mu", "lam", "t")


class WorldError(Exception):
    pass


# ================================================================= numbers and expressions

def Q(x):
    """Exact rational from an int or a string 'p' / 'p/q'."""
    if isinstance(x, bool):
        raise WorldError("boolean is not a number")
    if isinstance(x, int):
        return Fraction(x)
    if isinstance(x, str):
        s = x.strip()
        body = s[1:] if s.startswith("-") else s
        parts = body.split("/")
        if len(parts) in (1, 2) and all(p.isdigit() for p in parts):
            return Fraction(s)
    raise WorldError("not an exact rational: %r" % (x,))


def fstr(v):
    if v is None:
        return None
    v = Fraction(v)
    return str(v.numerator) if v.denominator == 1 else "%d/%d" % (v.numerator, v.denominator)


_GLOBALS = {"Integer": sp.Integer, "Rational": sp.Rational, "Symbol": sp.Symbol, "Float": sp.Float}


def parse(src, symbols):
    try:
        e = parse_expr(str(src), local_dict=dict(symbols), global_dict=dict(_GLOBALS),
                       transformations=standard_transformations)
    except Exception as ex:  # pragma: no cover - reported, not hidden
        raise WorldError("cannot parse %r: %s" % (src, ex))
    allowed = set(symbols.values())
    if not e.free_symbols <= allowed:
        raise WorldError("undeclared names in %r" % (src,))
    for node in sp.preorder_traversal(e):
        if node.is_Atom:
            if node.is_Number and not node.is_Rational:
                raise WorldError("non-rational number in %r" % (src,))
            continue
        if not (node.is_Add or node.is_Mul or node.is_Pow):
            raise WorldError("unsupported operation in %r" % (src,))
        if node.is_Pow and not node.args[1].is_Integer:
            raise WorldError("non-integer power in %r" % (src,))
    return e


def compile_expr(e):
    """sympy expression -> exact evaluator env -> Fraction."""
    if e.is_Rational:
        v = Fraction(int(e.p), int(e.q))
        return lambda env: v
    if e.is_Symbol:
        name = e.name
        return lambda env: env[name]
    if e.is_Add:
        fs = [compile_expr(a) for a in e.args]
        return lambda env: sum((f(env) for f in fs), Fraction(0))
    if e.is_Mul:
        fs = [compile_expr(a) for a in e.args]

        def mul(env):
            p = Fraction(1)
            for f in fs:
                p *= f(env)
            return p
        return mul
    if e.is_Pow:
        fb, k = compile_expr(e.args[0]), int(e.args[1])

        def pw(env):
            b = fb(env)
            if k < 0 and b == 0:
                raise WorldError("division by zero")
            return b ** k
        return pw
    raise WorldError("unsupported expression %s" % e)


def d_norm(d):
    return {k: v for k, v in d.items() if v != 0}


def d_add(a, b, s=1):
    r = dict(a)
    for k, v in b.items():
        r[k] = r.get(k, 0) + s * v
    return d_norm(r)


def dim_of(e, table):
    if e.is_Number:
        return {}
    if e.is_Symbol:
        return dict(table[e.name])
    if e.is_Add:
        ds = [dim_of(a, table) for a in e.args]
        for d in ds[1:]:
            if d != ds[0]:
                raise WorldError("sum of different dimensions")
        return ds[0]
    if e.is_Mul:
        r = {}
        for a in e.args:
            r = d_add(r, dim_of(a, table))
        return r
    if e.is_Pow:
        k = Fraction(int(e.args[1]))
        return d_norm({u: v * k for u, v in dim_of(e.args[0], table).items()})
    raise WorldError("cannot take dimensions of %s" % e)


# ================================================================= world model

class Cand:
    pass


class Obs:
    def __init__(self, state, value, observer, prec):
        self.state, self.value, self.observer, self.prec = state, value, observer, prec


class World:
    def __init__(self, w, ignore_coverage=False):
        self.raw = w
        self.id = w.get("id")
        self.ignore_coverage = ignore_coverage
        self.y = w["observable"]
        self.qd = {q: d_norm({k: Q(v) for k, v in d.items()}) for q, d in w["quantities"].items()}
        if self.y not in self.qd:
            raise WorldError("observable not among the quantities")
        self.state_q = [q for q in self.qd if q != self.y]
        consts = w.get("constants") or {}
        self.cval = {c: Q(s["value"]) for c, s in consts.items()}
        self.cd = {c: d_norm({k: Q(v) for k, v in (s.get("dims") or {}).items()}) for c, s in consts.items()}
        self.prec = {o: Q(p) for o, p in w["observers"].items()}
        self.sym = {n: sp.Symbol(n) for n in list(self.qd) + list(self.cval)}
        lhs, rhs = w["base_law"].split("=")
        if lhs.strip() != self.y:
            raise WorldError("base law must read  observable = expression")
        self.f_expr = parse(rhs, self.state_symbols())
        self.f = compile_expr(self.f_expr)
        vis = w.get("visible")
        self.visible = None
        if vis:
            self.visible = {"id": vis["id"], "expr": parse(vis["term"], self.state_symbols())}
            self.visible["h"] = compile_expr(self.visible["expr"])
        self.cands = []
        for c in w["ledger"]:
            R = Cand()
            R.id, R.object = c["id"], c.get("object")
            R.h_expr = parse(c["term"], self.state_symbols())
            R.h = compile_expr(R.h_expr)
            co = c.get("coefficient", "unknown")
            R.exact = None if co == "unknown" else Q(co["exact"])
            R.cov = None
            cov = c.get("coverage")
            if cov:
                R.cov = {"ratio_expr": parse(cov["ratio"], self.state_symbols())}
                R.cov["ratio"] = compile_expr(R.cov["ratio_expr"])
                fac = cov["factor"]
                R.cov["type"] = fac["type"]
                if fac["type"] == "dimmer":
                    R.cov["g"] = compile_expr(parse(fac["expr"], {"r": sp.Symbol("r")}))
                elif fac["type"] == "switch":
                    if fac["on"] not in ("<", ">"):
                        raise WorldError("switch 'on' must be < or >")
                    R.cov["on"], R.cov["t"] = fac["on"], Q(fac["threshold"])
                else:
                    raise WorldError("unknown factor type")
            self.cands.append(R)
        if len({R.id for R in self.cands}) != len(self.cands):
            raise WorldError("duplicate candidate ids")
        self.symmetries = []
        for s in w.get("symmetries") or []:
            mp = {self.sym[q]: parse(e, self.state_symbols()) for q, e in s["map"].items()}
            self.symmetries.append((s.get("name", "?"), mp))
        self.old = [self._obs(o) for o in w.get("old_observations") or []]
        self.new = [self._obs(o) for o in w.get("new_observations") or []]
        self.possible = [self._obs(o, reading=False) for o in w.get("possible_observations") or []]

    def state_symbols(self):
        return dict(self.sym)

    def _obs(self, o, reading=True):
        st = {q: Q(o["state"][q]) for q in self.state_q}
        obs = o["observer"]
        if obs not in self.prec:
            raise WorldError("unknown observer %s" % obs)
        return Obs(st, Q(o["value"]) if reading else None, obs, self.prec[obs])

    def env(self, state):
        e = dict(self.cval)
        e.update(state)
        return e

    def phi(self, R, env):
        if self.ignore_coverage or R.cov is None:
            return Fraction(1)
        rho = R.cov["ratio"](env)
        if R.cov["type"] == "dimmer":
            return R.cov["g"]({"r": rho})
        on = rho < R.cov["t"] if R.cov["on"] == "<" else rho > R.cov["t"]
        return Fraction(1) if on else Fraction(0)

    # ------------------------------------------------------------- linear systems
    def unknowns(self, R, mode):
        v = ["mu"] if self.visible is not None else []
        if R is not None and (R.exact is None or mode == "S"):
            v.append("lam")
        return v

    def rows(self, R, mode):
        """Inequalities  a.x <= b  (Row objects) of system Z, A, C or S for candidate R."""
        out = []
        for dom, obs_list in (("old", self.old), ("new", self.new)):
            for k, ob in enumerate(obs_list):
                env = self.env(ob.state)
                const = self.f(env)
                coef = {}
                if self.visible is not None:
                    coef["mu"] = self.visible["h"](env)
                if R is not None and mode != "Z" and not (mode == "S" and dom == "old"):
                    phi = Fraction(1) if (mode in ("C", "S") and dom == "new") else self.phi(R, env)
                    hv = R.h(env) * phi
                    if R.exact is not None and mode != "S":
                        const += R.exact * hv
                    else:
                        coef["lam"] = hv
                coef = {v: c for v, c in coef.items() if c != 0}
                out.append(Row(coef, ob.value + ob.prec - const, {(dom, k, "upper"): Fraction(1)}))
                out.append(Row({v: -c for v, c in coef.items()}, -(ob.value - ob.prec - const),
                               {(dom, k, "lower"): Fraction(1)}))
        return out

    def functional(self, R, state):
        """Predicted value of y at a state: (constant, {var: coefficient}), actual factors."""
        env = self.env(state)
        c0, coef = self.f(env), {}
        if self.visible is not None:
            coef["mu"] = self.visible["h"](env)
        if R is not None:
            hv = R.h(env) * self.phi(R, env)
            if R.exact is not None:
                c0 += R.exact * hv
            else:
                coef["lam"] = hv
        return c0, {v: c for v, c in coef.items() if c != 0}

    # ------------------------------------------------------------- theory checks
    def type_impossible(self, R):
        table = dict(self.qd)
        table.update(self.cd)
        need = d_add(self.qd[self.y], dim_of(R.h_expr, table), -1)
        if not need:
            return False
        names = sorted(self.cd)
        if not names:
            return True
        base = sorted(set(need) | {k for d in self.cd.values() for k in d})
        V = sp.Matrix([[sp.Rational(self.cd[c].get(b, 0)) for c in names] for b in base])
        t = sp.Matrix([sp.Rational(need.get(b, 0)) for b in base])
        return V.rank() != V.row_join(t).rank()

    def symmetry_forbids(self, R):
        ysym, lam, mu = self.sym[self.y], sp.Symbol("lam_"), sp.Symbol("mu_")
        F = self.f_expr + lam * R.h_expr
        if self.visible is not None:
            F = F + mu * self.visible["expr"]
        for name, mp in self.symmetries:
            y_new = mp.get(ysym, ysym).xreplace({ysym: F})
            rhs_new = F.xreplace({k: v for k, v in mp.items() if k != ysym})
            E = sp.simplify(sp.together(y_new - rhs_new))
            if sp.simplify(E.subs(lam, 0)) != 0:
                raise WorldError("declared symmetry %s is not a symmetry of the established law" % name)
            if sp.simplify(sp.diff(E, lam)) != 0:
                return True
        return False


# ================================================================= Fourier-Motzkin with multipliers

class Row:
    __slots__ = ("a", "b", "m")

    def __init__(self, a, b, m):
        self.a, self.b, self.m = a, b, m


def _scale(row, k):
    return Row({v: c * k for v, c in row.a.items()}, row.b * k, {t: y * k for t, y in row.m.items()})


def _prune(rows):
    best_const, by_dir = None, {}
    for r in rows:
        if not r.a:
            if r.b < 0 and (best_const is None or len(r.m) < len(best_const.m)
                            or (len(r.m) == len(best_const.m) and r.b < best_const.b)):
                best_const = r
            continue
        lead = next(v for v in VAR_ORDER if v in r.a)
        r = _scale(r, 1 / abs(r.a[lead]))
        key = tuple(sorted(r.a.items()))
        if key not in by_dir or r.b < by_dir[key].b:
            by_dir[key] = r
    out = list(by_dir.values())
    if best_const is not None:
        out.append(best_const)
    return out


def fm_eliminate(rows, var):
    pos, neg, out = [], [], []
    for r in rows:
        c = r.a.get(var, 0)
        (pos if c > 0 else neg if c < 0 else out).append(r)
    for p in pos:
        cp = p.a[var]
        for n in neg:
            cn = -n.a[var]
            a = {}
            for v in set(p.a) | set(n.a):
                if v != var:
                    val = cn * p.a.get(v, 0) + cp * n.a.get(v, 0)
                    if val != 0:
                        a[v] = val
            m = {}
            for t, y in p.m.items():
                m[t] = m.get(t, 0) + cn * y
            for t, y in n.m.items():
                m[t] = m.get(t, 0) + cp * y
            out.append(Row(a, cn * p.b + cp * n.b, m))
    return _prune(out)


def fm_feasible(rows, variables):
    cur = _prune(list(rows))
    for v in variables:
        cur = fm_eliminate(cur, v)
    bad = [r for r in cur if not r.a and r.b < 0]
    if not bad:
        return True, None
    bad.sort(key=lambda r: (len(r.m), r.b))
    return False, bad[0].m


def _bounds(rows, var):
    lo, hi = None, None
    for r in rows:
        c = r.a.get(var, 0)
        if any(v != var for v in r.a):
            raise WorldError("internal: projection not complete")
        if c > 0:
            hi = r.b / c if hi is None else min(hi, r.b / c)
        elif c < 0:
            lo = r.b / c if lo is None else max(lo, r.b / c)
        elif r.b < 0:
            raise WorldError("internal: infeasible system in projection")
    return lo, hi


def fm_interval(rows, variables, var):
    cur = _prune(list(rows))
    for v in variables:
        if v != var:
            cur = fm_eliminate(cur, v)
    return _bounds(cur, var)


def _choose(lo, hi):
    if lo is not None and hi is not None:
        return (lo + hi) / 2
    if lo is not None:
        return lo
    if hi is not None:
        return hi
    return Fraction(0)


def _substitute(rows, var, val):
    out = []
    for r in rows:
        if var in r.a:
            a = {v: c for v, c in r.a.items() if v != var}
            out.append(Row(a, r.b - r.a[var] * val, r.m))
        else:
            out.append(r)
    return out


def fm_point(rows, variables):
    vals, cur = {}, list(rows)
    for i in range(len(variables) - 1, -1, -1):
        v = variables[i]
        lo, hi = fm_interval(cur, variables[:i + 1], v)
        vals[v] = _choose(lo, hi)
        cur = _substitute(cur, v, vals[v])
    return {v: fstr(vals[v]) for v in variables}


def fm_range(rows, variables, c0, coef):
    """Exact [min, max] of c0 + coef.x over the feasible set (None = unbounded)."""
    extra = [Row(dict({"t": Fraction(1)}, **{v: -c for v, c in coef.items()}), c0, {}),
             Row(dict({"t": Fraction(-1)}, **{v: c for v, c in coef.items()}), -c0, {})]
    return fm_interval(list(rows) + extra, list(variables) + ["t"], "t")


def farkas_json(m):
    return [{"obs": t[0], "k": t[1], "side": t[2], "y": fstr(y)}
            for t, y in sorted(m.items()) if y != 0]


def interval_json(lo_hi):
    return [fstr(lo_hi[0]), fstr(lo_hi[1])]


# ================================================================= Part A analysis

def explanation(world, R, rows, variables):
    exp = {"point": fm_point(rows, variables),
           "intervals": {"lam": interval_json(fm_interval(rows, variables, "lam")) if "lam" in variables else None,
                         "mu": interval_json(fm_interval(rows, variables, "mu")) if "mu" in variables else None},
           "ranges": []}
    for p in world.possible:
        c0, coef = world.functional(R, p.state)
        exp["ranges"].append(interval_json(fm_range(rows, variables, c0, coef)))
    return exp


def _gap(I, J):
    if None in (I[0], I[1], J[0], J[1]):
        return None
    return max(Q(J[0]) - Q(I[1]), Q(I[0]) - Q(J[1]))


def decisive_set(world, branches, exps):
    pairs = [(a, b) for i, a in enumerate(branches) for b in branches[i + 1:]]
    sep = []
    for k, p in enumerate(world.possible):
        s = set()
        for a, b in pairs:
            g = _gap(exps[a]["ranges"][k], exps[b]["ranges"][k])
            if g is not None and g > 2 * p.prec:
                s.add((a, b))
        sep.append(s)
    remaining, chosen = set(pairs), []
    while remaining:
        best = max(range(len(sep)), key=lambda k: (len(sep[k] & remaining), -k)) if sep else None
        if best is None or not (sep[best] & remaining):
            return None
        chosen.append(best)
        remaining -= sep[best]
    return sorted(chosen)


def free_names(e, names):
    return {s.name for s in e.free_symbols if s.name in names}


def depends_on(world, verdict):
    consts = free_names(world.f_expr, world.cval)
    if world.visible is not None:
        consts |= free_names(world.visible["expr"], world.cval)
    examined = []
    if verdict != "NO_DEFICIT":
        examined = [R.id for R in world.cands]
        for R in world.cands:
            consts |= free_names(R.h_expr, world.cval)
            if R.cov is not None:
                consts |= free_names(R.cov["ratio_expr"], world.cval)
    observers = {o.observer for o in world.old + world.new}
    if verdict == "FORK":
        observers |= {p.observer for p in world.possible}
    return {"observable": world.y, "examined": examined, "constants": sorted(consts), "observers": sorted(observers)}


def analyse(world, proofs=True):
    out = {}
    zv = world.unknowns(None, "Z")
    Z = world.rows(None, "Z")
    ok, cert = fm_feasible(Z, zv)
    if ok:
        out["verdict"] = "NO_DEFICIT"
        if proofs:
            out["step0"] = {"deficit": False, "certificate": fm_point(Z, zv)}
            out["explanations"] = {"BASE": explanation(world, None, Z, zv)}
            out["depends_on"] = depends_on(world, "NO_DEFICIT")
        return out
    if proofs:
        out["step0"] = {"deficit": True, "certificate": farkas_json(cert)}
    suff, excluded, systems = [], {}, {}
    for R in world.cands:
        t_imp = world.type_impossible(R)
        s_forb = world.symmetry_forbids(R)
        av = world.unknowns(R, "A")
        A = world.rows(R, "A")
        fa, ca = fm_feasible(A, av)
        if fa and not t_imp and not s_forb:
            suff.append(R)
            systems[R.id] = (A, av)
            continue
        reasons, certs = [], {}
        if t_imp:
            reasons.append("TYPE")
        if s_forb:
            reasons.append("SYMMETRY")
        if not fa:
            cv, sv = world.unknowns(R, "C"), world.unknowns(R, "S")
            C, S = world.rows(R, "C"), world.rows(R, "S")
            fc, cc = fm_feasible(C, cv)
            fs, cs = fm_feasible(S, sv)
            if R.cov is not None and not world.ignore_coverage and fc:
                reasons.append("SCOPE")
                if proofs:
                    certs["SCOPE"] = {"A": farkas_json(ca), "C": fm_point(C, cv)}
            if not fs:
                reasons.append("SHAPE")
                if proofs:
                    certs["SHAPE"] = {"S": farkas_json(cs)}
            if fs and not fc:
                reasons.append("BOUND")
                if proofs:
                    certs["BOUND"] = {"S": fm_point(S, sv), "C": farkas_json(cc)}
        excluded[R.id] = {"reasons": reasons, "certificates": certs}
    if not suff:
        out["verdict"] = "NEW"
    elif len(suff) == 1:
        out["verdict"], out["relation"] = "KNOWN", suff[0].id
    else:
        out["verdict"], out["branches"] = "FORK", sorted(R.id for R in suff)
    if proofs:
        out["excluded"] = excluded
        exps = {}
        for R in suff:
            rows, variables = systems[R.id]
            exps[R.id] = explanation(world, R, rows, variables)
        if suff:
            out["explanations"] = exps
        if out["verdict"] == "FORK":
            out["decisive"] = decisive_set(world, out["branches"], exps)
        out["depends_on"] = depends_on(world, out["verdict"])
    return out


def answer(out):
    keep = {"verdict": out.get("verdict")}
    if "relation" in out:
        keep["relation"] = out["relation"]
    if "branches" in out:
        keep["branches"] = out["branches"]
    if "error" in out:
        keep["error"] = out["error"]
    return keep


def base_step(world):
    Z, zv = world.rows(None, "Z"), world.unknowns(None, "Z")
    return fm_feasible(Z, zv)[0]


def baseline_always_new(world):
    return {"verdict": "NO_DEFICIT"} if base_step(world) else {"verdict": "NEW"}


def baseline_dims_only(world):
    if base_step(world):
        return {"verdict": "NO_DEFICIT"}
    for R in world.cands:
        if not world.type_impossible(R):
            return {"verdict": "KNOWN", "relation": R.id}
    return {"verdict": "NEW"}


def baseline_no_scope(raw):
    return answer(analyse(World(raw, ignore_coverage=True), proofs=False))


def guarded(fn, *args):
    try:
        return fn(*args)
    except WorldError as ex:
        return {"verdict": None, "error": "WorldError: %s" % ex}
    except Exception as ex:  # pragma: no cover - recorded, not hidden
        return {"verdict": None, "error": "%s: %s" % (type(ex).__name__, ex)}


def run_world(raw):
    res = {"procedure": guarded(lambda r: analyse(World(r)), raw)}
    res["ALWAYS_NEW"] = guarded(lambda r: baseline_always_new(World(r)), raw)
    res["DIMS_ONLY"] = guarded(lambda r: baseline_dims_only(World(r)), raw)
    res["NO_SCOPE"] = guarded(baseline_no_scope, raw)
    return res


# ================================================================= Part B: reopening

def apply_datum(raw, item):
    w = copy.deepcopy(raw)
    t = item["type"]
    if t == "observation" and w.get("id") == item["world"]:
        w.setdefault("new_observations", []).append(
            {"state": item["state"], "value": item["value"], "observer": item["observer"]})
    elif t == "relation" and w["observable"] == item["observable"]:
        w["ledger"].append(copy.deepcopy(item["relation"]))
    elif t == "root":
        if "constant" in item and item["constant"] in (w.get("constants") or {}):
            w["constants"][item["constant"]]["value"] = item["new_value"]
        if "observer" in item and item["observer"] in w["observers"]:
            w["observers"][item["observer"]] = item["new_precision"]
    return w


def _misses(reading_lo, reading_hi, rng):
    lo = None if rng[0] is None else Q(rng[0])
    hi = None if rng[1] is None else Q(rng[1])
    return (hi is not None and reading_lo > hi) or (lo is not None and reading_hi < lo)


def reopen_list(item, worlds, files):
    """Rules R1-R3 applied to the procedure's own Part A files."""
    t = item["type"]
    if t == "observation":
        wid = item["world"]
        f = files.get(wid, {})
        if f.get("verdict") in (None, "NEW"):
            return []
        W = World(worlds[wid])
        st = {q: Q(item["state"][q]) for q in W.state_q}
        d = W.prec[item["observer"]]
        v = Q(item["value"])
        lo, hi = v - d, v + d
        idx = next((k for k, p in enumerate(W.possible)
                    if p.state == st and p.observer == item["observer"]), None)
        exps = f.get("explanations", {})
        targets = list(exps) if f["verdict"] == "FORK" else (["BASE"] if f["verdict"] == "NO_DEFICIT" else [f["relation"]])
        for key in targets:
            if idx is not None:
                rng = exps[key]["ranges"][idx]
            else:
                R = None if key == "BASE" else next(c for c in W.cands if c.id == key)
                rows = W.rows(R, "A" if R is not None else "Z")
                variables = W.unknowns(R, "A" if R is not None else "Z")
                c0, coef = W.functional(R, st)
                rng = interval_json(fm_range(rows, variables, c0, coef))
            if _misses(lo, hi, rng):
                return [wid]
        return []
    if t == "relation":
        return sorted(wid for wid, raw in worlds.items()
                      if raw["observable"] == item["observable"]
                      and files.get(wid, {}).get("verdict") not in (None, "NO_DEFICIT"))
    if t == "root":
        out = []
        for wid in worlds:
            dep = files.get(wid, {}).get("depends_on")
            if not dep:
                continue
            if "constant" in item and item["constant"] in dep["constants"]:
                out.append(wid)
            elif "observer" in item and item["observer"] in dep["observers"]:
                out.append(wid)
        return sorted(out)
    raise WorldError("unknown item type %s" % t)


def run_item(item, worlds, files):
    proc = {}
    try:
        rl = reopen_list(item, worlds, files)
        proc = {"reopened": rl, "verdicts": {}}
        for wid in rl:
            proc["verdicts"][wid] = guarded(lambda r: analyse(World(r)), apply_datum(worlds[wid], item))
    except Exception as ex:  # pragma: no cover - recorded, not hidden
        proc = {"reopened": [], "verdicts": {}, "error": "%s: %s" % (type(ex).__name__, ex)}
    allv = {wid: answer(guarded(lambda r: analyse(World(r), proofs=False), apply_datum(worlds[wid], item)))
            for wid in sorted(worlds)}
    return {"procedure": proc, "REOPEN_NONE": {"reopened": []},
            "REOPEN_ALL": {"reopened": sorted(worlds), "verdicts": allv}}


# ================================================================= runner

def load_dir(d, experiment):
    out = {}
    if not d or not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".json"):
            with open(os.path.join(d, fn), encoding="utf-8") as fh:
                obj = json.load(fh)
            if obj.get("experiment") == experiment:
                out[obj.get("id", fn)] = obj
    return out


def run(worlds_dir, data_dir, out_path):
    worlds = load_dir(worlds_dir, "A")
    items = load_dir(data_dir, "B")
    res = {"A": {}, "B": {}}
    for wid, raw in worlds.items():
        res["A"][wid] = run_world(raw)
        p = res["A"][wid]["procedure"]
        print(wid, json.dumps(answer(p), ensure_ascii=False))
    files = {wid: r["procedure"] for wid, r in res["A"].items()}
    for did, item in items.items():
        res["B"][did] = run_item(item, worlds, files)
        print(did, "reopened", res["B"][did]["procedure"].get("reopened"))
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, sort_keys=True)


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "run":
        run(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print(__doc__)
