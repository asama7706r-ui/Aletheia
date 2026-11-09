"""Deliberate corruption for test 5b (protocol_v5b.md, Section 12; the lesson of test 2): every kind of wrong
certificate, wrong output, wrong key and invalid world must be caught. Test 5's dev/mutation_test.py, run on the
5b scorer side with the 5b procedure's dev outputs (dev/check_dev/outputs_dev.json, from the run in
dev/check_dev_5b.py), plus the parts new in 5b: the reuse of certificates, V15 up to the numbers, the certificates
of variant worlds (T9, T10, T13), and the copy units (test 5 audit, correction 1).
Exit 0 only if every corruption is caught and every clean case passes.
Usage (from aletheia_blind_test_5b/): python -I dev/mutation_test_5b.py"""
import copy
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scorer"))
import certs_v5 as C  # noqa: E402
import ref_v5b as RF  # noqa: E402
import validate_v5b as V  # noqa: E402
import score_v5b as SC  # noqa: E402

B = os.path.join(HERE, "batch_dev")
KEY = {e["id"]: e for e in json.load(open(os.path.join(B, "key", "key.json"), encoding="utf-8"))}
OUT = json.load(open(os.path.join(HERE, "check_dev", "outputs_dev.json"), encoding="utf-8"))
REG = V.load_seed()
fails = 0


def world(wid):
    return C.R.load(os.path.join(B, "worlds", wid + ".json"))


def check(label, caught):
    global fails
    print(("ok    " if caught else "MISS  ") + label)
    if not caught:
        fails += 1


def rejects(fn, *args):
    return not C.safe(fn, *args)[0]


def find(verdict, pred=lambda e: True):
    for wid, e in sorted(KEY.items()):
        if e["verdict"] == verdict and pred(e):
            return wid, e
    raise SystemExit(f"no dev world with verdict {verdict}")


# ---------------------------------------------------------------- certificates
wid, e = find("BRANCHES", lambda e: any(b["witness"] and b["witness"]["dim"] == 4 for b in e["branches"]))
info = C.world_info(world(wid))
b = next(b for b in e["branches"] if b["witness"] and b["witness"]["dim"] == 4)
w = b["witness"]
check("clean witness accepted", not rejects(C.check_witness, w, info, b["drop"]))
m = copy.deepcopy(w)
m["table"][0][3] = "1" if m["table"][0][3] != "1" else "-1"
check("witness: a changed structure constant", rejects(C.check_witness, m, info, b["drop"]))
m = copy.deepcopy(w)
g = sorted(m["gens"])[0]
m["gens"][g] = ["0"] * m["dim"]
m["gens"][g][0] = "1"
check("witness: a wrong generator value", rejects(C.check_witness, m, info, b["drop"]))
m = copy.deepcopy(w)
if m.get("q12"):
    m["q12"]["N"] = [[("-1" if i == j and i == 1 else x) for j, x in enumerate(r)] for i, r in enumerate(m["q12"]["N"])]
    check("witness: a norm that is not positive definite", rejects(C.check_witness, m, info, b["drop"]))
smaller = [x for x in b["drop"] if x != "q14"]
check("witness: claims q14 in dimension > 1", rejects(C.check_witness, w, info, smaller))
check("witness: claims a smaller candidate than it has", rejects(C.check_witness, w, info, b["drop"][1:]))

ref = next((r for r in e["refutations"]), None)
check("clean refutation accepted", not rejects(C.check_refutation, ref["proof"], info, ref["drop"]))
m = copy.deepcopy(ref["proof"])


def first_close(node):
    if node["node"] in ("close", "positive"):
        return node
    return first_close(node["children"][0])


nd = first_close(m["tree"])
if nd["terms"]:
    nd["terms"][0][0] = "7" if nd["terms"][0][0] != "7" else "5"
check("refutation: a changed coefficient", rejects(C.check_refutation, m, info, ref["drop"]))
bigger = sorted(set(ref["drop"]) | {"q12", "q14"} & set(C.judged_units(info["origin"], info["frames"])))
check("refutation: used for a candidate that drops the units it needs", bigger == sorted(ref["drop"]) or
      rejects(C.check_refutation, ref["proof"], info, bigger))
m = {"theta": None, "tree": {"node": "positive", "t": [[["1", "ia"]]], "c": "-1", "terms": []}}
check("refutation: positivity with c <= 0", rejects(C.check_refutation, m, info, ["q6"]))

wk, ek = find("KNOWN_SUFFICES", lambda e: e["known"].get("theta"))
ik = C.world_info(world(wk))
check("clean known-kind solution accepted", not rejects(C.check_known, ek["known"], ik))
m = copy.deepcopy(ek["known"])
g = sorted(m["values"])[0]
m["values"][g] = ["1"] + ["0"] * (len(m["theta"]["poly"]) - 2) if isinstance(m["values"][g][0], str) else m["values"][g]
check("known: a wrong value", rejects(C.check_known, m, ik))
m = copy.deepcopy(ek["known"])
m["theta"]["lo"], m["theta"]["hi"] = "-10", "10"
check("known: theta's interval holds two roots", rejects(C.check_known, m, ik))

wi, ei = find("IMPOSSIBLE")
check("IMPOSSIBLE accepted on an impossible world", not rejects(C.check_impossible, {"kind": ei["impossible"]["kind"]}, C.world_info(world(wi))))
check("IMPOSSIBLE rejected on a possible world", rejects(C.check_impossible, {"kind": "values"}, info))

wm, em = find("NO_WITNESS", lambda e: any(b.get("mirror") for b in e["branches"]))
im = C.world_info(world(wm))
bm = next(b for b in em["branches"] if b.get("mirror"))
check("clean mirror accepted", not rejects(C.check_mirror, bm["mirror"], bm["drop"], bm["mirror"]["twin"], im))
check("mirror: a twin that is not the mirror", rejects(C.check_mirror, bm["mirror"], bm["drop"], bm["drop"], im))
check("mirror: on a world that is not mirror-invariant", rejects(C.check_mirror, {"perm": {"ia": "ia", "jb": "jb"}}, ["q5"], ["q6"], info))

# ---------------------------------------------------------------- outputs (scorer)
o = copy.deepcopy(OUT[wid]["procedure"])
truth = RF.truth(world(wid), V.key_pool(e, info))
check("clean output: decision correct", V.decision_equal(o, truth))
check("clean output: marks correct", SC.marks_correct(o, truth, info))
m = copy.deepcopy(o)
m["verdict"] = "NEW_KIND"
m["branches"] = m["branches"][:1]
check("output: one branch dropped is a silent choice", SC.silent_choice(m, truth) and not V.decision_equal(m, truth))
m = copy.deepcopy(o)
m["branches"][0]["marks"]["q5"] = "FRAME"
check("output: a wrong mark", not SC.marks_correct(m, truth, info))
m = copy.deepcopy(o)
u = m["branches"][0]["drop"][0]
m["branches"][0]["proofs"].pop(u, None)
check("output: a FORCED unit without a proof", not SC.marks_correct(m, truth, info))
m = copy.deepcopy(o)
wb = next(x for x in m["branches"] if x["witness"])
wb["witness"]["table"][0][3] = "1" if wb["witness"]["table"][0][3] != "1" else "-1"
pool, problems = SC.output_pool(m, info)
check("output: a false witness is counted", bool(problems["false_witness"]))
m = copy.deepcopy(o)
m["branches"].append({"drop": ["q14"], "status": "no_witness", "witness": None, "marks": {}, "proofs": {}, "mirror": None})
check("output: an added branch that a proof refutes", not V.decision_equal(m, truth))
m = copy.deepcopy(o)
m["branches"][0]["status"] = "no_witness" if m["branches"][0]["status"] == "witnessed" else "witnessed"
check("output: a wrong status", not V.decision_equal(m, truth))

# ---------------------------------------------------------------- worlds and keys (validator)
def vworld(doc, entry):
    path = os.path.join(HERE, "_mut_world.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)
    r = V.validate_world(path, entry, REG, set())
    os.remove(path)
    return r["errors"]


d0, e0 = world(wid), KEY[wid]
check("clean world and key: no validity error", vworld(d0, e0) == [])
m = copy.deepcopy(e0)
m["verdict"] = "NEW_KIND"
check("key: a wrong verdict (V9)", any(x.startswith("V9") for x in vworld(d0, m)))
m = copy.deepcopy(e0)
mb = next(x for x in m["branches"] if x["witness"])
mb["witness"]["table"][0][3] = "1" if mb["witness"]["table"][0][3] != "1" else "-1"
check("key: a corrupted witness (V9)", any(x.startswith("V9") for x in vworld(d0, m)))
m = copy.deepcopy(e0)
m["traps"] = ["T12"]
check("key: a declared trap that does not hold (V12)", any(x.startswith("V12") for x in vworld(d0, m)))
dm = copy.deepcopy(d0)
dm["builds"][0]["generators"] = ["a", "jb"]
dm["builds"][0]["role"] = [s.replace("ia", "a") for s in dm["builds"][0]["role"]]
check("world: a one-letter name (V2)", any(x.startswith("V2") for x in vworld(dm, e0)))
dm = copy.deepcopy(d0)
dm["builds"][0]["role"].append("ia*jb*ia*jb*ia = 1")
check("world: a product of more than P2 factors (V2)", any(x.startswith("V2") for x in vworld(dm, e0)))
dm = copy.deepcopy(d0)
dm["builds"][0]["role"].append("ia != 101")
check("world: a number above 100 (V2)", any(x.startswith("V2") for x in vworld(dm, e0)))
dm = copy.deepcopy(d0)
dm["builds"][0]["role"].append("ia^-1 = jb")
check("world: ^-1 on a new generator (V2)", any(x.startswith("V2") for x in vworld(dm, e0)))
dm = copy.deepcopy(d0)
dm["builds"].append(copy.deepcopy(dm["builds"][0]))
dm["builds"][1]["id"] = "bld2"
check("world: two builds (V2 or the reader)", vworld(dm, e0) != [])
wf, ef = find("FREEDOM")
df = world(wf)
df["builds"][0]["role"].append(f"{df['builds'][0]['generators'][0]} != 3")
check("world: a FREEDOM role that is not definitions (V3)", any(x.startswith("V3") for x in vworld(df, ef)))
wn, en = find("NO_WITNESS")
m = copy.deepcopy(en)
m["top_witness"] = None
check("key: a NO_WITNESS world without its top witness (V8)", any(x.startswith("V8") for x in vworld(world(wn), m)))
fps = set(json.load(open(V.DEV_FP, encoding="utf-8")))
r = V.validate_world(os.path.join(B, "worlds", wid + ".json"), e0, REG, fps)
check("world: a dev world is rejected (V11)", any(x.startswith("V11") for x in r["errors"]))

check("world: a world of test 5 is rejected (V11)", any(x.startswith("V11") for x in V.validate_world(
    os.path.join(HERE, "batch_t5A", "worlds", "W-01.json"), None, REG, fps)["errors"]))


# ---------------------------------------------------------------- new in 5b: the reuse of certificates (8.1)
def all_keys():
    for b_ in ("batch_dev", "batch_t5A", "batch_t5B"):
        for e_ in json.load(open(os.path.join(HERE, b_, "key", "key.json"), encoding="utf-8")):
            yield b_, e_


def reuse_example():
    """A key refutation the checker accepts for a candidate that is not a subset of its own (so test 5's
    reference, which used it only for subsets, could not use it there)."""
    import itertools
    for b_, e_ in all_keys():
        for r in e_.get("refutations") or []:
            inf = C.world_info(C.R.load(os.path.join(HERE, b_, "worlds", e_["id"] + ".json")))
            U = C.judged_units(inf["origin"], inf["frames"])
            need = RF.cited_units(r["proof"])
            for k in range(len(U) + 1):
                for d2_ in itertools.combinations(U, k):
                    if set(d2_) <= set(r["drop"]) or need & set(d2_):
                        continue
                    if C.safe(C.check_refutation, r["proof"], inf, sorted(d2_))[0]:
                        return b_, e_["id"], inf, r, sorted(d2_)
    return None


ex = reuse_example()
check("reuse: some key certificate refutes a candidate outside its own subsets", ex is not None)
if ex is not None:
    bx, wx, ix, rx, d2 = ex
    print(f"      (example: {bx} {wx}, written for {rx['drop']}, accepted for {d2})")
    with_reuse = RF.Classifier(ix, [], [rx["drop"]], search=False, certs=[(rx["drop"], rx["proof"])])
    without = RF.Classifier(ix, [], [rx["drop"]], search=False)
    check("reuse: the classifier refutes that candidate with the certificate offered", with_reuse.status(d2) == "REFUTED")
    check("reuse: test 5's rule alone does not", without.status(d2) == "UNDECIDED")
    cut = sorted(RF.cited_units(rx["proof"]))
    if cut:
        d3 = sorted(set(d2) | {cut[0]})
        fresh = RF.Classifier(ix, [], [rx["drop"]], search=False, certs=[(rx["drop"], rx["proof"])])
        check("reuse: never for a candidate that drops a unit the certificate cites",
              set(d3) <= set(rx["drop"]) or fresh.status(d3) != "REFUTED")
    bad = copy.deepcopy(rx["proof"])
    nd = first_close(bad["tree"])
    if nd["terms"]:
        nd["terms"][0][0] = "7" if nd["terms"][0][0] != "7" else "5"
    wx_world = C.R.load(os.path.join(HERE, bx, "worlds", wx + ".json"))
    t_bad, cl_bad = RF.truth_full(wx_world, {"witness": [], "refutation": [(rx["drop"], bad)], "known": []}, search=False)
    check("reuse: a corrupted certificate is never offered", cl_bad is None or not cl_bad.reused)


# ---------------------------------------------------------------- new in 5b: V15 up to the numbers
def info_of(role, gens, origin="k01", frames=()):
    w_ = copy.deepcopy(world(wid))
    w_["builds"][0].update(role=role, generators=gens, origin=origin, frames=list(frames))
    return C.world_info(w_)


fa = info_of(["pa*pa = 2", "pa*qe + qe*pa = 0", "qe != 0"], ["pa", "qe"])
fb = info_of(["xx*xx = 7", "xx*yy + yy*xx = 0", "yy != 0"], ["xx", "yy"])
fc = info_of(["xx*xx = 0", "xx*yy + yy*xx = 0", "yy != 0"], ["xx", "yy"])
fd = info_of(["xx*xx = -7", "xx*yy + yy*xx = 0", "yy != 0"], ["xx", "yy"])
check("V15: renaming and another nonzero number give the same shape",
      V.role_fingerprint(fa, shape=True) == V.role_fingerprint(fb, shape=True))
check("V15: a zero in place of a nonzero number is another shape",
      V.role_fingerprint(fa, shape=True) != V.role_fingerprint(fc, shape=True))
check("V15: a sign change is another shape", V.role_fingerprint(fa, shape=True) != V.role_fingerprint(fd, shape=True))
check("V11: another number is another world (V11 is up to renaming only)", V.role_fingerprint(fa) != V.role_fingerprint(fb))

# ---------------------------------------------------------------- new in 5b: certificates of variant worlds
wf3 = copy.deepcopy(world(wid))
wf3["builds"][0].update(role=["xa*xb*xc = xa", "xb*xc = 0", "xa != 0"], generators=["xa", "xb", "xc"],
                        origin="k01", frames=["f03"])
i3 = C.world_info(wf3)
r3 = RF.search_refutation(i3, [])
check("variant: a refutation exists in the framed test world", r3 is not None)
if r3 is not None:
    w3v = V.variant(wf3, role=V.first_chain_bracketed(i3, wf3["builds"][0]))
    p3 = V.variant_pool(i3, w3v, {"witness": [], "refutation": [([], r3)], "known": []})
    check("variant: with the frame, re-bracketing keeps the certificate valid (T9 is not a renumbering)",
          len(p3["refutation"]) == 1 and C.safe(C.check_refutation, p3["refutation"][0][1], C.world_info(w3v), [])[0])
    w3n = copy.deepcopy(wf3)
    w3n["builds"][0]["frames"] = []
    i3n = C.world_info(w3n)
    dn = ["q6", "q12", "q13", "q14"]                   # q5 kept: an associative ambient
    r3n = RF.search_refutation(i3n, dn)
    check("variant: a refutation exists without the frame, q5 kept", r3n is not None)
    if r3n is not None:
        w3nv = V.variant(w3n, role=V.first_chain_bracketed(i3n, w3n["builds"][0]))
        p3n = V.variant_pool(i3n, w3nv, {"witness": [], "refutation": [(dn, r3n)], "known": []})
        check("variant: q5 kept, the certificate carries over too",
              len(p3n["refutation"]) == 1 and C.safe(C.check_refutation, p3n["refutation"][0][1],
                                                     C.world_info(w3nv), dn)[0])
maps = V.relator_maps(i3, i3, False, False)
check("variant: an unchanged world maps every relator to itself",
      all(v is V.ZERO or v == k for k, v in maps[0].items()) and all(v == k for k, v in maps[1].items()))
fake = {"theta": None, "tree": {"node": "close", "target": {"ineq": 0}, "terms": [["1", {"ctx": 99}, []]]}}
check("variant: a relator added by a case node keeps its place after the role's",
      V.translate_refutation(fake, maps)["tree"]["terms"][0][1] == {"ctx": 99})

# ---------------------------------------------------------------- new in 5b: every copy unit gives relators
wk2 = copy.deepcopy(world(wid))
wk2["builds"][0].update(role=["xa*xb = xc", "xa != 0"], generators=["xa", "xb", "xc"], origin="k02", frames=[])
ik2 = C.world_info(wk2)
for u in C.COPIES:
    for assoc in (False, True):
        if assoc and u != "q6[on]":
            continue                       # associativity implies the q5 copies
        drop = [x for x in C.judged_units("k02", []) if x not in ({u} | ({"q5"} if assoc else set()))]
        s = RF.Searcher(ik2, drop)
        specs = [sp_ for sp_ in s.instance_specs(s.base_names) if sp_[0][1] == u]
        prod = [sp_ for sp_ in specs if any(isinstance(a[1], tuple) for a in sp_[0][2])]
        amb_name = "associative" if assoc else "non-associative"
        check(f"units: kept {u} gives relators in the {amb_name} ambient", bool(specs))
        if not assoc:
            check(f"units: kept {u} also takes the role's product xa*xb as an argument", bool(prod))


def cited_certs():
    for b_, e_ in all_keys():
        for r in e_.get("refutations") or []:
            yield b_, e_["id"], r["drop"], r["proof"]
    for wid_, o_ in OUT.items():
        for r in o_["procedure"].get("refutations") or []:
            yield "batch_dev", wid_, r["drop"], r["proof"]


seen_units = set()
for b_, w_, drop, proof in cited_certs():
    inf = C.world_info(C.R.load(os.path.join(HERE, b_, "worlds", w_ + ".json")))
    for u in sorted(RF.cited_units(proof) - seen_units):
        if u not in C.judged_units(inf["origin"], inf["frames"]) or u in drop:
            continue
        if not C.safe(C.check_refutation, proof, inf, drop)[0]:
            continue
        seen_units.add(u)
        check(f"units: a certificate citing {u} fails once {u} is dropped ({b_} {w_})",
              rejects(C.check_refutation, proof, inf, sorted(set(drop) | {u})))
print(f"      (units cited by some certificate in the dev data: {sorted(seen_units)})")

print("\nevery corruption caught" if fails == 0 else f"\n{fails} NOT CAUGHT")
sys.exit(1 if fails else 0)
