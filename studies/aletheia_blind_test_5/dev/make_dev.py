"""Dev set of blind test 5 (protocol_v5.md, Section 12): famous cases and toy worlds, written as v0.5
world files in dev/batch_dev/worlds/, with a dev key built from the procedure's own outputs (dev only:
a real key comes from a generator), and the fingerprints for V11 in scorer/dev_fingerprints.json.
Usage: python -I dev/make_dev.py"""
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scorer"))
sys.path.insert(0, os.path.join(ROOT, "procedure"))
import certs_v5 as C  # noqa: E402
import validate_v5 as V  # noqa: E402
import procedure_v5 as PR  # noqa: E402

R = C.R
ANTI = lambda a, b: f"{a}*{b} = -({b}*{a})"  # noqa: E731
DEV = [
    ("sqrt2", "k01", ["xa"], ["xa*xa = 2"], []),
    ("cbrt2", "k01", ["xa"], ["xa*xa*xa = 2"], []),
    ("i_over_r", "k01", ["ui"], ["ui*ui = -1"], []),
    ("sqrt_e1", "k02", ["uu"], ["uu*uu = e1"], []),
    ("x3_minus_x", "k01", ["xa"], ["xa*xa*xa = -xa", "xa != 0"], []),
    ("free1", "k01", ["fx"], ["fx = 0^-1"], []),
    ("free2", "k02", ["fx", "fy"], ["fx = 0^-1", "fy = fx*fx + e1"], []),
    ("imp1", "k01", ["xa"], ["xa = 1", "xa*xa = 2"], []),
    ("imp2", "k02", ["uu"], ["uu = e1", "uu*uu = 1"], []),
    ("imp3", "k01", ["xa", "ya"], ["xa = ya", "xa != ya"], []),
    ("quat", "k01", ["ia", "jb"], ["ia*ia = -1", "jb*jb = -1", ANTI("ia", "jb")], []),
    ("quat_frame", "k01", ["ia", "jb"], ["ia*ia = -1", "jb*jb = -1", ANTI("ia", "jb")], ["f03"]),
    ("quat_chain", "k01", ["ii", "jj", "kk"], ["ii*ii = -1", "jj*jj = -1", "kk*kk = -1", "ii*jj*kk = -1"], []),
    ("quat_brk", "k01", ["ii", "jj", "kk"], ["ii*ii = -1", "jj*jj = -1", "kk*kk = -1", "(ii*jj)*kk = -1"], []),
    ("split_cx", "k01", ["jj"], ["jj*jj = 1", "jj != 1", "jj != -1"], []),
    ("dual", "k01", ["th"], ["th*th = 0", "th != 0"], []),
    ("quat_c", "k02", ["hh"], ["hh*hh = -1", "hh*e1 = -(e1*hh)"], []),
    ("tess_c", "k02", ["jj"], ["jj*jj = 1", "jj != 1", "jj != -1", "jj != e1", "jj != -e1"], []),
    ("cl3", "k01", ["ga", "gb", "gc"], ["ga*ga = 1", "gb*gb = 1", "gc*gc = 1", ANTI("ga", "gb"), ANTI("gb", "gc"),
                                        ANTI("ga", "gc")], []),
    ("dirac", "k01", ["g0", "g1", "g2", "g3"], ["g0*g0 = 1", "g1*g1 = -1", "g2*g2 = -1", "g3*g3 = -1"]
     + [ANTI(f"g{i}", f"g{j}") for i in range(4) for j in range(i + 1, 4)], ["f03"]),
    ("mirror1", "k02", ["xx"], ["(e1*xx)*xx + (xx*xx)*e1 != e1*(xx*xx) + xx*(xx*e1)"], []),
    ("flex", "k01", ["aa", "bb"], ["aa*aa = -1", "bb*bb = -1", "aa*(bb*aa) != (aa*bb)*aa"], []),
]


# hand-made top witnesses (V8) where the procedure's templates do not close
MIRROR_T = [[1, 1, 0, "-1"], [1, 2, 3, "1"], [1, 3, 2, "-1"], [2, 1, 3, "1"], [2, 2, 0, "1"], [2, 3, 1, "-1"],
            [3, 1, 2, "-1"], [3, 2, 1, "1"], [3, 3, 0, "1"]]          # C + Cu, x*y = (ac + b conj(d), ad + bc)
FLEX_T = [[1, 1, 0, "-1"], [2, 2, 0, "-1"], [3, 3, 0, "-1"], [1, 2, 3, "1"], [2, 1, 3, "-1"], [1, 3, 2, "1"],
          [3, 1, 2, "1"], [2, 3, 1, "1"], [3, 2, 1, "-1"]]            # a non-flexible table with a*a = b*b = -1
TOP = {
    "mirror1": {"dim": 4, "table": MIRROR_T, "theta": None, "E": ["0", "1", "0", "0"],
                "gens": {"xx": ["0", "0", "1", "0"]}, "q12": None, "q13": None},
    "flex": {"dim": 4, "table": FLEX_T, "theta": None, "gens": {"aa": ["0", "1", "0", "0"], "bb": ["0", "0", "1", "0"]},
             "q12": None, "q13": None},
}


def world_doc(wid, origin, gens, role, frames, reg_sha):
    return {"v0": "0.5", "file": "world", "id": wid, "registry": "t5_tower", "registry_sha256": reg_sha,
            "bodies": [], "quantities": [], "relations": [], "laws": [], "observers": [], "observations": [],
            "fillers": [], "builds": [{"id": "bld", "origin": origin, "generators": gens, "role": role,
                                       "frames": frames, "src": "seed"}]}


def main():
    reg = V.load_seed()
    sha = R.sha256_of(reg["canon"])
    out_dir = os.path.join(HERE, "batch_dev")
    os.makedirs(os.path.join(out_dir, "worlds"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "key"), exist_ok=True)
    key, fps, outputs = [], [], {}
    for i, (name, origin, gens, role, frames) in enumerate(DEV, 1):
        wid = f"W-{i:02d}"
        doc = world_doc(f"w{i:02d}", origin, gens, role, frames, sha)
        path = os.path.join(out_dir, "worlds", wid + ".json")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, indent=1)
        errs, info = V.form_errors(doc, reg)
        if errs:
            print(f"{wid} {name}: FORM ERRORS {errs}")
            continue
        fps.append(V.role_fingerprint(info))
        t0 = time.time()
        o = PR.solve_world(doc, budget=600)
        outputs[wid] = {"procedure": o}
        entry = {"id": wid, "verdict": o["verdict"], "branches": None, "known": o.get("known"),
                 "freedom": o.get("freedom"), "impossible": o.get("impossible"), "top_witness": None,
                 "refutations": [], "traps": [], "notes": f"dev case {name}"}
        if o["verdict"] in ("NEW_KIND", "BRANCHES", "NO_WITNESS"):
            entry["branches"] = [{"drop": b["drop"], "status": b["status"], "witness": b["witness"],
                                  "mirror": b["mirror"]} for b in o["branches"]]
            w = PR.World(doc, time.time() + 300)
            U = frozenset(w.U)
            top = next((b["witness"] for b in o["branches"] if b["witness"]), None) or w.find_witness(U) or TOP.get(name)
            entry["top_witness"] = top
            for b in o["branches"]:
                for u, p in b["proofs"].items():
                    entry["refutations"].append({"drop": [x for x in b["drop"] if x != u], "proof": p})
        key.append(entry)
        print(f"{wid} {name}: {o['verdict']} {[(b['drop'], b['status']) for b in o.get('branches', [])]} "
              f"({time.time() - t0:.1f}s)", flush=True)
    with open(os.path.join(out_dir, "key", "key.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(key, fh, indent=1)
    with open(os.path.join(out_dir, "outputs_dev.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(outputs, fh, indent=1)
    with open(os.path.join(ROOT, "scorer", "dev_fingerprints.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(sorted(set(fps)), fh, indent=1)
    print(f"wrote {len(key)} dev worlds and {len(set(fps))} fingerprints")


if __name__ == "__main__":
    main()
