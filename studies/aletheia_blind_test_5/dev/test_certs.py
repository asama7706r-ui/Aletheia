"""Unit checks of scorer/certs_v5.py on hand-made certificates with known answers.
Every case states what must be accepted and what must be rejected. Exit 0 only if all pass.
Usage: python -I dev/test_certs.py   (from aletheia_blind_test_5/)"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scorer"))
import certs_v5 as C  # noqa: E402

fails = 0


def expect(ok_wanted, fn, *args, label=""):
    global fails
    ok, why = C.safe(fn, *args)
    good = ok == ok_wanted
    print(("ok    " if good else "FAIL  ") + label + ("" if ok else f"   [{why}]"))
    if not good:
        fails += 1


def info(origin, gens, role, frames=()):
    b = {"origin": origin, "generators": gens, "role": role, "frames": list(frames)}
    return {"origin": origin, "generators": sorted(gens), "frames": list(frames), "atoms": C.role_asts(b), "role": role}


SQRT2 = {"poly": ["-2", "0", "1"], "lo": "1", "hi": "2"}

# --- numbers
F = C.Field(SQRT2)
th = F.el(["0", "1"])
print("ok    sqrt2: theta^2 = 2 exactly" if F.mul(th, th) == F.c(2) else "FAIL  theta^2")
fails += F.mul(th, th) != F.c(2)
print("ok    sqrt2: theta - 1 certified > 0" if F.sign(F.sub(th, F.c(1))) == 1 else "FAIL  sign")
fails += F.sign(F.sub(th, F.c(1))) != 1
expect(False, C.Field, {"poly": ["-2", "0", "1"], "lo": "-2", "hi": "2"}, label="theta interval with two roots is rejected")

# --- known kinds
w_sqrt2 = info("k01", ["x"], ["x*x = 2"])
expect(True, C.check_known, {"kind": "k01", "theta": SQRT2, "values": {"x": ["0", "1"]}}, w_sqrt2, label="x*x = 2: x = sqrt2 in k01")
expect(False, C.check_known, {"kind": "k01", "theta": None, "values": {"x": "1"}}, w_sqrt2, label="x*x = 2: x = 1 is rejected")
w_i = info("k01", ["x"], ["x*x = -1"])
expect(True, C.check_known, {"kind": "k02", "theta": None, "values": {"x": ["0", "1"]}}, w_i, label="x*x = -1: x = i in k02")
expect(False, C.check_known, {"kind": "k01", "theta": None, "values": {"x": "1"}}, w_i, label="x*x = -1 has no value in k01")
w_e = info("k02", ["u"], ["u*u = e1"])
half = {"poly": ["-1/2", "0", "1"], "lo": "0", "hi": "1"}          # theta = 1/sqrt2
expect(True, C.check_known, {"kind": "k02", "theta": half, "values": {"u": [["0", "1"], ["0", "1"]]}}, w_e,
       label="u*u = e1: u = (1 + i)/sqrt2 in k02")

# --- witnesses: the quaternion request over the reals
quat_role = ["a*a = -1", "b*b = -1", "a*b = -(b*a)"]
wq = info("k01", ["a", "b"], quat_role)
QT = [[1, 1, 0, "-1"], [2, 2, 0, "-1"], [3, 3, 0, "-1"], [1, 2, 3, "1"], [2, 1, 3, "-1"],
      [2, 3, 1, "1"], [3, 2, 1, "-1"], [3, 1, 2, "1"], [1, 3, 2, "-1"]]
I4 = [["1" if i == j else "0" for j in range(4)] for i in range(4)]
CJ = [[("1" if i == 0 else "-1") if i == j else "0" for j in range(4)] for i in range(4)]
H = {"dim": 4, "table": QT, "theta": None, "gens": {"a": ["0", "1", "0", "0"], "b": ["0", "0", "1", "0"]},
     "q12": {"N": I4, "C": CJ}, "q13": None}
expect(True, C.check_witness, H, wq, ["q14", "q6"], label="H witnesses {q6, q14}")
expect(False, C.check_witness, H, wq, ["q14"], label="H does not witness {q14} (q6 fails)")
expect(False, C.check_witness, H, wq, ["q6"], label="H does not witness {q6} (q14 needs dimension 1)")
bad = dict(H, q12={"N": I4, "C": I4})
expect(False, C.check_witness, bad, wq, ["q6", "q14"], label="a wrong conjugation is rejected")
print("      fail units of H:", C.witness_fail_units(H, wq))
# a commutative, non-associative 3-dimensional rival: a*a = b*b = -1, a*b = b*a = 0, with inverses
T3 = {"dim": 3, "table": [[1, 1, 0, "-1"], [2, 2, 0, "-1"]], "theta": None,
      "gens": {"a": ["0", "1", "0"], "b": ["0", "0", "1"]}, "q12": None,
      "q13": {"N": [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
              "C": [["1", "0", "0"], ["0", "-1", "0"], ["0", "0", "-1"]]}}
expect(True, C.check_witness, T3, wq, ["q5", "q12", "q14"], label="the 3-dim commutative rival witnesses {q5, q12, q14}")
expect(False, C.check_witness, T3, wq, ["q12", "q14"], label="... but not {q12, q14} (q5 fails)")
print("      fail units of the rival:", C.witness_fail_units(T3, wq))

# --- refutations
A = [["1", "a"]]
B = [["1", "b"]]
tree_q14 = {"theta": None, "tree": {
    "node": "split", "by": "q12", "a": A, "b": B,
    "proof_ab": [["1/2", {"ctx": 2}, []]],
    "children": [
        {"node": "close", "target": {"const": "1"}, "terms": [["1", {"ctx": 0}, []], ["-1", {"ctx": 3}, [["L", A]]]]},
        {"node": "close", "target": {"const": "1"}, "terms": [["1", {"ctx": 1}, []], ["-1", {"ctx": 3}, [["L", B]]]]}]}}
expect(True, C.check_refutation, tree_q14, wq, ["q14"], label="{q14} refuted: commutativity and anticommutation give a zero divisor")
expect(False, C.check_refutation, tree_q14, wq, ["q12", "q14"], label="... the same tree is invalid once q12 is dropped")
tree_q6 = {"theta": None, "tree": {"node": "positive", "t": [A], "c": "1", "terms": [["1", {"ctx": 0}, []]]}}
expect(True, C.check_refutation, tree_q6, wq, ["q6"], label="{q6} refuted: a*a + 1 = 0 against the order bundle")
expect(False, C.check_refutation, tree_q6, wq, ["q6", "q14"], label="... invalid once q14 is dropped")
# {q12, q14}: commutativity and associativity, no division: a = (a*b)*b ... gives 1 = 0
tree_assoc = {"theta": None, "tree": {"node": "close", "target": {"const": "1"}, "terms": [
    # in the commutative associative ambient, r2 = 2ab; r1 = b^2 + 1. a = -a*(b*b+1) + (1/2)*(2ab)*b ... so a in I, then a*a in I
    ["1", {"ctx": 0}, []],                                        # a^2 + 1
    ["-1", {"ctx": 1}, [["L", [["1", "a"]]], ["L", [["1", "a"]]]]],   # -(a*a*(b^2+1)) = -a^2 b^2 - a^2
    ["1/2", {"ctx": 2}, [["L", [["1", "a"]]], ["R", [["1", "b"]]]]],  # (1/2)*a*(2ab)*b = a^2 b^2
]}}
expect(True, C.check_refutation, tree_assoc, wq, ["q12", "q14"], label="{q12, q14} refuted by associativity (no split needed)")

# C1-like: j*j = 1, j != 1, j != -1 (origin k01): {q14} refuted by a split (lemma Z)
wc = info("k01", ["j"], ["j*j = 1", "j != 1", "j != -1"])
P = [["1", "1"], ["1", "j"]]
M = [["1", "1"], ["-1", "j"]]
tree_z = {"theta": None, "tree": {
    "node": "split", "by": "q12", "a": P, "b": M, "proof_ab": [["-1", {"ctx": 0}, []]],
    "children": [
        {"node": "close", "target": {"ineq": 1}, "terms": [["1", {"ctx": 1}, []]]},
        {"node": "close", "target": {"ineq": 0}, "terms": [["-1", {"ctx": 1}, []]]}]}}
expect(True, C.check_refutation, tree_z, wc, ["q14"], label="C1-like: {q14} refuted by the split (1 + j)(1 - j) = 0")
expect(True, C.check_refutation, tree_z, wc, ["q13", "q14"], label="... and {q13, q14} too (q12 still kept)")
expect(False, C.check_refutation, tree_z, wc, ["q12", "q14"], label="... but not {q12, q14}")
# lemma I: q5 and q13 kept, q12 dropped: inverse of 1 + j
tree_i = {"theta": None, "tree": {
    "node": "inverse", "a": P, "v": "v",
    "children": [
        {"node": "close", "target": {"ineq": 1}, "terms": [["1", {"ctx": 1}, []]]},
        # (1 - j) = -(v(1+j) - 1)(1 - j) + v((1+j)(1-j)) = ... in the associative ambient
        {"node": "close", "target": {"ineq": 0}, "terms": [
            ["1", {"ctx": 2}, [["R", M]]],            # (v(1+j) - 1)(1 - j) = v(1+j)(1-j) - (1 - j)
            ["1", {"ctx": 0}, [["L", [["1", "v"]]]]],  # v(j^2 - 1) = -v(1+j)(1-j)
        ]}]}}
expect(True, C.check_refutation, tree_i, wc, ["q12", "q14"], label="C1-like: {q12, q14} refuted by the inverse of 1 + j (lemma I)")
expect(False, C.check_refutation, tree_i, wc, ["q5", "q12", "q14"], label="... invalid without associativity")

# --- IMPOSSIBLE by congruence closure
expect(True, C.check_impossible, {"kind": "values"}, info("k01", ["x"], ["x = 1", "x*x = 2"]), label="x = 1, x*x = 2 is impossible")
expect(True, C.check_impossible, {"kind": "inequation"}, info("k01", ["x", "y"], ["x = y", "x != y"]), label="x = y, x != y is impossible")
expect(False, C.check_impossible, {"kind": "values"}, info("k01", ["x"], ["x*x = 2"]), label="x*x = 2 is not impossible")
expect(True, C.check_impossible, {"kind": "values"}, info("k02", ["u"], ["u = e1", "u*u = 1"]), label="u = e1, u*u = 1 is impossible over k02")
expect(True, C.check_impossible, {"kind": "values"}, info("k01", ["x"], ["x*x = -1", "x*x*x*x = -1"]),
       label="x*x = -1 with x*x*x*x = -1 is impossible (a chain)")

# --- the mirror
wm = info("k02", ["x"], ["(e1*x)*x + (x*x)*e1 != e1*(x*x) + x*(x*e1)"])
print("ok    mirror-invariant role" if C.mirror_invariant(wm["atoms"], {"x": "x"}) else "FAIL  mirror invariance")
fails += not C.mirror_invariant(wm["atoms"], {"x": "x"})
wn = info("k02", ["x"], ["(e1*x)*x != e1*(x*x)"])
print("ok    a one-sided role is not mirror-invariant" if not C.mirror_invariant(wn["atoms"], {"x": "x"}) else "FAIL  one-sided")
fails += C.mirror_invariant(wn["atoms"], {"x": "x"})

print("\nall certificate checks pass" if fails == 0 else f"\n{fails} FAILED")
sys.exit(1 if fails else 0)
