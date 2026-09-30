# Core utilities for the blind-test world generator (exact rational arithmetic).
from fractions import Fraction as F
import itertools
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations

FORBIDDEN = {"I", "E", "S", "N", "O", "Q", "pi"}


def fr(x):
    if isinstance(x, F):
        return x
    if isinstance(x, int):
        return F(x)
    if isinstance(x, sp.Rational):
        return F(int(x.p), int(x.q))
    return F(str(x))


def fstr(x):
    x = fr(x)
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


# ---------------- parsing of E1 laws ----------------
def make_locals(world):
    loc = {}
    gsyms, vsyms, psyms = [], [], []
    for g in world["generators"]:
        s = sp.Symbol(g["name"], commutative=False)
        loc[g["name"]] = s
        gsyms.append(s)
    for v in world.get("variables", []):
        s = sp.Symbol(v)
        loc[v] = s
        vsyms.append(s)
    for p in world.get("parameters", []):
        s = sp.Symbol(p)
        loc[p] = s
        psyms.append(s)
    return loc, gsyms, vsyms, psyms


def _nc_word(factors, gindex):
    w = []
    for f in factors:
        if f.is_Symbol:
            w.append(gindex[f])
        elif f.is_Pow:
            b, e = f.args
            if not (e.is_Integer and int(e) >= 1):
                raise ValueError("bad power " + str(f))
            bw = _nc_word(b.args if b.is_Mul else [b], gindex)
            w.extend(bw * int(e))
        elif f.is_Mul:
            w.extend(_nc_word(f.args, gindex))
        else:
            raise ValueError("bad factor " + str(f))
    return tuple(w)


def parse_side(s, loc):
    return parse_expr(s, local_dict=loc, transformations=standard_transformations)


def law_poly(law, loc, gindex):
    """law string -> dict word(tuple of gen idx) -> sympy coeff in variables/params."""
    if law.count("=") != 1:
        raise ValueError("law must contain exactly one '=': " + law)
    lhs, rhs = law.split("=")
    expr = sp.expand(parse_side(lhs, loc) - parse_side(rhs, loc))
    poly = {}
    for term in sp.Add.make_args(expr):
        if term == 0:
            continue
        c, nc = term.args_cnc()
        coeff = sp.Mul(*c)
        w = _nc_word(nc, gindex)
        poly[w] = sp.expand(poly.get(w, 0) + coeff)
    return {w: c for w, c in poly.items() if c != 0}


def world_polys(world):
    loc, gsyms, vsyms, psyms = make_locals(world)
    gindex = {s: i for i, s in enumerate(gsyms)}
    return [law_poly(l, loc, gindex) for l in world["laws"]], vsyms, psyms


def relations(world, param_values=None):
    """Noncommutative relations with rational coefficients: every coefficient of
    every variable monomial of every law (laws hold for all variable values)."""
    polys, vsyms, psyms = world_polys(world)
    psubs = {}
    for p in psyms:
        if param_values is None or p.name not in param_values:
            raise ValueError("missing parameter value " + p.name)
        psubs[p] = sp.Rational(str(param_values[p.name]))
    rels = []
    for poly in polys:
        bymono = {}
        for w, c in poly.items():
            c = sp.expand(sp.sympify(c).subs(psubs))
            if c == 0:
                continue
            if vsyms:
                P = sp.Poly(c, *vsyms)
                terms = P.terms()
            else:
                terms = [((), c)]
            for mono, cc in terms:
                cc = sp.Rational(cc)
                d = bymono.setdefault(mono, {})
                d[w] = d.get(w, F(0)) + F(int(cc.p), int(cc.q))
        for mono in sorted(bymono):
            r = {w: v for w, v in bymono[mono].items() if v != 0}
            if r:
                rels.append(r)
    return rels


def max_degree(world):
    polys, _, _ = world_polys(world)
    return max((len(w) for p in polys for w in p), default=0)


def expr_poly(world, expr_str):
    """Expression in generators (no '=') -> dict word -> Fraction."""
    loc, gsyms, vsyms, psyms = make_locals(world)
    gindex = {s: i for i, s in enumerate(gsyms)}
    e = sp.expand(parse_side(expr_str, loc))
    out = {}
    for term in sp.Add.make_args(e):
        if term == 0:
            continue
        c, nc = term.args_cnc()
        coeff = sp.Rational(sp.Mul(*c))
        w = _nc_word(nc, gindex)
        out[w] = out.get(w, F(0)) + F(int(coeff.p), int(coeff.q))
    return {w: v for w, v in out.items() if v != 0}


# ---------------- exact matrices ----------------
def mat(rows):
    return [[fr(x) for x in r] for r in rows]


def mid(n):
    return [[F(int(i == j)) for j in range(n)] for i in range(n)]


def mzero(n):
    return [[F(0)] * n for _ in range(n)]


def mmul(A, B):
    n, m, p = len(A), len(B), len(B[0])
    C = [[F(0)] * p for _ in range(n)]
    for i in range(n):
        Ai = A[i]
        Ci = C[i]
        for k in range(m):
            a = Ai[k]
            if a:
                Bk = B[k]
                for j in range(p):
                    if Bk[j]:
                        Ci[j] += a * Bk[j]
    return C


def madd(A, B, c=F(1)):
    return [[a + c * b for a, b in zip(ra, rb)] for ra, rb in zip(A, B)]


def iszero(A):
    return all(x == 0 for r in A for x in r)


def meq(A, B):
    return all(a == b for ra, rb in zip(A, B) for a, b in zip(ra, rb))


class MatEval:
    def __init__(self, mats_list):
        self.m = mats_list
        self.n = len(mats_list[0])
        self.cache = {(): mid(self.n)}

    def word(self, w):
        w = tuple(w)
        if w in self.cache:
            return self.cache[w]
        r = mmul(self.word(w[:-1]), self.m[w[-1]])
        self.cache[w] = r
        return r

    def poly(self, p):
        acc = mzero(self.n)
        for w, c in p.items():
            acc = madd(acc, self.word(w), fr(c))
        return acc


def witness_list(world, witness):
    return [mat(witness[g["name"]]) for g in world["generators"]]


def family_of(mats, grades):
    n = len(mats)
    prods = {}
    for i in range(n):
        for j in range(n):
            prods[(i, j)] = mmul(mats[i], mats[j])
    if all(meq(prods[(i, j)], prods[(j, i)]) for i in range(n) for j in range(n)):
        return "comm"
    ok = True
    for i in range(n):
        for j in range(n):
            s = -1 if (grades[i] * grades[j]) % 2 else 1
            if not meq(prods[(i, j)], [[s * x for x in r] for r in prods[(j, i)]]):
                ok = False
    return "graded" if ok else "assoc"


def _reduce_vec(v, piv):
    v = list(v)
    for col, pv in piv:
        c = v[col]
        if c:
            for k in range(len(v)):
                if pv[k]:
                    v[k] -= c * pv[k]
    return v


def algebra_dim(mats):
    """Dimension (unit included) of the algebra generated by the matrices."""
    n = len(mats[0])
    piv = []
    basis = []

    def add(M):
        v = _reduce_vec([x for r in M for x in r], piv)
        for k, x in enumerate(v):
            if x:
                v = [y / x for y in v]
                piv.append((k, v))
                basis.append(M)
                return True
        return False

    add(mid(n))
    i = 0
    while i < len(basis):
        for G in mats:
            add(mmul(basis[i], G))
        i += 1
    return len(basis)


def rank_of_polys_on(mats, polys):
    """Rank of the images of given noncommutative polys (list of dicts) in the matrix algebra."""
    ev = MatEval(mats)
    piv = []
    r = 0
    for p in polys:
        M = ev.poly(p)
        v = _reduce_vec([x for row in M for x in row], piv)
        for k, x in enumerate(v):
            if x:
                piv.append((k, [y / x for y in v]))
                r += 1
                break
    return r
