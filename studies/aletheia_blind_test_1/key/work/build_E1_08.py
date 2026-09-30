from wcheck import *
world = {"id": "E1-08", "experiment": "E1",
  "generators": [{"name": "a", "grade": 0}, {"name": "b", "grade": 0}],
  "variables": ["x"],
  "laws": ["a*a = 2*b",
           "b**2 = 2*a",
           "(a - 1)*(b - 1) = 1",
           "a*b*a = b*a*b",
           "(a + b*x)*(b + a*x) = 4*(1 + x)**2"]}
key = {"id": "E1-08", "label": "SUBSUMED",
  "true_values": {"a": "2", "b": "2"},
  "observed_nonzero": ["a", "b", "a - 1", "b - 1", "a*b"],
  "category": "subsumed: two quantities, each half the square of the other, with a braid-type law and a factored (non-zero) product law",
  "notes": "a = b = 2 satisfies all laws with every factor nonzero ((a-1)*(b-1) = 1). Law 5 gives a*b = b*a = 4 and a^2 + b^2 = 8. In the commutative reading the only rational solution is a = b = 2 (the other roots of a^3 = 8 are not rational; a = b = 0 is excluded by law 5)."}
errs, info = check_E1(world, key)
print("E1-08 checks:", "PASS" if not errs else "FAIL")
print("rational solutions found:", info.get("ratpts") if isinstance(info.get("ratpts"), str) else len(info.get("ratpts")))
if errs: print(errs)
else:
    save_world_and_key(world, key); print(update_progress("E1-08 saved; next E1-09"))
