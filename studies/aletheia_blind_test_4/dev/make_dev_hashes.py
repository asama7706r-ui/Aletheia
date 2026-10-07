# Test 4 dev tool: print the SHA-256 fingerprints (law and sorted filled laws) of the dev worlds, for
# DEV_HASHES in scorer/ref_v4.py (validity rule V11). Run after make_dev.py.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scorer"))
import ref_v4 as R  # noqa: E402

reg = R.load_registry()
prints = set()
for fn in R.world_files(os.path.join(HERE, "worlds")):
    rw = R.RWorld(R.load_json(os.path.join(HERE, "worlds", fn)), reg)
    prints.add(R.fingerprint(rw))
print("DEV_HASHES = {")
for h in sorted(prints):
    print(f'    "{h}",')
print("}")
