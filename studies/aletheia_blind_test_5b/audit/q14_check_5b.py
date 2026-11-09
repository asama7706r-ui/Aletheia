"""Audit (not pre-registered): generator A's remark on the order rule q14.
Claim (generator A, progress.txt, stage 4): over k01, every algebra in W that keeps q14 is R itself (dimension 1),
so a candidate that keeps q14 has no model when the role has no real solution; but no certificate form of
Section 4 can say so, and such candidates stay undecided (or become no_witness branches).
This script lists, for every world over k01 in both batches, the truth's branches and the output's branches that
keep q14, with their status, and whether the role has a real solution (the sealed reference's
real_solution_count: the number of real solutions, or None when the solution set is not zero-dimensional).
The claim itself is argued in audit.md, not computed here.
Usage (from aletheia_blind_test_5b/): python -I audit/q14_check_5b.py"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scorer"))
import certs_v5 as C  # noqa: E402
import ref_v5b as RF  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")


def keeps_q14(branch):
    drops = branch[:-1]                     # one or more mirror-merged drop lists, then the status
    return all("q14" not in d for d in drops)


def main():
    totals = {"truth": 0, "output": 0}
    for batch in "AB":
        rep = json.load(open(os.path.join(ROOT, "results", f"report_{batch}.json"), encoding="utf-8"))["worlds"]
        for wid in sorted(rep):
            path = os.path.join(ROOT, f"batch_{batch}", "worlds", f"{wid}.json")
            info = C.world_info(C.R.load(path))
            if info["origin"] != "k01":
                continue
            row = rep[wid]
            tb = [b for b in (row["truth"][1] if isinstance(row["truth"][1], list) else []) if keeps_q14(b)]
            ob = [b for b in (row["output"][1] if isinstance(row["output"][1], list) else []) if keeps_q14(b)]
            if not tb and not ob:
                continue
            n = RF.real_solution_count(info)
            print(f"{batch} {wid}: truth {row['truth'][0]}, output {row['output'][0]}, "
                  f"decision {'ok' if row['decision_ok'] else 'WRONG'}; real solutions of the role: {n}")
            for b in tb:
                print(f"  truth branch keeping q14: {json.dumps(b)}")
                totals["truth"] += 1
            for b in ob:
                print(f"  output branch keeping q14: {json.dumps(b)}")
                totals["output"] += 1
    print(f"total: {totals['truth']} truth branches and {totals['output']} output branches keep q14 over k01")


if __name__ == "__main__":
    main()
