#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The procedure of blind test 5b (protocol_v5b.md, Section 2.9).

It is the sealed procedure of test 5 (procedure_v5.py, unchanged) with the changes of option C, as measured on the
workshop page (10.7, 10.9, 10.12), installed by the files of this folder:
- proc_c.py   round 1: q6[on] relators in associative ambients; copy instances whose arguments are products of two
              names written in the role; splits on the factors of a name's minimal polynomial; inverse nodes on the
              names; after the search, the shape-first witness search on the branches left undecided;
- proc_c2.py  round 2: refutation by small groups of kept rules first (at most 3 rules, 20 s each); the first phase
              stops at 2700 s and leaves the rest of the hour to the shape search; Frobenius off;
- proc_c3.py  10.10: the loop over the minimal hitting sets of the conflicts found so far, cores and parts, an
              example sought for a group before it is refuted, and every conflict written into "refutations".
And two changes of its own (workshop page, 10.13):
- A. The associative shape search is skipped for a branch when a conflict the procedure has proven is made only of
     rules the branch keeps and rules of the q5 family. Every associative table satisfies q5 and all its copies, so
     no associative table can be an example of that branch. The whole shape budget then goes to the non-associative
     search, and the branch's "searched" record names the conflict.
- B. (in proc_c.py) The time limit is checked inside the scan for zero-divisor pairs, so a group's 20 s and the
     first phase's limit hold there too.
Usage: python procedure/procedure_v5b.py run WORLDS_DIR OUTPUTS.json [PARTS_DIR]
Each world is saved in PARTS_DIR as soon as it is solved (default OUTPUTS.json.parts); a stopped run resumes at the
first unsaved world, which starts again from nothing."""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import proc_c as C1  # noqa: E402
import proc_c2 as C2  # noqa: E402
import proc_c3 as C3  # noqa: E402
import shape_search_na as NA  # noqa: E402

P = C3.P
ORIG_SHAPE = C2.shape_witness


def excluding_conflict(self, kept):
    """A proven conflict that every associative table keeping `kept` would satisfy, or None."""
    for c in self.conflicts:
        if all(u in P.Q5F or u in kept for u in c["keep"]):
            return c
    return None


def shape_witness(self, d, share):
    """Round 2's shape search, without the associative half when a proven conflict excludes it (change A)."""
    key = frozenset(d)
    if key in self.shape_reports:
        return self.shape_reports[key].get("witness"), self.shape_reports[key].get("source")
    kept = set(self.U) - set(d)
    c = excluding_conflict(self, kept)
    if c is None:
        return ORIG_SHAPE(self, d, share)
    rep = {"assoc": {"skipped": f"no associative example: the proven conflict {sorted(c['keep'])}"}}
    w, src = None, None
    rem = self.t_end - time.time()
    if rem > 5:
        deadline = time.time() + max(1, min(C1.SHAPE_BUDGET, share - 2, rem - 2))
        w, r2 = NA.search(self.world_json, sorted(d), nmax=C1.NMAX_NA, deadline=deadline)
        rep["nonassoc"] = r2
        src = "shape_nonassoc" if w is not None else None
    else:
        rep["skipped"] = "time"
    rep["witness"], rep["source"] = w, src
    self.shape_reports[key] = rep
    return w, src


C2.shape_witness = shape_witness                # proc_c3.minimal calls it by this name
solve_world = C3.solve_world

if __name__ == "__main__":
    if len(sys.argv) in (4, 5) and sys.argv[1] == "run":
        C3.run(*sys.argv[2:])
    else:
        print(__doc__)
        sys.exit(2)
