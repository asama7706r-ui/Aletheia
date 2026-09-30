#!/usr/bin/env python3
"""
Independent verification of the blind-test-2 key (worlds + key.json), written
from protocol_v2.md only (Sections 2-9).  It does not import the builder.

Part A, for every world (and, for parameter worlds, for every grid value
provided in aux_proofs.json):
  * world format and budgets (Section 3);
  * mentions extracted exactly as Section 2 says (sympy parse_expr(...,
    evaluate=False) nodes; flattened sums/products; identical polynomials
    deduplicated);
  * every witness checked by exact rational matrix arithmetic: every
    variable-monomial coefficient of lhs - rhs of every law is the zero
    matrix, level rules, demands nonzero, live mentions nonzero where
    required, preference-first level of truth witnesses;
  * every certificate expanded (sum coef*left*ref*right) and compared exactly;
    graded rules only in graded certificates;
  * comm claims by Groebner basis over QQ (sympy);
  * SUBSUMED claims by exact rational solutions (elimination polynomials);
  * the correct answer recomputed from the definitions (viable levels, F_occ,
    F_role, branches, conservatism, validity of the truth) and compared with
    the key.
Part B: class, bound and interval recomputed exactly (Section 7), key fields
checked (Section 8).
Composition (Sections 5, 9) checked on the full key.
"""
import json, sys, os, re, keyword, itertools
from fractions import Fraction
import sympy
from sympy import Symbol, Add, Mul, Pow, preorder_traversal
from sympy.parsing.sympy_parser import parse_expr

HERE = os.path.dirname(os.path.abspath(__file__))
GRID = ["-3", "-2", "-1", "0", "1", "2", "3", "1/2"]
KNOWN_VALUES = set(Fraction(v) for v in ["-3", "-2", "-1", "0", "1", "2", "3", "1/2", "-1/2"])
DEG_LIMIT = {1: 9, 2: 7, 3: 5, 4: 4}
FORBIDDEN_NAMES = {"I", "E", "S", "N", "O", "Q", "pi"}
LEVEL_ORDER = ["SUBSUMED", "comm", "graded", "assoc"]


def Fr(x):
    return Fraction(str(x))


class Report:
    def __init__(self):
        self.items = []  # (world, check, ok, detail)

    def add(self, wid, name, ok, detail=""):
        self.items.append((wid, name, bool(ok), detail))
        return bool(ok)

    def failures(self):
        return [it for it in self.items if not it[2]]


# ------------------------------------------------------------------ NC polys (words = tuples of names)
def p_add(p, q, c=Fraction(1)):
    r = dict(p)
    for w, v in q.items():
        nv = r.get(w, Fraction(0)) + c * v
        if nv == 0:
            r.pop(w, None)
        else:
            r[w] = nv
    return r


def p_mul(p, q):
    r = {}
    for w1, c1 in p.items():
        for w2, c2 in q.items():
            w = w1 + w2
            nv = r.get(w, Fraction(0)) + c1 * c2
            if nv == 0:
                r.pop(w, None)
            else:
                r[w] = nv
    return r


def word(ws):
    return {tuple(ws): Fraction(1)}


# ------------------------------------------------------------------ world model
class AWorld:
    def __init__(self, d, pv):
        self.d = d
        self.id = d["id"]
        self.gens = [g["name"] for g in d["generators"]]
        self.grade = {g["name"]: int(g["grade"]) for g in d["generators"]}
        self.vars = list(d["variables"])
        self.params = list(d["parameters"])
        self.pv = {k: sympy.Rational(str(v)) for k, v in (pv or {}).items()}
        self.gsym = {g: Symbol(g, commutative=False) for g in self.gens}
        self.vsym = {v: Symbol(v) for v in self.vars}
        self.psym = {p: Symbol(p) for p in self.params}
        self.ld = {}
        self.ld.update(self.gsym)
        self.ld.update(self.vsym)
        self.ld.update(self.psym)
        self.laws = list(d["laws"])
        self.obs = [o["expr"] for o in d["observations"]]
        self.law_groups = []
        for L in self.laws:
            lhs, rhs = L.split("=")
            e = parse_expr(lhs, local_dict=self.ld) - parse_expr(rhs, local_dict=self.ld)
            self.law_groups.append(self.groups_of(e))
        self.demand_polys = []
        for s in self.obs:
            g = self.groups_of(parse_expr(s, local_dict=self.ld))
            if any(vm != self.zero_vm() for vm in g):
                raise ValueError("demand contains variables: " + s)
            self.demand_polys.append(g.get(self.zero_vm(), {}))

    def zero_vm(self):
        return tuple(0 for _ in self.vars)

    def vm_from_dict(self, dct):
        for k in dct:
            if k not in self.vars:
                raise ValueError("unknown variable in varmono: %s" % k)
        return tuple(int(dct.get(v, 0)) for v in self.vars)

    def groups_of(self, expr):
        """expand with sympy; return dict varmono-tuple -> NC poly (words of names)"""
        if self.pv:
            expr = expr.subs({self.psym[k]: v for k, v in self.pv.items()})
        e = sympy.expand(expr)
        out = {}
        for term in Add.make_args(e):
            if term == 0:
                continue
            c_part, nc_part = term.args_cnc()
            coef = sympy.Integer(1)
            vm = [0] * len(self.vars)
            for f in c_part:
                if f.is_Number:
                    coef *= f
                    continue
                base, ex = f.as_base_exp()
                if base.is_Symbol and base.name in self.vsym and ex.is_Integer and ex > 0:
                    vm[self.vars.index(base.name)] += int(ex)
                else:
                    raise ValueError("unexpected commutative factor %s in %s" % (f, term))
            if not coef.is_Rational:
                raise ValueError("non-rational coefficient %s" % coef)
            ws = []
            for f in nc_part:
                base, ex = f.as_base_exp()
                if base.is_Symbol and base.name in self.gsym and ex.is_Integer and ex > 0:
                    ws.extend([base.name] * int(ex))
                else:
                    raise ValueError("unexpected noncommutative factor %s" % f)
            vmt = tuple(vm)
            grp = out.setdefault(vmt, {})
            w = tuple(ws)
            nv = grp.get(w, Fraction(0)) + Fraction(int(coef.p), int(coef.q))
            if nv == 0:
                grp.pop(w, None)
            else:
                grp[w] = nv
        return {k: v for k, v in out.items() if v}

    def mentions(self):
        """(string, groups) for each distinct mention polynomial"""
        gs = set(self.gsym.values())
        out = []
        seen = []
        for L in self.laws:
            lhs, rhs = L.split("=")
            for side in (lhs, rhs):
                tree = parse_expr(side, local_dict=self.ld, evaluate=False)
                for node in preorder_traversal(tree):
                    if node.free_symbols & gs:
                        g1 = self.groups_of(node)
                        g2 = self.groups_of(parse_expr(str(node), local_dict=self.ld))
                        if g1 != g2:
                            raise ValueError("mention string round trip mismatch: %s" % node)
                        key = sorted((vm, sorted(p.items())) for vm, p in g1.items())
                        if key in seen:
                            continue
                        seen.append(key)
                        out.append((str(node), g1))
        return out

    def rule_poly(self, pair):
        g, h = pair
        if g not in self.grade or h not in self.grade:
            raise ValueError("bad graded pair")
        if g == h:
            if self.grade[g] != 1:
                raise ValueError("graded rule (g,g) with even g")
            return {(g, g): Fraction(1)}
        s = -1 if (self.grade[g] == 1 and self.grade[h] == 1) else 1
        return p_add({(g, h): Fraction(1)}, {(h, g): Fraction(1)}, Fraction(-s))


# ------------------------------------------------------------------ matrices
def mat(wit, gens):
    Ms = {}
    n = None
    for g in gens:
        if g not in wit:
            raise ValueError("witness misses generator " + g)
        M = [[Fraction(x) for x in row] for row in wit[g]]
        if n is None:
            n = len(M)
        if len(M) != n or any(len(r) != n for r in M):
            raise ValueError("witness matrices not square of equal size")
        Ms[g] = M
    if set(wit) - set(gens):
        raise ValueError("witness has extra keys")
    return Ms, n


def m_mul(A, B):
    n = len(A)
    R = [[Fraction(0)] * n for _ in range(n)]
    for i in range(n):
        for k in range(n):
            a = A[i][k]
            if a:
                Bk = B[k]
                Ri = R[i]
                for j in range(n):
                    if Bk[j]:
                        Ri[j] += a * Bk[j]
    return R


def m_eval(p, Ms, n, cache):
    R = [[Fraction(0)] * n for _ in range(n)]
    for w, c in p.items():
        if w in cache:
            M = cache[w]
        else:
            M = [[Fraction(int(i == j)) for j in range(n)] for i in range(n)]
            for k in range(len(w)):
                pref = w[:k + 1]
                if pref in cache:
                    M = cache[pref]
                else:
                    M = m_mul(M, Ms[w[k]])
                    cache[pref] = M
        for i in range(n):
            Ri = R[i]
            Mi = M[i]
            for j in range(n):
                if Mi[j]:
                    Ri[j] += c * Mi[j]
    return R


def m_zero(M):
    return all(x == 0 for r in M for x in r)


class Witness:
    def __init__(self, W, wit):
        self.W = W
        self.Ms, self.n = mat(wit, W.gens)
        self.cache = {}

    def is_zero(self, p):
        if not p:
            return True
        return m_zero(m_eval(p, self.Ms, self.n, self.cache))

    def group_zero(self, groups):
        return all(self.is_zero(p) for p in groups.values())

    def laws_hold(self):
        return all(self.group_zero(g) for g in self.W.law_groups)

    def commute(self):
        gs = self.W.gens
        for i in range(len(gs)):
            for j in range(i + 1, len(gs)):
                if not self.is_zero(p_add(word([gs[i], gs[j]]), word([gs[j], gs[i]]), Fraction(-1))):
                    return False
        return True

    def graded_rules(self):
        gs = self.W.gens
        for i in range(len(gs)):
            for j in range(i, len(gs)):
                if i == j and self.W.grade[gs[i]] == 0:
                    continue
                if not self.is_zero(self.W.rule_poly([gs[i], gs[j]])):
                    return False
        return True

    def pref_level(self):
        if self.commute():
            return "comm"
        if self.graded_rules() and any(self.W.grade[g] == 1 for g in self.W.gens):
            return "graded"
        return "assoc"

    def satisfies_level(self, L):
        if L == "comm":
            return self.commute()
        if L == "graded":
            return self.graded_rules()
        if L == "assoc":
            return True
        return False


# ------------------------------------------------------------------ certificates
def check_certificate(W, cert, target_groups, allow_graded):
    """returns (ok, detail)"""
    if not isinstance(cert, list):
        return False, "certificate not a list"
    want = {vm: p for vm, p in target_groups.items() if p}
    seen = set()
    for grp in cert:
        vm = W.vm_from_dict(grp["varmono"])
        if vm in seen:
            return False, "duplicate varmono group"
        seen.add(vm)
        total = {}
        for t in grp["terms"]:
            coef, left, ref, right = t
            c = Fraction(coef)
            for g in list(left) + list(right):
                if g not in W.gens:
                    return False, "unknown generator in word"
            if "law" in ref:
                i = int(ref["law"])
                rvm = W.vm_from_dict(ref["varmono"])
                rp = W.law_groups[i].get(rvm, {})
                if not rp:
                    return False, "reference to zero law coefficient"
            elif ref.get("rule") == "graded":
                if not allow_graded:
                    return False, "graded rule in an assoc certificate"
                rp = W.rule_poly(ref["pair"])
            else:
                return False, "bad ref %r" % (ref,)
            total = p_add(total, p_mul(p_mul(word(left), rp), word(right)), c)
        if total != want.get(vm, {}):
            return False, "expansion mismatch at varmono %s" % (vm,)
    if seen != set(want):
        return False, "groups do not match target varmonos"
    return True, "ok"


# ------------------------------------------------------------------ commutative algebra
class CommIdeal:
    def __init__(self, W):
        self.W = W
        self.cs = [Symbol("c_" + g) for g in W.gens]
        self.cmap = dict(zip(W.gens, self.cs))
        self.polys = []
        for g in W.law_groups:
            for vm, p in g.items():
                self.polys.append(self.to_comm(p))
        self.polys = [p for p in self.polys if p != 0]
        if self.polys:
            self.G = sympy.groebner(self.polys, *self.cs, order="grevlex", domain="QQ")
        else:
            self.G = None

    def to_comm(self, p):
        e = sympy.Integer(0)
        for w, c in p.items():
            t = sympy.Rational(c.numerator, c.denominator)
            for g in w:
                t *= self.cmap[g]
            e += t
        return sympy.expand(e)

    def contains(self, p):
        e = self.to_comm(p)
        if e == 0:
            return True
        if self.G is None:
            return False
        return self.G.contains(e)

    def group_contained(self, groups):
        return all(self.contains(p) for p in groups.values())

    def rational_points(self):
        """exact rational solutions; None if not zero-dimensional"""
        if self.G is None:
            return None
        if list(self.G.exprs) == [1]:
            return []
        if not self.G.is_zero_dimensional:
            return None
        cands = []
        for i, x in enumerate(self.cs):
            order = [c for c in self.cs if c != x] + [x]
            Gl = sympy.groebner(self.polys, *order, order="lex", domain="QQ")
            uni = [g for g in Gl.exprs if g.free_symbols <= {x}]
            if not uni:
                return None
            f = uni[-1]
            roots = set()
            for fac, m in sympy.factor_list(f, x)[1]:
                if sympy.degree(fac, x) == 1:
                    r = sympy.solve(fac, x)[0]
                    roots.add(Fraction(int(r.p), int(r.q)))
            cands.append(sorted(roots))
        pts = []
        for vals in itertools.product(*cands):
            sub = dict(zip(self.cs, [sympy.Rational(v.numerator, v.denominator) for v in vals]))
            if all(sympy.expand(p.subs(sub)) == 0 for p in self.polys):
                pts.append(list(vals))
        return pts


def eval_at(p, vals, gens):
    s = Fraction(0)
    for w, c in p.items():
        t = c
        for g in w:
            t *= vals[gens.index(g)]
        s += t
    return s


def group_zero_at(groups, vals, gens):
    return all(eval_at(p, vals, gens) == 0 for p in groups.values())


# ------------------------------------------------------------------ world format checks (Section 3)
def check_world_format_A(d, rep):
    wid = d.get("id")
    ok = rep.add(wid, "A.format.fields", set(d.keys()) == {"id", "experiment", "generators", "variables", "parameters", "laws", "observations"},
                 str(sorted(d.keys())))
    rep.add(wid, "A.format.experiment", d.get("experiment") == "A")
    gens = d["generators"]
    rep.add(wid, "A.budget.ngens", 1 <= len(gens) <= 4, str(len(gens)))
    names = [g["name"] for g in gens] + list(d["variables"]) + list(d["parameters"])
    bad = [n for n in names if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", n) or n in FORBIDDEN_NAMES
           or keyword.iskeyword(n) or hasattr(sympy, n)]
    rep.add(wid, "A.format.names", not bad and len(set(names)) == len(names), str(bad))
    rep.add(wid, "A.format.grades", all(set(g.keys()) == {"name", "grade"} and g["grade"] in (0, 1) for g in gens))
    rep.add(wid, "A.format.observations", all(set(o.keys()) == {"expr", "status"} and o["status"] == "nonzero" for o in d["observations"]))
    texts = list(d["laws"]) + [o["expr"] for o in d["observations"]]
    rep.add(wid, "A.format.no_decimals", not any(re.search(r"\d\.\d|\.\d|\d\.", t) for t in texts))
    # division only by integer constants, integer exponents, rational numbers
    ld = {g["name"]: Symbol(g["name"], commutative=False) for g in gens}
    for v in d["variables"]:
        ld[v] = Symbol(v)
    for p in d["parameters"]:
        ld[p] = Symbol(p)
    okdiv = True
    for t in texts:
        parts = t.split("=") if "=" in t else [t]
        for s in parts:
            tree = parse_expr(s, local_dict=ld, evaluate=False)
            for node in preorder_traversal(tree):
                if node.is_Float:
                    okdiv = False
                if isinstance(node, Pow):
                    b, e = node.args
                    if not e.is_Integer:
                        okdiv = False
                    elif e < 0 and not b.is_Integer:
                        okdiv = False
                if node.is_Symbol and node.name not in ld:
                    okdiv = False
                if node.is_Function:
                    okdiv = False
    rep.add(wid, "A.budget.rational_no_division", okdiv)
    rep.add(wid, "A.format.law_eq", all(L.count("=") == 1 for L in d["laws"]))
    # noncommutative degree after expansion, parameters kept symbolic
    degs = []
    maxdeg = 0
    for L in d["laws"]:
        lhs, rhs = L.split("=")
        e = sympy.expand(parse_expr(lhs, local_dict=ld) - parse_expr(rhs, local_dict=ld))
        for term in Add.make_args(e):
            c_part, nc_part = term.args_cnc()
            deg = 0
            for f in nc_part:
                b, ex = f.as_base_exp()
                deg += int(ex)
            maxdeg = max(maxdeg, deg)
        degs.append(maxdeg)
    rep.add(wid, "A.budget.degree", maxdeg <= DEG_LIMIT[len(gens)], "max degree %d, limit %d" % (maxdeg, DEG_LIMIT[len(gens)]))
    return True


# ------------------------------------------------------------------ Part A: fixed parameter values
def verify_A_fixed(d, e, pv, rep, tag, extra_witnesses=None):
    """verify entry e for world d at parameter values pv. returns recomputed decision tuple or None"""
    wid = d["id"] + tag
    try:
        W = AWorld(d, pv)
    except Exception as ex:
        rep.add(wid, "A.parse", False, repr(ex))
        return None
    has_odd = any(W.grade[g] == 1 for g in W.gens)
    levels = ["SUBSUMED", "comm"] + (["graded"] if has_odd else []) + ["assoc"]
    C = CommIdeal(W)
    mentions = W.mentions()
    mention_by_poly = {}
    for s, g in mentions:
        mention_by_poly[s] = g

    def find_mention(s):
        g = W.groups_of(parse_expr(s, local_dict=W.ld))
        for s2, g2 in mentions:
            if g2 == g:
                return s2, g2
        return None, g

    # --- dead mentions: certificates + trivial
    dead = set()
    for item in e.get("dead_in_assoc", []):
        s2, g = find_mention(item["mention"])
        ok, det = check_certificate(W, item["certificate"], g, allow_graded=False)
        rep.add(wid, "A.dead_in_assoc.certificate[%s]" % item["mention"], ok and s2 is not None, det if s2 else "not a mention")
        if ok and s2 is not None:
            dead.add(s2)
    for s, g in mentions:
        if s in dead:
            continue
        for lg in W.law_groups:
            # constant multiple of a whole law residual
            if set(lg) == set(g) and lg:
                ratios = set()
                okm = True
                for vm in g:
                    a, b = g[vm], lg[vm]
                    if set(a) != set(b):
                        okm = False
                        break
                    for w in a:
                        ratios.add(a[w] / b[w])
                if okm and len(ratios) == 1:
                    dead.add(s)
                    break

    # --- witnesses
    wits = []  # (label, claimed level, Witness)
    def add_wit(label, level, wj):
        try:
            Wt = Witness(W, wj)
        except Exception as ex:
            rep.add(wid, "A.witness.format[%s]" % label, False, repr(ex))
            return None
        okl = Wt.laws_hold()
        rep.add(wid, "A.witness.laws[%s]" % label, okl)
        okr = Wt.satisfies_level(level)
        rep.add(wid, "A.witness.level_rules[%s:%s]" % (label, level), okr)
        if okl and okr:
            wits.append((label, level, Wt))
            return Wt
        return None

    ans = e.get("answer")
    answit = None
    if ans == "DETERMINED" and e.get("level") != "SUBSUMED":
        answit = add_wit("answer", e.get("level"), e.get("witness"))
    brw = {}
    if ans == "FORK":
        for b in e.get("branches", []):
            if b["level"] != "SUBSUMED":
                brw[b["level"]] = add_wit("branch-" + b["level"], b["level"], b.get("witness"))
    truthw = None
    tr = e.get("truth")
    if tr and tr.get("level") != "SUBSUMED" and "witness" in tr:
        truthw = add_wit("truth", tr["level"], tr["witness"])
    for k, wj in enumerate(extra_witnesses or []):
        add_wit("aux%d" % k, wj["level"], wj["witness"])

    # --- rational points
    pts = C.rational_points()
    if pts is None:
        rep.add(wid, "A.subsumed.zero_dimensional", False, "rational solutions not exactly computable")
        pts_known = False
        pts = []
    else:
        pts_known = True

    # --- live classification
    live = []
    for s, g in mentions:
        if s in dead:
            continue
        shown = any(not Wt.group_zero(g) for (_, _, Wt) in wits) or any(not group_zero_at(g, pt, W.gens) for pt in pts)
        rep.add(wid, "A.mention.classified[%s]" % s, shown, "neither certified dead nor shown nonzero")
        live.append((s, g))
    for s in dead:
        g = mention_by_poly[s]
        contra = any(not Wt.group_zero(g) for (_, _, Wt) in wits)
        rep.add(wid, "A.mention.dead_consistent[%s]" % s, not contra)

    # --- level status
    viable, role = {}, {}
    demands = W.demand_polys
    vpts = [pt for pt in pts if all(eval_at(dp, pt, W.gens) != 0 for dp in demands)]
    rpts = [pt for pt in vpts if all(not group_zero_at(g, pt, W.gens) for s, g in live)]
    viable["SUBSUMED"] = (len(vpts) > 0) if pts_known else None
    role["SUBSUMED"] = (len(rpts) > 0) if pts_known else None
    one = {(): Fraction(1)}
    comm_one = C.contains(one)
    comm_dem = [C.contains(dp) for dp in demands]
    viable["comm"] = (not comm_one) and not any(comm_dem)
    comm_kills = [s for s, g in live if C.group_contained(g)]
    role["comm"] = viable["comm"] and not comm_kills

    # certificates of non-viability (graded exclusions, contradiction)
    nonviable_cert = {"graded": False, "assoc": False}
    for ex in e.get("exclusions", []):
        L = ex.get("level")
        if L == "graded":
            t = ex.get("target")
            if t == "1":
                tg = {W.zero_vm(): one}
            elif t in W.obs:
                tg = {W.zero_vm(): W.demand_polys[W.obs.index(t)]}
            else:
                rep.add(wid, "A.exclusion.graded.target", False, str(t))
                continue
            ok, det = check_certificate(W, ex.get("certificate"), tg, allow_graded=True)
            rep.add(wid, "A.exclusion.graded.certificate", ok, det)
            if ok:
                nonviable_cert["graded"] = True
        elif L == "comm":
            t = ex.get("target")
            if t == "1":
                okc = comm_one
            elif t in W.obs:
                okc = comm_dem[W.obs.index(t)]
            else:
                okc = False
            rep.add(wid, "A.exclusion.comm.groebner", okc, "target %s" % t)
        elif L == "SUBSUMED":
            rep.add(wid, "A.exclusion.SUBSUMED.no_viable_solution", pts_known and not vpts)
        elif L == "assoc":
            rep.add(wid, "A.exclusion.assoc.not_allowed", False)
    contr = e.get("contradiction")
    if contr is not None:
        t = contr.get("target")
        if t == "1":
            tg = {W.zero_vm(): one}
        elif t in W.obs:
            tg = {W.zero_vm(): W.demand_polys[W.obs.index(t)]}
        else:
            tg = None
        if tg is None:
            rep.add(wid, "A.contradiction.target", False)
        else:
            ok, det = check_certificate(W, contr.get("certificate"), tg, allow_graded=False)
            rep.add(wid, "A.contradiction.certificate", ok, det)
            if ok:
                nonviable_cert["assoc"] = True
                nonviable_cert["graded"] = True

    graded_kill_cert = set()
    for b in e.get("branches", []):
        if b["level"] == "graded":
            for k in b.get("killed", []):
                s2, g = find_mention(k["mention"])
                ok, det = check_certificate(W, k.get("certificate"), g, allow_graded=True)
                rep.add(wid, "A.branch.graded.killed_certificate[%s]" % k["mention"], ok and s2 is not None, det)
                if ok and s2 is not None:
                    graded_kill_cert.add(s2)

    def wit_viable(L):
        return any(Wt.satisfies_level(L) and all(not Wt.is_zero(dp) for dp in demands) for (_, _, Wt) in wits)

    def wit_role(L):
        return any(Wt.satisfies_level(L) and all(not Wt.is_zero(dp) for dp in demands)
                   and all(not Wt.group_zero(g) for s, g in live) for (_, _, Wt) in wits)

    for L in ("graded", "assoc"):
        if L not in levels:
            continue
        v = None
        if wit_viable(L):
            v = True
        if nonviable_cert[L]:
            if v:
                rep.add(wid, "A.level.%s.consistency" % L, False, "witness and certificate disagree")
            v = False
        viable[L] = v
        r = None
        if v is False:
            r = False
        elif wit_role(L):
            r = True
        elif L == "graded" and (set(s for s, g in live) & graded_kill_cert):
            r = False
        elif L == "assoc" and v:
            r = True  # the assoc mold keeps every live mention nonzero by definition
        role[L] = r

    # --- F_occ, F_role
    def first(stat):
        for L in levels:
            if stat[L] is None:
                return "UNKNOWN"
            if stat[L]:
                return L
        return None

    F_occ = first(viable)
    F_role = first(role)
    if F_occ == "UNKNOWN" or F_role == "UNKNOWN":
        rep.add(wid, "A.answer.recomputable", False, "viable %s role %s" % (viable, role))
        return None
    if F_occ is None:
        dec = ("CONTRADICTION",)
        branches = []
    elif F_occ == F_role:
        dec = ("DETERMINED", F_occ)
        branches = [F_occ]
    else:
        i0, i1 = levels.index(F_occ), levels.index(F_role)
        branches = [L for L in levels[i0:i1 + 1] if viable[L]]
        dec = ("FORK",) + tuple(branches)

    # --- compare with key
    if ans == "DETERMINED":
        keydec = ("DETERMINED", e.get("level"))
    elif ans == "FORK":
        keydec = ("FORK",) + tuple(b["level"] for b in e.get("branches", []))
    elif ans == "CONTRADICTION":
        keydec = ("CONTRADICTION",)
    else:
        keydec = None
    if keydec is not None:
        rep.add(wid, "A.answer.matches_definitions", keydec == dec, "key %s recomputed %s" % (keydec, dec))

    # --- exclusions cover exactly the right levels
    if dec[0] != "CONTRADICTION":
        need = []
        i0, i1 = levels.index(F_occ), levels.index(F_role)
        for L in levels[:i0]:
            need.append(L)
        for L in levels[i0:i1 + 1]:
            if not viable[L]:
                need.append(L)
        have = [x["level"] for x in e.get("exclusions", [])]
        rep.add(wid, "A.exclusions.exact_levels", sorted(have) == sorted(need), "have %s need %s" % (have, need))
    else:
        have = [x["level"] for x in e.get("exclusions", [])]
        rep.add(wid, "A.exclusions.contradiction_levels", sorted(have) == sorted(L for L in levels if L != "assoc"), str(have))

    # dead_in_assoc lists every non-trivial dead mention (all dead mentions are listed in this key)
    listed = set()
    for item in e.get("dead_in_assoc", []):
        s2, g = find_mention(item["mention"])
        if s2:
            listed.add(s2)
    rep.add(wid, "A.dead_in_assoc.complete", listed == dead, "listed %s dead %s" % (sorted(listed), sorted(dead)))

    # --- answer-specific checks
    if ans == "DETERMINED":
        F = e.get("level")
        if F != "SUBSUMED":
            okw = answit is not None and all(not answit.is_zero(dp) for dp in demands) and all(not answit.group_zero(g) for s, g in live)
            rep.add(wid, "A.DET.witness_all_live_and_demands_nonzero", okw)
        else:
            rep.add(wid, "A.DET.SUBSUMED.no_witness_needed", "witness" not in e)
        if tr is None:
            rep.add(wid, "A.DET.truth_present", False)
        else:
            rep.add(wid, "A.DET.truth_level", tr.get("level") == F, str(tr.get("level")))
            if F == "SUBSUMED":
                vals = [Fraction(v) for v in tr.get("values", [])]
                okv = len(vals) == len(W.gens) and all(group_zero_at(g, vals, W.gens) for g in W.law_groups)
                okv = okv and all(eval_at(dp, vals, W.gens) != 0 for dp in demands)
                okv = okv and all(not group_zero_at(g, vals, W.gens) for s, g in live)
                rep.add(wid, "A.DET.SUBSUMED.truth_values", okv)
                rep.add(wid, "A.DET.SUBSUMED.known_values", all(v in KNOWN_VALUES for v in vals))
            else:
                okt = truthw is not None and truthw.pref_level() == F and all(not truthw.is_zero(dp) for dp in demands)
                rep.add(wid, "A.DET.truth_witness_pref_level", okt, truthw.pref_level() if truthw else "none")
                if truthw is not None:
                    rep.add(wid, "A.DET.truth_keeps_live_nonzero", all(not truthw.group_zero(g) for s, g in live))
    elif ans == "FORK":
        bl = e.get("branches", [])
        if not tag:
            rep.add(wid, "A.FORK.no_parameters", not W.params)
        for k, b in enumerate(bl):
            L = b["level"]
            last = (k == len(bl) - 1)
            if L == "SUBSUMED":
                rep.add(wid, "A.FORK.SUBSUMED_branch_first", k == 0)
                okk = pts_known and all(any(group_zero_at(g, pt, W.gens) for s, g in live) for pt in vpts)
                rep.add(wid, "A.FORK.SUBSUMED_every_viable_solution_kills_live", okk and not last)
                continue
            Wt = brw.get(L)
            okd = Wt is not None and all(not Wt.is_zero(dp) for dp in demands)
            rep.add(wid, "A.FORK.branch_witness_demands[%s]" % L, okd)
            if last:
                okl = Wt is not None and all(not Wt.group_zero(g) for s, g in live)
                rep.add(wid, "A.FORK.last_witness_all_live_nonzero", okl)
            elif L in ("comm", "graded"):
                ks = b.get("killed", [])
                rep.add(wid, "A.FORK.branch_lists_killed[%s]" % L, len(ks) >= 1)
                for kk in ks:
                    s2, g = find_mention(kk["mention"])
                    islive = s2 is not None and s2 not in dead
                    if L == "comm":
                        rep.add(wid, "A.FORK.comm_killed_in_ideal[%s]" % kk["mention"], islive and C.group_contained(g))
                    else:
                        rep.add(wid, "A.FORK.graded_killed_live[%s]" % kk["mention"], islive and s2 in graded_kill_cert)
                    if bl and bl[-1]["level"] != "SUBSUMED" and brw.get(bl[-1]["level"]) is not None:
                        rep.add(wid, "A.FORK.killed_nonzero_on_last[%s]" % kk["mention"], not brw[bl[-1]["level"]].group_zero(g))
        if tr is None:
            rep.add(wid, "A.FORK.truth_present", False)
        else:
            lv = [b["level"] for b in bl]
            rep.add(wid, "A.FORK.truth_is_branch", tr.get("level") in lv)
            if tr.get("level") == "SUBSUMED":
                vals = [Fraction(v) for v in tr.get("values", [])]
                okv = len(vals) == len(W.gens) and all(group_zero_at(g, vals, W.gens) for g in W.law_groups)
                okv = okv and all(eval_at(dp, vals, W.gens) != 0 for dp in demands)
                rep.add(wid, "A.FORK.truth_values_valid", okv)
                rep.add(wid, "A.FORK.truth_known_values", all(v in KNOWN_VALUES for v in vals))
            else:
                okt = truthw is not None and truthw.pref_level() == tr.get("level") and all(not truthw.is_zero(dp) for dp in demands)
                rep.add(wid, "A.FORK.truth_witness_pref_level", okt, truthw.pref_level() if truthw else "none")
    elif ans == "CONTRADICTION":
        rep.add(wid, "A.CONTRADICTION.certificate_present", contr is not None and nonviable_cert["assoc"])
    # conservatism: truth not looser than F_role
    if tr is not None and F_role is not None and tr.get("level") in levels:
        rep.add(wid, "A.conservatism.truth_not_looser", levels.index(tr["level"]) <= levels.index(F_role))
    return dec


def decision_str(dec):
    if dec is None:
        return "None"
    return dec[0] + ("(" + ",".join(dec[1:]) + ")" if len(dec) > 1 else "")


def verify_A(d, e, aux, rep):
    wid = d["id"]
    check_world_format_A(d, rep)
    params = d["parameters"]
    ans = e.get("answer")
    rep.add(wid, "A.key.answer_label", ans in ("DETERMINED", "FORK", "CONTRADICTION", "UNDERDETERMINED"))
    rep.add(wid, "A.key.category_notes", isinstance(e.get("category"), str) and isinstance(e.get("notes"), str))
    if params:
        rep.add(wid, "A.params.only_DET_or_UNDER", ans in ("DETERMINED", "UNDERDETERMINED"))
        grid = (aux or {}).get("grid")
        rep.add(wid, "A.params.aux_grid_present", grid is not None and sorted(grid) == sorted(GRID) if len(params) == 1 else grid is not None)
        decs = {}
        if grid:
            for gv, sub in grid.items():
                pvs = sub["true_parameter_values"]
                rep.add(wid + "@" + gv, "A.params.grid_value_matches", len(params) != 1 or Fraction(pvs[params[0]]) == Fraction(gv))
                decs[gv] = verify_A_fixed(d, sub, pvs, rep, "@%s" % gv, sub.get("aux_witnesses"))
        if ans == "UNDERDETERMINED":
            rep.add(wid, "A.UNDER.no_true_parameter_values_needed", True)
            distinct = set(decs.values())
            rep.add(wid, "A.UNDER.decision_changes_on_grid", len(distinct) >= 2 and None not in distinct,
                    "; ".join("%s:%s" % (k, decision_str(v)) for k, v in sorted(decs.items())))
            return {"decisions": decs}
        else:
            rep.add(wid, "A.params.true_values_present", set(e.get("true_parameter_values", {})) == set(params))
            dec = verify_A_fixed(d, e, e.get("true_parameter_values"), rep, "", (aux or {}).get("aux_witnesses"))
            same = all(v == dec for v in decs.values()) and dec is not None
            rep.add(wid, "A.params.decision_parameter_independent_on_grid", same,
                    "; ".join("%s:%s" % (k, decision_str(v)) for k, v in sorted(decs.items())))
            return {"decision": dec}
    else:
        rep.add(wid, "A.noparams.no_true_parameter_values", "true_parameter_values" not in e)
        rep.add(wid, "A.noparams.not_UNDER", ans != "UNDERDETERMINED")
        dec = verify_A_fixed(d, e, None, rep, "", (aux or {}).get("aux_witnesses"))
        return {"decision": dec}


# ------------------------------------------------------------------ Part B
def dims_add(a, b, k=Fraction(1)):
    r = dict(a)
    for x, v in b.items():
        r[x] = r.get(x, Fraction(0)) + k * v
        if r[x] == 0:
            del r[x]
    return r


class BWorld:
    def __init__(self, d):
        self.d = d
        self.q = {k: {x: Fraction(str(v)) for x, v in dm.items()} for k, dm in d["quantities"].items()}
        self.c = {k: (Fraction(v["value"]), {x: Fraction(str(y)) for x, y in v["dims"].items()}) for k, v in d["constants"].items()}
        self.p = {k: Fraction(v) for k, v in d["parameters"].items()}
        self.sym = {k: Symbol(k) for k in list(self.q) + list(self.c) + list(self.p) + [d["term"]["unknown"]]}
        lhs, rhs = d["law"].split("=")
        self.y = lhs.strip()
        self.f = parse_expr(rhs, local_dict=self.sym)
        self.lam = self.sym[d["term"]["unknown"]]
        te = parse_expr(d["term"]["expr"], local_dict=self.sym)
        self.h = sympy.simplify(sympy.diff(te, self.lam))
        self.term_linear = sympy.simplify(te - self.lam * self.h) == 0 and self.lam not in self.h.free_symbols
        self.inputs = [k for k in self.q if k != self.y]

    def dim_of(self, e):
        e = sympy.sympify(e)
        if e.is_Number:
            return {}
        if e.is_Symbol:
            n = e.name
            if n in self.q:
                return dict(self.q[n])
            if n in self.c:
                return dict(self.c[n][1])
            if n in self.p:
                return {}
            raise ValueError("unknown symbol " + n)
        if isinstance(e, Mul):
            r = {}
            for a in e.args:
                r = dims_add(r, self.dim_of(a))
            return r
        if isinstance(e, Pow):
            b, ex = e.args
            if not ex.is_Integer:
                raise ValueError("non-integer power")
            return {k: v * int(ex) for k, v in self.dim_of(b).items()}
        if isinstance(e, Add):
            ds = [self.dim_of(a) for a in e.args]
            for x in ds[1:]:
                if x != ds[0]:
                    raise ValueError("inhomogeneous sum %s" % e)
            return ds[0]
        raise ValueError("unsupported %s" % e)

    def values_sub(self, inputs):
        sub = {self.sym[k]: sympy.Rational(str(v)) for k, v in inputs.items()}
        for k, (v, _) in self.c.items():
            sub[self.sym[k]] = sympy.Rational(v.numerator, v.denominator)
        for k, v in self.p.items():
            sub[self.sym[k]] = sympy.Rational(v.numerator, v.denominator)
        return sub


def _q(x):
    x = Fraction(x)
    return sympy.Rational(x.numerator, x.denominator)


def in_rational_span(vectors, target):
    """is target a Q-linear combination of the vectors (dicts dim -> exponent)?"""
    if not target:
        return True
    if not vectors:
        return False
    keys = sorted(set(k for v in vectors for k in v) | set(target))
    M = sympy.Matrix([[_q(v.get(k, 0)) for v in vectors] for k in keys])
    b = sympy.Matrix([_q(target.get(k, 0)) for k in keys])
    return M.rank() == M.row_join(b).rank()


def classify_B(d):
    B = BWorld(d)
    info = {}
    # reason 1
    t1 = False
    if d["coefficient_form"] == "constants":
        target = dims_add(B.q[B.y], B.dim_of(B.h), Fraction(-1))
        vecs = [dm for (_, dm) in B.c.values()]
        t1 = not in_rational_span(vecs, target)
        info["target_dim"] = target
        info["bridge"] = (not t1) and bool(target)
    # reason 2
    t2 = False
    sub_const = {B.sym[k]: sympy.Rational(v.numerator, v.denominator) for k, (v, _) in B.c.items()}
    sub_par = {B.sym[k]: sympy.Rational(v.numerator, v.denominator) for k, v in B.p.items()}
    sym_ok = True
    for s in d["symmetries"]:
        mp = {k: parse_expr(v, local_dict=B.sym) for k, v in s["map"].items()}
        ymap = mp.get(B.y, B.sym[B.y])
        alpha = sympy.simplify(ymap / B.sym[B.y])
        if alpha.free_symbols:
            sym_ok = False
            continue
        xsub = {B.sym[k]: mp.get(k, B.sym[k]) for k in B.inputs}
        fb = sympy.simplify(B.f.subs(xsub, simultaneous=True).subs(sub_const).subs(sub_par) / alpha - B.f.subs(sub_const).subs(sub_par))
        if fb != 0:
            sym_ok = False
        hb = sympy.simplify(B.h.subs(xsub, simultaneous=True).subs(sub_const).subs(sub_par) / alpha - B.h.subs(sub_const).subs(sub_par))
        if hb != 0:
            t2 = True
    info["symmetries_of_base"] = sym_ok
    # reason 3
    hpar = sympy.simplify(B.h.subs(sub_const).subs(sub_par))
    hgen = sympy.simplify(B.h.subs(sub_const))
    t3 = (hpar == 0) and (hgen != 0)
    reasons = [t1, t2, t3]
    # observations
    lo, hi = None, None
    conflict = False
    any_h = False
    S_empty = False
    for o in d["observations"]:
        sub = B.values_sub(o["inputs"])
        fv = sympy.Rational(B.f.subs(sub))
        hv = sympy.Rational(B.h.subs(sub))
        r = sympy.Rational(o["output"]) - fv
        dd = sympy.Rational(o["resolution"])
        if hv == 0:
            if abs(r) > dd:
                conflict = True
            continue
        any_h = True
        a, b = (r - dd) / hv, (r + dd) / hv
        if a > b:
            a, b = b, a
        lo = a if lo is None else max(lo, a)
        hi = b if hi is None else min(hi, b)
    if any_h and lo > hi:
        S_empty = True
    info["S"] = None if not any_h else (None if S_empty else (str(lo), str(hi)))
    zero_in_S = (not any_h) or (not S_empty and lo <= 0 <= hi)
    if conflict or S_empty:
        cls = "CONFLICT"
    elif any(reasons):
        if not zero_in_S:
            cls = "CONFLICT"
        else:
            cls = ["TYPE_IMPOSSIBLE", "SYMMETRY_ZERO", "INCIDENTAL"][reasons.index(True)]
    elif not any_h:
        cls = "UNCONSTRAINED"
    elif not zero_in_S:
        cls = "ACTIVE"
    else:
        cls = "BOUNDED"
    info["reasons"] = reasons
    info["zero_in_S"] = zero_in_S
    info["h_zero_conflict"] = conflict
    info["S_empty"] = S_empty
    bound = None
    if cls == "BOUNDED":
        bound = max(abs(lo), abs(hi))
    info["bound"] = None if bound is None else str(bound)
    return cls, info, B, (lo, hi)


def check_world_format_B(d, rep):
    wid = d["id"]
    rep.add(wid, "B.format.fields", set(d.keys()) == {"id", "experiment", "quantities", "constants", "parameters", "law", "term", "coefficient_form", "symmetries", "observations"}, str(sorted(d.keys())))
    rep.add(wid, "B.format.experiment", d.get("experiment") == "B")
    rep.add(wid, "B.format.coefficient_form", d["coefficient_form"] in ("free", "constants"))
    lhs = d["law"].split("=")[0].strip()
    rep.add(wid, "B.format.output_y", lhs == "y" and "y" in d["quantities"])
    ninp = len(d["quantities"]) - 1
    rep.add(wid, "B.budget.inputs", 1 <= ninp <= 3, str(ninp))
    rep.add(wid, "B.budget.observations", 1 <= len(d["observations"]) <= 6)
    names = list(d["quantities"]) + list(d["constants"]) + list(d["parameters"]) + [d["term"]["unknown"]]
    bad = [n for n in names if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", n) or n in FORBIDDEN_NAMES or keyword.iskeyword(n) or hasattr(sympy, n)]
    rep.add(wid, "B.format.names", not bad and len(set(names)) == len(names), str(bad))
    texts = [d["law"], d["term"]["expr"]] + [v for s in d["symmetries"] for v in s["map"].values()]
    rep.add(wid, "B.format.no_decimals", not any(re.search(r"\d\.\d|\.\d|\d\.", t) for t in texts))
    B = BWorld(d)
    okops = True
    for t in [d["law"].split("=")[1], d["term"]["expr"]]:
        tree = parse_expr(t, local_dict=B.sym, evaluate=False)
        for node in preorder_traversal(tree):
            if node.is_Float or node.is_Function:
                okops = False
            if isinstance(node, Pow) and not node.args[1].is_Integer:
                okops = False
            if node.is_Symbol and node.name not in B.sym:
                okops = False
    rep.add(wid, "B.budget.ops", okops)
    rep.add(wid, "B.term.linear", B.term_linear)
    # dimensional consistency of base law
    try:
        okdim = B.dim_of(B.f) == B.q[B.y]
    except Exception as ex:
        okdim = False
    rep.add(wid, "B.law.dimensionally_consistent", okdim)
    # observations give every quantity except y; exact rational values
    okobs = True
    for o in d["observations"]:
        if set(o.keys()) != {"inputs", "output", "resolution"}:
            okobs = False
        if set(o["inputs"]) != set(B.inputs):
            okobs = False
        if Fraction(o["resolution"]) < 0:
            okobs = False
        sub = B.values_sub(o["inputs"])
        for ex in (B.f, B.h):
            v = ex.subs(sub)
            if not v.is_Rational:
                okobs = False
    rep.add(wid, "B.observations.format_exact", okobs)
    # symmetry maps: each quantity -> rational multiple of a quantity
    oksm = True
    for s in d["symmetries"]:
        for k, v in s["map"].items():
            if k not in B.q:
                oksm = False
                continue
            e = parse_expr(v, local_dict=B.sym)
            fs = e.free_symbols
            if len(fs) != 1 or list(fs)[0].name not in B.q:
                oksm = False
                continue
            ratio = sympy.simplify(e / list(fs)[0])
            if not ratio.is_Rational or ratio == 0:
                oksm = False
            if B.q[k] != B.q[list(fs)[0].name]:
                oksm = False
    rep.add(wid, "B.symmetries.maps_rational_multiples", oksm)


def verify_B(d, e, rep):
    wid = d["id"]
    check_world_format_B(d, rep)
    cls, info, B, (lo, hi) = classify_B(d)
    rep.add(wid, "B.symmetries.are_base_symmetries", info["symmetries_of_base"])
    rep.add(wid, "B.class.matches", e.get("class") == cls, "key %s recomputed %s" % (e.get("class"), cls))
    if cls == "BOUNDED":
        rep.add(wid, "B.bound.matches", e.get("bound") is not None and Fraction(e["bound"]) == Fraction(info["bound"]), "key %s recomputed %s" % (e.get("bound"), info["bound"]))
    if cls == "ACTIVE" and "interval" in e:
        rep.add(wid, "B.interval.matches", [Fraction(x) for x in e["interval"]] == [Fraction(str(lo)), Fraction(str(hi))])
    if "true_value" in e and cls in ("BOUNDED", "ACTIVE"):
        tv = sympy.Rational(e["true_value"])
        rep.add(wid, "B.true_value.in_S", lo <= tv <= hi)
    rep.add(wid, "B.key.category_notes", isinstance(e.get("category"), str) and isinstance(e.get("notes"), str))
    return cls, info


# ------------------------------------------------------------------ composition
def check_composition(worlds, entries, results, rep):
    A = [k for k in entries if k.startswith("A-")]
    Bk = [k for k in entries if k.startswith("B-")]
    rep.add("ALL", "ids.A", sorted(A) == ["A-%02d" % i for i in range(1, 31)])
    rep.add("ALL", "ids.B", sorted(Bk) == ["B-%02d" % i for i in range(1, 19)])
    ans = {k: entries[k]["answer"] for k in A}
    cnt = lambda lab: sum(1 for k in A if ans[k] == lab)
    rep.add("ALL", "A.composition.DETERMINED=13", cnt("DETERMINED") == 13, str(cnt("DETERMINED")))
    rep.add("ALL", "A.composition.FORK=10", cnt("FORK") == 10, str(cnt("FORK")))
    rep.add("ALL", "A.composition.CONTRADICTION=4", cnt("CONTRADICTION") == 4, str(cnt("CONTRADICTION")))
    rep.add("ALL", "A.composition.UNDERDETERMINED=3", cnt("UNDERDETERMINED") == 3, str(cnt("UNDERDETERMINED")))
    cat = {k: entries[k]["category"] for k in list(A) + list(Bk)}
    det = [k for k in A if ans[k] == "DETERMINED"]
    dvk = {L: [k for k in det if cat[k].startswith("DETERMINED/demand-vs-killed/" + L)] for L in ("comm", "graded", "assoc")}
    for L in ("comm", "graded", "assoc"):
        ks = dvk[L]
        ok = len(ks) == 2 and all(entries[k]["level"] == L for k in ks)
        # objectively: some exclusion targets an observation (demand), or SUBSUMED excluded with rational points present
        for k in ks:
            e = entries[k]
            has_dem_target = any(x.get("target") not in (None, "1") for x in e["exclusions"])
            sub_by_dem = any(x["level"] == "SUBSUMED" for x in e["exclusions"]) and worlds[k]["observations"]
            ok = ok and (has_dem_target or bool(sub_by_dem)) and len(worlds[k]["observations"]) > 0
        rep.add("ALL", "A.composition.demand_vs_killed.%s=2" % L, ok, str(ks))
    cons = [k for k in det if cat[k].startswith("DETERMINED/conservative")]
    rep.add("ALL", "A.composition.conservative=3", len(cons) == 3, str(cons))
    subs = [k for k in det if entries[k]["level"] == "SUBSUMED"]
    rep.add("ALL", "A.composition.SUBSUMED=4", len(subs) == 4 and all(cat[k].startswith("DETERMINED/SUBSUMED") for k in subs), str(subs))
    excl = [k for k in subs if results.get(k, {}).get("subsumed_demand_excludes_killing")]
    rep.add("ALL", "A.composition.SUBSUMED_demand_excludes_killing>=1", len(excl) >= 1, str(excl))
    forks = [k for k in A if ans[k] == "FORK"]
    first = [k for k in forks if entries[k]["truth"]["level"] == entries[k]["branches"][0]["level"]]
    last = [k for k in forks if entries[k]["truth"]["level"] == entries[k]["branches"][-1]["level"]]
    rep.add("ALL", "A.composition.FORK_truth_first=5", len(first) == 5, str(first))
    rep.add("ALL", "A.composition.FORK_truth_last=5", len(last) == 5, str(last))
    three = [k for k in forks if len(entries[k]["branches"]) >= 3]
    rep.add("ALL", "A.composition.FORK_3plus_branches>=2", len(three) >= 2, str(three))
    subb = [k for k in forks if entries[k]["branches"][0]["level"] == "SUBSUMED"]
    rep.add("ALL", "A.composition.FORK_SUBSUMED_branch>=2", len(subb) >= 2, str(subb))
    rep.add("ALL", "A.composition.FORK_no_params", all(not worlds[k]["parameters"] for k in forks))
    con = [k for k in A if ans[k] == "CONTRADICTION"]
    inc = [k for k in con if entries[k]["contradiction"]["target"] == "1"]
    dk = [k for k in con if entries[k]["contradiction"]["target"] != "1" and results.get(k, {}).get("laws_consistent")]
    rep.add("ALL", "A.composition.CONTRADICTION_inconsistent_laws=2", len(inc) == 2, str(inc))
    rep.add("ALL", "A.composition.CONTRADICTION_demand_killed=2", len(dk) == 2, str(dk))
    und = [k for k in A if ans[k] == "UNDERDETERMINED"]
    sw = []
    for k in und:
        decs = results.get(k, {}).get("decisions", {})
        labs = set(v[0] for v in decs.values() if v)
        if "DETERMINED" in labs and "FORK" in labs:
            sw.append(k)
    rep.add("ALL", "A.composition.UNDER_switch_DET_FORK>=1", len(sw) >= 1, str(sw))
    noncon = [k for k in A if ans[k] != "CONTRADICTION"]
    outside = [k for k in noncon if "outside-familiar" in entries[k]["notes"]]
    rep.add("ALL", "A.composition.outside_familiar>=third", 3 * len(outside) >= len(noncon), "%d of %d" % (len(outside), len(noncon)))
    # Part B
    cls = {k: results[k]["class"] for k in Bk if k in results}
    want = {"ACTIVE": 3, "BOUNDED": 3, "UNCONSTRAINED": 1, "SYMMETRY_ZERO": 3, "TYPE_IMPOSSIBLE": 3, "INCIDENTAL": 2, "CONFLICT": 3}
    for c, n in want.items():
        got = sum(1 for k in Bk if cls.get(k) == c)
        rep.add("ALL", "B.composition.%s=%d" % (c, n), got == n, str(got))
    bridge = [k for k in Bk if cls.get(k) != "TYPE_IMPOSSIBLE" and results[k]["info"].get("bridge")]
    rep.add("ALL", "B.composition.bridge_rescued>=2", len(bridge) >= 2, str(bridge))
    symc = [k for k in Bk if cls.get(k) == "CONFLICT" and results[k]["info"]["reasons"][1] and not results[k]["info"]["zero_in_S"]
            and not results[k]["info"]["h_zero_conflict"] and not results[k]["info"]["S_empty"]]
    rep.add("ALL", "B.composition.symmetry_forbidden_detection>=1", len(symc) >= 1, str(symc))


# ------------------------------------------------------------------ main
def load_entries(path):
    if path.endswith(".jsonl"):
        out = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def subsumed_demand_excludes_killing(d, e):
    """DET SUBSUMED: some rational solution of the laws kills a live mention and a demand is zero there"""
    W = AWorld(d, e.get("true_parameter_values"))
    C = CommIdeal(W)
    pts = C.rational_points() or []
    dead = set()
    for it in e.get("dead_in_assoc", []):
        dead.add(json.dumps(sorted((str(k), sorted((str(w), str(c)) for w, c in v.items())) for k, v in W.groups_of(parse_expr(it["mention"], local_dict=W.ld)).items())))
    live = []
    for s, g in W.mentions():
        key = json.dumps(sorted((str(k), sorted((str(w), str(c)) for w, c in v.items())) for k, v in g.items()))
        if key not in dead:
            live.append(g)
    trivial_dead = []
    for pt in pts:
        kills = [g for g in live if group_zero_at(g, pt, W.gens) and not any(g == lg for lg in W.law_groups)]
        dz = [dp for dp in W.demand_polys if eval_at(dp, pt, W.gens) == 0]
        if kills and dz:
            return True
    return False


def main():
    args = sys.argv[1:]
    keypath = os.path.join(HERE, "key.json")
    only = None
    if "--draft" in args:
        keypath = os.path.join(HERE, "key_draft.jsonl")
    if "--key" in args:
        keypath = args[args.index("--key") + 1]
    if "--only" in args:
        only = args[args.index("--only") + 1].split(",")
    worlds_dir = os.path.join(HERE, "..", "worlds")
    if "--worlds" in args:
        worlds_dir = args[args.index("--worlds") + 1]
    auxpath = os.path.join(HERE, "aux_proofs.json")
    if "--aux" in args:
        auxpath = args[args.index("--aux") + 1]
    aux = {}
    if os.path.exists(auxpath):
        with open(auxpath, encoding="utf-8") as f:
            aux = json.load(f)
    import hashlib
    def _sha(p):
        return hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else "absent"
    print("key file: %s  sha256=%s" % (os.path.basename(keypath), _sha(keypath)))
    print("aux file: %s  sha256=%s" % (os.path.basename(auxpath), _sha(auxpath)))
    print("protocol: protocol_v2.md  sha256=%s" % _sha(os.path.join(HERE, "..", "protocol_v2.md")))
    print("sympy %s, python %s" % (sympy.__version__, sys.version.split()[0]))
    entries_list = load_entries(keypath)
    entries = {}
    rep = Report()
    for e in entries_list:
        if e["id"] in entries:
            rep.add(e["id"], "key.duplicate_id", False)
        entries[e["id"]] = e
    worlds = {}
    results = {}
    for wid in sorted(entries):
        if only and wid not in only:
            continue
        p = os.path.join(worlds_dir, wid + ".json")
        if not rep.add(wid, "world.file_exists", os.path.exists(p)):
            continue
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        rep.add(wid, "world.id_matches", d.get("id") == wid)
        worlds[wid] = d
        e = entries[wid]
        try:
            if wid.startswith("A-"):
                res = verify_A(d, e, aux.get(wid), rep)
                if e.get("answer") == "DETERMINED" and e.get("level") == "SUBSUMED":
                    res["subsumed_demand_excludes_killing"] = subsumed_demand_excludes_killing(d, e)
                if e.get("answer") == "CONTRADICTION":
                    lc = aux.get(wid, {}).get("laws_consistent_witness")
                    okc = False
                    if lc is not None:
                        Wd = AWorld(d, None)
                        Wt = Witness(Wd, lc)
                        okc = Wt.laws_hold() and Wt.n > 0
                    if e.get("contradiction", {}).get("target") != "1":
                        rep.add(wid, "A.CONTRADICTION.demand_killed.laws_consistent", okc)
                    res["laws_consistent"] = okc
                results[wid] = res
            else:
                cls, info = verify_B(d, e, rep)
                results[wid] = {"class": cls, "info": info}
        except Exception as ex:
            import traceback
            rep.add(wid, "exception", False, traceback.format_exc())
    if not only and len(entries) == 48:
        check_composition(worlds, entries, results, rep)
    fails = rep.failures()
    lines = []
    byw = {}
    for (w, name, ok, det) in rep.items:
        byw.setdefault(w, [0, 0])
        byw[w][0 if ok else 1] += 1
    for w in sorted(byw):
        extra = ""
        if w in results:
            r = results[w]
            if "decision" in r:
                extra = " decision-recomputed"
            if "decisions" in r:
                extra = " grid-decisions-recomputed"
            if "class" in r:
                extra = " class-recomputed"
        lines.append("%-8s checks passed %4d failed %d%s" % (w, byw[w][0], byw[w][1], extra))
    for (w, name, ok, det) in fails:
        lines.append("FAIL %s %s %s" % (w, name, det))
    nworlds = len([w for w in worlds])
    lines.append("RESULT: checked %d worlds (%d items); %d items failed" % (nworlds, len(rep.items), len(fails)))
    print("\n".join(lines))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
