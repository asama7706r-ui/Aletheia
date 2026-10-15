"""Q10 / B2 check (2026-10-09): when a demand admits two relaxations, are the
two branches two laws, one law, or one inside the other?

The user's question: a law shows a contradiction without saying which old
rule causes it, and two relaxations work. Does that point to two different
laws, or really to one case? Try to refute too: find two options that are
NOT two different laws.

Part 1, Dirac without psi (one INSIDE the other):
    branch B (keep commutativity, drop associativity) is the 5-dim algebra
    of 7.3 (1, e0..e3; e_m e_n = 0 for m != n; e0^2 = 1, ei^2 = -1).
    branch A (keep associativity, drop commutativity) is the algebra of the
    Dirac matrices (16-dim).
    Claim: B sits inside A when A's elements are multiplied symmetrically,
    a o b = (ab + ba)/2. So B is A's symmetric shadow, not a rival law.
    A has more: the commutators [g_m, g_n] are outside B's image.

Part 2, mirror twins (ONE law up to a symmetry of the problem):
    demand: an element z with z*0 + 0*z != 0 (zero does not absorb z on
    at least one side). Old rules include left distributivity (L), right
    distributivity (R) and commutativity (C).
    L gives z*0 = 0, R gives 0*z = 0, so L and R cannot both stay.
    C with R gives L, and C with L gives R, so C must go too.
    Branch "drop L, C": all maps of Z/3 to itself, with pointwise addition
    and composition (a near-ring). Branch "drop R, C": the same maps with
    the order of multiplication reversed. The demand is unchanged by the
    reversal, so the two branches are one structure read in a mirror.

Part 3, bookkeeping twins: see q10_a1_order_split_check.py, part D
    (the quaternions dropping a different part of "order" each time).

Standard library only. Complex entries are Gaussian integers, so exact.
"""
from itertools import product

# ---------------- Part 1: Dirac ----------------
eta = [1, -1, -1, -1]


def bmul(a, b):  # branch B, coefficients over [1, e0, e1, e2, e3]
    out = [0] * 5
    for i in range(5):
        for j in range(5):
            c = a[i] * b[j]
            if not c:
                continue
            if i == 0:
                out[j] += c
            elif j == 0:
                out[i] += c
            elif i == j:
                out[0] += c * eta[i - 1]
    return out


def unit(k, n=5):
    v = [0] * n
    v[k] = 1
    return v


def mm(A, B):
    n = len(A)
    return [[sum(A[i][k] * B[k][j] for k in range(n)) for j in range(n)]
            for i in range(n)]


def lin(coeffs, mats):
    n = len(mats[0])
    return [[sum(c * M[i][j] for c, M in zip(coeffs, mats)) for j in range(n)]
            for i in range(n)]


def jordan(X, Y):  # (XY + YX) / 2; entries stay exact here
    P, Q = mm(X, Y), mm(Y, X)
    return [[(P[i][j] + Q[i][j]) / 2 for j in range(4)] for i in range(4)]


I4 = [[1 if i == j else 0 for j in range(4)] for i in range(4)]
# Dirac representation
g0 = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, -1]]
g1 = [[0, 0, 0, 1], [0, 0, 1, 0], [0, -1, 0, 0], [-1, 0, 0, 0]]
g2 = [[0, 0, 0, -1j], [0, 0, 1j, 0], [0, 1j, 0, 0], [-1j, 0, 0, 0]]
g3 = [[0, 0, 1, 0], [0, 0, 0, -1], [-1, 0, 0, 0], [0, 1, 0, 0]]
G = [g0, g1, g2, g3]
basis_img = [I4] + G  # image of [1, e0, e1, e2, e3]

# A satisfies the demand (Clifford relations)
for m in range(4):
    for n in range(4):
        s = [[a + b for a, b in zip(r1, r2)]
             for r1, r2 in zip(mm(G[m], G[n]), mm(G[n], G[m]))]
        assert s == lin([2 * (eta[m] if m == n else 0)], [I4])
assert mm(g0, g1) != mm(g1, g0)  # A is not commutative

# The map phi: B -> (A, o) is a homomorphism on all basis pairs
for i in range(5):
    for j in range(5):
        lhs = lin(bmul(unit(i), unit(j)), basis_img)
        rhs = jordan(basis_img[i], basis_img[j])
        assert lhs == rhs, (i, j)


def flat(M):
    return [x for r in M for x in r]


def rank(vectors):  # exact rank over complex rationals (Gaussian elimination)
    from fractions import Fraction
    rows = [[complex(x) for x in v] for v in vectors]
    r, ncols = 0, len(rows[0])
    for c in range(ncols):
        piv = next((k for k in range(r, len(rows)) if abs(rows[k][c]) > 1e-12),
                   None)
        if piv is None:
            continue
        rows[r], rows[piv] = rows[piv], rows[r]
        for k in range(len(rows)):
            if k != r and abs(rows[k][c]) > 1e-12:
                f = rows[k][c] / rows[r][c]
                rows[k] = [a - f * b for a, b in zip(rows[k], rows[r])]
        r += 1
    return r


assert rank([flat(M) for M in basis_img]) == 5      # phi is one-to-one
# B is commutative and not associative
assert all(bmul(unit(i), unit(j)) == bmul(unit(j), unit(i))
           for i in range(5) for j in range(5))
assert bmul(bmul(unit(1), unit(1)), unit(2)) != bmul(unit(1), bmul(unit(1), unit(2)))
# A has more than B: products of distinct generators give 16 independent elements
prods = []
for bits in product((0, 1), repeat=4):
    M = I4
    for k, b in enumerate(bits):
        if b:
            M = mm(M, G[k])
    prods.append(flat(M))
assert rank(prods) == 16
# the commutators [g_m, g_n] (Lorentz generators up to a factor) are outside B
comms = []
for m in range(4):
    for n in range(m + 1, 4):
        P, Q = mm(G[m], G[n]), mm(G[n], G[m])
        comms.append([a - b for a, b in zip(flat(P), flat(Q))])
assert rank([flat(M) for M in basis_img] + comms) == 5 + 6
print("Part 1: branch B (5-dim, commutative, not associative) = branch A's")
print("        elements 1, g0..g3 under the symmetric product (ab+ba)/2.")
print("        A is 16-dim; its 6 commutators lie outside B. One inside the other.")

# ---------------- Part 2: mirror twins ----------------
N = 3
ELEMS = list(product(range(N), repeat=N))  # all maps Z/3 -> Z/3 as tuples
ZERO = tuple(0 for _ in range(N))
ONE = tuple(range(N))                       # identity map
add = lambda f, g: tuple((f[x] + g[x]) % N for x in range(N))
comp = lambda f, g: tuple(f[g[x]] for x in range(N))  # (f*g)(x) = f(g(x))
rev = lambda f, g: comp(g, f)                         # the mirror product


def rules(mul):
    L = all(mul(a, add(b, c)) == add(mul(a, b), mul(a, c))
            for a in ELEMS for b in ELEMS for c in ELEMS)
    R = all(mul(add(a, b), c) == add(mul(a, c), mul(b, c))
            for a in ELEMS for b in ELEMS for c in ELEMS)
    C = all(mul(a, b) == mul(b, a) for a in ELEMS for b in ELEMS)
    A = all(mul(mul(a, b), c) == mul(a, mul(b, c))
            for a in ELEMS[:9] for b in ELEMS for c in ELEMS)
    U = all(mul(ONE, a) == a == mul(a, ONE) for a in ELEMS)
    return {"L": L, "R": R, "C": C, "assoc": A, "unit": U}


z = tuple((x + 1) % N for x in range(N))  # translation by 1
for name, mul in (("composition", comp), ("mirror", rev)):
    r = rules(mul)
    demand = add(mul(z, ZERO), mul(ZERO, z)) != ZERO
    broken = sorted(k for k, ok in r.items() if not ok)
    print(f"Part 2: {name:11s} demand holds: {demand}; breaks {broken}")
    assert demand
rc, rm = rules(comp), rules(rev)
assert (rc["L"], rc["R"], rc["C"]) == (False, True, False)
assert (rm["L"], rm["R"], rm["C"]) == (True, False, False)
print("        the two branches swap L and R and are the same maps read in a mirror.")

# ---------------- Part 2b: a third, genuinely different branch ----------------
# Keep L, R and C; drop "every element has a negative". Without negatives,
# z*0 = z*0 + z*0 no longer forces z*0 = 0. A brute-force search over all
# 3-element structures (commutative monoids for + and *, distributive) found
# two such structures and none with negatives; one is checked here: an
# element w that swallows everything, w + a = w and w * a = w (so w * 0 = w).
# The same works on the rationals plus such a w (sampled below).
from fractions import Fraction as Fr
import random
W = "w"
add3 = lambda a, b: W if W in (a, b) else a + b
mul3 = lambda a, b: W if W in (a, b) else a * b
rng = random.Random(9)
sample = [W, Fr(0), Fr(1)] + [Fr(rng.randint(-9, 9), rng.randint(1, 5)) for _ in range(12)]
for a in sample:
    for b in sample:
        assert mul3(a, b) == mul3(b, a)
        for c in sample:
            assert mul3(a, add3(b, c)) == add3(mul3(a, b), mul3(a, c))   # L
            assert mul3(add3(a, b), c) == add3(mul3(a, c), mul3(b, c))   # R
            assert mul3(mul3(a, b), c) == mul3(a, mul3(b, c))
            assert add3(add3(a, b), c) == add3(a, add3(b, c))
assert add3(mul3(W, 0), mul3(0, W)) != 0                 # demand holds
assert all(add3(W, b) != 0 for b in sample)              # w has no negative
assert all(mul3(W, b) != 1 for b in sample)              # nor an inverse
print("Part 2b: rationals plus a swallowing element w keep L, R, C and both")
print("         associativities; the demand holds; w has no negative (and no")
print("         inverse). A different set of broken rules from the twins.")
print("         So this demand has at least three branches: two mirror twins")
print("         (one law) and one genuinely different law.")
