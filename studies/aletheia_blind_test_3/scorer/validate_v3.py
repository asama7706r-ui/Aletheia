"""Aletheia blind test 3 -- world validator v3 (sealed together with the scorer).

For the world generator: run it on the generated worlds, items and key BEFORE the key hash is
published, and repair the files until it prints VALID. It does not import the procedure; it uses the
independent reference ref_v3 (the same code the scorer uses).

Checks: every Part A world (W1-W10) and its key entry; the Part A composition (protocol section 6);
every Part B item (validity, key, declared category) and the Part B composition (section 10.1).

Usage:  python validate_v3.py <worlds_dir> <data_dir> <key.json>
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ref_v3 as R  # noqa: E402
from score_v3 import load_dir  # noqa: E402


def main(worlds_dir, data_dir, key_path):
    worlds = load_dir(worlds_dir, "A")
    items = load_dir(data_dir, "B")
    with open(key_path, encoding="utf-8") as fh:
        key = json.load(fh)
    keysA = {k["id"]: k for k in key.get("A", []) if isinstance(k, dict) and "id" in k}
    keysB = {k["id"]: k for k in key.get("B", []) if isinstance(k, dict) and "id" in k}
    problems = []
    if len(worlds) != 27:
        problems.append("Part A: %d worlds, 27 required" % len(worlds))
    if len(items) != 18:
        problems.append("Part B: %d items, 18 required" % len(items))
    extra = (set(keysA) - set(worlds)) | (set(keysB) - set(items))
    if extra:
        problems.append("key entries without a world or item: %s" % sorted(extra))
    cross = R.cross_world_problems(worlds)
    valid = {}
    for wid, raw in sorted(worlds.items()):
        rw, a, p = R.load_and_check(raw)
        p = list(p) + cross.get(wid, [])
        if not p:
            p = R.key_problems_A(a, keysA.get(wid))
            ht = R.hidden_truth_ok(rw, (keysA.get(wid) or {}).get("hidden_truth"))
            if ht is False:
                print("note %s: the hidden truth does not reproduce every reading (reported, not scored)" % wid)
        if p:
            problems.extend("%s: %s" % (wid, x) for x in p)
        else:
            valid[wid] = (rw, a)
            print("%s ok: %s" % (wid, json.dumps(R.answer_of(a))))
    if len(valid) == len(worlds) and worlds:
        comp, unmet = R.composition(valid)
        problems.extend("Part A composition: %s" % x for x in unmet)
        print("Part A composition:", json.dumps({k: v for k, v in comp.items()}, default=list, sort_keys=True))
    else:
        problems.append("Part A composition not checked until every world is valid")
    invalid_worlds = set(worlds) - set(valid)
    cats = {}
    for did, item in sorted(items.items()):
        tw = R.touched(item, worlds)
        if tw & invalid_worlds:
            problems.append("%s: touches invalid worlds %s" % (did, sorted(tw & invalid_worlds)))
            continue
        p, rl, finals, facts = R.check_item(item, {w: worlds[w] for w in valid}, valid)
        if not p:
            p = R.key_problems_B(item, rl, finals, facts, keysB.get(did))
        if p:
            problems.extend("%s: %s" % (did, x) for x in p)
        else:
            cats[did] = (keysB[did]["type"], facts)
            print("%s ok: %s reopens %s" % (did, keysB[did]["type"], rl))
    if len(cats) == len(items) and items:
        counts, unmet = R.item_composition(cats)
        problems.extend("Part B composition: %s" % x for x in unmet)
        print("Part B composition:", json.dumps(counts, sort_keys=True))
    else:
        problems.append("Part B composition not checked until every item is valid")
    for p in problems:
        print("PROBLEM", p)
    print("VALID" if not problems else "INVALID (%d problems)" % len(problems))
    return 0 if not problems else 1


if __name__ == "__main__":
    if len(sys.argv) == 4:
        sys.exit(main(*sys.argv[1:]))
    print(__doc__)
