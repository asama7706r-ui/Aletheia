from wcheck import *
from wideal import regular_rep
from wsocle import socle_dim
world = {"id": "E1-14", "experiment": "E1",
  "generators": [{"name": "dx", "grade": 1}, {"name": "dy", "grade": 1}, {"name": "dz", "grade": 1}],
  "variables": ["s", "t", "u"],
  "laws": ["(s*dx + t*dy + u*dz)**2 = 0",
           "(dx + s*dy)*(dy + s*dz)*(dz + s*dx) = (1 + s**3)*dx*dy*dz",
           "dz*dx*dy = dx*dy*dz",
           "(dx + dy + dz)*(dx - dy)*(dy - dz) = 3*dx*dy*dz"]}
grades = [1, 1, 1]
mats, normal = regular_rep(3, relations(world) + family_relations(grades, "graded"), 5)
print("regular rep size:", len(normal), "socle dim:", socle_dim(mats))
sf = lambda M: [[fstr(x) for x in r] for r in M]
obs = ["dx*dy - dy*dx", "dx*dy*dz", "dx*dy", "dy*dz", "dx", "dy", "dz"]
key = {"id": "E1-14", "label": "NEW_KIND", "true_family": "graded", "true_dim": len(normal),
  "witness": {"dx": sf(mats[0]), "dy": sf(mats[1]), "dz": sf(mats[2])},
  "observed_nonzero": obs, "complete_presentation": True,
  "category": "new kind (graded, outside the familiar list): 3-generator exterior (Grassmann) algebra of differential forms with volume/determinant laws",
  "notes": "T = exterior algebra on dx, dy, dz (dim 8). Law 1 gives dx^2 = dy^2 = dz^2 = 0 and pairwise anticommutation; laws 2 and 4 compute oriented volumes. In comm the anticommutation gives dx*dy = 0 etc., so the volume dx*dy*dz collapses and the volume laws become 0 = 0 (silent collapse). Rational values force all generators to 0. Witness = regular representation (one-dimensional socle, so minimal)."}
errs, info = check_E1(world, key, {"roles": ["dx*dy*dz", "dx*dy", "dy*dz", "dx", "dy", "dz"]})
print("E1-14 checks:", "PASS" if not errs else "FAIL")
if errs: print(errs)
else:
    save_world_and_key(world, key); print(update_progress("E1-14 saved; next E1-15"))
