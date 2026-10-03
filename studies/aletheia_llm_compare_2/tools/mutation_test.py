"""Pre-seal checks of the parser and the scorer (protocol_llm2.md, section 9).

Builds synthetic replies from the key's answers, writes them as run files in a temporary folder,
parses and scores them, and checks every count and label against the expected change:
 - harmless variants change nothing;
 - each corruption changes exactly the expected counts;
 - verdict-boundary cases give the pre-registered labels;
 - overall labels and interpretations follow section 6;
 - the hash guard refuses a tampered key.
Usage:  python tools/mutation_test.py
"""
import copy
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse_answers as P  # noqa: E402
import score_llm2 as S  # noqa: E402

HERE = S.HERE
PLAN = json.load(open(os.path.join(HERE, "prompts", "batch_plan.json"), encoding="utf-8"))
R = S.load_reference()
IDS = sorted(R["ref"])
FAILS = []


def answer_obj(wid, triple, cond, reasons=True):
    v, rel, br = triple
    a = {"id": wid, "verdict": v}
    if v == "KNOWN":
        a["relation"] = rel
    if v == "FORK":
        a["branches"] = list(br)
    if cond == "M" and reasons and v != "NO_DEFICIT":
        a["excluded"] = R["reasons"][wid]
    return a


def perfect():
    return {c: {w: answer_obj(w, R["ref"][w], c) for w in IDS} for c in S.CONDS}


def write_run(d, answers, render=None, skip=()):
    os.makedirs(d, exist_ok=True)
    for batch, ids in PLAN.items():
        if batch in skip:
            continue
        objs = [answers[batch[0]][w] for w in ids if w in answers[batch[0]]]
        text = render(objs, batch) if render else "Working...\n```json\n%s\n```\n" % json.dumps(objs, indent=1)
        open(os.path.join(d, batch + ".txt"), "w", encoding="utf-8").write(text)
    json.dump({"name_as_shown": os.path.basename(d), "scored": True}, open(os.path.join(d, "meta.json"), "w"))


def run(answers, render=None, skip=()):
    d = tempfile.mkdtemp()
    try:
        write_run(os.path.join(d, "m"), answers, render, skip)
        parsed, _ = P.parse_model(os.path.join(d, "m"), PLAN)
        rep = S.score_entrants([("m", {"scored": True}, parsed)], R)
        return rep["models"]["m"], parsed
    finally:
        shutil.rmtree(d)


def check(name, cond_ok):
    print(("ok   " if cond_ok else "FAIL ") + name)
    if not cond_ok:
        FAILS.append(name)


def counts(m, cond):
    return m["conditions"][cond]["counts"]


BASE, _ = run(perfect())
BASE_N = counts(BASE, "N")
check("perfect answers: 27/27, NO_GAP in both conditions",
      BASE_N["correct"] == 27 and counts(BASE, "M")["correct"] == 27
      and all(BASE["conditions"][c]["verdict"] == "NO_GAP" for c in S.CONDS))
check("perfect reasons in M: recall and precision 1 for all five",
      all(BASE["reasons_M_exploratory"][r]["recall"] == "1" and BASE["reasons_M_exploratory"][r]["precision"] == "1"
          for r in S.REASONS))


def same_as_base(name, answers=None, render=None):
    m, _ = run(answers or perfect(), render)
    check("harmless: " + name, counts(m, "N") == BASE_N and counts(m, "M") == counts(BASE, "M")
          and m["reasons_M_exploratory"] == BASE["reasons_M_exploratory"])


def variant(fn):
    a = perfect()
    for c in S.CONDS:
        for w in IDS:
            fn(a[c][w])
    return a


same_as_base("lower-case verdicts", variant(lambda x: x.__setitem__("verdict", x["verdict"].lower())))
same_as_base("verdict with spaces/hyphens",
             variant(lambda x: x.__setitem__("verdict", x["verdict"].replace("_", " ").replace("NO ", "no-"))))
same_as_base("'label' instead of 'verdict'", variant(lambda x: x.__setitem__("label", x.pop("verdict"))))
same_as_base("lower-case ids and candidate ids", variant(lambda x: (
    x.__setitem__("id", x["id"].lower()),
    "relation" in x and x.__setitem__("relation", x["relation"].lower()))))
same_as_base("relation given as one-element list",
             variant(lambda x: "relation" in x and x.__setitem__("relation", [x["relation"]])))
same_as_base("branches reversed and duplicated",
             variant(lambda x: "branches" in x and x.__setitem__("branches", x["branches"][::-1] + x["branches"][:1])))
same_as_base("extra fields ignored", variant(lambda x: x.__setitem__("confidence", "high")))
same_as_base("trailing commas", render=lambda objs, b: "```json\n%s\n```" % json.dumps(objs).replace("}]", "},]"))
same_as_base("prose and an earlier code block",
             render=lambda objs, b: "First:\n```python\nprint(1)\n```\nNow:\n```json\n%s\n```\nDone." % json.dumps(objs))
same_as_base("untagged final block", render=lambda objs, b: "```\n%s\n```" % json.dumps(objs))
same_as_base("bare list without a fence", render=lambda objs, b: "Answer: %s" % json.dumps(objs))
same_as_base("wrapped in a dict", render=lambda objs, b: "```json\n%s\n```" % json.dumps({"answers": objs}))
same_as_base("repeated id: the last one counts",
             render=lambda objs, b: "```json\n%s\n```" % json.dumps(
                 [dict(objs[0], verdict="NEW" if objs[0]["verdict"] != "NEW" else "KNOWN", relation="R1")] + objs))

# --- corruptions -------------------------------------------------------------
by = {v: [w for w in IDS if R["ref"][w][0] == v] for v in ("KNOWN", "FORK", "NEW", "NO_DEFICIT")}
scope = set(R["scope"])


def corrupt(name, cond, wid, new, expect):
    a = perfect()
    a[cond][wid] = new
    m, _ = run(a)
    got = counts(m, cond)
    if wid in scope and S.norm(P.normalize(new, cond)) == R["noscope"][wid]:
        expect = dict(expect, scope_like_no_scope=1)
    diff = {k: got[k] - BASE_N[k] for k in got if got[k] != BASE_N[k]}
    other = "M" if cond == "N" else "N"
    check("corrupt: %s -> %s" % (name, diff), diff == expect and counts(m, other) == BASE_N)


def exp(wid, **kw):
    e = {"correct": -1, "wrong": 1}
    if wid in scope:
        e["scope_correct"] = -1
    e.update(kw)
    return {k: v for k, v in e.items() if v}


w = by["KNOWN"][0]
other_cand = "R9"
corrupt("KNOWN with the wrong relation", "N", w, {"id": w, "verdict": "KNOWN", "relation": other_cand}, exp(w))
corrupt("KNOWN answered NEW (false novelty)", "M", w, {"id": w, "verdict": "NEW"}, exp(w, false_novelty=1))
corrupt("KNOWN answered FORK (over-fork)", "N", w,
        {"id": w, "verdict": "FORK", "branches": [R["ref"][w][1], other_cand]}, exp(w, over_fork=1))
w = by["NEW"][0]
corrupt("NEW answered KNOWN (false familiarity)", "N", w, {"id": w, "verdict": "KNOWN", "relation": "R1"},
        exp(w, false_familiarity=1))
w = by["FORK"][0]
corrupt("FORK missing a branch", "N", w, {"id": w, "verdict": "FORK", "branches": list(R["ref"][w][2][:1])},
        exp(w, fork_correct=-1))
corrupt("FORK answered NO_DEFICIT (missed deficit)", "M", w, {"id": w, "verdict": "NO_DEFICIT"},
        exp(w, fork_correct=-1, missed_deficit=1))
w = by["NO_DEFICIT"][0]
corrupt("NO_DEFICIT answered KNOWN (planet-X)", "N", w, {"id": w, "verdict": "KNOWN", "relation": "R1"},
        exp(w, planet_x=1))
w = IDS[3]
corrupt("unknown verdict word (INVALID)", "N", w, {"id": w, "verdict": "MAYBE"}, exp(w, invalid=1))
w = by["KNOWN"][1]
corrupt("KNOWN without a relation (INVALID)", "M", w, {"id": w, "verdict": "KNOWN"}, exp(w, invalid=1))

a = perfect()
del a["N"][IDS[0]]
m, _ = run(a)
check("a missing answer counts as MISSING and wrong",
      counts(m, "N")["missing"] == 1 and counts(m, "N")["correct"] == 26)

m, _ = run(perfect(), skip=("N2",))
check("a missing batch file: 7 MISSING, format flag", counts(m, "N")["missing"] == 7
      and m["conditions"]["N"]["format_flag"] and not m["conditions"]["M"]["format_flag"])

a = perfect()
for w in R["scope"]:
    v, rel, br = R["noscope"][w]
    a["N"][w] = answer_obj(w, (v, rel, br), "N")
m, _ = run(a)
check("NO_SCOPE answers on the 15 scope-sensitive worlds: scope 0/15, like NO_SCOPE 15, GAP",
      counts(m, "N")["scope_correct"] == 0 and counts(m, "N")["scope_like_no_scope"] == 15
      and m["conditions"]["N"]["verdict"] == "GAP")

a = perfect()
for w in R["scope"][:3]:
    a["N"][w] = {"id": w, "verdict": "MAYBE"}
m, _ = run(a)
check("method effect: 3 correct in M only -> two-sided McNemar p = 1/4",
      m["method_effect"]["correct_in_M_only"] == 3 and m["method_effect"]["correct_in_N_only"] == 0
      and m["method_effect"]["mcnemar_two_sided_p"] == "1/4")

a = perfect()
a["M"][by["NEW"][0]]["excluded"] = {r: ["SHAPE"] for r in R["reasons"][by["NEW"][0]]}
m, _ = run(a)
check("exploratory reasons react to a changed reason list", m["reasons_M_exploratory"] != BASE["reasons_M_exploratory"]
      and counts(m, "M") == BASE_N)

# --- verdict boundaries ------------------------------------------------------
plain = [w for w in IDS if w not in scope and R["ref"][w][0] != "NEW"]       # wrong here: accuracy only
scope_nonnew = [w for w in R["scope"] if R["ref"][w][0] != "NEW"]          # wrong here: accuracy + scope
new_ws = by["NEW"]                                                         # KNOWN here: + false familiarity


def wrong_on(acc_only=0, scope_only=0, ff=0):
    a = perfect()
    for w in plain[:acc_only] + scope_nonnew[:scope_only]:
        a["N"][w] = {"id": w, "verdict": "MAYBE"}
    for w in new_ws[:ff]:
        a["N"][w] = {"id": w, "verdict": "KNOWN", "relation": "R1"}
    m, _ = run(a)
    return m["conditions"]["N"]["verdict"], counts(m, "N")


def boundary(name, expect, **kw):
    v, n = wrong_on(**kw)
    check("boundary %s: correct %d, scope %d, ff %d -> %s" % (name, n["correct"], n["scope_correct"],
                                                             n["false_familiarity"], v), v == expect)


assert len(plain) >= 6 and len(scope_nonnew) >= 4
boundary("acc 24", "NO_GAP", acc_only=3)
boundary("acc 23", "MIXED", acc_only=4)
boundary("acc 22", "MIXED", acc_only=5)
boundary("acc 21", "GAP", acc_only=6)
boundary("ff 1", "NO_GAP", ff=1)
boundary("ff 2", "MIXED", ff=2)
boundary("ff 3", "GAP", ff=3)
boundary("scope 13", "NO_GAP", scope_only=2)
boundary("scope 12", "MIXED", scope_only=3)
boundary("scope 11", "GAP", scope_only=4)

# --- overall labels ----------------------------------------------------------
check("overall: one NO_GAP among GAPs -> EDGE_NOT_SUPPORTED", S.overall(["GAP", "NO_GAP", "GAP"]) == "EDGE_NOT_SUPPORTED")
check("overall: all GAP -> GAP_SUPPORTED", S.overall(["GAP", "GAP"]) == "GAP_SUPPORTED")
check("overall: MIXED and GAP -> MIXED", S.overall(["MIXED", "GAP"]) == "MIXED")
check("overall: no scored model", S.overall([]) == "NO_SCORED_MODELS")
check("interpretations I1-I4 and NONE", [S.interpretation(*p) for p in (
    ("EDGE_NOT_SUPPORTED", "GAP_SUPPORTED"), ("GAP_SUPPORTED", "EDGE_NOT_SUPPORTED"),
    ("GAP_SUPPORTED", "GAP_SUPPORTED"), ("MIXED", "EDGE_NOT_SUPPORTED"), ("GAP_SUPPORTED", "MIXED"),
    ("NO_SCORED_MODELS", "NO_SCORED_MODELS"))] == ["I1", "I2", "I3", "I4", "I4", "NONE"])

two = tempfile.mkdtemp()
try:
    a = perfect()
    write_run(os.path.join(two, "good"), a)
    bad = perfect()
    for w in R["scope"]:
        bad["N"][w] = {"id": w, "verdict": "MAYBE"}
    write_run(os.path.join(two, "bad"), bad)
    ents = []
    for d in ("good", "bad"):
        parsed, _ = P.parse_model(os.path.join(two, d), PLAN)
        ents.append((d, {"scored": d == "good"}, parsed))
    rep = S.score_entrants(ents, R)
    check("unscored models do not enter the overall result", rep["scored_models"] == ["good"]
          and rep["overall"]["N"] == "EDGE_NOT_SUPPORTED")
finally:
    shutil.rmtree(two)

# --- hash guard ---------------------------------------------------------------
tmp = tempfile.mkdtemp()
try:
    for sub in ("key", "results"):
        os.makedirs(os.path.join(tmp, sub))
    shutil.copyfile(os.path.join(S.T3, "results", "report.json"), os.path.join(tmp, "results", "report.json"))
    key = json.load(open(os.path.join(S.T3, "key", "key.json"), encoding="utf-8"))
    key2 = copy.deepcopy(key)
    key2["A"][0]["verdict"] = "KNOWN"
    json.dump(key2, open(os.path.join(tmp, "key", "key.json"), "w"))
    saved, S.T3 = S.T3, tmp
    try:
        S.load_reference()
        refused = False
    except SystemExit as e:
        refused = str(e).startswith("REFUSED")
    finally:
        S.T3 = saved
    check("hash guard refuses a tampered key", refused)
finally:
    shutil.rmtree(tmp)

print("\n%d failures" % len(FAILS))
sys.exit(1 if FAILS else 0)
