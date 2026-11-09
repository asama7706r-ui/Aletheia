"""Option C of the workshop page (10.4), as a study copy of the sealed procedure (procedure_v5.py is not changed).

The sealed procedure runs as it is, with three changes:
1. Fix: a kept q6[on] gives relators in associative ambients too (the sealed procedure and reference add copy
   instances only in non-associative ambients; associativity implies the q5 copies, not q6[on]).
2. Wider refutations: copy instances whose arguments are products of two names (non-associative ambients), and
   splits on the factors of a name's minimal polynomial (associative ambients), e.g. fa*fa*(fa - 1) = 0.
3. On the minimal candidates left undecided (the branches), after the sealed search: the shape-first witness search
   (shape_search.py, shape_search_na.py), smallest dimension first, within a time budget. The bound it
   reached is written into every no_witness branch ("searched").
Test 5b copy: the only change from the study's file is the time check in search()'s scan for zero-divisor pairs
(workshop page, 10.13, C). The test runs procedure_v5b.py, not this file.
Usage: python -I proc_c.py run WORLDS_DIR OUT.json"""
import itertools
import json
import os
import sys
import time
from fractions import Fraction as Fr

import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import shape_search as SS  # noqa: E402
import shape_search_na as NA  # noqa: E402
from shape_search import P, CHK  # noqa: E402

NMAX_ASSOC, NMAX_NA = 5, 4
SHAPE_BUDGET = 600                       # seconds of shape search per undecided branch, at most
ORIG_COPIES = P.World.copy_instances
ORIG_FIND = P.World.find_witness
ORIG_INIT = P.World.__init__
LAST = {}


def init(self, world, t_end):
    ORIG_INIT(self, world, t_end)
    self.world_json = world
    self.shape_reports = {}
    self.t_start = time.time()
    self.phase1 = None
    LAST["w"] = self


def copy_instances(self, alg, kept, names, maxlen=1):
    W = alg.W
    m = alg.mul
    e = {W.gen("e1"): Fr(1)} if "e1" in names else None
    if W.assoc:
        out = []
        if "q6[on]" in kept and e is not None:
            for g in sorted(names):
                v = {W.gen(g): Fr(1)}
                d = alg.add(m(e, v), m(v, e), -1)
                if d:
                    out.append((("unit", "q6[on]", (("b", g),)), d))
        return out
    out = list(ORIG_COPIES(self, alg, kept, names, maxlen))
    if e is None:
        return out
    singles = sorted(names)
    pairs = [W.mul(W.gen(a), W.gen(b)) for a, b in role_products(self.atoms) if a in names and b in names]
    spec_vars = {"q5[onn]": "bc", "q5[non]": "ac", "q5[nno]": "ab", "q5[oon]": "c", "q5[ono]": "b",
                 "q5[noo]": "a", "q6[on]": "b"}
    for u in sorted(kept & set(P.COPIES)):
        vs = spec_vars[u]
        for pos in range(len(vs)):                       # exactly one argument is a product of two names
            for combo in itertools.product(*[pairs if k == pos else singles for k in range(len(vs))]):
                v = {k: {(W.gen(x) if isinstance(x, str) else x): Fr(1)} for k, x in zip(vs, combo)}
                if u == "q5[onn]":
                    x_, y_ = m(m(e, v["b"]), v["c"]), m(e, m(v["b"], v["c"]))
                elif u == "q5[non]":
                    x_, y_ = m(m(v["a"], e), v["c"]), m(v["a"], m(e, v["c"]))
                elif u == "q5[nno]":
                    x_, y_ = m(m(v["a"], v["b"]), e), m(v["a"], m(v["b"], e))
                elif u == "q5[oon]":
                    x_, y_ = m(m(e, e), v["c"]), m(e, m(e, v["c"]))
                elif u == "q5[ono]":
                    x_, y_ = m(m(e, v["b"]), e), m(e, m(v["b"], e))
                elif u == "q5[noo]":
                    x_, y_ = m(m(v["a"], e), e), m(v["a"], m(e, e))
                else:
                    x_, y_ = m(e, v["b"]), m(v["b"], e)
                d = alg.add(x_, y_, -1)
                if d:
                    out.append((("unit", u, tuple(zip(vs, combo))), d))
    return out


def role_products(atoms):
    """The products of two names written in the role (as copy arguments: change 2)."""
    out = []

    def walk(ast):
        if ast[0] == "prod" and len(ast[1]) == 2 and all(x[0] == "name" for x in ast[1]):
            p = (ast[1][0][1], ast[1][1][1])
            if p not in out:
                out.append(p)
        if ast[0] in ("prod", "sum"):
            for x in ast[1]:
                walk(x)
        elif ast[0] == "neg":
            walk(ast[1])
    for _op, l, r in atoms:
        walk(l)
        walk(r)
    return out


def minpoly_pairs(alg, rw, names):
    """Splits on the factors of each name's minimal polynomial (associative ambients only)."""
    W = alg.W
    if not W.assoc:
        return []
    out = []
    t = sp.Symbol("t")
    for g in sorted(names):
        gv = {W.gen(g): Fr(1)}
        powers = [{W.unit: Fr(1)}]
        coeffs = None
        for _k in range(1, 2 * P.P2 + 1):
            powers.append(rw.nf(alg.mul(powers[-1], gv)))
            words = sorted({w for p in powers for w in p}, key=repr)
            M = sp.Matrix([[sp.Rational(p.get(w, 0).numerator, p.get(w, 0).denominator) if p.get(w) else 0
                            for p in powers] for w in words]) if words else sp.zeros(1, len(powers))
            ns = M.nullspace()
            if ns:
                v = ns[0]
                coeffs = [v[i] / v[len(powers) - 1] for i in range(len(powers))] if v[len(powers) - 1] != 0 else None
                break
        if not coeffs:
            continue
        mp = sp.Poly(sum(c * t ** i for i, c in enumerate(coeffs)), t)
        _, facs = sp.factor_list(mp.as_expr(), t)
        parts = [sp.Poly(f ** e, t) for f, e in facs]
        cands = []
        if len(parts) >= 2:
            for p_ in parts:
                cands.append((p_, sp.Poly(sp.quo(mp, p_), t)))
        elif len(facs) == 1 and facs[0][1] >= 2:
            f, e = facs[0]
            cands.append((sp.Poly(f, t), sp.Poly(f ** (e - 1), t)))

        def elem(poly):
            out_ = {}
            for (i,), c in poly.terms():
                c = Fr(int(sp.Rational(c).p), int(sp.Rational(c).q))
                out_ = alg.add(out_, {w: c * x for w, x in powers[i].items()})
            return out_
        for pa, pb in cands:
            a, b = elem(pa), elem(pb)
            ab = alg.mul(a, b)
            if rw.nf(a) and rw.nf(b) and not rw.nf(ab):
                out.append((a, b, ab))
    return out


def search(self, kept, extra, names, depth):
    """procedure_v5.World.search, with the minimal-polynomial splits tried first."""
    if time.time() > self.t_end:
        return None
    alg, rw, rels, ineqs = self.rewriter(kept, extra, names)
    W = alg.W
    one = {W.unit: Fr(1)}
    mm = rw.member(one)
    if mm is not None:
        return {"node": "close", "target": {"const": "1"}, "terms": P.terms_json(mm, W)}
    for k, t_ in enumerate(ineqs):
        mm = rw.member(t_)
        if mm is not None:
            return {"node": "close", "target": {"ineq": k}, "terms": P.terms_json(mm, W)}
    forms = P.small_forms(alg, names, P.Surd(0, 1, self.th_c) if getattr(self, "th_c", None) else None)
    if "q14" in kept:
        for t_ in forms:
            tt = alg.mul(t_, t_)
            r = rw.nf(tt)
            if set(r) <= {W.unit} and r.get(W.unit, 0) < 0:
                c = -r[W.unit]
                mm = rw.member(alg.add(tt, {W.unit: c}))
                if mm is not None:
                    return {"node": "positive", "t": [P.el_json(t_, W)], "c": P.cj(c), "terms": P.terms_json(mm, W)}
    if depth >= P.S:
        return None
    splitter = "q12" if "q12" in kept else ("q14" if "q14" in kept else None)
    inverse = "q13" in kept and W.assoc and splitter is None
    if not splitter and not inverse:
        return None
    pairs = minpoly_pairs(alg, rw, names)
    if not splitter:
        # inverse nodes: also on each name itself, not only on members of zero-divisor pairs (change 2)
        for g in sorted(names):
            gv = {W.gen(g): Fr(1)}
            if rw.nf(gv) and all(gv != a for a, _b, _ab in pairs):
                pairs.append((gv, None, None))
    n_mp = len(pairs)
    for a in forms:
        if time.time() > self.t_end:               # test 5b: the time limit holds inside this scan too
            return None
        if not rw.nf(a):
            continue
        for b in forms:
            if not rw.nf(b):
                continue
            ab = alg.mul(a, b)
            if not rw.nf(ab):
                pairs.append((a, b, ab))
        if len(pairs) >= 8 + n_mp:
            break
    for a, b, ab in pairs[:8 + n_mp]:
        if splitter:
            k0 = self.search(kept, extra + [a], names, depth + 1)
            if k0 is None:
                continue
            k1 = self.search(kept, extra + [b], names, depth + 1)
            if k1 is None:
                continue
            return {"node": "split", "by": splitter, "a": P.el_json(a, W), "b": P.el_json(b, W),
                    "proof_ab": P.terms_json(rw.member(ab), W), "children": [k0, k1]}
        v = next(f"w{i}" for i in range(1, 99) if f"w{i}" not in names)
        k0 = self.search(kept, extra + [a], names, depth + 1)
        if k0 is None:
            continue
        vv = {W.gen(v): Fr(1)}
        av = alg.add(alg.mul(a, vv), {W.unit: Fr(1)}, -1)
        va = alg.add(alg.mul(vv, a), {W.unit: Fr(1)}, -1)
        k1 = self.search(kept, extra + [av, va], names | {v}, depth + 1)
        if k1 is None:
            continue
        return {"node": "inverse", "a": P.el_json(a, W), "v": v, "children": [k0, k1]}
    return None


ORIG_MIN = P.World.minimal


def minimal(self):
    """procedure_v5.World.minimal, then the shape search on the minimal candidates left undecided (change 3).
    A witness never changes which candidates are minimal, only a branch's status, so the search runs on the
    branches alone, sharing the time that is left."""
    mins = ORIG_MIN(self)
    t1 = time.time()
    self.phase1 = {"seconds": round(t1 - self.t_start, 1), "before_limit": t1 < self.t_end}
    und = [d for d in mins if self.status.get(frozenset(d)) == "UNDECIDED"]
    for i, d in enumerate(und):
        share = (self.t_end - time.time()) / (len(und) - i)
        w = shape_witness(self, d, share)
        if w is not None:
            self.witness_of[frozenset(CHK.witness_fail_units(w, self.info))] = w
            self.witness_of.setdefault(frozenset(d), w)
            self.status[frozenset(d)] = "WITNESSED"
    self.phase1["shape_seconds"] = round(time.time() - t1, 1)
    return mins


def shape_witness(self, d, share):
    key = frozenset(d)
    if key in self.shape_reports:
        return self.shape_reports[key].get("witness")
    rem = self.t_end - time.time()
    rep = {}
    w = None
    if rem > 5:
        deadline = time.time() + max(1, min(SHAPE_BUDGET, share - 2, rem - 2))
        w, r1 = SS.search(self.world_json, sorted(d), nmax=NMAX_ASSOC, deadline=deadline)
        rep["assoc"] = r1
        if w is None and time.time() < deadline:
            w, r2 = NA.search(self.world_json, sorted(d), nmax=NMAX_NA, deadline=deadline)
            rep["nonassoc"] = r2
    else:
        rep["skipped"] = "time"
    rep["witness"] = w
    self.shape_reports[key] = rep
    return w


def get_status(self, drop):
    d = frozenset(drop)
    if d in self.status:
        return self.status[d]
    for (k, w) in list(self.witness_of.items()):
        if w is not None and k <= d:
            self.status[d] = "WITNESSED"
            return "WITNESSED"
    for k in list(self.proof_of):
        if d <= k and self.proof_of[k] is not None:
            self.status[d] = "REFUTED"
            return "REFUTED"
    w = ORIG_FIND(self, d)
    if w is None:
        cert = self.refute(d)
        if cert is not None:
            self.proof_of[d] = cert
            self.status[d] = "REFUTED"
            return "REFUTED"
    if w is not None:
        self.witness_of[frozenset(CHK.witness_fail_units(w, self.info))] = w
        self.witness_of.setdefault(d, w)
        self.status[d] = "WITNESSED"
        return "WITNESSED"
    self.status[d] = "UNDECIDED"
    return "UNDECIDED"


def rewriter(self, kept, extra=(), names=None):
    """procedure_v5.World.rewriter, with q6[on] in the cache key of associative ambients (change 1)."""
    names = names or self.names
    alg = self.ambient(kept)
    ck = (getattr(self, "th_c", None), alg.W.assoc, alg.W.comm,
          frozenset(kept & set(P.COPIES)) if not alg.W.assoc else frozenset(kept & {"q6[on]"}),
          tuple(repr(sorted(e.items(), key=repr)) for e in extra), frozenset(names))
    if not hasattr(self, "rw_cache"):
        self.rw_cache = {}
    if ck in self.rw_cache:
        return self.rw_cache[ck]
    res = self._rewriter(kept, extra, names, alg)
    self.rw_cache[ck] = res
    return res


P.World.__init__ = init
P.World.rewriter = rewriter
P.World.copy_instances = copy_instances
P.World.search = search
P.World.get_status = get_status
P.World.minimal = minimal


def solve_world(world, budget=P.TIME_PER_WORLD):
    LAST.pop("w", None)
    out = P.solve_world(world, budget)
    W = LAST.get("w")
    if W is not None and W.world_json is world:
        out["phase1"] = W.phase1
        for b in out.get("branches") or []:
            if b["status"] == "no_witness":
                rep = W.shape_reports.get(frozenset(b["drop"]), {})
                a_, n_ = rep.get("assoc") or {}, rep.get("nonassoc") or {}
                b["searched"] = {"assoc_complete_to_dim": a_.get("bound"), "assoc_partial_from": a_.get("partial"),
                                 "nonassoc_complete_to_dim": n_.get("bound"),
                                 "nonassoc_partial_from": n_.get("partial"),
                                 "stopped": a_.get("stopped") or n_.get("stopped") or rep.get("skipped")
                                 or a_.get("skipped") or n_.get("skipped")}
    return out


def run(worlds_dir, out_path):
    res = {}
    for f in sorted(x for x in os.listdir(worlds_dir) if x.endswith(".json")):
        world = json.load(open(os.path.join(worlds_dir, f), encoding="utf-8"))
        t0 = time.time()
        try:
            o = solve_world(world)
        except Exception as e:  # noqa: BLE001
            o = {"verdict": "ERROR", "error": f"{type(e).__name__}: {e}"}
        res[f[:-5]] = {"procedure": o}
        print(f"{f}: {o['verdict']} ({time.time() - t0:.1f}s)", flush=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, sort_keys=True, default=str)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "run":
        run(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
