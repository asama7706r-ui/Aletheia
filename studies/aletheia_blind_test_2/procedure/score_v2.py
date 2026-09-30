"""Aletheia blind test 2 -- frozen scorer v2.

Independent of the procedure: it does NOT import procedure_v2. Every claim in the key is checked
by elementary means: witnesses by exact matrix arithmetic, noncommutative ideal membership by
expanding the certificate, commutative membership and rational solutions by its own sympy code.

Usage:  python score_v2.py <worlds_dir> <key_json> <outputs_json> <report_json>
"""
import json
import os
import sys
import itertools
from fractions import Fraction
from math import comb

import sympy as sp
from sympy.parsing.sympy_parser import parse_expr

GRID = [Fraction(v) for v in (-3, -2, -1, 0, 1, 2, 3)] + [Fraction(-1, 2), Fraction(1, 2)]
EXCLUSION_CAP = Fraction(1, 5)
LEVEL_ORDER = ("SUBSUMED", "comm", "graded", "assoc")


def fr(x):
    if isinstance(x, Fraction):
        return x
    if isinstance(x, sp.Rational):
        return Fraction(int(x.p), int(x.q))
    return Fraction(str(x))


def fstr(v):
    return str(v.numerator) if v.denominator == 1 else "%d/%d" % (v.numerator, v.denominator)


class KeyError_(Exception):
    pass


# ================================================================= Part A: polynomials

class Ctx:
    def __init__(self, world, pv):
        self.world = world
        self.gens = [g["name"] for g in world["generators"]]
        self.grades = [int(g.get("grade", 0)) % 2 for g in world["generators"]]
        self.vars = list(world.get("variables", []))
        self.gi = {n: i for i, n in enumerate(self.gens)}
        self.vi = {n: i for i, n in enumerate(self.vars)}
        self.loc = {n: sp.Symbol(n, commutative=False) for n in self.gens}
        for n in self.vars + list(world.get("parameters", [])):
            self.loc[n] = sp.Symbol(n, commutative=True)
        self.subs = {self.loc[p]: sp.Rational(str(v)) for p, v in (pv or {}).items()}
        self.zero = (0,) * len(self.vars)

    def poly(self, e):
        e = sp.expand(e.subs(self.subs) if self.subs else e)
        out = {}
        for term in sp.Add.make_args(e):
            if term == 0:
                continue
            c, nc = term.args_cnc()
            coef, vm = Fraction(1), [0] * len(self.vars)
            for f in c:
                if f.is_Number:
                    coef *= fr(f)
                elif f.is_Symbol and f.name in self.vi:
                    vm[self.vi[f.name]] += 1
                elif f.is_Pow and f.base.is_Symbol and f.base.name in self.vi and f.exp.is_Integer:
                    vm[self.vi[f.base.name]] += int(f.exp)
                else:
                    raise KeyError_("unexpected commutative factor %s" % f)
            word = []
            for f in nc:
                if f.is_Symbol and f.name in self.gi:
                    word.append(self.gi[f.name])
                elif f.is_Pow and f.base.is_Symbol and f.base.name in self.gi and f.exp.is_Integer and f.exp > 0:
                    word += [self.gi[f.base.name]] * int(f.exp)
                else:
                    raise KeyError_("unexpected factor %s" % f)
            k = (tuple(vm), tuple(word))
            v = out.get(k, 0) + coef
            if v == 0:
                out.pop(k, None)
            else:
                out[k] = v
        return out

    def expr_poly(self, s):
        return self.poly(parse_expr(s, local_dict=self.loc))

    def law_poly(self, i):
        lhs, rhs = self.world["laws"][i].split("=")
        p = self.expr_poly(lhs)
        for k, v in self.expr_poly(rhs).items():
            nv = p.get(k, 0) - v
            if nv == 0:
                p.pop(k, None)
            else:
                p[k] = nv
        return p

    def vm_of(self, d):
        return tuple(int(d.get(v, 0)) for v in self.vars)

    def relation(self, ref):
        if "law" in ref:
            vm = self.vm_of(ref.get("varmono", {}))
            return {w: c for (m, w), c in self.law_poly(int(ref["law"])).items() if m == vm}
        if ref.get("rule") == "graded":
            a, b = (self.gi[x] for x in ref["pair"])
            if a == b:
                if not self.grades[a]:
                    raise KeyError_("x*x rule only for odd generators")
                return {(a, a): Fraction(1)}
            s = -1 if (self.grades[a] and self.grades[b]) else 1
            return {(a, b): Fraction(1), (b, a): Fraction(-s)}
        raise KeyError_("unknown relation reference %s" % ref)

    def mentions(self):
        out, seen = [], set()
        for law in self.world["laws"]:
            for side in law.split("="):
                stack = [parse_expr(side, local_dict=self.loc, evaluate=False)]
                while stack:
                    x = stack.pop()
                    if any(getattr(s, "name", None) in self.gi for s in x.free_symbols):
                        p = self.poly(x)
                        key = frozenset(p.items())
                        if p and key not in seen:
                            seen.add(key)
                            out.append((str(x), p))
                    stack.extend(x.args)
        return out


def groups(poly):
    g = {}
    for (vm, w), c in poly.items():
        g.setdefault(vm, {})[w] = c
    return g


def pkey(poly):
    return frozenset(poly.items())


# ================================================================= Part A: certificates

def cert_expand(ctx, terms, level):
    out = {}
    for coef, left, ref, right in terms:
        if "rule" in ref and level != "graded":
            raise KeyError_("family rule used outside the graded level")
        rel = ctx.relation(ref)
        u = tuple(ctx.gi[x] for x in left)
        v = tuple(ctx.gi[x] for x in right)
        c = fr(coef)
        for w, rc in rel.items():
            k = u + w + v
            nv = out.get(k, 0) + c * rc
            if nv == 0:
                out.pop(k, None)
            else:
                out[k] = nv
    return out


def cert_ok(ctx, target, cert, level):
    """target: poly; cert: [{"varmono": {...}, "terms": [...]}, ...] covering every nonzero group."""
    tg = groups(target)
    by_vm = {ctx.vm_of(g.get("varmono", {})): g["terms"] for g in cert}
    for vm, grp in tg.items():
        if vm not in by_vm:
            return False
        if cert_expand(ctx, by_vm[vm], level) != grp:
            return False
    return True


def trivially_dead(ctx, poly):
    """A mention equal to a constant times a whole law residual (e.g. the left side of 'X = 0')."""
    for i in range(len(ctx.world["laws"])):
        lp = ctx.law_poly(i)
        if not lp or set(lp) != set(poly):
            continue
        ratios = {poly[k] / lp[k] for k in lp}
        if len(ratios) == 1:
            return True
    return False


# ================================================================= Part A: matrices

def mat(rows):
    return [[fr(x) for x in r] for r in rows]


def mmul(A, B):
    n, m, p = len(A), len(B), len(B[0])
    return [[sum((A[i][k] * B[k][j] for k in range(m)), Fraction(0)) for j in range(p)] for i in range(n)]


def ident(n):
    return [[Fraction(int(i == j)) for j in range(n)] for i in range(n)]


def is_zero(M):
    return all(v == 0 for r in M for v in r)


def witness_mats(ctx, W):
    Ms = [mat(W[g]) for g in ctx.gens]
    n = len(Ms[0])
    if any(len(M) != n or any(len(r) != n for r in M) for M in Ms):
        raise KeyError_("witness matrices must be square and of equal size")
    return Ms, n


def eval_group(grp, Ms, n):
    acc = [[Fraction(0)] * n for _ in range(n)]
    for w, c in grp.items():
        P = ident(n)
        for i in w:
            P = mmul(P, Ms[i])
        for a in range(n):
            for b in range(n):
                acc[a][b] += c * P[a][b]
    return acc


def nonzero_on(poly, Ms, n):
    return any(not is_zero(eval_group(g, Ms, n)) for g in groups(poly).values())


def laws_hold(ctx, Ms, n):
    return all(not nonzero_on(ctx.law_poly(i), Ms, n) for i in range(len(ctx.world["laws"])))


def in_level(ctx, Ms, level):
    k = len(Ms)
    if level == "comm":
        return all(mmul(Ms[i], Ms[j]) == mmul(Ms[j], Ms[i]) for i in range(k) for j in range(i + 1, k))
    if level == "graded":
        for i in range(k):
            if ctx.grades[i] and not is_zero(mmul(Ms[i], Ms[i])):
                return False
            for j in range(i + 1, k):
                s = -1 if (ctx.grades[i] and ctx.grades[j]) else 1
                a, b = mmul(Ms[i], Ms[j]), mmul(Ms[j], Ms[i])
                if any(a[x][y] - s * b[x][y] != 0 for x in range(len(a)) for y in range(len(a))):
                    return False
        return True
    return level == "assoc"


def pref_level(ctx, Ms):
    if in_level(ctx, Ms, "comm"):
        return "comm"
    if any(ctx.grades) and in_level(ctx, Ms, "graded"):
        return "graded"
    return "assoc"


def values_mats(vals):
    return [[[fr(v)]] for v in vals], 1


# ================================================================= Part A: commutative side

def comm_image(ctx, grp, syms):
    e = sp.Integer(0)
    for w, c in grp.items():
        t = sp.Rational(c.numerator, c.denominator)
        for i in w:
            t = t * syms[i]
        e += t
    return sp.expand(e)


def comm_basis(ctx):
    syms = sp.symbols("c0:%d" % len(ctx.gens))
    polys = []
    for i in range(len(ctx.world["laws"])):
        for g in groups(ctx.law_poly(i)).values():
            p = comm_image(ctx, g, syms)
            if p != 0:
                polys.append(p)
    G = sp.groebner(polys, *syms, order="grevlex", domain="QQ") if polys else None
    return G, syms


def comm_member(ctx, G, syms, poly):
    for g in groups(poly).values():
        p = comm_image(ctx, g, syms)
        if p == 0:
            continue
        if G is None or G.reduce(p)[1] != 0:
            return False
    return True


def rational_solutions(ctx, G, syms):
    n = len(ctx.gens)
    if G is not None and list(G.exprs) == [1]:
        return []
    if G is None:
        return [tuple(v) for v in itertools.product(GRID, repeat=n)]
    if G.is_zero_dimensional:
        sols = []
        for d in sp.solve(list(G.exprs), list(syms), dict=True):
            vals = [d.get(s) for s in syms]
            if all(v is not None and v.is_Rational for v in vals):
                sols.append(tuple(fr(v) for v in vals))
        return sols
    return [v for v in itertools.product(GRID, repeat=n)
            if all(sp.expand(g.subs({syms[i]: sp.Rational(v[i].numerator, v[i].denominator)
                                      for i in range(n)})) == 0 for g in G.exprs)]


def zero_at(poly, vals):
    tot = {}
    for (vm, w), c in poly.items():
        t = c
        for i in w:
            t *= vals[i]
        tot[vm] = tot.get(vm, 0) + t
    return all(v == 0 for v in tot.values())


# ================================================================= Part A: key validation

def validate_A(world, key):
    """Returns (ok, reason, info). info feeds the scoring of decisive sets."""
    ans = key.get("answer")
    params = list(world.get("parameters", []))
    if ans == "UNDERDETERMINED":
        return (bool(params), "accepted as keyed" if params else "UNDERDETERMINED without a parameter", {})
    pv = key.get("true_parameter_values", {})
    if params and set(pv) != set(params):
        return False, "true_parameter_values missing", {}
    ctx = Ctx(world, pv)
    demands = [ctx.expr_poly(o["expr"]) for o in world.get("observations", [])]
    if ans == "CONTRADICTION":
        c = key["contradiction"]
        t = c["target"]
        if t != "1" and t not in [o["expr"] for o in world.get("observations", [])]:
            return False, "contradiction target is neither 1 nor an observation", {}
        target = {(ctx.zero, ()): Fraction(1)} if t == "1" else ctx.expr_poly(t)
        return (cert_ok(ctx, target, c["certificate"], "assoc"), "contradiction certificate", {})
    ments = ctx.mentions()
    dead = set()
    for d in key.get("dead_in_assoc", []):
        p = ctx.expr_poly(d["mention"])
        if not cert_ok(ctx, p, d["certificate"], "assoc"):
            return False, "dead_in_assoc certificate for %s" % d["mention"], {}
        dead.add(pkey(p))
    live = [(t, p) for t, p in ments if pkey(p) not in dead and not trivially_dead(ctx, p)]
    G, syms = comm_basis(ctx)
    sols = rational_solutions(ctx, G, syms)
    viable = [s for s in sols if all(not zero_at(d, s) for d in demands)]
    levels = [L for L in LEVEL_ORDER if L != "graded" or any(ctx.grades)]
    excluded = set()
    for ex in key.get("exclusions", []):
        L = ex["level"]
        if L == "SUBSUMED":
            ok = not viable
        else:
            t = ex.get("target", "1")
            if t != "1" and t not in [o["expr"] for o in world.get("observations", [])]:
                return False, "exclusion target is neither 1 nor an observation", {}
            target = {(ctx.zero, ()): Fraction(1)} if t == "1" else ctx.expr_poly(t)
            if L == "comm":
                ok = comm_member(ctx, G, syms, target)
            elif L == "graded":
                ok = cert_ok(ctx, target, ex.get("certificate", []), "graded")
            else:
                ok = False
        if not ok:
            return False, "exclusion of %s not verified" % L, {}
        excluded.add(L)

    def check_witness(W, level, need_all_live):
        Ms, n = witness_mats(ctx, W)
        if not laws_hold(ctx, Ms, n):
            return "laws fail on the %s witness" % level
        if not in_level(ctx, Ms, level):
            return "the %s witness is not in its level" % level
        if any(not nonzero_on(d, Ms, n) for d in demands):
            return "a demand vanishes on the %s witness" % level
        if need_all_live:
            bad = [t for t, p in live if not nonzero_on(p, Ms, n)]
            if bad:
                return "live mention(s) %s vanish on the %s witness" % (bad[:3], level)
        return None

    info = {"ctx": ctx, "G": G, "syms": syms, "viable": viable, "live": live}
    truth = key.get("truth", {})
    if ans == "DETERMINED":
        F = key["level"]
        for L in levels[:levels.index(F)]:
            if L not in excluded:
                return False, "level %s before %s is not excluded" % (L, F), {}
        if F == "SUBSUMED":
            passing = [s for s in viable if all(not zero_at(p, s) for _, p in live)]
            if not passing:
                return False, "no passing rational solution", {}
            tv = tuple(fr(v) for v in truth.get("values", []))
            if tv not in passing:
                return False, "true values are not a passing solution", {}
            info["passing"] = passing
        else:
            err = check_witness(key["witness"], F, True)
            if err:
                return False, err, {}
            Ms, n = witness_mats(ctx, truth["witness"])
            if not laws_hold(ctx, Ms, n) or any(not nonzero_on(d, Ms, n) for d in demands):
                return False, "truth witness fails the laws or a demand", {}
            if pref_level(ctx, Ms) != F:
                return False, "truth witness level %s != %s" % (pref_level(ctx, Ms), F), {}
        return True, "ok", info
    if ans != "FORK":
        return False, "unknown answer %s" % ans, {}
    br = key["branches"]
    names = [b["level"] for b in br]
    idx = [levels.index(L) for L in names]
    if idx != sorted(set(idx)) or len(br) < 2:
        return False, "branches must be distinct levels in preference order", {}
    for L in levels[:idx[-1] + 1]:
        if L not in names and L not in excluded:
            return False, "level %s is neither a branch nor excluded" % L, {}
    if names[0] == "SUBSUMED" and not viable:
        return False, "SUBSUMED branch without a viable rational solution", {}
    last = br[-1]
    if last["level"] == "SUBSUMED":
        return False, "the last branch cannot be SUBSUMED", {}
    err = check_witness(last["witness"], last["level"], True)
    if err:
        return False, err, {}
    lastM = witness_mats(ctx, last["witness"])
    info["last"] = lastM
    for b in br[:-1]:
        if b["level"] == "SUBSUMED":
            if any(all(not zero_at(p, s) for _, p in live) for s in viable):
                return False, "a viable rational solution keeps every live mention", {}
            continue
        err = check_witness(b["witness"], b["level"], False)
        if err:
            return False, err, {}
        proved = False
        for k in b.get("killed", []):
            p = ctx.expr_poly(k["mention"])
            if pkey(p) not in {pkey(q) for _, q in live} or not nonzero_on(p, *lastM):
                continue
            if b["level"] == "comm":
                proved = proved or comm_member(ctx, G, syms, p)
            elif b["level"] == "graded":
                proved = proved or cert_ok(ctx, p, k.get("certificate", []), "graded")
        if not proved:
            return False, "no verified killed live mention at branch %s" % b["level"], {}
    tl = truth.get("level")
    if tl not in names:
        return False, "truth level is not a branch", {}
    if tl == "SUBSUMED":
        tv = tuple(fr(v) for v in truth.get("values", []))
        if tv not in viable:
            return False, "true values are not a viable rational solution", {}
    else:
        Ms, n = witness_mats(ctx, truth["witness"])
        if not laws_hold(ctx, Ms, n) or any(not nonzero_on(d, Ms, n) for d in demands):
            return False, "truth witness fails the laws or a demand", {}
        if pref_level(ctx, Ms) != tl:
            return False, "truth witness level %s != %s" % (pref_level(ctx, Ms), tl), {}
    return True, "ok", info


# ================================================================= Part A: scoring

def decisive_ok(out, key, info):
    ctx = info["ctx"]
    Ms, n = info["last"]
    certs = {(c.get("mention"), c.get("level")): c for c in out.get("certificates", []) or []}
    for i, b in enumerate(key["branches"][:-1]):
        try:
            Q = out["decisive"][i]
        except (KeyError, IndexError):
            return False
        polys = [ctx.expr_poly(q) for q in Q]
        if not polys or any(not nonzero_on(p, Ms, n) for p in polys):
            return False
        if b["level"] == "SUBSUMED":
            if any(all(not zero_at(p, s) for p in polys) for s in info["viable"]):
                return False
        elif b["level"] == "comm":
            if not any(comm_member(ctx, info["G"], info["syms"], p) for p in polys):
                return False
        elif b["level"] == "graded":
            ok = False
            for q, p in zip(Q, polys):
                c = certs.get((q, "graded"))
                if c and cert_ok(ctx, p, c["groups"], "graded"):
                    ok = True
            if not ok:
                return False
    return True


def correct_A(out, key, info):
    lab = out.get("label")
    if lab != key["answer"]:
        return False
    if lab == "DETERMINED":
        if out.get("level") != key["level"]:
            return False
        if key["level"] == "SUBSUMED" and "values" in out:
            tv = [fstr(fr(v)) for v in key["truth"]["values"]]
            return any([fstr(fr(v)) for v in vals] == tv for vals in out["values"])
        return True
    if lab == "FORK":
        if [b.get("level") for b in out.get("branches", [])] != [b["level"] for b in key["branches"]]:
            return False
        return decisive_ok(out, key, info)
    return True


def mcnemar_one_sided(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return sum(comb(n, k) for k in range(b, n + 1)) / 2 ** n


def score_A(worlds, keys, outputs):
    rows, excl = [], {}
    methods = ("procedure", "V1D", "OCC", "FORKALL")
    for wid, world in sorted(worlds.items()):
        key = keys.get(wid)
        if key is None:
            excl[wid] = "no key"
            continue
        try:
            ok, why, info = validate_A(world, key)
        except Exception as ex:
            ok, why, info = False, "%s: %s" % (type(ex).__name__, ex), {}
        if not ok:
            excl[wid] = why
            continue
        row = {"id": wid, "answer": key["answer"], "key_level": key.get("level") or
               "|".join(b["level"] for b in key.get("branches", []))}
        for m in methods:
            out = outputs.get(wid, {}).get(m, {"label": "MISSING"})
            try:
                row[m] = correct_A(out, key, info)
            except Exception as ex:
                row[m] = False
                row[m + "_error"] = "%s: %s" % (type(ex).__name__, ex)
            row[m + "_label"] = out.get("label")
            row[m + "_level"] = out.get("level") or "|".join(b.get("level", "?") for b in out.get("branches", []))
        rows.append(row)
    n = len(rows)
    rep = {"n_total": len(worlds), "n_valid": n, "excluded": excl,
           "void": len(worlds) > 0 and Fraction(len(excl), len(worlds)) > EXCLUSION_CAP}
    for m in methods:
        acc = sum(r[m] for r in rows)
        forks = [r for r in rows if r["answer"] == "FORK"]
        dets = [r for r in rows if r["answer"] == "DETERMINED"]
        rep[m] = {
            "correct": acc, "accuracy": acc / n if n else 0.0,
            "fork_accuracy": sum(r[m] for r in forks) / len(forks) if forks else None,
            "over_claim": sum(r[m + "_label"] == "DETERMINED" for r in forks) / len(forks) if forks else None,
            "over_fork": sum(r[m + "_label"] == "FORK" for r in dets) / len(dets) if dets else None,
            "determined_correct": sum(r[m] for r in dets),
            "contradictions_accepted": sum(r[m + "_label"] in ("DETERMINED", "FORK")
                                           for r in rows if r["answer"] == "CONTRADICTION"),
        }
    best = max(("V1D", "OCC", "FORKALL"), key=lambda m: rep[m]["correct"])
    b = sum(1 for r in rows if r["procedure"] and not r[best])
    c = sum(1 for r in rows if r[best] and not r["procedure"])
    P = rep["procedure"]
    better_det = max(rep["V1D"]["determined_correct"], rep["OCC"]["determined_correct"])
    rep.update({
        "best_baseline": best, "mcnemar_b": b, "mcnemar_c": c, "mcnemar_p": mcnemar_one_sided(b, c),
        "A1": P["accuracy"] >= 0.70,
        "A2": P["fork_accuracy"] is not None and P["fork_accuracy"] >= 0.70,
        "A3": P["over_fork"] is not None and P["over_fork"] <= 0.15,
        "A4": P["determined_correct"] >= better_det - 1,
        "A5": P["contradictions_accepted"] <= 1,
        "per_world": rows,
    })
    if rep["void"]:
        rep["outcome"] = "VOID"
    elif all(rep[k] for k in ("A1", "A2", "A3", "A4", "A5")):
        rep["outcome"] = "PASS"
    elif rep["A1"] and rep["A3"]:
        rep["outcome"] = "PARTIAL"
    else:
        rep["outcome"] = "FAIL"
    return rep


# ================================================================= Part B: independent reference

def dims_of(e, table):
    if e.is_Number:
        return {}
    if e.is_Symbol:
        return dict(table[e.name])
    if e.is_Add:
        ds = [dims_of(a, table) for a in e.args]
        if any(d != ds[0] for d in ds[1:]):
            raise KeyError_("sum of different dimensions")
        return ds[0]
    if e.is_Mul:
        r = {}
        for a in e.args:
            for k, v in dims_of(a, table).items():
                r[k] = r.get(k, 0) + v
        return {k: v for k, v in r.items() if v != 0}
    if e.is_Pow and e.exp.is_Rational:
        return {k: v * fr(e.exp) for k, v in dims_of(e.base, table).items() if v != 0}
    raise KeyError_("unsupported %s" % e)


def reference_B(world):
    qd = {q: {k: fr(v) for k, v in d.items() if fr(v) != 0} for q, d in world["quantities"].items()}
    consts = world.get("constants", {})
    cd = {c: {k: fr(v) for k, v in s.get("dims", {}).items() if fr(v) != 0} for c, s in consts.items()}
    params = {p: sp.Rational(v) for p, v in world.get("parameters", {}).items()}
    u = world["term"]["unknown"]
    names = list(qd) + list(consts) + list(params) + [u]
    for s in world.get("symmetries", []):
        names += list(s.get("params", {}))
    S = {n: sp.Symbol(n) for n in names}
    lhs, rhs = world["law"].split("=")
    y, f = sp.sympify(lhs.strip(), locals=S), sp.sympify(rhs.strip(), locals=S)
    lam = S[u]
    term = sp.sympify(world["term"]["expr"], locals=S)
    h = sp.expand(term / lam)
    if lam in h.free_symbols:
        raise KeyError_("term not linear in the unknown")
    penv = {S[p]: v for p, v in params.items()}
    cenv = {S[c]: sp.Rational(s["value"]) for c, s in consts.items()}
    # exact feasible set
    lo = hi = None
    conflict = None
    constrained = False
    for ob in world.get("observations", []):
        env = {S[k]: sp.Rational(v) for k, v in ob["inputs"].items()}
        env.update(cenv)
        env.update(penv)
        fv, hv = sp.nsimplify(f.subs(env)), sp.nsimplify(h.subs(env))
        if not (fv.is_Rational and hv.is_Rational):
            raise KeyError_("observation not exactly rational")
        r, d, hv = fr(sp.Rational(ob["output"])) - fr(fv), fr(sp.Rational(ob["resolution"])), fr(hv)
        if hv == 0:
            if abs(r) > d and conflict is None:
                conflict = "base law missed beyond resolution"
            continue
        a, b = sorted(((r - d) / hv, (r + d) / hv))
        lo = a if lo is None else max(lo, a)
        hi = b if hi is None else min(hi, b)
        constrained = True
    if conflict is None and constrained and lo > hi:
        conflict = "empty feasible set"
    # exact-zero reasons
    reasons = []
    if world.get("coefficient_form") == "constants":
        table = dict(qd)
        table.update(cd)
        table.update({p: {} for p in params})
        need = dict(dims_of(y, table))
        for k, v in dims_of(h, table).items():
            need[k] = need.get(k, 0) - v
        need = {k: v for k, v in need.items() if v != 0}
        if need:
            base = sorted(set(need) | {k for d in cd.values() for k in d})
            cols = sorted(cd)
            ok = False
            if cols:
                M = sp.Matrix([[sp.Rational(cd[c].get(b, 0).numerator, cd[c].get(b, 0).denominator)
                                if isinstance(cd[c].get(b, 0), Fraction) else 0 for c in cols] for b in base])
                t = sp.Matrix([sp.Rational(need.get(b, 0).numerator, need.get(b, 0).denominator)
                               if isinstance(need.get(b, 0), Fraction) else 0 for b in base])
                ok = M.rank() == M.row_join(t).rank()
            if not ok:
                reasons.append("TYPE_IMPOSSIBLE")
    F = f + lam * h
    for s in world.get("symmetries", []):
        new = {S[q]: sp.sympify(e, locals=S) for q, e in s["map"].items()}
        E = sp.simplify(new.get(y, y).subs(y, F) - F.xreplace({k: v for k, v in new.items() if k != y}))
        if sp.simplify(E.subs(lam, 0)) != 0:
            raise KeyError_("declared symmetry is not a symmetry of the base law")
        if sp.simplify(sp.diff(E, lam)) != 0:
            reasons.append("SYMMETRY_ZERO")
            break
    if params and sp.simplify(h.subs(penv)) == 0 and sp.simplify(h) != 0:
        reasons.append("INCIDENTAL")
    if conflict:
        return {"label": "CONFLICT"}
    detected = constrained and (lo > 0 or hi < 0)
    if reasons:
        return {"label": "CONFLICT"} if detected else {"label": reasons[0]}
    if not constrained:
        return {"label": "UNCONSTRAINED"}
    if detected:
        return {"label": "ACTIVE", "interval": [fstr(lo), fstr(hi)]}
    return {"label": "BOUNDED", "bound": fstr(max(abs(lo), abs(hi))), "interval": [fstr(lo), fstr(hi)]}


def correct_B(out, ref):
    if out.get("label") != ref["label"]:
        return False
    if ref["label"] == "BOUNDED":
        return out.get("bound") is not None and fr(out["bound"]) == fr(ref["bound"])
    if ref["label"] == "ACTIVE" and "interval" in out:
        return [fstr(fr(x)) for x in out["interval"]] == ref["interval"]
    return True


EXACT_ZERO = ("TYPE_IMPOSSIBLE", "SYMMETRY_ZERO", "INCIDENTAL", "ZERO")


def score_B(worlds, keys, outputs):
    rows, excl = [], {}
    methods = ("procedure", "THRESH", "MENTION", "NOSYM")
    for wid, world in sorted(worlds.items()):
        key = keys.get(wid)
        if key is None:
            excl[wid] = "no key"
            continue
        try:
            ref = reference_B(world)
        except Exception as ex:
            excl[wid] = "%s: %s" % (type(ex).__name__, ex)
            continue
        if key.get("class") != ref["label"] or \
                (ref["label"] == "BOUNDED" and fr(key.get("bound", "-1")) != fr(ref["bound"])):
            excl[wid] = "key class %s disagrees with the reference %s" % (key.get("class"), ref)
            continue
        tv = key.get("true_value")
        if tv is not None and ref["label"] in ("BOUNDED", "ACTIVE"):
            lo, hi = (fr(x) for x in ref["interval"])
            if not (lo <= fr(tv) <= hi):
                excl[wid] = "true value outside the feasible interval"
                continue
        row = {"id": wid, "class": ref["label"]}
        for m in methods:
            out = outputs.get(wid, {}).get(m, {"label": "MISSING"})
            row[m] = correct_B(out, ref)
            row[m + "_label"] = out.get("label")
        rows.append(row)
    n = len(rows)
    rep = {"n_total": len(worlds), "n_valid": n, "excluded": excl,
           "void": len(worlds) > 0 and Fraction(len(excl), len(worlds)) > EXCLUSION_CAP}
    classes = sorted({r["class"] for r in rows})
    for m in methods:
        per = {c: [sum(r[m] for r in rows if r["class"] == c), sum(1 for r in rows if r["class"] == c)]
               for c in classes}
        soft = [r for r in rows if r["class"] in ("BOUNDED", "UNCONSTRAINED")]
        conf = [r for r in rows if r["class"] == "CONFLICT"]
        rep[m] = {"correct": sum(r[m] for r in rows), "accuracy": sum(r[m] for r in rows) / n if n else 0.0,
                  "per_class": per,
                  "balanced_accuracy": sum(a / b for a, b in per.values()) / len(per) if per else 0.0,
                  "false_death": sum(r[m + "_label"] in EXACT_ZERO for r in soft) / len(soft) if soft else None,
                  "conflicts_detected": sum(r[m + "_label"] == "CONFLICT" for r in conf) / len(conf) if conf else None}
    P = rep["procedure"]
    rep.update({
        "B1": P["accuracy"] >= 0.80,
        "B2": P["false_death"] is not None and P["false_death"] <= 1 / 6,
        "B3": P["conflicts_detected"] is not None and P["conflicts_detected"] >= 2 / 3,
        "B4": all(P["balanced_accuracy"] > rep[m]["balanced_accuracy"] for m in methods[1:]),
        "per_world": rows,
    })
    rep["outcome"] = "VOID" if rep["void"] else ("PASS" if all(rep[k] for k in ("B1", "B2", "B3", "B4")) else "FAIL")
    return rep


# ================================================================= main

def main(worlds_dir, key_path, out_path, report_path):
    worlds = {}
    for fn in sorted(os.listdir(worlds_dir)):
        if fn.endswith(".json"):
            w = json.load(open(os.path.join(worlds_dir, fn), encoding="utf-8"))
            worlds[w["id"]] = w
    keys = {k["id"]: k for k in json.load(open(key_path, encoding="utf-8"))}
    outputs = json.load(open(out_path, encoding="utf-8"))
    A = {k: w for k, w in worlds.items() if w.get("experiment") == "A"}
    B = {k: w for k, w in worlds.items() if w.get("experiment") == "B"}
    report = {"A": score_A(A, keys, outputs), "B": score_B(B, keys, outputs)}
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1, default=str)
    summary = {part: {k: v for k, v in rep.items() if k != "per_world"} for part, rep in report.items()}
    print(json.dumps(summary, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    if len(sys.argv) == 5:
        main(*sys.argv[1:])
    else:
        print(__doc__)
