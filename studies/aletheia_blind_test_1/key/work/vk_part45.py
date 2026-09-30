

# ------------------------------------------------------------------ E2 checks
E2_FIELDS = ["id", "experiment", "quantities", "law_original", "filled_law", "symmetries", "ranges",
             "validated", "deficit", "state_original", "state_filled"]


def e2_parse(world, text, extra=()):
    import sympy as sp
    loc = {q: sp.Symbol(q, real=True) for q in list(world["quantities"]) + list(extra)}
    out, rhs = text.split("=")
    return out.strip(), sp.sympify(rhs, locals=loc)


def e2_dims(expr, qd):
    import sympy as sp

    def nz(d):
        return {k: v for k, v in d.items() if v != 0}
    if expr.is_Symbol:
        return nz({k: sp.Rational(v) for k, v in qd[expr.name].items()})
    if expr.is_Number:
        return {}
    if expr.is_Add:
        ds = [e2_dims(a, qd) for a in expr.args]
        if any(d is None or d != ds[0] for d in ds):
            return None
        return ds[0]
    if expr.is_Mul:
        acc = {}
        for a in expr.args:
            d = e2_dims(a, qd)
            if d is None:
                return None
            for k, v in d.items():
                acc[k] = acc.get(k, 0) + v
        return nz(acc)
    if expr.is_Pow:
        b, x = expr.args
        db = e2_dims(b, qd)
        if db is None or e2_dims(x, qd) != {} or (db and not x.is_Number):
            return None
        return nz({k: v * x for k, v in db.items()})
    if expr.is_Function:
        return {} if all(e2_dims(a, qd) == {} for a in expr.args) else None
    return None


def e2_consistent(world, law):
    import sympy as sp
    out, rhs = e2_parse(world, law)
    d = e2_dims(rhs, world["quantities"])
    want = {k: sp.Rational(v) for k, v in world["quantities"][out].items() if v != 0}
    return d is not None and d == want


def e2_val(expr, vals):
    import sympy as sp
    return complex(sp.N(expr.subs({sp.Symbol(k, real=True): sp.Rational(v) for k, v in vals.items()}), 40))


def e2_fits(world, law, point):
    out, rhs = e2_parse(world, law)
    return abs(e2_val(rhs, point["inputs"]) - complex(Fr(point["output"]))) <= float(point["tol"])


def e2_symmetric(world, law, sym, seed=11, trials=10):
    import sympy as sp
    params = sym.get("params", {})
    out, rhs = e2_parse(world, law, params)
    loc = {q: sp.Symbol(q, real=True) for q in list(world["quantities"]) + list(params)}
    maps = {q: sp.sympify(x, locals=loc) for q, x in sym["map"].items()}
    rng = random.Random(seed)
    rngs = world.get("ranges", {})
    for _ in range(trials):
        vals = {}
        for s in sorted(rhs.free_symbols, key=str):
            lo, hi = (Fr(z) for z in rngs.get(s.name, ["1/2", "3"]))
            vals[s] = sp.Rational(str(lo + (hi - lo) * Fr(rng.randint(0, 997), 997)))
        for p, (lo, hi) in params.items():
            lo, hi = Fr(lo), Fr(hi)
            vals[loc[p]] = sp.Rational(str(lo + (hi - lo) * Fr(rng.randint(0, 997), 997)))
        y = rhs.subs(vals)
        full = dict(vals)
        full[loc[out]] = y
        new = dict(vals)
        for q, x in maps.items():
            if q != out:
                new[loc[q]] = x.subs(full)
        y2 = maps[out].subs(full) if out in maps else y
        a, b = complex(sp.N(rhs.subs(new), 40)), complex(sp.N(y2, 40))
        if abs(a - b) > 1e-25 * (1 + abs(b)):
            return False
    return True


def check_E2_entry(world, key, spec):
    import sympy as sp
    e = []
    if [k for k in world if k not in E2_FIELDS] or any(k not in world for k in E2_FIELDS if k != "ranges"):
        e.append("world fields")
    if set(key) != {"id", "label", "detectable_by_card", "notes"}:
        e.append("key fields")
    for q in world["quantities"]:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", q) or q in FORBIDDEN or keyword.iskeyword(q) or hasattr(sp, q):
            e.append("quantity name " + q)
    o0, r0 = e2_parse(world, world["law_original"])
    o1, r1 = e2_parse(world, world["filled_law"])
    if o0 != o1:
        e.append("different output symbols")
    syms = {s.name for s in r0.free_symbols | r1.free_symbols}
    if syms | {o0} != set(world["quantities"]) or o0 in syms:
        e.append("quantities do not match the laws")
    law_syms = {s.name for s in r0.free_symbols} | {o0}
    for sym in world["symmetries"]:
        params = sym.get("params", {})
        loc = {q: sp.Symbol(q) for q in list(world["quantities"]) + list(params)}
        for q, x in sym["map"].items():
            if q not in law_syms or not {s.name for s in sp.sympify(x, locals=loc).free_symbols} <= law_syms | set(params):
                e.append("symmetry map uses symbols outside the law and its parameters")
    for p in world["validated"] + [world["deficit"]]:
        if set(p["inputs"]) != syms:
            e.append("a point does not list every quantity of both laws")
    if not e2_consistent(world, world["law_original"]):
        e.append("original law dimensionally inconsistent")
    if not all(e2_fits(world, world["law_original"], p) for p in world["validated"]):
        e.append("original law misses a validated point")
    if e2_fits(world, world["law_original"], world["deficit"]):
        e.append("original law fits the deficit point")
    if not e2_fits(world, world["filled_law"], world["deficit"]):
        e.append("filled law misses the deficit point")
    for sym in world["symmetries"]:
        if not e2_symmetric(world, world["law_original"], sym):
            e.append("listed symmetry does not hold for the original law")
    sig_val = not all(e2_fits(world, world["filled_law"], p) for p in world["validated"])
    sig_sym = not all(e2_symmetric(world, world["filled_law"], s) for s in world["symmetries"])
    sig_state = not set(world["state_original"]) <= set(world["state_filled"])
    cons = e2_consistent(world, world["filled_law"])
    lab, det = key["label"], key["detectable_by_card"]
    if lab == "SAME_LAW_NEW_STATE":
        if not cons or sig_val or sig_sym or sig_state or set(world["state_original"]) == set(world["state_filled"]):
            e.append("SAME_LAW_NEW_STATE not supported by the card")
    elif lab == "ANOTHER_LAW":
        if not cons:
            e.append("ANOTHER_LAW must be dimensionally consistent")
        if det and not (sig_val or sig_sym or sig_state):
            e.append("detectable ANOTHER_LAW without a card signal")
        if not det and (sig_val or sig_sym or sig_state):
            e.append("undetectable ANOTHER_LAW shows a card signal")
    elif lab == "INVALID":
        if cons:
            e.append("INVALID filled law is dimensionally consistent")
    else:
        e.append("label")
    ex = spec["E2_extra"].get(world["id"], {})
    for s in ex.get("natural_keep", []):
        if not (e2_symmetric(world, world["law_original"], s) and e2_symmetric(world, world["filled_law"], s)):
            e.append("natural symmetry not kept: " + s["name"])
    for s in ex.get("hidden_break", []):
        if not e2_symmetric(world, world["law_original"], s) or e2_symmetric(world, world["filled_law"], s):
            e.append("hidden symmetry-break claim fails: " + s["name"])
    info = "card signals: validated=%s symmetry=%s state=%s; filled dims consistent=%s" % (sig_val, sig_sym, sig_state, cons)
    return e, info


# ------------------------------------------------------------------ main
def main():
    kfile = sys.argv[1] if len(sys.argv) > 1 else os.path.join(KEYDIR, "key.json")
    if not os.path.exists(kfile):
        kfile = os.path.join(KEYDIR, "key_draft.jsonl")
    if kfile.endswith(".jsonl"):
        keys = [json.loads(l) for l in open(kfile, encoding="utf-8") if l.strip()]
    else:
        keys = json.load(open(kfile, encoding="utf-8"))
    spec = json.load(open(os.path.join(KEYDIR, "verify_spec.json"), encoding="utf-8"))
    report, nfail = [], 0
    report.append("key file: " + os.path.basename(kfile))
    ids = [k["id"] for k in keys]
    expect = ["E1-%02d" % i for i in range(1, 29)] + ["E2-%02d" % i for i in range(1, 17)]
    if sorted(ids) != expect:
        report.append("FAIL: key ids are not exactly E1-01..E1-28, E2-01..E2-16")
        nfail += 1
    wfiles = sorted(f[:-5] for f in os.listdir(WORLDDIR) if f.endswith(".json"))
    if wfiles != expect:
        report.append("FAIL: world files are not exactly the 44 expected ids")
        nfail += 1
    for k in keys:
        world = json.load(open(os.path.join(WORLDDIR, k["id"] + ".json"), encoding="utf-8"))
        if world.get("id") != k["id"]:
            errs, info = ["world id mismatch"], ""
        elif k["id"].startswith("E1-"):
            try:
                errs, info = check_E1_entry(world, k, spec)
            except Exception as ex:
                errs, info = ["exception %r" % ex], ""
        else:
            try:
                errs, info = check_E2_entry(world, k, spec)
            except Exception as ex:
                errs, info = ["exception %r" % ex], ""
        tag = k["label"] + (":" + k["true_family"] if k["label"] == "NEW_KIND" else "")
        if errs:
            nfail += 1
            report.append("%s [%s] FAIL: %s" % (k["id"], tag, "; ".join(errs)))
        else:
            report.append("%s [%s] OK: %s" % (k["id"], tag, info))
    from collections import Counter
    e1 = [k for k in keys if k["id"].startswith("E1-")]
    e2 = [k for k in keys if k["id"].startswith("E2-")]
    wl = {k["id"]: json.load(open(os.path.join(WORLDDIR, k["id"] + ".json"), encoding="utf-8")) for k in keys}
    c1 = Counter(k["label"] + (":" + k["true_family"] if k["label"] == "NEW_KIND" else "") for k in e1)
    want1 = {"SUBSUMED": 6, "NEW_KIND:comm": 4, "NEW_KIND:graded": 5, "NEW_KIND:assoc": 5, "CONTRADICTION": 4, "UNDERDETERMINED": 4}
    comp = []
    if dict(c1) != want1:
        comp.append("E1 label/family counts %s" % dict(c1))
    if sum(1 for k in e1 if k["label"] == "SUBSUMED" and wl[k["id"]].get("parameters")) != 1:
        comp.append("need exactly one SUBSUMED world with a parameter")
    if sum(1 for k in e1 if k["label"] == "NEW_KIND" and wl[k["id"]].get("parameters")) != 1:
        comp.append("need exactly one NEW_KIND world with a parameter")
    unfam = sum(1 for k in e1 if k["label"] == "NEW_KIND" and "outside the familiar list" in k["category"])
    if unfam * 3 < 14:
        comp.append("fewer than one third of NEW_KIND worlds outside the familiar list")
    c2 = Counter(k["label"] for k in e2)
    if dict(c2) != {"SAME_LAW_NEW_STATE": 6, "ANOTHER_LAW": 7, "INVALID": 3}:
        comp.append("E2 label counts %s" % dict(c2))
    if sum(1 for k in e2 if k["label"] == "ANOTHER_LAW" and not k["detectable_by_card"]) < 2:
        comp.append("fewer than 2 undetectable ANOTHER_LAW worlds")
    if comp:
        nfail += 1
        report.append("COMPOSITION FAIL: " + "; ".join(comp))
    else:
        report.append("COMPOSITION OK: E1 %s; NEW_KIND outside familiar list: %d/14; E2 %s; undetectable ANOTHER_LAW: %d"
                      % (dict(sorted(c1.items())), unfam, dict(sorted(c2.items())),
                         sum(1 for k in e2 if k["label"] == "ANOTHER_LAW" and not k["detectable_by_card"])))
    report.append("SUMMARY: %d worlds checked, %d failing items" % (len(keys), nfail))
    with open(os.path.join(KEYDIR, "verify_output.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(report) + "\n")
    print(report[-1])
    return 0 if nfail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
