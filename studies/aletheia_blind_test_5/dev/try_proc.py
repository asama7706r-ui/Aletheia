"""Quick dev runs of the procedure on hand-written builds, checked against the reference (not sealed)."""
import os, sys, time, json
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scorer")); sys.path.insert(0, os.path.join(ROOT, "procedure"))
import ref_v5 as RF, procedure_v5 as PR, certs_v5 as C  # noqa: E402

def W(origin, gens, role, frames=()):
    return {"builds": [{"id": "b1", "origin": origin, "generators": gens, "role": role, "frames": list(frames), "src": "dev"}]}

CASES = {
 "sqrt2": W("k01", ["x"], ["x*x = 2"]),
 "cbrt2": W("k01", ["x"], ["x*x*x = 2"]),
 "i_over_R": W("k01", ["x"], ["x*x = -1"]),
 "sqrt_i": W("k02", ["u"], ["u*u = e1"]),
 "free": W("k01", ["x"], ["x = 0^-1"]),
 "impossible": W("k01", ["x"], ["x = 1", "x*x = 2"]),
 "quat": W("k01", ["a", "b"], ["a*a = -1", "b*b = -1", "a*b = -(b*a)"]),
 "splitcomplex": W("k01", ["j"], ["j*j = 1", "j != 1", "j != -1"]),
 "nilpotent": W("k01", ["t"], ["t*t = 0", "t != 0"]),
 "quat_over_C": W("k02", ["h"], ["h*h = -1", "h*e1 = -(e1*h)"]),
 "quat_frame": W("k01", ["a", "b"], ["a*a = -1", "b*b = -1", "a*b = -(b*a)"], ["f03"]),
 "quat_chain": W("k01", ["i", "j", "k"], ["i*i = -1", "j*j = -1", "k*k = -1", "i*j*k = -1"]),
 "quat_bracket": W("k01", ["i", "j", "k"], ["i*i = -1", "j*j = -1", "k*k = -1", "(i*j)*k = -1"]),
 "cl3": W("k01", ["a", "b", "c"], ["a*a = 1", "b*b = 1", "c*c = 1", "a*b = -(b*a)", "b*c = -(c*b)", "a*c = -(c*a)"]),
 "dirac": W("k01", ["g0", "g1", "g2", "g3"], ["g0*g0 = 1", "g1*g1 = -1", "g2*g2 = -1", "g3*g3 = -1",
            "g0*g1 = -(g1*g0)", "g0*g2 = -(g2*g0)", "g0*g3 = -(g3*g0)", "g1*g2 = -(g2*g1)", "g1*g3 = -(g3*g1)", "g2*g3 = -(g3*g2)"], ["f03"]),
 "tessarine_C": W("k02", ["j"], ["j*j = 1", "j != 1", "j != -1", "j != e1", "j != -e1"]),
 "t13_c": W("k02", ["hh", "kk"], ["hh*hh = -1", "kk*kk = -1", "hh*kk = -(kk*hh)"]),
 "t13_r": W("k01", ["hh", "kk"], ["hh*hh = -1", "kk*kk = -1", "hh*kk = -(kk*hh)"]),
 "t14": W("k01", ["xa", "ya"], ["xa*xa*xa = -xa", "xa != 0", "ya*ya = -1", "xa*ya = -(ya*xa)"]),
 "t9_chain": W("k02", ["xx"], ["e1*xx*e1 = xx", "xx*xx = -1"]),
 "t9_brk": W("k02", ["xx"], ["(e1*xx)*e1 = xx", "xx*xx = -1"]),
 "t9b_chain": W("k01", ["aa", "bb"], ["aa*aa = 1", "bb*bb = 1", "aa*bb*aa = -bb"]),
 "t9b_brk": W("k01", ["aa", "bb"], ["aa*aa = 1", "bb*bb = 1", "(aa*bb)*aa = -bb"]),
}

def summary(t):
    if t["verdict"] in ("NEW_KIND", "BRANCHES", "NO_WITNESS"):
        return t["verdict"], sorted((tuple(b["drop"]), b["status"]) for b in t["branches"])
    return t["verdict"], t.get("known", {}).get("kind") if t.get("known") else None

for name in sys.argv[1:] or CASES:
    w = CASES[name]
    t0 = time.time()
    out = PR.solve_world(w, budget=300)
    t1 = time.time()
    info = C.world_info(w)
    pool = {"witness": [], "refutation": [], "known": []}
    for b in out.get("branches", []):
        if b.get("witness"):
            pool["witness"].append((b["drop"], b["witness"]))
        for u, pr in b.get("proofs", {}).items():
            pool["refutation"].append(([x for x in b["drop"] if x != u], pr))
    if out.get("known"):
        pool["known"].append(out["known"])
    tr = RF.truth(w, pool)
    ps, ts = summary(out), summary(tr)
    print(f"== {name}: procedure {t1-t0:.1f}s, reference {time.time()-t1:.1f}s  {'AGREE' if ps == ts else 'DIFFER'}")
    print("   procedure:", ps)
    if ps != ts:
        print("   reference:", ts)
    if out.get("known"):
        print("   known cert:", json.dumps(out["known"])[:200], C.safe(C.check_known, out["known"], info))
    for b in out.get("branches", []):
        bad = [u for u in b["drop"] if u not in b["proofs"]]
        if bad:
            print("   branch", b["drop"], "FORCED without proof:", bad)
