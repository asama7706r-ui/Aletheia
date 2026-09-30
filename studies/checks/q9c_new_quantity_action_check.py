# Q9c: how should a catalog transformation act on the NEW quantity a filler adds?
# Three policies, tested on two blind-test-1 worlds (post hoc, not evidence):
#   E2-11 (truly SAME_LAW_NEW_STATE): phi = -G*Ma/r  ->  phi = -G*Ma/r - G*Mb/rb
#   E2-10 (truly ANOTHER_LAW):        x'' = -w2*x   ->  x'' = -w2*x - gam*x'
import sympy as sp
l = sp.symbols('l', positive=True)
G, Ma, r, Mb, rb = sp.symbols('G Ma r Mb rb', positive=True)

def e2_11(mb_scales):
    # catalog transformation "scale every mass by l" (phi scales by l too)
    orig = -G*Ma/r
    filled = -G*Ma/r - G*Mb/rb
    t = {Ma: l*Ma}
    if mb_scales:
        t[Mb] = l*Mb
    ok_o = sp.simplify(orig.subs(t, simultaneous=True) - l*orig) == 0
    ok_f = sp.simplify(filled.subs(t, simultaneous=True) - l*filled) == 0
    return ok_o, ok_f

t_, w2, gam = sp.symbols('t w2 gam')
x = sp.Function('x')
def e2_10(gam_flips):
    # catalog transformation "reverse time": x(t) -> x(-t)
    res = []
    for rhs in (-w2*x(t_), -w2*x(t_) - gam*sp.diff(x(t_), t_)):
        law = sp.diff(x(t_), t_, 2) - rhs
        rev = law.subs(x(t_), x(-t_)).doit().subs(t_, -t_)
        if gam_flips:
            rev = rev.subs(gam, -gam)
        res.append(sp.simplify(rev - law) == 0)
    return tuple(res)

def verdict(ok_o, ok_f):
    return "ANOTHER_LAW (symmetry lost)" if ok_o and not ok_f else "card kept"

print("policy 'new quantity held fixed':")
print("  E2-11 (truth SAME):   ", verdict(*e2_11(False)))
print("  E2-10 (truth ANOTHER):", verdict(*e2_10(False)))
print("policy 'derive action from the filled law itself' (choose what keeps symmetry):")
print("  E2-11 (truth SAME):   ", verdict(*e2_11(True)))
print("  E2-10 (truth ANOTHER):", verdict(*e2_10(True)))
print("policy 'action by kind' (Mb is a mass -> scales; gam is a material coefficient -> fixed under time reversal):")
print("  E2-11 (truth SAME):   ", verdict(*e2_11(True)))
print("  E2-10 (truth ANOTHER):", verdict(*e2_10(False)))
