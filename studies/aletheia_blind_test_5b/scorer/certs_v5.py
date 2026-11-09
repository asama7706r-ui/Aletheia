#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Certificate checkers of blind test 5 (protocol_v5.md, Section 4). Exact arithmetic only.

Every judgement of the test rests on these checks: a witness (4.3), a refutation tree (4.4),
a known-kind solution (4.5), the congruence-closure contradiction of an IMPOSSIBLE world (4.6),
and the mirror translation of the merge step (2.7). The scorer and the validator use this module;
the procedure may import it to check its own certificates before writing them (it never decides
anything here). Python 3.12, standard library plus the v0.5 reader.
"""
import json
import os
import sys
from fractions import Fraction as Fr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lang"))
import reader_v0 as R  # noqa: E402

# ---------------------------------------------------------------- bounds (PENDING: fixed before sealing)
BOUNDS = {"P2": 4, "P3": 16, "S": 4}
LIMIT_TERMS = 20000          # terms in one refutation tree, all nodes together
LIMIT_TABLE = 4096           # nonzero structure constants in one witness
MAX_BISECT = 60              # bisections of theta's interval when certifying "not zero"

# ---------------------------------------------------------------- the judged units (Section 2.3)
COPIES = ["q5[onn]", "q5[non]", "q5[nno]", "q5[oon]", "q5[ono]", "q5[noo]", "q6[on]"]
UNITS = {"k01": ["q5", "q6", "q12", "q13", "q14"],
         "k02": ["q5", "q6", "q12", "q13"] + COPIES}
Q5_FAMILY = {"q5"} | {c for c in COPIES if c.startswith("q5[")}
MIRROR = {"q5[onn]": "q5[nno]", "q5[nno]": "q5[onn]", "q5[oon]": "q5[noo]", "q5[noo]": "q5[oon]"}
WORKSHOP = ["q3", "q4", "q7", "q8", "q9", "q10", "q11"]
PROTECTED = ["q1", "q2"]


def judged_units(origin, frames):
    """U for a build: the units a candidate may drop (Section 2.3)."""
    u = list(UNITS[origin])
    if "f03" in frames:
        u = [x for x in u if x not in Q5_FAMILY]
    return u


def mirror_set(drop):
    return sorted(MIRROR.get(u, u) for u in drop)


class CertError(Exception):
    pass


def need(cond, msg):
    if not cond:
        raise CertError(msg)


# ---------------------------------------------------------------- numbers: fractions and Q(theta) (4.1)
def frac(s):
    """A fraction written as a string 'p' or 'p/q' in lowest terms (an int is accepted too)."""
    if isinstance(s, bool):
        raise CertError(f"not a fraction: {s!r}")
    if isinstance(s, int):
        return Fr(s)
    need(isinstance(s, str) and R.FRAC_RE.match(s), f"not a fraction string: {s!r}")
    if "/" in s:
        p, q = s.split("/")
        f = Fr(int(p), int(q))
        need(f.denominator != 1 and (f.numerator, f.denominator) == (int(p), int(q)),
             f"fraction not in lowest terms (or denominator 1): {s}")
        return f
    return Fr(int(s))


def fstr(f):
    f = Fr(f)
    return str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"


def p_trim(p):
    p = list(p)
    while p and p[-1] == 0:
        p.pop()
    return p


def p_eval(p, x):
    acc = Fr(0)
    for c in reversed(p):
        acc = acc * x + c
    return acc


def p_rem(a, b):
    a, b = p_trim(a), p_trim(b)
    need(b, "division by the zero polynomial")
    while len(a) >= len(b) and a:
        q = a[-1] / b[-1]
        s = len(a) - len(b)
        for i, c in enumerate(b):
            a[s + i] -= q * c
        a = p_trim(a)
    return a


def p_deriv(p):
    return p_trim([i * c for i, c in enumerate(p)][1:])


def sturm_chain(p):
    chain = [p_trim(p), p_deriv(p)]
    while chain[-1] and len(chain[-1]) > 1:
        r = p_rem(chain[-2], chain[-1])
        if not r:
            break
        chain.append([-c for c in r])
    return [c for c in chain if c]


def sign_changes(chain, x):
    signs = [s for s in (p_eval(c, x) for c in chain) if s != 0]
    return sum(1 for a, b in zip(signs, signs[1:]) if (a > 0) != (b > 0))


def roots_in(chain, lo, hi):
    """Number of distinct real roots in (lo, hi] (Sturm)."""
    return sign_changes(chain, lo) - sign_changes(chain, hi)


class Field:
    """Q, or Q(theta) for one real algebraic theta given by a polynomial and an isolating interval."""

    def __init__(self, theta=None):
        self.theta = theta
        if theta is None:
            self.d, self.p = 1, None
            return
        need(isinstance(theta, dict) and set(theta) == {"poly", "lo", "hi"}, "theta must be {poly, lo, hi}")
        poly = [frac(a) for a in theta["poly"]]
        need(len(poly) >= 3 and poly[-1] != 0, "theta's polynomial must have degree >= 2 and a nonzero leading coefficient")
        lo, hi = frac(theta["lo"]), frac(theta["hi"])
        need(lo < hi, "theta's interval must have lo < hi")
        self.p = [c / poly[-1] for c in poly]          # monic
        self.d = len(self.p) - 1
        self.chain = sturm_chain(self.p)
        need(roots_in(self.chain, lo, hi) == 1, "theta's interval must hold exactly one real root (Sturm count)")
        self.lo, self.hi = lo, hi

    # elements are tuples of d Fractions: the coefficients of 1, theta, ..., theta^(d-1)
    def el(self, x):
        if isinstance(x, list):
            need(len(x) == self.d, f"an element of Q(theta) needs {self.d} coefficients")
            return tuple(frac(c) for c in x)
        return self.c(frac(x))

    def c(self, q):
        return (Fr(q),) + (Fr(0),) * (self.d - 1)

    def zero(self):
        return self.c(0)

    def one(self):
        return self.c(1)

    @staticmethod
    def add(a, b):
        return tuple(x + y for x, y in zip(a, b))

    @staticmethod
    def sub(a, b):
        return tuple(x - y for x, y in zip(a, b))

    @staticmethod
    def neg(a):
        return tuple(-x for x in a)

    @staticmethod
    def scale(q, a):
        return tuple(q * x for x in a)

    def mul(self, a, b):
        if self.d == 1:
            return (a[0] * b[0],)
        prod = [Fr(0)] * (2 * self.d - 1)
        for i, x in enumerate(a):
            if x:
                for j, y in enumerate(b):
                    if y:
                        prod[i + j] += x * y
        # reduce modulo the monic polynomial p (theta^d = -sum p_k theta^k)
        for k in range(len(prod) - 1, self.d - 1, -1):
            c = prod[k]
            if c:
                prod[k] = Fr(0)
                for j in range(self.d):
                    prod[k - self.d + j] -= c * self.p[j]
        return tuple(prod[:self.d])

    @staticmethod
    def is_zero(a):
        return all(x == 0 for x in a)

    def sign(self, a):
        """+1 or -1 when the sign of a(theta) is certified, 0 when a is exactly 0, None if undecided."""
        if self.is_zero(a):
            return 0
        if self.d == 1:
            return 1 if a[0] > 0 else -1
        lo, hi = self.lo, self.hi
        for _ in range(MAX_BISECT + 1):
            a_lo, a_hi = interval_poly(a, lo, hi)
            if a_lo > 0:
                return 1
            if a_hi < 0:
                return -1
            mid = (lo + hi) / 2
            if p_eval(self.p, mid) == 0:              # theta is the rational mid: evaluate exactly
                v = p_eval(list(a), mid)
                return 0 if v == 0 else (1 if v > 0 else -1)
            if roots_in(self.chain, lo, mid) == 1:
                hi = mid
            else:
                lo = mid
        return None

    def as_json(self, a):
        return fstr(a[0]) if self.d == 1 else [fstr(x) for x in a]


def interval_poly(coeffs, lo, hi):
    """Exact enclosure of sum c_k t^k for t in [lo, hi] (Horner in interval arithmetic)."""
    acc_lo = acc_hi = Fr(0)
    for c in reversed(coeffs):
        prods = [acc_lo * lo, acc_lo * hi, acc_hi * lo, acc_hi * hi]
        acc_lo, acc_hi = min(prods) + c, max(prods) + c
    return acc_lo, acc_hi


class Qs:
    """Numbers a + b*sqrt(c) with a, b rational, for one fixed c > 0 that is not a square (the
    searches' coefficients when a role has a square equal to such a c). Mixes with Fractions."""
    __slots__ = ("a", "b", "c")

    def __init__(self, a, b=0, c=None):
        self.a, self.b, self.c = Fr(a), Fr(b), c

    def _co(self, o):
        if isinstance(o, Qs):
            return o
        return Qs(o, 0, self.c)

    def __add__(self, o):
        o = self._co(o)
        return Qs(self.a + o.a, self.b + o.b, self.c or o.c)
    __radd__ = __add__

    def __neg__(self):
        return Qs(-self.a, -self.b, self.c)

    def __sub__(self, o):
        return self + (-self._co(o))

    def __rsub__(self, o):
        return self._co(o) - self

    def __mul__(self, o):
        o = self._co(o)
        c = self.c or o.c
        return Qs(self.a * o.a + (self.b * o.b * c if self.b and o.b else 0), self.a * o.b + self.b * o.a, c)
    __rmul__ = __mul__

    def __truediv__(self, o):
        o = self._co(o)
        c = self.c or o.c
        den = o.a * o.a - (o.b * o.b * c if o.b else 0)
        num = self * Qs(o.a, -o.b, c)
        return Qs(num.a / den, num.b / den, c)

    def __rtruediv__(self, o):
        return self._co(o) / self

    def __eq__(self, o):
        o = self._co(o) if not isinstance(o, Qs) else o
        return self.a == o.a and self.b == o.b

    def __hash__(self):
        return hash((self.a, self.b))

    def __bool__(self):
        return bool(self.a) or bool(self.b)

    def sign(self):
        """Exact sign of a + b*sqrt(c)."""
        if not self.b:
            return (self.a > 0) - (self.a < 0)
        if not self.a:
            return 1 if self.b > 0 else -1
        sa, sb = self.a > 0, self.b > 0
        if sa == sb:
            return 1 if sa else -1
        bigger_a = self.a * self.a > self.b * self.b * self.c
        return (1 if sa else -1) if bigger_a else (1 if sb else -1)

    def __lt__(self, o):
        return (self - o).sign() < 0

    def __gt__(self, o):
        return (self - o).sign() > 0

    def __le__(self, o):
        return (self - o).sign() <= 0

    def __ge__(self, o):
        return (self - o).sign() >= 0

    def json(self):
        return fstr(self.a) if not self.b else [fstr(self.a), fstr(self.b)]

    def __repr__(self):
        return f"Qs({self.a},{self.b},{self.c})"


def coef_json(x):
    return x.json() if isinstance(x, Qs) else fstr(x)


def field_of(obj):
    return Field(obj.get("theta")) if isinstance(obj, dict) else Field(None)


# ---------------------------------------------------------------- reading roles
def role_asts(build):
    """The role's atoms as (op, lhs, rhs) ASTs, read with the v0.5 sentence parser."""
    atoms = []
    for s in build["role"]:
        ast, _, _ = R.parse_sentence(s)
        _, prem, concl = ast
        need(prem == [] and len(concl) == 1, f"a role sentence is one atom: {s}")
        _, op, lhs, rhs = concl[0]
        need(op in ("=", "!="), f"a role uses = and != only: {s}")
        atoms.append((op, lhs, rhs))
    return atoms


def bracketings(vals, mul, memo=None, lo=0, hi=None):
    """All values of the product of vals[lo:hi] over every bracketing."""
    if hi is None:
        hi, memo = len(vals), {}
    if (lo, hi) in memo:
        return memo[(lo, hi)]
    if hi - lo == 1:
        out = [vals[lo]]
    else:
        out = []
        for k in range(lo + 1, hi):
            for a in bracketings(vals, mul, memo, lo, k):
                for b in bracketings(vals, mul, memo, k, hi):
                    out.append(mul(a, b))
    memo[(lo, hi)] = out
    return out


def evaluate(ast, ops, agree):
    """Evaluate a term AST with ops (const, name, add, neg, mul, inv). A chain of three or more
    factors contributes every bracketing: the pairs that must agree go to `agree`."""
    t = ast[0]
    if t == "num":
        return ops.const(Fr(ast[1]))
    if t == "frac":
        return ops.const(Fr(ast[1], ast[2]))
    if t == "name":
        return ops.name(ast[1])
    if t == "neg":
        return ops.neg(evaluate(ast[1], ops, agree))
    if t == "sum":
        return ops.add([evaluate(x, ops, agree) for x in ast[1]])
    if t == "prod":
        vals = [evaluate(x, ops, agree) for x in ast[1]]
        if len(vals) == 2:
            return ops.mul(vals[0], vals[1])
        brs = bracketings(vals, ops.mul)
        for b in brs[1:]:
            agree.append((brs[0], b))
        return brs[0]
    if t == "inv":
        return ops.inv(evaluate(ast[1], ops, agree))
    raise CertError(f"unknown term node {t}")


def contains_inv(ast):
    """Whether a term AST uses ^-1 anywhere."""
    t = ast[0]
    if t == "inv":
        return True
    if t in ("prod", "sum"):
        return any(contains_inv(x) for x in ast[1])
    if t == "neg":
        return contains_inv(ast[1])
    return False


# ---------------------------------------------------------------- the free algebra of a refutation (4.2)
class Ambient:
    """The free unital algebra over F modulo the kept global laws among q5 and q6.
    Words: tree ambients use "1", a name, or a pair (l, r); associative ambients use tuples of names."""

    def __init__(self, F, assoc, comm):
        self.F, self.assoc, self.comm = F, assoc, comm
        self.unit = () if assoc else "1"

    def key(self, w):
        return json.dumps(w)

    def name_word(self, g):
        return (g,) if self.assoc else g

    def mulw(self, a, b):
        if a == self.unit:
            return b
        if b == self.unit:
            return a
        if self.assoc:
            w = a + b
            return tuple(sorted(w)) if self.comm else w
        if self.comm and self.key(a) > self.key(b):
            a, b = b, a
        return (a, b)

    def word(self, j):
        """Parse a JSON word: "1", a name, or [left, right]."""
        if j == "1":
            return self.unit
        if isinstance(j, str):
            need(R.NAME_RE.match(j) is not None, f"bad name in a word: {j!r}")
            return self.name_word(j)
        need(isinstance(j, list) and len(j) == 2, f"a word is '1', a name or [left, right]: {j!r}")
        return self.mulw(self.word(j[0]), self.word(j[1]))

    # elements: dict word -> F element (no zero entries)
    def clean(self, d):
        return {w: c for w, c in d.items() if not self.F.is_zero(c)}

    def add(self, a, b):
        out = dict(a)
        for w, c in b.items():
            out[w] = self.F.add(out[w], c) if w in out else c
        return self.clean(out)

    def scale(self, q, a):
        return self.clean({w: self.F.mul(q, c) for w, c in a.items()})

    def neg(self, a):
        return {w: self.F.neg(c) for w, c in a.items()}

    def mul(self, a, b):
        out = {}
        for w1, c1 in a.items():
            for w2, c2 in b.items():
                w = self.mulw(w1, w2)
                c = self.F.mul(c1, c2)
                out[w] = self.F.add(out[w], c) if w in out else c
        return self.clean(out)

    def const(self, q):
        return self.clean({self.unit: self.F.c(q)})

    def fconst(self, fe):
        return self.clean({self.unit: fe})

    def gen(self, g):
        return {self.name_word(g): self.F.one()}

    def element(self, j, names):
        """Parse a JSON element: a list of [coefficient, word] pairs."""
        need(isinstance(j, list), "an element is a list of [coefficient, word] pairs")
        out = {}
        for pair in j:
            need(isinstance(pair, list) and len(pair) == 2, "an element entry is [coefficient, word]")
            c = self.F.el(pair[0])
            w = self.word(pair[1])
            for g in word_names(w):
                need(g in names, f"name '{g}' is not available here")
            out = self.add(out, {w: c})
        return out


def word_names(w):
    if isinstance(w, tuple) and (not w or isinstance(w[0], str)) and all(isinstance(x, str) for x in w):
        return set(w)                                   # associative word
    if w == "1":
        return set()
    if isinstance(w, str):
        return {w}
    return word_names(w[0]) | word_names(w[1])


class AmbOps:
    """Term evaluation into an ambient algebra."""

    def __init__(self, amb, names):
        self.a, self.names = amb, names

    def const(self, q):
        return self.a.const(q)

    def name(self, g):
        need(g in self.names, f"name '{g}' is not available here")
        return self.a.gen(g)

    def add(self, xs):
        out = {}
        for x in xs:
            out = self.a.add(out, x)
        return out

    def neg(self, x):
        return self.a.neg(x)

    def mul(self, x, y):
        return self.a.mul(x, y)

    def inv(self, x):
        raise CertError("^-1 is not allowed in a refutation's terms")


def role_context(atoms, amb, names, origin):
    """Relators (elements that are 0) and inequations (elements that are not 0) of the role."""
    ops = AmbOps(amb, names)
    rels, ineqs = [], []
    for op, lhs, rhs in atoms:
        agree = []
        a = evaluate(lhs, ops, agree)
        b = evaluate(rhs, ops, agree)
        for x, y in agree:
            rels.append(amb.add(x, amb.neg(y)))      # kept even when 0, so the numbering is fixed (4.4)
        d = amb.add(a, amb.neg(b))
        if op == "=":
            rels.append(d)
        else:
            ineqs.append(d)
    if origin == "k02":
        e = amb.gen("e1")
        rels.append(amb.add(amb.mul(e, e), amb.const(1)))
    return rels, ineqs


def copy_instance(amb, unit, args, names):
    """The instance of a kept equational unit, as an element that is 0 (4.4). Old variables are e1."""
    e = amb.gen("e1") if "e1" in names else None

    def arg(k):
        need(k in args, f"{unit} needs argument '{k}'")
        return amb.element(args[k], names)
    m = amb.mul
    if unit == "q5":
        a, b, c = arg("a"), arg("b"), arg("c")
        x, y = m(m(a, b), c), m(a, m(b, c))
    elif unit == "q6":
        a, b = arg("a"), arg("b")
        x, y = m(a, b), m(b, a)
    else:
        need(e is not None, f"{unit} is a copy with an old variable; it needs origin k02")
        if unit == "q5[onn]":
            b, c = arg("b"), arg("c")
            x, y = m(m(e, b), c), m(e, m(b, c))
        elif unit == "q5[non]":
            a, c = arg("a"), arg("c")
            x, y = m(m(a, e), c), m(a, m(e, c))
        elif unit == "q5[nno]":
            a, b = arg("a"), arg("b")
            x, y = m(m(a, b), e), m(a, m(b, e))
        elif unit == "q5[oon]":
            c = arg("c")
            x, y = m(m(e, e), c), m(e, m(e, c))
        elif unit == "q5[ono]":
            b = arg("b")
            x, y = m(m(e, b), e), m(e, m(b, e))
        elif unit == "q5[noo]":
            a = arg("a")
            x, y = m(m(a, e), e), m(a, m(e, e))
        elif unit == "q6[on]":
            b = arg("b")
            x, y = m(e, b), m(b, e)
        else:
            raise CertError(f"unknown unit {unit}")
    return amb.add(x, amb.neg(y))


# ---------------------------------------------------------------- refutation trees (4.4)
class TreeCheck:
    def __init__(self, info, drop, F, bounds):
        self.info, self.F, self.bounds = info, F, bounds
        U = judged_units(info["origin"], info["frames"])
        self.kept = set(U) - set(drop)
        frame = "f03" in info["frames"]
        assoc = frame or "q5" in self.kept
        comm = "q6" in self.kept
        self.amb = Ambient(F, assoc, comm)
        self.terms = 0
        self.allowed_instances = {u for u in self.kept if u in ("q5", "q6") or u in COPIES}
        if frame:
            self.allowed_instances |= Q5_FAMILY & set(UNITS[info["origin"]])

    def sum_terms(self, terms, rels, names):
        need(isinstance(terms, list), "terms must be a list")
        self.terms += len(terms)
        need(self.terms <= LIMIT_TERMS, f"more than {LIMIT_TERMS} terms in the tree")
        amb = self.amb
        total = {}
        for t in terms:
            need(isinstance(t, list) and len(t) == 3, "a term is [coefficient, relator, path]")
            coef = self.F.el(t[0])
            rel = t[1]
            if isinstance(rel, dict) and "ctx" in rel:
                k = rel["ctx"]
                need(isinstance(k, int) and 0 <= k < len(rels), f"relator index out of range: {k}")
                r = rels[k]
            elif isinstance(rel, dict) and "unit" in rel:
                need(rel["unit"] in self.allowed_instances, f"unit {rel['unit']} is not kept by this candidate")
                r = copy_instance(amb, rel["unit"], rel.get("args", {}), names)
            else:
                raise CertError(f"bad relator: {rel!r}")
            for step in t[2]:
                need(isinstance(step, list) and len(step) == 2 and step[0] in ("L", "R"), "a path step is ['L'|'R', element]")
                w = amb.element(step[1], names)
                r = amb.mul(w, r) if step[0] == "L" else amb.mul(r, w)
            total = amb.add(total, amb.scale(coef, r))
        return total

    def node(self, nd, rels, ineqs, names, depth):
        need(isinstance(nd, dict) and "node" in nd, "a tree node is a dict with 'node'")
        kind = nd["node"]
        amb = self.amb
        if kind == "close":
            tgt = nd["target"]
            if "const" in tgt:
                c = self.F.el(tgt["const"])
                need(self.F.sign(c) not in (0, None), "a constant target must be certified nonzero")
                T = amb.fconst(c)
            else:
                k = tgt.get("ineq")
                need(isinstance(k, int) and 0 <= k < len(ineqs), "bad inequation index")
                T = ineqs[k]
            need(self.sum_terms(nd["terms"], rels, names) == T, "close: the terms do not sum to the target")
            return
        if kind == "positive":
            need("q14" in self.kept, "positive: q14 must be kept")
            c = self.F.el(nd["c"])
            need(self.F.sign(c) == 1, "positive: c must be certified > 0")
            T = amb.fconst(c)
            for tj in nd["t"]:
                t = amb.element(tj, names)
                T = amb.add(T, amb.mul(t, t))
            need(self.sum_terms(nd["terms"], rels, names) == T, "positive: the terms do not sum to the sum of squares plus c")
            return
        need(depth < self.bounds["S"], f"case nodes nested deeper than S = {self.bounds['S']}")
        kids = nd.get("children")
        need(isinstance(kids, list) and len(kids) == 2, "a case node has two children")
        if kind == "split":
            need(nd.get("by") in ("q12", "q14") and nd["by"] in self.kept, "split: by q12 or q14, which must be kept")
            a = amb.element(nd["a"], names)
            b = amb.element(nd["b"], names)
            need(self.sum_terms(nd["proof_ab"], rels, names) == amb.mul(a, b), "split: proof_ab does not give a*b")
            self.node(kids[0], rels + [a], ineqs, names, depth + 1)
            self.node(kids[1], rels + [b], ineqs, names, depth + 1)
            return
        if kind == "inverse":
            need("q13" in self.kept, "inverse: q13 must be kept")
            a = amb.element(nd["a"], names)
            v = nd.get("v")
            need(isinstance(v, str) and R.NAME_RE.match(v) is not None and v not in names, "inverse: v must be a fresh name")
            self.node(kids[0], rels + [a], ineqs, names, depth + 1)
            vn = names | {v}
            av = amb.add(amb.mul(a, amb.gen(v)), amb.const(-1))
            va = amb.add(amb.mul(amb.gen(v), a), amb.const(-1))
            self.node(kids[1], rels + [av, va], ineqs, vn, depth + 1)
            return
        raise CertError(f"unknown node type {kind}")


def check_refutation(cert, info, drop, bounds=BOUNDS):
    """True when cert refutes the candidate `drop` in W; raises CertError otherwise."""
    U = judged_units(info["origin"], info["frames"])
    need(set(drop) <= set(U), "the refuted candidate drops a unit outside U")
    F = Field(cert.get("theta")) if isinstance(cert, dict) else Field(None)
    tc = TreeCheck(info, drop, F, bounds)
    names = set(info["generators"]) | ({"e1"} if info["origin"] == "k02" else set())
    rels, ineqs = role_context(info["atoms"], tc.amb, names, info["origin"])
    tc.node(cert["tree"], rels, ineqs, names, 0)
    return True


# ---------------------------------------------------------------- witnesses (4.3)
class Table:
    def __init__(self, w, bounds):
        n = w.get("dim")
        need(isinstance(n, int) and 1 <= n <= bounds["P3"], f"dim must be an integer from 1 to P3 = {bounds['P3']}")
        self.n = n
        entries = w.get("table", [])
        need(isinstance(entries, list) and len(entries) <= LIMIT_TABLE, f"at most {LIMIT_TABLE} table entries")
        M = {}
        for e in entries:
            need(isinstance(e, list) and len(e) == 4, "a table entry is [i, j, k, c]")
            i, j, k, c = e
            need(all(isinstance(x, int) for x in (i, j, k)) and 1 <= i < n and 1 <= j < n and 0 <= k < n,
                 "table indices: 1 <= i, j < n and 0 <= k < n (b0 is the unit and is not listed)")
            need((i, j, k) not in M, f"duplicate table entry {(i, j, k)}")
            v = frac(c)
            need(v != 0, "table entries must be nonzero")
            M[(i, j, k)] = v
        self.prod = [[[Fr(0)] * n for _ in range(n)] for _ in range(n)]
        for i in range(n):
            self.prod[0][i][i] = Fr(1)
            self.prod[i][0][i] = Fr(1)
        for (i, j, k), v in M.items():
            self.prod[i][j][k] = v

    def mulq(self, x, y):
        """Product of two rational coordinate vectors."""
        n = self.n
        out = [Fr(0)] * n
        for i, a in enumerate(x):
            if a:
                for j, b in enumerate(y):
                    if b:
                        ab = a * b
                        row = self.prod[i][j]
                        for k in range(n):
                            if row[k]:
                                out[k] += ab * row[k]
        return out

    def basis(self, i):
        v = [Fr(0)] * self.n
        v[i] = Fr(1)
        return v


class WitOps:
    """Term evaluation in a witness: vectors of F elements."""

    def __init__(self, T, F, vals):
        self.T, self.F, self.vals = T, F, vals

    def const(self, q):
        v = [self.F.zero() for _ in range(self.T.n)]
        v[0] = self.F.c(q)
        return v

    def name(self, g):
        need(g in self.vals, f"no value for '{g}'")
        return self.vals[g]

    def add(self, xs):
        out = [self.F.zero() for _ in range(self.T.n)]
        for x in xs:
            out = [self.F.add(a, b) for a, b in zip(out, x)]
        return out

    def neg(self, x):
        return [self.F.neg(a) for a in x]

    def mul(self, x, y):
        n, F = self.T.n, self.F
        out = [F.zero() for _ in range(n)]
        for i, a in enumerate(x):
            if F.is_zero(a):
                continue
            for j, b in enumerate(y):
                if F.is_zero(b):
                    continue
                ab = F.mul(a, b)
                row = self.T.prod[i][j]
                for k in range(n):
                    if row[k]:
                        out[k] = F.add(out[k], F.scale(row[k], ab))
        return out

    def inv(self, x):
        raise CertError("^-1 is not allowed in a role checked on a witness")


def vec_zero(v, F):
    return all(F.is_zero(a) for a in v)


def vec_certified_nonzero(v, F):
    return any(F.sign(a) not in (0, None) for a in v)


def check_role_values(atoms, ops, F, zero, nonzero, diff):
    for op, lhs, rhs in atoms:
        agree = []
        a = evaluate(lhs, ops, agree)
        b = evaluate(rhs, ops, agree)
        for x, y in agree:
            need(zero(diff(x, y)), "a chain's bracketings do not agree")
        if op == "=":
            need(zero(diff(a, b)), "a role equation fails")
        else:
            need(nonzero(diff(a, b)), "a role inequation is not certified")


def holds_unit(T, unit, E):
    """Whether an equational unit holds on the witness table (exact, on the basis; old variables are E)."""
    n = T.n
    m = T.mulq
    B = [T.basis(i) for i in range(n)]
    if unit == "q5":
        return all(m(m(B[i], B[j]), B[k]) == m(B[i], m(B[j], B[k]))
                   for i in range(1, n) for j in range(1, n) for k in range(1, n))
    if unit == "q6":
        return all(m(B[i], B[j]) == m(B[j], B[i]) for i in range(1, n) for j in range(i + 1, n))
    rng = range(n)
    if unit == "q5[onn]":
        return all(m(m(E, B[j]), B[k]) == m(E, m(B[j], B[k])) for j in rng for k in rng)
    if unit == "q5[non]":
        return all(m(m(B[i], E), B[k]) == m(B[i], m(E, B[k])) for i in rng for k in rng)
    if unit == "q5[nno]":
        return all(m(m(B[i], B[j]), E) == m(B[i], m(B[j], E)) for i in rng for j in rng)
    if unit == "q5[oon]":
        return all(m(m(E, E), B[k]) == m(E, m(E, B[k])) for k in rng)
    if unit == "q5[ono]":
        return all(m(m(E, B[j]), E) == m(E, m(B[j], E)) for j in rng)
    if unit == "q5[noo]":
        return all(m(m(B[i], E), E) == m(B[i], m(E, E)) for i in rng)
    if unit == "q6[on]":
        return all(m(E, B[j]) == m(B[j], E) for j in rng)
    raise CertError(f"{unit} is not an equational unit")


def pos_def(N):
    """Exact test of positive definiteness: all pivots of the symmetric elimination are > 0."""
    n = len(N)
    A = [row[:] for row in N]
    for k in range(n):
        if A[k][k] <= 0:
            return False
        for i in range(k + 1, n):
            f = A[i][k] / A[k][k]
            for j in range(k, n):
                A[i][j] -= f * A[k][j]
    return True


def bil(N, x, y):
    return sum(x[i] * N[i][j] * y[j] for i in range(len(x)) if x[i] for j in range(len(y)) if y[j])


def check_norm(T, cert, multiplicative, origin, E):
    """NORM (q12 and q13) or INV (q13): a positive-definite N and a conjugation C (4.3)."""
    n = T.n
    need(isinstance(cert, dict) and "N" in cert and "C" in cert, "a norm certificate is {N, C}")
    N = [[frac(x) for x in row] for row in cert["N"]]
    C = [[frac(x) for x in row] for row in cert["C"]]
    need(len(N) == n and all(len(r) == n for r in N) and len(C) == n and all(len(r) == n for r in C), "N and C must be n x n")
    need(all(N[i][j] == N[j][i] for i in range(n) for j in range(n)), "N must be symmetric")
    need(pos_def(N), "N must be positive definite")
    Cv = lambda v: [sum(C[i][j] * v[j] for j in range(n)) for i in range(n)]  # noqa: E731
    B = [T.basis(i) for i in range(n)]
    CB = [Cv(b) for b in B]
    m = T.mulq
    for i in range(n):
        for j in range(i, n):
            for left in (True, False):
                if left:
                    s = m(B[i], CB[j]) if i == j else [x + y for x, y in zip(m(B[i], CB[j]), m(B[j], CB[i]))]
                else:
                    s = m(CB[j], B[i]) if i == j else [x + y for x, y in zip(m(CB[j], B[i]), m(CB[i], B[j]))]
                want = [Fr(0)] * n
                want[0] = N[i][j] if i == j else 2 * N[i][j]
                need(s == want, "x*C(x) = C(x)*x = N(x)*1 fails")
    need(CB[0] == B[0] and N[0][0] == 1, "C(1) = 1 and N(1) = 1 are needed (old inverses, q2)")
    if origin == "k02":
        need(Cv(E) == [-x for x in E] and bil(N, E, E) == 1 and bil(N, B[0], E) == 0,
             "C(E) = -E, N(E) = 1 and no cross term between 1 and E are needed (old inverses, q2)")
    if multiplicative:
        prods = [[m(B[i], B[j]) for j in range(n)] for i in range(n)]

        def perms(a, b):
            return [(a, b)] if a == b else [(a, b), (b, a)]
        for i in range(n):
            for k in range(i, n):
                for j in range(n):
                    for l in range(j, n):  # noqa: E741
                        lhs = sum(bil(N, prods[a][b], prods[c][d]) for a, c in perms(i, k) for b, d in perms(j, l))
                        rhs = sum(N[a][c] for a, c in perms(i, k)) * sum(N[b][d] for b, d in perms(j, l))
                        need(lhs == rhs, "N is not multiplicative: N(x*y) = N(x)N(y) fails")
    return True


def check_witness(w, info, drop, bounds=BOUNDS):
    """True when w is a witness of the candidate `drop`: it satisfies the role and keeps every unit
    of U minus drop (4.3). Raises CertError otherwise."""
    U = judged_units(info["origin"], info["frames"])
    need(set(drop) <= set(U), "the candidate drops a unit outside U")
    need(isinstance(w, dict), "a witness is a dict")
    T = Table(w, bounds)
    F = Field(w.get("theta"))
    n = T.n
    E = None
    if info["origin"] == "k02":
        need(isinstance(w.get("E"), list) and len(w["E"]) == n, "origin k02 needs E with n coordinates")
        E = [frac(x) for x in w["E"]]
        minus1 = [Fr(0)] * n
        minus1[0] = Fr(-1)
        need(T.mulq(E, E) == minus1, "E*E = -1 fails")
    gens = w.get("gens")
    need(isinstance(gens, dict) and set(gens) == set(info["generators"]), "gens must give every generator, and only them")
    vals = {}
    for g, coords in gens.items():
        need(isinstance(coords, list) and len(coords) == n, f"generator '{g}' needs n coordinates")
        vals[g] = [F.el(x) for x in coords]
    if E is not None:
        vals["e1"] = [F.c(x) for x in E]
    ops = WitOps(T, F, vals)
    check_role_values(info["atoms"], ops, F, lambda v: vec_zero(v, F), lambda v: vec_certified_nonzero(v, F),
                      lambda x, y: [F.sub(a, b) for a, b in zip(x, y)])
    kept = set(U) - set(drop)
    if "f03" in info["frames"]:
        need(holds_unit(T, "q5", E), "the frame's theorem t1 (associativity) fails in the witness")
    for u in sorted(kept):
        if u in ("q12", "q13", "q14"):
            continue
        need(holds_unit(T, u, E), f"kept unit {u} fails in the witness")
    if n == 1:
        return True                       # the reals: q12, q13 and q14 hold
    need("q14" not in kept, "q14 is certified only in dimension 1")
    if "q12" in kept:
        need(w.get("q12") is not None, "q12 kept needs a NORM certificate")
        check_norm(T, w["q12"], True, info["origin"], E)
    if "q13" in kept:
        cert = w.get("q13") or w.get("q12")
        need(cert is not None, "q13 kept needs a NORM or INV certificate")
        check_norm(T, cert, cert is w.get("q12") and w.get("q13") is None, info["origin"], E)
    return True


def witness_fail_units(w, info, bounds=BOUNDS):
    """The judged units the witness does not show to hold (its smallest claimable candidate)."""
    U = judged_units(info["origin"], info["frames"])
    T = Table(w, bounds)
    E = [frac(x) for x in w["E"]] if info["origin"] == "k02" else None
    fail = []
    for u in U:
        if u in ("q12", "q13", "q14"):
            if T.n == 1:
                continue
            if u == "q14":
                fail.append(u)
                continue
            cert = w.get("q12") if u == "q12" else (w.get("q13") or w.get("q12"))
            try:
                ok = cert is not None and check_norm(T, cert, u == "q12" or (w.get("q13") is None), info["origin"], E)
            except CertError:
                ok = False
            if not ok:
                fail.append(u)
        elif not holds_unit(T, u, E):
            fail.append(u)
    return sorted(fail)


# ---------------------------------------------------------------- known kinds (4.5)
class RealOps:
    def __init__(self, F, vals):
        self.F, self.vals = F, vals

    def const(self, q):
        return self.F.c(q)

    def name(self, g):
        need(g in self.vals, f"no value for '{g}'")
        return self.vals[g]

    def add(self, xs):
        out = self.F.zero()
        for x in xs:
            out = self.F.add(out, x)
        return out

    def neg(self, x):
        return self.F.neg(x)

    def mul(self, x, y):
        return self.F.mul(x, y)

    def inv(self, x):
        raise CertError("^-1 is not allowed here")


class ComplexOps(RealOps):
    def const(self, q):
        return (self.F.c(q), self.F.zero())

    def add(self, xs):
        re, im = self.F.zero(), self.F.zero()
        for a, b in xs:
            re, im = self.F.add(re, a), self.F.add(im, b)
        return (re, im)

    def neg(self, x):
        return (self.F.neg(x[0]), self.F.neg(x[1]))

    def mul(self, x, y):
        F = self.F
        a, b = x
        c, d = y
        return (F.sub(F.mul(a, c), F.mul(b, d)), F.add(F.mul(a, d), F.mul(b, c)))


def check_known(cert, info):
    need(isinstance(cert, dict) and cert.get("kind") in ("k01", "k02"), "known: kind must be k01 or k02")
    kind = cert["kind"]
    need(kind == "k02" or info["origin"] == "k01", "the known kind must contain the origin")
    F = Field(cert.get("theta"))
    vals = cert.get("values")
    need(isinstance(vals, dict) and set(vals) == set(info["generators"]), "values for every generator, and only them")
    if kind == "k01":
        v = {g: F.el(x) for g, x in vals.items()}
        ops = RealOps(F, v)
        check_role_values(info["atoms"], ops, F, F.is_zero, lambda a: F.sign(a) not in (0, None), F.sub)
    else:
        v = {}
        for g, x in vals.items():
            need(isinstance(x, list) and len(x) == 2, f"a complex value is [real part, imaginary part]: {g}")
            v[g] = (F.el(x[0]), F.el(x[1]))
        v["e1"] = (F.zero(), F.one())
        ops = ComplexOps(F, v)
        check_role_values(info["atoms"], ops, F, lambda z: F.is_zero(z[0]) and F.is_zero(z[1]),
                          lambda z: F.sign(z[0]) not in (0, None) or F.sign(z[1]) not in (0, None),
                          lambda x, y: (F.sub(x[0], y[0]), F.sub(x[1], y[1])))
    return True


# ---------------------------------------------------------------- IMPOSSIBLE: congruence closure (4.6)
def congruence_contradiction(info):
    """Return (kind, detail) when congruence closure with the old arithmetic finds a contradiction,
    else None. Names are uninterpreted; terms of fractions and e1 are evaluated in the origin kind."""
    k02 = info["origin"] == "k02"
    nodes, index = [], {}

    def mk(key):
        if key not in index:
            index[key] = len(nodes)
            nodes.append(key)
        return index[key]

    def cval(q):                               # an old value
        return (Fr(q), Fr(0)) if k02 else Fr(q)

    class CCOps:
        def const(self, q):
            return mk(("c", cval(q)))

        def name(self, g):
            if g == "e1":
                return mk(("c", (Fr(0), Fr(1))))
            return mk(("g", g))

        def add(self, xs):
            return mk(("add", tuple(xs)))

        def neg(self, x):
            return mk(("neg", x))

        def mul(self, x, y):
            return mk(("mul", (x, y)))

        def inv(self, x):
            raise CertError("^-1 is not allowed in an IMPOSSIBLE world")
    eqs, neqs = [], []
    ops = CCOps()
    for op, lhs, rhs in info["atoms"]:
        agree = []
        a = evaluate(lhs, ops, agree)
        b = evaluate(rhs, ops, agree)
        eqs += agree
        (eqs if op == "=" else neqs).append((a, b))
    parent = {}
    value = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    conflict = []

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return False
        parent[rb] = ra
        va, vb = value.get(ra), value.get(rb)
        if va is not None and vb is not None and va != vb:
            conflict.append((va, vb))
        if va is None and vb is not None:
            value[ra] = vb
        return True

    def arith(op, vs):
        if op == "add":
            if k02:
                return (sum(v[0] for v in vs), sum(v[1] for v in vs))
            return sum(vs, Fr(0))
        if op == "neg":
            return (-vs[0][0], -vs[0][1]) if k02 else -vs[0]
        a, b = vs
        if k02:
            return (a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0])
        return a * b
    for i, key in enumerate(nodes):
        find(i)
        if key[0] == "c":
            value[find(i)] = key[1]
    for a, b in eqs:
        union(a, b)
    changed = True
    while changed and not conflict:
        changed = False
        sig = {}
        for i, key in enumerate(list(nodes)):
            if key[0] in ("c", "g"):
                continue
            kids = key[1] if key[0] in ("add", "mul") else (key[1],)
            s = (key[0], tuple(find(c) for c in kids))
            if s in sig:
                changed |= union(sig[s], i)
            else:
                sig[s] = i
            vs = [value.get(find(c)) for c in kids]
            if all(v is not None for v in vs):
                v = arith(key[0], vs)
                r = find(i)
                if value.get(r) is None:
                    value[r] = v
                    changed = True
                elif value[r] != v:
                    conflict.append((value[r], v))
                cnode = mk(("c", v))
                find(cnode)
                value.setdefault(find(cnode), v)
                changed |= union(r, cnode)
        # classes holding equal values are one class
        byval = {}
        for x in list(parent):
            r = find(x)
            if r in value:
                key = value[r]
                if key in byval and find(byval[key]) != r:
                    changed |= union(byval[key], r)
                byval.setdefault(key, r)
    if conflict:
        a, b = conflict[0]
        return ("values", [str(a), str(b)])
    for j, (a, b) in enumerate(neqs):
        if find(a) == find(b):
            return ("inequation", [j])
    return None


def check_impossible(cert, info):
    got = congruence_contradiction(info)
    need(got is not None, "congruence closure finds no contradiction")
    need(isinstance(cert, dict) and cert.get("kind") == got[0], f"the contradiction is of kind '{got[0]}'")
    return True


# ---------------------------------------------------------------- the mirror (2.7)
def rev_ast(ast):
    t = ast[0]
    if t == "prod":
        return ("prod", tuple(rev_ast(x) for x in reversed(ast[1])))
    if t == "sum":
        return ("sum", tuple(rev_ast(x) for x in ast[1]))
    if t in ("neg", "inv"):
        return (t, rev_ast(ast[1]))
    return ast


def rename_ast(ast, perm):
    t = ast[0]
    if t == "name":
        return ("name", perm.get(ast[1], ast[1]))
    if t in ("prod", "sum"):
        return (t, tuple(rename_ast(x, perm) for x in ast[1]))
    if t in ("neg", "inv"):
        return (t, rename_ast(ast[1], perm))
    return ast


def norm_sums(ast):
    """Flatten nested sums and sort their summands: addition is associative and commutative in W."""
    t = ast[0]
    if t == "sum":
        items = []
        for x in ast[1]:
            x = norm_sums(x)
            items += list(x[1]) if x[0] == "sum" else [x]
        return ("sum", tuple(sorted(items, key=R.sent_render)))
    if t == "prod":
        return ("prod", tuple(norm_sums(x) for x in ast[1]))
    if t in ("neg", "inv"):
        return (t, norm_sums(ast[1]))
    return ast


def atom_key(op, lhs, rhs):
    return (op,) + tuple(sorted([R.sent_render(norm_sums(lhs)), R.sent_render(norm_sums(rhs))]))


def mirror_invariant(atoms, perm):
    here = {atom_key(op, l, r) for op, l, r in atoms}
    there = {atom_key(op, rename_ast(rev_ast(l), perm), rename_ast(rev_ast(r), perm)) for op, l, r in atoms}
    return here == there


def check_mirror(m, d1, d2, info):
    need(info["origin"] == "k02", "the mirror merge needs origin k02")
    need(sorted(d2) == mirror_set(d1) and sorted(d1) != sorted(d2), "the twin must be the mirror of the branch")
    perm = m.get("perm")
    gens = set(info["generators"])
    need(isinstance(perm, dict) and set(perm) == gens and set(perm.values()) == gens, "perm must permute the generators")
    need(mirror_invariant(info["atoms"], perm), "the role is not mirror-invariant under perm")
    return True


# ---------------------------------------------------------------- world info
def world_info(world):
    """The facts of a world's single build that every checker needs."""
    b = world["builds"][0]
    return {"origin": b["origin"], "generators": sorted(b["generators"]), "frames": list(b["frames"]),
            "atoms": role_asts(b), "role": list(b["role"])}


def safe(fn, *args, **kw):
    """(True, '') or (False, reason) for a checker call."""
    try:
        fn(*args, **kw)
        return True, ""
    except CertError as e:
        return False, str(e)
    except (KeyError, TypeError, ValueError, ZeroDivisionError, R.ExprError) as e:
        return False, f"malformed certificate: {type(e).__name__}: {e}"
