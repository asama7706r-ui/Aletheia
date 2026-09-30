# Re-check of ladder step 2 (u^2 = c) identities. Scratch only.
import sympy as sp
a,b,p,q,t,x,v,phi,c = sp.symbols('a b p q t x v phi c')
u = sp.Symbol('u')
red = lambda e, cv: sp.expand(sp.rem(sp.expand(e), u**2 - cv, u))
parts = lambda e: (sp.Poly(e, u).coeff_monomial(1), sp.Poly(e, u).coeff_monomial(u))
for cv, name in [(-1, 'i'), (0, 'eps'), (1, 'j')]:
    z, w = a + b*u, p + q*u
    N = lambda e: red(e * (parts(e)[0] - parts(e)[1]*u), cv)
    zw = red(z*w, cv)
    print(name, '| N(z) =', N(z), '| N multiplicative:', sp.expand(N(zw) - N(z)*N(w)) == 0,
          '| z*zbar/N == 1:', sp.simplify(red(z*(a - b*u), cv)/N(z) - 1) == 0)
print('(1+j)(1-j) =', red((1+u)*(1-u), 1), '| eps^2 =', red(u*u, 0))
f = lambda s: 3*s**3 - 2*s + 5
print('AD ok:', sp.expand(red(f(a+u), 0) - (f(a) + sp.diff(f(a), a)*u)) == 0)
print('Galilei:', red((t + u*x)*(1 + u*v), 0))
T, X = parts(red((t + u*x)*(sp.cosh(phi) + u*sp.sinh(phi)), 1))
print('Lorentz interval preserved:', sp.simplify(T**2 - X**2 - (t**2 - x**2)) == 0)
Nc = red((t + u*x)*(t - u*x), 1/c**2)
print('size with u^2=1/c^2:', Nc, '| c->oo:', sp.limit(Nc, c, sp.oo))
X_ = sp.Symbol('X')
print('factor over Q:', sp.factor_list(X_**2 + 1), sp.factor_list(X_**2 + 2), sp.factor_list(X_**2 - 1))
