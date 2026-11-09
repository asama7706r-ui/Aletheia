"""Workshop 10.16 (an exact check, not a proof): Cayley-Dickson algebras over the rationals, doubling from the reals.
At every doubling tried (dimensions 2 to 64), x * conj(x) = conj(x) * x = |x|^2 for random rational x, so every
nonzero x has a two-sided inverse conj(x) / |x|^2: q13 holds in algebras of unbounded dimension. From dimension 16
on, the algebra has zero divisors, so q12 fails there. The general fact follows from the doubling formula by
induction; this script only checks samples.
Usage (from aletheia_blind_test_5b/): python -I audit/cayley_dickson_check.py"""
import random
import sys
from fractions import Fraction as F

sys.stdout.reconfigure(encoding="utf-8")


def conj(x):
    return [x[0]] + [-a for a in x[1:]]


def mul(x, y):
    """(a, b)(c, d) = (ac - conj(d) b, d a + b conj(c)), on vectors of length 2^k."""
    n = len(x)
    if n == 1:
        return [x[0] * y[0]]
    h = n // 2
    a, b, c, d = x[:h], x[h:], y[:h], y[h:]
    p = [u - v for u, v in zip(mul(a, c), mul(conj(d), b))]
    q = [u + v for u, v in zip(mul(d, a), mul(b, conj(c)))]
    return p + q


def unit(i, n):
    return [F(int(j == i)) for j in range(n)]


def main():
    random.seed(7)
    for n in (2, 4, 8, 16, 32, 64):
        ok = True
        for _ in range(12):
            x = [F(random.randint(-9, 9), random.randint(1, 5)) for _ in range(n)]
            if not any(x):
                continue
            norm = sum(a * a for a in x)
            for r in (mul(x, conj(x)), mul(conj(x), x)):
                if r[0] != norm or any(r[1:]):
                    ok = False
        print(f"dimension {n}: x*conj(x) = conj(x)*x = |x|^2 on 12 random rational x: {ok}")
    a = [u + v for u, v in zip(unit(3, 16), unit(10, 16))]
    b = [u - v for u, v in zip(unit(6, 16), unit(15, 16))]
    prod = mul(a, b)
    print(f"dimension 16: (e3 + e10) * (e6 - e15) = {'0' if not any(prod) else prod}, with both factors nonzero")


if __name__ == "__main__":
    main()
