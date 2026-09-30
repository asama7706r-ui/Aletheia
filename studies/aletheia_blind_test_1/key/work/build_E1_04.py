from wcheck import *
world = {"id": "E1-04", "experiment": "E1",
  "generators": [{"name": "d", "grade": 0}, {"name": "n", "grade": 0}],
  "variables": ["s"],
  "laws": ["(d - 1)*(d - 2)*(d - 3) = 0",
           "d*(1 + s*n) = (1 + s*n)*d - s*n",
           "n*(d - 2)*(d - 3) = 0",
           "d*n*n = n*n*(d - 2)",
           "(1 + n)*(1 - n + n**2) = 1"]}
D = [["1","0","0"],["0","2","0"],["0","0","3"]]
Nn = [["0","1","0"],["0","0","1"],["0","0","0"]]
obs = ["d*n - n*d", "n", "n*n", "d - 1", "d - 2", "d - 3"]
key = {"id": "E1-04", "label": "NEW_KIND", "true_family": "assoc", "true_dim": 6,
  "witness": {"d": D, "n": Nn},
  "observed_nonzero": obs,
  "complete_presentation": True,
  "category": "new kind (assoc, outside the familiar list): upper-triangular 3x3 matrix algebra as a three-level operator d with a one-step lowering transition n",
  "notes": "T = upper-triangular 3x3 matrices, d = diag(1,2,3), n = E12 + E23. In comm (= graded, all grades 0) the ladder law gives n*d = n*(d - 1), so n = 0 (the transition collapses silently; d still has three rational levels). Rational values force n = 0. Laws present T completely (dim 6)."}
errs, info = check_E1(world, key, {"roles": ["n", "n*n", "d - 1", "d - 2", "d - 3"]})
print("E1-04 checks:", "PASS" if not errs else "FAIL")
if errs: print(errs)
else:
    save_world_and_key(world, key); print(update_progress("E1-04 saved; next E1-05"))
