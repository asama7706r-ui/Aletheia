"""Write the four coded demands as v0.5 world files (PREREG_ADDENDUM_2, rules T1-T4), read against the test-5 seed tower.
T3: for the units the author names as independent, every pair u, v gets u != v and u != -v (the unit 1 included)."""
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "aletheia_blind_test_5", "lang"))
import reader_v0 as R  # noqa: E402

SEED = os.path.join(os.path.dirname(ROOT), "aletheia_blind_test_5", "seed", "seed_registry.json")
reg = json.load(open(SEED, encoding="utf-8"))
ctx, info = R.check_registry(reg)
assert not ctx.errors, ctx.errors
SHA = R.sha256_of(info["canon"])


def distinct(units):
    out = []
    for u, v in itertools.combinations(units, 2):
        out += [f"{v} != {u}", f"{v} != -{u}" if u != "1" else f"{v} != -1"]
    return out


QUAT = ["i*i = -1", "j*j = -1", "k*k = -1", "i*j = k", "j*i = -k", "j*k = i", "k*j = -i", "k*i = j", "i*k = -j"]
CASES = {
    # C1 Cockle 1848: a new j with j^2 = 1, not +-1, beside the ordinary i (origin: complex numbers, e1 = i)
    "C1_tessarines": ("k02", ["j"], ["j*j = 1"] + distinct(["1", "e1", "j"])[2:]),
    # C2 Segre 1892 (tricomplex): new units h, l with square -1, independent of 1 and i and of each other
    "C2_multicomplex": ("k02", ["h", "l"], ["h*h = -1", "l*l = -1"] + distinct(["1", "e1", "h", "l"])[2:]),
    # C3 Macfarlane 1891: squares +1 with Hamilton's cyclic rules (origin: reals)
    "C3_hyperbolic_quaternions": ("k01", ["i", "j", "k"],
                                  ["i*i = 1", "j*j = 1", "k*k = 1", "i*j = k", "j*i = -k", "j*k = i", "k*j = -i",
                                   "k*i = j", "i*k = -j"] + distinct(["1", "i", "j", "k"])),
    # C4 Clifford 1873: quaternions given (T2), and a new w with w^2 = 1 (elliptic case)
    "C4_split_biquaternions": ("k01", ["i", "j", "k", "w"], QUAT + ["w*w = 1"] + distinct(["1", "i", "j", "k", "w"])),
}
for name, (origin, gens, role) in CASES.items():
    world = {"v0": "0.5", "file": "world", "id": name.lower(), "registry": "t5_tower", "registry_sha256": SHA,
             "bodies": [], "quantities": [], "relations": [], "laws": [], "observers": [], "observations": [],
             "fillers": [], "builds": [{"id": "b1", "origin": origin, "generators": gens, "role": role,
                                        "frames": [], "src": "seed"}]}
    wctx, canon = R.check_world(world, info)
    print(name, "OK" if not wctx.errors else wctx.errors, "| role sentences:", len(role))
    with open(os.path.join(ROOT, "predictions", "roles", name + ".json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(world, fh, ensure_ascii=False, indent=1)
