"""Audit (not pre-registered): how much does learning from conflicts narrow the candidates in the sealed run?
For each world with a phase-1 record: |U|, the number of candidates 2^|U|, how many the procedure tested as whole
candidates, how many groups it tried, and how many conflicts it learned. Read from results/outputs_X.json only.
Usage (from aletheia_blind_test_5b/): python -I audit/narrowing_5b.py"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "procedure"))
sys.stdout.reconfigure(encoding="utf-8")


def main():
    tot = {"cands": 0, "tested": 0, "groups": 0, "conflicts": 0, "worlds": 0}
    for batch in "AB":
        o = json.load(open(os.path.join(ROOT, "results", f"outputs_{batch}.json"), encoding="utf-8"))
        for wid in sorted(o):
            e = o[wid]["procedure"]
            ph = e.get("phase1") or {}
            if not ph:
                continue
            w = json.load(open(os.path.join(ROOT, f"batch_{batch}", "worlds", f"{wid}.json"), encoding="utf-8"))
            b = w["builds"][0]
            n = 5 if b["origin"] == "k01" else 11       # judged units, before a frame removes the q5 family
            if "f03" in b["frames"]:
                n -= 7 if b["origin"] == "k02" else 1
            cands = 2 ** n
            tested = len(e.get("tested") or [])
            print(f"{batch} {wid}: {n} units, {cands} candidates, {tested} tested, "
                  f"{ph.get('groups_tried')} groups, {ph.get('conflicts')} conflicts, "
                  f"phase 1 {ph.get('seconds')} s")
            tot["cands"] += cands
            tot["tested"] += tested
            tot["groups"] += ph.get("groups_tried") or 0
            tot["conflicts"] += ph.get("conflicts") or 0
            tot["worlds"] += 1
    print(tot)


if __name__ == "__main__":
    main()
