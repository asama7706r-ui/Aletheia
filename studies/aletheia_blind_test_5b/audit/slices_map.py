"""Workshop 10.16 (not pre-registered; spent worlds): which candidates of tests 5 and 5b fall in classes where the
search can end in principle? Reads the published truths (results/report_X.json) and the keys of both tests.
Classes, by the rules a candidate keeps (assoc = q5 kept or frame f03; comm = q6 kept):
  A  q14 kept: the algebra is R itself, dimension 1 (workshop 10.14, section h; a proof on paper)
  B  q12 kept: a real division algebra, dimension 1, 2, 4 or 8 (Bott, Milnor, Kervaire, 1958)
  C  q13 kept and associative: q13 brings q12 (workshop 10.10), dimension 1, 2 or 4 (Frobenius)
  D  associative and commutative, none of q12, q13, q14: a finite computation (an argument on paper)
  E  associative, not commutative, none of them: not decidable in general (workshop 10.16, section b)
  F  not associative, q13 only: no dimension ceiling (Cayley-Dickson algebras, cayley_dickson_check.py)
  G  not associative, none of them: not studied
Also counts, in the sealed run of 5b, the groups of rules phase 1 tried, refuted, or found an example for.
Usage (from aletheia_blind_test_5b/): python -I audit/slices_map.py"""
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LAB = os.path.dirname(ROOT)
sys.stdout.reconfigure(encoding="utf-8")
UNITS = {"k01": ["q5", "q6", "q12", "q13", "q14"],
         "k02": ["q5", "q6", "q12", "q13", "q5[onn]", "q5[non]", "q5[nno]", "q5[oon]", "q5[ono]", "q5[noo]", "q6[on]"]}
Q5F = {"q5", "q5[nno]", "q5[non]", "q5[noo]", "q5[onn]", "q5[ono]", "q5[oon]"}


def slice_of(kept, assoc, comm):
    if "q14" in kept:
        return "A q14 kept"
    if "q12" in kept:
        return "B q12 kept"
    if "q13" in kept and assoc:
        return "C q13 kept, associative"
    if assoc and comm:
        return "D associative, commutative, no conditions"
    if assoc:
        return "E associative, not commutative, no conditions"
    if "q13" in kept:
        return "F not associative, q13 only"
    return "G not associative, no conditions"


def main():
    branches = collections.Counter()
    status = collections.Counter()
    proofs = collections.Counter()
    for test in ("aletheia_blind_test_5", "aletheia_blind_test_5b"):
        for batch in "AB":
            rep = json.load(open(os.path.join(LAB, test, "results", f"report_{batch}.json"), encoding="utf-8"))["worlds"]
            key = {e["id"]: e for e in json.load(open(os.path.join(LAB, test, f"batch_{batch}", "key", "key.json"),
                                                      encoding="utf-8"))}
            for wid, row in rep.items():
                build = json.load(open(os.path.join(LAB, test, f"batch_{batch}", "worlds", f"{wid}.json"),
                                       encoding="utf-8"))["builds"][0]
                frames = build["frames"]
                units = [u for u in UNITS[build["origin"]] if not ("f03" in frames and u in Q5F)]

                def cls(drop):
                    kept = set(units) - set(drop)
                    return slice_of(kept, "f03" in frames or "q5" in kept, "q6" in kept)
                if isinstance(row["truth"][1], list):
                    for br in row["truth"][1]:
                        for drop in br[:-1]:
                            branches[cls(drop)] += 1
                            status[(cls(drop), br[-1])] += 1
                for r in key[wid].get("refutations") or []:
                    proofs[cls(r["drop"])] += 1
    print("truth branch candidates, tests 5 and 5b, as published (twins counted one by one):")
    for s in sorted(branches):
        print(f"  {s}: {branches[s]} (witnessed {status[(s, 'witnessed')]}, no_witness {status[(s, 'no_witness')]})")
    print(f"  total {sum(branches.values())}, no_witness {sum(v for (s, st), v in status.items() if st == 'no_witness')}")
    print("key refutation candidates:")
    for s in sorted(proofs):
        print(f"  {s}: {proofs[s]}")
    print(f"  total {sum(proofs.values())}")
    tried = refuted = 0
    ex = collections.Counter()
    for batch in "AB":
        o = json.load(open(os.path.join(ROOT, "results", f"outputs_{batch}.json"), encoding="utf-8"))
        for v in o.values():
            ph = v["procedure"].get("phase1") or {}
            tried += ph.get("groups_tried") or 0
            refuted += ph.get("groups_refuted") or 0
            for k, n in (ph.get("group_witnesses") or {}).items():
                ex[k] += n
    print(f"sealed run of 5b, phase 1: groups tried {tried}, refuted {refuted}; "
          f"example search for a group: {ex.get('tried', 0)} tries, {ex.get('found', 0)} examples found")


if __name__ == "__main__":
    main()
