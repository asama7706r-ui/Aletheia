# Test 4 dev set: toy worlds, one or more per trap (protocol section 12). Writes dev/worlds/*.json and
# dev/key.json. The expected answers in the key were reasoned by hand before running any code; the
# procedure and the independent reference are then compared with them and with each other.
#   python make_dev.py
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "lang"))
import reader_v0 as R  # noqa: E402

REG = json.load(open(os.path.join(ROOT, "registry", "registry.json"), encoding="utf-8"))
_, INFO = R.check_registry(REG)
SHA = R.sha256_of(INFO["canon"])
ENERGY = {"M": 1, "L": 2, "T": -2}


def q(qid, meaning, dims, value="var", owner="world", comps=()):
    return {"id": qid, "meaning": meaning, "owner": owner, "dims": dims, "components": list(comps),
            "value": value, "src": "seed"}


def vec(qid, meaning, dims, value="var", owner="world"):
    return q(qid, meaning, dims, value, owner, [qid + "x", qid + "y", qid + "z"])


def new(qid, kind, meaning, under, value="?", old="0", dims="?", owner="world", comps=(), route="?"):
    return {"id": qid, "kind": kind, "meaning": meaning, "owner": owner, "dims": dims,
            "components": list(comps) if kind != "?" else "?", "under": under, "value": value,
            "old_value": old, "route": route}


ONES = {"rev_t": "1", "refl_x": "1", "conj_c": "1"}


def card(m):
    """the meaning card's actions, copied as the v0.3 rule requires"""
    return dict(next(x for x in REG["meanings"] if x["id"] == m)["under"])


def obs(oid, of, state, value, epoch, observer="ob1"):
    return {"id": oid, "observer": observer, "of": of, "state": {k: str(v) for k, v in state.items()},
            "value": str(value), "epoch": epoch, "src": observer}


def world(wid, quantities, law, observations, fillers, bodies=(), observers=None, inst="i04", prec="1/100"):
    return {"v0": "0.4", "file": "world", "id": wid, "registry": "test4_registry", "registry_sha256": SHA,
            "bodies": [{"id": b, "type": t, "src": "seed"} for b, t in bodies],
            "quantities": quantities, "relations": [],
            "laws": [{"id": "law1", "eq": law, "accepted_at": 0, "src": "seed"}],
            "observers": observers or [{"id": "ob1", "instrument": inst, "precision": prec,
                                        "calibrated_against": [], "src": "seed"}],
            "observations": observations,
            "fillers": [dict(f, of="law1", src="seed") for f in fillers]}


def filler(fid, eq, news, new_bodies=()):
    return {"id": fid, "eq": eq, "new_bodies": [{"id": b, "type": t} for b, t in new_bodies], "new": news}


COUL_Q = [q("uu", "m03", ENERGY), q("kk", "m07", {"M": 1, "L": 3, "T": -2, "Q": -2}, "2"),
          q("qa", "m04", {"Q": 1}), q("qb", "m04", {"Q": 1}), q("dd", "m11", {"L": 1})]
COUL = "uu = kk*qa*qb/dd"

WORLDS, KEY = [], []


def add(w, key):
    WORLDS.append(w)
    KEY.append(key)


# d01 (T1): a third charge must flip with the other two under charge conjugation -> SAME; FIX says ANOTHER.
add(world("dv01", COUL_Q, COUL,
          [obs("o1", "uu", {"qa": 1, "qb": 3, "dd": 2}, 3, 0),
           obs("o2", "uu", {"qa": 1, "qb": 1, "dd": 1}, 6, 1),
           obs("o3", "uu", {"qa": 2, "qb": 1, "dd": 1}, 10, 1)],
          [filler("f1", "uu = kk*qa*qb/dd + kk*qa*qc/dd + kk*qb*qc/dd",
                  [new("qc", "scalar", "m04", card("m04"), dims={"Q": 1}, route="i05")])]),
    {"id": "dv01", "fillers": {"f1": {"verdict": "SAME_LAW_NEW_STATE"}}, "traps": ["T1"],
     "notes": "FIX: ANOTHER (conj_c). zero report: absent."})

# d02 (T2): damping with a coefficient that does not flip under time reversal -> ANOTHER via rev_t.
MECH = [vec("ac", "m14", {"L": 1, "T": -2}), vec("xp", "m12", {"L": 1}), vec("vl", "m13", {"L": 1, "T": -1}),
        q("ms", "m02", {"M": 1}, "2"), q("ks", "m05", {"M": 1, "T": -2}, "4")]
add(world("dv02", MECH, "acx = -ks*xpx/ms",
          [obs("o1", "acx", {"xpx": 1, "vlx": 0}, -2, 0),
           obs("o2", "acx", {"xpx": 1, "vlx": 1}, -3, 1),
           obs("o3", "acx", {"xpx": 0, "vlx": 2}, -2, 1)],
          [filler("f1", "acx = -ks*xpx/ms - gd*vlx/ms",
                  [new("gd", "scalar", "m06", card("m06"))])], inst="i02"),
    {"id": "dv02", "fillers": {"f1": {"verdict": "ANOTHER_LAW", "F2": {"rev_t": "changed"}}}, "traps": ["T2"],
     "notes": "DERIVE and DIMS: SAME. gd inferred M T^-1."})

# d03 (T3): a magnetic field term; B flips under time reversal with the velocity -> SAME; FIX says ANOTHER.
LOR = [vec("ac", "m14", {"L": 1, "T": -2}), vec("vl", "m13", {"L": 1, "T": -1}),
       vec("ef", "m17", {"M": 1, "L": 1, "T": -2, "Q": -1}), q("ch", "m04", {"Q": 1}, "1"),
       q("ms", "m02", {"M": 1}, "1")]
add(world("dv03", LOR, "acx = ch*efx/ms",
          [obs("o1", "acx", {"efx": 2, "vly": 1, "vlz": 0}, 2, 0),
           obs("o2", "acx", {"efx": 2, "vly": 1, "vlz": 0}, 5, 1),
           obs("o3", "acx", {"efx": 0, "vly": 0, "vlz": 1}, -1, 1)],
          [filler("f1", "acx = ch*efx/ms + ch*(vly*bmz - vlz*bmy)/ms",
                  [new("bm", "vec3", "m18", card("m18"), old=["0", "0", "0"],
                       dims={"M": 1, "T": -1, "Q": -1}, comps=["bmx", "bmy", "bmz"], route="i08")])],
          inst="i02"),
    {"id": "dv03", "fillers": {"f1": {"verdict": "SAME_LAW_NEW_STATE"}}, "traps": ["T3"],
     "notes": "FIX: ANOTHER (rev_t). Note: o1 and o2 share a state; o1 is old (epoch 0), o2 new."})

# d04 (T4): energy seen by a moving observer; w flips in the mirror with the momentum -> SAME.
add(world("dv04", [q("uu", "m03", ENERGY), vec("pm", "m15", {"M": 1, "L": 1, "T": -1}), q("ms", "m02", {"M": 1}, "1")],
          "uu = (pmx^2 + pmy^2 + pmz^2)/(2*ms)",
          [obs("o1", "uu", {"pmx": 1, "pmy": 0, "pmz": 0}, "1/2", 0),
           obs("o2", "uu", {"pmx": 1, "pmy": 0, "pmz": 0}, "5/2", 1),
           obs("o3", "uu", {"pmx": 0, "pmy": 1, "pmz": 0}, "1/2", 1),
           obs("o4", "uu", {"pmx": 0, "pmy": 0, "pmz": 1}, "1/2", 1)],
          [filler("f1", "uu = (pmx^2 + pmy^2 + pmz^2)/(2*ms) + pmx*wox + pmy*woy + pmz*woz",
                  [new("wo", "vec3", "m22", card("m22"), old=["0", "0", "0"], comps=["wox", "woy", "woz"])])]),
    {"id": "dv04", "fillers": {"f1": {"verdict": "SAME_LAW_NEW_STATE"}}, "traps": ["T4"],
     "notes": "FIX: ANOTHER (rev_t, refl_x). wo inferred L T^-1."})

# d05 (T5): gained symmetry: u = h vx breaks rev_t and refl_x; u = px vx keeps both -> ANOTHER.
add(world("dv05", [q("uu", "m03", ENERGY), vec("vl", "m13", {"L": 1, "T": -1}),
                  q("hh", "m07", {"M": 1, "L": 1, "T": -1}, "2")], "uu = hh*vlx",
          [obs("o1", "uu", {"vlx": 1}, 2, 0), obs("o2", "uu", {"vlx": 3}, 6, 0),
           obs("o3", "uu", {"vlx": 1}, 5, 1)],
          [filler("f1", "uu = pnx*vlx",
                  [new("pn", "vec3", "m15", card("m15"), value="var", old=["2", "0", "0"],
                       comps=["pnx", "pny", "pnz"])])]),
    {"id": "dv05", "fillers": {"f1": {"verdict": "ANOTHER_LAW", "F2": {"rev_t": "changed", "refl_x": "changed",
                                                                       "rot_z": "no_change", "conj_c": "no_change"}}},
     "traps": ["T5"], "notes": "zero report: zero_for_any_value at both old observations."})

# d06 (T6): identical bodies; a term odd under their exchange -> ANOTHER via exch only.
add(world("dv06", [q("uu", "m03", ENERGY), q("kk", "m07", {"M": 1, "L": 3, "T": -2, "Q": -2}, "2"),
                  q("qa", "m04", {"Q": 1}, owner="ba"), q("qb", "m04", {"Q": 1}, owner="bb"), q("dd", "m11", {"L": 1})],
          COUL,
          [obs("o1", "uu", {"qa": 1, "qb": 3, "dd": 2}, 3, 0),
           obs("o2", "uu", {"qa": 2, "qb": 1, "dd": 1}, 7, 1)],
          [filler("f1", "uu = kk*qa*qb/dd + cc*(qa^2 - qb^2)",
                  [new("cc", "scalar", "m07", card("m07"))])],
          bodies=[("ba", "ty01"), ("bb", "ty01")]),
    {"id": "dv06", "fillers": {"f1": {"verdict": "ANOTHER_LAW", "F2": {"exch(ba,bb)": "changed"}}}, "traps": ["T6"],
     "notes": "only the exchange changes; cc inferred."})

# d07 (T7, a '?' card): the field m10 has an unknown action under time reversal -> CONDITIONAL.
add(world("dv07", [q("uu", "m03", ENERGY), q("sf", "m10", {"L": 1}), q("kk", "m07", {"M": 1, "L": 1, "T": -2}, "3"),
                  q("tt", "m01", {"T": 1})], "uu = sf*kk",
          [obs("o1", "uu", {"sf": 1, "tt": 0}, 3, 0),
           obs("o2", "uu", {"sf": 1, "tt": 1}, 5, 1)],
          [filler("f1", "uu = sf*kk + cc*sf*tt", [new("cc", "scalar", "m07", card("m07"))])]),
    {"id": "dv07", "fillers": {"f1": {"verdict": "CONDITIONAL", "F2": {"rev_t": "conditional"}}}, "traps": ["T7"],
     "notes": "keeping: sf:rev_t = -1; instrument '?' (m10 has no instrument)."})

# d08 (T7, a new quantity of meaning '?'): its charge-conjugation action is unknown -> CONDITIONAL.
add(world("dv08", COUL_Q, COUL,
          [obs("o1", "uu", {"qa": 1, "qb": 3, "dd": 2}, 3, 0),
           obs("o2", "uu", {"qa": 2, "qb": 1, "dd": 1}, 6, 1)],
          [filler("f1", "uu = kk*qa*qb/dd + zz*qa",
                  [new("zz", "scalar", "?", {"rev_t": "1", "refl_x": "1", "conj_c": "?"}, route="i05")])]),
    {"id": "dv08", "fillers": {"f1": {"verdict": "CONDITIONAL", "F2": {"conj_c": "conditional"}}}, "traps": ["T7"],
     "notes": "keeping zz:conj_c = -1; instrument i05 (route)."})

# d09 (T8): complex field under time reversal (conjugation, a matrix) -> ANOTHER via rev_t.
add(world("dv09", [q("uu", "m03", ENERGY), q("ph", "m23", {"L": 1}, comps=["pha", "phb"]),
                  q("kk", "m07", {"M": 1, "T": -2}, "1")], "uu = kk*(pha^2 + phb^2)",
          [obs("o1", "uu", {"pha": 1, "phb": 1}, 2, 0), obs("o2", "uu", {"pha": 1, "phb": 2}, 8, 1)],
          [filler("f1", "uu = kk*(pha^2 + phb^2) + cc*phb", [new("cc", "scalar", "m07", card("m07"))])]),
    {"id": "dv09", "fillers": {"f1": {"verdict": "ANOTHER_LAW", "F2": {"rev_t": "changed", "conj_c": "changed"}}},
     "traps": ["T8"], "notes": ""})

# d10 (T8): torque z component; an axial vector under the mirror -> ANOTHER via refl_x only.
add(world("dv10", [vec("nt", "m20", {"M": 1, "L": 2, "T": -2}), vec("xp", "m12", {"L": 1}),
                  vec("fo", "m16", {"M": 1, "L": 1, "T": -2})], "ntz = xpx*foy - xpy*fox",
          [obs("o1", "ntz", {"xpx": 1, "xpy": 0, "fox": 0, "foy": 2, "foz": 0}, 2, 0),
           obs("o2", "ntz", {"xpx": 1, "xpy": 0, "fox": 0, "foy": 2, "foz": 1}, 5, 1)],
          [filler("f1", "ntz = xpx*foy - xpy*fox + cc*foz", [new("cc", "scalar", "m07", card("m07"))])]),
    {"id": "dv10", "fillers": {"f1": {"verdict": "ANOTHER_LAW", "F2": {"refl_x": "changed", "rot_z": "no_change"}}},
     "traps": ["T8"], "notes": "cc inferred L."})

# d11 (kind-reading decides): a scalar law gains an x component of the electric field -> ANOTHER incl. rot_z;
#      and a second filler with a new quantity of unknown kind -> CONDITIONAL via rot_z.
add(world("dv11", COUL_Q + [vec("ef", "m17", {"M": 1, "L": 1, "T": -2, "Q": -1})], COUL,
          [obs("o1", "uu", {"qa": 1, "qb": 3, "dd": 2, "efx": 0}, 3, 0),
           obs("o2", "uu", {"qa": 1, "qb": 1, "dd": 1, "efx": 1}, 5, 1)],
          [filler("f1", "uu = kk*qa*qb/dd + cc*efx", [new("cc", "scalar", "m07", card("m07"))])]),
    {"id": "dv11", "fillers": {"f1": {"verdict": "ANOTHER_LAW", "F2": {"rot_z": "changed", "refl_x": "changed",
                                                                       "conj_c": "changed"}}},
     "traps": [], "notes": "zero report: zero_for_any_value (efx = 0 at the old observation)."})
add(world("dv12", COUL_Q, COUL,
          [obs("o1", "uu", {"qa": 1, "qb": 3, "dd": 2}, 3, 0),
           obs("o2", "uu", {"qa": 1, "qb": 1, "dd": 1}, 5, 1)],
          [filler("f1", "uu = kk*qa*qb/dd + zk", [new("zk", "?", "?", ONES, dims=ENERGY)])]),
    {"id": "dv12", "fillers": {"f1": {"verdict": "CONDITIONAL", "F2": {"rot_z": "conditional"}}}, "traps": ["T7"],
     "notes": "unknown kind: rot_z sign unknown; keeping zk:rot_z = +1; instrument '?'."})

# d13 (INVALID): a charge added to an energy.
add(world("dv13", COUL_Q, COUL,
          [obs("o1", "uu", {"qa": 1, "qb": 3, "dd": 2}, 3, 0),
           obs("o2", "uu", {"qa": 1, "qb": 1, "dd": 1}, 5, 1)],
          [filler("f1", "uu = kk*qa*qb/dd + qn", [new("qn", "scalar", "m04", card("m04"))])]),
    {"id": "dv13", "fillers": {"f1": {"verdict": "INVALID"}}, "traps": [], "notes": "m04 has dims Q."})

# d14 (F3 alone): a constant present all along that the old observations forbid -> ANOTHER via F3 only.
add(world("dv14", COUL_Q, COUL,
          [obs("o1", "uu", {"qa": 1, "qb": 3, "dd": 2}, 3, 0),
           obs("o2", "uu", {"qa": 2, "qb": 1, "dd": 1}, 8, 1)],
          [filler("f1", "uu = kk*qa*qb/dd + cc*qa*qb", [new("cc", "scalar", "m07", card("m07"), old="same")])]),
    {"id": "dv14", "fillers": {"f1": {"verdict": "ANOTHER_LAW", "F2": {}}}, "traps": [],
     "notes": "old obs needs |3cc| <= 1/100, new needs 2cc = 4: infeasible. Reason F3 only."})

# d15 (T9): three fillers; two keep the identity, one adds a conj_c-odd term.
add(world("dv15", [q("uu", "m03", ENERGY), q("kk", "m07", {"M": 1, "L": 3, "T": -2, "Q": -2}, "1"),
                  q("qa", "m04", {"Q": 1}), q("qb", "m04", {"Q": 1}), q("dd", "m11", {"L": 1})], COUL,
          [obs("o1", "uu", {"qa": 1, "qb": 1, "dd": 1}, 1, 0),
           obs("o2", "uu", {"qa": 2, "qb": 1, "dd": 1}, 4, 1)],
          [filler("f1", "uu = kk*qa*qb/dd + c1*qa*qb", [new("c1", "scalar", "m07", card("m07"))]),
           filler("f2", "uu = kk*qa*qb/dd + c2*qb^2", [new("c2", "scalar", "m07", card("m07"))]),
           filler("f3", "uu = kk*qa*qb/dd + c3*qa", [new("c3", "scalar", "m07", card("m07"))])]),
    {"id": "dv15", "fillers": {"f1": {"verdict": "SAME_LAW_NEW_STATE"}, "f2": {"verdict": "SAME_LAW_NEW_STATE"},
                              "f3": {"verdict": "ANOTHER_LAW"}}, "kept": ["f1", "f2"],
     "decisive": [{"pair": ["f1", "f2"], "state": {"qa": "10", "qb": "1", "dd": "1"}, "observer": "ob1"}],
     "traps": ["T9"], "notes": "f3: conj_c changed."})

# d16 (zero report): a term zero at one old observation and tiny at another; meaning '?' with a known action.
add(world("dv16", MECH, "acx = -ks*xpx/ms",
          [obs("o1", "acx", {"xpx": 1, "vlx": 0}, -2, 0),
           obs("o2", "acx", {"xpx": 1, "vlx": "1/1000"}, -2, 0),
           obs("o3", "acx", {"xpx": 1, "vlx": 1}, "-5/2", 1)],
          [filler("f1", "acx = -ks*xpx/ms - cv*vlx/ms",
                  [new("cv", "scalar", "?", {"rev_t": "-1", "refl_x": "1", "conj_c": "1"}, old="same")])],
          inst="i02"),
    {"id": "dv16", "fillers": {"f1": {"verdict": "SAME_LAW_NEW_STATE"}}, "traps": [],
     "notes": "zero report: zero_for_any_value, below_precision."})

# ---- E2 worlds of blind test 1, rewritten against this registry (published worlds; protocol section 12).
# Not expressible: E2-02, E2-04, E2-08 (square roots); E2-03 (a Galilean boost, affine); E2-09 (F5, scope);
# E2-12 and E2-16 (a new quantity in a denominator, V5; their scaling symmetries are not in the catalog).
# E2-10 and E2-15 are the dev worlds dv02 and dv06 above.
GRAV = {"M": -1, "L": 3, "T": -2}

# E2-01: moment of inertia of a rotor plus a point mass, absent at the old observations -> SAME.
add(world("ev01", [q("jj", "m07", {"M": 1, "L": 2}), q("ms", "m02", {"M": 1}), q("rr", "m11", {"L": 1}),
                   q("r2", "m11", {"L": 1})], "jj = ms*rr^2",
          [obs("o1", "jj", {"ms": 2, "rr": 1, "r2": 1}, 2, 0), obs("o2", "jj", {"ms": 1, "rr": 3, "r2": 2}, 9, 0),
           obs("o3", "jj", {"ms": 1, "rr": 1, "r2": 1}, 3, 1)],
          [filler("f1", "jj = ms*rr^2 + mp*r2^2", [new("mp", "scalar", "m02", card("m02"), route="i03")])]),
    {"id": "ev01", "fillers": {"f1": {"verdict": "SAME_LAW_NEW_STATE"}}, "traps": [], "notes": "E2-01"})

# E2-05, written as kinetic energy: a passenger of mass mp moving with the car -> SAME.
add(world("ev05", [q("uu", "m03", ENERGY), q("ms", "m02", {"M": 1}), vec("vl", "m13", {"L": 1, "T": -1})],
          "uu = ms*(vlx^2 + vly^2 + vlz^2)/2",
          [obs("o1", "uu", {"ms": 1, "vlx": 2, "vly": 0, "vlz": 0}, 2, 0),
           obs("o2", "uu", {"ms": 1, "vlx": 2, "vly": 0, "vlz": 0}, 4, 1)],
          [filler("f1", "uu = (ms + mp)*(vlx^2 + vly^2 + vlz^2)/2",
                  [new("mp", "scalar", "m02", card("m02"), route="i03")])]),
    {"id": "ev05", "fillers": {"f1": {"verdict": "SAME_LAW_NEW_STATE"}}, "traps": [], "notes": "E2-05"})

# E2-07, written as F = (m + m2) a so that the new mass is not in a denominator -> SAME.
add(world("ev07", [vec("fo", "m16", {"M": 1, "L": 1, "T": -2}), q("ms", "m02", {"M": 1}),
                   vec("ac", "m14", {"L": 1, "T": -2})], "fox = ms*acx",
          [obs("o1", "fox", {"ms": 1, "acx": 2}, 2, 0), obs("o2", "fox", {"ms": 2, "acx": "3/2"}, 3, 0),
           obs("o3", "fox", {"ms": 1, "acx": 1}, 3, 1)],
          [filler("f1", "fox = (ms + mq)*acx", [new("mq", "scalar", "m02", card("m02"), route="i03")])],
          inst="i06"),
    {"id": "ev07", "fillers": {"f1": {"verdict": "SAME_LAW_NEW_STATE"}}, "traps": [], "notes": "E2-07"})

# E2-11, written as the energy of a test mass: a second source (a moon) -> SAME.
add(world("ev11", [q("uu", "m03", ENERGY), q("gg", "m07", GRAV, "1"), q("ma", "m02", {"M": 1}),
                   q("mt", "m02", {"M": 1}), q("rr", "m11", {"L": 1}), q("rb", "m11", {"L": 1})],
          "uu = -gg*ma*mt/rr",
          [obs("o1", "uu", {"ma": 2, "mt": 1, "rr": 1, "rb": 1}, -2, 0),
           obs("o2", "uu", {"ma": 1, "mt": 2, "rr": 2, "rb": 3}, -1, 0),
           obs("o3", "uu", {"ma": 2, "mt": 1, "rr": 1, "rb": 2}, "-5/2", 1)],
          [filler("f1", "uu = -gg*ma*mt/rr - gg*mb*mt/rb", [new("mb", "scalar", "m02", card("m02"))])]),
    {"id": "ev11", "fillers": {"f1": {"verdict": "SAME_LAW_NEW_STATE"}}, "traps": [], "notes": "E2-11"})

# E2-13: a rolling ball instead of a sliding block: the factor 5/7 contradicts the old data -> ANOTHER (F3).
add(world("ev13", [vec("ac", "m14", {"L": 1, "T": -2}), vec("gf", "m21", {"L": 1, "T": -2}), q("sn", "m07", {})],
          "acx = gfx*sn",
          [obs("o1", "acx", {"gfx": 2, "sn": "1/2"}, 1, 0), obs("o2", "acx", {"gfx": 3, "sn": "1/3"}, 1, 0),
           obs("o3", "acx", {"gfx": 7, "sn": 1}, 5, 1)],
          [filler("f1", "acx = 5*gfx*sn/7", [])], inst="i02"),
    {"id": "ev13", "fillers": {"f1": {"verdict": "ANOTHER_LAW", "F2": {}}}, "traps": [], "notes": "E2-13"})

# E2-14: a viscous term with the wrong dimensions (a length missing) -> INVALID.
add(world("ev14", [vec("fd", "m16", {"M": 1, "L": 1, "T": -2}), vec("vl", "m13", {"L": 1, "T": -1}),
                   q("cd", "m06", {"M": 1, "T": -1}, "1")], "fdx = -cd*vlx",
          [obs("o1", "fdx", {"vlx": 1}, -1, 0), obs("o2", "fdx", {"vlx": 1}, -2, 1)],
          [filler("f1", "fdx = -cd*vlx - 3*mu*vlx",
                  [new("mu", "scalar", "m07", card("m07"), dims={"M": 1, "L": -1, "T": -1})])], inst="i06"),
    {"id": "ev14", "fillers": {"f1": {"verdict": "INVALID"}}, "traps": [], "notes": "E2-14"})

# ---- coverage-check cases of the language (language_v0/coverage/CASES_run2.md), rewritten against this
# registry. C8 (the complex field) is dv09; C11 has no law.
# C1: y = a x gains b x^2, written on the x component of a force. Rejected by V13, so it is kept apart as a
# case the validator must reject: under the half turn (rot_z applied twice, a product the catalog does not list)
# the law is unchanged and b x^2 is not, so the true answer is ANOTHER_LAW, not the catalog's CONDITIONAL.
REJECT = [("cv01", "V13", world("cv01", [vec("fo", "m16", {"M": 1, "L": 1, "T": -2}), vec("xp", "m12", {"L": 1}),
                                         q("aa", "m07", {"M": 1, "T": -2}, "2")], "fox = aa*xpx",
                                [obs("o1", "fox", {"xpx": 1}, 2, 0), obs("o2", "fox", {"xpx": 1}, 3, 1)],
                                [filler("f1", "fox = aa*xpx + bb*xpx^2",
                                        [new("bb", "scalar", "?", {"rev_t": "1", "refl_x": "?", "conj_c": "1"})])],
                                inst="i06"))]

# C2: the missing energy is carried by a new body (Pauli's neutrino); a variable, absent before -> SAME.
add(world("cv02", [q("et", "m03", ENERGY), q("e1", "m03", ENERGY, owner="ba"), q("e2", "m03", ENERGY, owner="bb")],
          "et = e1 + e2",
          [obs("o1", "et", {"e1": 1, "e2": 2}, 3, 0), obs("o2", "et", {"e1": 1, "e2": 2}, "7/2", 1),
           obs("o3", "et", {"e1": 2, "e2": 1}, 4, 1)],
          [filler("f1", "et = e1 + e2 + e3",
                  [new("e3", "scalar", "m03", card("m03"), value="var", owner="nu", route="i04")],
                  new_bodies=[("nu", "ty05")])],
          bodies=[("ba", "ty01"), ("bb", "ty01")]),
    {"id": "cv02", "fillers": {"f1": {"verdict": "SAME_LAW_NEW_STATE"}}, "traps": [],
     "notes": "C2; e3 differs between the two new observations (a variable)."})

# C3: a momentum added to an energy -> INVALID.
add(world("cv03", [q("ee", "m03", ENERGY), q("ms", "m02", {"M": 1}), q("cc", "m07", {"L": 1, "T": -1}, "1")],
          "ee = ms*cc^2",
          [obs("o1", "ee", {"ms": 1}, 1, 0), obs("o2", "ee", {"ms": 1}, 2, 1)],
          [filler("f1", "ee = ms*cc^2 + pp", [new("pp", "scalar", "?", ONES, dims={"M": 1, "L": 1, "T": -1})])]),
    {"id": "cv03", "fillers": {"f1": {"verdict": "INVALID"}}, "traps": [], "notes": "C3"})

PREFIX = {"dv": "D-", "ev": "E-", "cv": "C-"}

if __name__ == "__main__":
    out = os.path.join(HERE, "worlds")
    os.makedirs(out, exist_ok=True)
    bad = 0
    for w in WORLDS:
        ctx, canon = R.check_world(w, INFO, w["id"])
        if ctx.errors:
            bad += 1
            print("\n".join(ctx.errors))
        fn = PREFIX[w["id"][:2]] + w["id"][2:] + ".json"
        with open(os.path.join(out, fn), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(w, fh, indent=1)
            fh.write("\n")
    for k in KEY:
        k["id"] = PREFIX[k["id"][:2]] + k["id"][2:]
    with open(os.path.join(HERE, "key.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(KEY, fh, indent=1)
        fh.write("\n")
    rej = os.path.join(HERE, "rejected")
    os.makedirs(rej, exist_ok=True)
    for wid, rule, w in REJECT:
        with open(os.path.join(rej, f"{wid}_{rule}.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(w, fh, indent=1)
            fh.write("\n")
    print(f"{len(WORLDS)} dev worlds written, {bad} rejected by the reader; {len(REJECT)} cases that must be rejected")
