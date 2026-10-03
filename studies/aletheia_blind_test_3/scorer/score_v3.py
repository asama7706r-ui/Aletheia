"""Aletheia blind test 3 -- frozen scorer v3.

It does NOT import the procedure. It recomputes the reference answer of every world and item with
ref_v3 (independent code: ast parsing, exact simplex), excludes invalid worlds and items and keys that
disagree with the reference, proof-checks the procedure's outputs (points, Farkas certificates, exact
intervals and ranges, decisive sets, reasons), scores the baselines on their answers, and applies the
pre-registered criteria of protocol sections 7 and 10.

Usage:  python score_v3.py <worlds_dir> <data_dir> <key.json> <outputs.json> <report.json>
"""
import json
import os
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ref_v3 as R  # noqa: E402

BASELINES_A = ("ALWAYS_NEW", "DIMS_ONLY", "NO_SCOPE")
BASELINES_B = ("REOPEN_NONE", "REOPEN_ALL")


def load_dir(d, experiment):
    out = {}
    if d and os.path.isdir(d):
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".json"):
                with open(os.path.join(d, fn), encoding="utf-8") as fh:
                    obj = json.load(fh)
                if isinstance(obj, dict) and obj.get("experiment") == experiment:
                    out[obj.get("id", fn)] = obj
    return out


def mcnemar_p(b, c):
    """One-sided exact McNemar: P(X >= b), X ~ Binomial(b + c, 1/2)."""
    n = b + c
    if n == 0:
        return Fraction(1)
    from math import comb
    return Fraction(sum(comb(n, k) for k in range(b, n + 1)), 2 ** n)


def frac(a, b):
    return None if b == 0 else Fraction(a, b)


# ================================================================= Part A

def score_A(worlds, keys, outputs):
    cross = R.cross_world_problems(worlds)
    excluded, valid, info = {}, {}, {}
    for wid, raw in sorted(worlds.items()):
        rw, a, probs = R.load_and_check(raw)
        probs = list(probs) + cross.get(wid, [])
        if not probs:
            probs = R.key_problems_A(a, keys.get(wid))
        if probs:
            excluded[wid] = probs
            continue
        valid[wid] = (rw, a)
        info[wid] = {"hidden_truth_ok": R.hidden_truth_ok(rw, (keys.get(wid) or {}).get("hidden_truth"))}
    n_total = len(worlds)
    rep = {"n_total": n_total, "n_valid": len(valid), "excluded": excluded,
           "void": n_total > 0 and Fraction(len(excluded), n_total) > Fraction(1, 5)}
    comp, unmet = R.composition(valid) if valid else ({}, ["no valid worlds"])
    rep["composition"], rep["composition_unmet"] = comp, unmet
    rows = []
    pairs = {r: {"true": 0, "found": 0, "listed": 0, "listed_true": 0, "misses": []} for r in R.REASONS}
    for wid, (rw, a) in sorted(valid.items()):
        out = outputs.get(wid, {})
        proc = out.get("procedure", {})
        ok, probs, listed = R.check_world_output(rw, a, proc)
        row = {"id": wid, "reference": R.answer_of(a), "procedure": ok, "procedure_answer": R.norm_answer(proc),
               "procedure_problems": probs, "hidden_truth_ok": info[wid]["hidden_truth_ok"]}
        if a["verdict"] == "KNOWN":
            row["note_valid"] = ok or (R.norm_answer(proc) == R.answer_of(a)
                                       and not any("ranges" in x for x in probs))
        for m in BASELINES_A:
            row[m + "_answer"] = R.norm_answer(out.get(m, {}))
            row[m] = row[m + "_answer"] == R.answer_of(a)
        rows.append(row)
        if a["verdict"] in ("KNOWN", "NEW", "FORK"):
            for rid, rs in a["reasons"].items():
                got = listed.get(rid, set())
                for r in rs:
                    pairs[r]["true"] += 1
                    if r in got:
                        pairs[r]["found"] += 1
                    else:
                        pairs[r]["misses"].append("%s:%s" % (wid, rid))
            for rid, got in listed.items():
                for r in got:
                    pairs[r]["listed"] += 1
                    if r in a["reasons"].get(rid, set()):
                        pairs[r]["listed_true"] += 1
    rep["per_world"] = rows
    rep["analysis_accuracy"] = {r: {"recall": frac(v["found"], v["true"]), "precision": frac(v["listed_true"], v["listed"]),
                                    "applicable": v["true"], "found": v["found"], "listed": v["listed"],
                                    "misses": v["misses"]} for r, v in pairs.items()}

    def metrics(m):
        corr = [r[m] for r in rows]
        ans = [r["procedure_answer"] if m == "procedure" else r[m + "_answer"] for r in rows]
        refv = [r["reference"]["verdict"] for r in rows]
        kf = [i for i, v in enumerate(refv) if v in ("KNOWN", "FORK")]
        nw = [i for i, v in enumerate(refv) if v == "NEW"]
        fk = [i for i, v in enumerate(refv) if v == "FORK"]
        kn = [i for i, v in enumerate(refv) if v == "KNOWN"]
        return {"correct": sum(corr), "accuracy": frac(sum(corr), len(rows)),
                "false_novelty": frac(sum(ans[i]["verdict"] == "NEW" for i in kf), len(kf)),
                "false_familiarity": frac(sum(ans[i]["verdict"] in ("KNOWN", "FORK") for i in nw), len(nw)),
                "fork_accuracy": frac(sum(corr[i] for i in fk), len(fk)),
                "over_fork": frac(sum(ans[i]["verdict"] == "FORK" for i in kn), len(kn))}
    for m in ("procedure",) + BASELINES_A:
        rep[m] = metrics(m)
    kn_rows = [r for r in rows if r["reference"]["verdict"] == "KNOWN" and r["procedure_answer"] == r["reference"]]
    rep["procedure"]["notes_valid"] = frac(sum(r["note_valid"] for r in kn_rows), len(kn_rows))
    best = None
    for m in BASELINES_A:
        b = sum(r["procedure"] and not r[m] for r in rows)
        c = sum(r[m] and not r["procedure"] for r in rows)
        p = mcnemar_p(b, c)
        rep[m]["mcnemar"] = {"b": b, "c": c, "p_one_sided": p}
        key = (rep[m]["correct"], p)
        if best is None or key > best[0]:
            best = (key, m)
    P = rep["procedure"]
    bm = best[1] if best else None
    rep["best_baseline"] = bm

    def le(x, t):
        return x is not None and x <= t

    def ge(x, t):
        return x is not None and x >= t
    rep["A1"] = ge(P["accuracy"], Fraction(7, 10))
    rep["A2"] = le(P["false_novelty"], Fraction(3, 20))
    rep["A3"] = le(P["false_familiarity"], Fraction(3, 20))
    rep["A4"] = ge(P["fork_accuracy"], Fraction(7, 10))
    rep["A5"] = bool(bm) and P["accuracy"] is not None and \
        P["accuracy"] - rep[bm]["accuracy"] >= Fraction(3, 20) and rep[bm]["mcnemar"]["p_one_sided"] < Fraction(1, 20)
    rep["outcome"] = "VOID" if rep["void"] else (
        "PASS" if all(rep[k] for k in ("A1", "A2", "A3", "A4", "A5")) else "FAIL")
    return rep, valid


# ================================================================= Part B

def score_B(worlds, valid, items, keys, outputs):
    ref = valid
    invalid_worlds = set(worlds) - set(valid)
    valid_raw = {w: worlds[w] for w in valid}
    excluded, rows, cats = {}, [], {}
    for did, item in sorted(items.items()):
        tw = R.touched(item, worlds)
        if tw & invalid_worlds or (item.get("type") == "observation" and item.get("world") in invalid_worlds):
            excluded[did] = ["the datum touches an invalid world: %s" % sorted(tw & invalid_worlds)]
            continue
        probs, rl, finals, facts = R.check_item(item, valid_raw, ref)
        if not probs:
            probs = R.key_problems_B(item, rl, finals, facts, keys.get(did))
        if probs:
            excluded[did] = probs
            continue
        cats[did] = (keys[did]["type"], facts)
        out = outputs.get(did, {})
        proc = out.get("procedure", {}) if isinstance(out, dict) else {}
        plist = sorted(proc.get("reopened") or []) if isinstance(proc, dict) else []
        pver = proc.get("verdicts") or {}
        files = {w: outputs.get("_A", {}).get(w, {}) for w in worlds}
        list_exact = plist == rl
        verdicts_ok, vprob = True, []
        for w in rl:
            rw2, a2 = finals[w]
            if w in plist:
                ok, pr, _ = R.check_world_output(rw2, a2, pver.get(w, {}))
                if not ok:
                    verdicts_ok = False
                    vprob.append("%s: %s" % (w, pr))
            else:
                stale = R.norm_answer(files.get(w, {}).get("procedure", {}))
                if stale != R.answer_of(a2):
                    verdicts_ok = False
                    vprob.append("%s: stale verdict %s, reference %s" % (w, stale, R.answer_of(a2)))
        silent = []
        for w in pver:
            if w not in plist:
                silent.append("%s: verdict reported outside the procedure's own list" % w)
        for w in plist:
            if w not in rl and w in ref and R.norm_answer(pver.get(w, {})) != R.answer_of(ref[w][1]):
                silent.append("%s: verdict changed outside the reference list" % w)
        touched_files = set(rl) | ({item["world"]} if item["type"] == "observation" else set())
        propagated = sorted(w for w in touched_files if w in ref and
                            R.norm_answer(files.get(w, {}).get("procedure", {})) != R.answer_of(ref[w][1]))
        row = {"id": did, "category": keys[did]["type"], "reference_reopened": rl, "procedure_reopened": plist,
               "list_exact": list_exact, "verdicts_correct": verdicts_ok, "verdict_problems": vprob,
               "silent_changes": silent, "part_a_error_in_touched_files": propagated}
        for m in BASELINES_B:
            bo = out.get(m, {}) if isinstance(out, dict) else {}
            bl = sorted(bo.get("reopened") or [])
            bv = bo.get("verdicts") or {}
            bok = all(R.norm_answer(bv.get(w, files.get(w, {}).get("procedure", {}))
                                    if w in bl else files.get(w, {}).get("procedure", {})) == R.answer_of(finals[w][1])
                      for w in rl)
            row[m] = {"list_exact": bl == rl, "verdicts_correct": bok,
                      "tp": len(set(bl) & set(rl)), "fp": len(set(bl) - set(rl)), "fn": len(set(rl) - set(bl))}
        row["procedure_counts"] = {"tp": len(set(plist) & set(rl)), "fp": len(set(plist) - set(rl)),
                                   "fn": len(set(rl) - set(plist))}
        rows.append(row)
    n_total = len(items)
    rep = {"n_total": n_total, "n_valid": len(rows), "excluded": excluded, "void": len(excluded) >= 4,
           "per_item": rows}
    counts, unmet = R.item_composition(cats)
    rep["composition"], rep["composition_unmet"] = counts, unmet
    n = len(rows)

    def summary(get_exact, get_ok, get_counts):
        tp = sum(get_counts(r)["tp"] for r in rows)
        fp = sum(get_counts(r)["fp"] for r in rows)
        fn = sum(get_counts(r)["fn"] for r in rows)
        return {"list_exact": sum(get_exact(r) for r in rows), "list_exact_rate": frac(sum(get_exact(r) for r in rows), n),
                "verdicts_correct": sum(get_ok(r) for r in rows),
                "verdicts_correct_rate": frac(sum(get_ok(r) for r in rows), n),
                "micro_precision": frac(tp, tp + fp), "micro_recall": frac(tp, tp + fn)}
    rep["procedure"] = summary(lambda r: r["list_exact"], lambda r: r["verdicts_correct"],
                               lambda r: r["procedure_counts"])
    rep["procedure"]["silent_changes"] = sum(len(r["silent_changes"]) for r in rows)
    for m in BASELINES_B:
        rep[m] = summary(lambda r, m=m: r[m]["list_exact"], lambda r, m=m: r[m]["verdicts_correct"],
                         lambda r, m=m: r[m])
    P = rep["procedure"]
    rep["B1"] = P["list_exact_rate"] is not None and P["list_exact_rate"] >= Fraction(8, 9)
    rep["B2"] = P["verdicts_correct_rate"] is not None and P["verdicts_correct_rate"] >= Fraction(8, 9)
    rep["B3"] = P["silent_changes"] == 0
    rep["outcome"] = "VOID" if rep["void"] else ("PASS" if rep["B1"] and rep["B2"] and rep["B3"] else "FAIL")
    return rep


# ================================================================= main

def jsonable(x):
    if isinstance(x, Fraction):
        return R.s(x)
    if isinstance(x, set):
        return sorted(x)
    if isinstance(x, tuple):
        return list(x)
    return str(x)


def main(worlds_dir, data_dir, key_path, out_path, report_path):
    worlds = load_dir(worlds_dir, "A")
    items = load_dir(data_dir, "B")
    with open(key_path, encoding="utf-8") as fh:
        key = json.load(fh)
    with open(out_path, encoding="utf-8") as fh:
        outputs = json.load(fh)
    keysA = {k["id"]: k for k in key.get("A", []) if isinstance(k, dict) and "id" in k}
    keysB = {k["id"]: k for k in key.get("B", []) if isinstance(k, dict) and "id" in k}
    repA, valid = score_A(worlds, keysA, outputs.get("A", {}))
    outB = dict(outputs.get("B", {}))
    outB["_A"] = outputs.get("A", {})
    repB = score_B(worlds, valid, items, keysB, outB)
    report = {"A": repA, "B": repB}
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1, default=jsonable, sort_keys=True)
    summ = {part: {k: v for k, v in rep.items() if k not in ("per_world", "per_item")} for part, rep in report.items()}
    print(json.dumps(summ, ensure_ascii=False, indent=1, default=jsonable, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) == 6:
        main(*sys.argv[1:])
    else:
        print(__doc__)
