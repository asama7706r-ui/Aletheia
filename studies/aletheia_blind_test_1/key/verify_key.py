#!/usr/bin/env python3
"""Independent verification of the Aletheia blind-test-1 worlds and answer key.

Usage: python verify_key.py [key file]   (default: key.json, else key_draft.jsonl)
Writes a detailed report to verify_output.txt next to this file and prints a summary.
E1 laws are parsed with a hand-written parser (no sympy expansion) into noncommutative
polynomials; all algebra is exact over Q (fractions)."""
import sys, os, re, json, itertools, keyword, random
from fractions import Fraction as Fr

KEYDIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(KEYDIR)
WORLDDIR = os.path.join(ROOT, "worlds")
FORBIDDEN = {"I", "E", "S", "N", "O", "Q", "pi"}
BUDGET = {1: 9, 2: 7, 3: 5, 4: 4}
GRID_P = [Fr(-3), Fr(-2), Fr(-1), Fr(0), Fr(1), Fr(2), Fr(3), Fr(1, 2)]
GRID_B = [Fr(k) for k in range(-5, 6)] + [Fr(1, 2), Fr(-1, 2), Fr(1, 3), Fr(-1, 3)]
ALLOWED_VALUES = {Fr(k) for k in range(-3, 4)} | {Fr(1, 2), Fr(-1, 2)}
FAMS = ["comm", "graded", "assoc"]


def fs(x):
    x = Fr(x)
    return str(x.numerator) if x.denominator == 1 else "%d/%d" % (x.numerator, x.denominator)


# ------------------------------------------------------------------ independent parser
# value = dict {(word, cmono): Fraction}; word = tuple of generator indices,
# cmono = sorted tuple of (commuting symbol, exponent)
TOK = re.compile(r"\s*(\*\*|\d+|[A-Za-z_][A-Za-z0-9_]*|[+\-*/()])")


def tokenize(s):
    pos, out = 0, []
    s = s.strip()
    while pos < len(s):
        m = TOK.match(s, pos)
        if not m:
            raise ValueError("bad character in %r at %d" % (s, pos))
        out.append(m.group(1))
        pos = m.end()
    return out


def cm_mul(a, b):
    d = dict(a)
    for k, e in b:
        d[k] = d.get(k, 0) + e
    return tuple(sorted(d.items()))


def p_add(p, q, c=Fr(1)):
    r = dict(p)
    for k, v in q.items():
        r[k] = r.get(k, Fr(0)) + c * v
    return {k: v for k, v in r.items() if v != 0}


def p_mul(p, q):
    r = {}
    for (w1, c1), v1 in p.items():
        for (w2, c2), v2 in q.items():
            k = (w1 + w2, cm_mul(c1, c2))
            r[k] = r.get(k, Fr(0)) + v1 * v2
    return {k: v for k, v in r.items() if v != 0}


def p_const(c):
    return {((), ()): Fr(c)} if c != 0 else {}


class Parser:
    def __init__(self, text, gens, comm):
        self.t = tokenize(text)
        self.i = 0
        self.gens = gens
        self.comm = comm

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else None

    def take(self, x=None):
        tok = self.peek()
        if x is not None and tok != x:
            raise ValueError("expected %s got %s" % (x, tok))
        self.i += 1
        return tok

    def parse(self):
        v = self.expr()
        if self.peek() is not None:
            raise ValueError("trailing tokens")
        return v

    def expr(self):
        v = self.term()
        while self.peek() in ("+", "-"):
            op = self.take()
            w = self.term()
            v = p_add(v, w, Fr(1) if op == "+" else Fr(-1))
        return v

    def term(self):
        v = self.unary()
        while self.peek() in ("*", "/"):
            op = self.take()
            if op == "*":
                v = p_mul(v, self.unary())
            else:
                tok = self.take()
                if not tok.isdigit():
                    raise ValueError("division by a non-integer constant")
                v = {k: x / int(tok) for k, x in v.items()}
        return v

    def unary(self):
        if self.peek() == "-":
            self.take()
            return {k: -x for k, x in self.unary().items()}
        if self.peek() == "+":
            self.take()
            return self.unary()
        return self.power()

    def power(self):
        base = self.atom()
        if self.peek() == "**":
            self.take()
            tok = self.take()
            if not tok.isdigit():
                raise ValueError("exponent must be a nonnegative integer literal")
            r = p_const(1)
            for _ in range(int(tok)):
                r = p_mul(r, base)
            return r
        return base

    def atom(self):
        tok = self.take()
        if tok == "(":
            v = self.expr()
            self.take(")")
            return v
        if tok.isdigit():
            return p_const(int(tok))
        if tok in self.gens:
            return {((self.gens[tok],), ()): Fr(1)}
        if tok in self.comm:
            return {((), ((tok, 1),)): Fr(1)}
        raise ValueError("unknown symbol " + tok)


def gen_index(world):
    return {g["name"]: i for i, g in enumerate(world["generators"])}


def comm_names(world):
    return set(world.get("variables", [])) | set(world.get("parameters", []))


def parse_poly(world, text):
    return Parser(text, gen_index(world), comm_names(world)).parse()


def law_poly(world, law):
    lhs, rhs = law.split("=")
    return p_add(parse_poly(world, lhs), parse_poly(world, rhs), Fr(-1))


def relations(world, pvals):
    """Noncommutative relations over Q: coefficient of every variable monomial of every law."""
    params = set(world.get("parameters", []))
    rels = []
    for law in world["laws"]:
        groups = {}
        for (w, cm), v in law_poly(world, law).items():
            coef = v
            vm = []
            for name, e in cm:
                if name in params:
                    coef *= Fr(pvals[name]) ** e
                else:
                    vm.append((name, e))
            g = groups.setdefault(tuple(vm), {})
            g[w] = g.get(w, Fr(0)) + coef
        for vm in sorted(groups):
            r = {w: c for w, c in groups[vm].items() if c != 0}
            if r:
                rels.append(r)
    return rels


def nc_poly(world, text):
    """Expression in generators only (observed quantities)."""
    out = {}
    for (w, cm), v in parse_poly(world, text).items():
        if cm:
            raise ValueError("observed quantity uses a commuting symbol")
        out[w] = out.get(w, Fr(0)) + v
    return {w: v for w, v in out.items() if v != 0}


def law_degree(world):
    return max((len(w) for law in world["laws"] for (w, cm) in law_poly(world, law)), default=0)


# ------------------------------------------------------------------ exact matrices
def M(rows):
    return [[Fr(x) for x in r] for r in rows]


def eye(n):
    return [[Fr(int(i == j)) for j in range(n)] for i in range(n)]


def mul(A, B):
    n, m, p = len(A), len(B), len(B[0])
    C = [[Fr(0)] * p for _ in range(n)]
    for i in range(n):
        for k in range(m):
            a = A[i][k]
            if a:
                Bk = B[k]
                Ci = C[i]
                for j in range(p):
                    if Bk[j]:
                        Ci[j] += a * Bk[j]
    return C


def is_zero(A):
    return all(x == 0 for r in A for x in r)


class Eval:
    def __init__(self, mats):
        self.m = mats
        self.n = len(mats[0])
        self.c = {(): eye(self.n)}

    def w(self, word):
        if word not in self.c:
            self.c[word] = mul(self.w(word[:-1]), self.m[word[-1]])
        return self.c[word]

    def p(self, poly):
        acc = [[Fr(0)] * self.n for _ in range(self.n)]
        for word, c in poly.items():
            W = self.w(word)
            for i in range(self.n):
                for j in range(self.n):
                    if W[i][j]:
                        acc[i][j] += c * W[i][j]
        return acc


def family_of(mats, grades):
    n = len(mats)
    P = {(i, j): mul(mats[i], mats[j]) for i in range(n) for j in range(n)}
    if all(P[(i, j)] == P[(j, i)] for i in range(n) for j in range(n)):
        return "comm"
    for i in range(n):
        for j in range(n):
            s = -1 if grades[i] * grades[j] % 2 else 1
            if P[(i, j)] != [[s * x for x in r] for r in P[(j, i)]]:
                return "assoc"
    return "graded"


class Span:
    def __init__(self):
        self.piv = []

    def add(self, v):
        v = list(v)
        for col, pv in self.piv:
            c = v[col]
            if c:
                for k in range(len(v)):
                    if pv[k]:
                        v[k] -= c * pv[k]
        for k, x in enumerate(v):
            if x:
                self.piv.append((k, [y / x for y in v]))
                return True
        return False


def algebra_dim(mats):
    n = len(mats[0])
    sp_ = Span()
    basis = [eye(n)]
    sp_.add([x for r in basis[0] for x in r])
    i = 0
    while i < len(basis):
        for G in mats:
            B = mul(basis[i], G)
            if sp_.add([x for r in B for x in r]):
                basis.append(B)
        i += 1
    return len(basis)


# ------------------------------------------------------------------ free-algebra ideal (truncated)
def dk(w):
    return (len(w), w)


def fam_rels(grades, fam):
    n = len(grades)
    out = []
    for i in range(n):
        for j in range(i, n):
            odd = grades[i] * grades[j] % 2 == 1
            if fam == "comm" and i < j:
                out.append({(i, j): Fr(1), (j, i): Fr(-1)})
            if fam == "graded":
                if i == j and odd:
                    out.append({(i, i): Fr(1)})
                elif i < j:
                    out.append({(i, j): Fr(1), (j, i): Fr(1) if odd else Fr(-1)})
    return out


class Ideal:
    """Echelon basis (deglex leading words) of span{u*r*v : |u|+deg r+|v| <= D}."""

    def __init__(self, n, rels, D):
        self.n, self.D, self.lead = n, D, {}
        jobs = []
        for r in rels:
            if r:
                d = max(len(w) for w in r)
                for s in range(D - d + 1):
                    jobs.append((d + s, s, r))
        jobs.sort(key=lambda j: j[0])
        self.one = False
        for tot, s, r in jobs:
            for a in range(s + 1):
                for u in itertools.product(range(n), repeat=a):
                    for v in itertools.product(range(n), repeat=s - a):
                        self._ins({u + w + v: c for w, c in r.items()})
            if () in self.lead:
                self.one = True
                return

    def _ins(self, row):
        while row:
            lw = max(row, key=dk)
            p = self.lead.get(lw)
            if p is None:
                c = row[lw]
                self.lead[lw] = {w: x / c for w, x in row.items()}
                return
            c = row[lw]
            for w, x in p.items():
                y = row.get(w, 0) - c * x
                if y:
                    row[w] = y
                else:
                    row.pop(w, None)

    def nf(self, poly):
        row = {w: Fr(c) for w, c in poly.items() if c}
        out = {}
        while row:
            lw = max(row, key=dk)
            c = row.pop(lw)
            p = self.lead.get(lw)
            if p is None:
                out[lw] = c
                continue
            for w, x in p.items():
                if w != lw:
                    y = row.get(w, 0) - c * x
                    if y:
                        row[w] = y
                    else:
                        row.pop(w, None)
        return out

    def has(self, poly):
        return self.one or not self.nf(poly)

    def closing_length(self):
        for k in range(self.D + 1):
            if all(w in self.lead for w in itertools.product(range(self.n), repeat=k)):
                return k
        return None

    def normal_words(self):
        k = self.closing_length()
        if k is None:
            return None
        return [w for L in range(k) for w in itertools.product(range(self.n), repeat=L) if w not in self.lead]


def killed(n, rels, polys, dmin, dmax):
    """First D where 1 or one of the polys enters the truncated ideal: ('ONE'|index, D) or None."""
    for D in range(dmin, dmax + 1):
        I = Ideal(n, rels, D)
        if I.one:
            return ("ONE", D)
        for i, p in enumerate(polys):
            if I.has(p):
                return (i, D)
    return None


def regular_rep(n, rels, dmin, dmax):
    """Regular representation of the presented algebra on normal words (None if not closed)."""
    for D in range(dmin, dmax + 1):
        I = Ideal(n, rels, D)
        if I.one:
            return None
        normal = I.normal_words()
        if normal is None:
            continue
        idx = {w: i for i, w in enumerate(normal)}
        mats = []
        for g in range(n):
            A = [[Fr(0)] * len(normal) for _ in normal]
            for j, w in enumerate(normal):
                for w2, c in I.nf({(g,) + w: Fr(1)}).items():
                    if w2 not in idx:
                        break
                    A[idx[w2]][j] = c
            mats.append(A)
        return mats
    return None


# ------------------------------------------------------------------ rational points
def comm_eval(poly, vals):
    t = Fr(0)
    for w, c in poly.items():
        x = Fr(c)
        for g in w:
            x *= vals[g]
        t += x
    return t


def rational_solutions(rels, n):
    import sympy as sp
    xs = sp.symbols("q0:%d" % n)
    polys = []
    for r in rels:
        e = 0
        for w, c in r.items():
            t = sp.Rational(c.numerator, c.denominator)
            for g in w:
                t *= xs[g]
            e += t
        e = sp.expand(e)
        if e != 0:
            polys.append(e)

    def solve(ps, vs):
        ps = [p for p in (sp.expand(p) for p in ps) if p != 0]
        if any(p.is_number for p in ps):
            return []
        if not vs:
            return [{}]
        if not ps:
            return None
        G = list(sp.groebner(ps, *vs, order="lex").exprs)
        if any(g.is_number for g in G):
            return []
        last = vs[-1]
        uni = [g for g in G if g.free_symbols <= {last}]
        if not uni:
            return None
        sols = []
        for fac, _ in sp.factor_list(sp.Poly(uni[0], last))[1]:
            if fac.degree() == 1:
                a, b = fac.all_coeffs()
                r0 = sp.Rational(-b, a)
                sub = solve([g.subs(last, r0) for g in G], vs[:-1])
                if sub is None:
                    return None
                for s in sub:
                    s = dict(s)
                    s[last] = r0
                    sols.append(s)
        return sols

    res = solve(polys, list(xs))
    if res is None:
        return None
    return [[Fr(int(s[x].p), int(s[x].q)) for x in xs] for s in res]


# ------------------------------------------------------------------ E1 checks
def fmt_E1(world):
    e = []
    if set(world) - {"id", "experiment", "generators", "variables", "parameters", "laws"}:
        e.append("extra world fields")
    if world.get("experiment") != "E1":
        e.append("experiment field")
    gens = world["generators"]
    if not 1 <= len(gens) <= 4:
        e.append("generator count")
    names = [g["name"] for g in gens] + world.get("variables", []) + world.get("parameters", [])
    if len(set(names)) != len(names):
        e.append("duplicate names")
    for nm in names:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", nm) or keyword.iskeyword(nm) or nm in FORBIDDEN:
            e.append("bad name " + nm)
    for g in gens:
        if set(g) != {"name", "grade"} or g["grade"] not in (0, 1):
            e.append("bad generator entry")
    for law in world["laws"]:
        if law.count("=") != 1:
            e.append("law must have exactly one equals sign")
        if "." in law:
            e.append("decimal point in law")
    try:
        if law_degree(world) > BUDGET[len(gens)]:
            e.append("degree budget")
        used = set()
        for law in world["laws"]:
            used |= set(tokenize(law.replace("=", "+")))
        for nm in names:
            if nm not in used:
                e.append("unused declared name " + nm)
    except Exception as ex:
        e.append("parse: %r" % ex)
    return e


def sample_laws_on(world, mats, pvals, trials=4, seed=7):
    """Laws evaluated at random rational values of the universally quantified variables."""
    rng = random.Random(seed)
    params = set(world.get("parameters", []))
    ev = Eval(mats)
    for _ in range(trials):
        vv = {v: Fr(rng.randint(-9, 9), rng.randint(1, 6)) for v in world.get("variables", [])}
        for law in world["laws"]:
            poly = {}
            for (w, cm), c in law_poly(world, law).items():
                x = c
                for name, ex in cm:
                    x *= (Fr(pvals[name]) if name in params else vv[name]) ** ex
                poly[w] = poly.get(w, Fr(0)) + x
            if not is_zero(ev.p({w: c for w, c in poly.items() if c})):
                return False
    return True


def newkind_checks(world, mats, pvals, fam, dim, observed, strict_candidates=None, need_complete=False):
    e = []
    n = len(world["generators"])
    grades = [g["grade"] for g in world["generators"]]
    rels = relations(world, pvals)
    ev = Eval(mats)
    if not all(is_zero(ev.p(r)) for r in rels):
        e.append("laws fail on witness")
    if not sample_laws_on(world, mats, pvals):
        e.append("laws fail on witness at sampled variables")
    if family_of(mats, grades) != fam:
        e.append("family mismatch")
    if algebra_dim(mats) != dim:
        e.append("dimension mismatch")
    obs = [nc_poly(world, q) for q in observed]
    if any(is_zero(ev.p(q)) for q in obs):
        e.append("an observed quantity vanishes in T")
    comm_only = Ideal(n, fam_rels(grades, "comm"), 3)
    grounded = [q for q in obs if not comm_only.has(q)] if strict_candidates is None else \
        [nc_poly(world, q) for q in strict_candidates]
    dmin = max(law_degree(world), 2)
    for fz in FAMS[:FAMS.index(fam)]:
        fr_ = fam_rels(grades, fz)
        formal = killed(n, fr_, obs, 2, 3)
        fam_only = Ideal(n, fr_, 3)
        cand = [q for q in grounded if not fam_only.has(q)]
        strong = killed(n, rels + fr_, cand, dmin, dmin + 4)
        if formal is None and strong is None:
            e.append("identifiability (a) fails for " + fz)
        if strong is None:
            e.append("no law-grounded quantity killed in " + fz)
    # (b) rational values
    strong_b = None if fam == "comm" else killed(n, rels + fam_rels(grades, "comm"), grounded, dmin, dmin + 4)
    if strong_b is None:
        sols = rational_solutions(rels, n)
        if sols is None:
            e.append("positive-dimensional rational solution set (b) not decided")
        else:
            for s in sols:
                if all(comm_eval(q, s) != 0 for q in grounded):
                    e.append("identifiability (b): rational point keeps every grounded quantity")
                if all(comm_eval(q, s) != 0 for q in obs):
                    e.append("identifiability (b): rational point keeps every observed quantity")
    for vals in itertools.product(GRID_B, repeat=n):
        if all(comm_eval(r, vals) == 0 for r in rels) and all(comm_eval(q, vals) != 0 for q in obs):
            e.append("identifiability (b): grid point found")
            break
    if need_complete:
        R = regular_rep(n, rels + fam_rels(grades, fam), dmin, dmin + 6)
        if R is None or len(R[0]) != dim:
            e.append("complete_presentation claimed but presented dimension differs")
    return e


def single_law_consistent(world, li, pvals):
    sub = dict(world)
    sub["laws"] = [world["laws"][li]]
    n = len(world["generators"])
    rels = relations(sub, pvals)
    for vals in itertools.product(GRID_B, repeat=n):
        if all(comm_eval(r, vals) == 0 for r in rels):
            return True
    if len(rels) == 1:
        lw = max(rels[0], key=dk)
        if lw and all(lw[-k:] != lw[:k] for k in range(1, len(lw))):
            return True  # single relation without self-overlap: Groebner basis, 1 not in ideal
    R = regular_rep(n, rels, 2, max(law_degree(sub), 2) + 5)
    if R is not None and len(R[0]) >= 1:
        ev = Eval(R)
        return all(is_zero(ev.p(r)) for r in rels)
    return False


def check_E1_entry(world, key, spec):
    e = fmt_E1(world)
    lab = key["label"]
    n = len(world["generators"])
    params = world.get("parameters", [])
    base = {"id", "label", "category", "notes"}
    need = {"NEW_KIND": base | {"true_family", "true_dim", "witness", "observed_nonzero", "complete_presentation"},
            "SUBSUMED": base | {"true_values", "observed_nonzero"},
            "CONTRADICTION": base, "UNDERDETERMINED": base}.get(lab)
    if need is None:
        return ["unknown label"], ""
    if params and lab != "UNDERDETERMINED":
        need = need | {"true_parameter_values"}
    if set(key) != need:
        e.append("key fields differ from the protocol format")
    pv = key.get("true_parameter_values")
    info = ""
    if lab == "NEW_KIND":
        mats = [M(key["witness"][g["name"]]) for g in world["generators"]]
        e += newkind_checks(world, mats, pv, key["true_family"], key["true_dim"], key["observed_nonzero"],
                            need_complete=key["complete_presentation"])
        info = "witness %dx%d" % (len(mats[0]), len(mats[0]))
        if params:
            grades = [g["grade"] for g in world["generators"]]
            for c in GRID_P:
                pc = {params[0]: fs(c)}
                R = regular_rep(n, relations(world, pc) + fam_rels(grades, key["true_family"]), 2, 9)
                if R is None:
                    e.append("parameter %s: presented algebra not finite/closed" % fs(c))
                    continue
                e2 = newkind_checks(world, R, pc, key["true_family"], len(R[0]), key["observed_nonzero"])
                if e2:
                    e.append("parameter %s changes the decision: %s" % (fs(c), e2[:2]))
            info += "; decision stable on the parameter grid"
    elif lab == "SUBSUMED":
        vals = [Fr(key["true_values"][g["name"]]) for g in world["generators"]]
        if any(v not in ALLOWED_VALUES for v in vals):
            e.append("value outside -3..3, +-1/2")
        obs = [nc_poly(world, q) for q in key["observed_nonzero"]]
        cs = [pv] + ([{params[0]: fs(c)} for c in GRID_P] if params else [])
        for pc in cs:
            rels = relations(world, pc)
            if any(comm_eval(r, vals) != 0 for r in rels):
                e.append("laws fail at the true values (params %s)" % pc)
            if any(comm_eval(q, vals) == 0 for q in obs):
                e.append("observed quantity vanishes at the true values")
        sols = rational_solutions(relations(world, pv), n)
        info = "rational solutions: %s" % ("positive-dimensional" if sols is None else len(sols))
        if params:
            info += "; values valid on the whole parameter grid"
    elif lab == "CONTRADICTION":
        rels = relations(world, pv)
        d0 = max(law_degree(world), 2)
        got = next((D for D in range(d0, d0 + 7) if Ideal(n, rels, D).one), None)
        if got is None:
            e.append("1 = 0 not derived")
        for li in range(len(world["laws"])):
            if not single_law_consistent(world, li, pv):
                e.append("law %d alone: no nonzero model found" % li)
        info = "1 = 0 derived at degree %s; each single law consistent" % got
    elif lab == "UNDERDETERMINED":
        sp_ = spec["E1_UND"].get(world["id"])
        if not sp_ or len(params) != 1:
            return e + ["no underdetermined spec / parameter"], ""
        roles = [nc_poly(world, q) for q in sp_["roles"]]
        grades = [g["grade"] for g in world["generators"]]
        seen = set()
        for c in GRID_P:
            pc = {params[0]: fs(c)}
            d = sp_["decisions"][fs(c)]
            seen.add(d)
            rels = relations(world, pc)
            d0 = max(law_degree(world), 2)
            if d == "CONTRADICTION":
                if not any(Ideal(n, rels, D).one for D in range(d0, d0 + 7)):
                    e.append("c=%s: contradiction not derived" % fs(c))
            elif d == "SUBSUMED":
                sols = rational_solutions(rels, n)
                if not sols or not any(all(comm_eval(q, s) != 0 for q in roles) for s in sols):
                    e.append("c=%s: no rational point keeping the roles" % fs(c))
            else:
                fam = d.split(":")[1]
                R = regular_rep(n, rels + fam_rels(grades, fam), 2, d0 + 6)
                if R is None:
                    e.append("c=%s: no finite model" % fs(c))
                    continue
                e2 = newkind_checks(world, R, pc, fam, len(R[0]), sp_["roles"], strict_candidates=sp_["roles"])
                if e2:
                    e.append("c=%s: %s" % (fs(c), e2[:2]))
        if len(seen) < 2:
            e.append("decision does not change on the grid")
        info = "decisions on grid verified (%d distinct)" % len(seen)
    return e, info


# ------------------------------------------------------------------ E2 checks
E2_FIELDS = ["id", "experiment", "quantities", "law_original", "filled_law", "symmetries", "ranges",
             "validated", "deficit", "state_original", "state_filled"]


def e2_parse(world, text, extra=()):
    import sympy as sp
    loc = {q: sp.Symbol(q, real=True) for q in list(world["quantities"]) + list(extra)}
    out, rhs = text.split("=")
    return out.strip(), sp.sympify(rhs, locals=loc)


def e2_dims(expr, qd):
    import sympy as sp

    def nz(d):
        return {k: v for k, v in d.items() if v != 0}
    if expr.is_Symbol:
        return nz({k: sp.Rational(v) for k, v in qd[expr.name].items()})
    if expr.is_Number:
        return {}
    if expr.is_Add:
        ds = [e2_dims(a, qd) for a in expr.args]
        if any(d is None or d != ds[0] for d in ds):
            return None
        return ds[0]
    if expr.is_Mul:
        acc = {}
        for a in expr.args:
            d = e2_dims(a, qd)
            if d is None:
                return None
            for k, v in d.items():
                acc[k] = acc.get(k, 0) + v
        return nz(acc)
    if expr.is_Pow:
        b, x = expr.args
        db = e2_dims(b, qd)
        if db is None or e2_dims(x, qd) != {} or (db and not x.is_Number):
            return None
        return nz({k: v * x for k, v in db.items()})
    if expr.is_Function:
        return {} if all(e2_dims(a, qd) == {} for a in expr.args) else None
    return None


def e2_consistent(world, law):
    import sympy as sp
    out, rhs = e2_parse(world, law)
    d = e2_dims(rhs, world["quantities"])
    want = {k: sp.Rational(v) for k, v in world["quantities"][out].items() if v != 0}
    return d is not None and d == want


def e2_val(expr, vals):
    import sympy as sp
    return complex(sp.N(expr.subs({sp.Symbol(k, real=True): sp.Rational(v) for k, v in vals.items()}), 40))


def e2_fits(world, law, point):
    out, rhs = e2_parse(world, law)
    return abs(e2_val(rhs, point["inputs"]) - complex(Fr(point["output"]))) <= float(point["tol"])


def e2_symmetric(world, law, sym, seed=11, trials=10):
    import sympy as sp
    params = sym.get("params", {})
    out, rhs = e2_parse(world, law, params)
    loc = {q: sp.Symbol(q, real=True) for q in list(world["quantities"]) + list(params)}
    maps = {q: sp.sympify(x, locals=loc) for q, x in sym["map"].items()}
    rng = random.Random(seed)
    rngs = world.get("ranges", {})
    for _ in range(trials):
        vals = {}
        for s in sorted(rhs.free_symbols, key=str):
            lo, hi = (Fr(z) for z in rngs.get(s.name, ["1/2", "3"]))
            vals[s] = sp.Rational(str(lo + (hi - lo) * Fr(rng.randint(0, 997), 997)))
        for p, (lo, hi) in params.items():
            lo, hi = Fr(lo), Fr(hi)
            vals[loc[p]] = sp.Rational(str(lo + (hi - lo) * Fr(rng.randint(0, 997), 997)))
        y = rhs.subs(vals)
        full = dict(vals)
        full[loc[out]] = y
        new = dict(vals)
        for q, x in maps.items():
            if q != out:
                new[loc[q]] = x.subs(full)
        y2 = maps[out].subs(full) if out in maps else y
        a, b = complex(sp.N(rhs.subs(new), 40)), complex(sp.N(y2, 40))
        if abs(a - b) > 1e-25 * (1 + abs(b)):
            return False
    return True


def check_E2_entry(world, key, spec):
    import sympy as sp
    e = []
    if [k for k in world if k not in E2_FIELDS] or any(k not in world for k in E2_FIELDS if k != "ranges"):
        e.append("world fields")
    if set(key) != {"id", "label", "detectable_by_card", "notes"}:
        e.append("key fields")
    for q in world["quantities"]:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", q) or q in FORBIDDEN or keyword.iskeyword(q) or hasattr(sp, q):
            e.append("quantity name " + q)
    o0, r0 = e2_parse(world, world["law_original"])
    o1, r1 = e2_parse(world, world["filled_law"])
    if o0 != o1:
        e.append("different output symbols")
    syms = {s.name for s in r0.free_symbols | r1.free_symbols}
    if syms | {o0} != set(world["quantities"]) or o0 in syms:
        e.append("quantities do not match the laws")
    law_syms = {s.name for s in r0.free_symbols} | {o0}
    for sym in world["symmetries"]:
        params = sym.get("params", {})
        loc = {q: sp.Symbol(q) for q in list(world["quantities"]) + list(params)}
        for q, x in sym["map"].items():
            if q not in law_syms or not {s.name for s in sp.sympify(x, locals=loc).free_symbols} <= law_syms | set(params):
                e.append("symmetry map uses symbols outside the law and its parameters")
    for p in world["validated"] + [world["deficit"]]:
        if set(p["inputs"]) != syms:
            e.append("a point does not list every quantity of both laws")
    if not e2_consistent(world, world["law_original"]):
        e.append("original law dimensionally inconsistent")
    if not all(e2_fits(world, world["law_original"], p) for p in world["validated"]):
        e.append("original law misses a validated point")
    if e2_fits(world, world["law_original"], world["deficit"]):
        e.append("original law fits the deficit point")
    if not e2_fits(world, world["filled_law"], world["deficit"]):
        e.append("filled law misses the deficit point")
    for sym in world["symmetries"]:
        if not e2_symmetric(world, world["law_original"], sym):
            e.append("listed symmetry does not hold for the original law")
    sig_val = not all(e2_fits(world, world["filled_law"], p) for p in world["validated"])
    sig_sym = not all(e2_symmetric(world, world["filled_law"], s) for s in world["symmetries"])
    sig_state = not set(world["state_original"]) <= set(world["state_filled"])
    cons = e2_consistent(world, world["filled_law"])
    lab, det = key["label"], key["detectable_by_card"]
    if lab == "SAME_LAW_NEW_STATE":
        if not cons or sig_val or sig_sym or sig_state or set(world["state_original"]) == set(world["state_filled"]):
            e.append("SAME_LAW_NEW_STATE not supported by the card")
    elif lab == "ANOTHER_LAW":
        if not cons:
            e.append("ANOTHER_LAW must be dimensionally consistent")
        if det and not (sig_val or sig_sym or sig_state):
            e.append("detectable ANOTHER_LAW without a card signal")
        if not det and (sig_val or sig_sym or sig_state):
            e.append("undetectable ANOTHER_LAW shows a card signal")
    elif lab == "INVALID":
        if cons:
            e.append("INVALID filled law is dimensionally consistent")
    else:
        e.append("label")
    ex = spec["E2_extra"].get(world["id"], {})
    for s in ex.get("natural_keep", []):
        if not (e2_symmetric(world, world["law_original"], s) and e2_symmetric(world, world["filled_law"], s)):
            e.append("natural symmetry not kept: " + s["name"])
    for s in ex.get("hidden_break", []):
        if not e2_symmetric(world, world["law_original"], s) or e2_symmetric(world, world["filled_law"], s):
            e.append("hidden symmetry-break claim fails: " + s["name"])
    info = "card signals: validated=%s symmetry=%s state=%s; filled dims consistent=%s" % (sig_val, sig_sym, sig_state, cons)
    return e, info


# ------------------------------------------------------------------ main
def main():
    kfile = sys.argv[1] if len(sys.argv) > 1 else os.path.join(KEYDIR, "key.json")
    if not os.path.exists(kfile):
        kfile = os.path.join(KEYDIR, "key_draft.jsonl")
    if kfile.endswith(".jsonl"):
        keys = [json.loads(l) for l in open(kfile, encoding="utf-8") if l.strip()]
    else:
        keys = json.load(open(kfile, encoding="utf-8"))
    spec = json.load(open(os.path.join(KEYDIR, "verify_spec.json"), encoding="utf-8"))
    report, nfail = [], 0
    report.append("key file: " + os.path.basename(kfile))
    ids = [k["id"] for k in keys]
    expect = ["E1-%02d" % i for i in range(1, 29)] + ["E2-%02d" % i for i in range(1, 17)]
    if sorted(ids) != expect:
        report.append("FAIL: key ids are not exactly E1-01..E1-28, E2-01..E2-16")
        nfail += 1
    wfiles = sorted(f[:-5] for f in os.listdir(WORLDDIR) if f.endswith(".json"))
    if wfiles != expect:
        report.append("FAIL: world files are not exactly the 44 expected ids")
        nfail += 1
    for k in keys:
        world = json.load(open(os.path.join(WORLDDIR, k["id"] + ".json"), encoding="utf-8"))
        if world.get("id") != k["id"]:
            errs, info = ["world id mismatch"], ""
        elif k["id"].startswith("E1-"):
            try:
                errs, info = check_E1_entry(world, k, spec)
            except Exception as ex:
                errs, info = ["exception %r" % ex], ""
        else:
            try:
                errs, info = check_E2_entry(world, k, spec)
            except Exception as ex:
                errs, info = ["exception %r" % ex], ""
        tag = k["label"] + (":" + k["true_family"] if k["label"] == "NEW_KIND" else "")
        if errs:
            nfail += 1
            report.append("%s [%s] FAIL: %s" % (k["id"], tag, "; ".join(errs)))
        else:
            report.append("%s [%s] OK: %s" % (k["id"], tag, info))
    from collections import Counter
    e1 = [k for k in keys if k["id"].startswith("E1-")]
    e2 = [k for k in keys if k["id"].startswith("E2-")]
    wl = {k["id"]: json.load(open(os.path.join(WORLDDIR, k["id"] + ".json"), encoding="utf-8")) for k in keys}
    c1 = Counter(k["label"] + (":" + k["true_family"] if k["label"] == "NEW_KIND" else "") for k in e1)
    want1 = {"SUBSUMED": 6, "NEW_KIND:comm": 4, "NEW_KIND:graded": 5, "NEW_KIND:assoc": 5, "CONTRADICTION": 4, "UNDERDETERMINED": 4}
    comp = []
    if dict(c1) != want1:
        comp.append("E1 label/family counts %s" % dict(c1))
    if sum(1 for k in e1 if k["label"] == "SUBSUMED" and wl[k["id"]].get("parameters")) != 1:
        comp.append("need exactly one SUBSUMED world with a parameter")
    if sum(1 for k in e1 if k["label"] == "NEW_KIND" and wl[k["id"]].get("parameters")) != 1:
        comp.append("need exactly one NEW_KIND world with a parameter")
    unfam = sum(1 for k in e1 if k["label"] == "NEW_KIND" and "outside the familiar list" in k["category"])
    if unfam * 3 < 14:
        comp.append("fewer than one third of NEW_KIND worlds outside the familiar list")
    c2 = Counter(k["label"] for k in e2)
    if dict(c2) != {"SAME_LAW_NEW_STATE": 6, "ANOTHER_LAW": 7, "INVALID": 3}:
        comp.append("E2 label counts %s" % dict(c2))
    if sum(1 for k in e2 if k["label"] == "ANOTHER_LAW" and not k["detectable_by_card"]) < 2:
        comp.append("fewer than 2 undetectable ANOTHER_LAW worlds")
    if comp:
        nfail += 1
        report.append("COMPOSITION FAIL: " + "; ".join(comp))
    else:
        report.append("COMPOSITION OK: E1 %s; NEW_KIND outside familiar list: %d/14; E2 %s; undetectable ANOTHER_LAW: %d"
                      % (dict(sorted(c1.items())), unfam, dict(sorted(c2.items())),
                         sum(1 for k in e2 if k["label"] == "ANOTHER_LAW" and not k["detectable_by_card"])))
    report.append("SUMMARY: %d worlds checked, %d failing items" % (len(keys), nfail))
    with open(os.path.join(KEYDIR, "verify_output.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(report) + "\n")
    print(report[-1])
    return 0 if nfail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
