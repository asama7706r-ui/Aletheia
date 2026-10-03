"""Score the parsed answers of the models against the blind-test-3 Part A key.

The reference is the test-3 key (key/key.json) and the sealed test-3 report (results/report.json).
Both are used unmodified, and this script refuses to run if either SHA-256 differs from the hash
published before the test-3 run. The report gives, per world, the NO_SCOPE baseline's answer and
the list of scope-sensitive worlds. Every key answer must equal the report's reference answer.

Pre-registered (protocol_llm2.md, sections 4 and 6):
- correct = same verdict, and the same relation (KNOWN) or the same branch set (FORK).
- per model and condition (N = question only, M = question plus method): accuracy (of 27),
  scope-sensitive correct (of 15), false familiarity (KNOWN or FORK on NEW worlds, of 9) and the
  other counts below.
- NO_GAP:  accuracy >= 24 and false familiarity <= 1 and scope-sensitive >= 13.
  GAP:     accuracy <= 21 or false familiarity >= 3 or scope-sensitive <= 11.
  MIXED:   otherwise.
- overall per condition, over the scored models: EDGE_NOT_SUPPORTED if any model is NO_GAP;
  GAP_SUPPORTED if every model is GAP; MIXED otherwise.
- interpretation: I1 if N is EDGE_NOT_SUPPORTED; I2 if N is GAP_SUPPORTED and M is
  EDGE_NOT_SUPPORTED; I3 if both are GAP_SUPPORTED; I4 otherwise (NONE if no model is scored).
Usage:
  python tools/score_llm2.py runs/<a> runs/<b> ...     (writes results/summary.txt and results/report_llm2.json)
  python tools/score_llm2.py --reference-check         (scores the test-3 procedure and baselines)
"""
import hashlib
import json
import os
import sys
from fractions import Fraction
from math import comb

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T3 = os.path.join(os.path.dirname(HERE), "aletheia_blind_test_3")
KEY_SHA = "daee204d4432e3774dcf512dae5311b08ee70cc2b8bef53816133503d92d1b34"
REPORT_SHA = "dd7034634bb5ce700e1ce6a9e73d465df5fa7ed3cc5ab46a5ff5c41c8755f822"
OUTPUTS_SHA = "393e65dacff9119600305e53b5faa339d744ecadabbe0626a2c7ee330cf15a9b"
REASONS = ("TYPE", "SYMMETRY", "SCOPE", "SHAPE", "BOUND")
CONDS = ("N", "M")


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def load_checked(rel, expected):
    path = os.path.join(T3, rel)
    got = sha256(path)
    if got != expected:
        raise SystemExit("REFUSED: %s has SHA-256 %s, expected %s" % (rel, got, expected))
    return json.load(open(path, encoding="utf-8"))


def norm(a):
    """(verdict, relation, branches) of an answer dict; None fields where they do not apply."""
    v = a.get("verdict")
    rel = a.get("relation") if v == "KNOWN" else None
    br = tuple(sorted(a.get("branches") or ())) if v == "FORK" else None
    return (v, rel, br)


def load_reference():
    key = load_checked(os.path.join("key", "key.json"), KEY_SHA)
    report = load_checked(os.path.join("results", "report.json"), REPORT_SHA)
    ref = {e["id"]: norm(e) for e in key["A"]}
    reasons = {e["id"]: {r: sorted(rs) for r, rs in (e.get("reasons") or {}).items()} for e in key["A"]}
    noscope = {}
    for pw in report["A"]["per_world"]:
        if norm(pw["reference"]) != ref[pw["id"]]:
            raise SystemExit("REFUSED: key and sealed report disagree on %s" % pw["id"])
        noscope[pw["id"]] = norm(pw["NO_SCOPE_answer"])
    if set(noscope) != set(ref) or len(ref) != 27:
        raise SystemExit("REFUSED: world sets differ")
    scope = sorted(report["A"]["composition"]["scope_sensitive"])
    return {"ref": ref, "reasons": reasons, "noscope": noscope, "scope": scope}


def tally(ans, R):
    ref, ids = R["ref"], sorted(R["ref"])
    def cls(*vs):
        return [w for w in ids if ref[w][0] in vs]
    ok = {w: norm(ans.get(w, {"verdict": "MISSING"})) == ref[w] for w in ids}
    v = {w: ans.get(w, {}).get("verdict", "MISSING") for w in ids}
    t = {
        "correct": [w for w in ids if ok[w]],
        "scope_correct": [w for w in R["scope"] if ok[w]],
        "scope_like_no_scope": [w for w in R["scope"] if norm(ans.get(w, {"verdict": "MISSING"})) == R["noscope"][w]],
        "false_novelty": [w for w in cls("KNOWN", "FORK") if v[w] == "NEW"],
        "false_familiarity": [w for w in cls("NEW") if v[w] in ("KNOWN", "FORK")],
        "fork_correct": [w for w in cls("FORK") if ok[w]],
        "over_fork": [w for w in cls("KNOWN") if v[w] == "FORK"],
        "planet_x": [w for w in cls("NO_DEFICIT") if v[w] in ("KNOWN", "FORK")],
        "missed_deficit": [w for w in cls("KNOWN", "FORK", "NEW") if v[w] == "NO_DEFICIT"],
        "missing": [w for w in ids if v[w] == "MISSING"],
        "invalid": [w for w in ids if v[w] == "INVALID"],
    }
    t["wrong"] = [w for w in ids if not ok[w]]
    n = {k: len(x) for k, x in t.items()}
    if n["correct"] >= 24 and n["false_familiarity"] <= 1 and n["scope_correct"] >= 13:
        verdict = "NO_GAP"
    elif n["correct"] <= 21 or n["false_familiarity"] >= 3 or n["scope_correct"] <= 11:
        verdict = "GAP"
    else:
        verdict = "MIXED"
    return {"counts": n, "lists": t, "verdict": verdict, "ok": ok,
            "format_flag": n["missing"] + n["invalid"] >= 6}


def binom_tail_ge(b, n):
    return sum(Fraction(comb(n, i), 2 ** n) for i in range(b, n + 1)) if n else Fraction(1)


def mcnemar_two_sided(b, c):
    n = b + c
    if n == 0:
        return Fraction(1)
    lo = sum(Fraction(comb(n, i), 2 ** n) for i in range(0, min(b, c) + 1))
    return min(Fraction(1), 2 * lo)


def reason_analysis(ans, R):
    """Exploratory (condition M): (candidate, reason) pairs against the key's reason sets."""
    out = {}
    for reason in REASONS:
        applicable = listed = true = 0
        for w, rs in R["reasons"].items():
            ref_pairs = {c for c, names in rs.items() if reason in names}
            got = ans.get(w, {}).get("excluded") or {}
            got_pairs = {c for c, names in got.items() if reason in names}
            applicable += len(ref_pairs)
            listed += len(got_pairs)
            true += len(ref_pairs & got_pairs)
        out[reason] = {"applicable": applicable, "listed": listed, "true": true,
                       "recall": str(Fraction(true, applicable)) if applicable else None,
                       "precision": str(Fraction(true, listed)) if listed else None}
    return out


def overall(verdicts):
    if not verdicts:
        return "NO_SCORED_MODELS"
    if any(v == "NO_GAP" for v in verdicts):
        return "EDGE_NOT_SUPPORTED"
    if all(v == "GAP" for v in verdicts):
        return "GAP_SUPPORTED"
    return "MIXED"


def interpretation(n_all, m_all):
    if n_all == "NO_SCORED_MODELS":
        return "NONE"
    if n_all == "EDGE_NOT_SUPPORTED":
        return "I1"
    if n_all == "GAP_SUPPORTED" and m_all == "EDGE_NOT_SUPPORTED":
        return "I2"
    if n_all == "GAP_SUPPORTED" and m_all == "GAP_SUPPORTED":
        return "I3"
    return "I4"


INTERP = {
    "I1": "Without the method, at least one frontier model reached the procedure's answers. No kernel edge on these worlds.",
    "I2": "Without the method every scored model showed a gap; with it, at least one did not. The value is in the written method, which any model can be given.",
    "I3": "Every scored model showed a gap with and without the method. A present gap for this kind of task, nothing more.",
    "I4": "Mixed. Reported as is; no claim.",
    "NONE": "No scored model.",
}


def score_entrants(entrants, R):
    """entrants: list of (slug, meta, {"N": answers, "M": answers})."""
    rep = {"models": {}, "reference": {"key_sha256": KEY_SHA, "report_sha256": REPORT_SHA,
                                       "scope_sensitive": R["scope"]}}
    for slug, meta, answers in entrants:
        m = {"meta": meta, "conditions": {}}
        for cond in CONDS:
            t = tally(answers.get(cond, {}), R)
            b = 27 - t["counts"]["correct"]
            m["conditions"][cond] = {"verdict": t["verdict"], "counts": t["counts"], "lists": t["lists"],
                                     "format_flag": t["format_flag"],
                                     "vs_procedure_p_one_sided": str(binom_tail_ge(b, b))}
            m["_ok_" + cond] = t["ok"]
        okN, okM = m.pop("_ok_N"), m.pop("_ok_M")
        b = sum(okM[w] and not okN[w] for w in okN)
        c = sum(okN[w] and not okM[w] for w in okN)
        m["method_effect"] = {"correct_in_M_only": b, "correct_in_N_only": c,
                              "mcnemar_two_sided_p": str(mcnemar_two_sided(b, c))}
        m["reasons_M_exploratory"] = reason_analysis(answers.get("M", {}), R)
        rep["models"][slug] = m
    scored = [s for s, meta, _ in entrants if meta.get("scored") is True]
    rep["scored_models"] = scored
    rep["overall"] = {c: overall([rep["models"][s]["conditions"][c]["verdict"] for s in scored]) for c in CONDS}
    rep["interpretation"] = interpretation(rep["overall"]["N"], rep["overall"]["M"])
    rep["interpretation_text"] = INTERP[rep["interpretation"]]
    return rep


def summary_text(rep):
    L = ["LLM comparison 2 - summary (blind-test-3 Part A worlds)",
         "reference: key %s..., report %s..." % (KEY_SHA[:12], REPORT_SHA[:12]), ""]
    for slug, m in rep["models"].items():
        meta = m["meta"]
        L.append("%s | %s | interface: %s | reasoning: %s | code: %s | scored: %s" % (
            slug, meta.get("name_as_shown", "?"), meta.get("interface", "?"),
            meta.get("reasoning_option", "?"), meta.get("code_execution", "?"), meta.get("scored")))
        for cond in CONDS:
            x = m["conditions"][cond]
            n = x["counts"]
            L.append("  %s: %s | correct %d/27 | scope-sensitive %d/15 (like NO_SCOPE %d) | false familiarity %d/9 | "
                     "false novelty %d/15 | forks %d/6 | over-fork %d | planet-X %d/3 | missed deficit %d | "
                     "missing %d | invalid %d%s" % (
                         cond, x["verdict"], n["correct"], n["scope_correct"], n["scope_like_no_scope"],
                         n["false_familiarity"], n["false_novelty"], n["fork_correct"], n["over_fork"],
                         n["planet_x"], n["missed_deficit"], n["missing"], n["invalid"],
                         " | FORMAT-FLAGGED" if x["format_flag"] else ""))
            L.append("     wrong: %s" % (", ".join(x["lists"]["wrong"]) or "-"))
        me = m["method_effect"]
        L.append("  method effect: correct in M only %d, in N only %d, McNemar two-sided p = %s" % (
            me["correct_in_M_only"], me["correct_in_N_only"], me["mcnemar_two_sided_p"]))
        ra = m["reasons_M_exploratory"]
        L.append("  reasons in M (exploratory): " + "; ".join(
            "%s recall %s precision %s" % (r, ra[r]["recall"], ra[r]["precision"]) for r in REASONS))
        L.append("")
    L.append("scored models: %s" % (", ".join(rep["scored_models"]) or "-"))
    L.append("OVERALL N (question only): %s" % rep["overall"]["N"])
    L.append("OVERALL M (with method):   %s" % rep["overall"]["M"])
    L.append("INTERPRETATION: %s - %s" % (rep["interpretation"], rep["interpretation_text"]))
    return "\n".join(L) + "\n"


def load_model(model_dir):
    meta = json.load(open(os.path.join(model_dir, "meta.json"), encoding="utf-8"))
    parsed = json.load(open(os.path.join(model_dir, "parsed.json"), encoding="utf-8"))
    return os.path.basename(os.path.normpath(model_dir)), meta, parsed["answers"]


def reference_entrants():
    outputs = load_checked(os.path.join("results", "outputs.json"), OUTPUTS_SHA)
    entrants = []
    for method in ("procedure", "NO_SCOPE", "ALWAYS_NEW", "DIMS_ONLY"):
        ans = {}
        for w, per in outputs["A"].items():
            o = per[method]
            a = {"verdict": o["verdict"]}
            if o["verdict"] == "KNOWN":
                a["relation"] = o["relation"]
            if o["verdict"] == "FORK":
                a["branches"] = o["branches"]
            if method == "procedure" and o.get("excluded") is not None:
                a["excluded"] = {r: x["reasons"] for r, x in o["excluded"].items()}
            ans[w] = a
        entrants.append((method, {"name_as_shown": method, "scored": False}, {"N": ans, "M": ans}))
    return entrants


def main(argv):
    R = load_reference()
    if argv == ["--reference-check"]:
        rep = score_entrants(reference_entrants(), R)
        sys.stdout.write(summary_text(rep))
        return rep
    rep = score_entrants([load_model(d) for d in argv], R)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    with open(os.path.join(HERE, "results", "report_llm2.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=1)
    text = summary_text(rep)
    with open(os.path.join(HERE, "results", "summary.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    sys.stdout.write(text)
    return rep


if __name__ == "__main__":
    main(sys.argv[1:])
