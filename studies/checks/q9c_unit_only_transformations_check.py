# Q9c: are transformations computed from UNITS alone informative for the card (F2)?
# Claim: a pure change of units (scale a base unit by lam > 0) is a symmetry of every law
# whose units are consistent, so it can never reveal a change of law beyond what F1 sees.
# The "time-unit sign flip" (lam = -1 for T, i.e. q -> (-1)^(T exponent) q) is the
# dimension-only version of time reversal. We test both on all 16 E2 worlds of blind test 1
# (post hoc; these are the frozen world files, read only).
import json, glob, random
from pathlib import Path
from fractions import Fraction
import sympy as sp

ROOT = Path(__file__).resolve().parent.parent  # the lab folder, or studies/ in the repo
WORLDS = str(ROOT / "aletheia_blind_test_1" / "worlds" / "E2-*.json")
key = {it["id"]: it["label"] for it in json.load(open(
    ROOT / "aletheia_blind_test_1" / "key" / "key.json")) if it["id"].startswith("E2")}

def parse(law, loc):
    lhs, rhs = law.split("=", 1)
    return sp.sympify(lhs, locals=loc), sp.sympify(rhs, locals=loc)

def unit_scaling_ok(law, dims, loc, base):
    lam = sp.Symbol("lam", positive=True)
    L, R = parse(law, loc)
    sub = {loc[q]: lam ** sp.Rational(str(Fraction(str(d.get(base, 0))))) * loc[q] for q, d in dims.items()}
    dl = sp.Rational(str(Fraction(str(dims[str(L)].get(base, 0)))))
    diff = sp.simplify(sp.expand_power_base(R.subs(sub, simultaneous=True) - lam ** dl * R, force=True))
    return diff == 0

def time_sign_flip_ok(law, dims, loc, rng):
    L, R = parse(law, loc)
    ins = sorted(str(s) for s in R.free_symbols)
    sgn = {q: (-1) ** int(Fraction(str(d.get("T", 0)))) for q, d in dims.items()}
    for _ in range(5):
        vals = {q: sp.Rational(rng.randint(1, 10 ** 6), 10 ** 5) for q in ins}
        y = R.subs({loc[q]: v for q, v in vals.items()})
        y_new = sgn[str(L)] * y
        r_new = R.subs({loc[q]: sgn[q] * vals[q] for q in ins})
        if abs(complex(sp.N(y_new - r_new, 30))) > 1e-12:
            return False
    return True

rng = random.Random(7)
print("world  key_label            | unit scaling (all base units): orig/filled | time-unit sign flip: orig/filled -> detects change?")
for f in sorted(glob.glob(WORLDS)):
    w = json.load(open(f))
    dims = w["quantities"]
    loc = {q: sp.Symbol(q, positive=True) for q in dims}
    bases = sorted({b for d in dims.values() for b in d})
    us_o = all(unit_scaling_ok(w["law_original"], dims, loc, b) for b in bases)
    us_f = all(unit_scaling_ok(w["filled_law"], dims, loc, b) for b in bases)
    tf_o = time_sign_flip_ok(w["law_original"], dims, loc, rng)
    tf_f = time_sign_flip_ok(w["filled_law"], dims, loc, rng)
    det = "YES" if (tf_o and not tf_f) else "no"
    print("%-6s %-20s | %-5s / %-5s | %-5s / %-5s -> %s" % (w["id"], key[w["id"]], us_o, us_f, tf_o, tf_f, det))

# Contrast: the magnetic field B is constant in time, yet it is T-odd (its source is moving charge).
t, m, q, B = sp.symbols("t m q B")
X, Y = sp.Function("X"), sp.Function("Y")
def lorentz_T_invariant(flip_B):
    eqs = [m * sp.diff(X(t), t, 2) - q * B * sp.diff(Y(t), t), m * sp.diff(Y(t), t, 2) + q * B * sp.diff(X(t), t)]
    out = []
    for e in eqs:
        r = e.subs({X(t): X(-t), Y(t): Y(-t)}).doit().subs(t, -t)
        if flip_B:
            r = r.subs(B, -B)
        out.append(sp.simplify(r - e) == 0)
    return all(out)
print()
print("charge in uniform B, time reversal with B held fixed  :", lorentz_T_invariant(False))
print("charge in uniform B, time reversal with B reversed too:", lorentz_T_invariant(True))
