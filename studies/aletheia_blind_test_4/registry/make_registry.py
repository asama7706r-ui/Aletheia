# Test 4: the registry (sealed 2026-10-07). Builds registry.json in the v0.4 language,
# checks it with the strict reader, and prints its SHA-256.
#   python make_registry.py
# Meaning, instrument and body-type ids are neutral (m01, i01, ty01) so that names carry no meaning;
# the human-readable mapping and the source of every action are in registry_notes.md.
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lang"))
import reader_v0 as R  # noqa: E402

S = "seed"
ONE = "1"
POLAR = [["-1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]]     # x -> -x on an ordinary (polar) vector
AXIAL = [["1", "0", "0"], ["0", "-1", "0"], ["0", "0", "-1"]]    # x -> -x on an axial vector (det(R) R)
CONJ = [["1", "0"], ["0", "-1"]]                                 # complex conjugation on (real, imaginary)
QUARTER_Z = [["0", "-1", "0"], ["1", "0", "0"], ["0", "0", "1"]]  # a quarter turn about z


def meaning(mid, kind, anchor, t, p, c, conditions=()):
    """t, p, c: actions of time reversal, the reflection x -> -x, and charge conjugation."""
    return {"id": mid, "kind": kind, "anchor": anchor, "conditions": list(conditions),
            "under": {"rev_t": t, "refl_x": p, "conj_c": c}, "src": S}


def inst(i):
    return {"instrument": i}


SEED = {"seed": "human"}
DER = lambda d: {"derived": d}  # noqa: E731

registry = {
    "v0": "0.4", "file": "registry", "id": "test4_registry", "catalog": "1",
    "dimensions": ["L", "M", "Q", "T"],
    "floors": [
        {"id": "number", "depends_on": [], "src": S},
        {"id": "vector", "depends_on": ["number"], "src": S},
        {"id": "complex", "depends_on": ["number"], "src": S},
    ],
    "kinds": [
        {"id": "scalar", "floor": "number", "over": "fractions", "shape": [], "generators": [], "relations": [],
         "under": {"rot_z": ONE}, "src": S},
        {"id": "vec3", "floor": "vector", "over": "fractions", "shape": [3], "generators": [], "relations": [],
         "under": {"rot_z": QUARTER_Z}, "src": S},
        {"id": "cplx", "floor": "complex", "over": "fractions", "shape": [2], "generators": [], "relations": [],
         "under": {"rot_z": ONE}, "src": S},
    ],
    "transformations": [
        {"id": "rev_t", "reads": "meaning", "src": S},    # time reversal
        {"id": "refl_x", "reads": "meaning", "src": S},   # reflection of one axis, x -> -x
        {"id": "conj_c", "reads": "meaning", "src": S},   # charge conjugation
        {"id": "rot_z", "reads": "kind", "src": S},       # a quarter turn about z
        {"id": "exch", "reads": "cast", "src": S},        # exchange of two bodies of the same type
    ],
    "instruments": [
        {"id": "i01", "unit": {"T": 1}, "src": S},                        # clock
        {"id": "i02", "unit": {"L": 1}, "src": S},                        # ruler
        {"id": "i03", "unit": {"M": 1}, "src": S},                        # balance
        {"id": "i04", "unit": {"M": 1, "L": 2, "T": -2}, "src": S},       # calorimeter
        {"id": "i05", "unit": {"Q": 1}, "src": S},                        # electrometer
        {"id": "i06", "unit": {"M": 1, "L": 1, "T": -2}, "src": S},       # dynamometer
        {"id": "i07", "unit": {"M": 1, "L": 1, "T": -2, "Q": -1}, "src": S},  # electric field probe
        {"id": "i08", "unit": {"M": 1, "T": -1, "Q": -1}, "src": S},      # magnetometer
    ],
    "meanings": [
        # scalars
        meaning("m01", "scalar", inst("i01"), "-1", ONE, ONE),                       # time
        meaning("m02", "scalar", inst("i03"), ONE, ONE, ONE, ["m02 > 0"]),           # mass
        meaning("m03", "scalar", inst("i04"), ONE, ONE, ONE),                        # energy
        meaning("m04", "scalar", inst("i05"), ONE, ONE, "-1"),                       # electric charge
        meaning("m05", "scalar", SEED, ONE, ONE, ONE, ["m05 > 0"]),                  # spring stiffness
        meaning("m06", "scalar", SEED, ONE, ONE, ONE, ["m06 > 0"]),                  # damping coefficient (material)
        meaning("m07", "scalar", SEED, ONE, ONE, ONE),                               # coupling constant
        meaning("m08", "scalar", SEED, ONE, ONE, "-1"),                              # charge density
        meaning("m09", "scalar", SEED, ONE, "?", ONE),                               # coupling, parity never tested
        meaning("m10", "scalar", SEED, "?", ONE, ONE),                               # field, time reversal never tested
        meaning("m11", "scalar", inst("i02"), ONE, ONE, ONE, ["m11 > 0"]),           # distance between two bodies
        # 3-vectors
        meaning("m12", "vec3", inst("i02"), ONE, POLAR, ONE),                        # position
        meaning("m13", "vec3", DER("d01"), DER("d01"), DER("d01"), DER("d01")),      # velocity
        meaning("m14", "vec3", DER("d02"), DER("d02"), DER("d02"), DER("d02")),      # acceleration
        meaning("m15", "vec3", DER("d03"), DER("d03"), DER("d03"), DER("d03")),      # momentum
        meaning("m16", "vec3", inst("i06"), ONE, POLAR, ONE),                        # force
        meaning("m17", "vec3", inst("i07"), ONE, POLAR, "-1"),                       # electric field
        meaning("m18", "vec3", inst("i08"), "-1", AXIAL, "-1"),                      # magnetic field
        meaning("m19", "vec3", SEED, "-1", AXIAL, ONE),                              # angular momentum
        meaning("m20", "vec3", SEED, ONE, AXIAL, ONE),                               # torque
        meaning("m21", "vec3", SEED, ONE, POLAR, ONE),                               # free-fall field (gravity)
        meaning("m22", "vec3", SEED, "-1", POLAR, ONE),                              # velocity of a moving observer
        # complex
        meaning("m23", "cplx", SEED, CONJ, ONE, CONJ),                               # charged scalar field
    ],
    "definitions": [
        {"id": "d01", "eq": "m13 = D(m12, m01)", "src": S},   # velocity = rate of change of position
        {"id": "d02", "eq": "m14 = D(m13, m01)", "src": S},   # acceleration = rate of change of velocity
        {"id": "d03", "eq": "m15 = m02*m13", "src": S},       # momentum = mass times velocity
    ],
    "body_types": [{"id": f"ty{i:02d}", "src": S} for i in range(1, 9)],
}

if __name__ == "__main__":
    ctx, info = R.check_registry(registry)
    if ctx.errors:
        print("\n".join(ctx.errors))
        sys.exit(1)
    out = os.path.join(HERE, "registry.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(registry, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(f"OK  registry.json  sha256={R.sha256_of(info['canon'])}")
