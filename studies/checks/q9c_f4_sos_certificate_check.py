# Q9c / F4 difficulty 3: can a hard "is it bounded below?" check be turned into an
# exact algebraic certificate that anyone can verify by expansion?
# Example: the Motzkin polynomial (1967) is >= 0 everywhere but is NOT a sum of squares.
# Still, multiplying by (x^2+y^2)^2 gives an exact identity whose right side is visibly >= 0.
import sympy as sp
x, y = sp.symbols('x y', real=True)
M = x**4*y**2 + x**2*y**4 - 3*x**2*y**2 + 1
lhs = (x**2 + y**2)**2 * M
rhs = x**2*y**2*(x**2 + y**2 + 1)*(x**2 + y**2 - 2)**2 + (x**2 - y**2)**2
print("identity (x^2+y^2)^2 * M == x^2 y^2 (x^2+y^2+1)(x^2+y^2-2)^2 + (x^2-y^2)^2 :",
      sp.expand(lhs - rhs) == 0)
print("M(0,0) =", M.subs({x: 0, y: 0}), "  M(1,1) =", M.subs({x: 1, y: 1}), " (minimum 0, so M is bounded below by 0)")
