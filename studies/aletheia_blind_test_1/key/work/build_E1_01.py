from wcheck import *
world = {"id": "E1-01", "experiment": "E1",
  "generators": [{"name": "u", "grade": 0}, {"name": "v", "grade": 0}, {"name": "w", "grade": 1}],
  "variables": ["t"],
  "laws": ["u*v = 1",
           "(t + w)*(t - w) = t**2 - u",
           "u*w = -w*u",
           "(u + w)**2 = u**2 + u"]}
key = {"id": "E1-01", "label": "CONTRADICTION",
  "category": "contradiction: square root of an invertible element that anticommutes with it",
  "notes": "Derivation: law 2 (coefficient of t**0) gives w*w = u. Then w*u = w**3 = u*w, and law 3 gives u*w = -w*u, so 2*w*u = 0, w*u = 0. With law 1: w = w*(u*v) = (w*u)*v = 0, hence u = w*w = 0 and 1 = u*v = 0. Law 4 is a redundant consequence of laws 2 and 3. Each law alone has a nonzero model."}
errs, info = check_E1(world, key, {"loo_models": {}})
print("E1-01 checks:", "PASS" if not errs else "FAIL")
if errs: print(errs)
else:
    save_world_and_key(world, key); print(update_progress("E1-01 saved; next E1-02"))
