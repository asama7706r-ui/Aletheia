"""The user's proposal of 2026-10-26 (workshop page, 10.10), measured as pre-registered in 10.11: learn the smallest
contradictory rule sets. A study copy on top of round 2 (proc_c2.py, unchanged); only the first phase's traversal of
the candidates changes.

1. The loop. Instead of walking the candidates top-down (procedure_v5.World.minimal), the kernel keeps the conflicts
   found so far (sets of kept rules, each with a certificate the sealed checker accepts) and repeats: compute the
   smallest drop sets that hit every known conflict (Reiter 1987: the minimal hitting sets); take one not yet
   examined, smallest first; examine it as round 2 does (small groups, then the witness tricks, then the whole
   refutation); every new refutation becomes a conflict. It stops when every minimal hitting set has been examined,
   or at the first phase's limit (the sets left are undecided and counted as cut).
2. Cores. A new conflict is shrunk without a new search: its certificate is offered to the sealed checker with one
   kept rule fewer, rule by rule, and a rule the certificate does not need leaves the conflict.
3. Parts. A conflict that keeps parts of q5 (its copies) or q6[on] is also offered with the parent rule instead of
   those parts: once the parent is kept the parts' instances are zero, so their terms are removed from the
   certificate, and the sealed checker checks the result for the new set. An accepted twin is a conflict too.
4. Output. Every conflict is written into the protocol's optional "refutations" field, for the candidate that keeps
   exactly its set (10.9, fix 1); "conflicts" lists each one's rules, source and size before shrinking.
Everything else is round 2's: the witness tricks, the shape search and its limits, the hour per world, the first
phase's 2700 s, groups of at most 3 rules within 20 s each, Frobenius off.
Usage (from workshop_search_study/): python -I proc_c3.py run WORLDS_DIR OUT.json [PARTS_DIR]"""
import copy
import itertools
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import proc_c as C1  # noqa: E402
import proc_c2 as C2  # noqa: E402  (installs rounds 1 and 2 into procedure_v5)
from proc_c import P, CHK  # noqa: E402

PARENT = {u: ("q5" if u.startswith("q5[") else "q6") for u in P.COPIES}   # part -> the rule it is a part of


# ---------------------------------------------------------------- pure helpers (checked on their own)
def hitting_sets(units, conflicts):
    """The minimal sets of units that meet every conflict, smallest first, then in name order."""
    units = sorted(units)
    out = []
    for size in range(len(units) + 1):
        for h in itertools.combinations(units, size):
            hs = frozenset(h)
            if any(m <= hs for m in out):
                continue
            if all(hs & c for c in conflicts):
                out.append(hs)
    return out


def strip_units(cert, units):
    """The certificate without the terms that cite the given units."""
    c = copy.deepcopy(cert)

    def walk(nd):
        for key in ("terms", "proof_ab"):
            if key in nd:
                nd[key] = [t for t in nd[key] if not (isinstance(t[1], dict) and t[1].get("unit") in units)]
        for kid in nd.get("children") or []:
            walk(kid)
    walk(c["tree"])
    return c


# ---------------------------------------------------------------- state
def init(self, world, t_end):
    C2.init(self, world, t_end)
    self.conflicts = []        # {"keep": frozenset, "cert": ..., "source": "group"|"whole"|"part", "found": int}
    self.tested = []
    self.group_witness_stats = {"tried": 0, "found": 0, "cut": 0, "seconds": 0.0}


def drop_of(self, keep):
    return frozenset(self.U) - frozenset(keep)


def accepts(self, cert, keep):
    return CHK.safe(CHK.check_refutation, cert, self.info, sorted(drop_of(self, keep)))[0]


def covered(self, keep):
    """A known conflict lies inside keep."""
    return any(c["keep"] <= keep for c in self.conflicts)


def shrink(self, keep, cert):
    for r in sorted(keep):
        if time.time() > self.t_end:
            break
        if accepts(self, cert, keep - {r}):
            keep = keep - {r}
    return keep


def add_conflict(self, keep, cert, source):
    keep = frozenset(keep)
    if covered(self, keep):
        return
    found = len(keep)
    keep = shrink(self, keep, cert)
    if covered(self, keep):
        return
    self.conflicts = [c for c in self.conflicts if not keep <= c["keep"]]
    self.conflicts.append({"keep": keep, "cert": cert, "source": source, "found": found})
    self.proof_of[drop_of(self, keep)] = cert          # inheritance and the FORCED proofs use it
    for parent in ("q5", "q6"):
        parts = {u for u in keep if PARENT.get(u) == parent}
        if parts and parent in self.U and parent not in keep:
            twin = (keep - parts) | {parent}
            c2 = strip_units(cert, parts)
            if not covered(self, twin) and accepts(self, c2, twin):
                add_conflict(self, twin, c2, "part")


def harvest(self, before):
    """Refutations found since the snapshot become conflicts."""
    for k in list(self.proof_of):
        if k in before or self.proof_of[k] is None:
            continue
        keep = frozenset(self.U) - k
        cert = self.proof_of[k]
        src = "group" if self.groups_tried.get(keep) is cert else "whole"
        add_conflict(self, keep, cert, src)


# ---------------------------------------------------------------- 1b. a group: an example first (change after the short check)
def group_witness(self, virt):
    """The witness tricks on the candidate that keeps exactly a group, within GROUP_CAP seconds. A group with an
    example cannot be contradictory, and the example also covers every group of the rules it keeps."""
    real_end, t0 = self.t_end, time.time()
    self.t_end = min(real_end, t0 + C2.GROUP_CAP)
    try:
        w = C1.ORIG_FIND(self, virt)
    finally:
        capped = time.time() > self.t_end
        self.t_end = real_end
    gw = self.group_witness_stats
    gw["tried"] += 1
    gw["seconds"] += time.time() - t0
    if w is None:
        if capped:                     # a search cut by time is not cached as "no witness"
            kept = set(self.U) - set(virt)
            self.wit_cache.pop((frozenset(kept & P.EQUATIONAL), frozenset(kept & {"q12", "q13"})), None)
            gw["cut"] += 1
        return False
    gw["found"] += 1
    C2.note_witness(self, virt, w, "tricks")
    return True


def group_refute(self, d):
    """Round 2's refutation by small groups, with one change: before a group is refuted, an example of it is sought."""
    kept = set(self.U) - set(d)
    for size in range(0, C2.GROUP_MAX + 1):
        groups = sorted(itertools.combinations(sorted(kept), size), key=lambda g: (bool(set(g) & C2.SPLITTERS), g))
        for g in groups:
            G = frozenset(g)
            if G in self.groups_tried:
                continue
            if any(w is not None and not (G & k) for k, w in self.witness_of.items()):
                continue                       # a known witness satisfies every rule of G
            if time.time() > self.t_end:
                return None
            virt = frozenset(self.U) - G       # the candidate that keeps exactly G
            if group_witness(self, virt):
                continue
            if time.time() > self.t_end:
                return None
            real_end, t0 = self.t_end, time.time()
            self.t_end = min(real_end, t0 + C2.GROUP_CAP)
            try:
                cert = self.refute(virt)
            finally:
                capped = time.time() > self.t_end
                self.t_end = real_end
            self.group_stats["tried"] += 1
            self.group_stats["seconds"] += time.time() - t0
            if cert is None and capped:
                self.group_stats["cut"] += 1
                self.ref_cache.pop(virt, None)
            self.groups_tried[G] = cert
            if cert is not None:
                self.group_stats["refuted"] += 1
                self.proof_of[virt] = cert
                return cert
    return None


C2.group_refute = group_refute                 # proc_c2.get_status calls it by this name


# ---------------------------------------------------------------- 1. the loop
def traverse(self):
    tested = set()
    while True:
        H = hitting_sets(self.U, [c["keep"] for c in self.conflicts])
        todo = [h for h in H if h not in tested]
        if not todo:
            break
        if time.time() > self.t_end:
            for h in todo:
                self.status.setdefault(h, "UNDECIDED")
                self.cut.add(h)
            break
        h = todo[0]
        tested.add(h)
        self.tested.append(sorted(h))
        before = set(self.proof_of)
        self.get_status(h)
        harvest(self, before)
    return sorted((sorted(m) for m in H), key=lambda m: (len(m), m))


def minimal(self):
    """The loop within PHASE1 seconds, then round 2's shape search on the minimal candidates left undecided."""
    real_end = self.t_end
    phase_end = min(real_end, self.t_start + C2.PHASE1)
    self.t_end = phase_end
    try:
        mins = traverse(self)
    finally:
        t1 = time.time()
        self.t_end = real_end
    gs = self.group_stats
    sources, sizes = {}, {}
    for c in self.conflicts:
        sources[c["source"]] = sources.get(c["source"], 0) + 1
        sizes[str(len(c["keep"]))] = sizes.get(str(len(c["keep"])), 0) + 1
    self.phase1 = {"seconds": round(t1 - self.t_start, 1), "before_limit": t1 < phase_end, "limit": C2.PHASE1,
                   "cut_candidates": len(self.cut), "groups_tried": gs["tried"], "groups_refuted": gs["refuted"],
                   "groups_cut": gs["cut"], "group_seconds": round(gs["seconds"], 1),
                   "tested": len(self.tested), "conflicts": len(self.conflicts), "conflict_sources": sources,
                   "conflict_sizes": sizes, "shrunk": sum(1 for c in self.conflicts if len(c["keep"]) < c["found"]),
                   "group_witnesses": {k: (round(v, 1) if k == "seconds" else v)
                                       for k, v in self.group_witness_stats.items()}}
    und = [d for d in mins if self.status.get(frozenset(d)) == "UNDECIDED"]
    for i, d in enumerate(und):
        w = C2.frobenius_witness(self, d)
        src = "frobenius"
        if w is None:
            share = (self.t_end - time.time()) / (len(und) - i)
            w, src = C2.shape_witness(self, d, share)
        if w is not None:
            C2.note_witness(self, d, w, src)
    self.phase1["shape_seconds"] = round(time.time() - t1, 1)
    return mins


P.World.__init__ = init
P.World.minimal = minimal


def solve_world(world, budget=P.TIME_PER_WORLD):
    out = C2.solve_world(world, budget)
    W = C1.LAST.get("w")
    if W is not None and W.world_json is world:
        out["refutations"] = [{"drop": sorted(drop_of(W, c["keep"])), "proof": c["cert"]} for c in W.conflicts]
        out["conflicts"] = [{"keep": sorted(c["keep"]), "source": c["source"], "found_size": c["found"]}
                            for c in W.conflicts]
        out["tested"] = W.tested
    return out


def run(worlds_dir, out_path, parts_dir=None):
    """As proc_c2.run: each world is saved as soon as it is solved, and a stopped run resumes at the first unsaved
    world (the world in progress when it stopped starts again from nothing)."""
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
        os.replace(part + ".tmp", part)
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
