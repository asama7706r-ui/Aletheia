from wcheck import *
world = {"id": "E1-10", "experiment": "E1",
  "generators": [{"name": "g", "grade": 0}],
  "variables": ["s", "t", "u"],
  "laws": ["g**3 = 1",
           "(1 - g)*(1 + g + g**2) = 0",
           "(1 + g + g**2)**2 = 3*(1 + g + g**2)",
           "(s + t*g + u*g**2)*g = u + s*g + t*g**2"]}
G = [["0","0","1"],["1","0","0"],["0","1","0"]]
key = {"id": "E1-10", "label": "NEW_KIND", "true_family": "comm", "true_dim": 3,
  "witness": {"g": G},
  "observed_nonzero": ["1 - g", "1 + g + g**2"],
  "complete_presentation": True,
  "category": "new kind (comm, outside the familiar list): group algebra of the cyclic group of order 3, Q[g]/(g^3 - 1)",
  "notes": "Law 2 states that the rotation defect 1 - g and the averaging element 1 + g + g^2 are zero divisors; law 4 says g cyclically shifts three slots. The only rational solution g = 1 kills 1 - g. T = Q[C3] (= Q x Q(omega)), witness = 3x3 cyclic permutation matrix (minimal faithful). Laws present T completely (dim 3)."}
errs, info = check_E1(world, key, {"roles": ["1 - g", "1 + g + g**2"]})
print("E1-10 checks:", "PASS" if not errs else "FAIL")
if errs: print(errs)
else:
    save_world_and_key(world, key); print(update_progress("E1-10 saved; next E1-11"))
