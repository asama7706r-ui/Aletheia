"""Aletheia blind test 4 -- world validator, run by the world generator before it publishes the key hash.

Usage:  python validate_v4.py <worlds_dir> <key.json> [--no-composition] [--dev]

It checks every world against the validity rules V1-V13 (protocol section 3), the key against the
reference answers (V12, section 5), and the whole set against the composition of section 6.
It prints VALID, or every problem found. It never prints a reference answer that the key does not
already state, and it never imports the procedure.
"""
import os
import re
import sys

import ref_v4 as R
from score_v4 import key_problems

FILE_RE = re.compile(r"^W-(0[1-9]|[12][0-9]|30)\.json$")


def composition(per_world):
    """protocol section 6, on the valid worlds. per_world: wid -> (rw, cards)."""
    p = []
    single = {w: x for w, x in per_world.items() if len(x[0].fillers) == 1}
    several = {w: x for w, x in per_world.items() if len(x[0].fillers) >= 2}
    if len(per_world) != 30:
        p.append(f"30 worlds needed, {len(per_world)} valid")
    if len(single) != 25 or len(several) != 5:
        p.append(f"25 single-filler and 5 several-filler worlds needed, got {len(single)} and {len(several)}")
    want = {"SAME_LAW_NEW_STATE": 7, "ANOTHER_LAW": 8, "INVALID": 3, "CONDITIONAL": 7}
    got = {v: 0 for v in want}
    f3_only = 0
    for rw, cards in single.values():
        c = cards[rw.fillers[0].id]
        got[c["verdict"]] += 1
        if c["verdict"] == "ANOTHER_LAW" and c["reason"] == [("F3", None)] and c["group_agrees"]:
            f3_only += 1
    if got != want:
        p.append(f"single-filler verdicts {got}, needed {want}")
    if f3_only < 2:
        p.append(f"{f3_only} ANOTHER_LAW worlds decided by F3 alone, at least 2 needed")
    third = sum(any(c["verdict"] in ("ANOTHER_LAW", "INVALID") for c in cards.values())
                for rw, cards in several.values())
    if third < 2:
        p.append(f"{third} several-filler worlds with an ANOTHER_LAW or INVALID filler, at least 2 needed")
    traps = {}
    types = {"kind": set(), "meaning": set(), "cast": set()}
    wrong = {m: 0 for m in R.BASELINES}
    prints = {}
    for wid, (rw, cards) in per_world.items():
        labels = set()
        for F in rw.fillers:
            c = cards[F.id]
            labels |= R.traps_of(rw, F, c)
            for ty in R.decided_types(rw, c):
                types[ty].add(wid)
            for m in R.BASELINES:
                wrong[m] += c["baselines"][m]["verdict"] != c["verdict"]
        if len(rw.fillers) >= 2:
            labels.add("T9")
        for lab in labels:
            traps.setdefault(lab, set()).add(wid)
        prints.setdefault(R.fingerprint(rw), []).append(wid)
    for t in ("T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9"):
        if len(traps.get(t, ())) < 2:
            p.append(f"trap {t} appears in {len(traps.get(t, ()))} worlds, at least 2 needed")
    for lab, need in (("T2:m06", 1), ("T7:card", 2), ("T7:meaning", 2), ("T8:m23", 1), ("T8:axial", 1)):
        if len(traps.get(lab, ())) < need:
            p.append(f"{lab}: {len(traps.get(lab, ()))} worlds, at least {need} needed")
    for ty, ws in types.items():
        if len(ws) < 2:
            p.append(f"{ty}-reading transformations decide {len(ws)} worlds, at least 2 needed")
    for m, k in wrong.items():
        if k < 8:
            p.append(f"baseline {m} errs on {k} fillers, at least 8 needed")
    for fp, ws in prints.items():
        if len(ws) > 1:
            p.append(f"worlds {ws} share the same law and filled laws")
    return p


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    worlds_dir, key_path = argv[1], argv[2]
    check_comp = "--no-composition" not in argv
    if "--dev" in argv:
        R.ALLOW_DEV = True     # dev worlds only; never used on the test worlds
    reg = R.load_registry()
    try:
        key = {e["id"]: e for e in R.load_json(key_path)}
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"cannot read the key: {e}")
        return 1
    problems, valid = [], {}
    for fn in R.world_files(worlds_dir):
        wid = fn[:-5]
        if check_comp and not FILE_RE.match(fn):
            problems.append(f"{fn}: file names must be W-01.json ... W-30.json")
        try:
            rw, cards = R.reference(R.load_json(os.path.join(worlds_dir, fn)), reg)
        except R.Invalid as e:
            problems.append(f"{wid}: {e}")
            continue
        except Exception as e:  # a crash is a problem of the world or of the validator; never silent
            problems.append(f"{wid}: validator error {type(e).__name__}: {e}")
            continue
        if wid not in key:
            problems.append(f"{wid}: no key entry")
            continue
        kp = key_problems(rw, cards, key[wid])
        if kp:
            problems += [f"{wid}: V12 {x}" for x in kp]
            continue
        valid[wid] = (rw, cards)
    extra = set(key) - {fn[:-5] for fn in R.world_files(worlds_dir)}
    if extra:
        problems.append(f"key entries without a world: {sorted(extra)}")
    if check_comp:
        problems += [f"composition: {x}" for x in composition(valid)]
    if problems:
        print("\n".join(problems))
        print(f"NOT VALID ({len(problems)} problems)")
        return 1
    print(f"VALID ({len(valid)} worlds)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
