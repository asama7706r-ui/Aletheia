from wcheck import *
world = {"id": "E1-09", "experiment": "E1",
  "generators": [{"name": "x", "grade": 0}, {"name": "y", "grade": 0}],
  "variables": ["s", "t"],
  "laws": ["(s*x + t*y)**2 = s**2 + t**2",
           "(x*y)**3 = x*y",
           "x*y*x = -y",
           "(1 + x)*(1 - x) = 0"]}
cl = {"x": [["1","0"],["0","-1"]], "y": [["0","1"],["1","0"]]}
key = {"id": "E1-09", "label": "CONTRADICTION",
  "category": "contradiction: Euclidean Clifford reflections whose product is claimed to satisfy (x*y)^3 = x*y",
  "notes": "Derivation: law 1 gives x^2 = y^2 = 1 and x*y = -y*x, so (x*y)^2 = -x*x*y*y = -1 and (x*y)^3 = -x*y. Law 2 then gives 2*x*y = 0, so x*y = 0 and y = x*(x*y) = 0, hence 1 = y^2 = 0. Laws 3 and 4 are consequences of law 1. Without law 2 the laws have the model Cl(2,0) = M2(Q); without law 1 they have x = 1, y = 0."}
extra = {"single_models": {0: cl}, "loo_models": {1: cl}}
errs, info = check_E1(world, key, extra)
print("E1-09 checks:", "PASS" if not errs else "FAIL")
if errs: print(errs)
else:
    save_world_and_key(world, key); print(update_progress("E1-09 saved; next E1-10"))
