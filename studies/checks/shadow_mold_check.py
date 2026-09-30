# Hand-check support for the "Yoneda shadow = representing object (mold)" brainstorm.
import sympy as sp
from sympy import Matrix, I, Rational

# (1) Dirac 1+1D relations in COMMUTATIVE algebras: expect the ideal to be (1), i.e. 1 = 0
g0, g1 = sp.symbols('g0 g1')
G = sp.groebner([g0**2 - 1, g1**2 + 1, 2*g0*g1], g0, g1, order='lex')
print("(1) Dirac, commutative Groebner basis:", G.exprs)

# (2) Grassmann relations in COMMUTATIVE algebras: expect a nontrivial but smaller mold (dim 3, not 4)
t1, t2 = sp.symbols('t1 t2')
G2 = sp.groebner([t1**2, t2**2, 2*t1*t2], t1, t2, order='grevlex')
lead = [sp.Poly(g, t1, t2).monoms()[0] for g in G2.exprs]
cands = [(a, b) for a in range(3) for b in range(3)]
std = [m for m in cands if not any(m[0] >= l[0] and m[1] >= l[1] for l in lead)]
print("(2) Grassmann, commutative Groebner basis:", G2.exprs, "standard monomials:", std, "dim =", len(std))

# (3) Associative (non-commutative) witness for the Dirac relations: 2x2 rational matrices
e0 = Matrix([[1, 0], [0, -1]])
e1 = Matrix([[0, 1], [-1, 0]])
print("(3) e0^2 =", e0**2, " e1^2 =", e1**2, " e0e1+e1e0 =", e0*e1 + e1*e0)
basis = [sp.eye(2), e0, e1, e0*e1]
span = Matrix([[b[i, j] for i in range(2) for j in range(2)] for b in basis])
print("    rank of span{1,e0,e1,e0e1} =", span.rank(), "(4 means the mold is all of M2(Q))")

# (4) Bombelli
print("(4) (2+i)^3 =", sp.expand((2 + I)**3), " (2-i)^3 =", sp.expand((2 - I)**3), " sum of cube roots =", sp.expand((2 + I) + (2 - I)))
x = sp.symbols('x')
print("    x^3=7x+6 roots:", sp.solve(x**3 - 7*x - 6, x), " q^2/4 - p^3/27 =", Rational(6)**2/4 - Rational(7)**3/27)

# (5) Piezoelectric: the part of d antisymmetric in (j,k) is invisible when contracted with symmetric sigma
d = sp.symbols('d0:27')
s = sp.symbols('s0:9')
S = Matrix(3, 3, lambda i, j: s[min(i, j)*3 + max(i, j)])
res = []
for i in range(3):
    tot = 0
    for j in range(3):
        for k in range(3):
            tot += (d[i*9 + j*3 + k] - d[i*9 + k*3 + j]) * S[j, k]
    res.append(sp.expand(tot))
print("(5) antisymmetric part contracted with symmetric sigma:", res, " independent comps of symmetric part = 3*6 =", 3*6)

# (6) Alternative relaxation for Dirac: keep commutativity, drop associativity.
# Basis {1, g0, g1}; products: g0^2 = 1, g1^2 = -1, g0g1 = g1g0 = 0 (forced by anticommutation + commutativity).
T = {(0, 0): [1, 0, 0], (0, 1): [0, 1, 0], (0, 2): [0, 0, 1], (1, 0): [0, 1, 0], (2, 0): [0, 0, 1],
     (1, 1): [1, 0, 0], (2, 2): [-1, 0, 0], (1, 2): [0, 0, 0], (2, 1): [0, 0, 0]}
def mul(u, v):
    out = [0, 0, 0]
    for p in range(3):
        for q in range(3):
            c = u[p]*v[q]
            if c:
                for r in range(3):
                    out[r] += c*T[(p, q)][r]
    return out
G0, G1 = [0, 1, 0], [0, 0, 1]
print("(6) g0^2 =", mul(G0, G0), " g1^2 =", mul(G1, G1), " g0g1+g1g0 =", [a + b for a, b in zip(mul(G0, G1), mul(G1, G0))])
print("    (g0 g1) g1 =", mul(mul(G0, G1), G1), " vs g0 (g1 g1) =", mul(G0, mul(G1, G1)), " -> non-associative, but 1 != 0")
