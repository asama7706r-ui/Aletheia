# Rational points of the laws (generators replaced by commuting rationals).
from fractions import Fraction as F
import itertools
import sympy as sp

GRID_USER = [F(k) for k in range(-5, 6)] + [F(1, 2), F(-1, 2), F(1, 3), F(-1, 3)]


def eval_comm(poly, vals):
    tot = F(0)
    for w, c in poly.items():
        t = F(c)
        for g in w:
            t *= vals[g]
            if t == 0:
                break
        tot += t
    return tot


def comm_sympy(rels, ngens):
    xs = sp.symbols("z0:%d" % ngens)
    out = []
    for r in rels:
        e = 0
        for w, c in r.items():
            t = sp.Rational(c.numerator, c.denominator)
            for g in w:
                t = t * xs[g]
            e += t
        e = sp.expand(e)
        if e != 0:
            out.append(e)
    return out, xs


def _rat_roots(u, x):
    roots = []
    for fac, mult in sp.factor_list(sp.Poly(u, x))[1]:
        if fac.degree() == 1:
            a, b = fac.all_coeffs()
            roots.append(sp.Rational(-b, a))
    return roots


def rat_solve(polys, syms):
    """All rational solutions of a polynomial system, or 'POSDIM' if a positive-dimensional
    component blocks the enumeration."""
    polys = [sp.expand(p) for p in polys]
    polys = [p for p in polys if p != 0]
    if any(p.is_number for p in polys):
        return []
    if not syms:
        return [{}]
    if not polys:
        return "POSDIM"
    G = sp.groebner(polys, *syms, order="lex")
    ex = list(G.exprs)
    if ex == [1] or any(e.is_number and e != 0 for e in ex):
        return []
    last = syms[-1]
    uni = [g for g in ex if g.free_symbols <= {last}]
    if not uni:
        return "POSDIM"
    sols = []
    for r0 in _rat_roots(uni[0], last):
        sub = [sp.expand(g.subs(last, r0)) for g in ex]
        rec = rat_solve(sub, syms[:-1])
        if rec == "POSDIM":
            return "POSDIM"
        for s in rec:
            s = dict(s)
            s[last] = r0
            sols.append(s)
    return sols


def rational_points(rels, ngens):
    polys, xs = comm_sympy(rels, ngens)
    res = rat_solve(polys, list(xs))
    if res == "POSDIM":
        return "POSDIM"
    return [[F(int(s[x].p), int(s[x].q)) for x in xs] for s in res]


def radical_kills(rels, ngens, qpolys):
    """True if 1 is in <rels, 1 - t*prod(q)> in the commutative ring: then no point over any
    field (in particular no rational point) has all q nonzero."""
    polys, xs = comm_sympy(rels, ngens)
    qs, _ = comm_sympy(qpolys, ngens)
    t = sp.Symbol("tt_rab")
    prod = 1
    for q in qs:
        prod = prod * q
    if not qs:
        return False
    G = sp.groebner(polys + [1 - t * prod], t, *xs, order="grevlex")
    return list(G.exprs) == [1]


def grid_points(rels, ngens, observed, grid=GRID_USER):
    """Brute force: points of the grid satisfying all relations with all observed nonzero."""
    hits = []
    for vals in itertools.product(grid, repeat=ngens):
        if all(eval_comm(r, vals) == 0 for r in rels):
            if all(eval_comm(q, vals) != 0 for q in observed):
                hits.append(vals)
    return hits
