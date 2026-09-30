from wcheck import *
world = {"id": "E1-06", "experiment": "E1",
  "generators": [{"name": "x", "grade": 0}, {"name": "p", "grade": 0}],
  "variables": ["s"],
  "laws": ["p*x - x*p = 1",
           "p*x**2 - x**2*p = 2*x",
           "(x + s)**3 = s**3 + 3*s**2*x + 3*s*x**2",
           "(p + x)**2 = p**2 + 2*x*p + x**2 + 1"]}
key = {"id": "E1-06", "label": "CONTRADICTION",
  "category": "contradiction: canonical commutation relation p*x - x*p = 1 combined with a nilpotent x (x^3 = 0)",
  "notes": "Derivation: law 3 (coefficient of s**0) gives x^3 = 0. From law 1, p*x^n - x^n*p = n*x^(n-1); with n = 3 this gives 0 = 3*x^2, so x^2 = 0; with n = 2 (law 2) 0 = 2*x, so x = 0; then law 1 gives 0 = 1 (characteristic 0). Laws 2 and 4 are consequences of law 1. Law 1 alone (and law 4 alone) is consistent: its leading word has no self-overlap, so it is a Groebner basis of the Weyl algebra; laws 2 and 3 alone have the model x = 0."}
extra = {"single_models": {0: "GB", 3: "GB"}}
errs, info = check_E1(world, key, extra)
print("E1-06 checks:", "PASS" if not errs else "FAIL")
if errs: print(errs)
else:
    save_world_and_key(world, key); print(update_progress("E1-06 saved; next E1-07"))
