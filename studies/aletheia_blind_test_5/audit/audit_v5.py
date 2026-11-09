"""The audit of blind test 5 (protocol_v5.md, Section 0, order step 7: "then a separate audit").
Written after the outputs hashes were published and the keys opened; it reads the worlds, the keys, the
outputs and the reports, and changes none of them. Not pre-registered: every number here is a diagnostic.
Usage (from aletheia_blind_test_5/): python -I audit/audit_v5.py > audit/audit_out.txt

(The rules-or-evidence question is answered by audit/diag_inject.py: an output does not carry every
refutation the procedure found, so a truth assembled from the output's certificates alone cannot answer it.)
2. Each wrong world: missing witness (same drop sets, other statuses) or missing refutation (other drop sets).
3. For each candidate the procedure kept but the truth refutes: does the reference's own bounded search refute
   it (then only the procedure missed it), or only the key's certificate (a blind spot both share, limit 10)?
4. The "reported only" counts of Section 8.3 that the sealed scorer does not print.
5. Accuracy by verdict and by trap; time per world.
6. Families of worlds: the same role up to renaming the generators and changing the numbers."""
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scorer"))
import certs_v5 as C  # noqa: E402
import ref_v5 as RF  # noqa: E402
import score_v5 as S  # noqa: E402
import validate_v5 as V  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")


def keyset(drop):
    return tuple(sorted(drop))


def truth_sets(t):
    """Drop sets of a truth's branches, each mirror pair as both members."""
    out = set()
    for b in t.get("branches") or []:
        out.add(keyset(b["drop"]))
        if b.get("mirror"):
            out.add(keyset(b["mirror"]["twin"]))
    return out


def skeleton(info, role):
    names = {g: f"g{i + 1}" for i, g in enumerate(info["generators"])}
    out = []
    for s in role:
        s = re.sub(r"(?<![A-Za-z0-9_])\d+(/\d+)?", "#", s)
        s = re.sub(r"[A-Za-z][A-Za-z0-9]*", lambda m: names.get(m.group(0), m.group(0)), s)
        out.append(s)
    return (info["origin"], tuple(info["frames"]), tuple(sorted(out)))


def times(batch):
    t = {}
    for line in open(f"results/run_{batch}.log", encoding="utf-8"):
        m = re.match(r"(W-\d+)\.json: (\w+) \(([\d.]+)s\)", line.strip())
        if m:
            t[m.group(1)] = float(m.group(3))
    return t


def audit(batch):
    print(f"\n==================== batch {batch}")
    key = {e["id"]: e for e in json.load(open(f"batch_{batch}/key/key.json", encoding="utf-8"))}
    outs = json.load(open(f"results/outputs_{batch}.json", encoding="utf-8"))
    rep = json.load(open(f"results/report_{batch}.json", encoding="utf-8"))["worlds"]
    tm = times(batch)
    kinds, shared_spot, proc_only = {}, [], []
    added_decided, unmerged, nw_where_witness = [], [], []
    by_verdict, by_trap, fam = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0]), defaultdict(list)
    for wid in sorted(key):
        path = f"batch_{batch}/worlds/{wid}.json"
        world = C.R.load(path)
        info = C.world_info(world)
        out = outs[wid]["procedure"]
        row = rep[wid]
        ok = row["decision_ok"]
        role = json.load(open(path, encoding="utf-8"))["builds"][0]["role"]
        fam[skeleton(info, role)].append((wid, ok))
        opool, _ = S.output_pool(out, info)
        tv = row["truth"][0]
        by_verdict[tv][0] += 1
        by_verdict[tv][1] += ok
        for t in key[wid].get("traps") or []:
            by_trap[t][0] += 1
            by_trap[t][1] += ok
        if ok:
            continue
        # 2. the kind of error, from the full truth (key + procedure + the reference's search)
        full_pool = S.merge_pools(V.key_pool(key[wid], info), opool)
        tf, cl = RF.truth_full(world, full_pool)
        tsets, osets = truth_sets(tf), {keyset(b["drop"]) for b in out.get("branches") or []}
        for b in out.get("branches") or []:
            if b.get("mirror"):
                osets.add(keyset(b["mirror"]["twin"]))
        extra = sorted(osets - tsets)
        if out.get("verdict") in ("NEW_KIND", "BRANCHES", "NO_WITNESS") and not extra and osets == tsets:
            kinds[wid] = "missing witness (same drop sets, a witnessed branch reported as no_witness)"
        else:
            kinds[wid] = f"missing refutation: the output keeps {len(extra)} candidate(s) the truth refutes"
        # 3. who refutes each extra candidate
        for d in extra:
            st = cl.status(frozenset(d)) if cl else "?"
            if st == "REFUTED":
                added_decided.append((wid, list(d)))
            ref = RF.search_refutation(info, list(d))
            (proc_only if ref is not None else shared_spot).append((wid, list(d)))
        # 4. reported-only counts
        tw = {keyset(b["drop"]) for b in tf.get("branches") or [] if b["status"] == "witnessed"}
        if out.get("verdict") == "NO_WITNESS" and tf["verdict"] in ("NEW_KIND", "BRANCHES"):
            nw_where_witness.append(wid)
        for b in tf.get("branches") or []:
            if b.get("mirror"):
                pair = {keyset(b["drop"]), keyset(b["mirror"]["twin"])}
                plain = [keyset(o["drop"]) for o in out.get("branches") or [] if not o.get("mirror")]
                if pair <= set(plain):
                    unmerged.append((wid, sorted(pair)))
        _ = tw
    print("\n2. Wrong worlds:")
    for wid in sorted(kinds):
        print(f"   {wid}: {kinds[wid]}; time {tm.get(wid)} s; traps {key[wid].get('traps')}")
    print("\n3. Candidates the procedure kept but the truth refutes:")
    for wid, d in shared_spot:
        print(f"   {wid} {d}: the reference's own search does NOT refute it either (only the key's certificate)")
    for wid, d in proc_only:
        print(f"   {wid} {d}: the reference's own search refutes it (the procedure alone missed it)")
    print("\n4. Reported-only counts of Section 8.3 (not printed by the sealed scorer):")
    print(f"   branches the output adds where a valid proof decides: {len(added_decided)} in "
          f"{len({w for w, _ in added_decided})} worlds {sorted({w for w, _ in added_decided})}")
    print(f"   unmerged mirror twins: {len(unmerged)} {unmerged}")
    print(f"   NO_WITNESS answers where the truth has a witness: {len(nw_where_witness)} {nw_where_witness}")
    print("\n5. Decision accuracy by the truth's verdict:")
    for v, (n, k) in sorted(by_verdict.items()):
        print(f"   {v:15s} {k} of {n}")
    print("   by declared trap:")
    for t, (n, k) in sorted(by_trap.items(), key=lambda x: int(x[0][1:])):
        print(f"   {t:4s} {k} of {n}")
    slow = sorted(((s, w) for w, s in tm.items() if s >= 60), reverse=True)
    print(f"   worlds over 60 s: {[(w, s) for s, w in slow]}; total {sum(tm.values()):.0f} s")
    print("\n6. Families (same role up to renaming the generators and changing the numbers):")
    groups = sorted(fam.values(), key=lambda g: g[0][0])
    print(f"   {len(groups)} families for {sum(len(g) for g in groups)} worlds")
    for g in groups:
        if len(g) > 1:
            print("   " + ", ".join(f"{w} {'OK' if ok else 'WRONG'}" for w, ok in g))


if __name__ == "__main__":
    os.chdir(os.path.dirname(HERE))
    for b in (sys.argv[1:] or ["A", "B"]):
        audit(b)
