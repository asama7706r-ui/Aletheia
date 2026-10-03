from build_worlds import *

def group():
    return Group(
        "vexa",
        {"vexa": dims(M=1, L=2, T=-3), "dov": dims(L=1), "pim": dims(T=-1), "sel": dims(N=1)},
        {"kz": {"value": "7/3", "dims": dims(M=1)}, "kq": {"value": "40", "dims": dims(N=1)},
         "vu": {"value": "13/4", "dims": dims(L=1, T=-1)}},
        {"brav": "1/20", "kelto": "3/40", "yomp": "1/8"},
        "vexa = kz*dov**2*pim**3",
        None,
        [cand(1, "tarn", "kz*vu*dov*pim**2", cov=dimmer("sel/kq", "1/(1+r**2)", "fades as sel grows past kq")),
         cand(2, "wiss", "kz*dov*pim**2*(dov*pim - vu)"),
         cand(3, "hulo", "kz*dov*pim**3"),
         cand(4, "pemsy", "kz*vu**2*pim*sel/kq", cov=switch("dov*pim/vu", ">", 3, "acts only when dov*pim exceeds 3*vu"))],
        [])

OLD_MODEL = {'cands': {'R1': F(3, 40)}}
OLD = [((2, 1, 300), F(-3, 10)), ((3, F(1, 2), 520), F(-3, 5)), ((F(5, 2), F(3, 2), 410), F(-1, 2)),
       ((4, F(3, 4), 880), F(-9, 10)), ((F(3, 2), F(5, 4), 640), F(7, 10))]

def st(t):
    return {"dov": t[0], "pim": t[1], "sel": t[2]}

def build():
    g = group()
    g.d['old_observations'] = [reading(g.d, st(s), OLD_MODEL, "brav", o, 400) for s, o in OLD]
    return g

M_R1 = {'cands': {'R1': F(3, 40)}}
M_A3 = {'expr': [("kz*dov*pim**3", F(3, 2000))]}

def worlds():
    g = build()
    out = []
    # A1: NO_DEFICIT with a planet-X trap (R1 absorbs the sub-precision residual)
    new1 = [reading(g.d, st((F(5,2), F(1,2), 95)), M_R1, "kelto", F(0), 400),
            reading(g.d, st((F(9,4), F(3,4), 130)), M_R1, "kelto", F(-1,10), 400),
            reading(g.d, st((F(11,4), F(1,2), 80)), M_R1, "yomp", F(1,5), 400)]
    poss1 = [pos(st((3, F(3,4), 600)), "brav"), pos(st((F(5,2), F(3,2), 11)), "kelto"), pos(st((F(7,4), 2, 70)), "yomp")]
    out.append(("A1", g.world("A1", new1, poss1), M_R1, "NO_DEFICIT; planet-X trap: R1 (dimmer) fits the sub-precision residual"))
    # A2: KNOWN(R1), dimmer nebulium; R2 BOUND and R4 SCOPE close to the SHAPE boundary
    new2 = [reading(g.d, st((4, F(3,2), 30)), M_R1, "kelto", F(3,4), 200),
            reading(g.d, st((F(19,4), F(5,4), 29)), M_R1, "kelto", F(-1,4), 200)]
    poss2 = [pos(st((F(13,4), F(5,2), 45)), "yomp"), pos(st((F(9,2), F(3,2), 21)), "kelto"), pos(st((F(5,2), F(11,4), 260)), "brav")]
    out.append(("A2", g.world("A2", new2, poss2), M_R1, "KNOWN, nebulium type (dimmer on sel/kq)"))
    # A3: NEW; R3 TYPE sole (fits numerically), R1 and R4 SCOPE sole, R2 SHAPE sole
    new3 = [reading(g.d, st((2, 4, 320)), M_A3, "kelto", F(-2,5), 100),
            reading(g.d, st((F(3,2), 5, 375)), M_A3, "yomp", F(1,3), 100)]
    poss3 = [pos(st((2, F(9,2), 33)), "kelto"), pos(st((F(5,4), 6, 410)), "yomp"), pos(st((1, 3, 150)), "brav")]
    out.append(("A3", g.world("A3", new3, poss3), M_A3, "NEW; a dimensionally impossible term (R3) is the numerical fit"))
    # A4: FORK(R1, R4); separable at high sel with dov*pim > 3*vu
    new4 = [reading(g.d, st((F(7,2), F(7,2), 10)), M_R1, "kelto", F(1,5), 100),
            reading(g.d, st((F(11,2), 2, 9)), M_R1, "yomp", F(-1,2), 100)]
    poss4 = [pos(st((5, 3, 12)), "yomp"), pos(st((F(9,2), F(5,2), 160)), "kelto"), pos(st((F(3,2), 2, 7)), "brav")]
    out.append(("A4", g.world("A4", new4, poss4), M_R1, "FORK(R1, R4), scope-sensitive"))
    return out
