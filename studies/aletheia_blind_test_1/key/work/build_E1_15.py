from wcheck import *
world = {"id": "E1-15", "experiment": "E1",
  "generators": [{"name": "x", "grade": 0}, {"name": "y", "grade": 0}],
  "variables": ["s", "t"],
  "parameters": ["c"],
  "laws": ["(s*x + t*y)**2 = s**2 + 2*c*s*t + t**2",
           "(x*y)**3 = 1",
           "x*y*x = y*x*y"]}
und = {}
for c in PARAM_GRID:
    if c == 1: und[fstr(c)] = {"decision": "SUBSUMED", "point": {"x": "1", "y": "1"}}
    else: und[fstr(c)] = {"decision": "CONTRADICTION"}
key = {"id": "E1-15", "label": "UNDERDETERMINED",
  "category": "underdetermined: two mirrors (involutions) with angle cosine c whose rotation x*y is claimed to have order 3",
  "notes": "Law 1 gives x^2 = y^2 = 1 and x*y + y*x = 2c. With r = x*y (inverse y*x): r^2 - 2c*r + 1 = 0 and r^3 = 1 (law 2; law 3 is the equivalent braid form). c = 1: gcd is r - 1, so x*y = 1, y = x, x^2 = 1: SUBSUMED (x = y = 1 or x = y = -1). c in {-3,-2,-1,0,2,3,1/2}: gcd(r^2 - 2c*r + 1, r^3 - 1) = 1, so 1 = 0: CONTRADICTION. (Off the grid, c = -1/2 gives M2(Q), the standard representation of S3.)"}
errs, info = check_E1(world, key, {"roles": ["x", "y"], "und": und})
print("E1-15 checks:", "PASS" if not errs else "FAIL")
if errs: print(errs)
else:
    save_world_and_key(world, key); print(update_progress("E1-15 saved; next E1-16"))
