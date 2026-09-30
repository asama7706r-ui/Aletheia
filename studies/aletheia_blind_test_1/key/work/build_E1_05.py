from wcheck import *
from wideal import regular_rep
world = {"id": "E1-05", "experiment": "E1",
  "generators": [{"name": "z", "grade": 0}, {"name": "f1", "grade": 1}, {"name": "f2", "grade": 1}],
  "variables": ["s", "t"],
  "laws": ["(z + s*f1 + t*f2)*(z - s*f1 - t*f2) = z**2",
           "z*z = f1*f2",
           "(1 + z)**3 = 1 + 3*z + 3*f1*f2 + z*f1*f2",
           "f2*z*f1 = -z**3"]}
grades = [0, 1, 1]
rels = relations(world)
mats, normal = regular_rep(3, rels + family_relations(grades, "graded"), 6)
print("regular rep size:", len(normal))
s = lambda M: [[fstr(x) for x in r] for r in M]
wit = {"z": s(mats[0]), "f1": s(mats[1]), "f2": s(mats[2])}
obs = ["f1*f2 - f2*f1", "z", "z*z", "z**3", "f1", "f2", "f1*f2"]
key = {"id": "E1-05", "label": "NEW_KIND", "true_family": "graded", "true_dim": len(normal),
  "witness": wit, "observed_nonzero": obs, "complete_presentation": True,
  "category": "new kind (graded, outside the familiar list): mixed-grade superalgebra with an even z whose square is the fermion pair, z^2 = f1*f2",
  "notes": "T = supercommutative algebra on even z, odd f1, f2 with z^2 = f1*f2 (basis 1, z, z^2, z^3, f1, f2, z*f1, z*f2). Law 1 encodes f1^2 = f2^2 = 0, f1*f2 = -f2*f1 and z central. In comm the anticommutation gives f1*f2 = 0, hence z^2 = 0 (silent collapse of z^2, z^3 and the binomial law). Rational values force f1 = f2 = z = 0. Witness = regular representation (the algebra is local with one-dimensional socle, so no smaller faithful representation exists)."}
errs, info = check_E1(world, key, {"roles": ["z", "z*z", "z**3", "f1", "f2", "f1*f2"]})
print("E1-05 checks:", "PASS" if not errs else "FAIL")
if errs: print(errs)
else:
    save_world_and_key(world, key); print(update_progress("E1-05 saved; next E1-06"))
