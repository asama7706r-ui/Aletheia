"""Score LLM answers on the blind-test-2 worlds with the SEALED test-2 scorer (score_v2.py).

The sealed scorer is loaded only after its SHA-256 matches the published hash, and it is never modified.
Four entrants are scored per call by filling its four method slots. This wrapper adds only:
 - the primary Part A metric: a FORK counts when the branch level sequence matches, without decisive
   sets (decisive sets and graded certificates cannot fairly be asked of a chat model);
 - per-model counts and the pre-registered verdict rules (protocol_llm1.md, section 6).
Usage:  python tools/score_llm.py <run_dir> [<run_dir> ...]
        (each run_dir holds parsed.json and meta.json; writes results/report_llm.json and summary.txt)
"""
import hashlib
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T2 = os.path.join(os.path.dirname(HERE), "aletheia_blind_test_2")
SCORER = os.path.join(T2, "procedure", "score_v2.py")
SCORER_SHA = "4453d00c556e1b0e0ef3f02d982e8fad48c4ce5ea46f65f0405a9e8589cdecad"
A_SLOTS = ("procedure", "V1D", "OCC", "FORKALL")
B_SLOTS = ("procedure", "THRESH", "MENTION", "NOSYM")


def load_sealed(path=SCORER, sha=SCORER_SHA):
    got = hashlib.sha256(open(path, "rb").read()).hexdigest()
    if got != sha:
        raise SystemExit("REFUSED: score_v2.py hash %s != sealed %s" % (got, sha))
    spec = importlib.util.spec_from_file_location("score_v2_sealed", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_data():
    worlds = {}
    wd = os.path.join(T2, "worlds")
    for fn in sorted(os.listdir(wd)):
        if fn.endswith(".json"):
            w = json.load(open(os.path.join(wd, fn), encoding="utf-8"))
            worlds[w["id"]] = w
    keys = {k["id"]: k for k in json.load(open(os.path.join(T2, "key", "key.json"), encoding="utf-8"))}
    A = {k: w for k, w in worlds.items() if w["experiment"] == "A"}
    B = {k: w for k, w in worlds.items() if w["experiment"] == "B"}
    return A, B, keys


def slot_rows(S, fn, worlds, keys, entrants, slots):
    """Run the sealed score function with up to 4 entrants per call; return {name: [rows]}, excluded."""
    rows, excluded = {}, {}
    names = list(entrants)
    for i in range(0, len(names), 4):
        group = names[i:i + 4]
        outputs = {wid: {slot: entrants[n].get(wid, {"label": "MISSING"}) for slot, n in zip(slots, group)}
                   for wid in worlds}
        rep = fn(worlds, keys, outputs)
        excluded.update(rep["excluded"])
        for slot, n in zip(slots, group):
            rows[n] = [{"id": r["id"], "truth": r.get("answer") or r.get("class"), "correct": bool(r[slot]),
                        "label": r[slot + "_label"]} for r in rep["per_world"]]
    return rows, excluded


def primary_A(S, out, key, info):
    lab = out.get("label")
    if lab != key["answer"]:
        return False
    if lab == "FORK":
        return [b.get("level") for b in out.get("branches", [])] == [b["level"] for b in key["branches"]]
    try:
        return bool(S.correct_A(out, key, info))
    except Exception:
        return False


def evaluate(entrants, S=None):
    S = S or load_sealed()
    A, B, keys = load_data()
    infos = {}
    for wid in sorted(A):
        ok, why, info = S.validate_A(A[wid], keys[wid])
        if not ok:
            raise SystemExit("key validation failed for %s: %s" % (wid, why))
        infos[wid] = info
    strictA, exA = slot_rows(S, S.score_A, A, keys, {n: e["A"] for n, e in entrants.items()}, A_SLOTS)
    rowsB, exB = slot_rows(S, S.score_B, B, keys, {n: e["B"] for n, e in entrants.items()}, B_SLOTS)
    if exA or exB:
        raise SystemExit("unexpected exclusions: %s %s" % (exA, exB))
    report = {}
    for n, e in entrants.items():
        prim = {wid: primary_A(S, e["A"].get(wid, {"label": "MISSING"}), keys[wid], infos[wid]) for wid in A}
        lab = {wid: e["A"].get(wid, {}).get("label", "MISSING") for wid in A}
        ans = {wid: keys[wid]["answer"] for wid in A}
        forks = [w for w in A if ans[w] == "FORK"]
        dets = [w for w in A if ans[w] == "DETERMINED"]
        rb = rowsB[n]
        soft = [r for r in rb if r["truth"] in ("BOUNDED", "UNCONSTRAINED")]
        conf = [r for r in rb if r["truth"] == "CONFLICT"]
        classes = sorted({r["truth"] for r in rb})
        recall = [sum(r["correct"] for r in rb if r["truth"] == c) / sum(1 for r in rb if r["truth"] == c)
                  for c in classes]
        bad = sum(v.get("label") in ("MISSING", "INVALID") for part in ("A", "B") for v in
                  [e[part].get(w, {"label": "MISSING"}) for w in (A if part == "A" else B)])
        m = {
            "A_primary_correct": sum(prim.values()),
            "A_strict_correct": sum(r["correct"] for r in strictA[n]),
            "A_fork_primary_correct": sum(prim[w] for w in forks),
            "A_over_claim": sum(lab[w] == "DETERMINED" for w in forks),
            "A_over_fork": sum(lab[w] == "FORK" for w in dets),
            "A_determined_correct": sum(prim[w] for w in dets),
            "A_contradictions_accepted": sum(lab[w] in ("DETERMINED", "FORK") for w in A
                                             if ans[w] == "CONTRADICTION"),
            "B_correct": sum(r["correct"] for r in rb),
            "B_balanced_accuracy": round(sum(recall) / len(recall), 4),
            "B_false_death": sum(r["label"] in S.EXACT_ZERO for r in soft),
            "B_conflicts_detected": sum(r["label"] == "CONFLICT" for r in conf),
            "missing_or_invalid": bad,
            "n": {"A": len(A), "A_fork": len(forks), "A_determined": len(dets), "B": len(B),
                  "B_soft": len(soft), "B_conflict": len(conf)},
            "per_world_A": {w: {"truth": ans[w], "label": lab[w], "primary": prim[w],
                                "strict": next(r["correct"] for r in strictA[n] if r["id"] == w)} for w in sorted(A)},
            "per_world_B": {r["id"]: {"truth": r["truth"], "label": r["label"], "correct": r["correct"]} for r in rb},
        }
        report[n] = m
    return report


def verdict(m):
    if (m["A_primary_correct"] >= 27 and m["A_over_claim"] <= 1 and m["B_correct"] >= 16
            and m["B_false_death"] == 0):
        return "NO_GAP"
    if (m["A_primary_correct"] <= 24 or m["A_over_claim"] >= 3 or m["B_correct"] <= 13
            or m["B_false_death"] >= 2):
        return "GAP"
    return "MIXED"


def reference_entrants():
    outs = json.load(open(os.path.join(T2, "results", "outputs.json"), encoding="utf-8"))
    ent = {}
    for name in ("procedure",) + A_SLOTS[1:] + B_SLOTS[1:]:
        ent["ref:" + name] = {"A": {w: o[name] for w, o in outs.items() if w.startswith("A-") and name in o},
                              "B": {w: o[name] for w, o in outs.items() if w.startswith("B-") and name in o}}
    return ent


def main(run_dirs):
    S = load_sealed()
    entrants, metas = reference_entrants(), {}
    for d in run_dirs:
        name = os.path.basename(os.path.normpath(d))
        parsed = json.load(open(os.path.join(d, "parsed.json"), encoding="utf-8"))["answers"]
        entrants[name] = {"A": {w: v for w, v in parsed.items() if w.startswith("A-")},
                          "B": {w: v for w, v in parsed.items() if w.startswith("B-")}}
        mp = os.path.join(d, "meta.json")
        metas[name] = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
    report = evaluate(entrants, S)
    models = [os.path.basename(os.path.normpath(d)) for d in run_dirs]
    proc = report["ref:procedure"]["per_world_A"]
    for n in models:
        m = report[n]
        m["verdict"] = verdict(m)
        m["format_flag"] = m["missing_or_invalid"] >= 10
        b = sum(proc[w]["primary"] and not m["per_world_A"][w]["primary"] for w in proc)
        c = sum(m["per_world_A"][w]["primary"] and not proc[w]["primary"] for w in proc)
        m["mcnemar_vs_procedure"] = {"b": b, "c": c, "p_one_sided": S.mcnemar_one_sided(b, c)}
        m["meta"] = metas.get(n, {})
    vs = [report[n]["verdict"] for n in models]
    overall = ("NO_MODELS" if not vs else "RULE_EXECUTION_EDGE_NOT_SUPPORTED" if "NO_GAP" in vs else
               "PRESENT_GAP_SUPPORTED" if vs and all(v == "GAP" for v in vs) else "MIXED")
    out = {"overall": overall, "models": models, "report": report}
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    with open(os.path.join(HERE, "results", "report_llm.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    cols = ["A_primary_correct", "A_strict_correct", "A_fork_primary_correct", "A_over_claim", "A_over_fork",
            "A_contradictions_accepted", "B_correct", "B_false_death", "B_conflicts_detected", "missing_or_invalid"]
    lines = ["entrant | " + " | ".join(cols) + " | verdict"]
    for n, m in report.items():
        lines.append("%s | %s | %s" % (n, " | ".join(str(m[c]) for c in cols), m.get("verdict", "-")))
    lines.append("overall: " + overall)
    txt = "\n".join(lines)
    with open(os.path.join(HERE, "results", "summary.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main(sys.argv[1:])
