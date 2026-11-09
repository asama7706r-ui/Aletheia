#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The scorer of blind test 5b (protocol_v5b.md, Section 8).

Usage: python scorer/score_v5b.py BATCH_DIR OUTPUTS.json REPORT.json
The truth of each valid world comes from the key's certificates, the procedure's certificates and the
reference's own search (8.1). Prints the metrics and criteria C1-C7, and writes the full report.
"""
import json
import os
import sys
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import certs_v5 as C  # noqa: E402
import ref_v5b as RF  # noqa: E402
import baselines_v5b as BL  # noqa: E402
import validate_v5b as V  # noqa: E402

COLLAPSE_WORDS = ("role equation", "role inequation", "bracketings", "E*E", "old inverses")


def output_pool(out, info):
    """The procedure's certificates, each checked; returns (pool, problems)."""
    pool = {"witness": [], "refutation": [], "known": []}
    problems = {"false_witness": [], "collapse": [], "bad_proof": []}
    for b in out.get("branches") or []:
        w = b.get("witness")
        if w is not None:
            ok, why = C.safe(C.check_witness, w, info, b["drop"])
            if ok:
                pool["witness"].append((b["drop"], w))
            else:
                problems["false_witness"].append(f"{b['drop']}: {why}")
                if any(x in why for x in COLLAPSE_WORDS):
                    problems["collapse"].append(f"{b['drop']}: {why}")
        for u, p in (b.get("proofs") or {}).items():
            d = [x for x in b["drop"] if x != u]
            ok, why = C.safe(C.check_refutation, p, info, d)
            if ok:
                pool["refutation"].append((d, p))
            else:
                problems["bad_proof"].append(f"{u} in {b['drop']}: {why}")
    for r in out.get("refutations") or []:
        if C.safe(C.check_refutation, r.get("proof"), info, r.get("drop", []))[0]:
            pool["refutation"].append((r["drop"], r["proof"]))
    k = out.get("known")
    if k:
        ok, why = C.safe(C.check_known, k, info)
        if ok:
            pool["known"].append(k)
        else:
            problems["false_witness"].append(f"known: {why}")
            if any(x in why for x in COLLAPSE_WORDS):
                problems["collapse"].append(f"known: {why}")
    return pool, problems


def merge_pools(a, b):
    return {k: list(a.get(k, [])) + list(b.get(k, [])) for k in ("witness", "refutation", "known")}


def marks_correct(out, truth, info):
    """Section 8.2: decision correct, every mark equal, every FORCED unit with a valid proof, every witness valid."""
    if not V.decision_equal(out, truth):
        return False
    tb = {tuple(sorted(b["drop"])): b for b in truth["branches"]}
    for b in out.get("branches") or []:
        t = tb.get(tuple(sorted(b["drop"])))
        if t is None:
            return False
        if b.get("marks") != t["marks"]:
            return False
        for u in b["drop"]:
            p = (b.get("proofs") or {}).get(u)
            if p is None or not C.safe(C.check_refutation, p, info, [x for x in b["drop"] if x != u])[0]:
                return False
        if b["status"] == "witnessed":
            w = b.get("witness")
            if w is None or not C.safe(C.check_witness, w, info, b["drop"])[0]:
                return False
    return True


def silent_choice(out, truth):
    if truth["verdict"] not in ("BRANCHES", "NO_WITNESS") or len(truth["branches"]) < 2:
        return False
    t = {x for x, _ in V.norm_branches(truth["branches"])}
    o = {x for x, _ in V.norm_branches(out.get("branches") if out.get("verdict") in ("NEW_KIND", "BRANCHES", "NO_WITNESS") else [])}
    return o < t


REPORTED = ("branches_added_where_a_proof_decides", "unmerged_mirror_twins",
            "no_witness_branches_the_truth_witnesses", "no_witness_verdicts_where_the_truth_has_a_witness")


def reported_counts(out, truth, cl):
    """The "reported only" counts of Section 8.3, as lists (test 5 audit, lesson 2: print all of them)."""
    res = {k: [] for k in REPORTED}
    if truth["verdict"] not in ("NEW_KIND", "BRANCHES", "NO_WITNESS") or cl is None:
        return res
    obr = out.get("branches") if out.get("verdict") in ("NEW_KIND", "BRANCHES", "NO_WITNESS") else []
    obr = obr or []
    for b in obr:
        drops = [b["drop"]] + ([b["mirror"]["twin"]] if b.get("mirror") else [])
        if any(cl.status(frozenset(d)) == "REFUTED" for d in drops):
            res["branches_added_where_a_proof_decides"].append(sorted(b["drop"]))
        if b.get("status") == "no_witness" and any(cl.status(frozenset(d)) == "WITNESSED" for d in drops):
            res["no_witness_branches_the_truth_witnesses"].append(sorted(b["drop"]))
    plain = {tuple(sorted(b["drop"])) for b in obr if not b.get("mirror")}
    for t in truth["branches"]:
        if t.get("mirror") and {tuple(sorted(t["drop"])), tuple(sorted(t["mirror"]["twin"]))} <= plain:
            res["unmerged_mirror_twins"].append(sorted(t["drop"]))
    if out.get("verdict") == "NO_WITNESS" and truth["verdict"] in ("NEW_KIND", "BRANCHES"):
        res["no_witness_verdicts_where_the_truth_has_a_witness"].append(truth["verdict"])
    return res


def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return sum(comb(n, k) for k in range(b, n + 1)) / 2 ** n


def score(batch, outputs_path, report_path):
    reg = V.load_seed()
    key = {e["id"]: e for e in json.load(open(os.path.join(batch, "key", "key.json"), encoding="utf-8"))}
    outputs = json.load(open(outputs_path, encoding="utf-8"))
    dev_fps = set(json.load(open(V.DEV_FP, encoding="utf-8"))) if os.path.exists(V.DEV_FP) else set()
    rows, excluded = {}, []
    files = sorted(f for f in os.listdir(os.path.join(batch, "worlds")) if f.endswith(".json"))
    for f in files:
        wid = f[:-5]
        path = os.path.join(batch, "worlds", f)
        val = V.validate_world(path, key.get(wid), reg, dev_fps)
        if val["errors"]:
            excluded.append({"world": wid, "errors": val["errors"]})
            print(f"{wid}: EXCLUDED ({len(val['errors'])} validity errors)", flush=True)
            continue
        world = C.R.load(path)
        info = val["info"]
        out = (outputs.get(wid) or {}).get("procedure") or {"verdict": "MISSING"}
        opool, problems = output_pool(out, info)
        pool = merge_pools(V.key_pool(key[wid], info), opool)
        truth, cl = RF.truth_full(world, pool)
        changed = V.summary(truth) != V.summary(val["truth"])
        base = BL.run_all(world, truth, cl, info, pool) if truth["verdict"] not in ("UNDETERMINED", "OUTSIDE_W") else {}
        branched = truth["verdict"] in ("NEW_KIND", "BRANCHES", "NO_WITNESS")
        row = {
            "truth": V.summary_safe(truth), "output": V.summary_safe(out),
            "verdict_ok": out.get("verdict") == truth["verdict"],
            "decision_ok": V.decision_equal(out, truth),
            "drop_ok": V.decision_equal(out, truth) if branched else None,
            "marks_ok": marks_correct(out, truth, info) if branched else None,
            "false_witness": bool(problems["false_witness"]), "collapse": bool(problems["collapse"]),
            "silent_choice": silent_choice(out, truth), "problems": problems,
            "truth_changed_by_output": changed,
            "baselines": {n: V.decision_equal(o, truth) for n, o in base.items()},
            "reported": reported_counts(out, truth, cl),
        }
        rows[wid] = row
        print(f"{wid}: truth {row['truth']}  output {'OK' if row['decision_ok'] else 'WRONG'}"
              + ("  (truth changed by the output's certificates)" if changed else ""), flush=True)
    n = len(rows)
    acc = lambda key_: sum(1 for r in rows.values() if r[key_]) / n if n else 0.0  # noqa: E731
    br = [r for r in rows.values() if r["drop_ok"] is not None]
    drop_acc = sum(1 for r in br if r["drop_ok"]) / len(br) if br else 1.0
    marks_acc = sum(1 for r in br if r["marks_ok"]) / len(br) if br else 1.0
    base_acc = {b: sum(1 for r in rows.values() if r["baselines"].get(b)) / n if n else 0.0 for b in BL.NAMES}
    best = max(BL.NAMES, key=lambda b: base_acc[b])
    ties = [b for b in BL.NAMES if base_acc[b] == base_acc[best]]
    worst_p, chosen = -1, best
    for b in ties:
        bb = sum(1 for r in rows.values() if r["decision_ok"] and not r["baselines"].get(b))
        cc = sum(1 for r in rows.values() if not r["decision_ok"] and r["baselines"].get(b))
        p = mcnemar(bb, cc)
        if p > worst_p:
            worst_p, chosen = p, b
    dec_acc = acc("decision_ok")
    crit = {
        "C1 verdict accuracy >= 0.70": acc("verdict_ok") >= 0.70,
        "C2 drop-set accuracy >= 0.70": drop_acc >= 0.70,
        "C3 marks accuracy >= 0.70": marks_acc >= 0.70,
        "C4 beats the best baseline by >= 0.15 with p < 0.05": dec_acc - base_acc[chosen] >= 0.15 and worst_p < 0.05,
        "C5 silent collapse in 0 worlds": sum(r["collapse"] for r in rows.values()) == 0,
        "C6 silent choice in at most 1 world": sum(r["silent_choice"] for r in rows.values()) <= 1,
        "C7 false witness in 0 worlds": sum(r["false_witness"] for r in rows.values()) == 0,
    }
    outcome = "VOID" if len(excluded) >= 7 else ("PASS" if all(crit.values()) else "FAIL")
    report = {"outcome": outcome, "valid_worlds": n, "excluded": excluded,
              "metrics": {"verdict_accuracy": acc("verdict_ok"), "drop_set_accuracy": drop_acc,
                          "marks_accuracy": marks_acc, "decision_accuracy": dec_acc,
                          "baseline_decision_accuracy": base_acc, "best_baseline": chosen, "mcnemar_p": worst_p,
                          "false_witness": sum(r["false_witness"] for r in rows.values()),
                          "silent_collapse": sum(r["collapse"] for r in rows.values()),
                          "silent_choice": sum(r["silent_choice"] for r in rows.values()),
                          "truth_changed_by_output": sorted(w for w, r in rows.items() if r["truth_changed_by_output"]),
                          "reported_only": {k: {"count": sum(len(r["reported"][k]) for r in rows.values()),
                                                "worlds": sorted(w for w, r in rows.items() if r["reported"][k])}
                                            for k in REPORTED}},
              "criteria": crit, "worlds": rows}
    with open(report_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: report[k] for k in ("outcome", "valid_worlds", "metrics", "criteria")}, indent=1, default=str))
    return report


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(2)
    score(sys.argv[1], sys.argv[2], sys.argv[3])
