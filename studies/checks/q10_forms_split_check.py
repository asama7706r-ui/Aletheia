"""Q10 / meaning-transfer check (2026-10-14): when do two writings of one law
stop being one law?

The user's question (after the study-session definition "a theory is a list
of rules with everything derived from them; two lists that derive each
other are one theory"): a proof of a law covers all its equivalent writings,
but writings that are equivalent only through a rule that a new kind breaks
(e.g. commutativity) become different laws.

Part A: words (non-commutative polynomials). Expanding (x+y)^2 with
        distributivity alone gives xx + xy + yx + yy. Reaching xx + 2xy + yy
        needs one more step, sorting yx into xy, which is commutativity.
        The derivation records which rules it used; removing commutativity
        (the zero test on rules) leaves the first writing and kills the second.
Part B: numbers versus 2x2 integer matrices and quaternions: both writings
        agree on numbers; on matrices the 2xy writing holds exactly when
        AB = BA (checked on random pairs).
Part C: physics. With x and p as operators on polynomials (p = -i d/dx,
        hbar = 1), (p - ix)(p + ix) = p^2 + x^2 + 1, while for commuting
        symbols the "+1" is absent. The extra constant is the oscillator's
        zero-point offset: one classical law, two different quantum laws.
Standard library only; complex coefficients are exact Gaussian integers.
"""
import random
from fractions import Fraction

# ---------- Part A: derivations that record their rules ----------
def mul(P, Q):            # P, Q: dict word -> coefficient (non-commutative)
    out = {}
    for a, ca in P.items():
        for b, cb in Q.items():
            out[a + b] = out.get(a + b, 0) + ca * cb
    return {w: c for w, c in out.items() if c}


def sort_words(P):        # uses commutativity: letters may be reordered
    out = {}
    for w, c in P.items():
        s = "".join(sorted(w))
        out[s] = out.get(s, 0) + c
    return {w: c for w, c in out.items() if c}


xy = {"x": 1, "y": 1}
form1 = mul(xy, xy)                       # rules used: distributivity
form2 = sort_words(form1)                 # rules used: distributivity, commutativity
derivations = {
    "xx + xy + yx + yy": (form1, {"distributivity"}),
    "xx + 2xy + yy": (form2, {"distributivity", "commutativity"}),
}
assert form1 == {"xx": 1, "xy": 1, "yx": 1, "yy": 1}
assert form2 == {"xx": 1, "xy": 2, "yy": 1}
for name, (_, roots) in derivations.items():
    survives = "commutativity" not in roots
    print(f"Part A: (x+y)^2 = {name:18s} roots {sorted(roots)}"
          f" -> after dropping commutativity: {'survives' if survives else 'lost'}")

# ---------- Part B: numbers, matrices, quaternions ----------
def mm(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(2)) for j in range(2)] for i in range(2)]


def madd(*Ms):
    return [[sum(M[i][j] for M in Ms) for j in range(2)] for i in range(2)]


def scal(c, A):
    return [[c * v for v in r] for r in A]


rng = random.Random(14)
for _ in range(2000):                     # numbers: both writings agree
    a, b = Fraction(rng.randint(-9, 9), rng.randint(1, 5)), Fraction(rng.randint(-9, 9), 1)
    assert (a + b) ** 2 == a * a + a * b + b * a + b * b == a * a + 2 * a * b + b * b
agree_iff_commute = True
n_comm = n_non = 0
for _ in range(5000):
    A = [[rng.randint(-3, 3) for _ in range(2)] for _ in range(2)]
    B = [[rng.randint(-3, 3) for _ in range(2)] for _ in range(2)]
    S = madd(A, B)
    lhs = mm(S, S)
    f1 = madd(mm(A, A), mm(A, B), mm(B, A), mm(B, B))
    f2 = madd(mm(A, A), scal(2, mm(A, B)), mm(B, B))
    assert lhs == f1                      # distributivity alone always suffices
    commute = mm(A, B) == mm(B, A)
    n_comm += commute
    n_non += not commute
    agree_iff_commute &= ((lhs == f2) == commute)
assert agree_iff_commute and n_non > 0
print(f"Part B: numbers: both writings agree; 2x2 matrices: the 2xy writing holds"
      f" exactly when AB = BA ({n_comm} commuting pairs, {n_non} non-commuting, 5000 samples)")


def qm(a, b):                             # quaternion product
    a0, a1, a2, a3 = a
    b0, b1, b2, b3 = b
    return (a0*b0 - a1*b1 - a2*b2 - a3*b3, a0*b1 + a1*b0 + a2*b3 - a3*b2,
            a0*b2 - a1*b3 + a2*b0 + a3*b1, a0*b3 + a1*b2 - a2*b1 + a3*b0)


i, j = (0, 1, 0, 0), (0, 0, 1, 0)
s = (0, 1, 1, 0)
lhs = qm(s, s)
f1 = tuple(map(sum, zip(qm(i, i), qm(i, j), qm(j, i), qm(j, j))))
f2 = tuple(map(sum, zip(qm(i, i), tuple(2 * v for v in qm(i, j)), qm(j, j))))
assert lhs == f1 == (-2, 0, 0, 0) and f2 == (-2, 0, 0, 2)
print(f"        quaternions: (i+j)^2 = {lhs}; xy+yx writing {f1}; 2xy writing {f2}")

# ---------- Part C: the oscillator ----------
def deriv(f):             # f: list of complex coefficients, f[n] for x^n
    return [n * f[n] for n in range(1, len(f))] or [0]


def add(*fs):
    n = max(len(f) for f in fs)
    return [sum(f[k] if k < len(f) else 0 for f in fs) for k in range(n)]


def times_x(f):
    return [0] + list(f)


def sc(c, f):
    return [c * v for v in f]


P = lambda f: sc(-1j, deriv(f))           # p = -i d/dx  (hbar = 1)
X = times_x
for _ in range(50):
    f = [complex(rng.randint(-5, 5), rng.randint(-5, 5)) for _ in range(rng.randint(1, 7))]
    plus = add(P(f), sc(1j, X(f)))        # (p + ix) f
    left = add(P(plus), sc(-1j, X(plus))) # (p - ix)(p + ix) f
    right = add(P(P(f)), X(X(f)), f)      # (p^2 + x^2 + 1) f
    n = max(len(left), len(right))
    left += [0] * (n - len(left))
    right += [0] * (n - len(right))
    assert all(abs(a - b) < 1e-9 for a, b in zip(left, right))
print("Part C: (p - ix)(p + ix) = p^2 + x^2 + 1 as operators (hbar = 1);"
      " for commuting symbols the +1 is absent")
