#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The validator of blind test 5b (protocol_v5b.md, Sections 3, 5 and 6).

Usage: python scorer/validate_v5b.py BATCH_DIR [--quick]
BATCH_DIR holds worlds/W-01.json ... W-30.json and key/key.json. Prints, for every world, its errors,
the candidates the reference could not decide, and the trap and baseline facts; then the composition
checks; and finally VALID or NOT VALID. --quick skips the composition checks (for a few worlds).
"""
import hashlib
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import certs_v5 as C  # noqa: E402
import ref_v5b as RF  # noqa: E402
import baselines_v5b as BL  # noqa: E402

R = C.R
SEED = os.path.join(ROOT, "seed", "seed_registry.json")
DEV_FP = os.path.join(HERE, "dev_fingerprints_5b.json")
SEED_IDS = {"f01", "f02", "f03", "k01", "k02", "e1", "t1", "t5_tower"} | {f"q{i}" for i in range(1, 15)}
TRAPS = [f"T{i}" for i in range(1, 16)]
T6_ENABLED = True             # development found a mirror pair (Section 2.7, dev world mirror1)
COMPOSITION = {"NEW_KIND": 9, "BRANCHES": 6, "KNOWN_SUFFICES": 5, "NO_WITNESS": 4, "FREEDOM": 3, "IMPOSSIBLE": 3}


def load_seed():
    ctx, reg = R.check_registry(R.load(SEED), SEED)
    if ctx.errors or reg is None:
        raise SystemExit("the sealed seed does not read: " + "; ".join(ctx.errors))
    return reg


# ---------------------------------------------------------------- per-world form checks (V1-V5, V11, V15)
def leaves_of_product(ast):
    if ast[0] == "prod":
        return sum(leaves_of_product(x) for x in ast[1])
    return 1


def walk_terms(ast, fn):
    fn(ast)
    t = ast[0]
    if t in ("prod", "sum"):
        for x in ast[1]:
            walk_terms(x, fn)
    elif t in ("neg", "inv"):
        walk_terms(ast[1], fn)


def form_errors(world, reg):
    errs = []
    ctx, canon = R.check_world(world, reg, "world")
    errs += list(ctx.errors)
    if errs:
        return errs, None
    for k in ("bodies", "quantities", "relations", "laws", "observers", "observations", "fillers"):
        if world.get(k) != []:
            errs.append(f"V2: '{k}' must be []")
    if not isinstance(world.get("builds"), list) or len(world["builds"]) != 1:
        return errs + ["V2: exactly one build"], None
    b = world["builds"][0]
    info = C.world_info(world)
    if b["origin"] not in ("k01", "k02"):
        errs.append("V2: origin must be k01 or k02")
    if b["frames"] not in ([], ["f03"]):
        errs.append("V2: frames must be [] or ['f03']")
    if not 1 <= len(b["generators"]) <= 4:
        errs.append("V2: 1 to 4 generators")
    if not 1 <= len(b["role"]) <= 12:
        errs.append("V2: 1 to 12 role sentences")
    for g in b["generators"]:
        if not (2 <= len(g) <= 6) or not g[0].isalpha() or not all(c.isdigit() or ("a" <= c <= "z") for c in g):
            errs.append(f"V2: name '{g}' must have 2 to 6 lowercase letters and digits, starting with a letter")
        if g in SEED_IDS:
            errs.append(f"V2: name '{g}' is a seed id")
    for g in [world.get("id"), b.get("id")]:
        if g in SEED_IDS:
            errs.append(f"V2: id '{g}' is a seed id")
    bad = []

    def chk(node):
        t = node[0]
        if t == "prod" and leaves_of_product(node) > C.BOUNDS["P2"]:
            bad.append(f"V2: a product has more than P2 = {C.BOUNDS['P2']} factors")
        if t == "num" and abs(node[1]) > 100:
            bad.append("V2: a number above 100")
        if t == "frac" and (abs(node[1]) > 100 or node[2] > 100):
            bad.append("V2: a fraction above 100")
        if t == "inv" and node[1] != ("num", 0):
            bad.append("V2: ^-1 only as 0^-1")
    for op, l, r in info["atoms"]:
        walk_terms(l, chk)
        walk_terms(r, chk)
    errs += sorted(set(bad))
    if RF.has_free_slot(info):
        defined = set()
        for j, (op, l, r) in enumerate(info["atoms"]):
            names = set()
            walk_terms(r, lambda n: names.add(n[1]) if n[0] == "name" else None)
            if op != "=" or l[0] != "name" or l[1] not in b["generators"] or l[1] in defined:
                errs.append(f"V3: FREEDOM role sentence {j} must be 'g = t' defining a new generator once")
                continue
            if any(x not in defined and x != "e1" for x in names):
                errs.append(f"V3: sentence {j} uses a generator not defined before it")
            defined.add(l[1])
    return errs, info


def abstract_numbers(ast):
    """The role term with every nonzero number written as 1 (signs stay, as negations): its shape (V15)."""
    t = ast[0]
    if t in ("num", "frac"):
        return ("num", 0 if ast[1] == 0 else 1)
    if t in ("prod", "sum"):
        return (t, tuple(abstract_numbers(x) for x in ast[1]))
    if t in ("neg", "inv"):
        return (t, abstract_numbers(ast[1]))
    return ast


def role_fingerprint(info, shape=False):
    """SHA-256 of the canonical role up to renaming the generators, with origin and frames (V11). With shape=True,
    also up to changing the nonzero numbers (V15; test 5 audit, lesson 1)."""
    best = None
    gens = info["generators"]
    f = abstract_numbers if shape else (lambda a: a)
    for p in itertools.permutations(range(len(gens))):
        perm = {g: f"zz{p[i]}" for i, g in enumerate(gens)}
        sents = sorted(C.atom_key(op, f(C.rename_ast(l, perm)), f(C.rename_ast(r, perm))) for op, l, r in info["atoms"])
        s = json.dumps([info["origin"], info["frames"], sents])
        if best is None or s < best:
            best = s
    return hashlib.sha256(best.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- certificates of a variant world (T9, T10, T13)
ZERO = object()


def relator_maps(info_a, info_b, assoc, comm):
    """Where each relator and inequation of world a sits in world b: matched by their elements in the ambient algebra
    of the certificate's candidate (assoc, comm), never by their numbers (test 5 audit, lesson 3). A relator that is 0
    in that ambient maps to ZERO (its terms contribute nothing); an unmatched one maps to None."""
    amb = C.Ambient(C.Field(None), assoc, comm)

    def ctx(info):
        names = set(info["generators"]) | ({"e1"} if info["origin"] == "k02" else set())
        rels, ineqs = C.role_context(info["atoms"], amb, names, info["origin"])
        return [repr(sorted(r.items(), key=repr)) if r else None for r in rels], \
            [repr(sorted(r.items(), key=repr)) for r in ineqs]
    ra, ia = ctx(info_a)
    rb, ib = ctx(info_b)
    rmap = {i: (ZERO if k is None else (rb.index(k) if k in rb else None)) for i, k in enumerate(ra)}
    imap = {i: (ib.index(k) if k in ib else None) for i, k in enumerate(ia)}
    return rmap, imap, len(ra), len(rb)


def translate_refutation(cert, maps):
    """The refutation with its relator and inequation numbers moved to the variant world, or None when it cites
    one the variant does not have. Terms citing a relator that is 0 in the ambient are left out; relators added by
    case nodes keep their place after the role's relators."""
    rmap, imap, na, nb = maps

    def rel(x):
        if isinstance(x, dict) and set(x) == {"ctx"}:
            i = x["ctx"]
            j = rmap.get(i) if i < na else i - na + nb
            if j is None:
                raise KeyError(i)
            return j if j is ZERO else {"ctx": j}
        return walk(x)

    def walk(x):
        if isinstance(x, dict):
            if set(x) == {"ineq"}:
                j = imap.get(x["ineq"])
                if j is None:
                    raise KeyError(x["ineq"])
                return {"ineq": j}
            out = {}
            for k, v in x.items():
                if k in ("terms", "proof_ab"):
                    out[k] = [[t[0], r, walk(t[2])] for t in v for r in [rel(t[1])] if r is not ZERO]
                else:
                    out[k] = walk(v)
            return out
        if isinstance(x, list):
            return [walk(v) for v in x]
        return x
    try:
        return walk(cert)
    except (KeyError, TypeError, IndexError):
        return None


def variant_pool(info, world2, pool):
    """The pool for a variant world: witnesses and known-kind certificates as they are, refutations translated
    in the ambient algebra of their own candidate."""
    info2 = C.world_info(world2)
    U = C.judged_units(info["origin"], info["frames"])
    maps, refs = {}, []
    for d, cert in pool.get("refutation", []):
        kept = set(U) - set(d)
        amb = ("f03" in info["frames"] or "q5" in kept, "q6" in kept)
        if amb not in maps:
            maps[amb] = relator_maps(info, info2, *amb)
        c2 = translate_refutation(cert, maps[amb])
        if c2 is not None:
            refs.append((d, c2))
    return {"witness": list(pool.get("witness", [])), "refutation": refs, "known": list(pool.get("known", []))}


# ---------------------------------------------------------------- the key and the truth (V6-V9)
def key_pool(entry, info):
    pool = {"witness": [], "refutation": [], "known": []}
    U = C.judged_units(info["origin"], info["frames"])
    for b in entry.get("branches") or []:
        if b.get("witness"):
            pool["witness"].append((b["drop"], b["witness"]))
            if b.get("mirror"):
                pass
    if entry.get("top_witness"):
        pool["witness"].append((sorted(U), entry["top_witness"]))
    for r in entry.get("refutations") or []:
        pool["refutation"].append((r["drop"], r["proof"]))
    if entry.get("known"):
        pool["known"].append(entry["known"])
    return pool


def norm_branches(branches):
    out = set()
    for b in branches or []:
        if b.get("mirror"):
            out.add((frozenset([tuple(sorted(b["drop"])), tuple(sorted(b["mirror"]["twin"]))]), b["status"]))
        else:
            out.add((frozenset([tuple(sorted(b["drop"]))]), b["status"]))
    return out


def decision_equal(out, truth):
    """Section 8.2: the decision of an output equals the truth's."""
    v = truth["verdict"]
    if out.get("verdict") != v:
        return False
    if v in ("NEW_KIND", "BRANCHES", "NO_WITNESS"):
        return norm_branches(out.get("branches")) == norm_branches(truth["branches"])
    if v == "KNOWN_SUFFICES":
        return (out.get("known") or {}).get("kind") == truth["known"]["kind"]
    if v == "FREEDOM":
        f = out.get("freedom")
        return f is None or (f.get("slot") == "0^-1" and f.get("fate", "undecided") == "undecided")
    return True


def check_key_certs(entry, info):
    errs = []
    U = C.judged_units(info["origin"], info["frames"])
    for b in entry.get("branches") or []:
        if b.get("witness"):
            ok, why = C.safe(C.check_witness, b["witness"], info, b["drop"])
            if not ok:
                errs.append(f"V9: the witness of branch {b['drop']} fails: {why}")
        if b.get("mirror"):
            ok, why = C.safe(C.check_mirror, b["mirror"], b["drop"], b["mirror"].get("twin", []), info)
            if not ok:
                errs.append(f"V9: the mirror of branch {b['drop']} fails: {why}")
    if entry.get("top_witness"):
        ok, why = C.safe(C.check_witness, entry["top_witness"], info, sorted(U))
        if not ok:
            errs.append(f"V8: top_witness fails: {why}")
    for r in entry.get("refutations") or []:
        ok, why = C.safe(C.check_refutation, r["proof"], info, r["drop"])
        if not ok:
            errs.append(f"V9: the refutation of {r['drop']} fails: {why}")
    if entry.get("known"):
        ok, why = C.safe(C.check_known, entry["known"], info)
        if not ok:
            errs.append(f"V6: the known-kind solution fails: {why}")
    return errs


def summary(t):
    v = t["verdict"]
    if v in ("NEW_KIND", "BRANCHES", "NO_WITNESS"):
        return (v, frozenset(norm_branches(t["branches"])))
    if v == "KNOWN_SUFFICES":
        return (v, t["known"]["kind"])
    return (v, None)


# ---------------------------------------------------------------- traps (Section 6)
def variant(world, **change):
    w = json.loads(json.dumps(world))
    b = w["builds"][0]
    b.update(change)
    return w


def first_chain_bracketed(info, build):
    """The role with its first unbracketed chain replaced by its left-bracketed form, or None."""
    done = [False]

    def fix(ast):
        t = ast[0]
        if t == "prod":
            items = [fix(x) for x in ast[1]]
            if len(items) >= 3 and not done[0]:
                done[0] = True
                acc = ("prod", (items[0], items[1]))
                for x in items[2:]:
                    acc = ("prod", (acc, x))
                return acc
            return ("prod", tuple(items))
        if t == "sum":
            return ("sum", tuple(fix(x) for x in ast[1]))
        if t in ("neg", "inv"):
            return (t, fix(ast[1]))
        return ast
    role = []
    for op, l, r in info["atoms"]:
        l2, r2 = fix(l), fix(r)
        role.append(f"{R.sent_render(l2)} {op} {R.sent_render(r2)}")
    return role if done[0] else None


def quotient_witness(info, branch):
    """T14: the branch's witness satisfies a relation of length <= 2 among the generators that the
    role and the kept equations do not give (it is a proper quotient of the template)."""
    w = branch.get("witness")
    if not w or w.get("theta") is not None:
        return False
    T = C.Table(w, C.BOUNDS)
    gens = info["generators"] + (["e1"] if info["origin"] == "k02" else [])
    vals = {g: [C.frac(x) for x in w["gens"][g]] for g in info["generators"]}
    if info["origin"] == "k02":
        vals["e1"] = [C.frac(x) for x in w["E"]]
    words = [("1",)] + [(g,) for g in gens] + [(a, b) for a in gens for b in gens]

    def value(wd):
        if wd == ("1",):
            v = [C.Fr(0)] * T.n
            v[0] = C.Fr(1)
            return v
        if len(wd) == 1:
            return vals[wd[0]]
        return T.mulq(vals[wd[0]], vals[wd[1]])
    import sympy as sp
    M = sp.Matrix([[value(wd)[k] for wd in words] for k in range(T.n)])
    ns = M.nullspace()
    if not ns:
        return False
    s = RF.Searcher(info, branch["drop"])
    I = s.ideal([], s.base_names)
    for vec in ns:
        el = {}
        for c, wd in zip(vec, words):
            if c != 0:
                key = s.amb.unit if wd == ("1",) else (s.amb.name_word(wd[0]) if len(wd) == 1 else
                                                     s.amb.mulw(s.amb.name_word(wd[0]), s.amb.name_word(wd[1])))
                el[key] = el.get(key, 0) + C.Fr(int(sp.Rational(c).p), int(sp.Rational(c).q))
        el = {k: v for k, v in el.items() if v}
        if el and I.member(el) is None:
            return True
    return False


def trap_facts(world, info, truth, cl, base, entry, pool):
    """Which trap conditions hold (computed, never declared)."""
    facts = {}
    v = truth["verdict"]
    branched = v in ("NEW_KIND", "BRANCHES", "NO_WITNESS")
    tb = truth.get("branches", []) if branched else []
    drops = [set(b["drop"]) for b in tb]
    mx = base["MAXCON"]["branches"]
    facts["T1"] = any("q2" in b["drop"] and "q1" not in b["drop"] for b in mx)
    facts["T2"] = any(sorted(b["drop"]) == ["q1", "q2"] for b in mx)
    mins = cl.minimal() if cl is not None and branched else []
    facts["T3"] = len({len(m) for m in mins}) > 1 and not decision_equal(base["COUNT"], truth)
    facts["T4"] = info["origin"] == "k02" and any("q6" in d and "q6[on]" not in d for d in drops) \
        and not decision_equal(base["COARSE"], truth)
    facts["T5"] = info["origin"] == "k01" and any("q14" in d for d in drops) \
        and len(base["SPLIT_ORDER"]["branches"]) > len(tb)
    facts["T6"] = any(b.get("mirror") for b in tb)
    facts["T7"] = v == "KNOWN_SUFFICES" and info["origin"] == "k01" and truth["known"]["kind"] == "k02"
    facts["T8"] = any("q5" in d for d in drops) and any("q5" not in d for d in drops) \
        and not decision_equal(base["ASSOC"], truth)
    facts["T11"] = branched and bool(drops) and all("q12" in d for d in drops)
    facts["T12"] = v == "FREEDOM"
    kn = (entry or {}).get("known") or {}
    irr = False
    if v == "KNOWN_SUFFICES" and truth["known"]["kind"] == "k01" and kn.get("theta"):
        irr = any(isinstance(x, list) and any(C.frac(c) != 0 for c in x[1:]) for x in kn.get("values", {}).values())
    facts["T15"] = irr
    facts["T14"] = any(b["status"] == "witnessed" and "q12" not in b["drop"] and quotient_witness(info, b)
                       for b in (entry or {}).get("branches") or [] if b.get("witness"))
    # variants: the pool's refutations are carried over by their relators, not their numbers (variant_pool)
    facts["T9"] = False
    role2 = first_chain_bracketed(info, world["builds"][0])
    if role2 is not None:
        w2 = variant(world, role=role2)
        t2 = RF.truth(w2, variant_pool(info, w2, pool))
        facts["T9"] = summary(t2) != summary(truth)
    facts["T10"] = False
    if info["frames"] == ["f03"]:
        w2 = variant(world, frames=[])
        t2 = RF.truth(w2, variant_pool(info, w2, pool))
        facts["T10"] = summary(t2) != summary(truth)
    facts["T13"] = False
    uses_e1 = any("e1" in s for s in world["builds"][0]["role"])
    if info["origin"] == "k02" and not uses_e1:
        w2 = variant(world, origin="k01")
        t2 = RF.truth(w2, variant_pool(info, w2, pool))
        facts["T13"] = summary(t2) != summary(truth)
    return facts


# ---------------------------------------------------------------- one world
def validate_world(path, entry, reg, dev_fps):
    errs = []
    world = R.load(path)
    ferrs, info = form_errors(world, reg)
    errs += ferrs
    if info is None or errs:
        return {"errors": errs, "info": info}       # a world that fails its form is not judged further
    fp = role_fingerprint(info)
    if fp in dev_fps:
        errs.append("V11: the world reproduces a dev world")
    if entry is None:
        return {"errors": errs + ["the key has no entry for this world"], "fp": fp}
    errs += check_key_certs(entry, info)
    pool = key_pool(entry, info)
    truth, cl = RF.truth_full(world, pool)
    if truth["verdict"] == "UNDETERMINED":
        errs.append("V14: " + truth["why"])
    if truth["verdict"] == "OUTSIDE_W":
        errs.append("V8: " + truth["why"])
    if truth["verdict"] == "KNOWN_SUFFICES" and not any(
            k.get("kind") == truth["known"]["kind"] and C.safe(C.check_known, k, info)[0] for k in pool["known"]):
        errs.append("V6: the key gives no valid solution in the smallest tower kind")
    key_t = {"verdict": entry.get("verdict"), "branches": entry.get("branches") or [],
             "known": entry.get("known"), "freedom": entry.get("freedom")}
    if not decision_equal(key_t, truth):
        errs.append(f"V9: the key disagrees with the reference truth: key {summary_safe(key_t)} vs truth {summary_safe(truth)}")
    undecided = sorted(k for k, s in (truth.get("statuses") or {}).items() if s == "UNDECIDED")
    res = {"errors": errs, "fp": fp, "shape": role_fingerprint(info, shape=True), "truth": truth,
           "undecided": undecided, "info": info}
    if truth["verdict"] in ("UNDETERMINED", "OUTSIDE_W"):
        return res
    base = BL.run_all(world, truth, cl, info, pool)
    res["baselines_wrong"] = sorted(n for n, o in base.items() if not decision_equal(o, truth))
    facts = trap_facts(world, info, truth, cl, base, entry, pool)
    res["traps"] = sorted(t for t, ok in facts.items() if ok)
    for t in entry.get("traps") or []:
        if t not in TRAPS:
            errs.append(f"V12: unknown trap {t}")
        elif not facts.get(t):
            errs.append(f"V12: the declared trap {t} does not hold")
    return res


def summary_safe(t):
    try:
        s = summary(t)
        return (s[0], sorted(sorted(map(list, x[0])) + [x[1]] for x in s[1]) if isinstance(s[1], frozenset) else s[1])
    except Exception:
        return t.get("verdict")


def validate_batch(batch, quick=False, only=None):
    reg = load_seed()
    dev_fps = set(json.load(open(DEV_FP, encoding="utf-8"))) if os.path.exists(DEV_FP) else set()
    key_path = os.path.join(batch, "key", "key.json")
    key = {e["id"]: e for e in json.load(open(key_path, encoding="utf-8"))} if os.path.exists(key_path) else {}
    files = sorted(f for f in os.listdir(os.path.join(batch, "worlds")) if f.endswith(".json"))
    results = {}
    for f in files:
        wid = f[:-5]
        if only and wid not in only:
            continue
        r = validate_world(os.path.join(batch, "worlds", f), key.get(wid), reg, dev_fps)
        results[wid] = r
        status = "ok " if not r["errors"] else "BAD"
        print(f"{status} {wid}: {r.get('truth', {}).get('verdict', '-')}  traps={r.get('traps', [])}  "
              f"baselines wrong={r.get('baselines_wrong', [])}", flush=True)
        for e in r["errors"]:
            print(f"      {e}")
        if r.get("undecided"):
            print(f"      undecided candidates (no witness, no refutation found): {r['undecided'][:12]}")
    errs = []
    if not quick:
        expected = [f"W-{i:02d}" for i in range(1, 31)]
        if [f[:-5] for f in files] != expected:
            errs.append("the batch must hold exactly W-01.json ... W-30.json")
        if set(key) != set(expected):
            errs.append("the key must have exactly one entry per world")
        good = {w: r for w, r in results.items() if not r["errors"]}
        if len(good) != 30:
            errs.append(f"{30 - len(good)} worlds are invalid")
        counts = {}
        for r in good.values():
            counts[r["truth"]["verdict"]] = counts.get(r["truth"]["verdict"], 0) + 1
        for v, n in COMPOSITION.items():
            if counts.get(v, 0) != n:
                errs.append(f"composition: {counts.get(v, 0)} {v} worlds, {n} required")
        origins = [r["info"]["origin"] for r in good.values()]
        for o in ("k01", "k02"):
            if origins.count(o) < 10:
                errs.append(f"composition: {origins.count(o)} worlds with origin {o}, at least 10 required")
        if sum(1 for r in good.values() if r["info"]["frames"]) < 3:
            errs.append("composition: at least 3 worlds with the frame f03")
        for t in TRAPS:
            if t == "T6" and not T6_ENABLED:
                continue
            n = sum(1 for r in good.values() if t in r.get("traps", []))
            if n < 2:
                errs.append(f"composition: trap {t} holds in {n} worlds, at least 2 required")
        t7 = sum(1 for r in good.values() if "T7" in r.get("traps", []))
        t15 = sum(1 for r in good.values() if "T15" in r.get("traps", []))
        if t7 < 2 or t15 < 2:
            errs.append("composition: KNOWN_SUFFICES needs at least 2 T7 and 2 T15 worlds")
        for n in BL.NAMES:
            k = sum(1 for r in good.values() if n in r.get("baselines_wrong", []))
            if k < 8:
                errs.append(f"composition: baseline {n} is wrong in {k} worlds, at least 8 required")
        shapes = {}
        for w, r in sorted(good.items()):
            shapes.setdefault(r["shape"], []).append(w)
        for ws in shapes.values():
            if len(ws) > 1:
                errs.append(f"V15: {', '.join(ws)} have the same role up to renaming and the nonzero numbers")
    for e in errs:
        print("BATCH: " + e)
    bad = any(r["errors"] for r in results.values()) or errs
    print("NOT VALID" if bad else "VALID")
    return not bad, results


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 1:
        print(__doc__)
        sys.exit(2)
    ok, _ = validate_batch(args[0], quick="--quick" in sys.argv, only=set(args[1:]) or None)
    sys.exit(0 if ok else 1)
