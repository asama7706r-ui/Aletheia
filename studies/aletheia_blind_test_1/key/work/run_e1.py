import sys, json
from wcheck import *
import designs_e1

wid = sys.argv[1]
slot = json.load(open(ROOT + "/key/shuffle_private.json"))[wid]
world, key, extra = designs_e1.DESIGNS[slot]()
world = {"id": wid, **world}
key = {"id": wid, **key}
errs, info = check_E1(world, key, extra)
print(wid, "checks:", "PASS" if not errs else "FAIL")
if errs:
    print(errs)
else:
    save_world_and_key(world, key)
    nxt = "E1-%02d" % (int(wid[3:]) + 1) if int(wid[3:]) < 28 else "E2-01"
    print(update_progress("%s saved; next %s" % (wid, nxt)))
