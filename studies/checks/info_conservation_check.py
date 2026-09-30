# Scratch verification for the information-conservation test (not project code).
import sympy as sp
from grassmann_check import G, one, t1, t2   # reuse the exterior-algebra calculator
a,b,c,d,p,q,r,s,t,x,v,g0,g1,lam,C,n0,n1 = sp.symbols('a b c d p q r s t x v g0 g1 lam C n0 n1')
u = sp.Symbol('u')
red = lambda e, cv: sp.expand(sp.rem(sp.expand(e), u**2 - cv, u))
parts = lambda e: (sp.Poly(e, u).coeff_monomial(1), sp.Poly(e, u).coeff_monomial(u))
N = lambda e, cv: red(e*(parts(e)[0] - parts(e)[1]*u), cv)

print('--- T2: outside cracks, what N forgets is a norm-1 symmetry element ---')
for cv, name in [(-1,'i'), (0,'eps'), (1,'j')]:
    z0, z1 = a + b*u, p + q*u
    # g = z1 * z0^{-1} ; z0^{-1} = zbar0 / N(z0)
    g = red(z1*(a - b*u), cv) / N(z0, cv)
    Ng = sp.simplify(N(sp.expand(g*N(z0,cv)), cv) / N(z0,cv)**2)
    print(name, '| N(z1 z0^-1) =', sp.simplify(Ng), '(equals N(z1)/N(z0):', sp.simplify(Ng - N(z1,cv)/N(z0,cv)) == 0, ')')

print('--- T3: at the cracks (N=0, z!=0) the symmetry cannot move everything ---')
# eps: crack z = b*eps ; symmetry g = +/-(1 + v eps)
print('eps: (1+v eps)(b eps) =', red((1 + v*u)*(b*u), 0), ' -> magnitude b is invariant (up to sign)')
# j: cracks are the two light lines t(1+j), t(1-j); norm-1 g = g0 + g1 j with g0^2 - g1^2 = 1
print('j: g(1+j) =', red((g0 + g1*u)*(1 + u), 1), '| g(1-j) =', red((g0 + g1*u)*(1 - u), 1))
print('   each light line is mapped to itself -> "which light line" is extra information')
gl = (lam + 1/lam)/2 + (lam - 1/lam)/2*u
print('   rational scaling along the line: N(g) =', sp.simplify(N(sp.expand(gl*lam), 1)/lam**2), ', g(1+j) =', sp.simplify(red(gl*(1+u), 1)))
# Grassmann: crack z = b th1 + c th2 + d th1th2 ; norm-1 g = 1 + p th1 + q th2 + r th1th2
z = b*t1 + c*t2 + d*(t1*t2); gG = one + p*t1 + q*t2 + r*(t1*t2)
print('Grassmann: g*z =', gG*z, ' -> (b, c) invariant, d shifts by (p c - q b)')
print('           g*(d th1th2) =', gG*(d*(t1*t2)), ' -> area d invariant when b=c=0')

print('--- T4: contraction j^2 = 1/C^2, C -> oo ---')
Nc = N(t + u*x, 1/C**2)
print('size:', Nc, '-> limit', sp.limit(Nc, C, sp.oo))
print('zero divisors: t = +/- x/C  -> limit t =', sp.limit(x/C, C, sp.oo), '(two light lines merge into one)')

print('--- T5: two-body decay at rest (units c=1): electron energy is FIXED ---')
M, m1, m2 = sp.symbols('M m1 m2', positive=True)
E1, E2, P = sp.symbols('E1 E2 P', positive=True)
sol = sp.solve([sp.Eq(E1 + E2, M), sp.Eq(E1**2 - P**2, m1**2), sp.Eq(E2**2 - P**2, m2**2)], [E1, E2, P], dict=True)
print('E1 =', sp.simplify(sol[0][E1]), ' (a single value -> a continuous spectrum means a hidden third body)')
