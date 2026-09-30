# E1 world checks. Success output is deliberately opaque (no labels, no families).
import json, keyword, re, os, time, random
from fractions import Fraction as F
import sympy as sp
from wcore import *
from wideal import TruncIdeal, family_relations
from wrat import eval_comm, rational_points, radical_kills, grid_points, GRID_USER

ROOT = r"C:\Users\HP\AppData\Local\Temp\claude\aletheia_blind_test_1"
BUDGET = {1: 9, 2: 7, 3: 5, 4: 4}
FAM_ORDER = ["comm", "graded", "assoc"]
PARAM_GRID = [F(-3), F(-2), F(-1), F(0), F(1), F(2), F(3), F(1, 2)]
ALLOWED_VALUES = {F(k) for k in range(-3, 4)} | {F(1, 2), F(-1, 2)}


def check_format_E1(world):
    errs = []
    allowed = {"id", "experiment", "generators", "variables", "parameters", "laws"}
    if set(world) - allowed:
        errs.append("extra fields")
    for k in ("id", "experiment", "generators", "laws"):
        if k not in world:
            errs.append("missing " + k)
    if world.get("experiment") != "E1":
        errs.append("experiment field")
    gens = world["generators"]
    if not 1 <= len(gens) <= 4:
        errs.append("generator count")
    names = [g["name"] for g in gens] + world.get("variables", []) + world.get("parameters", [])
    if len(set(names)) != len(names):
        errs.append("duplicate names")
    for nm in names:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", nm) or keyword.iskeyword(nm) or nm in FORBIDDEN or hasattr(sp, nm):
            errs.append("bad name " + nm)
    for g in gens:
        if set(g) != {"name", "grade"} or g["grade"] not in (0, 1):
            errs.append("bad generator entry")
    text = " ".join(world["laws"])
    for law in world["laws"]:
        if law.count("=") != 1 or "==" in law:
            errs.append("law needs exactly one '='")
        if re.search(r"\d\.\d|\.\d|\d\.", law):
            errs.append("decimal in law")
        for m in re.finditer(r"/", law):
            rest = law[m.end():].lstrip()
            if not re.match(r"\d+", rest):
                errs.append("division by non-integer-constant")
        for m in re.finditer(r"\*\*\s*([^\s\)\*\+\-/,]+)", law):
            if not re.fullmatch(r"\d+", m.group(1)) or int(m.group(1)) < 1:
                errs.append("bad exponent")
    for nm in names:
        if not re.search(r"(?<![A-Za-z0-9_])" + re.escape(nm) + r"(?![A-Za-z0-9_])", text):
            errs.append("declared but unused " + nm)
    try:
        d = max_degree(world)
        if d > BUDGET.get(len(gens), 0):
            errs.append("degree budget %d" % d)
    except Exception as ex:
        errs.append("parse error " + repr(ex))
    return errs


def ideal_contains_any(n, rels, targets, dmin, dmax):
    """Smallest D in [dmin,dmax] at which 1 or some target lies in the truncated ideal."""
    for D in range(dmin, dmax + 1):
        T = TruncIdeal(n, rels, D)
        if T.contradiction:
            return ("ONE", D)
        for i, t in enumerate(targets):
            if T.contains(t):
                return (i, D)
    return None


def presented_dim(n, rels, dmin, dmax, target=None):
    for D in range(dmin, dmax + 1):
        T = TruncIdeal(n, rels, D)
        ub = T.dim_upper_bound()
        if ub is not None and (target is None or ub <= target):
            return ub, D
    return None, None


def stricter(fam):
    return FAM_ORDER[: FAM_ORDER.index(fam)]


def check_newkind_core(world, witness, pvals, true_family, true_dim, observed, roles, dmax_extra=4, check_complete=False):
    errs, info = [], {}
    gens = world["generators"]
    n = len(gens)
    grades = [g["grade"] for g in gens]
    mats = witness_list(world, witness)
    size = len(mats[0])
    if any(len(M) != size or any(len(r) != size for r in M) for M in mats):
        errs.append("witness shapes")
        return errs, info
    rels = relations(world, pvals)
    ev = MatEval(mats)
    for i, r in enumerate(rels):
        if not iszero(ev.poly(r)):
            errs.append("law relation %d fails on witness" % i)
    # random sampling of the universally quantified variables (in addition to the exact test)
    polys, vsyms, psyms = world_polys(world)
    rng = random.Random(12345)
    psubs = {p: sp.Rational(str(pvals[p.name])) for p in psyms} if psyms else {}
    for trial in range(4 if vsyms else 1):
        vs = {v: sp.Rational(rng.randint(-9, 9), rng.randint(1, 5)) for v in vsyms}
        for li, poly in enumerate(polys):
            acc = mzero(size)
            for w, c in poly.items():
                cv = sp.Rational(sp.sympify(c).subs(psubs).subs(vs))
                if cv != 0:
                    acc = madd(acc, ev.word(w), F(int(cv.p), int(cv.q)))
            if not iszero(acc):
                errs.append("law %d fails at sampled variables" % li)
    fam = family_of(mats, grades)
    if fam != true_family:
        errs.append("family mismatch")
    dim = algebra_dim(mats)
    if dim != true_dim:
        errs.append("dim mismatch %d" % dim)
    obs = [expr_poly(world, q) for q in observed]
    rolep = [expr_poly(world, q) for q in roles]
    for q, p in zip(observed, obs):
        if iszero(ev.poly(p)):
            errs.append("observed quantity vanishes in T")
    if not set(roles) <= set(observed):
        errs.append("roles not subset of observed")
    dmin = max(max_degree(world), 2)
    # identifiability (a): every stricter family kills an observed quantity (formally) and a role (strongly)
    for fz in stricter(true_family):
        fr_ = family_relations(grades, fz)
        formal = ideal_contains_any(n, fr_, obs, 2, 3)
        strong = ideal_contains_any(n, rels + fr_, rolep, dmin, dmin + dmax_extra)
        if formal is None and strong is None:
            errs.append("(a) not shown for a stricter family")
        if strong is None:
            errs.append("(a-strong) no role killed in a stricter family")
        info["a_" + fz] = (formal, strong)
    # identifiability (b): no rational point with all observed nonzero
    commrels = family_relations(grades, "comm")
    formal_b = ideal_contains_any(n, commrels, obs, 2, 3)
    strong_b = ideal_contains_any(n, rels + commrels, rolep, dmin, dmin + dmax_extra) if true_family != "comm" else None
    pts = None
    if strong_b is None:
        pts = rational_points(rels, n)
        if pts == "POSDIM":
            if not radical_kills(rels, n, rolep):
                errs.append("(b) positive-dimensional rational set not handled")
        else:
            for pt in pts:
                if all(eval_comm(q, pt) != 0 for q in rolep):
                    errs.append("(b-strong) rational point keeps all roles")
                if all(eval_comm(q, pt) != 0 for q in obs):
                    errs.append("(b) rational point keeps all observed")
    info["b"] = (formal_b, strong_b, None if pts is None else ("POSDIM" if pts == "POSDIM" else len(pts)))
    hits = grid_points(rels, n, obs)
    if hits:
        errs.append("(b) grid hit")
    if check_complete:
        fr_ = family_relations(grades, true_family)
        ub, D = presented_dim(n, rels + fr_, dmin, dmin + dmax_extra + 2, target=true_dim)
        info["complete"] = (ub, D)
        if ub != true_dim:
            errs.append("completeness not verified (ub=%s)" % ub)
    return errs, info


def check_E1(world, key, extra=None):
    extra = extra or {}
    errs = check_format_E1(world)
    label = key["label"]
    params = world.get("parameters", [])
    pvals = key.get("true_parameter_values")
    if params and label != "UNDERDETERMINED":
        if not pvals or set(pvals) != set(params):
            errs.append("true_parameter_values missing")
    base = {"id", "label", "category", "notes"}
    need = {
        "NEW_KIND": base | {"true_family", "true_dim", "witness", "observed_nonzero", "complete_presentation"},
        "SUBSUMED": base | {"true_values", "observed_nonzero"},
        "CONTRADICTION": base,
        "UNDERDETERMINED": base,
    }[label]
    if params and label != "UNDERDETERMINED":
        need = need | {"true_parameter_values"}
    if set(key) != need:
        errs.append("key fields %s" % sorted(set(key) ^ need))
    if key["id"] != world["id"]:
        errs.append("id mismatch")
    info = {}
    n = len(world["generators"])
    if label == "NEW_KIND":
        e, info = check_newkind_core(world, key["witness"], pvals, key["true_family"], key["true_dim"],
                                     key["observed_nonzero"], extra.get("roles", []),
                                     check_complete=key["complete_presentation"])
        errs += e
        if params:
            for c in PARAM_GRID:
                ev = extra["param_evidence"][fstr(c)]
                e2, _ = check_newkind_core(world, ev["witness"], {params[0]: fstr(c)}, key["true_family"],
                                           ev["dim"], key["observed_nonzero"], extra.get("roles", []))
                if e2:
                    errs.append("parameter value %s changes the decision: %s" % (fstr(c), e2[:2]))
    elif label == "SUBSUMED":
        vals = [fr(key["true_values"][g["name"]]) for g in world["generators"]]
        if any(v not in ALLOWED_VALUES for v in vals):
            errs.append("value outside allowed set")
        obs = [expr_poly(world, q) for q in key["observed_nonzero"]]
        cs = [None] if not params else [fr(pvals[params[0]])] + PARAM_GRID
        for c in cs:
            pv = None if c is None else {params[0]: fstr(c)}
            rels = relations(world, pv)
            if any(eval_comm(r, vals) != 0 for r in rels):
                errs.append("laws fail at true values (param %s)" % c)
            if any(eval_comm(q, vals) == 0 for q in obs):
                errs.append("observed vanish at true values (param %s)" % c)
        info["ratpts"] = rational_points(relations(world, pvals), n)
    elif label == "CONTRADICTION":
        rels = relations(world, pvals)
        dmin = max(max_degree(world), 2)
        got = None
        for D in range(dmin, dmin + extra.get("dextra", 5) + 1):
            if TruncIdeal(n, rels, D).contradiction:
                got = D
                break
        if got is None:
            errs.append("1 not derived in the truncated ideal")
        info["D"] = got
        # each law alone (and each leave-one-out subset, when a model is supplied) has a nonzero model
        for li in range(len(world["laws"])):
            sub = dict(world)
            sub["laws"] = [world["laws"][li]]
            if not model_exists(sub, pvals, extra.get("single_models", {}).get(li)):
                errs.append("law %d alone has no model found" % li)
        for li, wit in extra.get("loo_models", {}).items():
            sub = dict(world)
            sub["laws"] = [l for k, l in enumerate(world["laws"]) if k != li]
            if not model_exists(sub, pvals, wit):
                errs.append("leave-one-out %d model fails" % li)
    elif label == "UNDERDETERMINED":
        errs += check_und(world, extra)
    return errs, info


def model_exists(world, pvals, wit=None):
    n = len(world["generators"])
    rels = relations(world, pvals)
    if wit == "GB":
        # a single relation whose leading word has no self-overlap is a Groebner basis,
        # so 1 is not in the ideal (e.g. the Weyl relation p*x - x*p = 1)
        if len(rels) != 1:
            return False
        from wideal import dkey
        lw = max(rels[0], key=dkey)
        return len(lw) > 0 and all(lw[-k:] != lw[:k] for k in range(1, len(lw)))
    if wit is not None:
        mats = witness_list(world, wit)
        ev = MatEval(mats)
        return all(iszero(ev.poly(r)) for r in rels) and len(mats[0]) > 0
    for vals in itertools.product(GRID_USER, repeat=n):
        if all(eval_comm(r, vals) == 0 for r in rels):
            return True
    return False


def check_und(world, extra):
    errs = []
    params = world.get("parameters", [])
    if len(params) != 1:
        return ["UNDERDETERMINED needs one parameter"]
    p = params[0]
    n = len(world["generators"])
    roles = extra.get("roles", [])
    rolep = [expr_poly(world, q) for q in roles]
    decisions = {}
    for c in PARAM_GRID:
        ev = extra["und"][fstr(c)]
        pv = {p: fstr(c)}
        rels = relations(world, pv)
        d = ev["decision"]
        if d == "SUBSUMED":
            vals = [fr(ev["point"][g["name"]]) for g in world["generators"]]
            if any(eval_comm(r, vals) != 0 for r in rels) or any(eval_comm(q, vals) == 0 for q in rolep):
                errs.append("UND %s: subsumed evidence fails" % fstr(c))
        elif d == "CONTRADICTION":
            dmin = max(max_degree(world), 2)
            if not any(TruncIdeal(n, rels, D).contradiction for D in range(dmin, dmin + 6)):
                errs.append("UND %s: contradiction not derived" % fstr(c))
        elif d.startswith("NEW_KIND"):
            fam = d.split(":")[1]
            e2, _ = check_newkind_core(world, ev["witness"], pv, fam, ev["dim"], ev["observed"], roles)
            if e2:
                errs.append("UND %s: new-kind evidence fails %s" % (fstr(c), e2[:3]))
        decisions[fstr(c)] = d
    if len(set(decisions.values())) < 2:
        errs.append("UND: decision does not change on the grid")
    return errs


# ---------------- saving and progress ----------------
def save_world_and_key(world, key):
    wpath = os.path.join(ROOT, "worlds", world["id"] + ".json")
    with open(wpath, "w", encoding="utf-8") as f:
        json.dump(world, f, indent=2, ensure_ascii=True)
        f.write("\n")
    kpath = os.path.join(ROOT, "key", "key_draft.jsonl")
    lines = []
    if os.path.exists(kpath):
        with open(kpath, encoding="utf-8") as f:
            lines = [l for l in f.read().splitlines() if l.strip()]
    lines = [l for l in lines if json.loads(l)["id"] != key["id"]]
    lines.append(json.dumps(key, ensure_ascii=True))
    with open(kpath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def update_progress(step, replacements=0):
    kpath = os.path.join(ROOT, "key", "key_draft.jsonl")
    ids = []
    if os.path.exists(kpath):
        with open(kpath, encoding="utf-8") as f:
            ids = [json.loads(l)["id"] for l in f.read().splitlines() if l.strip()]
    e1 = sum(1 for i in ids if i.startswith("E1-"))
    e2 = sum(1 for i in ids if i.startswith("E2-"))
    line = "E1: %d/28 verified; E2: %d/16 verified; replacements so far: %d; step: %s; updated %s" % (
        e1, e2, replacements, step, time.strftime("%H:%M"))
    with open(os.path.join(ROOT, "progress.txt"), "w", encoding="utf-8") as f:
        f.write(line + "\n")
    return line
