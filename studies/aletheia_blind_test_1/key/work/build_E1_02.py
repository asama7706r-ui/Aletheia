from wcheck import *
world = {"id": "E1-02", "experiment": "E1",
  "generators": [{"name": "h", "grade": 1}, {"name": "k", "grade": 1}],
  "variables": ["s", "t"],
  "laws": ["h*h = 0",
           "(s + h)*(t + k) = (t + k)*(s + h)",
           "(h + k)**2 = 2*h*k",
           "(s + h)**2*(t + k)**2 = s**2*t**2 + 2*s*t**2*h + 2*s**2*t*k + 4*s*t*h*k"]}
# regular representation on basis (1, h, k, hk)
H = [["0","0","0","0"],["1","0","0","0"],["0","0","0","0"],["0","0","1","0"]]
K = [["0","0","0","0"],["0","0","0","0"],["1","0","0","0"],["0","1","0","0"]]
key = {"id": "E1-02", "label": "NEW_KIND", "true_family": "comm", "true_dim": 4,
  "witness": {"h": H, "k": K},
  "observed_nonzero": ["h", "k", "h*k"],
  "complete_presentation": True,
  "category": "new kind (comm, outside the familiar list): two commuting nilpotent increments declared with odd grade, Q[h,k]/(h^2,k^2)",
  "notes": "Law 4 (mixed second difference) uses h, k and h*k. Rational values force h = k = 0. The graded family would add h*k = -k*h, which with law 2 gives h*k = 0 (silent collapse of the mixed term), so comm is both the most restrictive family and the only one keeping h*k. Laws present T completely in comm (dim 4)."}
errs, info = check_E1(world, key, {"roles": ["h", "k", "h*k"]})
print("E1-02 checks:", "PASS" if not errs else "FAIL")
if errs: print(errs)
else:
    save_world_and_key(world, key); print(update_progress("E1-02 saved; next E1-03"))
