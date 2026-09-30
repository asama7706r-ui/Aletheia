import json
from wcheck import ROOT, PARAM_GRID, fstr
import designs_e1, designs_e2
shuffle = json.load(open(ROOT + "/key/shuffle_private.json"))
spec = {"E1_UND": {}, "E2_extra": {}}
def dec(special, default):
    return {fstr(c): special.get(fstr(c), default) for c in PARAM_GRID}
# the three underdetermined worlds that were built individually
spec["E1_UND"]["E1-03"] = {"roles": ["a", "b"], "decisions": dec({"0": "SUBSUMED", "3": "SUBSUMED"}, "NEW_KIND:comm")}
spec["E1_UND"]["E1-07"] = {"roles": ["a", "b", "b*a"], "decisions": dec({"0": "NEW_KIND:assoc", "1": "NEW_KIND:assoc"}, "CONTRADICTION")}
spec["E1_UND"]["E1-15"] = {"roles": ["x", "y"], "decisions": dec({"1": "SUBSUMED"}, "CONTRADICTION")}
for wid, slot in shuffle.items():
    if wid.startswith("E1-") and slot in designs_e1.DESIGNS and slot.startswith("UND"):
        w, k, x = designs_e1.DESIGNS[slot]()
        spec["E1_UND"][wid] = {"roles": x["roles"], "decisions": {v: e["decision"] for v, e in x["und"].items()}}
    if wid.startswith("E2-"):
        w, k, x = designs_e2.DESIGNS[slot]()
        if x:
            spec["E2_extra"][wid] = x
json.dump(spec, open(ROOT + "/key/verify_spec.json", "w"), indent=1)
print("spec written:", len(spec["E1_UND"]), "E1 entries,", len(spec["E2_extra"]), "E2 entries")
