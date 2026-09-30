# E2 designs keyed by private slot. Each returns (world, key, extra) without id.
FORCE = {"M": 1, "L": 1, "T": -2}


def pt(inp, out):
    return {"inputs": {k: str(v) for k, v in inp.items()}, "output": str(out), "tol": "1e-9"}


def W(q, lo, lf, syms, val, dfc, so, sf, ranges=None):
    w = {"experiment": "E2", "quantities": q, "law_original": lo, "filled_law": lf, "symmetries": syms}
    if ranges:
        w["ranges"] = ranges
    w.update({"validated": val, "deficit": dfc, "state_original": so, "state_filled": sf})
    return w


def K(label, det, notes):
    return {"label": label, "detectable_by_card": det, "notes": notes}


def SAME_1():
    w = W({"F": FORCE, "k": {"M": 1, "T": -2}, "x": {"L": 1}, "c2": {"M": -1, "T": 2}},
          "F = k*x", "F = k*x/(1 + k*c2)",
          [{"name": "reflection", "map": {"x": "-x", "F": "-F"}, "params": {}},
           {"name": "linear scaling", "map": {"x": "l*x", "F": "l*F"}, "params": {"l": ["1/2", "2"]}}],
          [pt({"k": 2, "x": 1, "c2": 0}, 2), pt({"k": 3, "x": "1/2", "c2": 0}, "3/2"), pt({"k": "1/2", "x": 3, "c2": 0}, "3/2")],
          pt({"k": 2, "x": 1, "c2": "1/2"}, 1), ["spring"], ["spring", "second spring in series"])
    k = K("SAME_LAW_NEW_STATE", True, "Hooke's law for the combined system: a second spring of compliance c2 in series gives effective stiffness k/(1 + k*c2); c2 = 0 at every validated point. Reflection, linear scaling and stiffness scaling (k -> l*k, F -> l*F, c2 -> c2/l) are all kept.")
    return w, k, {"natural_keep": [{"name": "stiffness scaling", "map": {"k": "l*k", "F": "l*F", "c2": "c2/l"}, "params": {"l": ["1/2", "2"]}}]}


def SAME_2():
    w = W({"a": {"L": 1, "T": -2}, "F": FORCE, "m": {"M": 1}, "m2": {"M": 1}},
          "a = F/m", "a = F/(m + m2)",
          [{"name": "force reversal", "map": {"F": "-F", "a": "-a"}, "params": {}},
           {"name": "force scaling", "map": {"F": "l*F", "a": "l*a"}, "params": {"l": ["1/2", "3"]}}],
          [pt({"F": 2, "m": 1, "m2": 0}, 2), pt({"F": 3, "m": 2, "m2": 0}, "3/2"), pt({"F": "1/2", "m": "1/2", "m2": 0}, 1)],
          pt({"F": 3, "m": 1, "m2": 2}, 1), ["cart"], ["cart", "load"])
    k = K("SAME_LAW_NEW_STATE", True, "Newton's second law for the cart plus a rigidly attached load m2 (absent, m2 = 0, at the validated points). Force reversal, force scaling and mass scaling (m, m2 -> l*m, l*m2, a -> a/l) are kept.")
    return w, k, {"natural_keep": [{"name": "mass scaling", "map": {"m": "l*m", "m2": "l*m2", "a": "a/l"}, "params": {"l": ["1/2", "2"]}}]}


def SAME_3():
    w = W({"J": {"M": 1, "L": 2}, "m": {"M": 1}, "r": {"L": 1}, "m2": {"M": 1}, "r2": {"L": 1}},
          "J = m*r**2", "J = m*r**2 + m2*r2**2",
          [{"name": "mirror", "map": {"r": "-r"}, "params": {}},
           {"name": "mass-radius trade", "map": {"m": "l**2*m", "r": "r/l"}, "params": {"l": ["1/2", "2"]}}],
          [pt({"m": 2, "r": 1, "m2": 0, "r2": 1}, 2), pt({"m": 1, "r": 3, "m2": 0, "r2": 2}, 9), pt({"m": "1/2", "r": 2, "m2": 0, "r2": "1/2"}, 2)],
          pt({"m": 1, "r": 1, "m2": 2, "r2": 1}, 3), ["rotor"], ["rotor", "added point mass"])
    k = K("SAME_LAW_NEW_STATE", True, "Moment of inertia is additive: a second point mass m2 at radius r2 adds m2*r2^2 (m2 = 0 at the validated points). Mirror and mass-radius trade are kept, as is mirroring r2.")
    return w, k, {"natural_keep": [{"name": "mirror both", "map": {"r": "-r", "r2": "-r2"}, "params": {}}]}


def SAME_4():
    w = W({"phi": {"L": 2, "T": -2}, "G": {"M": -1, "L": 3, "T": -2}, "Ma": {"M": 1}, "r": {"L": 1}, "Mb": {"M": 1}, "rb": {"L": 1}},
          "phi = -G*Ma/r", "phi = -G*Ma/r - G*Mb/rb",
          [{"name": "coupling scaling", "map": {"G": "l*G", "phi": "l*phi"}, "params": {"l": ["1/2", "2"]}},
           {"name": "mass-distance scaling", "map": {"Ma": "l*Ma", "r": "l*r"}, "params": {"l": ["1/2", "2"]}}],
          [pt({"G": 1, "Ma": 2, "r": 1, "Mb": 0, "rb": 1}, -2), pt({"G": 2, "Ma": 1, "r": 2, "Mb": 0, "rb": 3}, -1),
           pt({"G": "1/2", "Ma": 3, "r": "3/2", "Mb": 0, "rb": 2}, -1)],
          pt({"G": 1, "Ma": 2, "r": 1, "Mb": 1, "rb": 2}, "-5/2"), ["planet"], ["planet", "moon"])
    k = K("SAME_LAW_NEW_STATE", True, "Superposition of Newtonian potentials: a second source Mb at distance rb adds -G*Mb/rb (Mb = 0 at the validated points). Both listed symmetries are kept; mass scaling of both sources is kept too.")
    return w, k, {"natural_keep": [{"name": "all masses scaled", "map": {"Ma": "l*Ma", "Mb": "l*Mb", "phi": "l*phi"}, "params": {"l": ["1/2", "2"]}}]}


def SAME_5():
    w = W({"Fb": FORCE, "rho": {"M": 1, "L": -3}, "g": {"L": 1, "T": -2}, "V": {"L": 3}, "V2": {"L": 3}},
          "Fb = rho*g*V", "Fb = rho*g*(V + V2)",
          [{"name": "gravity scaling", "map": {"g": "l*g", "Fb": "l*Fb"}, "params": {"l": ["1/2", "2"]}},
           {"name": "density scaling", "map": {"rho": "l*rho", "Fb": "l*Fb"}, "params": {"l": ["1/2", "2"]}}],
          [pt({"rho": 1, "g": 2, "V": 3, "V2": 0}, 6), pt({"rho": 2, "g": 1, "V": "1/2", "V2": 0}, 1), pt({"rho": "3/2", "g": 2, "V": 1, "V2": 0}, 3)],
          pt({"rho": 1, "g": 2, "V": 1, "V2": "1/2"}, 3), ["immersed hull"], ["immersed hull", "attached float"])
    k = K("SAME_LAW_NEW_STATE", True, "Archimedes' law applied to the hull plus an attached float of volume V2 (V2 = 0 at the validated points); the buoyant force is still rho*g times the total displaced volume. Listed symmetries and volume scaling of both bodies are kept.")
    return w, k, {"natural_keep": [{"name": "volume scaling", "map": {"V": "l*V", "V2": "l*V2", "Fb": "l*Fb"}, "params": {"l": ["1/2", "2"]}}]}


def SAME_6():
    w = W({"F": FORCE, "m": {"M": 1}, "v": {"L": 1, "T": -1}, "r": {"L": 1}, "m2": {"M": 1}},
          "F = m*v**2/r", "F = (m + m2)*v**2/r",
          [{"name": "time reversal", "map": {"v": "-v"}, "params": {}},
           {"name": "speed-radius scaling", "map": {"v": "l*v", "r": "l**2*r"}, "params": {"l": ["1/2", "2"]}}],
          [pt({"m": 1, "v": 2, "r": 1, "m2": 0}, 4), pt({"m": 2, "v": 1, "r": 2, "m2": 0}, 1), pt({"m": 3, "v": 3, "r": 3, "m2": 0}, 9)],
          pt({"m": 1, "v": 2, "r": 1, "m2": 1}, 8), ["car on a curve"], ["car on a curve", "passenger"])
    k = K("SAME_LAW_NEW_STATE", True, "Centripetal force for the car plus a passenger of mass m2 moving with it (m2 = 0 at the validated points); same law for the enlarged body. Time reversal and speed-radius scaling are kept.")
    return w, k, {"natural_keep": [{"name": "mass scaling", "map": {"m": "l*m", "m2": "l*m2", "F": "l*F"}, "params": {"l": ["1/2", "2"]}}]}


def ANO_D1():
    w = W({"F": FORCE, "G": {"M": -1, "L": 3, "T": -2}, "m1": {"M": 1}, "m2": {"M": 1}, "r": {"L": 1}, "d": {}},
          "F = G*m1*m2/r**2", "F = G*m1*m2/r**2 + d*G*m1*m2*(m1 - m2)/((m1 + m2)*r**2)",
          [{"name": "exchange of the two bodies", "map": {"m1": "m2", "m2": "m1"}, "params": {}},
           {"name": "distance scaling", "map": {"r": "l*r", "F": "F/l**2"}, "params": {"l": ["1/2", "2"]}}],
          [pt({"G": 1, "m1": 2, "m2": 3, "r": 1, "d": 0}, 6), pt({"G": 2, "m1": 1, "m2": 1, "r": 2, "d": 0}, "1/2"),
           pt({"G": 1, "m1": 3, "m2": "1/2", "r": "3/2", "d": 0}, "2/3")],
          pt({"G": 1, "m1": 3, "m2": 1, "r": 1, "d": "1/2"}, "15/4"), ["body 1", "body 2"], ["body 1", "body 2", "composition charge"])
    k = K("ANOTHER_LAW", True, "The added term is odd under exchange of the two bodies (composition-dependent force, violating action = reaction): it breaks the listed exchange symmetry, so the filled law is a different law.")
    return w, k, {}


def ANO_D2():
    w = W({"p": {"M": 1, "L": 1, "T": -1}, "m": {"M": 1}, "v": {"L": 1, "T": -1}, "cl": {"L": 1, "T": -1}},
          "p = m*v", "p = m*v/sqrt(1 - v**2/cl**2)",
          [{"name": "Galilean boost", "map": {"v": "v + w", "p": "p + m*w"}, "params": {"w": ["-1", "1"]}},
           {"name": "mass scaling", "map": {"m": "l*m", "p": "l*p"}, "params": {"l": ["1/2", "2"]}}],
          [pt({"m": 1, "v": 2, "cl": 1000000}, 2), pt({"m": 2, "v": 3, "cl": 1000000}, 6), pt({"m": "1/2", "v": 1, "cl": 1000000}, "1/2")],
          pt({"m": 1, "v": 3, "cl": 5}, "15/4"), ["particle"], ["particle", "limiting speed"],
          ranges={"cl": ["10", "20"]})
    k = K("ANOTHER_LAW", True, "Relativistic momentum is a different regime: it fits the validated points (cl huge there) but breaks the listed Galilean boost symmetry.")
    return w, k, {}


def ANO_D3():
    w = W({"P": {"M": 1, "L": -1, "T": -2}, "n": {}, "kT": {"M": 1, "L": 2, "T": -2}, "V": {"L": 3},
           "a0": {"M": 1, "L": 5, "T": -2}, "b0": {"L": 3}},
          "P = n*kT/V", "P = n*kT/(V - n*b0) - a0*n**2/V**2",
          [{"name": "temperature scaling", "map": {"kT": "l*kT", "P": "l*P"}, "params": {"l": ["1/2", "2"]}},
           {"name": "extensivity", "map": {"n": "l*n", "V": "l*V"}, "params": {"l": ["1/2", "2"]}}],
          [pt({"n": 1, "kT": 2, "V": 1, "a0": "1/10", "b0": "1/20"}, 2), pt({"n": 2, "kT": 1, "V": 2, "a0": "1/10", "b0": "1/20"}, 1),
           pt({"n": 3, "kT": "1/2", "V": "3/2", "a0": "1/10", "b0": "1/20"}, 1)],
          pt({"n": 2, "kT": 1, "V": 1, "a0": "1/10", "b0": "1/20"}, "82/45"), ["gas"], ["gas", "molecular size", "molecular attraction"])
    k = K("ANOTHER_LAW", True, "Van der Waals law with the gas's own a0, b0 (nonzero at the validated points): it contradicts the validated ideal-gas data and breaks temperature scaling, so it is a different law, not a new object.")
    return w, k, {}


def ANO_D4():
    w = W({"v": {"L": 1, "T": -1}, "g": {"L": 1, "T": -2}, "d": {"L": 1}, "s": {"M": 1, "T": -2}, "kw": {"L": -1}, "rho": {"M": 1, "L": -3}},
          "v = sqrt(g*d)", "v = sqrt(g*d + s*kw/rho)",
          [{"name": "depth scaling", "map": {"d": "l*d", "v": "sqrt(l)*v"}, "params": {"l": ["1/2", "2"]}},
           {"name": "gravity scaling", "map": {"g": "l*g", "v": "sqrt(l)*v"}, "params": {"l": ["1/2", "2"]}}],
          [pt({"g": 2, "d": 2, "s": 0, "kw": 1, "rho": 1}, 2), pt({"g": 1, "d": "1/4", "s": 0, "kw": 2, "rho": 1}, "1/2"),
           pt({"g": 3, "d": 3, "s": 0, "kw": "1/2", "rho": 2}, 3)],
          pt({"g": 2, "d": 2, "s": 5, "kw": 1, "rho": 1}, 3), ["water layer"], ["water layer", "surface film"])
    k = K("ANOTHER_LAW", True, "Capillary-gravity wave speed is a different regime: the surface-tension term breaks the listed depth and gravity scalings of shallow-water waves.")
    return w, k, {}


def ANO_D5():
    w = W({"a": {"L": 1, "T": -2}, "g": {"L": 1, "T": -2}, "sn": {}},
          "a = g*sn", "a = 5*g*sn/7",
          [{"name": "gravity scaling", "map": {"g": "l*g", "a": "l*a"}, "params": {"l": ["1/2", "2"]}},
           {"name": "incline reversal", "map": {"sn": "-sn", "a": "-a"}, "params": {}}],
          [pt({"g": 2, "sn": "1/2"}, 1), pt({"g": 3, "sn": "1/3"}, 1), pt({"g": 1, "sn": 1}, 1)],
          pt({"g": 7, "sn": 1}, 5), ["sliding block", "frictionless incline"], ["rolling ball", "incline with friction"])
    k = K("ANOTHER_LAW", True, "A different system (a rolling solid ball instead of a sliding block): the filled law contradicts the validated data (factor 5/7) and the state replaces the original objects.")
    return w, k, {}


def ANO_U1():
    w = W({"Fd": FORCE, "b": {"M": 1, "T": -1}, "v": {"L": 1, "T": -1}, "v0": {"L": 1, "T": -1}},
          "Fd = b*v", "Fd = b*v**3/v0**2",
          [{"name": "reversal", "map": {"v": "-v", "Fd": "-Fd"}, "params": {}},
           {"name": "coefficient scaling", "map": {"b": "l*b", "Fd": "l*Fd"}, "params": {"l": ["1/2", "2"]}}],
          [pt({"b": 2, "v": 1, "v0": 1}, 2), pt({"b": "1/2", "v": 1, "v0": 1}, "1/2"), pt({"b": 3, "v": -1, "v0": 1}, -3)],
          pt({"b": 1, "v": 2, "v0": 1}, 8), ["sphere in fluid"], ["sphere in fluid", "turbulent wake"])
    k = K("ANOTHER_LAW", False, "A different drag regime (cubic instead of linear in v). Every validated point was taken at |v| = v0, where the two laws agree, and the listed symmetries (reversal, coefficient scaling) are kept, so the card cannot see it; the hidden difference is the broken linearity v -> l*v, Fd -> l*Fd.")
    return w, k, {"hidden_break": [{"name": "linear scaling", "map": {"v": "l*v", "Fd": "l*Fd"}, "params": {"l": ["1/2", "2"]}}]}


def ANO_U2():
    w = W({"a": {"L": 1, "T": -2}, "w2": {"T": -2}, "x": {"L": 1}, "gam": {"T": -1}, "v": {"L": 1, "T": -1}},
          "a = -w2*x", "a = -w2*x - gam*v",
          [{"name": "stiffness-amplitude trade", "map": {"w2": "l*w2", "x": "x/l"}, "params": {"l": ["1/2", "2"]}},
           {"name": "sign flip of stiffness and displacement", "map": {"w2": "-w2", "x": "-x"}, "params": {}}],
          [pt({"w2": 4, "x": "1/2", "gam": 0, "v": 1}, -2), pt({"w2": 1, "x": 3, "gam": 0, "v": 2}, -3), pt({"w2": 9, "x": "1/3", "gam": 0, "v": -1}, -3)],
          pt({"w2": 4, "x": "1/2", "gam": 1, "v": 2}, -4), ["mass", "spring"], ["mass", "spring", "dashpot"])
    k = K("ANOTHER_LAW", False, "Damping turns the conservative oscillator law into a dissipative one: time reversal (v -> -v, a and x unchanged) is a symmetry of the original law but not of the filled law. That symmetry is not listed, gam = 0 at the validated points and the listed symmetries are kept, so the card cannot see the change.")
    return w, k, {"hidden_break": [{"name": "time reversal", "map": {"v": "-v"}, "params": {}}]}


def INV_1():
    w = W({"Fd": FORCE, "cd": {}, "rho": {"M": 1, "L": -3}, "A": {"L": 2}, "v": {"L": 1, "T": -1}, "mu": {"M": 1, "L": -1, "T": -1}},
          "Fd = cd*rho*A*v**2/2", "Fd = cd*rho*A*v**2/2 + 3*mu*v",
          [{"name": "density scaling", "map": {"rho": "l*rho", "Fd": "l*Fd"}, "params": {"l": ["1/2", "2"]}}],
          [pt({"cd": 1, "rho": 2, "A": 1, "v": 1, "mu": 0}, 1), pt({"cd": "1/2", "rho": 1, "A": 2, "v": 2, "mu": 0}, 2),
           pt({"cd": 2, "rho": 1, "A": "1/2", "v": 3, "mu": 0}, "9/2")],
          pt({"cd": 1, "rho": 2, "A": 1, "v": 1, "mu": "1/3"}, 2), ["sphere", "air"], ["sphere", "air", "viscous boundary layer"])
    k = K("INVALID", True, "The viscous term 3*mu*v has dimension M T^-2, not a force (a length, the diameter, is missing): the filled law is dimensionally inconsistent.")
    return w, k, {}


def INV_2():
    w = W({"t": {"T": 1}, "h": {"L": 1}, "g": {"L": 1, "T": -2}, "h0": {"L": 1}},
          "t = sqrt(2*h/g)", "t = sqrt(2*h/g + h0)",
          [{"name": "joint scaling", "map": {"h": "l*h", "g": "l*g"}, "params": {"l": ["1/2", "2"]}}],
          [pt({"h": 1, "g": 2, "h0": 0}, 1), pt({"h": 2, "g": 1, "h0": 0}, 2), pt({"h": "9/2", "g": 1, "h0": 0}, 3)],
          pt({"h": 1, "g": 2, "h0": 3}, 2), ["dropped ball"], ["dropped ball", "launch platform"])
    k = K("INVALID", True, "Inside the square root a length h0 is added to 2*h/g, which has dimension T^2: dimensionally inconsistent.")
    return w, k, {}


def INV_3():
    w = W({"w": {"T": -1}, "G": {"M": -1, "L": 3, "T": -2}, "Mc": {"M": 1}, "a": {"L": 1}, "m": {"M": 1}},
          "w = sqrt(G*Mc/a**3)", "w = sqrt(G*(Mc + m)/a**2)",
          [{"name": "mass scaling", "map": {"Mc": "l**2*Mc", "w": "l*w"}, "params": {"l": ["1/2", "2"]}}],
          [pt({"G": 1, "Mc": 1, "a": 1, "m": 0}, 1), pt({"G": 1, "Mc": 8, "a": 2, "m": 0}, 1), pt({"G": 2, "Mc": 2, "a": 1, "m": 0}, 2)],
          pt({"G": 1, "Mc": 3, "a": 1, "m": 1}, 2), ["planet", "star"], ["planet", "star", "companion"])
    k = K("INVALID", True, "Adding the companion mass is fine, but the power of a changed from 3 to 2: G*(Mc + m)/a^2 has dimension L T^-2, so its square root is not a frequency. Dimensionally inconsistent (hidden by a = 1 at the deficit point).")
    return w, k, {}


DESIGNS = {"SAME-1": SAME_1, "SAME-2": SAME_2, "SAME-3": SAME_3, "SAME-4": SAME_4, "SAME-5": SAME_5, "SAME-6": SAME_6,
           "ANO-D1": ANO_D1, "ANO-D2": ANO_D2, "ANO-D3": ANO_D3, "ANO-D4": ANO_D4, "ANO-D5": ANO_D5,
           "ANO-U1": ANO_U1, "ANO-U2": ANO_U2, "INV-1": INV_1, "INV-2": INV_2, "INV-3": INV_3}
