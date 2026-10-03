"""Scorer mutation test (development only), protocol section 6 lesson of blind test 2.

Starting from the dev worlds, the dev key and the procedure's dev outputs (all correct), it applies one
deliberate corruption at a time and checks that the frozen scorer catches it: corrupted keys and worlds
must be excluded; corrupted procedure outputs must be scored incorrect. The originals must be accepted.

Usage:  python mutation_test.py
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scorer"))
import score_v3 as S  # noqa: E402
import ref_v3  # noqa: E402

ref_v3.DEV_HASHES.clear()   # the dev worlds are the dev set itself (W10 would exclude them)

worlds = S.load_dir(os.path.join(HERE, "worlds"), "A")
items = S.load_dir(os.path.join(HERE, "data"), "B")
key = json.load(open(os.path.join(HERE, "key.json"), encoding="utf-8"))
outs = json.load(open(os.path.join(HERE, "results", "dev_outputs.json"), encoding="utf-8"))
KA = {k["id"]: k for k in key["A"]}
KB = {k["id"]: k for k in key["B"]}


def run(w=None, ka=None, kb=None, o=None):
    w, ka, kb, o = w or worlds, ka or KA, kb or KB, o or outs
    repA, valid = S.score_A(w, ka, o["A"])
    ob = dict(o["B"])
    ob["_A"] = o["A"]
    repB = S.score_B(w, valid, items, kb, ob)
    return repA, repB


def world_ok(repA, wid):
    return next((r["procedure"] for r in repA["per_world"] if r["id"] == wid), None)


def item_row(repB, did):
    return next((r for r in repB["per_item"] if r["id"] == did), None)


results = []


def check(name, cond):
    results.append((name, bool(cond)))
    print(("CAUGHT  " if cond else "MISSED  ") + name)


base_A, base_B = run()
assert not base_A["excluded"] and not base_B["excluded"], (base_A["excluded"], base_B["excluded"])
assert all(r["procedure"] for r in base_A["per_world"])
assert all(r["list_exact"] and r["verdicts_correct"] and not r["silent_changes"] for r in base_B["per_item"])
print("originals: all accepted and correct")

# ---------------------------------------------------------------- key corruptions -> exclusion
for name, wid, mut in [
        ("key: KNOWN relation changed", "dA-nebdim", lambda k: k.update(relation="R2")),
        ("key: NEW -> KNOWN", "dA-helium", lambda k: k.update(verdict="KNOWN", relation="R1")),
        ("key: FORK branch dropped", "dA-fork", lambda k: k.update(branches=["R1"])),
        ("key: FORK -> KNOWN", "dA-fork", lambda k: k.update(verdict="KNOWN", relation="R1")),
        ("key: NO_DEFICIT -> NEW", "dA-step0", lambda k: k.update(verdict="NEW")),
        ("key: wrong reason list", "dA-typesole", lambda k: k.update(reasons={"R1": ["BOUND"], "R2": ["SHAPE"]})),
        ("key: reason given for a sufficient candidate", "dA-nebdim", lambda k: k.update(reasons={"R1": ["BOUND"]}))]:
    ka = copy.deepcopy(KA)
    mut(ka[wid])
    a, _ = run(ka=ka)
    check(name, wid in a["excluded"])

for name, did, mut in [
        ("key B: reopened list wrong", "dB-nd", lambda k: k.update(reopened=["dA-nebdim", "dA-step0"])),
        ("key B: final verdict wrong", "dB-bowen", lambda k: k["final"].update({"dA-helium": {"verdict": "NEW"}})),
        ("key B: category wrong", "dB-nd", lambda k: k.update(type="rel_none")),
        ("key B: category of another item type", "dB-fall", lambda k: k.update(type="root_vanish"))]:
    kb = copy.deepcopy(KB)
    mut(kb[did])
    _, b = run(kb=kb)
    check(name, did in b["excluded"])

# ---------------------------------------------------------------- world corruptions -> exclusion
for name, wid, mut in [
        ("world: dimmer leaves [0, 1]", "dA-coronium",
         lambda w: w["ledger"][0]["coverage"]["factor"].update(expr="2*r/(1+r)")),
        ("world: old reading contradicts the base law", "dA-helium",
         lambda w: w["old_observations"][0].update(value="3")),
        ("world: reserved name", "dA-typesole",
         lambda w: w.update(quantities={"yc": {"L": 1}, "exp": {"T": 1}})),
        ("world: decimal number", "dA-visible", lambda w: w["new_observations"][0].update(value="4.0")),
        ("world: listed state on a switch threshold", "dA-nebsw",
         lambda w: w["new_observations"][0]["state"].update(nc="50")),
        ("world: symmetry not of the base law", "dA-symsole", lambda w: w.update(base_law="yd = kn*xf**2 + kn*xf")),
        ("world: combination explains a NEW world", "dA-helium",
         lambda w: w["ledger"].append({"id": "R4", "object": "ob1", "term": "xa*(xa-1)*(xa-2)/6",
                                       "coefficient": "unknown", "coverage": None}) or w["ledger"].append(
             {"id": "R5", "object": "ob2", "term": "xa*(xa-1)*(xa-2)/3", "coefficient": "unknown", "coverage": None}))]:
    w = copy.deepcopy(worlds)
    mut(w[wid])
    a, _ = run(w=w)
    check(name, wid in a["excluded"])

# ---------------------------------------------------------------- output corruptions -> incorrect


def out_mut(name, wid, fn):
    o = copy.deepcopy(outs)
    fn(o["A"][wid]["procedure"])
    a, _ = run(o=o)
    check(name, world_ok(a, wid) is False)


out_mut("output: verdict changed", "dA-helium", lambda p: p.update(verdict="KNOWN", relation="R1"))
out_mut("output: step-0 Farkas points at a satisfied inequality", "dA-helium",
        lambda p: p["step0"]["certificate"][0].update(obs="old", k=0))
out_mut("output: step-0 Farkas multiplier changed (unknown mu no longer cancels)", "dA-visible",
        lambda p: p["step0"]["certificate"][0].update(y=str(int(p["step0"]["certificate"][0]["y"].split("/")[0]) * 3)
                                                      + ("/" + p["step0"]["certificate"][0]["y"].split("/")[1]
                                                         if "/" in p["step0"]["certificate"][0]["y"] else "")))
out_mut("output: step-0 certificate removed", "dA-nebdim", lambda p: p["step0"].update(certificate=[]))
out_mut("output: KNOWN point made infeasible", "dA-nebdim",
        lambda p: p["explanations"]["R1"]["point"].update(lam="1000"))
out_mut("output: lam interval end changed", "dA-nebdim",
        lambda p: p["explanations"]["R1"]["intervals"].update(lam=[p["explanations"]["R1"]["intervals"]["lam"][0], "6"]))
out_mut("output: quarantine note range changed", "dA-nebdim",
        lambda p: p["explanations"]["R1"]["ranges"].__setitem__(0, ["0", "1"]))
out_mut("output: false reason added", "dA-helium",
        lambda p: p["excluded"]["R1"]["reasons"].append("SHAPE"))
out_mut("output: reasons removed", "dA-helium", lambda p: p["excluded"]["R1"].update(reasons=[]))
out_mut("output: BOUND certificate corrupted", "dA-helium",
        lambda p: p["excluded"]["R1"]["certificates"]["BOUND"].update(C=[]))
out_mut("output: SCOPE point corrupted", "dA-scopesole",
        lambda p: p["excluded"]["R1"]["certificates"]["SCOPE"]["C"].update(lam="9"))
out_mut("output: SHAPE certificate replaced", "dA-typesole",
        lambda p: p["excluded"]["R2"]["certificates"]["SHAPE"].update(S=[{"obs": "old", "k": 0, "side": "upper", "y": "1"}]))
out_mut("output: decisive set emptied", "dA-fork", lambda p: p.update(decisive=[]))
out_mut("output: decisive index wrong", "dA-fork", lambda p: p.update(decisive=[1]))
out_mut("output: FORK branch range changed", "dA-fork",
        lambda p: p["explanations"]["R2"]["ranges"].__setitem__(1, ["0", "0"]))
out_mut("output: NO_DEFICIT base note changed", "dA-step0",
        lambda p: p["explanations"]["BASE"]["ranges"].__setitem__(1, ["0", "0"]))
out_mut("output: visible interval changed", "dA-visible",
        lambda p: p["explanations"]["R1"]["intervals"].update(mu=["1", "3"]))


def outb_mut(name, did, fn, test):
    o = copy.deepcopy(outs)
    fn(o["B"][did]["procedure"])
    _, b = run(o=o)
    check(name, test(item_row(b, did)))


outb_mut("output B: extra file reopened and changed", "dB-nd",
         lambda p: (p["reopened"].append("dA-step0"),
                    p["verdicts"].update({"dA-step0": {"verdict": "NEW"}})),
         lambda r: not r["list_exact"] and r["silent_changes"])
outb_mut("output B: reopened file missing", "dB-bowen",
         lambda p: (p.update(reopened=[]), p.update(verdicts={})),
         lambda r: not r["list_exact"] and not r["verdicts_correct"])
outb_mut("output B: wrong new verdict", "dB-fall",
         lambda p: p["verdicts"]["dA-nebdim"].update(verdict="KNOWN", relation="R2"),
         lambda r: not r["verdicts_correct"])
outb_mut("output B: verdict reported outside the own list", "dB-inside",
         lambda p: p["verdicts"].update({"dA-nebdim": {"verdict": "NEW"}}),
         lambda r: r["silent_changes"])
outb_mut("output B: corrupted proof in a reopened verdict", "dB-precision",
         lambda p: p["verdicts"]["dA-helium"]["step0"].update(certificate=[]),
         lambda r: not r["verdicts_correct"])

n_caught = sum(c for _, c in results)
print("caught %d of %d corruptions" % (n_caught, len(results)))
sys.exit(0 if n_caught == len(results) else 1)
