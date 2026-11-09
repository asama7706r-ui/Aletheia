"""Check every algebra the history test uses: the system history built (its properties), and every
witness behind a prediction. Exact arithmetic; exit 0 only if every stated fact checks.
Usage: python -I tools/check_witnesses.py   (from history_ladder_test/)"""
import json
import os
import sys
from fractions import Fraction as F

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import algebras as A  # noqa: E402

ROOT = os.path.dirname(HERE)
ROLES = {n: json.load(open(os.path.join(ROOT, "predictions", "roles", n + ".json"), encoding="utf-8"))["builds"][0]["role"]
         for n in ("C1_tessarines", "C2_multicomplex", "C3_hyperbolic_quaternions", "C4_split_biquaternions")}
failures = 0


def fact(ok, text):
    global failures
    print(("ok    " if ok else "FAIL  ") + text)
    if not ok:
        failures += 1


def check(alg, role_name, env, assoc, comm, zero_div=None, noninv=None):
    bad = A.role_holds(alg, env, ROLES[role_name])
    fact(not bad, f"{alg.name}: satisfies the {role_name} demand" + (f" (fails {bad})" if bad else ""))
    a, wit = alg.associative()
    fact(a == assoc, f"{alg.name}: associative = {a}" + (f" (e.g. basis {wit})" if wit else ""))
    c, wit = alg.commutative()
    fact(c == comm, f"{alg.name}: commutative = {c}" + (f" (e.g. basis {wit})" if wit else ""))
    if zero_div:
        x, y = zero_div
        fact(x != {} and y != {} and alg.mul(x, y) == {}, f"{alg.name}: zero divisors {x} * {y} = 0, so q12 fails")
    if noninv:
        fact(noninv != {} and alg.no_right_inverse(noninv), f"{alg.name}: {noninv} has no right inverse, so q13 fails")


# C1 -- tessarines (Cockle): commuting i (= e1, square -1) and j (square +1); history's system and OURS' witness
tess = A.commuting_units("tessarines C(x)R[j]", [-1, 1])
e = lambda t: {t: 1}  # noqa: E731
one, i_, j_ = e((0, 0)), e((1, 0)), e((0, 1))
check(tess, "C1_tessarines", {"e1": i_, "j": j_}, assoc=True, comm=True,
      zero_div=(tess.add(one, j_), tess.add(one, tess.neg(j_))), noninv=tess.add(one, j_))

# C2 -- tricomplex (Segre): three commuting units with square -1 (e1 = first); history's system and a witness
tri = A.commuting_units("tricomplex numbers", [-1, -1, -1])
i3, h3, l3 = e((1, 0, 0)), e((0, 1, 0)), e((0, 0, 1))
one3 = e((0, 0, 0))
check(tri, "C2_multicomplex", {"e1": i3, "h": h3, "l": l3}, assoc=True, comm=True,
      zero_div=(tri.add(h3, tri.neg(i3)), tri.add(h3, i3)), noninv=tri.add(h3, tri.neg(i3)))
# C2 -- the other branch's witness: H contains C (e1 = i), h = j, l = (3i + 4j)/5; H is a division ring
H = A.quaternions()
check(H, "C2_multicomplex", {"e1": e("i"), "h": e("j"), "l": {"i": F(3, 5), "j": F(4, 5)}}, assoc=True, comm=False)
print("      (H has no zero divisors and every nonzero element has the two-sided inverse conj(x)/N(x): "
      "standard, Frobenius 1877; not recomputed here)")

# C3 -- Macfarlane 1891: history's system, and OURS' witness
mac = A.macfarlane_1891()
check(mac, "C3_hyperbolic_quaternions", {"i": e("i"), "j": e("j"), "k": e("k")}, assoc=False, comm=False,
      zero_div=(mac.add(mac.one(), e("i")), mac.add(mac.one(), mac.neg(e("i")))),
      noninv=mac.add(mac.one(), e("i")))
# C3 -- MAXCON's char-2 branch: the same rules over GF(2) (q2 dropped)
m2 = A.char2_quaternion_rules()
check(m2, "C3_hyperbolic_quaternions", {"i": e("i"), "j": e("j"), "k": e("k")}, assoc=True, comm=True,
      zero_div=(m2.add(m2.one(), e("i")), m2.add(m2.one(), e("i"))), noninv=m2.add(m2.one(), e("i")))

# C4 -- Clifford's biquaternions H(+)H (w central): history's system, and OURS' witness
cb = A.clifford_biquaternions()
E = lambda q, w=0: {(q, w): 1}  # noqa: E731
env4 = {"i": E("i"), "j": E("j"), "k": E("k"), "w": E("1", 1)}
check(cb, "C4_split_biquaternions", env4, assoc=True, comm=False,
      zero_div=(cb.add(E("1"), E("1", 1)), cb.add(E("1"), cb.neg(E("1", 1)))), noninv=cb.add(E("1"), E("1", 1)))
# C4 -- MAXCON's char-2 branch
cb2 = A.clifford_biquaternions(char=2)
check(cb2, "C4_split_biquaternions", env4, assoc=True, comm=True,
      zero_div=(cb2.add(E("1"), E("i")), cb2.add(E("1"), E("i"))), noninv=cb2.add(E("1"), E("i")))

print("\nall facts check" if failures == 0 else f"\n{failures} FAILED")
sys.exit(1 if failures else 0)
