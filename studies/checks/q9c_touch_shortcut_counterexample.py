# Q9c: is "only re-check transformations that touch the added term" safe?
# Counterexample: a vertical spring. Adding gravity (-g) touches neither x nor a,
# yet it breaks the up/down mirror x -> -x (which also flips a = x'').
import sympy as sp
t, w2, g = sp.symbols('t w2 g')
x = sp.Function('x')
def mirror_invariant(rhs):
    law = sp.diff(x(t), t, 2) - rhs
    m = law.subs(x(t), -x(t)).doit()
    return sp.simplify(m + law) == 0 or sp.simplify(m - law) == 0
print("horizontal spring  x'' = -w2 x      mirror symmetric:", mirror_invariant(-w2*x(t)))
print("vertical spring    x'' = -w2 x - g  mirror symmetric:", mirror_invariant(-w2*x(t) - g))
