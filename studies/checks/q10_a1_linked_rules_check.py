"""Q10 / A1 check (2026-10-14): when do two old rules stand or fall together?

The user asked whether splitting rules is always better, and whether some
rules cannot work without each other.

Part 1: "no zero divisors" (ab = 0 -> a = 0 or b = 0) and "cancellation"
(ab = ac, a != 0 -> b = c) agree in every ring checked: Z/n for n = 2..30
and all 2x2 matrices over Z/2 and Z/3 (16 and 81 elements). Proof sketch:
a(b - c) = 0 needs negatives; a*0 = 0 needs distributivity and negatives.
Part 2: without negatives they come apart: the rationals plus an element w
that swallows everything (w + a = w, w * a = w) keep "no zero divisors" but
break cancellation (w*1 = w*2 with 1 != 2).
So "same fact" is relative to the other rules kept.
Standard library only.
"""
from fractions import Fraction as Fr
from itertools import product


def check(elems, add, mul, zero):
    nzd = all(not (mul(a, b) == zero and a != zero and b != zero)
              for a in elems for b in elems)
    canc = all(not (mul(a, b) == mul(a, c) and a != zero and b != c)
               for a in elems for b in elems for c in elems)
    return nzd, canc


# Part 1: Z/n
for n in range(2, 31):
    E = range(n)
    r = check(E, lambda a, b: (a + b) % n, lambda a, b: (a * b) % n, 0)
    assert r[0] == r[1], n
# Part 1: 2x2 matrices over Z/p (non-commutative rings)
for p in (2, 3):
    M = [tuple(v) for v in product(range(p), repeat=4)]
    mm = lambda A, B: ((A[0]*B[0] + A[1]*B[2]) % p, (A[0]*B[1] + A[1]*B[3]) % p,
                       (A[2]*B[0] + A[3]*B[2]) % p, (A[2]*B[1] + A[3]*B[3]) % p)
    r = check(M, None, mm, (0, 0, 0, 0))
    assert r == (False, False), (p, r)   # both fail together
print("Part 1: no-zero-divisors and cancellation agree in Z/2..Z/30 and 2x2 matrices")

# Part 2: rationals plus a swallowing element w
W = "w"
mul = lambda a, b: W if W in (a, b) else a * b
S = [W, Fr(0), Fr(1), Fr(2), Fr(-1), Fr(1, 2), Fr(3)]
nzd, canc = check(S, None, mul, Fr(0))
assert nzd and not canc
print("Part 2: with w (no negatives): no-zero-divisors holds, cancellation fails")
