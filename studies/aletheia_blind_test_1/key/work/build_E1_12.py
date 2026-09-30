from wcheck import *
world = {"id": "E1-12", "experiment": "E1",
  "generators": [{"name": "s", "grade": 0}, {"name": "r", "grade": 0}],
  "variables": ["t"],
  "laws": ["s*s = 1",
           "r**3 = 1",
           "s*r*s = r*r",
           "(1 - r)*(1 + r + r**2) = 0",
           "((1 + r + r**2)*(1 - s))**2 = 6*(1 + r + r**2)*(1 - s)",
           "(1 + t*s)*(1 - t*s) = 1 - t**2"]}
# faithful 4-dim representation: trivial + sign + standard
Sm = [["1","0","0","0"],["0","-1","0","0"],["0","0","0","1"],["0","0","1","0"]]
Rm = [["1","0","0","0"],["0","1","0","0"],["0","0","0","-1"],["0","0","1","-1"]]
obs = ["r*s - s*r", "1 - r", "1 + r + r**2", "(1 + r + r**2)*(1 - s)"]
key = {"id": "E1-12", "label": "NEW_KIND", "true_family": "assoc", "true_dim": 6,
  "witness": {"s": Sm, "r": Rm},
  "observed_nonzero": obs,
  "complete_presentation": True,
  "category": "new kind (assoc, outside the familiar list): group algebra of the symmetric group S3 (reflection s, rotation r)",
  "notes": "T = Q[S3] = Q x Q x M2(Q), faithful witness = trivial + sign + standard representation (4x4, the minimal faithful size). Law 5 says the signed sum over S3 is (6 times) an idempotent. In comm (= graded, grades 0) law 3 gives r = r^2, so r = 1 and the rotation defect 1 - r of law 4 collapses; rational values also force r = 1. Laws present T completely (dim 6)."}
errs, info = check_E1(world, key, {"roles": ["1 - r", "1 + r + r**2", "(1 + r + r**2)*(1 - s)"]})
print("E1-12 checks:", "PASS" if not errs else "FAIL")
if errs: print(errs)
else:
    save_world_and_key(world, key); print(update_progress("E1-12 saved; next E1-13"))
