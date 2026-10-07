# Test 4 dev tool: deliberate corruption of outputs, worlds and keys (lesson of test 2).
#   python mutation_test.py
# Part A corrupts the procedure's dev outputs; the scorer must mark each corrupted card incorrect (8.1/8.2).
# Part B corrupts dev worlds and keys; the reference/validator must reject each one with the expected rule.
# Every mutation that is not caught is printed; the script exits 1 if any is missed.
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scorer"))
import ref_v4 as R  # noqa: E402
import score_v4 as S  # noqa: E402

R.ALLOW_DEV = True
REG = R.load_registry()
WDIR = os.path.join(HERE, "worlds")
OUT = R.load_json(os.path.join(HERE, "results", "dev_outputs.json"))
KEY = {e["id"]: e for e in R.load_json(os.path.join(HERE, "key.json"))}
missed, caught = [], 0


def expect(ok_detected, label):
    global caught
    if ok_detected:
        caught += 1
    else:
        missed.append(label)


# ================================================================= Part A: corrupted procedure outputs

def filler_mutations(c):
    """yield (label, mutated filler output)"""
    other = {"SAME_LAW_NEW_STATE": "ANOTHER_LAW", "ANOTHER_LAW": "SAME_LAW_NEW_STATE",
             "INVALID": "ANOTHER_LAW", "CONDITIONAL": "SAME_LAW_NEW_STATE"}

    def m(fn):
        x = copy.deepcopy(c)
        fn(x)
        return x
    yield "verdict", m(lambda x: x.__setitem__("verdict", other[x["verdict"]]))
    yield "reason add", m(lambda x: x["reason"].append({"item": "F3"}))
    if c["reason"]:
        yield "reason drop", m(lambda x: x["reason"].pop())
    yield "F1 flip", m(lambda x: x["F1"].__setitem__("consistent", not x["F1"]["consistent"]))
    for q, d in c["F1"]["inferred_dims"].items():
        if isinstance(d, dict):
            yield "F1 dims", m(lambda x, q=q: x["F1"]["inferred_dims"][q].__setitem__(
                "L", x["F1"]["inferred_dims"][q].get("L", 0) + 1))
        break
    yield "F1 dims extra", m(lambda x: x["F1"]["inferred_dims"].__setitem__("zz9", {"M": 1}))
    for t, r in c["F2"].items():
        st = r["status"]
        for new in ("no_change", "changed", "conditional"):
            if new != st:
                yield f"F2 {t} status", m(lambda x, t=t, new=new: x["F2"][t].__setitem__("status", new))
        yield f"F2 {t} unknowns", m(lambda x, t=t: x["F2"][t]["unknowns"].append("zz9:" + t))
        yield f"F2 {t} removed", m(lambda x, t=t: x["F2"].pop(t))
        for i, a in enumerate(r["assignments"]):
            for side in ("old", "new"):
                if a[side] == "unchanged":
                    yield f"F2 {t} fake point", m(lambda x, t=t, i=i, side=side: x["F2"][t]["assignments"][i].__setitem__(
                        side, {"point": {k: "1" for k in ("qa", "qb", "dd", "kk")}}))
                else:
                    yield f"F2 {t} point->unchanged", m(lambda x, t=t, i=i, side=side:
                                                        x["F2"][t]["assignments"][i].__setitem__(side, "unchanged"))
                    yield f"F2 {t} point emptied", m(lambda x, t=t, i=i, side=side:
                                                     x["F2"][t]["assignments"][i][side].__setitem__("point", {}))
                    yield f"F2 {t} point zeroed", m(lambda x, t=t, i=i, side=side:
                                                    x["F2"][t]["assignments"][i][side].__setitem__(
                                                        "point", {k: "0" for k in x["F2"][t]["assignments"][i][side]["point"]}))
        if r["assignments"]:
            yield f"F2 {t} assignment dropped", m(lambda x, t=t: x["F2"][t]["assignments"].pop())
        if st == "conditional":
            yield f"F2 {t} keeping flipped", m(lambda x, t=t: x["F2"][t].__setitem__(
                "keeping", [{k: -v for k, v in kp.items()} for kp in x["F2"][t]["keeping"]]))
            yield f"F2 {t} matters emptied", m(lambda x, t=t: x["F2"][t].__setitem__("matters", []))
    yield "F3 flip", m(lambda x: x["F3"].__setitem__("holds", not x["F3"]["holds"]))
    if c["F3"]["holds"] and c["F3"]["point"]:
        k0 = sorted(c["F3"]["point"])[0]
        yield "F3 point missing", m(lambda x: x["F3"]["point"].pop(k0))
        yield "F3 point far", m(lambda x: x["F3"].__setitem__("point", {k: "1000000000" for k in x["F3"]["point"]}))
    if not c["F3"]["holds"]:
        if len(c["F3"]["farkas"]) > 1:   # one violated inequality alone stays valid when scaled
            yield "F3 farkas doubled", m(lambda x: x["F3"]["farkas"][0].__setitem__(
                "y", str(2 * R.num(x["F3"]["farkas"][0]["y"], limit=False))))
        yield "F3 farkas other side", m(lambda x: x["F3"]["farkas"][0].__setitem__(
            "side", "upper" if x["F3"]["farkas"][0]["side"] == "lower" else "lower"))
        yield "F3 farkas dropped", m(lambda x: x["F3"]["farkas"].pop())
        yield "F3 farkas negative", m(lambda x: x["F3"]["farkas"][0].__setitem__("y", "-1"))
    if c["verdict"] == "CONDITIONAL":
        yield "decisive instrument", m(lambda x: x["decisive"][0]["measure"][0].__setitem__("instrument", "i01"))
        yield "decisive emptied", m(lambda x: x["decisive"][0].__setitem__("measure", []))
        yield "decisive removed", m(lambda x: x.pop("decisive"))
    yield "error output", {"error": "crash"}


def part_a():
    for fn in R.world_files(WDIR):
        wid = fn[:-5]
        rw, cards = R.reference(R.load_json(os.path.join(WDIR, fn)), REG)
        for F in rw.fillers:
            c = OUT[wid]["procedure"]["fillers"][F.id]
            if R.check_filler_output(rw, F, cards[F.id], c):
                missed.append(f"A {wid}/{F.id}: the true output is marked incorrect")
            for label, mut in filler_mutations(c):
                probs = R.check_filler_output(rw, F, cards[F.id], mut)
                if label == "F3 point far" and not probs:
                    continue    # a far point may still be feasible when the system is unbounded; then it is a valid proof
                expect(bool(probs), f"A {wid}/{F.id}: {label}")
        if len(rw.fillers) >= 2:
            Fs = {F.id: F for F in rw.fillers}
            dec = OUT[wid]["procedure"]["world"]["decisive"]
            for e in dec:
                expect(R.decisive_ok(rw, Fs, cards, e), f"A {wid}: true decisive state rejected")
                bad = copy.deepcopy(e)
                bad["intervals"][e["pair"][0]][0] = "-99"
                expect(not R.decisive_ok(rw, Fs, cards, bad), f"A {wid}: wrong interval")
                bad = copy.deepcopy(e)
                st0 = R.load_json(os.path.join(WDIR, fn))["observations"][-1]["state"]
                bad["state"] = dict(st0)
                expect(not R.decisive_ok(rw, Fs, cards, bad, check_intervals=False),
                       f"A {wid}: a state where the fillers overlap accepted")
                bad = copy.deepcopy(e)
                bad["observer"] = "nobody"
                expect(not R.decisive_ok(rw, Fs, cards, bad), f"A {wid}: unknown observer")
                bad = copy.deepcopy(e)
                bad["state"].pop(sorted(bad["state"])[0])
                expect(not R.decisive_ok(rw, Fs, cards, bad), f"A {wid}: state missing a name")


# ================================================================= Part B: corrupted worlds and keys

def world(wid):
    return R.load_json(os.path.join(WDIR, wid + ".json"))


def rejects(raw, rule, label):
    try:
        rw, cards = R.reference(raw, REG)
    except R.Invalid as e:
        expect(str(e).startswith(rule) or rule == "any", f"B {label}: rejected by '{e}' instead of {rule}")
        return
    except Exception as e:  # noqa: BLE001
        missed.append(f"B {label}: crash {type(e).__name__}: {e}")
        return
    missed.append(f"B {label}: accepted, expected {rule}")


def key_rejects(wid, keymut, label):
    rw, cards = R.reference(world(wid), REG)
    k = copy.deepcopy(KEY[wid])
    keymut(k)
    expect(bool(S.key_problems(rw, cards, k)), f"B key {label}")


def part_b():
    # V1
    w = world("D-01"); w["registry_sha256"] = "0" * 64; rejects(w, "V1", "wrong registry hash")
    w = world("D-01"); w["quantities"][0]["dims"] = {"Z": 1}; rejects(w, "V1", "undeclared dimension")
    # budgets and names
    w = world("D-06"); w["bodies"].append({"id": "bc", "type": "ty01", "src": "seed"}); rejects(w, "budget", "3 bodies of a type")
    w = world("D-01"); w["relations"] = [{"id": "rl", "eq": "uu = kk", "src": "seed"}]; rejects(w, "budget", "a relation")
    w = world("D-01"); w["quantities"][2]["id"] = "qalong"; rejects(w, "any", "a 6+ letter name")
    w = world("D-01"); w["observations"][0]["state"]["qa"] = "2000000000"; rejects(w, "any", "a number over 10^9")
    w = world("D-01"); w["fillers"][0]["new"][0]["id"] = "m04"
    w["fillers"][0]["eq"] = w["fillers"][0]["eq"].replace("qc", "m04"); rejects(w, "any", "a registry id as a name")
    w = world("D-01"); w["laws"][0]["eq"] = "uu = kk*qa*qb^4/dd"; rejects(w, "any", "a power of 4")
    # V2
    w = world("D-01"); w["laws"].append(dict(w["laws"][0], id="law2")); rejects(w, "V2", "two laws")
    w = world("D-02"); w["laws"][0]["eq"] = "acx = -ks*xpx/ms + D(xpx, ms)"; rejects(w, "any", "D() in the law")
    w = world("D-01"); w["fillers"][0]["eq"] = "uu = kk*qa*qb/dd + qc*uu"; rejects(w, "V2", "y on a filler's right side")
    w = world("D-01"); w["laws"][0]["eq"] = "2*uu = kk*qa*qb/dd"; rejects(w, "V2", "a left side that is not a name")
    # V3
    w = world("D-01"); w["fillers"][0]["new"][0]["owner"] = "?"; rejects(w, "V3", "unknown owner")
    w = world("D-01"); w["fillers"][0]["new"][0]["old_value"] = "?"; rejects(w, "V3", "old value '?'")
    # V4
    w = world("D-03"); nq = w["fillers"][0]["new"][0]; nq["meaning"] = "?"; nq["under"] = {"rev_t": "?", "refl_x": "?", "conj_c": "?"}
    rejects(w, "V4", "unknown action on a vector")
    w = world("D-08"); nq = w["fillers"][0]["new"][0]; nq["under"] = {"rev_t": "?", "refl_x": "?", "conj_c": "?"}
    rejects(w, "V4", "three unknown signs")
    # V5
    w = world("D-15"); f = w["fillers"][0]; f["new"].append(dict(f["new"][0], id="c9"))
    f["eq"] = "uu = kk*qa*qb/dd + c1*c9*qa*qb"; w["fillers"] = [f]; rejects(w, "V5", "a product of new quantities")
    w = world("D-01"); w["fillers"][0]["eq"] = "uu = kk*qa*qb/dd + kk*qa/qc"; rejects(w, "V5", "a new quantity in a denominator")
    w = world("D-01"); w["fillers"][0]["eq"] = "uu = kk*qa*qb/dd + qc - qc"; rejects(w, "V5", "a new quantity that cancels")
    # V6
    w = world("D-01"); w["quantities"][1]["value"] = "?"; rejects(w, "V6", "world value '?'")
    w = world("D-01"); w["quantities"][2]["dims"] = {"L": 1}; rejects(w, "V6", "dims differ from the meaning")
    w = world("D-01"); w["quantities"][1]["dims"] = {"M": 1}; rejects(w, "V6", "law dimensionally inconsistent")
    # V7
    w = world("D-06"); w["quantities"][3]["meaning"] = "m02"; w["quantities"][3]["dims"] = {"M": 1}
    w["fillers"][0]["eq"] = "uu = kk*qa*qb/dd + cc*qa"; rejects(w, "any", "paired bodies own different meanings")
    w = world("D-06"); w["fillers"][0]["new_bodies"] = [{"id": "bn", "type": "ty01"}]
    w["fillers"][0]["new"][0]["owner"] = "bn"; rejects(w, "V7", "a new body of a world body's type")
    w = world("D-06"); w["fillers"][0]["new"][0]["owner"] = "ba"; w["fillers"][0]["new"][0]["meaning"] = "m02"
    w["fillers"][0]["new"][0]["under"] = R.Reg().meanings["m02"]["under"]; rejects(w, "V7", "a new quantity without a partner")
    # V8
    w = world("D-01"); w["observations"][0]["state"].pop("qa"); rejects(w, "V8", "a state missing a variable")
    w = world("D-01"); w["observations"][0]["state"]["kk"] = "2"; rejects(w, "V8", "a state fixing a constant")
    w = world("D-01"); w["observations"][0]["value"] = "4"; rejects(w, "V8", "the law misses an old observation")
    w = world("D-01"); w["observations"][1]["value"] = "2"; w["observations"][2]["value"] = "4"; rejects(w, "V8", "no deficit")
    w = world("D-01"); w["observations"][2]["value"] = "100"; rejects(w, "V8", "the filler cannot fit the new observations")
    w = world("D-01"); w["observations"][0]["state"]["dd"] = "0"; rejects(w, "V8", "division by zero")
    w = world("D-01"); w["observations"][0]["of"] = "qa"; rejects(w, "any", "an observation not of y")
    # V10
    w = world("D-15"); w["fillers"][2] = copy.deepcopy(R.load_json(os.path.join(WDIR, "D-08.json"))["fillers"][0])
    w["fillers"][2]["id"] = "f3"; rejects(w, "V10", "a CONDITIONAL filler among several")
    w = world("D-15"); w["fillers"][1]["new"][0]["value"] = "var"; rejects(w, "V10", "a kept filler with a variable")
    # V11
    w = world("D-01"); R.ALLOW_DEV = False; rejects(w, "V11", "a copy of a dev world"); R.ALLOW_DEV = True
    # V13: the verified example (protocol V13)
    raw = world("D-01")
    raw["quantities"] = [
        {"id": "uu", "meaning": "m03", "owner": "world", "dims": {"M": 1, "L": 2, "T": -2}, "components": [], "value": "var", "src": "seed"},
        {"id": "kk", "meaning": "m07", "owner": "world", "dims": {"M": 1, "L": 1, "T": -1, "Q": -1}, "components": [], "value": "2", "src": "seed"},
        {"id": "qa", "meaning": "m04", "owner": "world", "dims": {"Q": 1}, "components": [], "value": "var", "src": "seed"},
        {"id": "wo", "meaning": "m22", "owner": "world", "dims": {"L": 1, "T": -1}, "components": ["wox", "woy", "woz"], "value": "var", "src": "seed"}]
    raw["laws"][0]["eq"] = "uu = kk*qa*wox"
    raw["fillers"][0]["eq"] = "uu = kk*qa*wox + cc*wox"
    raw["fillers"][0]["new"] = [{"id": "cc", "kind": "scalar", "meaning": "m07", "owner": "world", "dims": "?", "components": [],
                                 "under": {"rev_t": "1", "refl_x": "1", "conj_c": "1"}, "value": "?", "old_value": "0", "route": "?"}]
    raw["observations"] = [
        {"id": "o1", "observer": "ob1", "of": "uu", "state": {"qa": "1", "wox": "1"}, "value": "2", "epoch": 0, "src": "ob1"},
        {"id": "o2", "observer": "ob1", "of": "uu", "state": {"qa": "1", "wox": "1"}, "value": "3", "epoch": 1, "src": "ob1"}]
    rejects(raw, "V13", "the time-reversal x charge-conjugation example")
    for fn in sorted(os.listdir(os.path.join(HERE, "rejected"))):
        rule = fn[:-5].split("_")[-1]
        rejects(R.load_json(os.path.join(HERE, "rejected", fn)), rule, f"dev case {fn}")
    # V12: the key
    key_rejects("D-01", lambda k: k["fillers"]["f1"].__setitem__("verdict", "ANOTHER_LAW"), "wrong verdict")
    key_rejects("D-02", lambda k: k["fillers"]["f1"].__setitem__("F2", {"rev_t": "no_change"}), "wrong F2 status")
    key_rejects("D-15", lambda k: k.__setitem__("kept", ["f1"]), "wrong kept")
    key_rejects("D-15", lambda k: k.__setitem__("decisive", []), "missing decisive state")
    key_rejects("D-15", lambda k: k["decisive"][0].__setitem__("state", {"qa": "2", "qb": "1", "dd": "1"}),
                "an overlapping decisive state")
    key_rejects("D-01", lambda k: k.__setitem__("traps", ["T2"]), "a declared trap that does not hold")
    key_rejects("D-01", lambda k: k["fillers"].__setitem__("f9", {"verdict": "SAME_LAW_NEW_STATE"}), "an extra filler")


def part_c():
    """the scorer's metrics: a procedure that answers like FIX must FAIL; the true outputs PASS."""
    rep = S.evaluate(WDIR, os.path.join(HERE, "key.json"), os.path.join(HERE, "results", "dev_outputs.json"))
    expect(rep["outcome"] == "PASS", "C true outputs do not PASS on the dev set")
    fake = copy.deepcopy(OUT)
    for wid, r in fake.items():
        r["procedure"] = copy.deepcopy(r["FIX"])
    path = os.path.join(HERE, "results", "mutated_outputs.json")
    json.dump(fake, open(path, "w", encoding="utf-8"))
    rep = S.evaluate(WDIR, os.path.join(HERE, "key.json"), path)
    expect(rep["outcome"] == "FAIL", "C a FIX-like procedure does not FAIL")
    os.remove(path)


if __name__ == "__main__":
    part_a()
    part_b()
    part_c()
    print(f"caught {caught} mutations, missed {len(missed)}")
    for x in missed:
        print("  MISSED:", x)
    sys.exit(1 if missed else 0)
