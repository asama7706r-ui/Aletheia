"""Quick dev runs of the reference on hand-written builds (not a sealed check)."""
import os, sys, time, json
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scorer"))
import ref_v5 as RF  # noqa: E402

def W(origin, gens, role, frames=()):
    return {"builds": [{"id": "b1", "origin": origin, "generators": gens, "role": role, "frames": list(frames), "src": "dev"}]}

cases = {
 "sqrt2": (W("k01", ["x"], ["x*x = 2"]), {}),
 "i_over_R": (W("k01", ["x"], ["x*x = -1"]), {}),
 "free": (W("k01", ["x"], ["x = 0^-1"]), {}),
 "impossible": (W("k01", ["x"], ["x = 1", "x*x = 2"]), {}),
}
QT = [[1,1,0,"-1"],[2,2,0,"-1"],[3,3,0,"-1"],[1,2,3,"1"],[2,1,3,"-1"],[2,3,1,"1"],[3,2,1,"-1"],[3,1,2,"1"],[1,3,2,"-1"]]
I4 = [["1" if i == j else "0" for j in range(4)] for i in range(4)]
CJ = [[("1" if i == 0 else "-1") if i == j else "0" for j in range(4)] for i in range(4)]
H = {"dim": 4, "table": QT, "theta": None, "gens": {"a": ["0","1","0","0"], "b": ["0","0","1","0"]}, "q12": {"N": I4, "C": CJ}, "q13": None}
T3 = {"dim": 3, "table": [[1,1,0,"-1"],[2,2,0,"-1"]], "theta": None, "gens": {"a": ["0","1","0"], "b": ["0","0","1"]}, "q12": None,
      "q13": {"N": [["1","0","0"],["0","1","0"],["0","0","1"]], "C": [["1","0","0"],["0","-1","0"],["0","0","-1"]]}}
cases["quat"] = (W("k01", ["a","b"], ["a*a = -1", "b*b = -1", "a*b = -(b*a)"]), {"witness": [(["q6","q14"], H), (["q5","q12","q14"], T3)]})
cases["quat_H_only"] = (W("k01", ["a","b"], ["a*a = -1", "b*b = -1", "a*b = -(b*a)"]), {"witness": [(["q6","q14"], H)]})
# C1-like j*j = 1 with the split-complex witness
SC = {"dim": 2, "table": [[1,1,0,"1"]], "theta": None, "gens": {"j": ["0","1"]}, "q12": None, "q13": None}
cases["splitcomplex"] = (W("k01", ["j"], ["j*j = 1", "j != 1", "j != -1"]), {"witness": [(["q12","q13","q14"], SC)]})
for name in sys.argv[1:] or cases:
    w, pool = cases[name]
    t0 = time.time()
    t = RF.truth(w, pool)
    t.pop("found_refutations", None)
    print(f"== {name} ({time.time()-t0:.1f}s)")
    print(json.dumps({k: v for k, v in t.items() if k != "statuses"}, ensure_ascii=False)[:600])
    if "statuses" in t:
        print("   statuses:", t["statuses"])
