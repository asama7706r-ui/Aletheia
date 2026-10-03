"""Differential test of Part B (development only): random cabinets and random items.

For each random item it compares the procedure's reopened list with the reference rules R1-R3, compares
the recomputed answers of the reopened files, and checks rule soundness: no file outside the list may
change its answer. Random worlds are throwaway sanity checks, not test worlds.

Usage:  python fuzz_partb.py [n_items] [seed]
"""
import copy
import os
import random
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "procedure"))
sys.path.insert(0, os.path.join(HERE, "..", "scorer"))
import fuzz_compare as FZ  # noqa: E402
import procedure_v3 as P  # noqa: E402
import ref_v3 as R  # noqa: E402


def loadable(w):
    try:
        rw = R.RWorld(w)
        a = R.analyse(rw)
        P.analyse(P.World(w))
        return rw, a
    except (R.Invalid, P.WorldError):
        return None


def cabinet(rng, start):
    worlds, i = {}, start
    while len(worlds) < 4:
        w = FZ.rand_world(rng, i)
        i += 1
        if w is None or loadable(w) is None:
            continue
        worlds[w["id"]] = w
        if len(worlds) == 1:   # a sibling sharing the observable, with other new readings
            sib = copy.deepcopy(w)
            sib["id"] = w["id"] + "s"
            for o in sib["new_observations"]:
                o["value"] = R.s(Fraction(o["value"]) + Fraction(rng.randint(-20, 20), 10))
            if loadable(sib) is not None:
                worlds[sib["id"]] = sib
    return worlds, i


def rand_item(rng, worlds):
    t = rng.choice(["observation", "relation", "root"])
    wid = rng.choice(sorted(worlds))
    w = worlds[wid]
    if t == "observation":
        p = rng.choice(w["possible_observations"])
        return {"id": "X", "experiment": "B", "type": "observation", "world": wid, "state": p["state"],
                "observer": p["observer"], "value": R.s(FZ.rq(rng, -40, 40))}
    if t == "relation":
        qs = [q for q in w["quantities"] if q != w["observable"]]
        rel = {"id": "R9", "object": "o0", "term": FZ.rand_term(rng, qs, list(w["constants"])),
               "coefficient": "unknown", "coverage": None}
        return {"id": "X", "experiment": "B", "type": "relation", "observable": w["observable"], "relation": rel}
    if w["constants"] and rng.random() < 0.6:
        c = rng.choice(sorted(w["constants"]))
        return {"id": "X", "experiment": "B", "type": "root", "constant": c,
                "new_value": R.s(Fraction(rng.randint(1, 9), rng.choice([1, 2, 5])))}
    o = rng.choice(sorted(w["observers"]))
    return {"id": "X", "experiment": "B", "type": "root", "observer": o,
            "new_precision": R.s(Fraction(rng.randint(0, 20), rng.choice([10, 20])))}


def main(n=400, seed=3):
    rng = random.Random(seed)
    stats = {"items": 0, "agree": 0, "mismatch": 0, "skipped": 0, "reopened_nonempty": 0, "changed": 0}
    idx = 0
    while stats["items"] < n:
        worlds, idx = cabinet(rng, idx)
        ref = {wid: loadable(w) for wid, w in worlds.items()}
        files = {wid: P.analyse(P.World(w)) for wid, w in worlds.items()}
        for _ in range(5):
            item = rand_item(rng, worlds)
            try:
                rl_ref = R.ref_reopen(item, worlds, ref)
            except R.Invalid:
                stats["skipped"] += 1
                continue
            after = {}
            ok = True
            for wid, w in worlds.items():
                nw, changed = R.apply_item(w, item)
                if changed:
                    got = loadable(nw)
                    if got is None:
                        ok = False
                        break
                    after[wid] = (nw, got)
            if not ok:
                stats["skipped"] += 1
                continue
            stats["items"] += 1
            rl_proc = P.reopen_list(item, worlds, files)
            probs = []
            if rl_proc != rl_ref:
                probs.append("lists %s vs %s" % (rl_proc, rl_ref))
            for wid in rl_ref:
                nw, (rw2, a2) = after.get(wid, (worlds[wid], ref[wid]))
                pa = R.norm_answer(P.analyse(P.World(nw), proofs=False))
                if pa != R.answer_of(a2):
                    probs.append("final %s: %s vs %s" % (wid, pa, R.answer_of(a2)))
                if R.answer_of(a2) != R.answer_of(ref[wid][1]):
                    stats["changed"] += 1
            for wid, (nw, (rw2, a2)) in after.items():
                if wid not in rl_ref and R.answer_of(a2) != R.answer_of(ref[wid][1]):
                    probs.append("rule gap: %s changed outside the list (%s)" % (wid, item["type"]))
            stats["reopened_nonempty"] += bool(rl_ref)
            if probs:
                stats["mismatch"] += 1
                print("MISMATCH", item, probs)
            else:
                stats["agree"] += 1
    print(stats)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 400, int(sys.argv[2]) if len(sys.argv) > 2 else 3)
