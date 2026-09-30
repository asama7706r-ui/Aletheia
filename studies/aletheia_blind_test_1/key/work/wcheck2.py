# E2 world checks (exact sympy evaluation, high-precision numeric comparison).
import json, os, random, keyword, re
import sympy as sp
from wcheck import ROOT, save_world_and_key, update_progress, FORBIDDEN

TOPKEYS = ["id", "experiment", "quantities", "law_original", "filled_law", "symmetries", "ranges",
           "validated", "deficit", "state_original", "state_filled"]


class DimErr(Exception):
    pass


def _norm(d):
    return {k: sp.Rational(v) for k, v in d.items() if sp.Rational(v) != 0}


def dim_expr(e, qd):
    if e.is_Symbol:
        return _norm(qd[e.name])
    if e.is_Number or e is sp.pi:
        return {}
    if e.is_Add:
        ds = [dim_expr(a, qd) for a in e.args]
        for d in ds[1:]:
            if d != ds[0]:
                raise DimErr("add")
        return ds[0]
    if e.is_Mul:
        out = {}
        for a in e.args:
            for k, v in dim_expr(a, qd).items():
                out[k] = out.get(k, 0) + v
        return _norm(out)
    if e.is_Pow:
        b, x = e.args
        if dim_expr(x, qd) != {}:
            raise DimErr("exponent dims")
        db = dim_expr(b, qd)
        if db and not x.is_Number:
            raise DimErr("symbolic exponent on dimensional base")
        return _norm({k: v * x for k, v in db.items()})
    if isinstance(e, sp.Function):
        for a in e.args:
            if dim_expr(a, qd) != {}:
                raise DimErr("function of dimensional argument")
        return {}
    raise DimErr("unknown node " + str(type(e)))


def syms_for(world, extra_names=()):
    names = list(world["quantities"]) + list(extra_names)
    return {n: sp.Symbol(n, real=True) for n in names}


def parse_law(s, loc):
    lhs, rhs = s.split("=")
    lhs = lhs.strip()
    return lhs, sp.sympify(rhs, locals=loc)


def law_dims_ok(world, law, loc):
    out, rhs = parse_law(law, loc)
    try:
        return dim_expr(rhs, world["quantities"]) == _norm(world["quantities"][out])
    except DimErr:
        return False


def evalf(expr, vals):
    v = expr.subs({sp.Symbol(k, real=True): sp.Rational(x) for k, x in vals.items()})
    return sp.N(v, 50)


def close(a, b, tol):
    a, b = complex(a), complex(b)
    return abs(a - b) <= tol


def sym_params(sym):
    return sym.get("params", {})


def check_symmetry(world, law, sym, loc, rng, trials=12):
    """True if the law is invariant under the map: (x, y) on the law -> mapped (x', y') on the law."""
    out, rhs = parse_law(law, loc)
    inputs = sorted(s.name for s in rhs.free_symbols)
    ranges = world.get("ranges", {})
    ploc = dict(loc)
    for p in sym_params(sym):
        ploc[p] = sp.Symbol(p, real=True)
    maps = {q: sp.sympify(e, locals=ploc) for q, e in sym["map"].items()}
    for _ in range(trials):
        vals = {}
        for q in inputs:
            lo, hi = [sp.Rational(z) for z in ranges.get(q, ["1/2", "3"])]
            vals[q] = lo + (hi - lo) * sp.Rational(rng.randint(0, 1000), 1000)
        for p, (lo, hi) in sym_params(sym).items():
            lo, hi = sp.Rational(lo), sp.Rational(hi)
            vals[p] = lo + (hi - lo) * sp.Rational(rng.randint(0, 1000), 1000)
        subs = {sp.Symbol(k, real=True): v for k, v in vals.items()}
        y = sp.nsimplify(rhs.subs(subs)) if False else rhs.subs(subs)
        subs_y = dict(subs)
        subs_y[sp.Symbol(out, real=True)] = y
        newvals = dict(subs)
        for q, e in maps.items():
            if q != out:
                newvals[sp.Symbol(q, real=True)] = e.subs(subs_y)
        y_new = maps[out].subs(subs_y) if out in maps else y
        lhs_new = rhs.subs(newvals)
        if not close(sp.N(lhs_new, 40), sp.N(y_new, 40), 1e-20 * (1 + abs(complex(sp.N(y_new, 20))))):
            return False
    return True


def check_E2(world, key, extra=None):
    extra = extra or {}
    errs = []
    rng = random.Random(777)
    if [k for k in world if k not in TOPKEYS] or any(k not in world for k in TOPKEYS if k != "ranges"):
        errs.append("world fields")
    if world.get("experiment") != "E2":
        errs.append("experiment")
    for q in world["quantities"]:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", q) or keyword.iskeyword(q) or q in FORBIDDEN or q in ("M", "L", "T"):
            errs.append("bad quantity name " + q)
    loc = syms_for(world)
    out0, rhs0 = parse_law(world["law_original"], loc)
    out1, rhs1 = parse_law(world["filled_law"], loc)
    if out0 != out1 or out0 not in world["quantities"]:
        errs.append("output symbol")
    used = {s.name for s in rhs0.free_symbols | rhs1.free_symbols} | {out0}
    if used != set(world["quantities"]):
        errs.append("quantities list != symbols of the laws")
    if out0 in {s.name for s in rhs0.free_symbols | rhs1.free_symbols}:
        errs.append("output appears on the right")
    orig_syms = {s.name for s in rhs0.free_symbols} | {out0}
    inputs_all = sorted(used - {out0})
    # symmetry maps: only quantities of the (original) law and declared params
    for sym in world["symmetries"]:
        allowed = orig_syms | set(sym_params(sym))
        for q, e in sym["map"].items():
            if q not in orig_syms:
                errs.append("map key outside original law")
            fs = {s.name for s in sp.sympify(e, locals={**loc, **{p: sp.Symbol(p, real=True) for p in sym_params(sym)}}).free_symbols}
            if not fs <= allowed:
                errs.append("map uses disallowed symbols")
        for p in sym_params(sym):
            if p in world["quantities"]:
                errs.append("symmetry param collides with a quantity")
    # validated points and deficit
    for pt in world["validated"] + [world["deficit"]]:
        if set(pt["inputs"]) != set(inputs_all):
            errs.append("point does not list every quantity")
    orig_ok = law_dims_ok(world, world["law_original"], loc)
    fill_ok = law_dims_ok(world, world["filled_law"], loc)
    if not orig_ok:
        errs.append("original law dimensionally inconsistent")
    for pt in world["validated"]:
        if not close(evalf(rhs0, pt["inputs"]), sp.Rational(pt["output"]), float(pt["tol"])):
            errs.append("original law misses a validated point")
    d = world["deficit"]
    if close(evalf(rhs0, d["inputs"]), sp.Rational(d["output"]), float(d["tol"])):
        errs.append("original law fits the deficit point")
    if not close(evalf(rhs1, d["inputs"]), sp.Rational(d["output"]), float(d["tol"])):
        errs.append("filled law misses the deficit point")
    for sym in world["symmetries"]:
        if not check_symmetry(world, world["law_original"], sym, loc, rng):
            errs.append("listed symmetry is not a symmetry of the original law")
    # card signals for the filled law
    fits_val = all(close(evalf(rhs1, pt["inputs"]), sp.Rational(pt["output"]), float(pt["tol"])) for pt in world["validated"])
    keeps_sym = all(check_symmetry(world, world["filled_law"], sym, loc, rng) for sym in world["symmetries"])
    so, sf_ = world["state_original"], world["state_filled"]
    state_super = set(so) <= set(sf_)
    signals = {"validated": not fits_val, "symmetry": not keeps_sym, "state": not state_super}
    lab = key["label"]
    if set(key) != {"id", "label", "detectable_by_card", "notes"}:
        errs.append("key fields")
    if lab == "SAME_LAW_NEW_STATE":
        if not fill_ok or any(signals.values()) or not (set(so) < set(sf_)):
            errs.append("SAME: filled law not consistent with the card")
        if key["detectable_by_card"] is not True:
            errs.append("SAME flag")
    elif lab == "ANOTHER_LAW":
        if not fill_ok:
            errs.append("ANOTHER: filled law must be dimensionally consistent")
        if key["detectable_by_card"] and not any(signals.values()):
            errs.append("ANOTHER detectable: no card signal")
        if not key["detectable_by_card"] and any(signals.values()):
            errs.append("ANOTHER undetectable: a card signal exists")
    elif lab == "INVALID":
        if fill_ok:
            errs.append("INVALID: filled law is dimensionally consistent")
    else:
        errs.append("label")
    # extra: natural (possibly unlisted) symmetries, with new quantities transformed
    for sym in extra.get("natural_keep", []):
        if not (check_symmetry(world, world["law_original"], sym, syms_for(world, sym_params(sym)), rng)
                and check_symmetry(world, world["filled_law"], sym, syms_for(world, sym_params(sym)), rng)):
            errs.append("natural symmetry not kept: " + sym["name"])
    for sym in extra.get("hidden_break", []):
        lc = syms_for(world, sym_params(sym))
        if not check_symmetry(world, world["law_original"], sym, lc, rng) or check_symmetry(world, world["filled_law"], sym, lc, rng):
            errs.append("hidden symmetry claim fails: " + sym["name"])
    return errs, signals
