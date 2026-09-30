"""Mutation test of the parser + wrapper BEFORE sealing (lesson of blind test 2).

Builds a "perfect" set of chat replies from the key (decisive sets taken from the frozen procedure's
outputs), then applies deliberate corruptions at the TEXT level and checks that every one changes the
scores exactly as expected, while harmless format variations change nothing.
Usage:  python tools/mutation_test.py        (exit code 0 only if every check passes)
"""
import copy
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse_answers as P  # noqa: E402
import score_llm as L  # noqa: E402

HERE = L.HERE
PLAN = json.load(open(os.path.join(HERE, "prompts", "batch_plan.json"), encoding="utf-8"))


def perfect_answers(S):
    A, B, keys = L.load_data()
    outs = json.load(open(os.path.join(L.T2, "results", "outputs.json"), encoding="utf-8"))
    ans = {}
    for w in A:
        k = keys[w]
        a = {"id": w, "label": k["answer"]}
        if k["answer"] == "DETERMINED":
            a["level"] = k["level"]
        if k["answer"] == "FORK":
            a["branches"] = [b["level"] for b in k["branches"]]
            a["decisive"] = outs[w]["procedure"]["decisive"]
        ans[w] = a
    for w in B:
        ref = S.reference_B(B[w])
        a = {"id": w, "label": ref["label"]}
        if ref["label"] == "BOUNDED":
            a["bound"] = ref["bound"]
        if ref["label"] == "ACTIVE":
            a["interval"] = ref["interval"]
        ans[w] = a
    return ans


def render(ans, batch, tail=None):
    items = [ans[w] for w in PLAN[batch] if w in ans]
    body = json.dumps(items, ensure_ascii=False, indent=1)
    return "Reasoning omitted.\n\n```json\n%s\n```\n%s" % (body, tail or "")


def texts_from(ans):
    return {b: render(ans, b) for b in PLAN}


def run_scenarios(scenarios, S):
    tmp = tempfile.mkdtemp(prefix="llmcmp_mut_")
    entrants = {}
    try:
        for name, texts in scenarios.items():
            d = os.path.join(tmp, name)
            os.makedirs(d)
            for b, t in texts.items():
                if t is not None:
                    open(os.path.join(d, b + ".txt"), "w", encoding="utf-8").write(t)
            parsed, _ = P.parse_model(d, PLAN)
            entrants[name] = {"A": {w: v for w, v in parsed.items() if w.startswith("A-")},
                              "B": {w: v for w, v in parsed.items() if w.startswith("B-")}}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return L.evaluate(entrants, S)


def main():
    S = L.load_sealed()
    base = perfect_answers(S)
    sc, expect = {}, {}

    def mut(name, change, **exp):
        ans = copy.deepcopy(base)
        texts = change(ans)
        sc[name] = texts if isinstance(texts, dict) else texts_from(ans)
        expect[name] = exp

    def set_(w, **kv):
        def f(ans):
            ans[w].update(kv)
            for k, v in list(kv.items()):
                if v is None:
                    ans[w].pop(k)
        return f

    P0 = dict(A_primary_correct=30, A_strict_correct=27, B_correct=18, missing_or_invalid=0,
              A_over_claim=0, A_over_fork=0, B_false_death=0, A_contradictions_accepted=0)
    mut("perfect", lambda a: None, **P0)
    mut("det_to_fork", set_("A-03", label="FORK", branches=["SUBSUMED", "comm"], level=None),
        A_primary_correct=29, A_over_fork=1)
    mut("fork_to_det", set_("A-07", label="DETERMINED", level="assoc", branches=None, decisive=None),
        A_primary_correct=29, A_over_claim=1, A_fork_primary_correct=9)
    mut("branches_reversed", lambda a: a["A-11"].update(branches=a["A-11"]["branches"][::-1]),
        A_primary_correct=29)
    mut("branch_dropped", lambda a: a["A-21"].update(branches=a["A-21"]["branches"][:-1]),
        A_primary_correct=29)
    mut("det_wrong_level", lambda a: a["A-03"].update(
        level={"SUBSUMED": "comm", "comm": "graded", "graded": "assoc", "assoc": "comm"}[a["A-03"]["level"]]),
        A_primary_correct=29)
    mut("contradiction_accepted", set_("A-05", label="DETERMINED", level="assoc"),
        A_primary_correct=29, A_contradictions_accepted=1)

    def harmless_case(a):
        for w in a:
            a[w]["label"] = a[w]["label"].lower().replace("_", " ")
        for w in a:
            if a[w].get("level") == "comm":
                a[w]["level"] = "Commutative"
            if "branches" in a[w]:
                a[w]["branches"] = [{"level": x.upper() if x == "assoc" else x} for x in a[w]["branches"]]
    mut("harmless_case_and_words", harmless_case, **P0)
    mut("bound_off", lambda a: a["B-02"].update(bound=str(L_frac(a["B-02"]["bound"]) + L_frac("1/1000"))),
        B_correct=17)
    mut("bound_decimal_inexact", set_("B-05", bound="0.0046"), B_correct=17)
    mut("bound_garbage", set_("B-13", bound="about 0.005"), B_correct=17, missing_or_invalid=1)
    mut("interval_off", lambda a: a["B-10"].update(interval=[a["B-10"]["interval"][0], "999"]), B_correct=17)
    mut("interval_malformed", set_("B-11", interval=["1/2"]), B_correct=17, missing_or_invalid=1)
    mut("false_death_symmetry", set_("B-02", label="SYMMETRY_ZERO", bound=None), B_correct=17, B_false_death=1)
    mut("false_death_incidental", set_("B-17", label="INCIDENTAL"), B_correct=17, B_false_death=1)
    mut("conflict_missed", set_("B-04", label="BOUNDED", bound="1"), B_correct=17, B_conflicts_detected=2)

    def id_typo(a):
        a["A-03"]["id"] = "A-3"
    mut("id_typo", id_typo, A_primary_correct=29, missing_or_invalid=1)

    def dup(right_last):
        def f(a):
            t = texts_from(a)
            wrong = dict(a["A-04"], label="CONTRADICTION")
            items = [wrong, a["A-04"]] if right_last else [a["A-04"], wrong]
            others = [a[w] for w in PLAN["A1"] if w != "A-04"]
            t["A1"] = "```json\n%s\n```" % json.dumps(others + items)
            return t
        return f
    mut("duplicate_right_last", dup(True), **P0)
    mut("duplicate_wrong_last", dup(False), A_primary_correct=29)

    def malformed(a):
        t = texts_from(a)
        t["B1"] = t["B1"].replace("]\n```", "\n```")
        return t
    mut("malformed_json_batch", malformed, B_correct=12, missing_or_invalid=6)

    def unfenced(a):
        t = texts_from(a)
        t["A2"] = "Final answer: " + json.dumps([a[w] for w in PLAN["A2"]]) + " done."
        return t
    mut("unfenced_list", unfenced, **P0)

    def trailing(a):
        t = texts_from(a)
        t["B2"] = t["B2"].replace("}\n]", "},\n]")
        return t
    mut("trailing_comma", trailing, **P0)

    def two_blocks(a):
        t = texts_from(a)
        wrong = [dict(a[w], label="CONFLICT") for w in PLAN["B3"]]
        t["B3"] = "Draft:\n```json\n%s\n```\nCorrected:\n%s" % (json.dumps(wrong), render(a, "B3"))
        return t
    mut("two_blocks_last_wins", two_blocks, **P0)

    def foreign_id(a):
        t = texts_from(a)
        items = [a[w] for w in PLAN["B1"]] + [dict(a["A-01"], label="FORK")]
        t["B1"] = "```json\n%s\n```" % json.dumps(items)
        return t
    mut("foreign_id_ignored", foreign_id, **P0)

    def flat_decisive(a):
        if len(a["A-07"]["branches"]) == 2 and len(a["A-07"]["decisive"]) == 1:
            a["A-07"]["decisive"] = a["A-07"]["decisive"][0]
    mut("flat_decisive_wrapped", flat_decisive, **P0)

    def missing_file(a):
        t = texts_from(a)
        t["A5"] = None
        return t
    mut("missing_batch_file", missing_file, A_primary_correct=24, missing_or_invalid=6)

    rep = run_scenarios(sc, S)
    fails = 0
    for name, exp in expect.items():
        m = rep[name]
        want = dict(P0)
        if name != "perfect":
            want.update({k: v for k, v in exp.items()})
            if "A_primary_correct" in exp and exp["A_primary_correct"] < 30 and "A_strict_correct" not in exp:
                want.pop("A_strict_correct")
        bad = {k: (m[k], v) for k, v in want.items() if m[k] != v}
        print("%-26s %s %s" % (name, "PASS" if not bad else "FAIL", bad or ""))
        fails += bool(bad)
    # verdict boundaries
    def vm(a, o, b, fd):
        return {"A_primary_correct": a, "A_over_claim": o, "B_correct": b, "B_false_death": fd}
    cases = [(vm(27, 1, 16, 0), "NO_GAP"), (vm(26, 1, 16, 0), "MIXED"), (vm(24, 0, 18, 0), "GAP"),
             (vm(30, 2, 18, 0), "MIXED"), (vm(30, 3, 18, 0), "GAP"), (vm(30, 0, 15, 0), "MIXED"),
             (vm(30, 0, 13, 0), "GAP"), (vm(30, 0, 18, 1), "MIXED"), (vm(30, 0, 18, 2), "GAP")]
    for m, want in cases:
        got = L.verdict(m)
        ok = got == want
        fails += not ok
        print("verdict %-40s %s (%s)" % (m, "PASS" if ok else "FAIL", got))
    # hash guard
    tmpd = tempfile.mkdtemp()
    try:
        cp = os.path.join(tmpd, "score_v2.py")
        shutil.copy(L.SCORER, cp)
        open(cp, "a").write("\n# tampered\n")
        try:
            L.load_sealed(cp)
            print("hash_guard FAIL (tampered scorer accepted)")
            fails += 1
        except SystemExit:
            print("hash_guard PASS")
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)
    print("TOTAL FAILURES:", fails)
    sys.exit(1 if fails else 0)


def L_frac(s):
    from fractions import Fraction
    return Fraction(s)


if __name__ == "__main__":
    main()
