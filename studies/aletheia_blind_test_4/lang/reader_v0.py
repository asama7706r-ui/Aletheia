#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Strict reader for the Aletheia description language, version 0.4.

The reader checks FORM only, never truth:
  * every required field is present and no unknown field appears (no defaults;
    an unknown value is written explicitly as "?");
  * every reference resolves;
  * every expression uses only the letters (exact numbers, lowercase names,
    + - * /, integer powers, D(x, t), and = or >= > != where allowed);
  * numbers are exact fractions in lowest terms.
It never judges dimensions, symmetries, laws or fillers: those are kernel verdicts.

Two file types:
  registry  sealed before any world exists: dimensions, floors, kinds, transformations,
            instruments, meaning cards, definitions between meanings, body types.
  world     refers to one registry by id and by the SHA-256 of its canonical form;
            holds bodies (the cast), quantities (each with an owner), relations, laws,
            observers, observations and fillers.
The registry holds TYPES (kind, meaning card, instrument, body type); a world holds
their INSTANCES (quantity, observer, body).

New in v0.2 (coverage check 1, gaps G1, G2, G5):
  * a filler may add bodies (new_bodies); each new body must own a new quantity of
    that filler, and each new quantity must appear in the filler's equation;
  * observations carry their arrival order (epoch), laws the epoch at which they were
    accepted (accepted_at), observers what they were calibrated against;
  * a meaning-reading action may be an n x n matrix on an n-component quantity.
New in v0.3 (decision 11): when a new quantity's meaning is known, its actions must
equal its meaning card's, so a chosen meaning cannot silently decide a freedom.
New in v0.4 (G8): a new quantity states whether it is a variable or an unknown constant
(value), and its value at the old observations is old_value (formerly absent_value).

Usage:
  python reader_v0.py check REGISTRY.json [WORLD.json ...]
  python reader_v0.py canon REGISTRY.json [WORLD.json]
      prints the canonical JSON of the last file and its SHA-256.
Exit code: 0 well-formed, 1 form errors (all listed), 2 usage or I/O error.
Standard library only (Python 3.12).
"""
import hashlib
import json
import re
import sys
from fractions import Fraction

VERSION = "0.4"
UNKNOWN = "?"

NAME_RE = re.compile(r"[a-z][a-z0-9_]*\Z")
DIM_RE = re.compile(r"[A-Z][A-Za-z]*\Z")
FRAC_RE = re.compile(r"-?(0|[1-9][0-9]*)(/[1-9][0-9]*)?\Z")
HEX_RE = re.compile(r"[0-9a-f]{64}\Z")
CATALOG_RE = re.compile(r"[0-9]+(\.[0-9]+)*\Z")

REGISTRY_FIELDS = ["v0", "file", "id", "catalog", "dimensions", "floors", "kinds",
                   "transformations", "instruments", "meanings", "definitions", "body_types"]
WORLD_FIELDS = ["v0", "file", "id", "registry", "registry_sha256", "bodies", "quantities",
                "relations", "laws", "observers", "observations", "fillers"]
FLOOR_FIELDS = ["id", "depends_on", "src"]
KIND_FIELDS = ["id", "floor", "over", "shape", "generators", "relations", "under", "src"]
TRANSFORMATION_FIELDS = ["id", "reads", "src"]
INSTRUMENT_FIELDS = ["id", "unit", "src"]
MEANING_FIELDS = ["id", "kind", "anchor", "conditions", "under", "src"]
DEFINITION_FIELDS = ["id", "eq", "src"]
BODY_TYPE_FIELDS = ["id", "src"]
BODY_FIELDS = ["id", "type", "src"]
QUANTITY_FIELDS = ["id", "meaning", "owner", "dims", "components", "value", "src"]
RELATION_FIELDS = ["id", "eq", "src"]
LAW_FIELDS = ["id", "eq", "accepted_at", "src"]
OBSERVER_FIELDS = ["id", "instrument", "precision", "calibrated_against", "src"]
OBSERVATION_FIELDS = ["id", "observer", "of", "state", "value", "epoch", "src"]
FILLER_FIELDS = ["id", "of", "eq", "new_bodies", "new", "src"]
NEW_BODY_FIELDS = ["id", "type"]
NEW_FIELDS = ["id", "kind", "meaning", "owner", "dims", "components", "value", "old_value", "under", "route"]

STATEMENT_LISTS = {
    "registry": ["floors", "kinds", "transformations", "instruments", "meanings", "definitions", "body_types"],
    "world": ["bodies", "quantities", "relations", "laws", "observers", "observations", "fillers"],
}


class Ctx:
    def __init__(self, label):
        self.label = label
        self.errors = []

    def err(self, path, msg):
        self.errors.append(f"{self.label}:{path}: {msg}")


# ----------------------------------------------------------------- expressions

class ExprError(Exception):
    pass


TOKEN_RE = re.compile(r"\s*(?:(?P<num>[0-9]+)|(?P<name>[A-Za-z_][A-Za-z0-9_]*)|(?P<op>>=|!=|<=|[-+*/^()=>,<]))")
REL_OPS = {"=", ">=", ">", "!="}


def tokenize(s):
    toks, pos = [], 0
    while pos < len(s):
        if s[pos:].strip() == "":
            break
        m = TOKEN_RE.match(s, pos)
        if not m:
            ch = s[pos:].lstrip()[0]
            hint = f" (decimals are not letters in v{VERSION}; write a fraction like 3/2)" if ch == "." else ""
            raise ExprError(f"unknown character {ch!r}{hint}")
        pos = m.end()
        if m.group("num") is not None:
            toks.append(("num", int(m.group("num"))))
        elif m.group("name") is not None:
            toks.append(("name", m.group("name")))
        else:
            op = m.group("op")
            if op in ("<", "<="):
                raise ExprError(f"'{op}' is not a v{VERSION} letter; write the inequality with '>' or '>='")
            toks.append(("op", op))
    return toks


class Parser:
    """Recursive descent over the letters. Returns an AST and the names used."""

    def __init__(self, s):
        self.toks = tokenize(s)
        self.i = 0
        self.names = set()

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else (None, None)

    def take(self):
        t = self.peek()
        self.i += 1
        return t

    def expect_op(self, op):
        t = self.take()
        if t != ("op", op):
            raise ExprError(f"expected '{op}'")

    def relation(self, allowed):
        lhs = self.expr()
        kind, op = self.take()
        if kind != "op" or op not in REL_OPS:
            raise ExprError(f"expected one of {sorted(allowed)}")
        if op not in allowed:
            raise ExprError(f"'{op}' is not allowed here; allowed: {sorted(allowed)}")
        rhs = self.expr()
        if self.i != len(self.toks):
            raise ExprError("unexpected text after the expression (only one relation sign is allowed)")
        return ("rel", op, lhs, rhs)

    def expr(self):
        node = self.term()
        while self.peek() in (("op", "+"), ("op", "-")):
            op = self.take()[1]
            node = ("bin", op, node, self.term())
        return node

    def term(self):
        node = self.unary()
        while self.peek() in (("op", "*"), ("op", "/")):
            op = self.take()[1]
            node = ("bin", op, node, self.unary())
        return node

    def unary(self):
        if self.peek() == ("op", "-"):
            self.take()
            return ("neg", self.unary())
        return self.power()

    def power(self):
        base = self.atom()
        if self.peek() == ("op", "^"):
            self.take()
            paren = False
            if self.peek() == ("op", "("):
                self.take()
                paren = True
            sign = 1
            if self.peek() == ("op", "-"):
                self.take()
                sign = -1
            kind, val = self.take()
            if kind != "num" or (paren and self.peek() != ("op", ")")):
                raise ExprError("powers take an integer exponent only (no names, fractions or decimals)")
            if paren:
                self.expect_op(")")
            return ("pow", base, sign * val)
        return base

    def atom(self):
        kind, val = self.take()
        if kind == "num":
            return ("num", val)
        if kind == "name":
            if val == "D":
                self.expect_op("(")
                a = self.take()
                self.expect_op(",")
                b = self.take()
                self.expect_op(")")
                for t in (a, b):
                    if t[0] != "name" or not NAME_RE.match(t[1]):
                        raise ExprError("D(x, t) takes two lowercase names")
                self.names.update([a[1], b[1]])
                return ("D", a[1], b[1])
            if self.peek() == ("op", "("):
                raise ExprError(f"functions are not letters in v{VERSION} (got '{val}(')")
            if not NAME_RE.match(val):
                raise ExprError(f"names are lowercase letters, digits and '_' ('{val}' is not a v{VERSION} name)")
            self.names.add(val)
            return ("name", val)
        if (kind, val) == ("op", "("):
            node = self.expr()
            self.expect_op(")")
            return node
        raise ExprError("incomplete expression")


PREC = {"+": 1, "-": 1, "*": 2, "/": 2}


def render(node, parent=0, right=False):
    t = node[0]
    if t == "num":
        return str(node[1])
    if t == "name":
        return node[1]
    if t == "D":
        return f"D({node[1]}, {node[2]})"
    if t == "neg":
        s = "-" + render(node[1], 3)
        return f"({s})" if parent > 3 else s
    if t == "pow":
        return f"{render(node[1], 5)}^{node[2]}"
    if t == "bin":
        op, p = node[1], PREC[node[1]]
        sep = f" {op} " if op in "+-" else op
        s = render(node[2], p) + sep + render(node[3], p, right=True)
        need = p < parent or (right and p == parent)
        return f"({s})" if need else s
    if t == "rel":
        return f"{render(node[2])} {node[1]} {render(node[3])}"
    raise ValueError(node)


def check_relation(ctx, s, path, allowed, names):
    """Parse a relation string; check its sign and names. Returns canonical text or None."""
    if not isinstance(s, str):
        ctx.err(path, "must be an expression string")
        return None
    try:
        p = Parser(s)
        ast = p.relation(allowed)
    except ExprError as e:
        ctx.err(path, f"{e} in {s!r}")
        return None
    for n in sorted(p.names - set(names)):
        ctx.err(path, f"unknown name '{n}' in {s!r}")
    return render(ast)


# ----------------------------------------------------------------- small checks

def fields(ctx, obj, path, required):
    if not isinstance(obj, dict):
        ctx.err(path, "must be an object")
        return False
    keys = set(obj)
    for k in sorted(set(required) - keys):
        ctx.err(path, f"missing field '{k}' (v{VERSION} has no defaults; write '?' where unknown is allowed)")
    for k in sorted(keys - set(required)):
        ctx.err(path, f"unknown field '{k}' (not in the v{VERSION} grammar)")
    return True


def check_fraction(ctx, v, path, positive=False):
    if not isinstance(v, str) or not FRAC_RE.match(v):
        ctx.err(path, f"must be an exact fraction string like '7/4' or '-3', got {v!r}")
        return False
    if str(Fraction(v)) != v:
        ctx.err(path, f"fraction must be in lowest terms: write '{Fraction(v)}' not '{v}'")
        return False
    if positive and Fraction(v) <= 0:
        ctx.err(path, "must be > 0")
        return False
    return True


def check_name(ctx, v, path, what="id"):
    if not isinstance(v, str) or not NAME_RE.match(v):
        ctx.err(path, f"{what} must be lowercase letters, digits and '_', starting with a letter; got {v!r}")
        return False
    return True


def check_dims(ctx, v, path, dims_declared):
    if not isinstance(v, dict):
        ctx.err(path, "dims must be an object like {\"L\": 1, \"T\": -1}")
        return
    for k, e in v.items():
        if k not in dims_declared:
            ctx.err(path, f"undeclared dimension '{k}'")
        if not isinstance(e, int) or isinstance(e, bool) or e == 0:
            ctx.err(path, f"exponent of '{k}' must be a nonzero integer, got {e!r}")


def check_src(ctx, v, path, known_ids, seed_only=False):
    if v == "seed":
        return
    if not isinstance(v, str):
        ctx.err(path, f"src must be 'seed' or an id string, got {v!r}")
    elif seed_only:
        ctx.err(path, "src must be 'seed' in a registry")
    elif v not in known_ids:
        ctx.err(path, f"src must be 'seed' or an existing id, got {v!r}")


def ref(ctx, v, path, table, what, allow_unknown=False):
    if allow_unknown and v == UNKNOWN:
        return True
    if not isinstance(v, str) or v not in table:
        ctx.err(path, f"unknown {what} {v!r}")
        return False
    return True


def sid(st):
    """The id of a statement if it is a string, else None (malformed ids are reported elsewhere)."""
    return st.get("id") if isinstance(st, dict) and isinstance(st.get("id"), str) else None


def by_id(lst):
    return {sid(s): s for s in lst if sid(s) is not None}


def size(shape):
    n = 1
    for d in shape:
        n *= d
    return n


def clean_shape(shape):
    """The shape if it is well-formed, else None (errors are reported where the kind is checked)."""
    if isinstance(shape, list) and all(isinstance(d, int) and not isinstance(d, bool) and d >= 1 for d in shape):
        return shape
    return None


def check_action(ctx, v, path, n, shape):
    """A transformation's action on one quantity: a fraction (multiplies every component),
    or an n x n matrix of fractions acting on its n components (only when n >= 2).
    n is None when the kind is unknown."""
    if isinstance(v, list):
        if n is None:
            ctx.err(path, "a matrix action needs a known kind; write a fraction or '?'")
        elif n < 2:
            ctx.err(path, "a matrix action needs a kind with at least 2 components; use a number")
        elif len(v) != n or any(not isinstance(row, list) or len(row) != n for row in v):
            ctx.err(path, f"matrix must be {n}x{n} for shape {shape}")
        else:
            for a, row in enumerate(v):
                for b, e in enumerate(row):
                    check_fraction(ctx, e, f"{path}[{a}][{b}]")
    else:
        check_fraction(ctx, v, path)


def check_old_value(ctx, v, path, kind, n, value):
    """A new quantity's value at the old observations (G8, v0.4): a fraction (or a list of
    n fractions for an n-component kind), 'same' (present all along with its constant value),
    or '?'. With an unknown kind only '0' (the zero of its kind) can be written as a number."""
    if v == UNKNOWN:
        return
    if v == "same":
        if value != UNKNOWN:
            ctx.err(path, "'same' means present all along with its constant value, so it needs value '?'; "
                          "a variable has no single value to carry back")
        return
    if kind == UNKNOWN:
        if v != "0":
            ctx.err(path, "with kind '?' the old value can only be '0' (the zero of its kind), 'same' or '?'")
        return
    if n is None:           # the kind itself is invalid; reported where the kind is checked
        return
    if n == 1:
        check_fraction(ctx, v, path)
    elif not isinstance(v, list) or len(v) != n:
        ctx.err(path, f"its kind has {n} components; write a list of {n} fractions, 'same' or '?'")
    else:
        for j, e in enumerate(v):
            check_fraction(ctx, e, f"{path}[{j}]")


def check_epoch(ctx, v, path):
    if not isinstance(v, int) or isinstance(v, bool) or v < 0:
        ctx.err(path, f"must be a non-negative integer (an arrival order, not a time), got {v!r}")


def report_cycles(graph, report):
    """Depth-first search; calls report(path) once for each cycle entry found."""
    state = {}

    def visit(n, stack):
        if state.get(n) == 1:
            report(stack + [n])
            return
        if state.get(n) == 2:
            return
        state[n] = 1
        for m in graph.get(n, []):
            visit(m, stack + [n])
        state[n] = 2

    for n in graph:
        visit(n, [])


def names_in(s):
    """The names used by a well-formed equation string, or None if it does not parse."""
    if not isinstance(s, str):
        return None
    try:
        p = Parser(s)
        p.relation({"="})
    except ExprError:
        return None
    return p.names


def statements(ctx, doc, key, path):
    lst = doc.get(key)
    if not isinstance(lst, list):
        ctx.err(f"{path}.{key}", "must be a list (write [] if empty)")
        return []
    return lst


def collect_ids(ctx, doc, kind, seen):
    for key in STATEMENT_LISTS[kind]:
        lst = doc.get(key)
        for i, st in enumerate(lst if isinstance(lst, list) else []):
            if isinstance(st, dict) and isinstance(st.get("id"), str):
                this = st["id"]
                if this in seen:
                    ctx.err(f"{key}[{i}].id", f"duplicate id '{this}'")
                seen.add(this)


# ----------------------------------------------------------------- registry

def check_registry(doc, label="registry"):
    ctx = Ctx(label)
    if not fields(ctx, doc, "$", REGISTRY_FIELDS):
        return ctx, None
    if doc.get("v0") != VERSION:
        ctx.err("$.v0", f"version must be '{VERSION}', got {doc.get('v0')!r}")
    if doc.get("file") != "registry":
        ctx.err("$.file", "must be 'registry'")
    check_name(ctx, doc.get("id"), "$.id")
    if not isinstance(doc.get("catalog"), str) or not CATALOG_RE.match(doc.get("catalog", "")):
        ctx.err("$.catalog", "catalog version must look like '1' or '1.2'")
    dims = doc.get("dimensions")
    if not isinstance(dims, list) or any(not isinstance(d, str) or not DIM_RE.match(d) for d in dims):
        ctx.err("$.dimensions", "must be a list of base-dimension names like 'L', 'T', 'M'")
        dims = []
    elif len(set(dims)) != len(dims):
        ctx.err("$.dimensions", "duplicate dimension")
    seen = set()
    collect_ids(ctx, doc, "registry", seen)

    floors = statements(ctx, doc, "floors", "$")
    kinds = statements(ctx, doc, "kinds", "$")
    trans = statements(ctx, doc, "transformations", "$")
    insts = statements(ctx, doc, "instruments", "$")
    btypes = statements(ctx, doc, "body_types", "$")
    means = statements(ctx, doc, "meanings", "$")
    defs = statements(ctx, doc, "definitions", "$")
    floor_ids = set(by_id(floors))
    kind_by_id = by_id(kinds)
    t_by_id = by_id(trans)
    inst_ids = set(by_id(insts))
    btype_ids = set(by_id(btypes))
    meaning_ids = set(by_id(means))
    def_by_id = by_id(defs)
    kind_reading = sorted(t for t, v in t_by_id.items() if isinstance(v, dict) and v.get("reads") == "kind")
    meaning_reading = sorted(t for t, v in t_by_id.items() if isinstance(v, dict) and v.get("reads") == "meaning")

    graph = {}
    for i, f in enumerate(floors):
        p = f"floors[{i}]"
        fields(ctx, f, p, FLOOR_FIELDS)
        if not isinstance(f, dict):
            continue
        check_name(ctx, f.get("id"), p + ".id")
        deps = f.get("depends_on")
        if not isinstance(deps, list):
            ctx.err(p + ".depends_on", "must be a list of floor ids (write [] if none)")
            deps = []
        for d in deps:
            ref(ctx, d, p + ".depends_on", floor_ids, "floor")
        if sid(f) is not None:
            graph[sid(f)] = [d for d in deps if isinstance(d, str) and d in floor_ids]
        check_src(ctx, f.get("src"), p + ".src", set(), seed_only=True)
    # cycles in floor order (the tower order is computed from dependencies, blueprint 2.10)
    report_cycles(graph, lambda cyc: ctx.err("floors", f"dependency cycle: {' -> '.join(cyc)}"))

    for i, t in enumerate(trans):
        p = f"transformations[{i}]"
        fields(ctx, t, p, TRANSFORMATION_FIELDS)
        if not isinstance(t, dict):
            continue
        check_name(ctx, t.get("id"), p + ".id")
        if t.get("reads") not in ("kind", "meaning", "cast"):
            ctx.err(p + ".reads", "must be 'kind', 'meaning' or 'cast' (blueprint 2.11; 'cast' = the bodies of a world, F5)")
        check_src(ctx, t.get("src"), p + ".src", set(), seed_only=True)

    canon_kinds = {}
    for i, k in enumerate(kinds):
        p = f"kinds[{i}]"
        fields(ctx, k, p, KIND_FIELDS)
        if not isinstance(k, dict):
            continue
        check_name(ctx, k.get("id"), p + ".id")
        ref(ctx, k.get("floor"), p + ".floor", floor_ids, "floor")
        if k.get("over") != "fractions":
            ctx.err(p + ".over", f"v{VERSION} knows one number system: 'fractions'")
        shape = k.get("shape")
        if not isinstance(shape, list) or any(not isinstance(d, int) or isinstance(d, bool) or d < 1 for d in shape):
            ctx.err(p + ".shape", "must be a list of positive integers ([] for a single number)")
            shape = []
        n = size(shape)
        gens = k.get("generators")
        if not isinstance(gens, list):
            ctx.err(p + ".generators", "must be a list (write [] if none)")
            gens = []
        for g in gens:
            check_name(ctx, g, p + ".generators", "generator")
        if len(set(map(str, gens))) != len(gens):
            ctx.err(p + ".generators", "duplicate generator")
        rels = k.get("relations")
        canon_rels = []
        if not isinstance(rels, list):
            ctx.err(p + ".relations", "must be a list (write [] if none)")
            rels = []
        for j, r in enumerate(rels):
            c = check_relation(ctx, r, f"{p}.relations[{j}]", {"="}, gens)
            canon_rels.append(c)
        under = k.get("under")
        if not isinstance(under, dict):
            ctx.err(p + ".under", "must be an object with one action per kind-reading transformation")
            under = {}
        for t in kind_reading:
            if t not in under:
                ctx.err(p + ".under", f"missing action for transformation '{t}' (write '?' if unknown)")
        for t, v in under.items():
            q = f"{p}.under.{t}"
            if t not in kind_reading:
                ctx.err(q, f"'{t}' is not a kind-reading transformation")
                continue
            if v == UNKNOWN:
                continue
            check_action(ctx, v, q, n, shape)
        check_src(ctx, k.get("src"), p + ".src", set(), seed_only=True)
        canon_kinds[sid(k)] = canon_rels

    for i, b in enumerate(btypes):
        p = f"body_types[{i}]"
        fields(ctx, b, p, BODY_TYPE_FIELDS)
        if not isinstance(b, dict):
            continue
        check_name(ctx, b.get("id"), p + ".id")
        check_src(ctx, b.get("src"), p + ".src", set(), seed_only=True)

    for i, s in enumerate(insts):
        p = f"instruments[{i}]"
        fields(ctx, s, p, INSTRUMENT_FIELDS)
        if not isinstance(s, dict):
            continue
        check_name(ctx, s.get("id"), p + ".id")
        check_dims(ctx, s.get("unit"), p + ".unit", dims)
        check_src(ctx, s.get("src"), p + ".src", set(), seed_only=True)

    canon_defs = {}
    for i, d in enumerate(defs):
        p = f"definitions[{i}]"
        fields(ctx, d, p, DEFINITION_FIELDS)
        if not isinstance(d, dict):
            continue
        check_name(ctx, d.get("id"), p + ".id")
        canon_defs[sid(d)] = check_relation(ctx, d.get("eq"), p + ".eq", {"="}, meaning_ids)
        check_src(ctx, d.get("src"), p + ".src", set(), seed_only=True)

    def mentions(def_id, meaning):
        d = def_by_id.get(def_id)
        if not isinstance(meaning, str) or not isinstance(d, dict) or not isinstance(d.get("eq"), str):
            return False
        try:
            pr = Parser(d["eq"])
            pr.relation({"="})
            return meaning in pr.names
        except (ExprError, AttributeError):
            return False

    canon_conditions = {}
    for i, m in enumerate(means):
        p = f"meanings[{i}]"
        fields(ctx, m, p, MEANING_FIELDS)
        if not isinstance(m, dict):
            continue
        mid = m.get("id")
        check_name(ctx, mid, p + ".id")
        mshape = None
        if ref(ctx, m.get("kind"), p + ".kind", kind_by_id, "kind") and isinstance(kind_by_id[m["kind"]], dict):
            mshape = clean_shape(kind_by_id[m["kind"]].get("shape"))
        mn = size(mshape) if mshape is not None else None
        anchor = m.get("anchor")
        if not isinstance(anchor, dict) or len(anchor) != 1:
            ctx.err(p + ".anchor", "anchor must be exactly one of {\"instrument\": id}, {\"seed\": \"human\"}, {\"derived\": definition id}")
        else:
            (ak, av), = anchor.items()
            if ak == "instrument":
                ref(ctx, av, p + ".anchor.instrument", inst_ids, "instrument")
            elif ak == "seed":
                if av != "human":
                    ctx.err(p + ".anchor.seed", "must be 'human'")
            elif ak == "derived":
                if ref(ctx, av, p + ".anchor.derived", def_by_id, "definition") and not mentions(av, mid):
                    ctx.err(p + ".anchor.derived", f"definition '{av}' does not mention meaning '{mid}'")
            else:
                ctx.err(p + ".anchor", f"unknown anchor type '{ak}' (instrument, seed or derived)")
        conds = m.get("conditions")
        canon_c = []
        if not isinstance(conds, list):
            ctx.err(p + ".conditions", "must be a list (write [] if none)")
            conds = []
        for j, c in enumerate(conds):
            canon_c.append(check_relation(ctx, c, f"{p}.conditions[{j}]", {">=", ">", "!="}, meaning_ids))
        canon_conditions[sid(m)] = canon_c
        under = m.get("under")
        if not isinstance(under, dict):
            ctx.err(p + ".under", "must be an object with one action per meaning-reading transformation")
            under = {}
        for t in meaning_reading:
            if t not in under:
                ctx.err(p + ".under", f"missing action for transformation '{t}' (write '?' if unknown)")
        for t, v in under.items():
            q = f"{p}.under.{t}"
            if t not in meaning_reading:
                ctx.err(q, f"'{t}' is not a meaning-reading transformation")
                continue
            if v == UNKNOWN:
                continue
            if isinstance(v, dict):
                if list(v) != ["derived"]:
                    ctx.err(q, "an object action must be {\"derived\": definition id}")
                elif ref(ctx, v["derived"], q + ".derived", def_by_id, "definition") and not mentions(v["derived"], mid):
                    ctx.err(q, f"definition '{v['derived']}' does not mention meaning '{mid}'")
            else:
                check_action(ctx, v, q, mn, mshape)
        check_src(ctx, m.get("src"), p + ".src", set(), seed_only=True)

    if ctx.errors:
        return ctx, None
    info = {
        "id": doc["id"], "dims": set(dims), "kinds": kind_by_id, "meanings": {m["id"]: m for m in means},
        "instruments": inst_ids, "meaning_reading": meaning_reading, "ids": seen,
        "body_types": btype_ids,
        "canon": canonical_registry(doc, canon_kinds, canon_defs, canon_conditions),
    }
    return ctx, info


def canonical_registry(doc, canon_kinds, canon_defs, canon_conditions):
    out = json.loads(json.dumps(doc))
    out["dimensions"] = sorted(out["dimensions"])
    for k in out["kinds"]:
        k["relations"] = sorted(canon_kinds[k["id"]])
    for d in out["definitions"]:
        d["eq"] = canon_defs[d["id"]]
    for m in out["meanings"]:
        m["conditions"] = sorted(canon_conditions[m["id"]])
    for f in out["floors"]:
        f["depends_on"] = sorted(f["depends_on"])
    for key in STATEMENT_LISTS["registry"]:
        out[key] = sorted(out[key], key=lambda s: s["id"])
    return out


# ----------------------------------------------------------------- world

def check_world(doc, reg, label="world"):
    ctx = Ctx(label)
    if not fields(ctx, doc, "$", WORLD_FIELDS):
        return ctx, None
    if doc.get("v0") != VERSION:
        ctx.err("$.v0", f"version must be '{VERSION}', got {doc.get('v0')!r}")
    if doc.get("file") != "world":
        ctx.err("$.file", "must be 'world'")
    check_name(ctx, doc.get("id"), "$.id")
    if doc.get("registry") != reg["id"]:
        ctx.err("$.registry", f"must name the registry '{reg['id']}'")
    reg_sha = sha256_of(reg["canon"])
    if not isinstance(doc.get("registry_sha256"), str) or not HEX_RE.match(doc.get("registry_sha256", "")):
        ctx.err("$.registry_sha256", "must be the 64-hex SHA-256 of the registry's canonical form")
    elif doc["registry_sha256"] != reg_sha:
        ctx.err("$.registry_sha256", "registry_sha256 does not match the registry given to the reader")

    seen = set()
    collect_ids(ctx, doc, "world", seen)
    for clash in sorted(seen & reg["ids"]):
        ctx.err("$", f"id '{clash}' is already used in the registry")

    quants = statements(ctx, doc, "quantities", "$")
    rels = statements(ctx, doc, "relations", "$")
    laws = statements(ctx, doc, "laws", "$")
    obsrs = statements(ctx, doc, "observers", "$")
    bodies = statements(ctx, doc, "bodies", "$")
    obss = statements(ctx, doc, "observations", "$")
    fills = statements(ctx, doc, "fillers", "$")
    law_ids = set(by_id(laws))
    obs_by_id = by_id(obsrs)
    body_ids = set(by_id(bodies))
    for i, b in enumerate(bodies):
        p = f"bodies[{i}]"
        fields(ctx, b, p, BODY_FIELDS)
        if not isinstance(b, dict):
            continue
        if check_name(ctx, b.get("id"), p + ".id") and b.get("id") == "world":
            ctx.err(p + ".id", "'world' is reserved for quantities that belong to the whole world")
        ref(ctx, b.get("type"), p + ".type", reg["body_types"], "body type")
        check_src(ctx, b.get("src"), p + ".src", seen | reg["ids"])

    def check_owner(v, path, allow_unknown=False, new_bodies=frozenset()):
        if v == "world" or (allow_unknown and v == UNKNOWN):
            return
        if not isinstance(v, str) or (v not in body_ids and v not in new_bodies):
            extra = " or '?'" if allow_unknown else ""
            ctx.err(path, f"unknown owner {v!r} (must be a body id or 'world'{extra})")

    scalar_names, tensor_ids = set(), set()
    for i, q in enumerate(quants):
        p = f"quantities[{i}]"
        fields(ctx, q, p, QUANTITY_FIELDS)
        if not isinstance(q, dict):
            continue
        check_name(ctx, q.get("id"), p + ".id")
        check_owner(q.get("owner"), p + ".owner")
        n = 1
        if ref(ctx, q.get("meaning"), p + ".meaning", reg["meanings"], "meaning"):
            kind = reg["kinds"][reg["meanings"][q["meaning"]]["kind"]]
            n = size(kind["shape"])
        check_dims(ctx, q.get("dims"), p + ".dims", reg["dims"])
        comps = q.get("components")
        if not isinstance(comps, list):
            ctx.err(p + ".components", "must be a list of component names ([] for a single number)")
            comps = []
        if n == 1 and comps:
            ctx.err(p + ".components", "a single-number quantity has components []")
        if n > 1 and len(comps) != n:
            ctx.err(p + ".components", f"its kind has {n} components; list {n} names")
        for c in comps:
            if check_name(ctx, c, p + ".components", "component name"):
                if c in seen or c in reg["ids"]:
                    ctx.err(p + ".components", f"duplicate id '{c}'")
                seen.add(c)
        val = q.get("value")
        if val in ("var", UNKNOWN):
            pass
        elif isinstance(val, list):
            if n == 1 or len(val) != n:
                ctx.err(p + ".value", f"a constant value list needs exactly {n} entries for a {n}-component kind")
            for j, e in enumerate(val):
                check_fraction(ctx, e, f"{p}.value[{j}]")
        else:
            if n > 1:
                ctx.err(p + ".value", "a multi-component constant needs a list of values")
            else:
                check_fraction(ctx, val, p + ".value")
        if sid(q) is None:
            continue
        if n == 1:
            scalar_names.add(sid(q))
        else:
            tensor_ids.add(sid(q))
            scalar_names.update(c for c in comps if isinstance(c, str))
    all_ids = seen | reg["ids"]
    for i, q in enumerate(quants):
        if isinstance(q, dict):
            check_src(ctx, q.get("src"), f"quantities[{i}].src", all_ids)

    def check_eq(s, path, names):
        bad = [t for t in tensor_ids if isinstance(s, str) and re.search(rf"\b{re.escape(t)}\b", s)]
        for t in bad:
            ctx.err(path, f"'{t}' is a tensor quantity; in v{VERSION} expressions use its component names")
        return check_relation(ctx, s, path, {"="}, names) if not bad else None

    canon_eq = {}
    for key, lst, req in (("relations", rels, RELATION_FIELDS), ("laws", laws, LAW_FIELDS)):
        for i, r in enumerate(lst):
            p = f"{key}[{i}]"
            fields(ctx, r, p, req)
            if not isinstance(r, dict):
                continue
            check_name(ctx, r.get("id"), p + ".id")
            canon_eq[sid(r)] = check_eq(r.get("eq"), p + ".eq", scalar_names)
            if key == "laws":
                check_epoch(ctx, r.get("accepted_at"), p + ".accepted_at")
            check_src(ctx, r.get("src"), p + ".src", all_ids)

    calibration = {}
    for i, o in enumerate(obsrs):
        p = f"observers[{i}]"
        fields(ctx, o, p, OBSERVER_FIELDS)
        if not isinstance(o, dict):
            continue
        check_name(ctx, o.get("id"), p + ".id")
        ref(ctx, o.get("instrument"), p + ".instrument", reg["instruments"], "instrument")
        check_fraction(ctx, o.get("precision"), p + ".precision", positive=True)
        cal = o.get("calibrated_against")
        if cal != UNKNOWN:
            if not isinstance(cal, list):
                ctx.err(p + ".calibrated_against", "must be a list of observer ids ([] if calibrated against no observer of this world) or '?'")
                cal = []
            for c in cal:
                if c == sid(o):
                    ctx.err(p + ".calibrated_against", f"observer '{c}' cannot be calibrated against itself")
                else:
                    ref(ctx, c, p + ".calibrated_against", obs_by_id, "observer")
            if len(set(map(repr, cal))) != len(cal):
                ctx.err(p + ".calibrated_against", "duplicate observer")
            if sid(o) is not None:
                calibration[sid(o)] = [c for c in cal if isinstance(c, str) and c in obs_by_id and c != sid(o)]
        check_src(ctx, o.get("src"), p + ".src", all_ids)
    # calibration roots must not loop: a reference cannot rest on what rests on it (blueprint 4.1)
    report_cycles(calibration, lambda cyc: ctx.err("observers", f"calibration cycle: {' -> '.join(cyc)}"))

    for i, o in enumerate(obss):
        p = f"observations[{i}]"
        fields(ctx, o, p, OBSERVATION_FIELDS)
        if not isinstance(o, dict):
            continue
        check_name(ctx, o.get("id"), p + ".id")
        ref(ctx, o.get("observer"), p + ".observer", obs_by_id, "observer")
        if not isinstance(o.get("of"), str) or o.get("of") not in scalar_names:
            ctx.err(p + ".of", f"must name a single-number quantity or a component, got {o.get('of')!r}")
        st = o.get("state")
        if not isinstance(st, dict):
            ctx.err(p + ".state", "must be an object {name: fraction} (write {} if none)")
            st = {}
        for k, v in st.items():
            if k not in scalar_names:
                ctx.err(p + ".state", f"unknown name '{k}'")
            if k == o.get("of"):
                ctx.err(p + ".state", f"the observed '{k}' cannot also be part of the state")
            check_fraction(ctx, v, f"{p}.state.{k}")
        check_fraction(ctx, o.get("value"), p + ".value")
        check_epoch(ctx, o.get("epoch"), p + ".epoch")
        if o.get("src") != o.get("observer"):
            ctx.err(p + ".src", "the src of an observation must be its observer")

    for i, f in enumerate(fills):
        p = f"fillers[{i}]"
        fields(ctx, f, p, FILLER_FIELDS)
        if not isinstance(f, dict):
            continue
        check_name(ctx, f.get("id"), p + ".id")
        ref(ctx, f.get("of"), p + ".of", law_ids, "law")
        taken = set()       # ids local to this filler: new bodies, new quantities, their components
        local = set()       # names the filler's eq may use besides the world's
        new_bodies = []
        nbs = f.get("new_bodies")
        if not isinstance(nbs, list):
            ctx.err(p + ".new_bodies", "must be a list of new bodies (write [] if none)")
            nbs = []
        for j, nb in enumerate(nbs):
            q = f"{p}.new_bodies[{j}]"
            fields(ctx, nb, q, NEW_BODY_FIELDS)
            if not isinstance(nb, dict):
                continue
            bid = nb.get("id")
            if check_name(ctx, bid, q + ".id"):
                if bid == "world":
                    ctx.err(q + ".id", "'world' is reserved for quantities that belong to the whole world")
                elif bid in all_ids or bid in taken:
                    ctx.err(q + ".id", f"duplicate id '{bid}'")
                else:
                    new_bodies.append(bid)
                taken.add(bid)
            ref(ctx, nb.get("type"), q + ".type", reg["body_types"], "body type")
        news = f.get("new")
        if not isinstance(news, list):
            ctx.err(p + ".new", "must be a list of new quantities (write [] if none)")
            news = []
        owners, contributes = set(), []
        for j, nq in enumerate(news):
            q = f"{p}.new[{j}]"
            fields(ctx, nq, q, NEW_FIELDS)
            if not isinstance(nq, dict):
                continue
            nid = nq.get("id")
            if check_name(ctx, nid, q + ".id"):
                if nid in all_ids or nid in taken:
                    ctx.err(q + ".id", f"duplicate id '{nid}'")
                taken.add(nid)
            kind = nq.get("kind")
            n, nshape = None, None
            if ref(ctx, kind, q + ".kind", reg["kinds"], "kind", allow_unknown=True) and kind != UNKNOWN:
                nshape = reg["kinds"][kind]["shape"]
                n = size(nshape)
            mean = nq.get("meaning")
            if ref(ctx, mean, q + ".meaning", reg["meanings"], "meaning", allow_unknown=True) and mean != UNKNOWN:
                if kind not in (UNKNOWN, None) and reg["meanings"][mean]["kind"] != kind:
                    ctx.err(q + ".meaning", f"meaning '{mean}' has kind '{reg['meanings'][mean]['kind']}', not '{kind}'")
            if nq.get("dims") != UNKNOWN:
                check_dims(ctx, nq.get("dims"), q + ".dims", reg["dims"])
            comps = nq.get("components")
            names = set()   # the names by which this new quantity can enter the eq
            if kind == UNKNOWN:
                if comps != UNKNOWN:
                    ctx.err(q + ".components", "components must be '?' when the kind is '?'")
                if isinstance(nid, str):
                    names.add(nid)
            elif n is not None:
                if not isinstance(comps, list):
                    ctx.err(q + ".components", "must be a list ([] for a single number)")
                elif n == 1:
                    if comps:
                        ctx.err(q + ".components", "a single-number quantity has components []")
                    if isinstance(nid, str):
                        names.add(nid)
                elif len(comps) != n:
                    ctx.err(q + ".components", f"its kind has {n} components; list {n} names")
                else:
                    for c in comps:
                        if check_name(ctx, c, q + ".components", "component name"):
                            if c in all_ids or c in taken:
                                ctx.err(q + ".components", f"duplicate id '{c}'")
                            taken.add(c)
                            names.add(c)
            local |= names
            contributes.append((q, nid, names))
            under = nq.get("under")
            if not isinstance(under, dict):
                ctx.err(q + ".under", "must be an object with one action per meaning-reading transformation")
                under = {}
            for t in reg["meaning_reading"]:
                if t not in under:
                    ctx.err(q + ".under", f"missing action for transformation '{t}' (write '?' if unknown)")
            card = reg["meanings"].get(mean) if isinstance(mean, str) and mean != UNKNOWN else None
            for t, v in under.items():
                if t not in reg["meaning_reading"]:
                    ctx.err(f"{q}.under.{t}", f"'{t}' is not a meaning-reading transformation")
                elif card is not None:
                    # decision 11 (2026-10-06): a known meaning already fixes the action, so the
                    # filler must say so openly; otherwise choosing a meaning would silently decide a freedom
                    if v != card["under"][t]:
                        ctx.err(f"{q}.under.{t}", f"must match its meaning card '{mean}' ({card['under'][t]!r}); "
                                                  "write the card's action, or set the meaning to '?'")
                elif v != UNKNOWN:
                    check_action(ctx, v, f"{q}.under.{t}", n, nshape)
            val = nq.get("value")
            if val not in ("var", UNKNOWN):
                ctx.err(q + ".value", f"must be 'var' (a variable) or '?' (an unknown constant), got {val!r}")
            check_old_value(ctx, nq.get("old_value"), q + ".old_value", kind, n, val)
            ref(ctx, nq.get("route"), q + ".route", reg["instruments"], "instrument", allow_unknown=True)
            owner = nq.get("owner")
            check_owner(owner, q + ".owner", allow_unknown=True, new_bodies=set(new_bodies))
            if isinstance(owner, str):
                owners.add(owner)
        canon_eq[sid(f)] = check_eq(f.get("eq"), p + ".eq", scalar_names | local)
        # form side of "necessary" (decision on G1, 2026-10-06): whatever a filler adds must
        # enter its law. Whether it is necessary and proven is the kernel's verdict.
        used = names_in(f.get("eq"))
        if used is not None:
            for q, nid, names in contributes:
                if names and not names & used:
                    ctx.err(q, f"new quantity {nid!r} does not appear in the filler's eq")
        for bid in new_bodies:
            if bid not in owners:
                ctx.err(p + ".new_bodies", f"new body '{bid}' owns no new quantity of this filler (a body that owns nothing cannot enter the law)")
        check_src(ctx, f.get("src"), p + ".src", all_ids)

    if ctx.errors:
        return ctx, None
    out = json.loads(json.dumps(doc))
    for key in ("relations", "laws", "fillers"):
        for st in out[key]:
            st["eq"] = canon_eq[st["id"]]
    for f in out["fillers"]:
        f["new_bodies"] = sorted(f["new_bodies"], key=lambda b: b["id"])
        f["new"] = sorted(f["new"], key=lambda nq: nq["id"])
    for o in out["observers"]:
        if isinstance(o["calibrated_against"], list):
            o["calibrated_against"] = sorted(o["calibrated_against"])
    for key in STATEMENT_LISTS["world"]:
        out[key] = sorted(out[key], key=lambda s: s["id"])
    return ctx, out


# ----------------------------------------------------------------- canonical form

def canonical_text(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_of(obj):
    return hashlib.sha256(canonical_text(obj).encode("utf-8")).hexdigest()


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main(argv):
    if len(argv) < 3 or argv[1] not in ("check", "canon"):
        print(__doc__)
        return 2
    try:
        docs = [load(p) for p in argv[2:]]
    except (OSError, json.JSONDecodeError) as e:
        print(f"cannot read input: {e}")
        return 2
    ctx, reg = check_registry(docs[0], argv[2])
    errors = list(ctx.errors)
    results = []
    if reg is not None:
        results.append((argv[2], reg["canon"]))
        for path, doc in zip(argv[3:], docs[1:]):
            wctx, canon = check_world(doc, reg, path)
            errors += wctx.errors
            if canon is not None:
                results.append((path, canon))
    if errors:
        for e in errors:
            print(e)
        print(f"FORM ERRORS: {len(errors)}")
        return 1
    if argv[1] == "canon":
        path, canon = results[-1]
        print(canonical_text(canon))
        print(f"sha256 {sha256_of(canon)}  {path}")
        return 0
    for path, canon in results:
        print(f"OK  {path}  sha256={sha256_of(canon)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
