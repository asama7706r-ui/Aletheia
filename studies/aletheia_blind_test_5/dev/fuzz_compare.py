"""Random small builds: the procedure against the independent reference (protocol_v5.md, Section 12).
For each build, the reference computes the truth from the procedure's own certificates plus its own
search; a disagreement means the procedure missed a branch, branched where a proof decides, or wrote
an invalid certificate. Usage: python -I dev/fuzz_compare.py N SEED [BUDGET] [REPORT]
(BUDGET in seconds per build, default 240; the sealed TIME_PER_WORLD is 1800. REPORT defaults to
dev/fuzz_report.json; give each parallel run its own.)"""
import json
import os
import random
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scorer"))
sys.path.insert(0, os.path.join(ROOT, "procedure"))
import certs_v5 as C  # noqa: E402
import ref_v5 as RF  # noqa: E402
import validate_v5 as V  # noqa: E402
import score_v5 as SC  # noqa: E402
import procedure_v5 as PR  # noqa: E402


def random_build(rng):
    origin = rng.choice(["k01", "k01", "k02"])
    n = rng.choice([1, 2, 2, 3])
    gens = ["ga", "gb", "gc"][:n]
    olds = ["e1"] if origin == "k02" else []
    role = []
    for g in gens:
        if rng.random() < 0.8:
            role.append(f"{g}*{g} = {rng.choice(['-1', '1', '0', '2', '-2'])}")
    for i in range(n):
        for j in range(i + 1, n):
            r = rng.random()
            a, b = gens[i], gens[j]
            if r < 0.4:
                role.append(f"{a}*{b} = -({b}*{a})")
            elif r < 0.55:
                role.append(f"{a}*{b} = {b}*{a}")
            elif r < 0.7 and n == 3:
                c = [x for x in gens if x not in (a, b)][0]
                role.append(f"{a}*{b} = {c}")
    for g in gens:
        if olds and rng.random() < 0.4:
            role.append(rng.choice([f"{g}*e1 = -(e1*{g})", f"{g}*e1 = e1*{g}", f"{g} != e1"]))
        if rng.random() < 0.3:
            role.append(f"{g} != {rng.choice(['0', '1', '-1'])}")
    if not role or any(not any(g in s for s in role) for g in gens):
        role += [f"{g} != 0" for g in gens if not any(g in s for s in role)]
    if not role:
        role = [f"{gens[0]}*{gens[0]} = -1"]
    frames = ["f03"] if rng.random() < 0.15 else []
    return {"builds": [{"id": "bld", "origin": origin, "generators": gens, "role": role, "frames": frames, "src": "seed"}]}


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    rng = random.Random(int(sys.argv[2]) if len(sys.argv) > 2 else 1)
    budget = int(sys.argv[3]) if len(sys.argv) > 3 else 240
    report = sys.argv[4] if len(sys.argv) > 4 else os.path.join(HERE, "fuzz_report.json")
    rows = []
    disagree = skipped = 0
    for k in range(N):
        w = random_build(rng)
        b = w["builds"][0]
        t0 = time.time()
        try:
            out = PR.solve_world(w, budget=budget)
        except Exception as e:
            out = {"verdict": "ERROR", "error": repr(e)}
        t1 = time.time()
        info = C.world_info(w)
        opool, problems = SC.output_pool(out, info)
        tr = RF.truth(w, opool)
        same = V.decision_equal(out, tr)
        bad = problems["false_witness"] or problems["bad_proof"]
        if tr["verdict"] == "OUTSIDE_W":
            # no witness of the largest candidate from the procedure: a generator would have to give one (V8);
            # not comparable here, and not counted
            print(f"{k:3d} SKIP   {b['origin']} {b['frames']} {b['role']}  (no top witness; procedure {V.summary_safe(out)})",
                  flush=True)
            skipped += 1
            continue
        if not same or bad:
            disagree += 1
        rows.append({"role": b["role"], "origin": b["origin"], "frames": b["frames"],
                     "procedure": V.summary_safe(out), "truth": V.summary_safe(tr), "agree": same,
                     "problems": problems, "t_proc": round(t1 - t0, 1), "t_ref": round(time.time() - t1, 1)})
        print(f"{k:3d} {'AGREE ' if same and not bad else 'DIFFER'} {b['origin']} {b['frames']} {b['role']}  "
              f"proc {V.summary_safe(out)}" + ("" if same else f"  truth {V.summary_safe(tr)}")
              + (f"  PROBLEMS {problems}" if bad else "") + f"  ({t1 - t0:.0f}s)", flush=True)
    with open(report, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rows, fh, indent=1, default=str)
    print(f"\n{N - skipped - disagree} of {N - skipped} comparable builds agree ({skipped} skipped: no top witness)")


if __name__ == "__main__":
    main()
