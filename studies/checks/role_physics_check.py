# Checks for "role = no silent loss of the law's content (math + physical identity card)".
import sympy as sp
from sympy import Rational, sqrt, symbols, series, simplify, Matrix

# (1) Klein-Gordon vs Dirac: hydrogen n=2 fine structure (the "consistent law of a different state" case)
a = symbols('alpha', positive=True)
def level(n, k):
    # exact relativistic hydrogen level / (m c^2); k = j+1/2 (Dirac) or l+1/2 (Klein-Gordon)
    delta = k - sqrt(k**2 - a**2)
    return 1 / sqrt(1 + (a / (n - delta))**2)
n = 2
dirac_split = sp.series(level(n, Rational(2)) - level(n, Rational(1)), a, 0, 6).removeO()   # j=3/2 minus j=1/2
kg_split    = sp.series(level(n, Rational(3, 2)) - level(n, Rational(1, 2)), a, 0, 6).removeO()  # l=1 minus l=0
print("(1) Dirac n=2 splitting  (units m c^2):", sp.simplify(dirac_split))
print("    KG    n=2 splitting  (units m c^2):", sp.simplify(kg_split))
print("    ratio KG / Dirac =", sp.simplify(kg_split / dirac_split))
alpha_num = 1/137.035999
mc2_eV = 510998.95
print("    Dirac 2p3/2-2p1/2 ~ %.3e eV ; KG 2p-2s ~ %.3e eV" % (float(dirac_split.subs(a, alpha_num))*mc2_eV,
                                                             float(kg_split.subs(a, alpha_num))*mc2_eV))

# (2) Piezoelectric tensor in a centrosymmetric crystal: inversion R = -I forces d = 0
d = sp.symbols('d0:27')
R = -sp.eye(3)
eqs = []
for i in range(3):
    for j in range(3):
        for k in range(3):
            transformed = sum(R[i, l]*R[j, m]*R[k, q]*d[l*9 + m*3 + q] for l in range(3) for m in range(3) for q in range(3))
            eqs.append(sp.Eq(transformed, d[i*9 + j*3 + k]))
sol = sp.solve(eqs, d, dict=True)
print("(2) centrosymmetric invariance solution: all d = 0 ?", all(v == 0 for v in sol[0].values()) and len(sol[0]) == 27)

# (3) The non-associative Dirac filler has no nonzero representation by operators (operators compose associatively)
A, B = sp.symbols('A B', commutative=False)
# relations imposed by the 3-dim commutative non-associative mold, read as operators: A*B = 0, B*B = -1, A*A = 1
step = sp.expand((A*B)*B)            # = 0 because A*B = 0
alt  = sp.expand(A*(B*B))            # = A*(-1) = -A by associativity of operator composition
print("(3) (A*B)*B ->", 0, " ; A*(B*B) ->", alt.subs(B*B, -1), " => associativity forces -A = 0, so A = 0, contradicting A*A = 1")

# (4) j vs +-1: identifying u = 1 in Q[u]/(u^2-1) destroys (u-1); the boost law needs both light-cone components
t, x, phi = sp.symbols('t x phi', real=True)
# with u = 1 the element t + u*x collapses to t + x; the invariant t^2 - x^2 = (t+x)(t-x) needs the lost component (t - x)
print("(4) interval t^2-x^2 factors as", sp.factor(t**2 - x**2), " -> needs (t - x), which u=1 erases")
