from build_worlds import *

def group():
    return Group(
        "dral",
        {"dral": dims(M=1, L=1, T=-2), "ux": dims(L=1), "vy": dims(M=1), "wq": dims(T=1)},
        {"ga": {"value": "49/4", "dims": dims(L=2, T=-2)}, "gm": {"value": "3", "dims": dims(M=1)}},
        {"hesk": "1/30", "pirro": "1/16"},
        "dral = ga*vy/ux",
        None,
        [cand(1, "pask", "vy*ux/wq**2", coef=F(1, 8)),
         cand(2, "tolu", "gm*ux**2/wq**3"),
         cand(3, "zemo", "vy*ux**2/wq**2"),
         cand(4, "hirn", "gm*ga/ux", cov=dimmer("ux**2/(ga*wq**2)", "1/(1 + r**3)"))],
        [])

def st(t):
    return {"ux": t[0], "vy": t[1], "wq": t[2]}

OLD_MODEL = {}
OLD = [((F(3, 2), 2, 9), F(1, 3)), ((4, F(1, 2), 14), F(-1, 2)), ((F(5, 2), 5, 11), F(3, 5)), ((6, 3, 20), F(-1, 4))]

def build():
    g = group()
    g.d['old_observations'] = [reading(g.d, st(s), OLD_MODEL, "hesk", o, 600) for s, o in OLD]
    return g

M_F1 = {'cands': {'R1': F(1, 8)}}
M_F2 = {'expr': [("gm*ux/wq**2", F(1, 20))]}
M_F3 = {'expr': [("vy*ux/wq**2", F(1, 6))]}
M_F4 = {'cands': {'R1': F(1, 8)}}

def worlds():
    g = build()
    out = []
    new1 = [reading(g.d, st((2, 3, F(3,2))), M_F1, "hesk", F(1,4), 600), reading(g.d, st((F(7,2), F(4,3), 2)), M_F1, "pirro", F(-1,3), 600)]
    poss1 = [pos(st((3, 2, F(5,4))), "hesk"), pos(st((1, 6, 3)), "pirro"), pos(st((5, 1, 4)), "hesk")]
    out.append(("F1", g.world("F1", new1, poss1), M_F1, "KNOWN with an exact coefficient (no unknowns in A_R1)"))
    # revised after the W8 reading issue (key/generator_notes.md): no combination of R2, R4 (with or without R1) fits
    new2 = [fixed(g.d, st((3, F(9,2), F(11,4))), F(11077,600), "hesk", M_F2), fixed(g.d, st((6, 2, F(11,4))), F(2491,600), "pirro", M_F2),
            fixed(g.d, st((F(3,2), 6, F(9,4))), F(1961,40), "hesk", M_F2)]
    poss2 = [pos(st((2, 4, F(3,2))), "hesk"), pos(st((4, 1, 3)), "pirro")]
    out.append(("F2", g.world("F2", new2, poss2), M_F2, "NEW; R3 (TYPE-impossible) fits, R1 has the right shape but the wrong exact value"))
    new3 = [fixed(g.d, st((2, 5, F(3,4))), F(1343,40), "hesk", M_F3), fixed(g.d, st((F(15,2), F(5,2), F(5,4))), F(92,15), "pirro", M_F3)]
    poss3 = [pos(st((2, 4, F(3,2))), "hesk"), pos(st((4, 1, 3)), "pirro"), pos(st((7, 3, F(1,2))), "hesk"), pos(st((1, 2, F(5,4))), "pirro")]
    out.append(("F3", g.world("F3", new3, poss3), M_F3, "NEW; R1's registered exact value is contradicted (BOUND alone)"))
    new4 = [reading(g.d, st((3, 2, 1)), M_F4, "hesk", F(1,3), 600), reading(g.d, st((9, 3, 2)), M_F4, "pirro", F(-1,4), 600)]
    poss4 = [pos(st((2, 6, 1)), "hesk"), pos(st((9, 1, F(3,2))), "pirro"), pos(st((5, 3, 4)), "hesk")]
    out.append(("F4", g.world("F4", new4, poss4), M_F4, "FORK(R1 exact, R2)"))
    return out
