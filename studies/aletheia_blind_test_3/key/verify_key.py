#!/usr/bin/env python3
"""Generator's own verification of blind test 3 (written from protocol_v3.md alone).

It recomputes, with exact rational arithmetic, the reference answer of every
Part A world and every Part B item, checks the validity rules W1-W9 (W10 only
against the format example of Section 3), checks the compositions of Sections
6 and 10.1, and compares everything with key/key.json.

Usage:  python key/verify_key.py worlds data key/key.json
"""
import copy
import itertools
import json
import os
import re
import sys
from fractions import Fraction as F

import sympy

LIMIT = 10 ** 9
RESERVED = set("re im ln pi oo li lam mu nan zoo sin cos tan cot sec csc exp log abs max "
               "min sqrt sign floor root beta gamma zeta erf".split())
NAME_RE = re.compile(r'^[a-z][a-z0-9]{1,5}$')
RAT_RE = re.compile(r'^\s*(-?)(\d+)(?:/(\d+))?\s*$')
SYM_RE = re.compile(r'^\s*(-?\d+(?:/\d+)?)\s*\*\s*([a-z][a-z0-9]*)\s*$')
REASONS = ["TYPE", "SYMMETRY", "SCOPE", "SHAPE", "BOUND"]


class Invalid(Exception):
    pass


# ----------------------------------------------------------------------------
# rationals and dimensions
# ----------------------------------------------------------------------------
def rat(s, where=""):
    if isinstance(s, bool) or not isinstance(s, str):
        raise Invalid(f"{where}: rational must be a string, got {s!r}")
    m = RAT_RE.match(s)
    if not m:
        raise Invalid(f"{where}: bad rational {s!r}")
    num = int(m.group(2))
    den = int(m.group(3)) if m.group(3) else 1
    if den == 0:
        raise Invalid(f"{where}: zero denominator")
    if num > LIMIT or den > LIMIT:
        raise Invalid(f"{where}: rational {s!r} exceeds 10^9")
    v = F(num, den)
    return -v if m.group(1) else v


def fs(x):
    """exact rational -> string"""
    x = F(x)
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def ndims(d, where=""):
    if not isinstance(d, dict):
        raise Invalid(f"{where}: dims must be a map")
    out = {}
    for k, v in d.items():
        if isinstance(v, bool):
            raise Invalid(f"{where}: bad exponent")
        if isinstance(v, int):
            fv = F(v)
        elif isinstance(v, str):
            fv = rat(v, where)
        else:
            raise Invalid(f"{where}: bad exponent {v!r}")
        if fv != 0:
            out[k] = fv
    return out


def dadd(a, b, s=1):
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, F(0)) + s * v
        if out[k] == 0:
            del out[k]
    return out


def dscale(a, n):
    return {k: v * n for k, v in a.items() if v * n != 0}


def rank(M):
    M = [list(r) for r in M]
    rk, cols = 0, (len(M[0]) if M else 0)
    for c in range(cols):
        piv = next((i for i in range(rk, len(M)) if M[i][c] != 0), None)
        if piv is None:
            continue
        M[rk], M[piv] = M[piv], M[rk]
        for i in range(len(M)):
            if i != rk and M[i][c] != 0:
                f = M[i][c] / M[rk][c]
                M[i] = [a - f * b for a, b in zip(M[i], M[rk])]
        rk += 1
    return rk


def reachable(target, const_dims):
    """Is `target` a product of rational powers of the given constant dims?"""
    keys = sorted(set(target) | {k for d in const_dims for k in d})
    if not keys:
        return True
    A = [[d.get(k, F(0)) for d in const_dims] for k in keys]
    Ab = [A[i] + [target.get(k, F(0))] for i, k in enumerate(keys)]
    if not const_dims:
        return all(v == 0 for v in target.values())
    return rank(A) == rank(Ab)


# ----------------------------------------------------------------------------
# expressions
# ----------------------------------------------------------------------------
TOKEN = re.compile(r'\s*(?:(?P<num>\d+)|(?P<name>[A-Za-z_][A-Za-z0-9_]*)|(?P<op>\*\*|[-+*/()]))')


def tokenize(s):
    s = s.strip()
    pos, out = 0, []
    while pos < len(s):
        m = TOKEN.match(s, pos)
        if not m or m.end() == pos:
            raise Invalid(f"bad token in {s!r} at {pos}")
        if m.group('num') is not None:
            out.append(('num', m.group('num')))
        elif m.group('name') is not None:
            out.append(('name', m.group('name')))
        else:
            out.append(('op', m.group('op')))
        pos = m.end()
    return out


class Parser:
    def __init__(self, s):
        self.s = s
        self.t = tokenize(s)
        self.i = 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def take(self):
        tok = self.peek()
        self.i += 1
        return tok

    def expect(self, op):
        if self.take() != ('op', op):
            raise Invalid(f"expected {op!r} in {self.s!r}")

    def parse(self):
        node = self.expr()
        if self.i != len(self.t):
            raise Invalid(f"trailing tokens in {self.s!r}")
        return node

    def expr(self):
        node = self.term()
        while self.peek() in (('op', '+'), ('op', '-')):
            op = self.take()[1]
            node = ('add' if op == '+' else 'sub', node, self.term())
        return node

    def term(self):
        node = self.unary()
        while self.peek() in (('op', '*'), ('op', '/')):
            op = self.take()[1]
            node = ('mul' if op == '*' else 'div', node, self.unary())
        return node

    def unary(self):
        if self.peek() == ('op', '-'):
            self.take()
            return ('neg', self.unary())
        if self.peek() == ('op', '+'):
            self.take()
            return self.unary()
        return self.power()

    def power(self):
        base = self.atom()
        if self.peek() == ('op', '**'):
            self.take()
            paren = neg = False
            if self.peek() == ('op', '('):
                self.take()
                paren = True
            if self.peek() == ('op', '-'):
                self.take()
                neg = True
            tok = self.take()
            if tok[0] != 'num':
                raise Invalid(f"power must be an integer in {self.s!r}")
            n = -int(tok[1]) if neg else int(tok[1])
            if paren:
                self.expect(')')
            if not -3 <= n <= 3:
                raise Invalid(f"power {n} out of [-3,3] in {self.s!r}")
            return ('pow', base, n)
        return base

    def atom(self):
        tok = self.take()
        if tok[0] == 'num':
            v = int(tok[1])
            if v > LIMIT:
                raise Invalid(f"number {v} exceeds 10^9 in {self.s!r}")
            return ('num', F(v))
        if tok[0] == 'name':
            return ('var', tok[1])
        if tok == ('op', '('):
            node = self.expr()
            self.expect(')')
            return node
        raise Invalid(f"unexpected token {tok} in {self.s!r}")


def parse(s):
    if not isinstance(s, str):
        raise Invalid(f"expression must be a string: {s!r}")
    return Parser(s).parse()


def ev(node, env):
    k = node[0]
    if k == 'num':
        return node[1]
    if k == 'var':
        return env[node[1]]
    if k == 'neg':
        return -ev(node[1], env)
    if k == 'pow':
        b = ev(node[1], env)
        if node[2] < 0 and b == 0:
            raise ZeroDivisionError
        return b ** node[2]
    a, b = ev(node[1], env), ev(node[2], env)
    if k == 'add':
        return a + b
    if k == 'sub':
        return a - b
    if k == 'mul':
        return a * b
    if b == 0:
        raise ZeroDivisionError
    return a / b


def dm(node, denv):
    k = node[0]
    if k == 'num':
        return {}
    if k == 'var':
        return dict(denv[node[1]])
    if k == 'neg':
        return dm(node[1], denv)
    if k == 'pow':
        return dscale(dm(node[1], denv), node[2])
    a, b = dm(node[1], denv), dm(node[2], denv)
    if k in ('add', 'sub'):
        if a != b:
            raise Invalid(f"inhomogeneous sum: {a} vs {b}")
        return a
    if k == 'mul':
        return dadd(a, b)
    return dadd(a, b, -1)


def names(node):
    k = node[0]
    if k == 'num':
        return set()
    if k == 'var':
        return {node[1]}
    if k in ('neg', 'pow'):
        return names(node[1])
    return names(node[1]) | names(node[2])


def to_sym(node, S):
    k = node[0]
    if k == 'num':
        return sympy.Rational(node[1].numerator, node[1].denominator)
    if k == 'var':
        return S[node[1]]
    if k == 'neg':
        return -to_sym(node[1], S)
    if k == 'pow':
        return to_sym(node[1], S) ** node[2]
    a, b = to_sym(node[1], S), to_sym(node[2], S)
    if k == 'add':
        return a + b
    if k == 'sub':
        return a - b
    if k == 'mul':
        return a * b
    return a / b


def is_zero(e):
    return sympy.cancel(sympy.together(e)) == 0


# ----------------------------------------------------------------------------
# exact LP (two-phase simplex, Bland's rule), x free
# ----------------------------------------------------------------------------
def _pivot(T, basis, r, col):
    pv = T[r][col]
    T[r] = [v / pv for v in T[r]]
    for i in range(len(T)):
        if i != r and T[i][col] != 0:
            f = T[i][col]
            T[i] = [a - f * b for a, b in zip(T[i], T[r])]
    basis[r] = col


def _run(T, basis, obj, ncols):
    while True:
        bset = set(basis)
        enter = None
        for j in range(ncols):
            if j in bset:
                continue
            rc = obj[j] - sum(obj[basis[i]] * T[i][j] for i in range(len(T)) if obj[basis[i]] != 0)
            if rc > 0:
                enter = j
                break
        if enter is None:
            return 'optimal'
        best = None
        for i in range(len(T)):
            a = T[i][enter]
            if a > 0:
                ratio = T[i][-1] / a
                if best is None or ratio < best[0] or (ratio == best[0] and basis[i] < basis[best[1]]):
                    best = (ratio, i)
        if best is None:
            return 'unbounded'
        _pivot(T, basis, best[1], enter)


def lp(A, b, c=None):
    """max c.x s.t. A x <= b (x free). Returns (status, value, x)."""
    m = len(A)
    n = len(c) if c is not None else (len(A[0]) if m else 0)
    if m == 0:
        if c is None or all(v == 0 for v in c):
            return ('optimal', F(0), [F(0)] * n)
        return ('unbounded', None, None)
    width0 = 2 * n + m
    T, arts = [], []
    for i in range(m):
        row = [F(0)] * width0
        for j in range(n):
            row[j] = F(A[i][j])
            row[n + j] = -F(A[i][j])
        row[2 * n + i] = F(1)
        rhs = F(b[i])
        if rhs < 0:
            row = [-v for v in row]
            rhs = -rhs
            arts.append(i)
        T.append(row + [rhs])
    na = len(arts)
    T = [r[:-1] + [F(0)] * na + [r[-1]] for r in T]
    basis = [2 * n + i for i in range(m)]
    for t, i in enumerate(arts):
        T[i][width0 + t] = F(1)
        basis[i] = width0 + t
    if na:
        obj1 = [F(0)] * width0 + [F(-1)] * na
        _run(T, basis, obj1, width0 + na)
        val = sum(obj1[basis[i]] * T[i][-1] for i in range(len(T)))
        if val < 0:
            return ('infeasible', None, None)
        for i in range(len(T) - 1, -1, -1):
            if basis[i] >= width0:
                for j in range(width0):
                    if T[i][j] != 0:
                        _pivot(T, basis, i, j)
                        break
                else:
                    del T[i]
                    del basis[i]
        T = [r[:width0] + [r[-1]] for r in T]
    if c is None:
        x = [F(0)] * width0
        for i in range(len(T)):
            x[basis[i]] = T[i][-1]
        return ('optimal', F(0), [x[j] - x[n + j] for j in range(n)])
    obj = [F(v) for v in c] + [-F(v) for v in c] + [F(0)] * m
    st = _run(T, basis, obj, width0)
    if st == 'unbounded':
        return ('unbounded', None, None)
    x = [F(0)] * width0
    for i in range(len(T)):
        x[basis[i]] = T[i][-1]
    xs = [x[j] - x[n + j] for j in range(n)]
    return ('optimal', sum(F(c[j]) * xs[j] for j in range(n)), xs)


class System:
    """rows: list of (coef dict, rhs, tag); meaning coef.x <= rhs"""

    def __init__(self, unknowns, rows):
        self.unknowns = unknowns
        self.rows = rows

    def mat(self):
        A = [[r[0].get(u, F(0)) for u in self.unknowns] for r in self.rows]
        b = [r[1] for r in self.rows]
        return A, b

    def feasible(self):
        if not self.unknowns:
            return all(r[1] >= 0 for r in self.rows)
        A, b = self.mat()
        return lp(A, b)[0] == 'optimal'

    def point(self):
        A, b = self.mat()
        st, _, x = lp(A, b)
        return None if st != 'optimal' else dict(zip(self.unknowns, x))

    def maxof(self, coef, const=F(0)):
        """max of coef.x + const over the feasible set (None if unbounded)"""
        if not self.unknowns:
            return const
        A, b = self.mat()
        st, val, _ = lp(A, b, [coef.get(u, F(0)) for u in self.unknowns])
        if st == 'infeasible':
            raise RuntimeError("maxof on infeasible system")
        return None if st == 'unbounded' else val + const

    def rangeof(self, coef, const=F(0)):
        hi = self.maxof(coef, const)
        lo = self.maxof({k: -v for k, v in coef.items()}, -const)
        return (None if lo is None else -lo, hi)

    def bounded(self):
        for u in self.unknowns:
            lo, hi = self.rangeof({u: F(1)})
            if lo is None or hi is None:
                return False
        return True


# ----------------------------------------------------------------------------
# worlds
# ----------------------------------------------------------------------------
class World:
    def __init__(self, d):
        self.raw = d
        try:
            self._load(d)
        except Invalid:
            raise
        except (KeyError, TypeError, AttributeError, ValueError) as e:
            raise Invalid(f"{d.get('id', '?')}: format error {e!r}")

    def _load(self, d):
        self.id = d['id']
        if d.get('experiment') != 'A':
            raise Invalid(f"{self.id}: experiment must be A")
        self.y = d['observable']
        self.qdims = {q: ndims(v, f"{self.id}.quantities.{q}") for q, v in d['quantities'].items()}
        if self.y not in self.qdims:
            raise Invalid(f"{self.id}: observable not among quantities")
        self.states = [q for q in d['quantities'] if q != self.y]
        self.consts = {c: (rat(v['value'], f"{self.id}.{c}"), ndims(v['dims'], f"{self.id}.{c}"))
                       for c, v in d['constants'].items()}
        for c, (v, _) in self.consts.items():
            if v == 0:
                raise Invalid(f"{self.id}: constant {c} is zero")
        self.observers = {o: rat(p, f"{self.id}.observer {o}") for o, p in d['observers'].items()}
        for o, p in self.observers.items():
            if p < 0:
                raise Invalid(f"{self.id}: negative precision")
        lhs, rhs = d['base_law'].split('=')
        if lhs.strip() != self.y:
            raise Invalid(f"{self.id}: base law lhs")
        self.f = parse(rhs)
        self.f_str = rhs.strip()
        self.vis = None
        if d.get('visible') is not None:
            v = d['visible']
            if v['id'] != 'V1':
                raise Invalid(f"{self.id}: visible id must be V1")
            self.vis = {'id': v['id'], 'object': v['object'], 'term': parse(v['term']), 'term_str': v['term']}
        self.ledger = []
        for i, c in enumerate(d['ledger']):
            if c['id'] != f"R{i + 1}":
                raise Invalid(f"{self.id}: candidate ids must be R1, R2, ... in order (got {c['id']})")
            self.ledger.append(load_cand(c, self.id))
        self.syms = []
        for s in d['symmetries']:
            mp = {}
            for q, t in s['map'].items():
                m = SYM_RE.match(t)
                if not m:
                    raise Invalid(f"{self.id}: bad symmetry map {t!r}")
                mp[q] = (rat(m.group(1)), m.group(2))
            self.syms.append({'name': s['name'], 'map': mp})
        self.old = [load_obs(o, self, True) for o in d['old_observations']]
        self.new = [load_obs(o, self, True) for o in d['new_observations']]
        self.poss = [load_obs(o, self, False) for o in d['possible_observations']]

    def env(self, state):
        e = dict(state)
        for c, (v, _) in self.consts.items():
            e[c] = v
        return e

    def denv(self):
        e = dict(self.qdims)
        for c, (_, dd) in self.consts.items():
            e[c] = dd
        return e

    def fval(self, s):
        return ev(self.f, self.env(s))

    def hv(self, s):
        return ev(self.vis['term'], self.env(s))

    def h(self, R, s):
        return ev(R['term'], self.env(s))

    def phi(self, R, s):
        if R['cov'] is None:
            return F(1)
        rho = ev(R['cov']['ratio'], self.env(s))
        cv = R['cov']
        if cv['type'] == 'dimmer':
            return ev(cv['g'], {'r': rho})
        if cv['on'] == '<':
            return F(1) if rho < cv['thr'] else F(0)
        return F(1) if rho > cv['thr'] else F(0)

    def rho(self, R, s):
        return ev(R['cov']['ratio'], self.env(s))

    def prec(self, ob):
        return self.observers[ob['observer']]

    def cand(self, rid):
        return next(R for R in self.ledger if R['id'] == rid)


def load_cand(c, wid):
    R = {'id': c['id'], 'object': c['object'], 'term': parse(c['term']), 'term_str': c['term'], 'raw': c}
    co = c['coefficient']
    if co == 'unknown':
        R['coef'] = None
    elif isinstance(co, dict) and set(co) == {'exact'}:
        R['coef'] = rat(co['exact'], f"{wid}.{c['id']}.exact")
    else:
        raise Invalid(f"{wid}: bad coefficient {co!r}")
    cv = c.get('coverage')
    if cv is None:
        R['cov'] = None
    else:
        fac = cv['factor']
        X = {'ratio': parse(cv['ratio']), 'ratio_str': cv['ratio'], 'type': fac['type']}
        if fac['type'] == 'dimmer':
            X['g'] = parse(fac['expr'])
            if not names(X['g']) <= {'r'}:
                raise Invalid(f"{wid}: dimmer uses names other than r")
        elif fac['type'] == 'switch':
            if fac['on'] not in ('<', '>'):
                raise Invalid(f"{wid}: bad switch")
            X['on'] = fac['on']
            X['thr'] = rat(fac['threshold'], f"{wid}.threshold")
            if X['thr'] <= 0:
                raise Invalid(f"{wid}: threshold must be positive")
        else:
            raise Invalid(f"{wid}: bad factor type")
        R['cov'] = X
    return R


def load_obs(o, W, with_value):
    st = o['state']
    if set(st) != set(W.states):
        raise Invalid(f"{W.id}: observation state must list every state quantity: {st}")
    ob = {'state': {q: rat(v, f"{W.id}.state") for q, v in st.items()}, 'observer': o['observer']}
    if ob['observer'] not in W.observers:
        raise Invalid(f"{W.id}: undeclared observer {ob['observer']}")
    if with_value:
        ob['value'] = rat(o['value'], f"{W.id}.value")
    elif 'value' in o:
        raise Invalid(f"{W.id}: possible observation with a value")
    return ob


# ----------------------------------------------------------------------------
# analysis
# ----------------------------------------------------------------------------
def type_impossible(W, term):
    dd = dm(term, W.denv())
    target = dadd(W.qdims[W.y], dd, -1)
    return not reachable(target, [d for (_, d) in W.consts.values()])


def sym_symbols(W):
    S = {}
    for nm in list(W.qdims) + list(W.consts):
        S[nm] = sympy.Symbol(nm)
    return S


def sym_apply(W, sym, S):
    sub = {}
    for q, (c, q2) in sym['map'].items():
        if q == W.y:
            continue
        sub[S[q]] = sympy.Rational(c.numerator, c.denominator) * S[q2]
    cy = sym['map'].get(W.y, (F(1), W.y))[0]
    return sub, sympy.Rational(cy.numerator, cy.denominator)


def sym_forbidden(W, R):
    S = sym_symbols(W)
    for sym in W.syms:
        sub, cy = sym_apply(W, sym, S)
        h = to_sym(R['term'], S)
        if not is_zero(h.xreplace(sub) - cy * h):
            return True
    return False


class Ctx:
    """options: no_scope (all factors 1), mu_fixed (value or None)"""

    def __init__(self, W, no_scope=False, mu_fixed=None):
        self.W = W
        self.no_scope = no_scope
        self.mu_fixed = mu_fixed

    def fac(self, R, s, mode):
        if self.no_scope or R['cov'] is None or mode == 'one':
            return F(1)
        return self.W.phi(R, s)

    def obs_list(self, extra_new=()):
        W = self.W
        return [('old', k, o) for k, o in enumerate(W.old)] + [('new', k, o) for k, o in enumerate(W.new)]

    def system(self, spec):
        """spec: list of (dom, k, ob, included) ; included: list of (R, factor, lam_fixed or None)"""
        W = self.W
        unknowns = []
        if W.vis is not None and self.mu_fixed is None:
            unknowns.append('mu')
        for (_, _, _, inc) in spec:
            for (R, _, lv) in inc:
                u = 'lam_' + R['id']
                if lv is None and u not in unknowns:
                    unknowns.append(u)
        rows = []
        for (dom, k, ob, inc) in spec:
            s = ob['state']
            K = W.fval(s)
            a = {}
            if W.vis is not None:
                if self.mu_fixed is None:
                    a['mu'] = W.hv(s)
                else:
                    K += self.mu_fixed * W.hv(s)
            for (R, fac, lv) in inc:
                t = W.h(R, s) * fac
                if lv is None:
                    a['lam_' + R['id']] = a.get('lam_' + R['id'], F(0)) + t
                else:
                    K += lv * t
            v, d = ob['value'], W.prec(ob)
            rows.append((dict(a), v + d - K, (dom, k, 'upper')))
            rows.append(({u: -c for u, c in a.items()}, -(v - d - K), (dom, k, 'lower')))
        return System(unknowns, rows)

    def Z(self):
        return self.system([(d, k, o, []) for (d, k, o) in self.obs_list()])

    def A(self, R):
        return self.system([(d, k, o, [(R, self.fac(R, o['state'], 'actual'), R['coef'])])
                            for (d, k, o) in self.obs_list()])

    def C(self, R):
        return self.system([(d, k, o, [(R, self.fac(R, o['state'], 'actual' if d == 'old' else 'one'), R['coef'])])
                            for (d, k, o) in self.obs_list()])

    def S(self, R):
        spec = []
        for (d, k, o) in self.obs_list():
            if d == 'old':
                spec.append((d, k, o, []))
            else:
                spec.append((d, k, o, [(R, F(1), None)]))
        return self.system(spec)

    def joint(self, cands):
        return self.system([(d, k, o, [(R, self.fac(R, o['state'], 'actual'), R['coef']) for R in cands])
                            for (d, k, o) in self.obs_list()])

    def pred(self, s, R):
        """(coef, const) of the predicted value at s for system Z (R None) or A_R (actual factor)"""
        W = self.W
        K = W.fval(s)
        a = {}
        if W.vis is not None:
            if self.mu_fixed is None:
                a['mu'] = W.hv(s)
            else:
                K += self.mu_fixed * W.hv(s)
        if R is not None:
            t = W.h(R, s) * self.fac(R, s, 'actual')
            if R['coef'] is None:
                a['lam_' + R['id']] = t
            else:
                K += R['coef'] * t
        return a, K


def m_old(W):
    """M_old: range of mu satisfying all old observations with every candidate at zero"""
    ctx = Ctx(W)
    X = ctx.system([('old', k, o, []) for k, o in enumerate(W.old)])
    if not X.feasible():
        return None, X
    return X.rangeof({'mu': F(1)}), X


def gap(I, J):
    return max(J[0] - I[1], I[0] - J[1])


def analyze(W, no_scope=False, mu_fixed=None, details=True):
    ctx = Ctx(W, no_scope, mu_fixed)
    out = {}
    Z = ctx.Z()
    zf = Z.feasible()
    out['deficit'] = not zf
    info = {}
    for R in W.ledger:
        ti = type_impossible(W, R['term'])
        sf = sym_forbidden(W, R) if W.syms else False
        A = ctx.A(R)
        af = A.feasible()
        ri = {'TYPE': ti, 'SYM': sf, 'A': af}
        if not af:
            C = ctx.C(R)
            S = ctx.S(R)
            ri['C'] = C.feasible()
            ri['S'] = S.feasible()
        info[R['id']] = ri
    out['info'] = info
    if zf:
        out['verdict'] = 'NO_DEFICIT'
        out['answer'] = ('NO_DEFICIT', None, None)
        if details:
            out['bounded'] = Z.bounded()
            out['ranges'] = {'BASE': [Z.rangeof(*ctx.pred(p['state'], None)) for p in W.poss]}
            out['intervals'] = {'BASE': {u: Z.rangeof({u: F(1)}) for u in Z.unknowns}}
        out['sufficient'] = []
        out['reasons'] = {}
        return out
    suff = [R['id'] for R in W.ledger if not info[R['id']]['TYPE'] and not info[R['id']]['SYM'] and info[R['id']]['A']]
    out['sufficient'] = suff
    reasons = {}
    for R in W.ledger:
        if R['id'] in suff:
            continue
        ri = info[R['id']]
        rs = []
        if ri['TYPE']:
            rs.append('TYPE')
        if ri['SYM']:
            rs.append('SYMMETRY')
        if not ri['A']:
            has_cov = R['cov'] is not None and not no_scope
            if has_cov and ri['C']:
                rs.append('SCOPE')
            if not ri['S']:
                rs.append('SHAPE')
            if ri['S'] and not ri['C']:
                rs.append('BOUND')
        reasons[R['id']] = rs
    out['reasons'] = reasons
    if len(suff) == 0:
        out['verdict'] = 'NEW'
        out['answer'] = ('NEW', None, None)
    elif len(suff) == 1:
        out['verdict'] = 'KNOWN'
        out['answer'] = ('KNOWN', suff[0], None)
    else:
        out['verdict'] = 'FORK'
        out['answer'] = ('FORK', None, tuple(sorted(suff, key=lambda r: int(r[1:]))))
    if details and suff and len(suff) <= 3:
        out['ranges'] = {}
        out['intervals'] = {}
        out['bounded'] = True
        for rid in suff:
            R = W.cand(rid)
            A = ctx.A(R)
            if not A.bounded():
                out['bounded'] = False
                continue
            out['ranges'][rid] = [A.rangeof(*ctx.pred(p['state'], R)) for p in W.poss]
            out['intervals'][rid] = {u: A.rangeof({u: F(1)}) for u in A.unknowns}
        if len(suff) >= 2 and out['bounded']:
            sep = {}
            for r1, r2 in itertools.combinations(suff, 2):
                ok = []
                for i, p in enumerate(W.poss):
                    if gap(out['ranges'][r1][i], out['ranges'][r2][i]) > 2 * W.prec(p):
                        ok.append(i)
                sep[(r1, r2)] = ok
            out['separating'] = sep
    if out['verdict'] == 'NEW' and details:
        elig = [R for R in W.ledger if not info[R['id']]['TYPE'] and not info[R['id']]['SYM']]
        # W8 is checked under both readings (see key/generator_notes.md, issue 1):
        # (L) one joint system, exact coefficients fixed; (C) no subset explains, i.e. every
        # exact-coefficient candidate may also be absent. Unknown coefficients are free in both.
        exact = [R for R in elig if R['coef'] is not None]
        unk = [R for R in elig if R['coef'] is None]
        lit = ctx.joint(elig).feasible() if elig else False
        sub = any(ctx.joint(unk + list(c)).feasible() if (unk or c) else False
                  for k in range(len(exact) + 1) for c in itertools.combinations(exact, k))
        out['joint_feasible'] = lit or sub
        out['joint_feasible_readings'] = {'L': lit, 'C': sub}
    return out


def answer_str(a):
    v, r, b = a
    if v == 'KNOWN':
        return f"KNOWN({r})"
    if v == 'FORK':
        return f"FORK({','.join(b)})"
    return v


# ----------------------------------------------------------------------------
# validity W1-W9 (+W10 vs format example)
# ----------------------------------------------------------------------------
FORMAT_EXAMPLE_TERMS = ("ku*bb", ("ku*bb", "ku*bb**2", "ku*bb**3"))


def check_name(nm, where, errs):
    if not isinstance(nm, str) or not NAME_RE.match(nm):
        errs.append(f"{where}: bad name {nm!r}")
        return
    if nm in RESERVED:
        errs.append(f"{where}: reserved name {nm!r}")
    try:
        if not isinstance(sympy.sympify(nm), sympy.Symbol):
            errs.append(f"{where}: name {nm!r} is not a plain sympy symbol")
    except Exception:
        errs.append(f"{where}: name {nm!r} not sympifiable")


def all_rationals_ok(d, errs, where):
    pass  # every rational is parsed through rat(), which enforces the 10^9 budget


def world_errors(W):
    errs = []
    d = W.raw
    wid = W.id
    # W1 budgets
    if not 1 <= len(W.states) <= 4:
        errs.append("W1: 1-4 state quantities")
    if not 0 <= len(W.consts) <= 4:
        errs.append("W1: 0-4 constants")
    if not 1 <= len(W.observers) <= 3:
        errs.append("W1: 1-3 observers")
    if not 2 <= len(W.ledger) <= 5:
        errs.append("W1: 2-5 candidates")
    if not 0 <= len(W.syms) <= 2:
        errs.append("W1: 0-2 symmetries")
    if not 1 <= len(W.old) <= 6:
        errs.append("W1: 1-6 old observations")
    if not 1 <= len(W.new) <= 4:
        errs.append("W1: 1-4 new observations")
    if not 2 <= len(W.poss) <= 6:
        errs.append("W1: 2-6 possible observations")
    allnames = []
    allnames += list(W.qdims)
    allnames += list(W.consts)
    allnames += list(W.observers)
    objs = {R['object'] for R in W.ledger}
    if W.vis:
        objs.add(W.vis['object'])
    allnames += sorted(objs)
    allnames += [s['name'] for s in W.syms]
    for nm in allnames:
        check_name(nm, wid, errs)
    if len(allnames) != len(set(allnames)):
        errs.append(f"W1: names not distinct: {allnames}")
    declared = set(W.qdims) | set(W.consts)
    stq = set(W.states) | set(W.consts)
    exprs = [('base', W.f)] + ([('vis', W.vis['term'])] if W.vis else [])
    for R in W.ledger:
        exprs.append((R['id'], R['term']))
        if R['cov']:
            exprs.append((R['id'] + '.ratio', R['cov']['ratio']))
    for nm, e in exprs:
        if not names(e) <= stq:
            errs.append(f"W1: {nm} uses undeclared or non-state names {names(e) - stq}")
    # W2
    denv = W.denv()
    try:
        if dm(W.f, denv) != W.qdims[W.y]:
            errs.append("W2: dim(f) != dim(y)")
        for R in W.ledger:
            dm(R['term'], denv)
            if R['cov'] and dm(R['cov']['ratio'], denv) != {}:
                errs.append(f"W2: {R['id']} ratio not dimensionless")
        if W.vis:
            dm(W.vis['term'], denv)
    except Invalid as e:
        errs.append(f"W2: {e}")
    allstates = [o['state'] for o in W.old + W.new + W.poss]
    for s in allstates:
        try:
            W.fval(s)
            if W.vis:
                W.hv(s)
            for R in W.ledger:
                W.h(R, s)
                if R['cov']:
                    rho = W.rho(R, s)
                    if R['cov']['type'] == 'dimmer':
                        g = W.phi(R, s)
                        if not (0 <= g <= 1):
                            errs.append(f"W2: {R['id']} dimmer {g} outside [0,1] at {s}")
                    elif rho == R['cov']['thr']:
                        errs.append(f"W2: {R['id']} state on switch threshold")
        except ZeroDivisionError:
            errs.append(f"W2: division by zero at {s}")
    if errs:
        return errs
    # W3
    if W.vis:
        if type_impossible(W, W.vis['term']):
            errs.append("W3: visible relation TYPE-impossible")
        rng, _ = m_old(W)
        if rng is None:
            errs.append("W3: M_old empty")
        else:
            lo, hi = rng
            if lo is None or hi is None:
                errs.append("W3: M_old unbounded")
            elif lo <= 0 <= hi:
                errs.append("W3: M_old contains 0")
    # W4
    ctx = Ctx(W)
    if not ctx.system([('old', k, o, []) for k, o in enumerate(W.old)]).feasible():
        errs.append("W4: old observations fail with every candidate at zero")
    rd = W.old + W.new
    for o1, o2 in itertools.combinations(rd, 2):
        if o1['state'] == o2['state']:
            d1, d2 = W.prec(o1), W.prec(o2)
            if o1['value'] + d1 < o2['value'] - d2 or o2['value'] + d2 < o1['value'] - d1:
                errs.append("W4: readings at identical state do not overlap")
    # W5
    S = sym_symbols(W)
    for sym in W.syms:
        for q, (c, q2) in sym['map'].items():
            if c == 0:
                errs.append("W5: zero multiple")
            if q == W.y and q2 != W.y:
                errs.append("W5: observable must map to itself")
            if q != W.y and (q not in W.states or q2 not in W.states):
                errs.append("W5: state quantity must map to a state quantity")
            if q != W.y and q in W.qdims and q2 in W.qdims and W.qdims[q] != W.qdims[q2]:
                errs.append("W5(note): map between quantities of different dims")
        sub, cy = sym_apply(W, sym, S)
        fx = to_sym(W.f, S)
        if not is_zero(fx.xreplace(sub) - cy * fx):
            errs.append(f"W5: {sym['name']} does not preserve f")
        if W.vis:
            hx = to_sym(W.vis['term'], S)
            if not is_zero(hx.xreplace(sub) - cy * hx):
                errs.append(f"W5: {sym['name']} does not preserve h_V")
        for R in W.ledger:
            if R['cov']:
                rx = to_sym(R['cov']['ratio'], S)
                if not is_zero(rx.xreplace(sub) - rx):
                    errs.append(f"W5: {sym['name']} changes ratio of {R['id']}")
    if errs:
        return errs
    an = analyze(W)
    # W6
    ans = an['answer']
    inans = set()
    if ans[0] == 'KNOWN':
        inans = {ans[1]}
    elif ans[0] == 'FORK':
        inans = set(ans[2])
    if not any(not an['info'][R['id']]['TYPE'] and R['id'] not in inans for R in W.ledger):
        errs.append("W6: no distractor with the right dimensions")
    # W7
    if len(an['sufficient']) > 3:
        errs.append("W7: more than 3 sufficient candidates")
    else:
        if not an.get('bounded', True):
            errs.append("W7: unbounded feasible set")
        if an['verdict'] == 'FORK':
            for pair, ok in an['separating'].items():
                if not ok:
                    errs.append(f"W7: pair {pair} not decisively separable")
    # extra safety: NO_DEFICIT worlds -> at most 3 eligible candidates with feasible A_R
    if an['verdict'] == 'NO_DEFICIT':
        nfe = [R['id'] for R in W.ledger if not an['info'][R['id']]['TYPE'] and not an['info'][R['id']]['SYM']
               and an['info'][R['id']]['A']]
        if len(nfe) > 3:
            errs.append(f"W7(note, safety only): NO_DEFICIT world with {len(nfe)} feasible eligible candidates")
    # W8
    if an['verdict'] == 'NEW' and an.get('joint_feasible'):
        errs.append("W8: joint system feasible in a NEW world")
    # W10 (format example only)
    if W.f_str.replace(' ', '') == FORMAT_EXAMPLE_TERMS[0] and \
            tuple(R['term_str'].replace(' ', '') for R in W.ledger) == FORMAT_EXAMPLE_TERMS[1]:
        errs.append("W10: reproduces the format example")
    return errs


def group_signature(d):
    keys = ['quantities', 'constants', 'base_law', 'visible', 'ledger', 'symmetries', 'observers', 'old_observations']
    return json.dumps({k: d[k] for k in keys}, sort_keys=True)


def cross_errors(raws):
    """W9 and the 'different new observations' rule"""
    errs = []
    consts, obsv, groups, qd = {}, {}, {}, {}
    for d in raws:
        for c, v in d['constants'].items():
            key = (rat(v['value']), json.dumps(ndims(v['dims']), sort_keys=True, default=str))
            if c in consts and consts[c][0] != key:
                errs.append(f"W9: constant {c} differs between {consts[c][1]} and {d['id']}")
            consts.setdefault(c, (key, d['id']))
        for o, p in d['observers'].items():
            if o in obsv and obsv[o][0] != rat(p):
                errs.append(f"W9: observer {o} differs between {obsv[o][1]} and {d['id']}")
            obsv.setdefault(o, (rat(p), d['id']))
        groups.setdefault(d['observable'], []).append(d)
        for q, v in d['quantities'].items():
            key = json.dumps(ndims(v), sort_keys=True, default=str)
            if q in qd and qd[q][0] != key:
                errs.append(f"W9(note): quantity {q} has different dims in {qd[q][1]} and {d['id']}")
            qd.setdefault(q, (key, d['id']))
    for y, ds in groups.items():
        sigs = {group_signature(d) for d in ds}
        if len(sigs) > 1:
            errs.append(f"W9: worlds of observable {y} differ outside new/possible observations: {[d['id'] for d in ds]}")
        news = [json.dumps(d['new_observations'], sort_keys=True) for d in ds]
        if len(set(news)) != len(news):
            errs.append(f"Sec6: worlds of observable {y} share new observations")
    return errs


# ----------------------------------------------------------------------------
# Part A summary per world
# ----------------------------------------------------------------------------
def world_summary(W):
    an = analyze(W)
    s = {'answer': an['answer'], 'reasons': an['reasons'], 'an': an}
    ns = analyze(W, no_scope=True, details=False)
    s['no_scope'] = ns['answer'] if len(ns['sufficient']) <= 3 or not ns['deficit'] else \
        ('FORK', None, tuple(sorted(ns['sufficient'], key=lambda r: int(r[1:]))))
    s['scope_sensitive'] = s['no_scope'] != an['answer']
    s['mid_mu'] = None
    s['mu_matters'] = False
    if W.vis:
        (lo, hi), _ = m_old(W)
        mid = (lo + hi) / 2
        mm = analyze(W, mu_fixed=mid, details=False)
        s['mid_mu'] = mm['answer'] if len(mm['sufficient']) <= 3 or not mm['deficit'] else \
            ('FORK', None, tuple(sorted(mm['sufficient'], key=lambda r: int(r[1:]))))
        s['mu_matters'] = s['mid_mu'] != an['answer']
        s['M_old'] = (lo, hi)
    # nebulium type
    s['nebulium'] = None
    if an['verdict'] == 'KNOWN':
        R = W.cand(an['answer'][1])
        if R['cov'] is not None and s['scope_sensitive']:
            s['nebulium'] = R['cov']['type']
    # DIMS_ONLY
    first = next((R['id'] for R in W.ledger if not an['info'][R['id']]['TYPE']), None)
    if not an['deficit']:
        s['dims_only'] = ('NO_DEFICIT', None, None)
    else:
        s['dims_only'] = ('KNOWN', first, None) if first else ('NEW', None, None)
    s['always_new'] = ('NO_DEFICIT', None, None) if not an['deficit'] else ('NEW', None, None)
    # planet-X trap
    s['planet_x'] = an['verdict'] == 'NO_DEFICIT' and any(
        not an['info'][R['id']]['TYPE'] and not an['info'][R['id']]['SYM'] and an['info'][R['id']]['A'] for R in W.ledger)
    return s


# ----------------------------------------------------------------------------
# Part B
# ----------------------------------------------------------------------------
def used_constants(W, verdict):
    u = names(W.f)
    if W.vis:
        u |= names(W.vis['term'])
    if verdict != 'NO_DEFICIT':
        for R in W.ledger:
            u |= names(R['term'])
            if R['cov']:
                u |= names(R['cov']['ratio'])
    return u & set(W.consts)


def used_observers(W, verdict):
    u = {o['observer'] for o in W.old + W.new}
    if verdict == 'FORK':
        u |= {o['observer'] for o in W.poss}
    return u


def apply_item(raws, item):
    """return (new raw worlds dict id->raw, set of changed world ids)"""
    new = {d['id']: copy.deepcopy(d) for d in raws}
    changed = set()
    t = item['type']
    if t == 'observation':
        d = new[item['world']]
        d['new_observations'].append({'state': item['state'], 'value': item['value'], 'observer': item['observer']})
        changed.add(d['id'])
    elif t == 'relation':
        for d in new.values():
            if d['observable'] == item['observable']:
                d['ledger'].append(copy.deepcopy(item['relation']))
                changed.add(d['id'])
    elif t == 'root':
        if 'constant' in item:
            for d in new.values():
                if item['constant'] in d['constants']:
                    d['constants'][item['constant']]['value'] = item['new_value']
                    changed.add(d['id'])
        else:
            for d in new.values():
                if item['observer'] in d['observers']:
                    d['observers'][item['observer']] = item['new_precision']
                    changed.add(d['id'])
    return new, changed


def item_reference(raws, worlds, summaries, item):
    """compute the reference list and finals, and validity errors"""
    errs = []
    t = item['type']
    reop = []
    if t == 'observation':
        W = worlds[item['world']]
        st = {q: rat(v) for q, v in item['state'].items()}
        idx = [i for i, p in enumerate(W.poss) if p['state'] == st and p['observer'] == item['observer']]
        if not idx:
            errs.append("item: state/observer is not a possible observation of the world")
            return None, None, errs
        i = idx[0]
        v = rat(item['value'])
        dd = W.observers[item['observer']]
        I = (v - dd, v + dd)
        for o in W.old + W.new:
            if o['state'] == st:
                d2 = W.prec(o)
                if o['value'] + d2 < I[0] or I[1] < o['value'] - d2:
                    errs.append("item: conflicts with an existing reading")
        an = summaries[W.id]['an']
        verdict = an['verdict']
        if verdict == 'NEW':
            pass
        elif verdict in ('KNOWN', 'NO_DEFICIT'):
            key = 'BASE' if verdict == 'NO_DEFICIT' else an['answer'][1]
            P = an['ranges'][key][i]
            if gap(I, P) > 0:
                reop = [W.id]
        else:
            for rid in an['answer'][2]:
                P = an['ranges'][rid][i]
                if gap(I, P) > 0:
                    reop = [W.id]
    elif t == 'relation':
        y = item['observable']
        ws = [W for W in worlds.values() if W.y == y]
        if not ws and 'observable_dims' not in item:
            errs.append("item: unused observable without observable_dims")
        rid = item['relation']['id']
        for W in ws:
            if any(R['id'] == rid for R in W.ledger):
                errs.append("item: relation id not new")
        objs = {R['object'] for W in worlds.values() for R in W.ledger}
        if item['relation']['object'] not in objs:
            errs.append("item: relation object does not appear in any ledger")
        reop = sorted(W.id for W in ws if summaries[W.id]['an']['verdict'] != 'NO_DEFICIT')
    elif t == 'root':
        if 'constant' in item:
            c = item['constant']
            ws = [W for W in worlds.values() if c in W.consts]
            if not ws:
                errs.append("item: constant appears in no world")
            reop = sorted(W.id for W in ws if c in used_constants(W, summaries[W.id]['an']['verdict']))
        else:
            o = item['observer']
            ws = [W for W in worlds.values() if o in W.observers]
            if not ws:
                errs.append("item: observer appears in no world")
            if rat(item['new_precision']) < 0:
                errs.append("item: negative precision")
            reop = sorted(W.id for W in ws if o in used_observers(W, summaries[W.id]['an']['verdict']))
    else:
        errs.append("item: bad type")
        return None, None, errs
    new_raws, changed = apply_item(raws, item)
    new_worlds = {}
    for wid in changed:
        try:
            new_worlds[wid] = World(new_raws[wid])
        except Invalid as e:
            errs.append(f"after item, {wid}: {e}")
    if errs:
        return reop, None, errs
    for wid in sorted(changed):
        we = [x for x in world_errors(new_worlds[wid]) if 'note' not in x]
        if we:
            errs.append(f"after item, {wid} invalid: {we}")
    errs += [f"after item: {e}" for e in cross_errors(list(new_raws.values())) if 'note' not in e]
    finals = {}
    new_answers = {}
    for wid in sorted(changed):
        a = analyze(new_worlds[wid], details=False)
        new_answers[wid] = a['answer'] if len(a['sufficient']) <= 3 else ('TOO_MANY', None, None)
    for wid, a in new_answers.items():
        old = summaries[wid]['answer']
        if wid not in reop and a != old:
            errs.append(f"item: file {wid} outside the reference list changes {answer_str(old)} -> {answer_str(a)}")
    for wid in reop:
        finals[wid] = new_answers.get(wid, summaries[wid]['answer'])
    return reop, finals, errs


def item_category_ok(item, cat, reop, finals, summaries, worlds):
    old = {wid: summaries[wid]['answer'] for wid in summaries}
    changed = [w for w in reop if finals[w] != old[w]]
    t = item['type']
    if cat == 'obs_flip':
        return t == 'observation' and reop == [item['world']] and old[item['world']][0] in ('KNOWN', 'NO_DEFICIT')
    if cat == 'obs_inside':
        return t == 'observation' and reop == []
    if cat == 'obs_fork':
        return t == 'observation' and reop == [item['world']] and old[item['world']][0] == 'FORK'
    if cat == 'rel_new_known':
        if t != 'relation':
            return False
        rid = item['relation']['id']
        return any(old[w][0] == 'NEW' and finals[w] == ('KNOWN', rid, None) for w in reop)
    if cat == 'rel_known_fork':
        if t != 'relation':
            return False
        rid = item['relation']['id']
        return any(old[w][0] == 'KNOWN' and finals[w][0] == 'FORK' and rid in finals[w][2] for w in reop)
    if cat == 'rel_unchanged':
        return t == 'relation' and reop and not changed
    if cat == 'rel_none':
        return t == 'relation' and not reop
    if cat == 'root_vanish':
        return t == 'root' and any(old[w][0] != 'NO_DEFICIT' and finals[w][0] == 'NO_DEFICIT' for w in reop)
    if cat == 'root_revive':
        if t != 'root':
            return False
        for w in reop:
            os_ = set()
            if old[w][0] == 'KNOWN':
                os_ = {old[w][1]}
            elif old[w][0] == 'FORK':
                os_ = set(old[w][2])
            ns = set()
            if finals[w][0] == 'KNOWN':
                ns = {finals[w][1]}
            elif finals[w][0] == 'FORK':
                ns = set(finals[w][2])
            if old[w][0] != 'NO_DEFICIT' and ns - os_:
                return True
        return False
    if cat == 'root_unchanged':
        return t == 'root' and reop and not changed
    if cat == 'root_none':
        return t == 'root' and not reop
    return False


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------
def load_all(wdir, ddir):
    raws = []
    for i in range(1, 28):
        with open(os.path.join(wdir, f"W-{i:02d}.json"), encoding='utf-8') as fh:
            raws.append(json.load(fh))
    items = []
    for i in range(1, 19):
        with open(os.path.join(ddir, f"D-{i:02d}.json"), encoding='utf-8') as fh:
            items.append(json.load(fh))
    return raws, items


def fmt_rng(r):
    return f"[{fs(r[0])}, {fs(r[1])}]"


def main(argv):
    wdir, ddir, keyp = argv[1], argv[2], argv[3]
    raws, items = load_all(wdir, ddir)
    with open(keyp, encoding='utf-8') as fh:
        key = json.load(fh)
    problems = []
    lines = []
    P = lines.append
    worlds, summaries = {}, {}
    P("=" * 78)
    P("PART A")
    P("=" * 78)
    for d in raws:
        try:
            W = World(d)
        except Invalid as e:
            problems.append(f"{d.get('id')}: {e}")
            continue
        worlds[W.id] = W
        e = world_errors(W)
        hard = [x for x in e if 'note' not in x]
        if hard:
            problems += [f"{W.id}: {x}" for x in hard]
        s = world_summary(W)
        summaries[W.id] = s
        an = s['an']
        P(f"{W.id}  observable={W.y}  answer={answer_str(s['answer'])}")
        P(f"   NO_SCOPE={answer_str(s['no_scope'])}  scope_sensitive={s['scope_sensitive']}  "
          f"DIMS_ONLY={answer_str(s['dims_only'])}" + (f"  nebulium={s['nebulium']}" if s['nebulium'] else ''))
        if W.vis:
            P(f"   M_old={fmt_rng(s['M_old'])}  mid-mu answer={answer_str(s['mid_mu'])}  mu_matters={s['mu_matters']}")
        for rid, rs in an['reasons'].items():
            P(f"   {rid}: {rs}")
        if an['verdict'] in ('KNOWN', 'FORK', 'NO_DEFICIT') and 'intervals' in an:
            for k, iv in an['intervals'].items():
                P(f"   {k} intervals: " + ", ".join(f"{u}={fmt_rng(r)}" for u, r in iv.items()))
                P(f"   {k} ranges: " + " ".join(fmt_rng(r) for r in an['ranges'][k]))
        if an['verdict'] == 'FORK':
            P(f"   separating possible observations: " + "; ".join(f"{a}-{b}:{v}" for (a, b), v in an['separating'].items()))
        if an['verdict'] == 'NEW':
            P(f"   joint system feasible (W8, readings L and C): {an['joint_feasible_readings']}")
        if s['planet_x']:
            P("   planet-X trap: yes")
        for x in e:
            P(f"   note: {x}")
    problems += cross_errors(raws)
    # key A
    keyA = {k['id']: k for k in key['A']}
    for wid, s in summaries.items():
        k = keyA.get(wid)
        if k is None:
            problems.append(f"key: missing entry {wid}")
            continue
        ka = (k['verdict'], k.get('relation'), tuple(k['branches']) if k.get('branches') else None)
        if ka != s['answer']:
            problems.append(f"key {wid}: {ka} != reference {s['answer']}")
        if k.get('reasons') is not None:
            ref = {r: sorted(v) for r, v in s['an']['reasons'].items()}
            got = {r: sorted(v) for r, v in k['reasons'].items()}
            if ref != got:
                problems.append(f"key {wid}: reasons {got} != reference {ref}")
        ht = k.get('hidden_truth')
        if ht:
            W = worlds[wid]
            for ob in W.old + W.new:
                s_ = ob['state']
                val = W.fval(s_)
                if W.vis and ht.get('visible_coefficient') is not None:
                    val += rat(ht['visible_coefficient']) * W.hv(s_)
                for term in ht['terms']:
                    c = rat(term['coefficient'])
                    if 'candidate' in term:
                        R = W.cand(term['candidate'])
                        val += c * W.h(R, s_) * W.phi(R, s_)
                    else:
                        val += c * ev(parse(term['expr']), W.env(s_))
                if abs(val - ob['value']) > W.prec(ob):
                    problems.append(f"key {wid}: hidden truth not within precision at {s_}")
    # composition A
    cnt = {}
    for s in summaries.values():
        cnt[s['answer'][0]] = cnt.get(s['answer'][0], 0) + 1
    P("")
    P(f"Composition: {cnt}")
    if cnt != {'KNOWN': 9, 'NEW': 9, 'FORK': 6, 'NO_DEFICIT': 3}:
        problems.append(f"Sec6: verdict counts {cnt}")
    ss = [w for w, s in summaries.items() if s['scope_sensitive']]
    neb = [w for w, s in summaries.items() if s['nebulium']]
    nebd = [w for w in neb if summaries[w]['nebulium'] == 'dimmer']
    nebs = [w for w in neb if summaries[w]['nebulium'] == 'switch']
    ssnew = [w for w in ss if summaries[w]['answer'][0] == 'NEW']
    ssfork = [w for w in ss if summaries[w]['answer'][0] == 'FORK']
    P(f"scope-sensitive: {len(ss)} {ss}")
    P(f"nebulium KNOWN: dimmer {nebd}, switch {nebs}; scope-sensitive NEW {ssnew}; FORK {ssfork}")
    if len(ss) < 8 or len(nebd) < 3 or len(nebs) < 2 or len(neb) < 5 or len(ssnew) < 2 or len(ssfork) < 1:
        problems.append("Sec6: scope-sensitivity composition fails")
    sole = {r: [] for r in REASONS}
    for wid, s in summaries.items():
        if s['answer'][0] == 'NEW':
            for rid, rs in s['an']['reasons'].items():
                if len(rs) == 1:
                    sole[rs[0]].append(f"{wid}.{rid}")
    P(f"sole reasons in NEW worlds: {sole}")
    for r in REASONS:
        if not sole[r]:
            problems.append(f"Sec6: no sole {r}")
    mm = [w for w, s in summaries.items() if s['mu_matters']]
    P(f"visible relation matters: {mm}")
    if len(mm) < 3:
        problems.append("Sec6: fewer than 3 worlds where the visible relation matters")
    f3 = [w for w, s in summaries.items() if s['answer'][0] == 'FORK' and len(s['answer'][2]) == 3]
    P(f"three-branch forks: {f3}")
    if not f3:
        problems.append("Sec6: no three-branch fork")
    px = [w for w, s in summaries.items() if s['planet_x']]
    P(f"planet-X traps: {px}")
    if not px:
        problems.append("Sec6: no planet-X trap")
    groups = {}
    for W in worlds.values():
        groups.setdefault(W.y, []).append(W.id)
    P(f"observable groups: {groups}")
    if not any(len(v) >= 3 and any(summaries[w]['answer'][0] == 'NO_DEFICIT' for w in v) for v in groups.values()):
        problems.append("Sec6: no observable shared by 3 worlds incl. a NO_DEFICIT")
    # baselines
    for bname in ('no_scope', 'dims_only', 'always_new'):
        acc = sum(1 for s in summaries.values() if s[bname] == s['answer'])
        P(f"baseline {bname}: correct on {acc}/27")
    pos = {}
    for wid, s in summaries.items():
        if s['answer'][0] == 'KNOWN':
            pos[wid] = s['answer'][1]
    P(f"KNOWN answer positions: {pos}")
    # Part B
    P("")
    P("=" * 78)
    P("PART B")
    P("=" * 78)
    keyB = {k['id']: k for k in key['B']}
    cats = {}
    multi_rel = multi_root = rel_nd = 0
    for item in items:
        iid = item['id']
        k = keyB.get(iid)
        if k is None:
            problems.append(f"key: missing {iid}")
            continue
        reop, finals, errs = item_reference(raws, worlds, summaries, item)
        if errs:
            problems += [f"{iid}: {x}" for x in errs]
            P(f"{iid} ERRORS {errs}")
            continue
        cat = k['type']
        cats[cat] = cats.get(cat, 0) + 1
        if not item_category_ok(item, cat, reop, finals, summaries, worlds):
            problems.append(f"{iid}: category {cat} does not match the outcome")
        P(f"{iid} [{cat}] type={item['type']} reopened={reop} finals=" +
          ", ".join(f"{w}:{answer_str(summaries[w]['answer'])}->{answer_str(a)}" for w, a in finals.items()))
        if sorted(k['reopened']) != reop:
            problems.append(f"key {iid}: reopened {k['reopened']} != reference {reop}")
        kf = {w: (v['verdict'], v.get('relation'), tuple(v['branches']) if v.get('branches') else None)
              for w, v in k['final'].items()}
        if kf != finals:
            problems.append(f"key {iid}: finals {kf} != reference {finals}")
        if item['type'] == 'relation' and len(reop) >= 2:
            multi_rel += 1
        if item['type'] == 'root' and len(reop) >= 2:
            multi_root += 1
        if item['type'] == 'relation':
            if any(summaries[W.id]['answer'][0] == 'NO_DEFICIT' for W in worlds.values() if W.y == item['observable']):
                rel_nd += 1
    want = {'obs_flip': 2, 'obs_inside': 2, 'obs_fork': 2, 'rel_new_known': 2, 'rel_known_fork': 2,
            'rel_unchanged': 2, 'rel_none': 2, 'root_vanish': 1, 'root_revive': 1, 'root_unchanged': 1,
            'root_none': 1}
    P(f"categories: {cats}")
    if cats != want:
        problems.append(f"Sec10.1: categories {cats}")
    P(f"relation items with >=2 files: {multi_rel}; root items with >=2 files: {multi_root}; "
      f"relation items on an observable with a NO_DEFICIT file: {rel_nd}")
    if multi_rel < 2 or multi_root < 1 or rel_nd < 1:
        problems.append("Sec10.1: extra requirements fail")
    flips = [i for i in items if keyB[i['id']]['type'] == 'obs_flip']
    if not any(summaries[i['world']]['answer'][0] == 'KNOWN' for i in flips):
        problems.append("Sec10.1: no obs_flip on a KNOWN file")
    ins = [i for i in items if keyB[i['id']]['type'] == 'obs_inside']
    if not any(summaries[i['world']]['answer'][0] == 'KNOWN' for i in ins):
        problems.append("Sec10.1: no obs_inside on a KNOWN file")
    P("")
    if problems:
        P(f"PROBLEMS ({len(problems)}):")
        for p in problems:
            P("  - " + p)
        P("RESULT: KEY NOT CONSISTENT")
    else:
        P("RESULT: KEY CONSISTENT (all checks of this script pass)")
    print("\n".join(lines))
    return 0 if not problems else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
