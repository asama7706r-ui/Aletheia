"""Aletheia blind test 1 -- frozen scorer v1.

Step 1 (key validation, independent of the procedure's role heuristic):
  E1 NEW_KIND truths : witness matrices must satisfy every law (variables sampled), the observed
                       quantities must be nonzero in the witness algebra, true_family must equal
                       the family computed from the witnesses, true_dim must equal the dimension of
                       the algebra the witnesses generate, and the world must be identifiable:
                       in every strictly more restrictive family, the mold of the laws is trivial or
                       kills at least one observed quantity.
  E1 SUBSUMED truths : true_values satisfy the laws; observed quantities nonzero at those values;
                       identifiable: every family mold kills an observed quantity or is trivial.
  Worlds failing validation are excluded and listed. If more than 20% of a block is excluded,
  that block is VOID.
Step 2 (scoring): pre-registered metrics, baselines, exact one-sided McNemar test, outcome.

Usage: python score_v1.py <worlds_dir> <key_json> <outputs_json> <report_json>
"""
import json
import os
import sys
import random
import itertools
from fractions import Fraction
from math import comb

import sympy as sp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import procedure_v1 as P  # noqa: E402

FAM_RANK = {"comm": 0, "graded": 1, "assoc": 2}
VAR_SAMPLES = 5
VAR_SEED = 777
EXCLUSION_CAP = 0.20


# ----------------------------------------------------------------- witness algebra helpers

def mat(m):
    return sp.Matrix([[sp.Rational(str(x)) for x in row] for row in m])


def eval_nc(nc, mats, size):
    out = sp.zeros(size, size)
    for w, c in nc.items():
        t = sp.eye(size) * sp.Rational(c.numerator, c.denominator)
        for i in w:
            t = t * mats[i]
        out += t
    return out


def laws_hold_on(world, mats, param_values):
    ctx = P.Ctx(world, param_values)
    size = mats[0].shape[0]
    rng = random.Random(VAR_SEED)
    for law in world["laws"]:
        lhs_s, rhs_s = law.split("=")
        resid = P.p_add(P.to_poly(ctx.parse(lhs_s), ctx), P.to_poly(ctx.parse(rhs_s), ctx), -1)
        for _ in range(VAR_SAMPLES if ctx.vars else 1):
            vals = [Fraction(rng.randint(-9, 9), rng.randint(1, 5)) for _ in ctx.vars]
            nc = {}
            for (vm, w), c in resid.items():
                t = c
                for k, e in enumerate(vm):
                    t *= vals[k] ** e
                nc[w] = nc.get(w, 0) + t
            if eval_nc(nc, mats, size) != sp.zeros(size, size):
                return False
    return True


def expr_nonzero_on(world, expr, mats, param_values):
    ctx = P.Ctx(world, param_values)
    size = mats[0].shape[0]
    poly = P.to_poly(ctx.parse(expr), ctx)
    for vm, nc in P.split_by_vm(poly).items():
        if eval_nc(nc, mats, size) != sp.zeros(size, size):
            return True
    return False


def witness_family(world, mats):
    grades = [int(g.get("grade", 0)) % 2 for g in world["generators"]]
    n = len(mats)
    if all(mats[i] * mats[j] == mats[j] * mats[i] for i in range(n) for j in range(n)):
        return "comm"
    if any(grades):
        ok = True
        for i in range(n):
            for j in range(i, n):
                s = -1 if (grades[i] and grades[j]) else 1
                if mats[i] * mats[j] != s * mats[j] * mats[i]:
                    ok = False
        if ok:
            return "graded"
    return "assoc"


def witness_dim(mats):
    size = mats[0].shape[0]
    basis = []

    def add(M):
        v = list(M)
        trial = sp.Matrix(basis + [v]) if basis else sp.Matrix([v])
        if trial.rank() > len(basis):
            basis.append(v)
            return True
        return False

    add(sp.eye(size))
    frontier = [sp.eye(size)]
    while frontier:
        new = []
        for M in frontier:
            for g in mats:
                X = M * g
                if add(X):
                    new.append(X)
        frontier = new
    return len(basis)


def observed_killed_by_all_stricter(world, key, true_fam, param_values):
    """Identifiability: every family strictly more restrictive than true_fam gives a trivial
    mold or kills at least one observed quantity (checked with the mold engine)."""
    ctx, relations, _content, n, D = P._prepare(world, param_values)
    observed = [P.to_poly(ctx.parse(e), ctx) for e in key.get("observed_nonzero", [])]
    for fam in P.FAMILY_ORDER:
        if true_fam is not None and FAM_RANK[fam] >= FAM_RANK[true_fam]:
            continue
        if fam == "graded" and not any(ctx.grades):
            continue
        M = P.build_mold(fam, ctx, relations, D)
        if M.trivial():
            continue
        if not any(not P.alive(M, p) for p in observed):
            return False
    return True


def subsumed_identifiable(world, key, param_values):
    """For SUBSUMED truths nothing stricter than 'known value' exists; valid if the values
    satisfy the laws and the observed quantities are nonzero at those values."""
    ctx, relations, _content, n, D = P._prepare(world, param_values)
    vals = [Fraction(str(key["true_values"][g])) for g in ctx.gens]
    for r in relations:
        if P.nonzero_at({(ctx.zero_vm, w): c for w, c in r.items()}, vals):
            return False
    for e in key.get("observed_nonzero", []):
        if not P.nonzero_at(P.to_poly(ctx.parse(e), ctx), vals):
            return False
    return True


def validate_e1(world, key):
    pv = {k: Fraction(str(v)) for k, v in key.get("true_parameter_values", {}).items()} or None
    label = key["label"]
    if label == "NEW_KIND":
        if "witness" not in key:
            return False, "no witness"
        gens = [g["name"] for g in world["generators"]]
        mats = [mat(key["witness"][g]) for g in gens]
        if not laws_hold_on(world, mats, pv):
            return False, "witness violates a law"
        for e in key.get("observed_nonzero", []):
            if not expr_nonzero_on(world, e, mats, pv):
                return False, "observed quantity zero in witness: %s" % e
        wf = witness_family(world, mats)
        if wf != key.get("true_family"):
            return False, "true_family %s but witness family %s" % (key.get("true_family"), wf)
        wd = witness_dim(mats)
        if int(key.get("true_dim", -1)) != wd:
            return False, "true_dim %s but witness dim %d" % (key.get("true_dim"), wd)
        if not observed_killed_by_all_stricter(world, key, wf, pv):
            return False, "not identifiable (a stricter family keeps all observed quantities)"
        ctx, relations, _c, n, _D = P._prepare(world, pv)
        observed = [P.to_poly(ctx.parse(e), ctx) for e in key.get("observed_nonzero", [])]
        for s in P.rational_solutions(relations, n):
            if all(P.nonzero_at(p, s) for p in observed):
                return False, "not identifiable (a known rational value keeps all observed quantities)"
        return True, ""
    if label == "SUBSUMED":
        if "true_values" not in key:
            return False, "no true_values"
        if not subsumed_identifiable(world, key, pv):
            return False, "true_values violate a law or kill an observed quantity"
        return True, ""
    if label in ("CONTRADICTION", "UNDERDETERMINED"):
        return True, ""
    return False, "unknown label"


# ----------------------------------------------------------------- scoring

def e1_correct(out, key):
    lab = out.get("label")
    if lab != key["label"]:
        return False
    if lab == "NEW_KIND":
        return out.get("family") == key.get("true_family")
    if lab == "SUBSUMED" and "true_values" in key and "values" in out:
        gens = list(key["true_values"].keys())
        tv = [str(Fraction(str(key["true_values"][g]))) for g in gens]
        return any([str(Fraction(v)) for v in vals] == tv for vals in out["values"])
    return True


def silent_collapse(out, key):
    if key["label"] != "NEW_KIND":
        return None
    if out.get("label") == "SUBSUMED":
        return True
    if out.get("label") == "NEW_KIND" and out.get("family") in FAM_RANK:
        return FAM_RANK[out["family"]] < FAM_RANK[key["true_family"]]
    return False


def over_loose(out, key):
    if key["label"] != "NEW_KIND" or key["true_family"] == "assoc":
        return None
    if out.get("label") == "NEW_KIND" and out.get("family") in FAM_RANK:
        return FAM_RANK[out["family"]] > FAM_RANK[key["true_family"]]
    return False


def mcnemar_one_sided(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return sum(comb(n, k) for k in range(b, n + 1)) / 2 ** n


def e2_group(label):
    if label in ("SAME_LAW_NEW_STATE", "SAME_CARD"):
        return "SAME"
    if label == "ANOTHER_LAW":
        return "ANOTHER"
    if label == "INVALID":
        return "INVALID"
    return "OTHER"


def main(worlds_dir, key_path, outputs_path, report_path):
    worlds = {}
    for fn in os.listdir(worlds_dir):
        if fn.endswith(".json"):
            with open(os.path.join(worlds_dir, fn), encoding="utf-8") as fh:
                w = json.load(fh)
            worlds[w["id"]] = w
    with open(key_path, encoding="utf-8") as fh:
        key = {k["id"]: k for k in json.load(fh)}
    with open(outputs_path, encoding="utf-8") as fh:
        outs = json.load(fh)

    report = {"excluded": {}, "E1": {}, "E2": {}}
    e1_ids = sorted(i for i, w in worlds.items() if w.get("experiment") == "E1")
    e2_ids = sorted(i for i, w in worlds.items() if w.get("experiment") == "E2")

    valid_e1 = []
    for i in e1_ids:
        try:
            ok, why = validate_e1(worlds[i], key[i])
        except Exception as ex:
            ok, why = False, "validation error %s: %s" % (type(ex).__name__, ex)
        if ok:
            valid_e1.append(i)
        else:
            report["excluded"][i] = why
    valid_e2 = [i for i in e2_ids if i in key]

    # ---------------- E1
    names = ("procedure", "B1", "B2", "B3")
    acc = {nm: [e1_correct(outs[i][nm], key[i]) for i in valid_e1] for nm in names}
    e1 = {"n_total": len(e1_ids), "n_valid": len(valid_e1),
          "void": (len(e1_ids) - len(valid_e1)) > EXCLUSION_CAP * max(1, len(e1_ids))}
    for nm in names:
        a = acc[nm]
        sc = [silent_collapse(outs[i][nm], key[i]) for i in valid_e1]
        sc = [x for x in sc if x is not None]
        ol = [over_loose(outs[i][nm], key[i]) for i in valid_e1]
        ol = [x for x in ol if x is not None]
        e1[nm] = {"accuracy": sum(a) / len(a) if a else None, "correct": sum(a),
                  "silent_collapse_rate": sum(sc) / len(sc) if sc else None,
                  "over_loose_rate": sum(ol) / len(ol) if ol else None}
    best = max(("B1", "B2", "B3"), key=lambda nm: e1[nm]["accuracy"] or 0)
    b = sum(1 for p, q in zip(acc["procedure"], acc[best]) if p and not q)
    c = sum(1 for p, q in zip(acc["procedure"], acc[best]) if q and not p)
    contra_wrong = sum(1 for i in valid_e1 if key[i]["label"] == "CONTRADICTION"
                       and outs[i]["procedure"].get("label") in ("NEW_KIND", "SUBSUMED"))
    dims = [outs[i]["procedure"].get("dim") == key[i].get("true_dim") for i in valid_e1
            if key[i]["label"] == "NEW_KIND" and key[i].get("complete_presentation")
            and e1_correct(outs[i]["procedure"], key[i])]
    pa = e1["procedure"]["accuracy"] or 0
    S1 = pa >= 0.70
    S2 = (pa - (e1[best]["accuracy"] or 0) >= 0.15) and mcnemar_one_sided(b, c) < 0.05
    S3 = (e1["procedure"]["silent_collapse_rate"] or 0) <= 0.15
    S4 = contra_wrong <= 1
    e1.update({"best_baseline": best, "mcnemar_b": b, "mcnemar_c": c,
               "mcnemar_p": mcnemar_one_sided(b, c), "contradiction_accepted": contra_wrong,
               "dim_agreement": (sum(dims), len(dims)),
               "S1": S1, "S2": S2, "S3": S3, "S4": S4})
    if e1["void"]:
        e1["outcome"] = "VOID"
    elif S1 and S2 and S3 and S4:
        e1["outcome"] = "PASS"
    elif S1 and S3:
        e1["outcome"] = "PARTIAL"
    else:
        e1["outcome"] = "FAIL"
    e1["per_world"] = {i: {"truth": [key[i]["label"], key[i].get("true_family")],
                           "procedure": [outs[i]["procedure"].get("label"), outs[i]["procedure"].get("family")],
                           "B3": [outs[i]["B3"].get("label"), outs[i]["B3"].get("family")],
                           "correct": e1_correct(outs[i]["procedure"], key[i])} for i in valid_e1}
    report["E1"] = e1

    # ---------------- E2
    e2 = {"n": len(valid_e2)}
    for nm in ("procedure", "C1", "C2", "C3"):
        per_class = {}
        for cls in ("SAME", "ANOTHER", "INVALID"):
            ids = [i for i in valid_e2 if e2_group(key[i]["label"]) == cls]
            hits = [e2_group(outs[i][nm]["label"]) == cls for i in ids]
            per_class[cls] = (sum(hits), len(hits))
        rates = [h / t for h, t in per_class.values() if t]
        e2[nm] = {"per_class": per_class, "balanced_accuracy": sum(rates) / len(rates) if rates else None}
    det = [i for i in valid_e2 if key[i]["label"] == "ANOTHER_LAW" and key[i].get("detectable_by_card")]
    det_hits = sum(1 for i in det if outs[i]["procedure"]["label"] == "ANOTHER_LAW")
    same = [i for i in valid_e2 if key[i]["label"] == "SAME_LAW_NEW_STATE"]
    false_alarms = sum(1 for i in same if e2_group(outs[i]["procedure"]["label"]) != "SAME")
    inval = [i for i in valid_e2 if key[i]["label"] == "INVALID"]
    inval_hits = sum(1 for i in inval if outs[i]["procedure"]["label"] == "INVALID")
    T1 = (det_hits / len(det)) >= 0.80 if det else False
    T2 = (false_alarms / len(same)) <= (1 / 6) if same else False
    T3 = (inval_hits / len(inval)) >= (2 / 3) if inval else False
    base_best = max(e2[nm]["balanced_accuracy"] or 0 for nm in ("C1", "C2", "C3"))
    T4 = (e2["procedure"]["balanced_accuracy"] or 0) > base_best
    e2.update({"detectable_recall": (det_hits, len(det)), "false_alarms": (false_alarms, len(same)),
               "invalid_detected": (inval_hits, len(inval)), "T1": T1, "T2": T2, "T3": T3, "T4": T4,
               "outcome": "PASS" if (T1 and T2 and T3 and T4) else "FAIL",
               "per_world": {i: {"truth": key[i]["label"], "procedure": outs[i]["procedure"]["label"],
                                 "changed": outs[i]["procedure"].get("changed")} for i in valid_e2}})
    report["E2"] = e2

    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1, default=str)
    print(json.dumps({"E1": {k: report["E1"][k] for k in report["E1"] if k != "per_world"},
                      "E2": {k: report["E2"][k] for k in report["E2"] if k != "per_world"},
                      "excluded": report["excluded"]}, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    if len(sys.argv) == 5:
        main(*sys.argv[1:])
    else:
        print(__doc__)
