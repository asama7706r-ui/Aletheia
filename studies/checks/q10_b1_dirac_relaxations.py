"""Q10 / B1 check (2026-10-07): the two relaxations of the Dirac demand.

Demand: (g.p)^2 = p0^2 - p1^2 - p2^2 - p3^2 for all p, with g0..g3 new.
1. Drop associativity, keep commutativity: a 5-dim algebra {1,e0..e3},
   e_m e_n = 0 (m != n), e0^2 = 1, ei^2 = -1. Check the demand (as an
   identity in p: coefficient of every p_m p_n), commutativity,
   non-associativity, and a zero divisor.
2. Drop commutativity, keep associativity: Dirac matrices. Check the
   Clifford relations, and that a zero divisor appears here too.
3. Operators acting on states compose associatively (random 4x4 maps).
Standard library only.
"""
import random

eta = [1, -1, -1, -1]

# --- 1. commutative, non-associative model --------------------------------
def mul(a, b):  # element = 5 coefficients over [1, e0, e1, e2, e3]
    out = [0] * 5
    for i in range(5):
        for j in range(5):
            c = a[i] * b[j]
            if c == 0:
                continue
            if i == 0:
                out[j] += c
            elif j == 0:
                out[i] += c
            elif i == j:
                out[0] += c * eta[i - 1]
    return out

def e(k):
    v = [0] * 5; v[k] = 1; return v

def add(a, b):
    return [x + y for x, y in zip(a, b)]

# (g.p)^2 = sum_mn p_m p_n e_m e_n; identity in p <=> e_m e_n + e_n e_m = 2 eta_mn
ok1 = all(add(mul(e(m + 1), e(n + 1)), mul(e(n + 1), e(m + 1)))
          == [2 * (eta[m] if m == n else 0), 0, 0, 0, 0]
          for m in range(4) for n in range(4))
print("1. demand holds as identity in p:", ok1)
print("1. commutative:", all(mul(e(i), e(j)) == mul(e(j), e(i)) for i in range(5) for j in range(5)))
print("1. (e0 e0) e1 =", mul(mul(e(1), e(1)), e(2)), "  e0 (e0 e1) =", mul(e(1), mul(e(1), e(2))))
print("1. (1+e0)(1-e0) =", mul([1, 1, 0, 0, 0], [1, -1, 0, 0, 0]))

# --- 2. Dirac matrices -----------------------------------------------------
def mm(A, B):
    n = len(A)
    return [[sum(A[i][k] * B[k][j] for k in range(n)) for j in range(n)] for i in range(n)]

def madd(A, B, s=1):
    return [[A[i][j] + s * B[i][j] for j in range(len(A))] for i in range(len(A))]

def block(a, b, c, d):
    return [a[0] + b[0], a[1] + b[1], c[0] + d[0], c[1] + d[1]]

I2 = [[1, 0], [0, 1]]; Z2 = [[0, 0], [0, 0]]
neg = lambda M: [[-x for x in r] for r in M]
sx = [[0, 1], [1, 0]]; sy = [[0, -1j], [1j, 0]]; sz = [[1, 0], [0, -1]]
g = [block(I2, Z2, Z2, neg(I2))] + [block(Z2, s, neg(s), Z2) for s in (sx, sy, sz)]
I4 = [[1 if i == j else 0 for j in range(4)] for i in range(4)]
close = lambda A, B: all(abs(A[i][j] - B[i][j]) < 1e-12 for i in range(4) for j in range(4))
ok2 = all(close(madd(mm(g[m], g[n]), mm(g[n], g[m])),
                [[2 * (eta[m] if m == n else 0) * x for x in r] for r in I4])
          for m in range(4) for n in range(4))
print("2. Clifford relations hold:", ok2)
print("2. (1+g0)(1-g0) == 0:", close(mm(madd(I4, g[0]), madd(I4, g[0], -1)), [[0] * 4] * 4))
print("2. g0 g1 == g1 g0:", close(mm(g[0], g[1]), mm(g[1], g[0])))

# --- 3. composition of linear maps is associative --------------------------
random.seed(0)
R = lambda: [[random.uniform(-1, 1) for _ in range(4)] for _ in range(4)]
A, B, C = R(), R(), R()
print("3. (AB)C == A(BC):", close(mm(mm(A, B), C), mm(A, mm(B, C))))
