from wcheck import *
world = {"id": "E1-07", "experiment": "E1",
  "generators": [{"name": "a", "grade": 1}, {"name": "b", "grade": 1}],
  "variables": ["s", "t"],
  "parameters": ["c"],
  "laws": ["a**2 = 0",
           "b*b = 0",
           "a*b + b*a = c**2 - c + 1",
           "a*b*a = a",
           "(1 + s*b*a)*(1 + t*b*a) = 1 + (s + t + s*t)*b*a"]}
A = [["0","1"],["0","0"]]; B = [["0","0"],["1","0"]]
obs = ["a*b - b*a", "a*b + b*a", "a", "b", "b*a"]
und = {}
for c in PARAM_GRID:
    if c in (0, 1):
        und[fstr(c)] = {"decision": "NEW_KIND:assoc", "witness": {"a": A, "b": B}, "dim": 4, "observed": obs}
    else:
        und[fstr(c)] = {"decision": "CONTRADICTION"}
key = {"id": "E1-07", "label": "UNDERDETERMINED",
  "category": "underdetermined: fermionic mode with unknown anticommutator normalization c^2 - c + 1 and partial-isometry law a*b*a = a",
  "notes": "Let f = c^2 - c + 1 (never 0 for rational c). Laws 1,3 give a*b*a = a*(f - a*b) = f*a, so law 4 gives (f - 1)*a = 0. c in {0,1} (f = 1): canonical anticommutation relations, T = M2(Q) (a = E12, b = E21), NEW_KIND assoc (comm and graded both force 1 = 0). c in {-3,-2,-1,2,3,1/2} (f != 1): a = 0, then law 3 gives 0 = f, so CONTRADICTION."}
errs, info = check_E1(world, key, {"roles": ["a", "b", "b*a"], "und": und})
print("E1-07 checks:", "PASS" if not errs else "FAIL")
if errs: print(errs)
else:
    save_world_and_key(world, key); print(update_progress("E1-07 saved; next E1-08"))
