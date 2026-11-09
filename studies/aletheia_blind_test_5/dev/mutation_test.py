"""Deliberate corruption (protocol_v5.md, Section 12; the lesson of test 2): every kind of wrong
certificate, wrong output, wrong key and invalid world must be caught. Uses the dev batch
(run dev/make_dev.py first). Exit 0 only if every corruption is caught and every clean case passes.
Usage: python -I dev/mutation_test.py"""
import copy
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scorer"))
import certs_v5 as C  # noqa: E402
import ref_v5 as RF  # noqa: E402
import validate_v5 as V  # noqa: E402
import score_v5 as SC  # noqa: E402

B = os.path.join(HERE, "batch_dev")
KEY = {e["id"]: e for e in json.load(open(os.path.join(B, "key", "key.json"), encoding="utf-8"))}
OUT = json.load(open(os.path.join(B, "outputs_dev.json"), encoding="utf-8"))
REG = V.load_seed()
fails = 0


def world(wid):
    return C.R.load(os.path.join(B, "worlds", wid + ".json"))


def check(label, caught):
    global fails
    print(("ok    " if caught else "MISS  ") + label)
    if not caught:
        fails += 1


def rejects(fn, *args):
    return not C.safe(fn, *args)[0]


def find(verdict, pred=lambda e: True):
    for wid, e in sorted(KEY.items()):
        if e["verdict"] == verdict and pred(e):
            return wid, e
    raise SystemExit(f"no dev world with verdict {verdict}")


# ---------------------------------------------------------------- certificates
wid, e = find("BRANCHES", lambda e: any(b["witness"] and b["witness"]["dim"] == 4 for b in e["branches"]))
info = C.world_info(world(wid))
b = next(b for b in e["branches"] if b["witness"] and b["witness"]["dim"] == 4)
w = b["witness"]
check("clean witness accepted", not rejects(C.check_witness, w, info, b["drop"]))
m = copy.deepcopy(w)
m["table"][0][3] = "1" if m["table"][0][3] != "1" else "-1"
check("witness: a changed structure constant", rejects(C.check_witness, m, info, b["drop"]))
m = copy.deepcopy(w)
g = sorted(m["gens"])[0]
m["gens"][g] = ["0"] * m["dim"]
m["gens"][g][0] = "1"
check("witness: a wrong generator value", rejects(C.check_witness, m, info, b["drop"]))
m = copy.deepcopy(w)
if m.get("q12"):
    m["q12"]["N"] = [[("-1" if i == j and i == 1 else x) for j, x in enumerate(r)] for i, r in enumerate(m["q12"]["N"])]
    check("witness: a norm that is not positive definite", rejects(C.check_witness, m, info, b["drop"]))
smaller = [x for x in b["drop"] if x != "q14"]
check("witness: claims q14 in dimension > 1", rejects(C.check_witness, w, info, smaller))
check("witness: claims a smaller candidate than it has", rejects(C.check_witness, w, info, b["drop"][1:]))

ref = next((r for r in e["refutations"]), None)
check("clean refutation accepted", not rejects(C.check_refutation, ref["proof"], info, ref["drop"]))
m = copy.deepcopy(ref["proof"])


def first_close(node):
    if node["node"] in ("close", "positive"):
        return node
    return first_close(node["children"][0])


nd = first_close(m["tree"])
if nd["terms"]:
    nd["terms"][0][0] = "7" if nd["terms"][0][0] != "7" else "5"
check("refutation: a changed coefficient", rejects(C.check_refutation, m, info, ref["drop"]))
bigger = sorted(set(ref["drop"]) | {"q12", "q14"} & set(C.judged_units(info["origin"], info["frames"])))
check("refutation: used for a candidate that drops the units it needs", bigger == sorted(ref["drop"]) or
      rejects(C.check_refutation, ref["proof"], info, bigger))
m = {"theta": None, "tree": {"node": "positive", "t": [[["1", "ia"]]], "c": "-1", "terms": []}}
check("refutation: positivity with c <= 0", rejects(C.check_refutation, m, info, ["q6"]))

wk, ek = find("KNOWN_SUFFICES", lambda e: e["known"].get("theta"))
ik = C.world_info(world(wk))
check("clean known-kind solution accepted", not rejects(C.check_known, ek["known"], ik))
m = copy.deepcopy(ek["known"])
g = sorted(m["values"])[0]
m["values"][g] = ["1"] + ["0"] * (len(m["theta"]["poly"]) - 2) if isinstance(m["values"][g][0], str) else m["values"][g]
check("known: a wrong value", rejects(C.check_known, m, ik))
m = copy.deepcopy(ek["known"])
m["theta"]["lo"], m["theta"]["hi"] = "-10", "10"
check("known: theta's interval holds two roots", rejects(C.check_known, m, ik))

wi, ei = find("IMPOSSIBLE")
check("IMPOSSIBLE accepted on an impossible world", not rejects(C.check_impossible, {"kind": ei["impossible"]["kind"]}, C.world_info(world(wi))))
check("IMPOSSIBLE rejected on a possible world", rejects(C.check_impossible, {"kind": "values"}, info))

wm, em = find("NO_WITNESS", lambda e: any(b.get("mirror") for b in e["branches"]))
im = C.world_info(world(wm))
bm = next(b for b in em["branches"] if b.get("mirror"))
check("clean mirror accepted", not rejects(C.check_mirror, bm["mirror"], bm["drop"], bm["mirror"]["twin"], im))
check("mirror: a twin that is not the mirror", rejects(C.check_mirror, bm["mirror"], bm["drop"], bm["drop"], im))
check("mirror: on a world that is not mirror-invariant", rejects(C.check_mirror, {"perm": {"ia": "ia", "jb": "jb"}}, ["q5"], ["q6"], info))

# ---------------------------------------------------------------- outputs (scorer)
o = copy.deepcopy(OUT[wid]["procedure"])
truth = RF.truth(world(wid), V.key_pool(e, info))
check("clean output: decision correct", V.decision_equal(o, truth))
check("clean output: marks correct", SC.marks_correct(o, truth, info))
m = copy.deepcopy(o)
m["verdict"] = "NEW_KIND"
m["branches"] = m["branches"][:1]
check("output: one branch dropped is a silent choice", SC.silent_choice(m, truth) and not V.decision_equal(m, truth))
m = copy.deepcopy(o)
m["branches"][0]["marks"]["q5"] = "FRAME"
check("output: a wrong mark", not SC.marks_correct(m, truth, info))
m = copy.deepcopy(o)
u = m["branches"][0]["drop"][0]
m["branches"][0]["proofs"].pop(u, None)
check("output: a FORCED unit without a proof", not SC.marks_correct(m, truth, info))
m = copy.deepcopy(o)
wb = next(x for x in m["branches"] if x["witness"])
wb["witness"]["table"][0][3] = "1" if wb["witness"]["table"][0][3] != "1" else "-1"
pool, problems = SC.output_pool(m, info)
check("output: a false witness is counted", bool(problems["false_witness"]))
m = copy.deepcopy(o)
m["branches"].append({"drop": ["q14"], "status": "no_witness", "witness": None, "marks": {}, "proofs": {}, "mirror": None})
check("output: an added branch that a proof refutes", not V.decision_equal(m, truth))
m = copy.deepcopy(o)
m["branches"][0]["status"] = "no_witness" if m["branches"][0]["status"] == "witnessed" else "witnessed"
check("output: a wrong status", not V.decision_equal(m, truth))

# ---------------------------------------------------------------- worlds and keys (validator)
def vworld(doc, entry):
    path = os.path.join(HERE, "_mut_world.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)
    r = V.validate_world(path, entry, REG, set())
    os.remove(path)
    return r["errors"]


d0, e0 = world(wid), KEY[wid]
check("clean world and key: no validity error", vworld(d0, e0) == [])
m = copy.deepcopy(e0)
m["verdict"] = "NEW_KIND"
check("key: a wrong verdict (V9)", any(x.startswith("V9") for x in vworld(d0, m)))
m = copy.deepcopy(e0)
mb = next(x for x in m["branches"] if x["witness"])
mb["witness"]["table"][0][3] = "1" if mb["witness"]["table"][0][3] != "1" else "-1"
check("key: a corrupted witness (V9)", any(x.startswith("V9") for x in vworld(d0, m)))
m = copy.deepcopy(e0)
m["traps"] = ["T12"]
check("key: a declared trap that does not hold (V12)", any(x.startswith("V12") for x in vworld(d0, m)))
dm = copy.deepcopy(d0)
dm["builds"][0]["generators"] = ["a", "jb"]
dm["builds"][0]["role"] = [s.replace("ia", "a") for s in dm["builds"][0]["role"]]
check("world: a one-letter name (V2)", any(x.startswith("V2") for x in vworld(dm, e0)))
dm = copy.deepcopy(d0)
dm["builds"][0]["role"].append("ia*jb*ia*jb*ia = 1")
check("world: a product of more than P2 factors (V2)", any(x.startswith("V2") for x in vworld(dm, e0)))
dm = copy.deepcopy(d0)
dm["builds"][0]["role"].append("ia != 101")
check("world: a number above 100 (V2)", any(x.startswith("V2") for x in vworld(dm, e0)))
dm = copy.deepcopy(d0)
dm["builds"][0]["role"].append("ia^-1 = jb")
check("world: ^-1 on a new generator (V2)", any(x.startswith("V2") for x in vworld(dm, e0)))
dm = copy.deepcopy(d0)
dm["builds"].append(copy.deepcopy(dm["builds"][0]))
dm["builds"][1]["id"] = "bld2"
check("world: two builds (V2 or the reader)", vworld(dm, e0) != [])
wf, ef = find("FREEDOM")
df = world(wf)
df["builds"][0]["role"].append(f"{df['builds'][0]['generators'][0]} != 3")
check("world: a FREEDOM role that is not definitions (V3)", any(x.startswith("V3") for x in vworld(df, ef)))
wn, en = find("NO_WITNESS")
m = copy.deepcopy(en)
m["top_witness"] = None
check("key: a NO_WITNESS world without its top witness (V8)", any(x.startswith("V8") for x in vworld(world(wn), m)))
fps = set(json.load(open(V.DEV_FP, encoding="utf-8")))
r = V.validate_world(os.path.join(B, "worlds", wid + ".json"), e0, REG, fps)
check("world: a dev world is rejected (V11)", any(x.startswith("V11") for x in r["errors"]))

print("\nevery corruption caught" if fails == 0 else f"\n{fails} NOT CAUGHT")
sys.exit(1 if fails else 0)
