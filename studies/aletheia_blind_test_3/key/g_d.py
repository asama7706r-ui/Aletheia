from build_worlds import *

def group():
    return Group(
        "ostr",
        {"ostr": dims(J=1), "xel": dims(L=1), "yor": dims(L=1), "zun": {}},
        {"cj": {"value": "9/14", "dims": dims(J=1, L=-2)}, "cl": {"value": "6", "dims": dims(L=1)}},
        {"tavo": "1/25", "sunda": "2/5"},
        "ostr = cj*(xel**2 + yor**2)",
        None,
        [cand(1, "qova", "cj*xel*yor"),
         cand(2, "bry", "cj*(xel**2 - yor**2)"),
         cand(3, "nim", "cj*(xel**2 + yor**2)**2/cl**2"),
         cand(4, "terk", "cj*cl**2*zun**2", cov=dimmer("zun", "r/(1 + r)"))],
        [{"name": "swp", "map": {"xel": "1*yor", "yor": "1*xel"}},
         {"name": "flp", "map": {"xel": "-1*xel"}}])

def st(t):
    return {"xel": t[0], "yor": t[1], "zun": t[2]}

OLD_MODEL = {}
OLD = [((F(1, 2), 2, F(1, 9)), F(1, 2)), ((-1, F(3, 2), F(1, 5)), F(-3, 5)), ((F(5, 2), F(-1, 2), F(1, 7)), F(1, 4)),
       ((F(3, 2), 1, F(1, 4)), F(-1, 3)), ((-2, -1, F(1, 12)), F(2, 3))]

def build():
    g = group()
    g.d['old_observations'] = [reading(g.d, st(s), OLD_MODEL, "tavo", o, 100) for s, o in OLD]
    return g

M_D1 = {'expr': [("cj*xel**2*yor**2/cl**2", F(9, 100))]}
M_D2 = {'cands': {'R4': F(3, 50)}}
M_D3 = {'cands': {'R3': F(3, 100)}}

def worlds():
    g = build()
    out = []
    # D1: NEW; R1 fits numerically but the reflection flp forbids it (SYMMETRY alone)
    new1 = [reading(g.d, st((3, 4, F(1,3))), M_D1, "tavo", F(1,2), 200), reading(g.d, st((F(12,5), 5, F(2,7))), M_D1, "tavo", F(-3,5), 200),
            reading(g.d, st((2, F(13,2), F(1,6))), M_D1, "sunda", F(1,4), 200)]
    poss1 = [pos(st((-3, 4, F(1,3))), "tavo"), pos(st((4, 3, 2)), "tavo"), pos(st((1, 1, 3)), "sunda")]
    out.append(("D1", g.world("D1", new1, poss1), M_D1, "NEW; SYMMETRY is the sole reason for R1, SHAPE for R3, SCOPE for R4"))
    # D2: KNOWN(R4), dimmer nebulium (zun); R1 fits too but is forbidden by flp
    new2 = [reading(g.d, st((6, 6, 1)), M_D2, "tavo", F(1,4), 100), reading(g.d, st((9, F(54,5), F(3,2))), M_D2, "tavo", F(-1,4), 100)]
    poss2 = [pos(st((-6, 6, 1)), "tavo"), pos(st((2, 3, 3)), "sunda"), pos(st((7, 1, F(5,4))), "tavo")]
    out.append(("D2", g.world("D2", new2, poss2), M_D2, "KNOWN, nebulium type (dimmer on zun); forbidden R1 is a numerical fit"))
    # D3: FORK(R3, R4)
    new3 = [reading(g.d, st((4, 3, 1)), M_D3, "tavo", F(1,3), 100), reading(g.d, st((5, 5, F(7,4))), M_D3, "tavo", F(-1,5), 100)]
    poss3 = [pos(st((5, -5, F(1,3))), "tavo"), pos(st((1, 2, 3)), "tavo"), pos(st((3, 4, F(7,4))), "sunda")]
    out.append(("D3", g.world("D3", new3, poss3), M_D3, "FORK(R3, R4); scope-sensitive"))
    return out
