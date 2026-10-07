"""Aletheia blind test 4 -- scorer (protocol sections 8.1-8.4). Never imports the procedure.

Usage:  python score_v4.py <worlds_dir> <key.json> <outputs.json> <report.json> [--dev]
"""
import json
import math
import os
import sys
from fractions import Fraction

import ref_v4 as R


def mcnemar_p(b, c):
    """one-sided exact McNemar: P(X >= b), X ~ Binomial(b + c, 1/2)"""
    n = b + c
    if n == 0:
        return Fraction(1)
    return Fraction(sum(math.comb(n, k) for k in range(b, n + 1)), 2 ** n)


def key_problems(rw, cards, k):
    """V12: the key entry agrees with the reference."""
    p = []
    if not isinstance(k, dict) or not isinstance(k.get("fillers"), dict):
        return ["key entry malformed"]
    if set(k["fillers"]) != {F.id for F in rw.fillers}:
        p.append("key fillers differ from the world's")
    for fid, e in k["fillers"].items():
        if fid not in cards:
            continue
        if e.get("verdict") != cards[fid]["verdict"]:
            p.append(f"{fid}: key verdict {e.get('verdict')} != reference {cards[fid]['verdict']}")
        for t, st in (e.get("F2") or {}).items():
            ref = cards[fid]["F2"].get(t)
            if ref is None or ref["status"] != st:
                p.append(f"{fid}: key F2 {t}={st} != reference {ref['status'] if ref else 'absent'}")
    if len(rw.fillers) >= 2:
        if k.get("kept") != R.kept_of(cards):
            p.append(f"kept {k.get('kept')} != reference {R.kept_of(cards)}")
        Fs = {F.id: F for F in rw.fillers}
        kept = R.kept_of(cards)
        pairs = {(a, b) for i, a in enumerate(kept) for b in kept[i + 1:]}
        got = set()
        for e in k.get("decisive") or []:
            if R.decisive_ok(rw, Fs, cards, e, check_intervals=False):
                got.add(tuple(sorted(e["pair"])))
        if not pairs <= got:
            p.append("V10: a pair of kept fillers has no valid decisive state in the key")
    labels = set()
    for F in rw.fillers:
        labels |= R.traps_of(rw, F, cards[F.id])
    if len(rw.fillers) >= 2:
        labels.add("T9")
    for t in k.get("traps") or []:
        if t not in labels:
            p.append(f"declared trap {t} does not hold")
    return p


def evaluate(worlds_dir, key_path, out_path):
    reg = R.load_registry()
    key = {e["id"]: e for e in R.load_json(key_path)}
    outputs = R.load_json(out_path)
    files = R.world_files(worlds_dir)
    excluded, worlds = {}, {}
    for fn in files:
        wid = fn[:-5]
        try:
            rw, cards = R.reference(R.load_json(os.path.join(worlds_dir, fn)), reg)
        except R.Invalid as e:
            excluded[wid] = str(e)
            continue
        kp = key_problems(rw, cards, key.get(wid)) if wid in key else ["no key entry"]
        if kp:
            excluded[wid] = "V12: " + "; ".join(kp)
            continue
        worlds[wid] = (rw, cards)
    void = len(excluded) * 5 > len(files)
    methods = ("procedure",) + R.BASELINES
    rows = []           # one per valid filler
    choice_fail, several = [], []
    zero_counts, zero_agree, zero_total = {}, 0, 0
    for wid, (rw, cards) in sorted(worlds.items()):
        wout = outputs.get(wid, {})
        for F in rw.fillers:
            c = cards[F.id]
            rec = {"world": wid, "filler": F.id, "ref": c["verdict"]}
            po = ((wout.get("procedure") or {}).get("fillers") or {}).get(F.id)
            probs = R.check_filler_output(rw, F, c, po)
            rec["procedure"] = {"verdict": (po or {}).get("verdict") if isinstance(po, dict) else None,
                                "correct": not probs, "problems": probs}
            for m in R.BASELINES:
                bo = ((wout.get(m) or {}).get("fillers") or {}).get(F.id)
                bv = bo.get("verdict") if isinstance(bo, dict) else None
                rec[m] = {"verdict": bv, "correct": bv == c["verdict"]}
            if isinstance(po, dict) and isinstance(po.get("zero_report"), list):
                for lab in po["zero_report"]:
                    zero_counts[lab] = zero_counts.get(lab, 0) + 1
            zero_total += 1
            zero_agree += R.zero_agree(c, po or {})
            rows.append(rec)
        if len(rw.fillers) >= 2:
            several.append(wid)
            pw = (wout.get("procedure") or {}).get("world") or {}
            kept_ref = R.kept_of(cards)
            got = pw.get("kept") if isinstance(pw.get("kept"), list) else []
            missing = [f for f in kept_ref if f not in got]
            Fs = {F.id: F for F in rw.fillers}
            ok_pairs = set()
            for e in pw.get("decisive") or []:
                if isinstance(e, dict) and R.decisive_ok(rw, Fs, cards, e):
                    ok_pairs.add(tuple(sorted(e["pair"])))
            need = {(a, b) for i, a in enumerate(kept_ref) for b in kept_ref[i + 1:]}
            if missing or not need <= ok_pairs:
                choice_fail.append({"world": wid, "missing": missing,
                                    "pairs_without_state": sorted(map(list, need - ok_pairs))})
    n = len(rows)

    def acc(m):
        return Fraction(sum(r[m]["correct"] for r in rows), n) if n else Fraction(0)
    accuracy = {m: acc(m) for m in methods}
    another = [r for r in rows if r["ref"] == "ANOTHER_LAW"]
    same = [r for r in rows if r["ref"] == "SAME_LAW_NEW_STATE"]
    cond = [r for r in rows if r["ref"] == "CONDITIONAL"]
    inval = [r for r in rows if r["ref"] == "INVALID"]
    pv = lambda r: r["procedure"]["verdict"]  # noqa: E731
    silent_sub = [f"{r['world']}/{r['filler']}" for r in another if pv(r) in ("SAME_LAW_NEW_STATE", "CONDITIONAL")]
    false_alarm = Fraction(sum(pv(r) == "ANOTHER_LAW" for r in same), len(same)) if same else Fraction(0)
    branch_acc = Fraction(sum(r["procedure"]["correct"] for r in cond), len(cond)) if cond else Fraction(0)
    inv_det = Fraction(sum(pv(r) == "INVALID" for r in inval), len(inval)) if inval else Fraction(0)
    over_branch = sum(pv(r) == "CONDITIONAL" for r in rows if r["ref"] != "CONDITIONAL")
    best = None
    for m in R.BASELINES:
        b = sum(r["procedure"]["correct"] and not r[m]["correct"] for r in rows)
        c = sum(r[m]["correct"] and not r["procedure"]["correct"] for r in rows)
        p = mcnemar_p(b, c)
        cand = (accuracy[m], p, m, b, c)
        if best is None or cand[0] > best[0] or (cand[0] == best[0] and cand[1] > best[1]):
            best = cand
    crit = {
        "C1 accuracy >= 0.70": accuracy["procedure"] >= Fraction(7, 10),
        "C2 silent substitution <= 1 filler": len(silent_sub) <= 1,
        "C3 false alarms <= 0.15": false_alarm <= Fraction(15, 100),
        "C4 branch accuracy >= 0.70": branch_acc >= Fraction(7, 10),
        "C5 silent choice <= 1 world": len(choice_fail) <= 1,
        "C6 INVALID detection >= 2/3": inv_det >= Fraction(2, 3),
        "C7 +0.15 over the best baseline and McNemar p < 0.05":
            accuracy["procedure"] - best[0] >= Fraction(15, 100) and best[1] < Fraction(5, 100),
    }
    outcome = "VOID" if void else ("PASS" if all(crit.values()) else "FAIL")
    f = lambda x: f"{x} ({float(x):.3f})"  # noqa: E731
    report = {
        "outcome": outcome,
        "worlds": len(files), "excluded": excluded, "valid_worlds": len(worlds), "valid_fillers": n,
        "accuracy": {m: f(a) for m, a in accuracy.items()},
        "silent_substitution": silent_sub,
        "false_alarms": f(false_alarm), "branch_accuracy": f(branch_acc),
        "silent_choice": choice_fail, "several_filler_worlds": several,
        "invalid_detection": f(inv_det), "over_branching": over_branch,
        "best_baseline": {"method": best[2], "accuracy": f(best[0]), "b": best[3], "c": best[4],
                          "mcnemar_p": f(best[1])},
        "criteria": crit,
        "zero_report": {"counts": zero_counts, "agree_with_reference": f"{zero_agree}/{zero_total}"},
        "fillers": rows,
    }
    return report


if __name__ == "__main__":
    if "--dev" in sys.argv:
        sys.argv.remove("--dev")
        R.ALLOW_DEV = True     # dev worlds only; never used on the test worlds
    if len(sys.argv) != 5:
        print(__doc__)
        sys.exit(1)
    rep = evaluate(*sys.argv[1:4])
    with open(sys.argv[4], "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rep, fh, indent=1, sort_keys=True, default=str)
        fh.write("\n")
    print(json.dumps({k: rep[k] for k in ("outcome", "valid_worlds", "valid_fillers", "accuracy",
                                          "silent_substitution", "false_alarms", "branch_accuracy",
                                          "silent_choice", "invalid_detection", "over_branching",
                                          "best_baseline", "criteria", "zero_report", "excluded")},
                     indent=1, default=str))
