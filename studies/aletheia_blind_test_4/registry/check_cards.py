# Test 4: check the registry draft's meaning cards against laws whose symmetries are known.
#   python check_cards.py
# For each law and each transformation the script computes, from the cards alone, whether the law
# is unchanged, and compares with what physics says. A card with a wrong action shows up as a
# known-symmetric law that comes out broken (the Klein-Gordon error of coverage check 2 would).
# It also prints the derived actions (velocity, acceleration, momentum) for the review table.
# This is a consistency check of the cards, not evidence about the kernel.
import json
import os
import re
import sys

import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lang"))
import reader_v0 as R  # noqa: E402

reg = json.load(open(os.path.join(HERE, "registry.json"), encoding="utf-8"))
MEANINGS = {m["id"]: m for m in reg["meanings"]}
KINDS = {k["id"]: k for k in reg["kinds"]}
DEFS = {d["id"]: d for d in reg["definitions"]}
READS = {t["id"]: t["reads"] for t in reg["transformations"]}
CHECKED = ["rev_t", "refl_x", "conj_c", "rot_z"]   # exch reads the bodies, not the cards


def to_action(v):
    if v == "?":
        return None
    if isinstance(v, list):
        return sp.Matrix([[sp.Rational(e) for e in row] for row in v])
    return sp.Rational(v)


def action(m, t):
    if READS[t] == "kind":
        return to_action(KINDS[MEANINGS[m]["kind"]]["under"][t])
    v = MEANINGS[m]["under"][t]
    if isinstance(v, dict):
        rel = R.Parser(DEFS[v["derived"]]["eq"]).relation({"="})
        assert rel[2] == ("name", m), "definitions here are written 'meaning = expression'"
        return evaluate(rel[3], t)
    return to_action(v)


def evaluate(node, t):
    """Action of an expression built from meanings (multiplicative actions only)."""
    kind = node[0]
    if kind == "num":
        return sp.Integer(1)
    if kind == "name":
        return action(node[1], t)
    if kind == "neg":
        return evaluate(node[1], t)
    if kind == "pow":
        a = evaluate(node[1], t)
        return None if a is None else a ** node[2]
    if kind == "D":
        a, b = action(node[1], t), action(node[2], t)
        return None if a is None or b is None else a / b
    a, b = evaluate(node[2], t), evaluate(node[3], t)
    if a is None or b is None:
        return None
    if node[1] == "*":
        return b * a if isinstance(a, sp.Matrix) else a * b
    if node[1] == "/":
        return a / b
    assert a == b, "a sum of terms that transform differently"
    return a


D_RE = re.compile(r"D\(\s*([a-z][a-z0-9_]*)\s*,\s*([a-z][a-z0-9_]*)\s*\)")


def to_sympy(expr):
    return sp.sympify(D_RE.sub(r"D__\1__\2", expr).replace("^", "**"))


def transform(quantities, equations, t):
    """Return the transformed equations, or None if an action is unknown ('?')."""
    subs = {}
    for name, (m, comps) in quantities.items():
        a = action(m, t)
        if a is None:
            return None
        if comps is None:
            subs[sp.Symbol(name)] = a * sp.Symbol(name)
        else:
            vec = sp.Matrix([sp.Symbol(c) for c in comps])
            img = (a * vec) if isinstance(a, sp.Matrix) else a * vec
            for c, e in zip(comps, img):
                subs[sp.Symbol(c)] = e
    exprs = [to_sympy(lhs) - to_sympy(rhs) for lhs, rhs in (e.split("=") for e in equations)]
    dsubs = {}
    for e in exprs:
        for s in e.free_symbols:
            m = re.fullmatch(r"D__([a-z][a-z0-9_]*)__([a-z][a-z0-9_]*)", s.name)
            if m:
                x, tt = sp.Symbol(m.group(1)), sp.Symbol(m.group(2))
                img_x = subs[x]
                scale_t = sp.simplify(subs[tt] / tt)
                d_img = img_x.xreplace({y: sp.Symbol(f"D__{y.name}__{tt.name}") for y in img_x.free_symbols})
                dsubs[s] = d_img / scale_t
    allsubs = {**subs, **dsubs}
    return exprs, [sp.expand(e.xreplace(allsubs)) for e in exprs]


def invariant(quantities, equations, t):
    out = transform(quantities, equations, t)
    if out is None:
        return None
    exprs, images = out
    exprs = [sp.expand(e) for e in exprs]

    def same_law(img):
        # the same equation up to a nonzero constant factor (a scaling multiplies a whole law by a number)
        for e in exprs:
            ratio = sp.simplify(img / e)
            if ratio != 0 and not ratio.free_symbols:
                return True
        return False
    return all(same_law(img) for img in images)


V = lambda p: [p + "x", p + "y", p + "z"]  # noqa: E731

# (name, quantities {name: (meaning, components or None)}, equations, expected {t: True/False/None})
ALL = {t: True for t in CHECKED}
LAWS = [
    ("Newton's second law", {"m": ("m02", None), "t": ("m01", None), "v": ("m13", V("v")), "f": ("m16", V("f"))},
     ["m*D(vx, t) = fx", "m*D(vy, t) = fy", "m*D(vz, t) = fz"], ALL),
    ("Lorentz force", {"m": ("m02", None), "q": ("m04", None), "t": ("m01", None), "v": ("m13", V("v")),
                       "e": ("m17", V("e")), "b": ("m18", V("b"))},
     ["m*D(vx, t) = q*(ex + vy*bz - vz*by)", "m*D(vy, t) = q*(ey + vz*bx - vx*bz)",
      "m*D(vz, t) = q*(ez + vx*by - vy*bx)"], ALL),
    ("isotropic spring", {"m": ("m02", None), "k": ("m05", None), "t": ("m01", None), "v": ("m13", V("v")),
                          "r": ("m12", V("x"))},
     ["m*D(vx, t) = -k*xx", "m*D(vy, t) = -k*xy", "m*D(vz, t) = -k*xz"], ALL),
    ("damped spring (friction breaks time reversal)",
     {"m": ("m02", None), "k": ("m05", None), "g": ("m06", None), "t": ("m01", None), "v": ("m13", V("v")),
      "r": ("m12", V("x"))},
     ["m*D(vx, t) = -k*xx - g*vx", "m*D(vy, t) = -k*xy - g*vy", "m*D(vz, t) = -k*xz - g*vz"],
     {**ALL, "rev_t": False}),
    ("free fall in a uniform field", {"m": ("m02", None), "t": ("m01", None), "v": ("m13", V("v")),
                                      "g": ("m21", V("g"))},
     ["m*D(vx, t) = m*gx", "m*D(vy, t) = m*gy", "m*D(vz, t) = m*gz"], ALL),
    ("Coulomb energy of two charges", {"u": ("m03", None), "k": ("m07", None), "q1": ("m04", None),
                                       "q2": ("m04", None), "d": ("m11", None)},
     ["u*d = k*q1*q2"], ALL),
    ("energy seen by a moving observer", {"u": ("m03", None), "m": ("m02", None), "p": ("m15", V("p")),
                                          "w": ("m22", V("w"))},
     ["u = (px^2 + py^2 + pz^2)/(2*m) + px*wx + py*wy + pz*wz + m*(wx^2 + wy^2 + wz^2)/2"], ALL),
    ("angular momentum L = r x p", {"l": ("m19", V("l")), "r": ("m12", V("x")), "p": ("m15", V("p"))},
     ["lx = xy*pz - xz*py", "ly = xz*px - xx*pz", "lz = xx*py - xy*px"], ALL),
    ("torque N = r x F", {"n": ("m20", V("n")), "r": ("m12", V("x")), "f": ("m16", V("f"))},
     ["nx = xy*fz - xz*fy", "ny = xz*fx - xx*fz", "nz = xx*fy - xy*fx"], ALL),
    ("rate of angular momentum = torque", {"t": ("m01", None), "l": ("m19", V("l")), "n": ("m20", V("n"))},
     ["D(lx, t) = nx", "D(ly, t) = ny", "D(lz, t) = nz"], ALL),
    ("momentum p = m v", {"p": ("m15", V("p")), "m": ("m02", None), "v": ("m13", V("v"))},
     ["px = m*vx", "py = m*vy", "pz = m*vz"], ALL),
    ("force on a charge F = q E", {"f": ("m16", V("f")), "q": ("m04", None), "e": ("m17", V("e"))},
     ["fx = q*ex", "fy = q*ey", "fz = q*ez"], ALL),
    ("Klein-Gordon charge density", {"rho": ("m08", None), "t": ("m01", None), "phi": ("m23", ["fa", "fb"])},
     ["rho = 2*(fa*D(fb, t) - fb*D(fa, t))"], ALL),
    ("law with the untested-parity coupling", {"u": ("m03", None), "w": ("m09", None), "q1": ("m04", None),
                                               "q2": ("m04", None), "d": ("m11", None)},
     ["u*d = w*q1*q2"], {**ALL, "refl_x": None}),
    ("law with the untested-time field", {"u": ("m03", None), "s": ("m10", None), "k": ("m07", None)},
     ["u = s*k"], {**ALL, "rev_t": None}),
]

if __name__ == "__main__":
    print("Derived actions (from the definitions):")
    for m in ("m13", "m14", "m15"):
        print(f"  {m}: " + ", ".join(f"{t}={action(m, t).tolist() if isinstance(action(m, t), sp.Matrix) else action(m, t)}"
                                    for t in ("rev_t", "refl_x", "conj_c")))
    bad = 0
    print("\nKnown laws (True = unchanged, False = changed, None = unknown because of a '?' card):")
    for name, quantities, equations, expected in LAWS:
        got = {t: invariant(quantities, equations, t) for t in CHECKED}
        ok = got == expected
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} {name}: " + ", ".join(f"{t}={got[t]}" for t in CHECKED)
              + ("" if ok else f"   expected {expected}"))
    print(f"\n{len(LAWS) - bad}/{len(LAWS)} laws behave as physics says")
    sys.exit(1 if bad else 0)
