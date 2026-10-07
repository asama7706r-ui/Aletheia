# Test 4 dev tool: random worlds, procedure vs independent reference.
#   python fuzz_compare.py [n_worlds] [seed]
# Each random world is built from random quantities, meanings, cards, bodies and observations. Worlds the
# reference rejects (V1-V13) are skipped and counted. For every valid filler the procedure's full card must
# pass the scorer's correctness check (protocol 8.1), and every baseline verdict and the zero-effect report
# must equal the reference. This is a consistency check between two independent implementations, not evidence.
import json
import os
import random
import sys
import time
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "procedure"))
sys.path.insert(0, os.path.join(ROOT, "scorer"))
import procedure_v4 as P  # noqa: E402
import ref_v4 as R  # noqa: E402

REGRAW = json.load(open(os.path.join(ROOT, "registry", "registry.json"), encoding="utf-8"))
MEAN = {m["id"]: m for m in REGRAW["meanings"]}
UNIT = {i["id"]: i["unit"] for i in REGRAW["instruments"]}
FIXED_DIMS = {"m13": {"L": 1, "T": -1}, "m14": {"L": 1, "T": -2}, "m15": {"M": 1, "L": 1, "T": -1}}
SCALARS = ["m01", "m02", "m03", "m04", "m05", "m06", "m07", "m08", "m09", "m10", "m11"]
VECTORS = ["m12", "m13", "m14", "m15", "m16", "m17", "m18", "m19", "m20", "m21", "m22"]
SEED_DIMS = [{}, {"L": 1}, {"M": 1}, {"Q": 1}, {"T": -1}, {"M": 1, "L": 2, "T": -1}, {"L": 1, "T": -2}]


def mdims(m, rng):
    a = MEAN[m]["anchor"]
    if "instrument" in a:
        return dict(UNIT[a["instrument"]])
    if m in FIXED_DIMS:
        return dict(FIXED_DIMS[m])
    return dict(rng.choice(SEED_DIMS))


def dadd(a, b, s=1):
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, 0) + s * v
    return {k: v for k, v in out.items() if v != 0}


def card(m):
    return dict(MEAN[m]["under"])


def make_world(rng, idx):
    names = iter(["a%d" % i for i in range(10, 99)])
    qs, factors = [], []          # factors: (name, dims)
    bodies = []
    # bodies: sometimes a pair of identical bodies with partner quantities
    if rng.random() < 0.4:
        bodies = [("ba", "ty01"), ("bb", "ty01")]
        m = rng.choice(["m04", "m02", "m11", "m07"])
        d = mdims(m, rng)
        for b in ("ba", "bb"):
            nm = next(names)
            qs.append({"id": nm, "meaning": m, "owner": b, "dims": d, "components": [], "value": "var", "src": "seed"})
            factors.append((nm, d))
    for _ in range(rng.randint(1, 3)):
        if rng.random() < 0.6:
            m = rng.choice(SCALARS)
            d = mdims(m, rng)
            nm = next(names)
            qs.append({"id": nm, "meaning": m, "owner": "world", "dims": d, "components": [], "value": "var",
                       "src": "seed"})
            factors.append((nm, d))
        else:
            m = rng.choice(VECTORS)
            d = mdims(m, rng)
            nm = next(names)
            comps = [nm + c for c in "xyz"]
            qs.append({"id": nm, "meaning": m, "owner": "world", "dims": d, "components": comps, "value": "var",
                       "src": "seed"})
            for c in rng.sample(comps, rng.randint(1, 2)):
                factors.append((c, d))
    if rng.random() < 0.2:
        nm = next(names)
        d = {"L": 1}
        qs.append({"id": nm, "meaning": "m23", "owner": "world", "dims": d, "components": [nm + "p", nm + "q"],
                   "value": "var", "src": "seed"})
        factors += [(nm + "p", d), (nm + "q", d)]
    # left side
    if rng.random() < 0.5:
        y = next(names)
        yd = {"M": 1, "L": 2, "T": -2}
        qs.append({"id": y, "meaning": "m03", "owner": "world", "dims": yd, "components": [], "value": "var",
                   "src": "seed"})
    else:
        base = next(names)
        m = rng.choice(["m16", "m14", "m20", "m18"])
        yd = mdims(m, rng)
        comps = [base + c for c in "xyz"]
        qs.append({"id": base, "meaning": m, "owner": "world", "dims": yd, "components": comps, "value": "var",
                   "src": "seed"})
        y = rng.choice(comps)

    def product(k):
        fs = rng.sample(factors, min(k, len(factors)))
        parts, d = [], {}
        for nm, fd in fs:
            e = rng.choice([1, 1, 1, 2, -1])
            parts.append(nm if e == 1 else f"{nm}^{e}")
            d = dadd(d, {kk: v * e for kk, v in fd.items()})
        return "*".join(parts), d

    terms = []
    for _ in range(rng.randint(1, 2)):
        pr, d = product(rng.randint(1, 2))
        k = next(names)
        qs.append({"id": k, "meaning": "m07", "owner": "world", "dims": dadd(yd, d, -1), "components": [],
                   "value": str(rng.choice([1, 2, 3, -1, Fraction(1, 2)])), "src": "seed"})
        terms.append(f"{k}*{pr}")
    law = f"{y} = " + " + ".join(terms)
    # filler
    newq = []
    pr, d = product(rng.randint(1, 2))
    c = "zc"
    kind_unknown = rng.random() < 0.15
    choice = rng.random()
    if choice < 0.35:
        meaning, under, dims = "m07", card("m07"), "?"
    elif choice < 0.5:
        meaning, under, dims = "m04", card("m04"), "?"
    elif choice < 0.6:
        meaning, under, dims = "m06", card("m06"), "?"
    else:
        meaning = "?"
        under = {t: rng.choice(["1", "-1", "?", "1"]) for t in ("rev_t", "refl_x", "conj_c")}
        dims = dadd(yd, d, -1) if rng.random() < 0.7 else "?"
    owner = "world"
    if bodies and meaning != "?" and rng.random() < 0.3:
        owner = "ba"
        newq.append({"id": "zp", "kind": "scalar", "meaning": meaning, "owner": "bb", "dims": dims,
                     "components": [], "under": under, "value": "?", "old_value": "0", "route": "?"})
    old = rng.choice(["0", "0", "same"])
    newq.insert(0, {"id": c, "kind": "?" if kind_unknown else "scalar", "meaning": meaning if not kind_unknown else "?",
                    "owner": owner, "dims": dims, "components": "?" if kind_unknown else [],
                    "under": under if not kind_unknown else {t: rng.choice(["1", "-1", "?"])
                                                             for t in ("rev_t", "refl_x", "conj_c")},
                    "value": "?", "old_value": old if not (kind_unknown and old not in ("0", "same")) else "0",
                    "route": "?"})
    extra = f" + zp*{pr}" if len(newq) == 2 else ""
    feq = law + f" + {c}*{pr}" + extra
    if rng.random() < 0.15:
        feq = law.replace(" = ", " = 2*", 1) + f" + {c}*{pr}" + extra   # a filler that also changes the old law
    # observations: exact values
    reg = P.Registry()
    w = {"v0": "0.4", "file": "world", "id": f"fz{idx % 1000:03d}", "registry": "test4_registry",
         "registry_sha256": reg.sha, "bodies": [{"id": b, "type": t, "src": "seed"} for b, t in bodies],
         "quantities": qs, "relations": [], "laws": [{"id": "law1", "eq": law, "accepted_at": 0, "src": "seed"}],
         "observers": [{"id": "ob1", "instrument": "i04", "precision": "1/100", "calibrated_against": [],
                        "src": "seed"}],
         "observations": [], "fillers": [{"id": "f1", "of": "law1", "eq": feq, "new_bodies": [], "new": newq,
                                          "src": "seed"}]}
    import sympy as sp
    varnames = [nm for q in qs for nm in (q["components"] or [q["id"]]) if q["value"] == "var"]
    consts = {q["id"]: Fraction(q["value"]) for q in qs if q["value"] != "var"}
    lhs, rhs = law.split(" = ")
    _, frhs = feq.split(" = ", 1)
    used = set()
    for tok in (rhs + " " + frhs).replace("*", " ").replace("^", " ").replace("+", " ").replace("-", " ").split():
        if tok in varnames:
            used.add(tok)
    cval = {c: Fraction(rng.choice([1, 2, -1, 3])), "zp": Fraction(rng.choice([1, -2]))}

    def ev(expr, st, newv):
        vals = {**consts, **st, **newv}
        loc = {k: sp.Symbol(k) for k in vals}
        e = sp.sympify(expr.replace("^", "**"), locals=loc)
        val = e.xreplace({loc[k]: sp.Rational(v.numerator, v.denominator) for k, v in vals.items()})
        if not val.is_Rational:
            raise ZeroDivisionError
        return Fraction(int(val.p), int(val.q))
    obs = []
    try:
        for i in range(rng.randint(1, 3)):
            st = {nm: Fraction(rng.choice([1, 2, 3, -1, -2, Fraction(1, 2)])) for nm in sorted(used)}
            obs.append({"id": f"o{i}", "observer": "ob1", "of": y, "state": {k: P.fstr(v) for k, v in st.items()},
                        "value": P.fstr(ev(rhs, st, {})), "epoch": 0, "src": "ob1"})
        for i in range(rng.randint(1, 2)):
            st = {nm: Fraction(rng.choice([1, 2, 3, -1, -2, Fraction(1, 2)])) for nm in sorted(used)}
            obs.append({"id": f"n{i}", "observer": "ob1", "of": y, "state": {k: P.fstr(v) for k, v in st.items()},
                        "value": P.fstr(ev(frhs, st, cval)), "epoch": 1, "src": "ob1"})
    except (ZeroDivisionError, TypeError, ValueError):
        return None
    w["observations"] = obs
    if rng.random() < 0.35:   # several fillers: more constants of meaning m07 on other products of the law's names
        for j in range(rng.randint(1, 2)):
            pr2, _ = product(rng.randint(1, 2))
            cid = f"zk{j}"
            w["fillers"].append({"id": f"f{j + 2}", "of": "law1", "eq": law + f" + {cid}*{pr2}", "new_bodies": [],
                                 "new": [{"id": cid, "kind": "scalar", "meaning": "m07", "owner": "world", "dims": "?",
                                          "components": [], "under": card("m07"), "value": "?", "old_value": "0",
                                          "route": "?"}], "src": "seed"})
        used2 = set()
        for f in w["fillers"]:
            for tok in f["eq"].split(" = ", 1)[1].replace("*", " ").replace("^", " ").replace("+", " ").replace("-", " ").split():
                if tok in varnames:
                    used2.add(tok)
        if used2 - used:
            return None
    return w


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    rng = random.Random(seed)
    reg_p, reg_r = P.Registry(), R.load_registry()
    stats = {"built": 0, "rejected": {}, "fillers": 0, "card_ok": 0, "base_ok": 0, "zero_ok": 0, "verdicts": {}}
    bad = []
    t0 = time.time()
    for i in range(n):
        w = make_world(rng, i)
        if w is None:
            continue
        stats["built"] += 1
        try:
            rw, cards = R.reference(w, reg_r)
        except R.Invalid as e:
            key = str(e).split(":")[0]
            stats["rejected"][key] = stats["rejected"].get(key, 0) + 1
            continue
        out = P.run_world(w, reg_p)
        for F in rw.fillers:
            c = cards[F.id]
            stats["fillers"] += 1
            stats["verdicts"][c["verdict"]] = stats["verdicts"].get(c["verdict"], 0) + 1
            po = out["procedure"]["fillers"].get(F.id)
            probs = R.check_filler_output(rw, F, c, po)
            stats["card_ok"] += not probs
            bok = all(out[m]["fillers"][F.id].get("verdict") == c["baselines"][m]["verdict"] for m in R.BASELINES)
            stats["base_ok"] += bok
            zok = R.zero_agree(c, po or {})
            stats["zero_ok"] += zok
            if probs or not bok or not zok:
                bad.append({"i": i, "world": w, "problems": probs, "base": {m: (out[m]["fillers"][F.id].get("verdict"),
                            c["baselines"][m]["verdict"]) for m in R.BASELINES}, "zero": (po or {}).get("zero_report"),
                            "zero_ref": c["zero"]})
        if len(rw.fillers) >= 2:
            stats["several"] = stats.get("several", 0) + 1
            pw = out["procedure"]["world"]
            Fs = {F.id: F for F in rw.fillers}
            kept = R.kept_of(cards)
            okp = {tuple(sorted(e["pair"])) for e in pw.get("decisive") or [] if R.decisive_ok(rw, Fs, cards, e)}
            need = {(a, b) for x, a in enumerate(kept) for b in kept[x + 1:]}
            if pw.get("kept") == kept and need <= okp:
                stats["several_ok"] = stats.get("several_ok", 0) + 1
            else:
                bad.append({"i": i, "world": w, "problems": ["several-filler world"], "base": {}, "zero": pw,
                            "zero_ref": kept})
    stats["seconds"] = round(time.time() - t0, 1)
    print(json.dumps(stats, indent=1))
    if bad:
        path = os.path.join(HERE, "results", f"fuzz_failures_{seed}.json")
        json.dump(bad, open(path, "w", encoding="utf-8"), indent=1, default=str)
        print(f"{len(bad)} disagreements written to {path}")
        for b in bad[:5]:
            print(b["i"], b["problems"], b["base"], b["zero"], b["zero_ref"])


if __name__ == "__main__":
    main()
