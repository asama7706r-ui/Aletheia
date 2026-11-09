"""Audit (not pre-registered): what do the missing refutations look like?
For every branch the output added where a valid proof decides (the scorer's reported_only list), find the key
refutations that the sealed checker accepts for that branch's candidate, and describe each one:
its field (theta), its case nodes (split by q12/q14 with the two factors, inverse by q13), whether it uses the
order rule's "positive" node, its number of terms, the longest multiplier word, and the copy instances it uses.
Only the sealed checker runs here (no search), so this is fast.
Usage (from aletheia_blind_test_5b/): python -I audit/refutation_shapes_5b.py"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scorer"))
import certs_v5 as C  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")


def describe(tree):
    info = {"nodes": [], "terms": 0, "longest_path": 0, "units": set(), "depth": 0}

    def walk(nd, depth):
        info["depth"] = max(info["depth"], depth)
        k = nd["node"]
        if k == "split":
            info["nodes"].append(f"split by {nd['by']}: ({json.dumps(nd['a'])})*({json.dumps(nd['b'])})")
        elif k == "inverse":
            info["nodes"].append(f"inverse of {json.dumps(nd['a'])} as {nd['v']}")
        elif k == "positive":
            info["nodes"].append(f"positive (q14): c={nd['c']}, {len(nd['t'])} squares")
        for key in ("terms", "proof_ab"):
            for t in nd.get(key) or []:
                info["terms"] += 1
                info["longest_path"] = max(info["longest_path"], len(t[2]))
                if isinstance(t[1], dict) and "unit" in t[1]:
                    info["units"].add(f"{t[1]['unit']}{json.dumps(t[1].get('args', {}), sort_keys=True)}")
        for kid in nd.get("children") or []:
            walk(kid, depth + 1)

    walk(tree, 0)
    return info


def main():
    for batch in "AB":
        rep = json.load(open(os.path.join(ROOT, "results", f"report_{batch}.json"), encoding="utf-8"))["worlds"]
        key = {e["id"]: e for e in json.load(open(os.path.join(ROOT, f"batch_{batch}", "key", "key.json"),
                                                  encoding="utf-8"))}
        for wid in sorted(rep):
            added = rep[wid]["reported"]["branches_added_where_a_proof_decides"]
            if not added:
                continue
            path = os.path.join(ROOT, f"batch_{batch}", "worlds", f"{wid}.json")
            winfo = C.world_info(C.R.load(path))
            for d in added:
                print(f"{batch} {wid}: output branch drops {d}")
                hits = 0
                for i, r in enumerate(key[wid].get("refutations") or []):
                    if not C.safe(C.check_refutation, r["proof"], winfo, d)[0]:
                        continue
                    hits += 1
                    s = describe(r["proof"]["tree"])
                    print(f"  key refutation #{i} (written for drop {r['drop']}): theta {r['proof'].get('theta')}, "
                          f"case depth {s['depth']}, {s['terms']} terms, longest multiplier path {s['longest_path']}")
                    for n in s["nodes"]:
                        print(f"    {n}")
                    if s["units"]:
                        print(f"    copy instances: {', '.join(sorted(s['units']))}")
                if not hits:
                    print("  no key refutation is accepted for it (the truth refutes it by another route)")


if __name__ == "__main__":
    main()
