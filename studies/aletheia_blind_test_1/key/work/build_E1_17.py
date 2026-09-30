from wcheck import *
world = {"id": "E1-17", "experiment": "E1",
  "generators": [{"name": "x", "grade": 0}],
  "variables": ["t"],
  "laws": ["x**3 = x + 6",
           "(x - 1)*x*(x + 1) = 6",
           "(t - x)*(t**2 + x*t + x**2 - 1) = t**3 - t - 6"]}
key = {"id": "E1-17", "label": "SUBSUMED",
  "true_values": {"x": "2"},
  "observed_nonzero": ["x", "x - 1", "x + 1"],
  "category": "subsumed: root of a cubic that looks like it defines a new number (t^3 - t - 6), but has the rational root 2",
  "notes": "x^3 - x - 6 = (x - 2)*(x^2 + 2x + 3); the quadratic factor has no rational root, so x = 2 is the unique rational solution, and the factors x - 1, x, x + 1 of law 2 are 1, 2, 3 there. Law 3 is the factor theorem for t^3 - t - 6."}
errs, info = check_E1(world, key)
print("E1-17 checks:", "PASS" if not errs else "FAIL")
if errs: print(errs)
else:
    save_world_and_key(world, key); print(update_progress("E1-17 saved; next E1-18"))
