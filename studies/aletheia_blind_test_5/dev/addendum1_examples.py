"""The worked examples of PROTOCOL_ADDENDUM_1.md, checked with the sealed checker (scorer/certs_v5.py).
Prints the relator numbering of the numbering example and each refutation as JSON; every refutation
must be accepted, and every deliberately broken copy rejected. Exit 0 only if all hold.
Usage: python -I dev/addendum1_examples.py   (from aletheia_blind_test_5/)"""
import copy
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scorer"))
import certs_v5 as C  # noqa: E402

fails = 0


def info(origin, gens, role, frames=()):
    return C.world_info({"builds": [{"id": "b", "origin": origin, "generators": gens, "role": role,
                                     "frames": list(frames), "src": "seed"}]})


def show_context(inf):
    F = C.Field(None)
    tc = C.TreeCheck(inf, [], F, C.BOUNDS)
    names = set(inf["generators"]) | ({"e1"} if inf["origin"] == "k02" else set())
    rels, ineqs = C.role_context(inf["atoms"], tc.amb, names, inf["origin"])
    for i, r in enumerate(rels):
        print(f"  relator {i}: {r}")
    for i, q in enumerate(ineqs):
        print(f"  inequation {i}: {q}")


def check(label, inf, drop, cert, want=True):
    global fails
    ok, why = C.safe(C.check_refutation, cert, inf, drop)
    good = ok == want
    print(("ok    " if good else "FAIL  ") + label + ("" if ok else f"   [{why}]"))
    if not good:
        fails += 1


def el(*pairs):
    return [[c, w] for c, w in pairs]


# numbering example (A2): two chains, one in an equation and one in an inequation
print("numbering example: origin k01, role ['x*y*z = x', 'x*x*x != 0'], candidate [] (q5 and q6 kept)")
show_context(info("k01", ["x", "y", "z"], ["x*y*z = x", "x*x*x != 0"]))
print("the same role, candidate ['q5', 'q6'] (bracketed words):")
inf_n = info("k01", ["x", "y", "z"], ["x*y*z = x", "x*x*x != 0"])
F0 = C.Field(None)
tc = C.TreeCheck(inf_n, ["q5", "q6"], F0, C.BOUNDS)
rels, ineqs = C.role_context(inf_n["atoms"], tc.amb, {"x", "y", "z"}, "k01")
for i, r in enumerate(rels):
    print(f"  relator {i}: {r}")
for i, q in enumerate(ineqs):
    print(f"  inequation {i}: {q}")

# E1 positive: x*x = -1 over the reals with q14 kept
inf1 = info("k01", ["x"], ["x*x = -1"])
E1 = {"theta": None, "tree": {"node": "positive", "t": [el(["1", "x"])], "c": "1",
                              "terms": [["1", {"ctx": 0}, []]]}}
check("E1 positive node refutes [] for x*x = -1", inf1, [], E1)
bad = copy.deepcopy(E1)
bad["tree"]["c"] = "2"
check("E1 broken (c = 2) is rejected", inf1, [], bad, want=False)
check("E1 used where q14 is dropped is rejected", inf1, ["q14"], E1, want=False)

# E2 split by q12, with a fraction coefficient: x*x = 2, x*y + y*x = 0, y != 0, q6 kept
inf2 = info("k01", ["x", "y"], ["x*x = 2", "x*y + y*x = 0", "y != 0"])
E2 = {"theta": None, "tree": {
    "node": "split", "by": "q12", "a": el(["1", "x"]), "b": el(["1", "y"]),
    "proof_ab": [["1/2", {"ctx": 1}, []]],
    "children": [
        {"node": "close", "target": {"const": "-2"},
         "terms": [["1", {"ctx": 0}, []], ["-1", {"ctx": 2}, [["R", el(["1", "x"])]]]]},
        {"node": "close", "target": {"ineq": 0}, "terms": [["1", {"ctx": 2}, []]]}]}}
check("E2 split by q12 refutes ['q14'] (q6 and q12 kept)", inf2, ["q14"], E2)
check("E2 used where q6 is dropped is rejected", inf2, ["q6", "q14"], E2, want=False)

# E3 inverse: t*t = 0, t != 0, with q5 and q13 kept (q12 and q14 dropped)
inf3 = info("k01", ["t"], ["t*t = 0", "t != 0"])
E3 = {"theta": None, "tree": {
    "node": "inverse", "a": el(["1", "t"]), "v": "tv",
    "children": [
        {"node": "close", "target": {"ineq": 0}, "terms": [["1", {"ctx": 1}, []]]},
        {"node": "close", "target": {"ineq": 0},
         "terms": [["1", {"ctx": 0}, [["R", el(["1", "tv"])]]], ["-1", {"ctx": 1}, [["L", el(["1", "t"])]]]]}]}}
check("E3 inverse node refutes ['q12', 'q14']", inf3, ["q12", "q14"], E3)
bad = copy.deepcopy(E3)
bad["tree"]["v"] = "t"
check("E3 broken (v not fresh) is rejected", inf3, ["q12", "q14"], bad, want=False)
check("E3 used where q5 is dropped is rejected", inf3, ["q5", "q12", "q14"], E3, want=False)

# E4 theta: x*x = 2, x*y = 0, y != 0; split by q12 on (x - th, x + th) with th = sqrt 2
inf4 = info("k01", ["x", "y"], ["x*x = 2", "x*y = 0", "y != 0"])
TH = {"poly": ["-2", "0", "1"], "lo": "1", "hi": "2"}
E4 = {"theta": TH, "tree": {
    "node": "split", "by": "q12", "a": el(["1", "x"], [["0", "-1"], "1"]), "b": el(["1", "x"], [["0", "1"], "1"]),
    "proof_ab": [["1", {"ctx": 0}, []]],
    "children": [
        {"node": "close", "target": {"ineq": 0},
         "terms": [[["0", "1/2"], {"ctx": 1}, []], [["0", "-1/2"], {"ctx": 2}, [["R", el(["1", "y"])]]]]},
        {"node": "close", "target": {"ineq": 0},
         "terms": [[["0", "-1/2"], {"ctx": 1}, []], [["0", "1/2"], {"ctx": 2}, [["R", el(["1", "y"])]]]]}]}}
check("E4 split over Q(sqrt 2) refutes []", inf4, [], E4)
bad = copy.deepcopy(E4)
bad["theta"] = None
check("E4 without theta is rejected", inf4, [], bad, want=False)

for name, cert in (("E1", E1), ("E2", E2), ("E3", E3), ("E4", E4)):
    print(f"\n{name} = " + json.dumps(cert, ensure_ascii=False))
print("\nall examples behave as stated" if not fails else f"\n{fails} FAILED")
sys.exit(1 if fails else 0)
