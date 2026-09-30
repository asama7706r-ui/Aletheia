from wcheck import *
world = {"id": "E1-11", "experiment": "E1",
  "generators": [{"name": "r", "grade": 0}, {"name": "q", "grade": 0}],
  "variables": ["x", "y", "z"],
  "laws": ["r*r = q",
           "r*q = 2",
           "(r - 1)*(q + r + 1) = 1",
           "(x + y*r + z*q)*(x**2 - 2*y*z + (2*z**2 - x*y)*r + (y**2 - x*z)*q) = x**3 + 2*y**3 + 4*z**3 - 6*x*y*z"]}
R = mat([["0","0","2"],["1","0","0"],["0","1","0"]])
Qm = mmul(R, R)
s = lambda M: [[fstr(v) for v in row] for row in M]
key = {"id": "E1-11", "label": "NEW_KIND", "true_family": "comm", "true_dim": 3,
  "witness": {"r": s(R), "q": s(Qm)},
  "observed_nonzero": ["r", "q", "r - 1"],
  "complete_presentation": True,
  "category": "new kind (comm, outside the familiar list): cubic number field Q(2^(1/3)) as edge r and face area q of a cube of volume 2",
  "notes": "Laws 1-2 give r^3 = 2 (Delian cube duplication); law 3 is the factored difference of cubes; law 4 is the norm form (element times its adjugate = norm), i.e. every nonzero element is invertible. No rational value of r satisfies r^3 = 2. T = Q(2^(1/3)), witness = companion matrix of x^3 - 2 and its square. Laws present T completely (dim 3)."}
errs, info = check_E1(world, key, {"roles": ["r", "q"]})
print("E1-11 checks:", "PASS" if not errs else "FAIL")
if errs: print(errs)
else:
    save_world_and_key(world, key); print(update_progress("E1-11 saved; next E1-12"))
