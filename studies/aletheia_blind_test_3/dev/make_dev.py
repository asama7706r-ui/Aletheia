"""Write the dev worlds, dev items and the dev key of blind test 3 (development only; excluded from the test).

Each world was designed by hand; its intended answer is in EXPECT (the dev key) and the reasoning is in
the comment above it. Usage:  python make_dev.py   (writes dev/worlds, dev/data, dev/key.json)
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
W, D, KEY_A, KEY_B = {}, {}, [], []


def world(wid, **kw):
    w = {"id": wid, "experiment": "A"}
    w.update(kw)
    w.setdefault("constants", {})
    w.setdefault("visible", None)
    w.setdefault("symmetries", [])
    W[wid] = w


def cand(rid, obj, term, coverage=None, exact=None):
    return {"id": rid, "object": obj, "term": term,
            "coefficient": "unknown" if exact is None else {"exact": exact}, "coverage": coverage}


def dimmer(ratio, expr, summary=None):
    c = {"ratio": ratio, "factor": {"type": "dimmer", "expr": expr}}
    if summary:
        c["summary"] = summary
    return c


def switch(ratio, on, t, summary=None):
    c = {"ratio": ratio, "factor": {"type": "switch", "on": on, "threshold": t}}
    if summary:
        c["summary"] = summary
    return c


def ob(state, value, observer):
    return {"state": state, "value": value, "observer": observer}


def po(state, observer):
    return {"state": state, "observer": observer}


# --- nebulium toy, dimmer: R1 covered by density at the lab, back in the thin gas -> KNOWN(R1); R2 BOUND.
neb_shared = dict(
    observable="yl", quantities={"yl": {"M": 1, "T": -3}, "na": {"L": -3}, "nb": {}},
    constants={"kc": {"value": "100", "dims": {"L": -3}}, "ku": {"value": "1", "dims": {"M": 1, "T": -3}}},
    observers={"lab1": "1/100", "far1": "1/10"}, base_law="yl = ku*nb/10",
    ledger=[cand("R1", "ob1", "ku*nb", dimmer("na/kc", "1/(1+r)", "fades when na exceeds kc")),
            cand("R2", "ob2", "ku*nb**2")],
    old_observations=[ob({"na": "1000000", "nb": "1"}, "1/10", "lab1"),
                      ob({"na": "1000000", "nb": "3"}, "3/10", "lab1")],
    possible_observations=[po({"na": "1000000", "nb": "2"}, "lab1"), po({"na": "1", "nb": "2"}, "far1")])
world("dA-nebdim", new_observations=[ob({"na": "1", "nb": "1"}, "51/10", "far1")], **neb_shared)
KEY_A.append({"id": "dA-nebdim", "verdict": "KNOWN", "relation": "R1", "reasons": {"R2": ["BOUND"]}})
# --- step-0 toy sharing the observable: residual 1/20 within 1/10 -> NO_DEFICIT; R1 is a planet-X trap.
world("dA-step0", new_observations=[ob({"na": "1", "nb": "1"}, "3/20", "far1")], **neb_shared)
KEY_A.append({"id": "dA-step0", "verdict": "NO_DEFICIT"})

# --- nebulium toy, switch: R2 off at the lab (ratio 100), on in the thin gas -> KNOWN(R2).
# R1 needs kelvin^-1 (TYPE) and is also too weak (BOUND); R3 BOUND.
world("dA-nebsw", observable="ym",
      quantities={"ym": {"M": 1, "L": -1}, "nc": {"L": -3}, "nd": {}, "te": {"K": 1}},
      constants={"kd": {"value": "50", "dims": {"L": -3}}, "kw": {"value": "2", "dims": {"M": 1, "L": -1}}},
      observers={"lab2": "1/50", "far2": "1/5"}, base_law="ym = kw*nd",
      ledger=[cand("R1", "ob1", "kw*nd*te"), cand("R2", "ob2", "kw*nd", switch("nc/kd", "<", "1")),
              cand("R3", "ob2", "kw*nd**3")],
      old_observations=[ob({"nc": "5000", "nd": "1", "te": "1"}, "2", "lab2"),
                        ob({"nc": "5000", "nd": "2", "te": "1"}, "4", "lab2")],
      new_observations=[ob({"nc": "10", "nd": "1", "te": "1"}, "5", "far2")],
      possible_observations=[po({"nc": "5000", "nd": "2", "te": "1"}, "lab2"),
                             po({"nc": "10", "nd": "2", "te": "1"}, "far2")])
KEY_A.append({"id": "dA-nebsw", "verdict": "KNOWN", "relation": "R2", "reasons": {"R1": ["TYPE", "BOUND"], "R3": ["BOUND"]}})

# --- helium toy: both candidates bounded by the old readings -> NEW (BOUND, BOUND). lab13 appears only
# in a possible observation (used by the root_none item).
world("dA-helium", observable="ya", quantities={"ya": {}, "xa": {}},
      observers={"lab3": "1/100", "far3": "1/10", "lab13": "1/100"}, base_law="ya = xa",
      ledger=[cand("R1", "ob1", "xa**2"), cand("R2", "ob2", "xa**3"),
              cand("R3", "ob2", "xa**2", switch("xa", ">", "20"))],
      old_observations=[ob({"xa": "1"}, "1", "lab3"), ob({"xa": "2"}, "2", "lab3")],
      new_observations=[ob({"xa": "3"}, "5", "far3")],
      possible_observations=[po({"xa": "4"}, "lab13"), po({"xa": "10"}, "far3")])
KEY_A.append({"id": "dA-helium", "verdict": "NEW", "reasons": {"R1": ["BOUND"], "R2": ["BOUND"], "R3": ["SCOPE"]}})

# --- coronium toy: coverage by a temperature ratio (dimmer r/(1+r)) -> KNOWN(R1); R2 BOUND.
world("dA-coronium", observable="yk", quantities={"yk": {"M": 1}, "tq": {"K": 1}, "ne": {}},
      constants={"kt": {"value": "1000", "dims": {"K": 1}}, "km": {"value": "3", "dims": {"M": 1}}},
      observers={"lab4": "1/100", "far4": "1/10"}, base_law="yk = km*ne",
      ledger=[cand("R1", "ob1", "km*ne", dimmer("tq/kt", "r/(1+r)")), cand("R2", "ob2", "km*ne**2")],
      old_observations=[ob({"tq": "1", "ne": "1"}, "3", "lab4"), ob({"tq": "1", "ne": "2"}, "6", "lab4")],
      new_observations=[ob({"tq": "100000", "ne": "1"}, "603/101", "far4")],
      possible_observations=[po({"tq": "1", "ne": "3"}, "lab4"), po({"tq": "100000", "ne": "3"}, "far4"),
                             po({"tq": "1000", "ne": "3"}, "far4")])
KEY_A.append({"id": "dA-coronium", "verdict": "KNOWN", "relation": "R1", "reasons": {"R2": ["BOUND"]}})

# --- fork toy: same term, two coverages (dimmer at ka, switch at kb) both back in the thin gas; they
# differ at nf = 50 (dimmer 2/3, switch off) -> FORK(R1, R2); R3 BOUND.
world("dA-fork", observable="yf", quantities={"yf": {"L": 2}, "nf": {"L": -3}, "mf": {}},
      constants={"ka": {"value": "100", "dims": {"L": -3}}, "kb": {"value": "10", "dims": {"L": -3}},
                 "kl": {"value": "1", "dims": {"L": 2}}},
      observers={"lab5": "1/100", "far5": "1/10"}, base_law="yf = kl*mf",
      ledger=[cand("R1", "ob1", "kl*mf", dimmer("nf/ka", "1/(1+r)")),
              cand("R2", "ob2", "kl*mf", switch("nf/kb", "<", "1")), cand("R3", "ob3", "kl*mf**2")],
      old_observations=[ob({"nf": "100000", "mf": "1"}, "1", "lab5"), ob({"nf": "100000", "mf": "2"}, "2", "lab5")],
      new_observations=[ob({"nf": "1", "mf": "1"}, "5", "far5")],
      possible_observations=[po({"nf": "50", "mf": "1"}, "far5"), po({"nf": "1", "mf": "2"}, "far5")])
KEY_A.append({"id": "dA-fork", "verdict": "FORK", "branches": ["R1", "R2"], "reasons": {"R3": ["BOUND"]}})

# --- visible-relation toy: mu in [1, 3] from the old readings, R1 bounded to [-3/5, 3/5]; the deficit needs
# mu + lam = 7/2 +- 1/10, possible only near mu = 3 -> KNOWN(R1); with mu fixed at 2 it would be NEW.
world("dA-visible", observable="yb", quantities={"yb": {"M": 1, "L": 2, "T": -2}, "xb": {}, "xc": {}},
      constants={"ke": {"value": "1", "dims": {"M": 1, "L": 2, "T": -2}}},
      observers={"lab6": "1", "lab7": "3/5", "far6": "1/10"}, base_law="yb = ke/2",
      visible={"id": "V1", "object": "ob0", "term": "ke*xb"},
      ledger=[cand("R1", "ob1", "ke*xc"), cand("R2", "ob2", "ke*xb**2")],
      old_observations=[ob({"xb": "1", "xc": "0"}, "5/2", "lab6"), ob({"xb": "0", "xc": "1"}, "1/2", "lab7")],
      new_observations=[ob({"xb": "1", "xc": "1"}, "4", "far6")],
      possible_observations=[po({"xb": "2", "xc": "0"}, "lab6"), po({"xb": "0", "xc": "2"}, "far6")])
KEY_A.append({"id": "dA-visible", "verdict": "KNOWN", "relation": "R1", "reasons": {"R2": ["BOUND"]}})

# --- TYPE-sole and SHAPE-sole toy: R1 (xd**2) fits the numbers but needs L T^-2 (TYPE only); R2 has the
# right dimensions but its shape needs two strengths (SHAPE only) -> NEW.
world("dA-typesole", observable="yc", quantities={"yc": {"L": 1}, "xd": {"T": 1}},
      constants={"kv": {"value": "2", "dims": {"L": 1, "T": -1}}},
      observers={"lab8": "1", "far8": "1/20"}, base_law="yc = kv*xd",
      ledger=[cand("R1", "ob1", "xd**2"), cand("R2", "ob2", "kv*xd")],
      old_observations=[ob({"xd": "1"}, "2", "lab8")],
      new_observations=[ob({"xd": "2"}, "6", "far8"), ob({"xd": "4"}, "16", "far8")],
      possible_observations=[po({"xd": "3"}, "lab8"), po({"xd": "5"}, "far8")])
KEY_A.append({"id": "dA-typesole", "verdict": "NEW", "reasons": {"R1": ["TYPE"], "R2": ["SHAPE"]}})

# --- SYMMETRY-sole toy: the mirror xf -> -xf forbids the odd R1 although it fits; R2 BOUND -> NEW.
world("dA-symsole", observable="yd", quantities={"yd": {"M": 1}, "xf": {}, "xg": {}},
      constants={"kn": {"value": "1", "dims": {"M": 1}}},
      observers={"lab9": "1/100", "far9": "1/100"}, base_law="yd = kn*xf**2",
      symmetries=[{"name": "mirror", "map": {"xf": "-xf"}}],
      ledger=[cand("R1", "ob1", "kn*xf"), cand("R2", "ob2", "kn*xg")],
      old_observations=[ob({"xf": "1/10", "xg": "0"}, "1/100", "lab9"), ob({"xf": "0", "xg": "1"}, "0", "lab9")],
      new_observations=[ob({"xf": "2", "xg": "1"}, "83/20", "far9")],
      possible_observations=[po({"xf": "3", "xg": "0"}, "lab9"), po({"xf": "1", "xg": "2"}, "far9")])
KEY_A.append({"id": "dA-symsole", "verdict": "NEW", "reasons": {"R1": ["SYMMETRY"], "R2": ["BOUND"]}})

# --- SCOPE-sole toy: R1's switch is on at the lab and off in the dense new state; uncovered it would fit
# (SCOPE only). R2 = kg*(mh+1) is bounded at a dense old state where R1's term is zero (BOUND), so no
# combination fits -> NEW. NO_SCOPE would answer KNOWN(R1).
world("dA-scopesole", observable="yh", quantities={"yh": {"L": -1}, "nh": {"L": -3}, "mh": {}},
      constants={"kh": {"value": "20", "dims": {"L": -3}}, "kg": {"value": "1", "dims": {"L": -1}}},
      observers={"lab10": "1", "lab12": "1/10", "far10": "1/10"}, base_law="yh = kg*mh",
      ledger=[cand("R1", "ob1", "kg*mh", switch("nh/kh", "<", "1")), cand("R2", "ob2", "kg*(mh+1)")],
      old_observations=[ob({"nh": "1", "mh": "1"}, "1", "lab10"), ob({"nh": "1", "mh": "2"}, "2", "lab10"),
                        ob({"nh": "1000", "mh": "0"}, "0", "lab12")],
      new_observations=[ob({"nh": "1000", "mh": "1"}, "7/5", "far10")],
      possible_observations=[po({"nh": "1", "mh": "3"}, "lab10"), po({"nh": "1000", "mh": "3"}, "far10")])
KEY_A.append({"id": "dA-scopesole", "verdict": "NEW", "reasons": {"R1": ["SCOPE"], "R2": ["BOUND"]}})

# --- planet-X toy: the deficit at xp = 5 is 2; the old readings at xp = 0 bound both candidates and any
# combination -> NEW. Correcting kq from 1 to 7/5 makes the deficit vanish (root_vanish); kq plays no role
# at xp = 0.
world("dA-planetx", observable="yp", quantities={"yp": {"L": 1}, "xp": {}, "zp": {}},
      constants={"kp": {"value": "1", "dims": {"L": 1}}, "kq": {"value": "1", "dims": {"L": 1}}},
      observers={"lab11": "1/100", "far11": "1/10"}, base_law="yp = kp + kq*xp",
      ledger=[cand("R1", "ob1", "kp*zp"), cand("R2", "ob2", "kp*zp**2")],
      old_observations=[ob({"xp": "0", "zp": "1"}, "1", "lab11"), ob({"xp": "0", "zp": "2"}, "1", "lab11")],
      new_observations=[ob({"xp": "5", "zp": "1"}, "8", "far11")],
      possible_observations=[po({"xp": "2", "zp": "1"}, "lab11"), po({"xp": "5", "zp": "2"}, "far11")])
KEY_A.append({"id": "dA-planetx", "verdict": "NEW", "reasons": {"R1": ["BOUND"], "R2": ["BOUND"]}})


# ================================================================= Part B dev items
def item(did, cat, reopened, final, **kw):
    it = {"id": did, "experiment": "B"}
    it.update(kw)
    D[did] = it
    KEY_B.append({"id": did, "type": cat, "reopened": reopened, "final": final})


item("dB-bowen", "rel_new_known", ["dA-helium"], {"dA-helium": {"verdict": "KNOWN", "relation": "R4"}},
     type="relation", observable="ya", relation=cand("R4", "ob1", "xa*(xa-1)*(xa-2)"))
item("dB-fall", "obs_flip", ["dA-nebdim"], {"dA-nebdim": {"verdict": "NEW"}},
     type="observation", world="dA-nebdim", state={"na": "1000000", "nb": "2"}, observer="lab1", value="1")
item("dB-inside", "obs_inside", [], {},
     type="observation", world="dA-nebdim", state={"na": "1", "nb": "2"}, observer="far1", value="51/5")
item("dB-forkdecide", "obs_fork", ["dA-fork"], {"dA-fork": {"verdict": "KNOWN", "relation": "R2"}},
     type="observation", world="dA-fork", state={"nf": "50", "mf": "1"}, observer="far5", value="1")
item("dB-planetx", "root_vanish", ["dA-planetx"], {"dA-planetx": {"verdict": "NO_DEFICIT"}},
     type="root", constant="kq", new_value="7/5")
item("dB-precision", "root_revive", ["dA-helium"], {"dA-helium": {"verdict": "FORK", "branches": ["R1", "R2"]}},
     type="root", observer="lab3", new_precision="1")
item("dB-nd", "rel_unchanged", ["dA-nebdim"], {"dA-nebdim": {"verdict": "KNOWN", "relation": "R1"}},
     type="relation", observable="yl", relation=cand("R3", "ob2", "ku*nb**3"))
item("dB-none", "rel_none", [], {},
     type="relation", observable="zz", observable_dims={"L": 1}, relation=cand("R1", "ob1", "zz"))
item("dB-rootnone", "root_none", [], {}, type="root", observer="lab13", new_precision="1/2")
item("dB-knownfork", "rel_known_fork", ["dA-coronium"],
     {"dA-coronium": {"verdict": "FORK", "branches": ["R1", "R3"]}},
     type="relation", observable="yk", relation=cand("R3", "ob1", "km*ne", switch("tq/kt", ">", "10")))


if __name__ == "__main__":
    for sub, objs in (("worlds", W), ("data", D)):
        d = os.path.join(HERE, sub)
        os.makedirs(d, exist_ok=True)
        for f in os.listdir(d):
            if f.endswith(".json"):
                os.remove(os.path.join(d, f))
        for oid, obj in objs.items():
            with open(os.path.join(d, oid + ".json"), "w", encoding="utf-8") as fh:
                json.dump(obj, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, "key.json"), "w", encoding="utf-8") as fh:
        json.dump({"A": KEY_A, "B": KEY_B}, fh, ensure_ascii=False, indent=1)
    print("wrote %d worlds, %d items" % (len(W), len(D)))
