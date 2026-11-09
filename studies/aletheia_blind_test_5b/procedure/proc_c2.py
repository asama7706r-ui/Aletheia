"""Round 2 of the option-C feasibility study (workshop page, 10.8): proc_c.py (round 1, unchanged) with these changes.

1. Refutation by small groups first. Before a candidate's witness tricks and its whole refutation, its kept rules are
   searched for a contradiction in groups of at most GROUP_MAX rules, smallest first: no rule (the request alone),
   then one rule, then two, then three; within a size, groups that allow no case split (no q12, q13 or q14) first,
   since they are cheap. Each group is tried once per world, within GROUP_CAP seconds, by round 1's refutation search
   run on the candidate that keeps exactly the group. A contradictory group refutes every candidate that keeps it
   (as procedure_v5 already uses refutations of larger candidates); a group that a known witness satisfies is not
   tried.
2. Reserved time for the shape search. The first phase (groups, witness tricks, whole refutations) stops at PHASE1
   seconds; the shape search has the rest of the hour, at least TIME_PER_WORLD - PHASE1 seconds.
3. Frobenius narrowing, written and checked but OFF in the measured run (FROBENIUS = False): it is a theorem a human
   chose after seeing the failed worlds, so it is kept aside as a test case for "how the kernel builds its own proof
   tools". A finite-dimensional associative real algebra without zero divisors (q12), or with an inverse for every
   nonzero element (q13), is R, C or H (Frobenius, 1877): dimension 1, 2 or 4. For such candidates: (a) the algebra
   the named generators span under the role's relations without e1 is built; if its dimension is 1, 2 or 4, e1 is
   sought inside it (a small system in e1's coordinates); (b) the shape search tries the dimensions 1, 2 and 4 only,
   and no non-associative shapes (the witness is associative).
4. Fix of round 1: copy-instance arguments that are products of two names were written into certificates as Python
   tuples, which the sealed checker rejects inside refute(), so every proof using them was lost; they are now written
   as JSON words.
Every witness in the output names its source ("witness_source"). A rewriting system whose completion was cut by a
time limit is not cached. Runner only (the procedure is unchanged): each world's result is saved as soon as it is
solved, so a stopped run resumes at the first unsaved world. Usage: python -I proc_c2.py run WORLDS_DIR OUT.json
[PARTS_DIR]"""
import copy
import itertools
import json
import os
import sys
import time
from fractions import Fraction as Fr

import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import proc_c as C1  # noqa: E402  (installs round 1's changes into procedure_v5)
import shape_driver as D  # noqa: E402
import shape_search as SS  # noqa: E402
import shape_search_na as NA  # noqa: E402
from proc_c import P, CHK  # noqa: E402

FROBENIUS = False                      # change 3: off in round 2's measured run (workshop page, 10.8)
GROUP_MAX = 3                          # rules per group, at most
GROUP_CAP = 20                         # seconds per group, at most
PHASE1 = 2700                          # seconds of the hour for the first phase; the rest is the shape search's
FROB_DIMS = (1, 2, 4)                  # Frobenius: R, C, H
SPLITTERS = {"q12", "q13", "q14"}


# ---------------------------------------------------------------- 4. certificates: arguments as JSON words
def terms_json(prov, W):
    out = []
    for (spec, path), c in sorted(prov.items(), key=lambda kv: repr(kv[0])):
        if spec[0] == "ctx":
            sj = {"ctx": spec[1]}
        else:
            sj = {"unit": spec[1], "args": {k: [["1", g if isinstance(g, str) else W.json(g)]] for k, g in spec[2]}}
        steps = [[side, [["1", W.json(w)]]] for side, w in path]
        out.append([P.cj(c), sj, steps])
    return out


P.terms_json = terms_json


# ---------------------------------------------------------------- state
def init(self, world, t_end):
    C1.init(self, world, t_end)
    self.groups_tried = {}             # group -> certificate or None
    self.group_stats = {"tried": 0, "refuted": 0, "cut": 0, "seconds": 0.0}
    self.cut = set()                   # candidates left undecided because the first phase was over
    self.wit_src = {}                  # id(witness) -> where it came from
    self.frob_cache, self.frob_pts = {}, {}


def note_witness(self, d, w, src):
    self.wit_src[id(w)] = src
    self.witness_of[frozenset(CHK.witness_fail_units(w, self.info))] = w
    self.witness_of.setdefault(frozenset(d), w)
    self.status[frozenset(d)] = "WITNESSED"


def rewriter(self, kept, extra=(), names=None):
    """Round 1's rewriter (cache key with q6[on] in associative ambients), but a system cut by time is not cached."""
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
    rw = res[1]
    if not (rw.incomplete and time.time() > rw.t_end):
        self.rw_cache[ck] = res
    return res


# ---------------------------------------------------------------- 1. refutation by small groups first
def group_refute(self, d):
    """A refutation of candidate d from a small group of its kept rules, smallest groups first, or None."""
    kept = set(self.U) - set(d)
    for size in range(0, GROUP_MAX + 1):
        groups = sorted(itertools.combinations(sorted(kept), size), key=lambda g: (bool(set(g) & SPLITTERS), g))
        for g in groups:
            G = frozenset(g)
            if G in self.groups_tried:
                continue
            if any(w is not None and not (G & k) for k, w in self.witness_of.items()):
                continue                       # a known witness satisfies every rule of G
            if time.time() > self.t_end:
                return None
            virt = frozenset(self.U) - G       # the candidate that keeps exactly G
            real_end, t0 = self.t_end, time.time()
            self.t_end = min(real_end, t0 + GROUP_CAP)
            try:
                cert = self.refute(virt)
            finally:
                capped = time.time() > self.t_end
                self.t_end = real_end
            self.group_stats["tried"] += 1
            self.group_stats["seconds"] += time.time() - t0
            if cert is None and capped:
                self.group_stats["cut"] += 1
                self.ref_cache.pop(virt, None)  # a later whole refutation of this candidate may try again
            self.groups_tried[G] = cert
            if cert is not None:
                self.group_stats["refuted"] += 1
                self.proof_of[virt] = cert
                return cert
    return None


# ---------------------------------------------------------------- 3. Frobenius narrowing
def frobenius_applies(self, kept):
    return FROBENIUS and ("f03" in self.frames or "q5" in kept) and bool(kept & {"q12", "q13"}) and "q14" not in kept


def mentions(ast, name):
    if ast[0] == "name":
        return ast[1] == name
    if ast[0] in ("prod", "sum"):
        return any(mentions(x, name) for x in ast[1])
    if ast[0] == "neg":
        return mentions(ast[1], name)
    return False


def frob_base(self, kept):
    """The algebra the named generators span under the role's relations without e1 (a template), or None."""
    key = "q6" in kept
    if key not in self.frob_cache:
        sub = copy.copy(self)
        sub.atoms = [a for a in self.atoms if not (mentions(a[1], "e1") or mentions(a[2], "e1"))]
        sub.names = set(self.gens)
        sub.rw_cache = {}
        eq = {u for u in kept if u in P.EQUATIONAL and u != "q6[on]"} | (kept & {"q12", "q13"})
        self.frob_cache[key] = P.World.template(sub, eq)
    return self.frob_cache[key]


def frob_e1_points(self, tpl, kept):
    """Rational coordinates of e1 inside the template: the role's relations with e1, e1*e1 = -1, and e1 commuting
    with the generators when q6 or q6[on] is kept."""
    key = ("q6" in kept, "q6[on]" in kept)
    if key in self.frob_pts:
        return self.frob_pts[key]
    n, T = tpl["n"], tpl["table"]
    xs = [sp.Symbol(f"x{i}") for i in range(n)]
    vec = {g: [sp.Rational(c.numerator, c.denominator) for c in tpl["gens"][g]] for g in self.gens}
    vec["e1"] = list(xs)

    def mul(u, v):
        out = [sp.Integer(0)] * n
        for i in range(n):
            if u[i] == 0:
                continue
            for j in range(n):
                if v[j] == 0:
                    continue
                c = u[i] * v[j]
                if i == 0:
                    out[j] += c
                elif j == 0:
                    out[i] += c
                else:
                    for k in range(n):
                        t = T.get((i, j, k))
                        if t:
                            out[k] += c * sp.Rational(t.numerator, t.denominator)
        return out

    def ev(p):
        out = [sp.Integer(0)] * n
        for word, c in p.items():
            r = [sp.Integer(1)] + [sp.Integer(0)] * (n - 1)
            for g in word:
                r = mul(r, vec[g])
            for k in range(n):
                out[k] += sp.Rational(c.numerator, c.denominator) * r[k]
        return out
    eqs = []
    for op, l, r in self.atoms:
        if op == "=" and (mentions(l, "e1") or mentions(r, "e1")):
            eqs += ev(SS.padd(SS.free_term(l), SS.free_term(r), -1))
    sq = mul(vec["e1"], vec["e1"])
    eqs += [sq[0] + 1] + sq[1:]
    if "q6" in kept or "q6[on]" in kept:
        for g in self.gens:
            eqs += [a - b for a, b in zip(mul(vec["e1"], vec[g]), mul(vec[g], vec["e1"]))]
    eqs = [q for q in (sp.expand(x) for x in eqs) if q != 0]
    pts = []
    rem = self.t_end - time.time()
    if rem > 1:
        r = D.SOLVER.call(("exact", [str(q) for q in eqs], [str(x) for x in xs]), min(D.EXACT_TIMEOUT, rem))
        if r[0] == "ok" and r[1] != "none":
            for sol in r[1]:
                for pt in D.rational_points(sol, xs, (0, 1, -1, 2, -2), 50):
                    pts.append([Fr(int(pt[x].p), int(pt[x].q)) for x in xs])
    self.frob_pts[key] = pts
    return pts


def frobenius_witness(self, d):
    """A witness of candidate d from the Frobenius narrowing (part a), or None."""
    if self.origin != "k02":
        return None                    # without e1 the template of the generators is the sealed tricks' own
    kept = set(self.U) - set(d)
    if not frobenius_applies(self, kept) or time.time() > self.t_end:
        return None
    tpl = frob_base(self, kept)
    if tpl is None or tpl["n"] not in FROB_DIMS:
        return None
    for e in frob_e1_points(self, tpl, kept):
        full = {"n": tpl["n"], "table": tpl["table"], "gens": dict(tpl["gens"], e1=e), "basis": tpl["basis"]}
        w = P.World.witness_cert(self, full, sorted(d))
        if w is not None:
            return w
    return None


# ---------------------------------------------------------------- statuses
def get_status(self, drop):
    d = frozenset(drop)
    if d in self.status:
        return self.status[d]
    for k, w in list(self.witness_of.items()):
        if w is not None and k <= d:
            self.status[d] = "WITNESSED"
            return "WITNESSED"
    for k in list(self.proof_of):
        if d <= k and self.proof_of[k] is not None:
            self.status[d] = "REFUTED"
            return "REFUTED"
    if time.time() > self.t_end:
        self.cut.add(d)
        self.status[d] = "UNDECIDED"
        return "UNDECIDED"
    if group_refute(self, d) is not None:
        self.status[d] = "REFUTED"
        return "REFUTED"
    w = C1.ORIG_FIND(self, d)
    src = "tricks"
    if w is None:
        w, src = frobenius_witness(self, d), "frobenius"
    if w is not None:
        note_witness(self, d, w, src)
        return "WITNESSED"
    cert = self.refute(d)
    if cert is not None:
        self.proof_of[d] = cert
        self.status[d] = "REFUTED"
        return "REFUTED"
    self.status[d] = "UNDECIDED"
    return "UNDECIDED"


# ---------------------------------------------------------------- the two phases
def shape_witness(self, d, share):
    """Round 1's shape search; for Frobenius candidates only the dimensions 1, 2, 4 and no non-associative shapes."""
    key = frozenset(d)
    if key in self.shape_reports:
        return self.shape_reports[key].get("witness"), self.shape_reports[key].get("source")
    kept = set(self.U) - set(d)
    frob = frobenius_applies(self, kept)
    rem = self.t_end - time.time()
    rep, w, src = {}, None, None
    if rem > 5:
        deadline = time.time() + max(1, min(C1.SHAPE_BUDGET, share - 2, rem - 2))
        w, r1 = SS.search(self.world_json, sorted(d), nmax=C1.NMAX_ASSOC, deadline=deadline,
                          dims=FROB_DIMS if frob else None)
        rep["assoc"] = r1
        src = "shape_assoc" if w is not None else None
        if frob:
            rep["frobenius"] = list(FROB_DIMS)
        elif w is None and time.time() < deadline:
            w, r2 = NA.search(self.world_json, sorted(d), nmax=C1.NMAX_NA, deadline=deadline)
            rep["nonassoc"] = r2
            src = "shape_nonassoc" if w is not None else None
    else:
        rep["skipped"] = "time"
    rep["witness"], rep["source"] = w, src
    self.shape_reports[key] = rep
    return w, src


def minimal(self):
    """The sealed traversal within PHASE1 seconds, then the Frobenius narrowing and round 1's shape search on the
    minimal candidates left undecided, with the rest of the hour."""
    real_end = self.t_end
    phase_end = min(real_end, self.t_start + PHASE1)
    self.t_end = phase_end
    try:
        mins = C1.ORIG_MIN(self)
    finally:
        t1 = time.time()
        self.t_end = real_end
    gs = self.group_stats
    self.phase1 = {"seconds": round(t1 - self.t_start, 1), "before_limit": t1 < phase_end, "limit": PHASE1,
                   "cut_candidates": len(self.cut), "groups_tried": gs["tried"], "groups_refuted": gs["refuted"],
                   "groups_cut": gs["cut"], "group_seconds": round(gs["seconds"], 1)}
    und = [d for d in mins if self.status.get(frozenset(d)) == "UNDECIDED"]
    for i, d in enumerate(und):
        w = frobenius_witness(self, d)
        src = "frobenius"
        if w is None:
            share = (self.t_end - time.time()) / (len(und) - i)
            w, src = shape_witness(self, d, share)
        if w is not None:
            note_witness(self, d, w, src)
    self.phase1["shape_seconds"] = round(time.time() - t1, 1)
    return mins


P.World.__init__ = init
P.World.rewriter = rewriter
P.World.get_status = get_status
P.World.minimal = minimal


def solve_world(world, budget=P.TIME_PER_WORLD):
    out = C1.solve_world(world, budget)        # round 1's: phase1 and "searched" are added there
    W = C1.LAST.get("w")
    if W is not None and W.world_json is world:
        for b in out.get("branches") or []:
            if b.get("witness") is not None:
                b["witness_source"] = W.wit_src.get(id(b["witness"]), "tricks")
            elif b["status"] == "no_witness" and b.get("searched") is not None:
                rep = W.shape_reports.get(frozenset(b["drop"]), {})
                if rep.get("frobenius"):
                    b["searched"]["dims_by_frobenius"] = rep["frobenius"]
    return out


def run(worlds_dir, out_path, parts_dir=None):
    """Each world's result is saved in parts_dir as soon as it is solved; a world saved by an earlier, stopped session is
    not solved again (the world in progress when it stopped starts again from nothing). The merged file is written at
    the end, as before."""
    parts_dir = parts_dir or out_path + ".parts"
    os.makedirs(parts_dir, exist_ok=True)
    names = sorted(x for x in os.listdir(worlds_dir) if x.endswith(".json"))
    for f in names:
        part = os.path.join(parts_dir, f)
        if os.path.exists(part):
            p = json.load(open(part, encoding="utf-8"))
            print(f"{f}: {p['procedure']['verdict']} ({p['seconds']:.1f}s) [saved by an earlier session]", flush=True)
            continue
        world = json.load(open(os.path.join(worlds_dir, f), encoding="utf-8"))
        t0 = time.time()
        try:
            o = solve_world(world)
        except Exception as e:  # noqa: BLE001
            o = {"verdict": "ERROR", "error": f"{type(e).__name__}: {e}"}
        secs = time.time() - t0
        with open(part + ".tmp", "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"procedure": o, "seconds": secs}, fh, ensure_ascii=False, indent=1, sort_keys=True, default=str)
        os.replace(part + ".tmp", part)  # a stop while writing leaves no half-written result
        print(f"{f}: {o['verdict']} ({secs:.1f}s)", flush=True)
    res = {f[:-5]: {"procedure": json.load(open(os.path.join(parts_dir, f), encoding="utf-8"))["procedure"]}
           for f in names}
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, sort_keys=True, default=str)


if __name__ == "__main__":
    if len(sys.argv) in (4, 5) and sys.argv[1] == "run":
        run(*sys.argv[2:])
    else:
        print(__doc__)
