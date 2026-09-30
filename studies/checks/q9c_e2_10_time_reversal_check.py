import sympy as sp
t, s = sp.symbols('t s')
w2, gam = sp.symbols('w2 gam')
x = sp.Function('x')
def rev(expr):
    # time reversal: x(t) -> x(-t); constants stay fixed
    return sp.simplify(expr.subs(x(t), x(-t)).doit())
for name, rhs in [("original", -w2*x(t)), ("filled", -w2*x(t) - gam*sp.diff(x(t), t))]:
    law = sp.diff(x(t), t, 2) - rhs            # law: x'' - rhs = 0
    r = rev(law).subs(t, -t)                   # evaluate reversed law at same instant
    print(name, "invariant (constants fixed):", sp.simplify(r - law) == 0)
    r2 = rev(law).subs(t, -t).subs(gam, -gam)  # also flip gam as if it were T^-1 "kinematic"
    print(name, "invariant if gam also flips:", sp.simplify(r2 - law) == 0)
