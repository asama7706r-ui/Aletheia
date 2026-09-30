from wcheck import *
world = {"id": "E1-13", "experiment": "E1",
  "generators": [{"name": "a", "grade": 0}, {"name": "b", "grade": 0}],
  "variables": ["t", "x", "y"],
  "laws": ["(a*x + b*y)**2 = 4*x**2 - 4*x*y + y**2",
           "(t + a*x)*(t + b*x) = t**2 + t*x - 2*x**2",
           "(t + b*x)*(t + a*x) = (t + a*x)*(t + b*x)"]}
key = {"id": "E1-13", "label": "SUBSUMED",
  "true_values": {"a": "2", "b": "-1"},
  "observed_nonzero": ["a", "b", "a - b", "a*b"],
  "category": "subsumed: Clifford-looking square law with a nonzero cross term, plus a factorization of a quadratic form",
  "notes": "Law 1 gives a^2 = 4, b^2 = 1, a*b + b*a = -4; law 2 gives a + b = 1 and a*b = -2; law 3 gives a*b = b*a. The unique rational solution is a = 2, b = -1 (so t^2 + t*x - 2*x^2 = (t + 2x)(t - x)); nothing that the laws use vanishes there."}
errs, info = check_E1(world, key)
print("E1-13 checks:", "PASS" if not errs else "FAIL")
if errs: print(errs)
else:
    save_world_and_key(world, key); print(update_progress("E1-13 saved; next E1-14"))
