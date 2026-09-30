import sys, json
import sympy as sp
from wcheck2 import *
import designs_e2

wid = sys.argv[1]
slot = json.load(open(ROOT + "/key/shuffle_private.json"))[wid]
world, key, extra = designs_e2.DESIGNS[slot]()
world = {"id": wid, **world}
key = {"id": wid, **key}
errs, signals = check_E2(world, key, extra)
for q in world["quantities"]:
    if hasattr(sp, q):
        errs.append("quantity name shadows a sympy name: " + q)
print(wid, "checks:", "PASS" if not errs else "FAIL")
if errs:
    print(errs)
else:
    save_world_and_key(world, key)
    n = int(wid[3:])
    nxt = "E2-%02d" % (n + 1) if n < 16 else "independent verification script"
    print(update_progress("%s saved; next %s" % (wid, nxt)))
