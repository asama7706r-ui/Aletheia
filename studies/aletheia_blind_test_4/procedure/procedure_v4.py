"""Aletheia blind test 4 -- the procedure: it fills the identity card of every filler.

Usage:
  python procedure_v4.py run <worlds_dir> <out.json>     every *.json world in the folder
  python procedure_v4.py one <world.json>                 one world, printed

It reads the sealed registry (../registry/registry.json) and the strict reader (../lang/reader_v0.py).
It never reads registry_notes.md. Protocol: ../protocol_v4.md, sections 2 and 4.
Card items: F1 dimensions, F2 symmetry (actions from kinds, meaning cards and bodies), F3 old observations.
Exact arithmetic everywhere: sympy rationals for algebra; Fractions and an exact simplex (Chvatal's
dictionary method, Bland's rule) for the observation systems, with Farkas certificates from the dual.
"""
import itertools
import json
import os
import sys
from fractions import Fraction

import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "lang"))
import reader_v0 as R  # noqa: E402

REGISTRY_PATH = os.path.join(ROOT, "registry", "registry.json")
METHODS = ("procedure", "FIX", "DERIVE", "DIMS", "FORK_ALL")
UNKNOWN = "?"
# DIMS baseline: the dimension whose exponent gives the sign under each meaning-reading transformation (protocol 7).
DIMS_EXPONENT = {"rev_t": "T", "refl_x": "L", "conj_c": "Q"}


class WorldError(Exception):
    pass


def fstr(v):
    v = Fraction(v)
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def frac(s):
    return Fraction(s)


def to_rat(v):
    return sp.Rational(v.numerator, v.denominator) if isinstance(v, Fraction) else sp.Rational(v)


# ================================================================= registry

class Registry:
    def __init__(self, path=REGISTRY_PATH):
        with open(path, encoding="utf-8") as fh:
            self.raw = json.load(fh)
        ctx, info = R.check_registry(self.raw, path)
        if ctx.errors:
            raise SystemExit("registry rejected by the reader:\n" + "\n".join(ctx.errors))
        self.info = info
        self.sha = R.sha256_of(info["canon"])
        self.dims = list(self.raw["dimensions"])
        self.catalog = self.raw["catalog"]
        self.reads = {t["id"]: t["reads"] for t in self.raw["transformations"]}
        self.kinds = {k["id"]: k for k in self.raw["kinds"]}
        self.meanings = {m["id"]: m for m in self.raw["meanings"]}
        self.instruments = {i["id"]: i for i in self.raw["instruments"]}
        self.defs = {d["id"]: R.Parser(d["eq"]).relation({"="}) for d in self.raw["definitions"]}
        self._mdims, self._mact = {}, {}

    def kind_size(self, kind):
        shape = self.kinds[kind]["shape"]
        n = 1
        for s in shape:
            n *= s
        return n

    def meaning_size(self, m):
        return self.kind_size(self.meanings[m]["kind"])

    # ---- actions (as n x n sympy matrices; None = unknown)
    def as_matrix(self, v, n):
        if v == UNKNOWN:
            return None
        if isinstance(v, list):
            return sp.Matrix([[to_rat(frac(e)) for e in row] for row in v])
        return to_rat(frac(v)) * sp.eye(n)

    def meaning_action(self, m, t):
        key = (m, t)
        if key not in self._mact:
            v = self.meanings[m]["under"][t]
            if isinstance(v, dict):
                self._mact[key] = self._derived_action(v["derived"], m, t)
            else:
                self._mact[key] = self.as_matrix(v, self.meaning_size(m))
        return self._mact[key]

    def _derived_action(self, d, m, t):
        rel = self.defs[d]
        if rel[2] != ("name", m):
            raise SystemExit(f"definition {d} must be written '{m} = expression'")
        return self._eval_action(rel[3], t)

    def _eval_action(self, node, t):
        kind = node[0]
        if kind == "num":
            return sp.Matrix([[1]])
        if kind == "name":
            return self.meaning_action(node[1], t)
        if kind == "neg":
            return self._eval_action(node[1], t)
        if kind == "pow":
            a = self._eval_action(node[1], t)
            if a is None:
                return None
            if a.shape != (1, 1):
                raise SystemExit("a power of a multi-component meaning in a definition")
            return sp.Matrix([[a[0] ** node[2]]])
        if kind == "D":
            a, b = self.meaning_action(node[1], t), self.meaning_action(node[2], t)
            if a is None or b is None:
                return None
            return act_div(a, b)
        a, b = self._eval_action(node[2], t), self._eval_action(node[3], t)
        if a is None or b is None:
            return None
        if node[1] == "*":
            return act_mul(a, b)
        if node[1] == "/":
            return act_div(a, b)
        if a != b:
            raise SystemExit("a definition adds terms that transform differently")
        return a

    # ---- dimensions of a meaning (dict or None)
    def meaning_dims(self, m):
        if m not in self._mdims:
            anchor = self.meanings[m]["anchor"]
            if "instrument" in anchor:
                self._mdims[m] = dict(self.instruments[anchor["instrument"]]["unit"])
            elif "derived" in anchor:
                rel = self.defs[anchor["derived"]]
                self._mdims[m] = self._eval_dims(rel[3])
            else:
                self._mdims[m] = None
        return self._mdims[m]

    def _eval_dims(self, node):
        kind = node[0]
        if kind == "num":
            return {}
        if kind == "name":
            return self.meaning_dims(node[1])
        if kind == "neg":
            return self._eval_dims(node[1])
        if kind == "pow":
            a = self._eval_dims(node[1])
            return None if a is None else dnorm({k: v * node[2] for k, v in a.items()})
        if kind == "D":
            a, b = self.meaning_dims(node[1]), self.meaning_dims(node[2])
            return None if a is None or b is None else dadd(a, b, -1)
        a, b = self._eval_dims(node[2]), self._eval_dims(node[3])
        if a is None or b is None:
            return None
        if node[1] == "*":
            return dadd(a, b)
        if node[1] == "/":
            return dadd(a, b, -1)
        return a if a == b else None

    def anchor_instrument(self, m):
        anchor = self.meanings[m]["anchor"]
        return anchor.get("instrument", UNKNOWN)


def act_mul(a, b):
    if a.shape == (1, 1):
        return a[0] * b
    if b.shape == (1, 1):
        return b[0] * a
    raise SystemExit("product of two multi-component actions in a definition")


def act_div(a, b):
    if b.shape != (1, 1):
        raise SystemExit("division by a multi-component meaning in a definition")
    return a / b[0]


def dnorm(d):
    return {k: v for k, v in d.items() if v != 0}


def dadd(a, b, s=1):
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, 0) + s * v
    return dnorm(out)


# ================================================================= world

class Qty:
    """A world quantity or a new quantity of one filler."""

    def __init__(self, qid, meaning, kind, owner, dims, names, value, new=False, raw=None):
        self.id, self.meaning, self.kind, self.owner = qid, meaning, kind, owner
        self.dims, self.names, self.value, self.new, self.raw = dims, names, value, new, raw

    @property
    def n(self):
        return len(self.names)


def expr_of(node, S):
    kind = node[0]
    if kind == "num":
        return sp.Integer(node[1])
    if kind == "name":
        return S[node[1]]
    if kind == "neg":
        return -expr_of(node[1], S)
    if kind == "pow":
        return expr_of(node[1], S) ** node[2]
    if kind == "D":
        raise WorldError("D() inside a law or a filler (protocol V2)")
    a, b = expr_of(node[2], S), expr_of(node[3], S)
    return {"+": a + b, "-": a - b, "*": a * b, "/": a / b}[node[1]]


def parse_eq(s):
    rel = R.Parser(s).relation({"="})
    if rel[2][0] != "name":
        raise WorldError(f"the left side of '{s}' is not a single name (protocol V2)")
    return rel[2][1], rel[3]


class Filler:
    def __init__(self, raw):
        self.raw, self.id = raw, raw["id"]
        self.bodies = {b["id"]: b["type"] for b in raw["new_bodies"]}
        self.new = []


class World:
    def __init__(self, raw, reg):
        self.raw, self.reg = raw, reg
        ctx, canon = R.check_world(raw, reg.info, raw.get("id", "world"))
        if ctx.errors:
            raise WorldError("reader: " + "; ".join(ctx.errors[:5]))
        if raw["registry_sha256"] != reg.sha:
            raise WorldError("the world names another registry")
        self.id = raw["id"]
        self.bodies = {b["id"]: b["type"] for b in raw["bodies"]}
        self.qty = {}
        self.name_qty = {}
        for q in raw["quantities"]:
            kind = reg.meanings[q["meaning"]]["kind"]
            names = q["components"] if q["components"] else [q["id"]]
            if len(names) != reg.kind_size(kind):
                raise WorldError(f"quantity {q['id']}: components do not match its kind")
            val = q["value"]
            if val == UNKNOWN:
                raise WorldError(f"world quantity {q['id']} has value '?' (protocol V6)")
            if val != "var":
                vals = val if isinstance(val, list) else [val]
                val = [frac(v) for v in vals]
            qq = Qty(q["id"], q["meaning"], kind, q["owner"], dnorm(dict(q["dims"])), names, val, raw=q)
            self.qty[q["id"]] = qq
            for nm in names:
                self.name_qty[nm] = (qq, names.index(nm))
        if len(raw["laws"]) != 1:
            raise WorldError("a world must have exactly one law (protocol V2)")
        law = raw["laws"][0]
        self.law_id, self.accepted_at = law["id"], law["accepted_at"]
        self.y, law_ast = parse_eq(law["eq"])
        if self.y not in self.name_qty:
            raise WorldError("the law's left side is not a world quantity")
        self.fillers = []
        for fr in raw["fillers"]:
            f = Filler(fr)
            if fr["of"] != self.law_id:
                raise WorldError(f"filler {f.id} repairs another law")
            for nq in fr["new"]:
                kind = nq["kind"]
                if kind == UNKNOWN:
                    names = [nq["id"]]
                else:
                    n = reg.kind_size(kind)
                    names = nq["components"] if nq["components"] else [nq["id"]]
                    if len(names) != n:
                        raise WorldError(f"new quantity {nq['id']}: components do not match its kind")
                if nq["owner"] == UNKNOWN:
                    raise WorldError(f"new quantity {nq['id']} has an unknown owner (protocol V3)")
                dims = None if nq["dims"] == UNKNOWN else dnorm(dict(nq["dims"]))
                f.new.append(Qty(nq["id"], nq["meaning"], kind, nq["owner"], dims, names, nq["value"], True, nq))
            f.y, f.ast = parse_eq(fr["eq"])
            if f.y != self.y:
                raise WorldError(f"filler {f.id} has another left side")
            self.fillers.append(f)
        # symbols
        self.S = {nm: sp.Symbol(nm) for nm in self.name_qty}
        for f in self.fillers:
            f.S = dict(self.S)
            f.name_qty = dict(self.name_qty)
            for q in f.new:
                for i, nm in enumerate(q.names):
                    f.S[nm] = sp.Symbol(nm)
                    f.name_qty[nm] = (q, i)
            f.expr = expr_of(f.ast, f.S)
            if f.S[self.y] in f.expr.free_symbols:
                raise WorldError("the left side appears on a filler's right side (protocol V2)")
        self.law_expr = expr_of(law_ast, self.S)
        if self.S[self.y] in self.law_expr.free_symbols:
            raise WorldError("the left side appears on the law's right side (protocol V2)")
        # observations
        self.observers = {o["id"]: o for o in raw["observers"]}
        self.old, self.newobs = [], []
        for o in raw["observations"]:
            if o["of"] != self.y:
                raise WorldError(f"observation {o['id']} is not of the law's left side (protocol V8)")
            rec = {"id": o["id"], "state": {k: frac(v) for k, v in o["state"].items()},
                   "value": frac(o["value"]), "prec": frac(self.observers[o["observer"]]["precision"]),
                   "observer": o["observer"]}
            (self.old if o["epoch"] <= self.accepted_at else self.newobs).append(rec)
        # catalog
        self.catalog = [t for t in ("rev_t", "refl_x", "conj_c", "rot_z") if t in reg.reads]
        self.pairs = []
        cast_t = [t for t, r in reg.reads.items() if r == "cast"]
        if cast_t:
            ids = sorted(self.bodies)
            for i, a in enumerate(ids):
                for b in ids[i + 1:]:
                    if self.bodies[a] == self.bodies[b]:
                        self.pairs.append((a, b))
        self.cast_name = cast_t[0] if cast_t else None
        self.transformations = list(self.catalog) + [f"{self.cast_name}({a},{b})" for a, b in self.pairs]

    def constants(self):
        out = {}
        for q in self.qty.values():
            if q.value != "var":
                for nm, v in zip(q.names, q.value):
                    out[nm] = v
        return out


# ================================================================= actions and images

class ActionRule:
    """How a method gets actions. mode: 'procedure', 'FIX', 'DIMS', 'FORK_ALL', 'DERIVE'."""

    def __init__(self, mode, dims_of=None):
        self.mode, self.dims_of = mode, dims_of


def sign_symbol(qid, t):
    return sp.Symbol(f"{qid}:{t}")


def action_of(world, q, t, rule, free):
    """Action matrix of quantity q under meaning- or kind-reading t (entries may hold sign symbols).
    free collects the unknown sign symbols used."""
    reg, n = world.reg, q.n
    reads = reg.reads[t]
    if q.new and rule.mode == "FIX":
        return sp.eye(n)
    if reads == "meaning":
        if rule.mode == "DIMS":
            d = rule.dims_of(q)
            e = (d or {}).get(DIMS_EXPONENT[t], 0)
            if not isinstance(e, int) and not (isinstance(e, Fraction) and e.denominator == 1):
                e = 0
            return (-1) ** int(e) * sp.eye(n)
        if q.new and rule.mode in ("FORK_ALL", "DERIVE"):
            if n == 1:
                s = sign_symbol(q.id, t)
                free.append(s)
                return sp.Matrix([[s]])
            syms = [sign_symbol(f"{q.id}[{i}]", t) for i in range(n)]
            free.extend(syms)
            return sp.diag(*syms)
        v = q.raw["under"][t] if q.new else reg.meanings[q.meaning]["under"][t]
        if isinstance(v, dict):
            a = reg.meaning_action(q.meaning, t)
        else:
            a = reg.as_matrix(v, n)
    else:  # kind
        if q.kind == UNKNOWN:
            a = None
        else:
            a = reg.as_matrix(reg.kinds[q.kind]["under"][t], n)
    if a is None:
        if n != 1:
            raise WorldError(f"unknown action of the multi-component quantity {q.id} (protocol V4)")
        if rule.mode == "FIX":
            return sp.eye(1)
        s = sign_symbol(q.id, t)
        free.append(s)
        return sp.Matrix([[s]])
    return a


def image_map(world, qtys, t, rule, free, filler=None):
    """name -> image expression under transformation t (a catalog entry, including exchanges)."""
    S = filler.S if filler else world.S
    img = {}
    if t in world.reg.reads:
        for q in qtys:
            a = action_of(world, q, t, rule, free)
            vec = [S[nm] for nm in q.names]
            for i, nm in enumerate(q.names):
                img[S[nm]] = sum((a[i, j] * vec[j] for j in range(q.n)), sp.Integer(0))
        return img
    # exchange of two bodies
    b1, b2 = t[t.index("(") + 1:-1].split(",")
    by_owner = {}
    for q in qtys:
        by_owner.setdefault(q.owner, {})[q.meaning] = q
    for q in qtys:
        if q.owner not in (b1, b2) or (q.new and rule.mode == "FIX"):
            continue
        other = b2 if q.owner == b1 else b1
        p = by_owner.get(other, {}).get(q.meaning)
        if p is None or (p.new and rule.mode == "FIX"):
            if rule.mode == "FIX":
                continue
            raise WorldError(f"quantity {q.id} has no partner on body {other} (protocol V7)")
        for nm, pn in zip(q.names, p.names):
            img[S[nm]] = S[pn]
    return img


def all_quantities(world, filler):
    return list(world.qty.values()) + (list(filler.new) if filler else [])


def candidate_values(k):
    """A deterministic sequence of rational test values for witness points."""
    base = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
    return [Fraction(base[(k + j) % len(base)], 1 + (j % 3)) * (1 if (k + j) % 2 == 0 else -1)
            for j in range(40)]


def invariant(world, y_sym, f, img, names):
    """Protocol 2.3. Returns ('unchanged', None) or ('changed', point)."""
    iy = img.get(y_sym, y_sym)
    fi = f.xreplace(img)
    d = (iy - fi).xreplace({y_sym: f})
    if sp.cancel(sp.together(d)) == 0:
        return "unchanged", None
    syms = sorted(names, key=lambda z: z.name)
    for attempt in range(40):
        point = {s: to_rat(candidate_values(i)[attempt]) for i, s in enumerate(syms)}
        try:
            fv = f.xreplace(point)
            dv = d.xreplace(point)
        except (ZeroDivisionError, ValueError):
            continue
        if fv.has(sp.zoo, sp.nan, sp.oo) or dv.has(sp.zoo, sp.nan, sp.oo):
            continue
        dv = sp.nsimplify(dv) if not dv.is_Rational else dv
        if dv.is_Rational and dv != 0 and fv.is_Rational:
            return "changed", {s.name: fstr(Fraction(int(point[s].p), int(point[s].q))) for s in syms}
    raise WorldError("no witness point found for a changed equation")


def proof_json(status_point):
    st, pt = status_point
    return "unchanged" if st == "unchanged" else {"point": pt}


# ================================================================= F2

def f2_transformation(world, filler, t, rule, want_proofs=True):
    """Status of one transformation for one filler (protocol 2.4)."""
    y_sym = filler.S[world.y]
    qall = all_quantities(world, filler)
    q_law = [q for q in qall if not q.new]
    free = []
    img_old = image_map(world, q_law, t, rule, free)
    img_new = image_map(world, qall, t, rule, free, filler)
    used = (world.law_expr.free_symbols | {y_sym} | filler.expr.free_symbols)
    used_imgs = set()
    for s in used:
        for m in (img_old, img_new):
            if s in m:
                used_imgs |= m[s].free_symbols
    unknowns = sorted({s for s in free if s in used_imgs}, key=lambda z: z.name)
    names_old = set(filler.S.values()) - {y_sym}
    rows = []
    for signs in itertools.product((1, -1), repeat=len(unknowns)):
        sub = dict(zip(unknowns, (sp.Integer(v) for v in signs)))
        io = {k: v.xreplace(sub) for k, v in img_old.items()}
        inew = {k: v.xreplace(sub) for k, v in img_new.items()}
        old = invariant(world, y_sym, world.law_expr, io, names_old)
        new = invariant(world, y_sym, filler.expr, inew, names_old)
        rows.append((dict(zip((u.name for u in unknowns), signs)), old, new))
    changed = [o[0] != n[0] for _, o, n in rows]
    if not any(changed):
        status = "no_change"
    elif all(changed):
        status = "changed"
    else:
        status = "conditional"
    out = {"status": status, "unknowns": [u.name for u in unknowns]}
    if want_proofs:
        out["assignments"] = [{"signs": sg, "old": proof_json(o), "new": proof_json(n)} for sg, o, n in rows]
    if status == "conditional":
        out["keeping"] = [sg for (sg, o, n), c in zip(rows, changed) if not c]
        idx = {tuple(sorted(sg.items())): c for (sg, _, _), c in zip(rows, changed)}
        matters = []
        for u in unknowns:
            for sg, _, _ in rows:
                flip = dict(sg)
                flip[u.name] = -flip[u.name]
                if idx[tuple(sorted(sg.items()))] != idx[tuple(sorted(flip.items()))]:
                    matters.append(u.name)
                    break
        out["matters"] = matters
    return out


def f2_derive(world, filler, t):
    """DERIVE baseline: some choice of the free actions keeps the card -> no_change."""
    st = f2_transformation(world, filler, t, ActionRule("DERIVE"), want_proofs=False)
    return "changed" if st["status"] == "changed" else "no_change"


# ================================================================= F1

def f1(world, filler):
    reg = world.reg
    unknown_vars = {}
    eqs = []

    def dims_of_name(nm):
        q, _ = filler.name_qty[nm]
        if not q.new:
            return {k: sp.Integer(v) for k, v in q.dims.items()}
        if q.id not in unknown_vars:
            md = reg.meaning_dims(q.meaning) if q.meaning != UNKNOWN else None
            if q.dims is not None:
                if md is not None and dnorm(md) != dnorm(q.dims):
                    unknown_vars[q.id] = "contradiction"
                else:
                    unknown_vars[q.id] = {k: sp.Integer(v) for k, v in q.dims.items()}
            elif md is not None:
                unknown_vars[q.id] = {k: sp.Integer(v) for k, v in md.items()}
            else:
                unknown_vars[q.id] = {d: sp.Symbol(f"dim_{q.id}_{d}") for d in reg.dims}
        v = unknown_vars[q.id]
        return {} if v == "contradiction" else v

    def walk(node):
        kind = node[0]
        if kind == "num":
            return {}
        if kind == "name":
            return dims_of_name(node[1])
        if kind == "neg":
            return walk(node[1])
        if kind == "pow":
            a = walk(node[1])
            return {k: v * node[2] for k, v in a.items()}
        a, b = walk(node[2]), walk(node[3])
        if node[1] == "*":
            return {k: a.get(k, 0) + b.get(k, 0) for k in set(a) | set(b)}
        if node[1] == "/":
            return {k: a.get(k, 0) - b.get(k, 0) for k in set(a) | set(b)}
        for k in set(a) | set(b):
            eqs.append(sp.Integer(0) + a.get(k, 0) - b.get(k, 0))
        return a

    rhs = walk(filler.ast)
    lhs = dims_of_name(world.y)
    for k in set(lhs) | set(rhs):
        eqs.append(sp.Integer(0) + lhs.get(k, 0) - rhs.get(k, 0))
    contradiction = any(v == "contradiction" for v in unknown_vars.values())
    syms = sorted({s for v in unknown_vars.values() if isinstance(v, dict)
                   for e in v.values() for s in sp.sympify(e).free_symbols}, key=lambda z: z.name)
    eqs = [sp.expand(e) for e in eqs if sp.expand(e) != 0]
    inferred = {}
    if contradiction:
        return {"consistent": False, "inferred_dims": {}}, None
    if not syms:
        ok = all(e == 0 for e in eqs)
        return {"consistent": ok, "inferred_dims": {}}, ({} if ok else None)
    sol = sp.linsolve(eqs, syms) if eqs else sp.FiniteSet(tuple(syms))
    if sol == sp.EmptySet:
        return {"consistent": False, "inferred_dims": {}}, None
    sol = list(sol)[0]
    values = dict(zip(syms, sol))
    resolved = {}
    for q in filler.new:
        v = unknown_vars.get(q.id)
        if not isinstance(v, dict) or not any(isinstance(e, sp.Symbol) and e.name.startswith("dim_") for e in v.values()):
            continue
        dd, det = {}, True
        for d in reg.dims:
            e = sp.sympify(v[d]).xreplace(values)
            if e.free_symbols:
                det = False
                break
            if e != 0:
                dd[d] = int(e) if e.is_integer else fstr(Fraction(int(e.p), int(e.q)))
        inferred[q.id] = dd if det else "undetermined"
        resolved[q.id] = dd if det else None
    return {"consistent": True, "inferred_dims": inferred}, resolved


# ================================================================= F3: exact linear programming
# Chvatal's dictionary method with Bland's rule and one auxiliary variable for phase 1, over Fractions.
# Infeasibility is proved by a Farkas certificate found by a second LP on the dual system.

class Row:
    __slots__ = ("a", "b", "m")

    def __init__(self, a, b, m):
        self.a, self.b, self.m = a, b, m


def _pivot(D, obj, enter, leave):
    const, coefs = D.pop(leave)
    a = coefs.pop(enter)
    new = [-const / a, {k: -v / a for k, v in coefs.items()}]
    new[1][leave] = 1 / a
    for row in list(D.values()) + [obj]:
        c = row[1].pop(enter, None)
        if c is None:
            continue
        row[0] += c * new[0]
        for k, v in new[1].items():
            w = row[1].get(k, 0) + c * v
            if w == 0:
                row[1].pop(k, None)
            else:
                row[1][k] = w
    D[enter] = new


def _bland(D, obj):
    while True:
        enter = min((k for k, v in obj[1].items() if v > 0), default=None)
        if enter is None:
            return "optimal"
        leave, best = None, None
        for k in sorted(D):
            a = D[k][1].get(enter, 0)
            if a < 0:
                ratio = D[k][0] / -a
                if best is None or ratio < best:
                    best, leave = ratio, k
        if leave is None:
            return "unbounded"
        _pivot(D, obj, enter, leave)


def lp_max(A, b, c):
    """maximize c.x subject to A x <= b, x free. Returns (status, value, x)."""
    m, n = len(A), len(c)
    D = {}
    for i in range(m):
        coefs = {0: Fraction(1)}
        for j in range(n):
            a = Fraction(A[i][j])
            if a != 0:
                coefs[1 + j] = -a
                coefs[1 + n + j] = a
        D[2 * n + 1 + i] = [Fraction(b[i]), coefs]
    if any(r[0] < 0 for r in D.values()):
        obj = [Fraction(0), {0: Fraction(-1)}]
        leave = min(D, key=lambda k: (D[k][0], k))
        _pivot(D, obj, 0, leave)
        _bland(D, obj)
        if obj[0] < 0:
            return "infeasible", None, None
        if 0 in D:
            const, coefs = D[0]
            k = min(coefs) if coefs else None
            if k is not None:
                _pivot(D, [Fraction(0), {}], k, 0)
            else:
                D.pop(0)
    for row in D.values():
        row[1].pop(0, None)
    obj = [Fraction(0), {}]

    def add(var, w):
        if var in D:
            obj[0] += w * D[var][0]
            for k, v in D[var][1].items():
                obj[1][k] = obj[1].get(k, 0) + w * v
        else:
            obj[1][var] = obj[1].get(var, 0) + w
    for j in range(n):
        cj = Fraction(c[j])
        if cj != 0:
            add(1 + j, cj)
            add(1 + n + j, -cj)
    obj[1] = {k: v for k, v in obj[1].items() if v != 0 and k != 0}
    if _bland(D, obj) == "unbounded":
        return "unbounded", None, None
    val = {k: r[0] for k, r in D.items()}
    x = [val.get(1 + j, Fraction(0)) - val.get(1 + n + j, Fraction(0)) for j in range(n)]
    return "optimal", obj[0], x


class System:
    def __init__(self, variables, rows):
        self.vars, self.rows = list(variables), rows

    def _ab(self):
        return [[r.a.get(v, Fraction(0)) for v in self.vars] for r in self.rows], [r.b for r in self.rows]

    def feasible(self):
        A, b = self._ab()
        st, _, x = lp_max(A, b, [Fraction(0)] * len(self.vars))
        if st != "infeasible":
            self._point = x
            return True, None
        # Farkas: y >= 0, A^T y = 0, sum y = 1, minimize b.y (negative by Farkas' lemma)
        m, n = len(A), len(self.vars)
        rows, rhs = [], []
        for i in range(m):
            rows.append([Fraction(-1) if k == i else Fraction(0) for k in range(m)])
            rhs.append(Fraction(0))
        for j in range(n):
            col = [A[i][j] for i in range(m)]
            rows.append(col)
            rhs.append(Fraction(0))
            rows.append([-v for v in col])
            rhs.append(Fraction(0))
        rows.append([Fraction(1)] * m)
        rhs.append(Fraction(1))
        rows.append([Fraction(-1)] * m)
        rhs.append(Fraction(-1))
        st, val, y = lp_max(rows, rhs, [-bi for bi in b])
        if st != "optimal" or -val >= 0:
            raise WorldError("internal: no Farkas certificate for an infeasible system")
        mult = {}
        for i, yi in enumerate(y):
            if yi > 0:
                for tag in self.rows[i].m:
                    mult[tag] = mult.get(tag, 0) + yi
        return False, mult

    def point(self):
        if not hasattr(self, "_point"):
            ok, _ = self.feasible()
            if not ok:
                raise WorldError("internal: point of an infeasible system")
        return dict(zip(self.vars, self._point))

    def range(self, c0, coef):
        A, b = self._ab()
        c = [coef.get(v, Fraction(0)) for v in self.vars]
        st_hi, hi, _ = lp_max(A, b, c)
        st_lo, lo, _ = lp_max(A, b, [-x for x in c])
        if st_hi == "infeasible":
            raise WorldError("internal: range over an infeasible system")
        return (None if st_lo == "unbounded" else c0 - lo), (None if st_hi == "unbounded" else c0 + hi)


def linear_form(expr, unknowns):
    """expr affine in unknowns (sympy symbols) with rational coefficients -> (K, {name: coef})."""
    e = sp.together(expr)
    num, den = sp.fraction(e)
    if den.free_symbols & set(unknowns):
        raise WorldError("a new quantity in a denominator (protocol V5)")
    if e.has(sp.zoo, sp.nan, sp.oo):
        raise WorldError("division by zero at an observation state")
    if not unknowns:
        val = sp.nsimplify(e)
        if not val.is_Rational or val.has(sp.zoo, sp.nan):
            raise WorldError("an observation state leaves a name without a value")
        return Fraction(int(val.p), int(val.q)), {}
    poly = sp.Poly(sp.expand(num), *unknowns)
    if poly.total_degree() > 1:
        raise WorldError("a filled law that is not affine in its new quantities (protocol V5)")
    den = sp.nsimplify(den)
    coef = {}
    for u in unknowns:
        c = poly.coeff_monomial(u) / den
        c = sp.nsimplify(c)
        if c.free_symbols:
            raise WorldError("an observation state leaves a name without a value")
        if not c.is_Rational:
            raise WorldError("division by zero at a state")
        if c != 0:
            coef[u.name] = Fraction(int(c.p), int(c.q))
    k0 = poly.coeff_monomial(1) / den
    k0 = sp.nsimplify(k0)
    if k0.free_symbols:
        raise WorldError("an observation state leaves a name without a value")
    if not k0.is_Rational:
        raise WorldError("division by zero at a state")
    return Fraction(int(k0.p), int(k0.q)), coef


def obs_substitution(world, filler, obs, dom, k):
    """Values for the names at one observation (protocol 2.6). Returns (subs, unknown symbols)."""
    sub = {}
    consts = world.constants()
    for nm, v in consts.items():
        sub[filler.S[nm]] = to_rat(v)
    for nm, v in obs["state"].items():
        if nm in filler.S:
            sub[filler.S[nm]] = to_rat(v)
    unknowns = []
    present = {z.name for z in filler.expr.free_symbols}
    for q in filler.new:
        if not any(nm in present for nm in q.names):
            continue
        if dom == "old":
            ov = q.raw["old_value"]
            if ov == "same":
                for nm in q.names:
                    if nm in present:
                        s = sp.Symbol(nm)
                        sub[filler.S[nm]] = s
                        unknowns.append(s)
            else:
                vals = ov if isinstance(ov, list) else [ov] * q.n
                for nm, v in zip(q.names, vals):
                    sub[filler.S[nm]] = to_rat(frac(v))
        else:
            for nm in q.names:
                if nm not in present:
                    continue
                s = sp.Symbol(nm if q.value == UNKNOWN else f"{nm}@{k}")
                sub[filler.S[nm]] = s
                unknowns.append(s)
    return sub, unknowns


def f3_system(world, filler):
    rows, variables_c, variables_v = [], [], []
    forms = {}
    for dom, lst in (("old", world.old), ("new", world.newobs)):
        for k, o in enumerate(lst):
            sub, unk = obs_substitution(world, filler, o, dom, k)
            e = filler.expr.xreplace(sub)
            K, a = linear_form(e, unk)
            forms[(dom, k)] = (K, a)
            for s in unk:
                bucket = variables_v if "@" in s.name else variables_c
                if s.name not in bucket:
                    bucket.append(s.name)
            v, d = o["value"], o["prec"]
            rows.append(Row(dict(a), v + d - K, {(dom, k, "upper"): Fraction(1)}))
            rows.append(Row({u: -c for u, c in a.items()}, -(v - d - K), {(dom, k, "lower"): Fraction(1)}))
    variables = variables_v + sorted(variables_c)
    return System(variables, rows), forms


def f3(world, filler):
    system, forms = f3_system(world, filler)
    ok, mult = system.feasible()
    if ok:
        pt = system.point()
        return {"holds": True, "point": {v: fstr(pt[v]) for v in system.vars}}, system, forms
    cert = [{"obs": t[0], "k": t[1], "side": t[2], "y": fstr(y)} for t, y in sorted(mult.items()) if y != 0]
    return {"holds": False, "farkas": cert}, system, forms


def zero_report(world, filler, f3res, system):
    """Protocol 2.6, the zero-effect report (one label per old observation)."""
    sub_abs = {}
    for q in filler.new:
        ov = q.raw["old_value"]
        if ov != "same":
            vals = ov if isinstance(ov, list) else [ov] * q.n
            for nm, v in zip(q.names, vals):
                sub_abs[filler.S[nm]] = to_rat(frac(v))
    absent = sp.cancel(sp.together(filler.expr.xreplace(sub_abs) - world.law_expr)) == 0
    labels = []
    for k, o in enumerate(world.old):
        if absent:
            labels.append("absent")
            continue
        sub, unk = obs_substitution(world, filler, o, "old", k)
        e = (filler.expr - world.law_expr).xreplace(sub)
        K, a = linear_form(e, unk)
        if K == 0 and not a:
            labels.append("zero_for_any_value")
            continue
        if not f3res["holds"]:
            labels.append("n/a")
            continue
        lo, hi = system.range(K, a)
        d = o["prec"]
        labels.append("below_precision" if lo is not None and hi is not None and -d <= lo and hi <= d else "visible")
    return labels


# ================================================================= the card and the verdict

def verdict_of(f1res, f2res, f3res):
    if not f1res["consistent"]:
        return "INVALID", [{"item": "F1"}]
    reason = []
    if not f3res["holds"]:
        reason.append({"item": "F3"})
    reason += [{"item": "F2", "transformation": t} for t, r in f2res.items() if r["status"] == "changed"]
    if reason:
        return "ANOTHER_LAW", reason
    cond = [{"item": "F2", "transformation": t} for t, r in f2res.items() if r["status"] == "conditional"]
    if cond:
        return "CONDITIONAL", cond
    return "SAME_LAW_NEW_STATE", []


def decisive_branches(world, filler, f2res):
    out = []
    for t, r in f2res.items():
        if r["status"] != "conditional":
            continue
        meas = []
        for u in r["matters"]:
            qid = u.rsplit(":", 1)[0]
            q = next((x for x in filler.new if x.id == qid), None)
            if q is not None:
                inst = q.raw["route"]
            else:
                inst = world.reg.anchor_instrument(world.qty[qid].meaning)
            meas.append({"unknown": u, "instrument": inst})
        out.append({"transformation": t, "measure": meas})
    return out


def card(world, filler):
    f1res, dims_resolved = f1(world, filler)
    f2res = {t: f2_transformation(world, filler, t, ActionRule("procedure")) for t in world.transformations}
    f3res, system, forms = f3(world, filler)
    verdict, reason = verdict_of(f1res, f2res, f3res)
    out = {"verdict": verdict, "reason": reason, "F1": f1res, "F2": f2res, "F3": f3res,
           "zero_report": zero_report(world, filler, f3res, system)}
    if verdict == "CONDITIONAL":
        out["decisive"] = decisive_branches(world, filler, f2res)
    return out, f1res, f3res, system, dims_resolved


# ================================================================= several fillers: decisive states

def predicted_interval(world, filler, system, state):
    sub = {filler.S[nm]: to_rat(v) for nm, v in world.constants().items()}
    for nm, v in state.items():
        sub[filler.S[nm]] = to_rat(v)
    unk = []
    present = {z.name for z in filler.expr.free_symbols}
    for q in filler.new:
        for nm in q.names:
            if nm not in present:
                continue
            s = sp.Symbol(nm)
            sub[filler.S[nm]] = s
            unk.append(s)
    e = filler.expr.xreplace(sub)
    try:
        K, a = linear_form(e, unk)
        return system.range(K, a)
    except (WorldError, ZeroDivisionError):
        return None


def gap(I, J):
    if None in I or None in J:
        return None
    if I[1] < J[0]:
        return J[0] - I[1]
    if J[1] < I[0]:
        return I[0] - J[1]
    return Fraction(0)


def variable_names(world, fillers):
    names = set()
    for f in fillers:
        for s in f.expr.free_symbols:
            q, _ = f.name_qty[s.name]
            if not q.new and q.value == "var" and s.name != world.y:
                names.add(s.name)
    return sorted(names)


def candidate_states(world, names):
    factors = [Fraction(f) for f in (2, 3, 5, 10, -1, -2, 100, 1000, Fraction(1, 2), Fraction(1, 10), -10,
                                     10 ** 4, 10 ** 6, -1000)]
    bases = []
    for o in world.old + world.newobs:
        st = {nm: o["state"][nm] for nm in names if nm in o["state"]}
        if len(st) == len(names) and st not in bases:
            bases.append(st)
    for st in bases:
        yield st
    for st in bases:
        for nm in names:
            for fct in factors:
                v = st[nm] * fct if st[nm] != 0 else fct
                new = dict(st)
                new[nm] = v
                yield new
    for st in bases:
        for a, b in itertools.combinations(names, 2):
            for fct in factors:
                new = dict(st)
                new[a] = st[a] * fct if st[a] != 0 else fct
                new[b] = st[b] * fct if st[b] != 0 else fct
                yield new
    for st in bases:
        for fct in factors:
            yield {nm: (v * fct if v != 0 else fct) for nm, v in st.items()}


def decisive_state(world, f1_, s1, f2_, s2):
    names = variable_names(world, [f1_, f2_])
    obs_ids = sorted({o["observer"] for o in world.old + world.newobs},
                     key=lambda i: (frac(world.observers[i]["precision"]), i))
    best = obs_ids[0]
    d = frac(world.observers[best]["precision"])
    for st in candidate_states(world, names):
        I = predicted_interval(world, f1_, s1, st)
        J = predicted_interval(world, f2_, s2, st)
        if I is None or J is None:
            continue
        g = gap(I, J)
        if g is not None and g > 2 * d:
            return {"pair": [f1_.id, f2_.id], "state": {k: fstr(v) for k, v in sorted(st.items())},
                    "observer": best,
                    "intervals": {f1_.id: [fstr(I[0]), fstr(I[1])], f2_.id: [fstr(J[0]), fstr(J[1])]}}
    return None


# ================================================================= baselines

def baseline_verdict(world, filler, mode, f1res, f3res, dims_resolved):
    def dims_of(q):
        if not q.new:
            return q.dims
        if q.dims is not None:
            return q.dims
        if q.meaning != UNKNOWN and world.reg.meaning_dims(q.meaning) is not None:
            return world.reg.meaning_dims(q.meaning)
        return (dims_resolved or {}).get(q.id) or {}
    f2res = {}
    for t in world.transformations:
        if mode == "DERIVE":
            f2res[t] = {"status": f2_derive(world, filler, t)}
        else:
            f2res[t] = f2_transformation(world, filler, t, ActionRule(mode, dims_of), want_proofs=False)
    return verdict_of(f1res, f2res, f3res)[0]


# ================================================================= one world

def run_world(raw, reg):
    try:
        world = World(raw, reg)
    except (WorldError, R.ExprError, KeyError, TypeError, ValueError) as e:
        err = {"error": f"{type(e).__name__}: {e}"}
        return {m: err for m in METHODS}
    out = {m: {"fillers": {}, "world": {"kept": None}, "catalog": reg.catalog} for m in METHODS}
    systems, details = {}, {}
    for f in world.fillers:
        try:
            c, f1res, f3res, system, dims_resolved = card(world, f)
        except (WorldError, R.ExprError, KeyError, TypeError, ValueError, ZeroDivisionError) as e:
            err = {"error": f"{type(e).__name__}: {e}"}
            for m in METHODS:
                out[m]["fillers"][f.id] = err
            continue
        out["procedure"]["fillers"][f.id] = c
        systems[f.id] = system
        details[f.id] = c
        for m in METHODS[1:]:
            try:
                out[m]["fillers"][f.id] = {"verdict": baseline_verdict(world, f, m, f1res, f3res, dims_resolved)}
            except (WorldError, KeyError, TypeError, ValueError, ZeroDivisionError) as e:
                out[m]["fillers"][f.id] = {"error": f"{type(e).__name__}: {e}"}
    if len(world.fillers) >= 2:
        for m in METHODS:
            out[m]["world"]["kept"] = sorted(fid for fid, c in out[m]["fillers"].items()
                                             if c.get("verdict") == "SAME_LAW_NEW_STATE")
        kept = out["procedure"]["world"]["kept"]
        dec = []
        byid = {f.id: f for f in world.fillers}
        for a, b in itertools.combinations(kept, 2):
            try:
                ds = decisive_state(world, byid[a], systems[a], byid[b], systems[b])
            except (WorldError, ZeroDivisionError, ValueError, TypeError, AttributeError):
                ds = None
            dec.append(ds if ds is not None else {"pair": [a, b], "state": None})
        out["procedure"]["world"]["decisive"] = dec
    return out


def world_key(path, raw):
    base = os.path.splitext(os.path.basename(path))[0]
    return base


def run(worlds_dir, out_path):
    reg = Registry()
    results = {}
    for fn in sorted(os.listdir(worlds_dir)):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(worlds_dir, fn)
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
        results[world_key(path, raw)] = run_world(raw, reg)
        print(f"{fn}: " + ", ".join(f"{fid}={c.get('verdict', c.get('error'))}"
                                    for fid, c in results[world_key(path, raw)]["procedure"]["fillers"].items()))
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(results, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(f"wrote {out_path} ({len(results)} worlds)")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "run":
        run(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 3 and sys.argv[1] == "one":
        with open(sys.argv[2], encoding="utf-8") as fh:
            print(json.dumps(run_world(json.load(fh), Registry()), indent=1, sort_keys=True))
    else:
        print(__doc__)
        sys.exit(1)
