"""Check for Q10 page section 11.3 item 4 (A1, list of old rules), 2026-10-09.

Claim under test (written by Claude on 2026-10-08): without the protected rule
"the old kind stays inside the new one", minimal change picks the strange
two-element world (GF(2), i = j = k = 1) over the quaternions, "by count and by
containment both".

This holds when "order" is ONE rule. Section 11.3 item 3 lists order as three
parts: total (O1), kept by addition (O2), kept by multiplication by positives
(O3). This script checks what each candidate breaks when the parts are separate.

Part A: GF(2), brute force over all 16 binary relations on {0, 1}.
Part B: quaternions, with the lexicographic order on R^4 (O1 and O2 hold;
        sampled check) and the proof that O3 fails for ANY order.
Part C: no world breaks only a strict subset of {O3, comm} (proof sketch,
        printed; the arithmetic steps are checked).

Standard library only.
"""
from itertools import product
import random

# ---------- Part A: GF(2) ----------
E = (0, 1)
add = lambda a, b: (a + b) % 2
mul = lambda a, b: (a * b) % 2


def order_parts(R):
    """R is a set of pairs (a, b) meaning a < b. Strictness (irreflexive,
    transitive) is required of every candidate; the three listed parts are
    then checked separately."""
    strict = all((a, a) not in R for a in E) and all(
        (a, c) in R for (a, b) in R for (b2, c) in R if b == b2)
    if not strict:
        return None
    total = all(a == b or (a, b) in R or (b, a) in R for a in E for b in E)
    by_add = all((add(a, c), add(b, c)) in R for (a, b) in R for c in E)
    by_mul = all((0, mul(a, b)) in R for a in E for b in E
                 if (0, a) in R and (0, b) in R)
    return {"O1_total": total, "O2_add": by_add, "O3_mul": by_mul}


pairs = [(a, b) for a in E for b in E]
broken_sets = set()
for bits in product((0, 1), repeat=len(pairs)):
    R = {p for p, keep in zip(pairs, bits) if keep}
    parts = order_parts(R)
    if parts is None:
        continue
    broken_sets.add(frozenset(k for k, ok in parts.items() if not ok))

minimal = {s for s in broken_sets if not any(t < s for t in broken_sets)}
print("Part A: GF(2), order parts broken (all strict relations):")
for s in sorted(broken_sets, key=lambda s: (len(s), sorted(s))):
    print("   ", sorted(s), "(minimal)" if s in minimal else "")
assert frozenset() not in broken_sets, "GF(2) cannot keep all three parts"
assert minimal == {frozenset({"O1_total"}), frozenset({"O2_add"})}
# The algebra side: field, commutative, i = j = k = 1 satisfies the role.
neg = lambda a: (-a) % 2
m1 = neg(1)
assert mul(1, 1) == m1 and mul(mul(1, 1), 1) == m1  # i^2 = ijk = -1
print("    GF(2) breaks no algebra rule; minimal order breaks: {O1} or {O2}")

# ---------- Part B: quaternions ----------
def qmul(p, q):
    a1, b1, c1, d1 = p
    a2, b2, c2, d2 = q
    return (a1*a2 - b1*b2 - c1*c2 - d1*d2,
            a1*b2 + b1*a2 + c1*d2 - d1*c2,
            a1*c2 - b1*d2 + c1*a2 + d1*b2,
            a1*d2 + b1*c2 - c1*b2 + d1*a2)


def qadd(p, q):
    return tuple(x + y for x, y in zip(p, q))


lex_less = lambda p, q: p != q and p < q  # Python tuple order = lexicographic

rng = random.Random(20261009)
rnd = lambda: tuple(rng.randint(-3, 3) for _ in range(4))
for _ in range(20000):
    p, q, r = rnd(), rnd(), rnd()
    if p != q:
        assert lex_less(p, q) or lex_less(q, p)          # O1
    if lex_less(p, q):
        assert lex_less(qadd(p, r), qadd(q, r))          # O2
i, j, k = (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)
minus_one = (-1, 0, 0, 0)
assert qmul(i, i) == qmul(j, j) == qmul(k, k) == qmul(qmul(i, j), k) == minus_one
assert qmul(i, j) != qmul(j, i)
# O3 fails for any total order with O1: either 0 < i or 0 < -i, and both
# i*i and (-i)*(-i) equal -1, while 0 < 1 = (1)(1) forces -1 < 0 (by O2).
neg_i = (0, -1, 0, 0)
assert qmul(neg_i, neg_i) == minus_one
print("Part B: quaternions with lex order keep O1, O2; break O3 and comm"
      " (sampled 20000 triples; O3 failure is forced for every order)")

# ---------- Part C: nothing breaks a strict subset of {O3, comm} ----------
# {} or {comm}: an ordered ring has squares >= 0 and -1 < 0, so i^2 = -1 is
#   impossible (does not use commutativity).
# {O3}: commutative + associative gives (ijk)^2 = i^2 j^2 k^2 = (-1)^3 = -1,
#   and (ijk)^2 = (-1)^2 = 1, so 1 + 1 = 0; with O1 and O2 and 1 != 0 this
#   is impossible (0 < 1 gives 1 < 0; 1 < 0 gives 0 < 1).
assert (-1) ** 3 == -1 and (-1) ** 2 == 1
print("Part C: {O3, comm} is minimal by containment (proof in comments)")

# ---------- Part D: the same algebra gives several incomparable branches ----------
# Even WITH the protected rule (GF(2) excluded), the quaternion algebra can
# drop a different order part each time: {O1, comm} (empty order),
# {O3, comm} (lex order), {O2, comm} (the order below). These are pairwise
# incomparable, so containment would branch between copies of one algebra.
def is_pos_real(q):
    return q[0] > 0 and q[1:] == (0, 0, 0)


def key(q):  # positive reals above 0, everything else below 0, lex inside
    if is_pos_real(q):
        return (2, q[0])
    if q == (0, 0, 0, 0):
        return (1, 0)
    return (0, q)


less = lambda p, q: key(p) < key(q)
zero = (0, 0, 0, 0)
o2_broken = False
for _ in range(20000):
    p, q, r = rnd(), rnd(), rnd()
    if p != q:
        assert less(p, q) or less(q, p)                     # O1 holds
    if less(zero, p) and less(zero, q):
        assert less(zero, qmul(p, q))                       # O3 holds
    if less(p, q) and not less(qadd(p, r), qadd(q, r)):
        o2_broken = True
assert o2_broken
print("Part D: quaternions also break exactly {O2, comm} under another order;")
print("        {O1,comm}, {O2,comm}, {O3,comm} are pairwise incomparable")

print()
print("Result: with order as ONE rule, GF(2) {order} is contained in the")
print("quaternions {order, comm}: the strange world wins by count and by")
print("containment. With order as THREE parts, by count GF(2) still wins")
print("(1 < 2), but by containment {O2} and {O3, comm} are incomparable:")
print("a tie, so a branch between them, not a pick of GF(2) alone.")
print("Either way the quaternions are never picked alone without the")
print("protected rule, so the rule is still needed.")
