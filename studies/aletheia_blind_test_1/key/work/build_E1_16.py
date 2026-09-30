from wcheck import *
world = {"id": "E1-16", "experiment": "E1",
  "generators": [{"name": "x", "grade": 0}, {"name": "y", "grade": 0}],
  "laws": ["y = 2*x**2 - 1",
           "4*x**3 - 3*x = -1",
           "2*x*y = x - 1",
           "2*y**2 - 1 = y"]}
key = {"id": "E1-16", "label": "SUBSUMED",
  "true_values": {"x": "1/2", "y": "-1/2"},
  "observed_nonzero": ["x", "y", "x - y"],
  "category": "subsumed: cosines of an angle and of its double (Chebyshev double/triple-angle laws) that look like they need an irrational rotation",
  "notes": "x = cos(60 deg) = 1/2, y = cos(120 deg) = -1/2. y is a polynomial in x, and the laws reduce to (x + 1)*(2x - 1) = 0 (law 4 removes the double root of law 2), so every solution is rational: (1/2, -1/2) (intended) and (-1, 1); both keep x, y nonzero."}
errs, info = check_E1(world, key)
print("E1-16 checks:", "PASS" if not errs else "FAIL")
if errs: print(errs)
else:
    save_world_and_key(world, key); print(update_progress("E1-16 saved; next E1-17"))
