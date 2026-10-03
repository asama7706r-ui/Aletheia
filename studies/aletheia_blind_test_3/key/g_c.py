from build_worlds import *

def group():
    return Group(
        "plin",
        {"plin": dims(M=1, L=-3), "hax": dims(L=1), "mev": dims(T=1), "jor": {}},
        {"bq": {"value": "1250", "dims": dims(M=1, L=-3)}, "tz": {"value": "45/7", "dims": dims(T=1)},
         "lh": {"value": "3/8", "dims": dims(L=1)}},
        {"sunda": "2/5", "yomp": "1/8"},
        "plin = bq*jor/(jor + 2)",
        None,
        [cand(1, "fosk", "bq*tz/mev"),
         cand(2, "gix", "bq*lh**2/hax**2", cov=dimmer("mev/tz", "3/(r + 3)")),
         cand(3, "yelm", "bq*jor**3/(jor + 8)", coef=F(1, 1500)),
         cand(4, "trov", "bq*hax*mev/(lh*tz)", cov=switch("jor", ">", F(3, 2)))],
        [])

def st(t):
    return {"hax": t[0], "mev": t[1], "jor": t[2]}

OLD_MODEL = {}
OLD = [((F(1, 2), 30, F(1, 3)), F(1, 2)), ((2, 55, F(5, 4)), F(-2, 5)), ((F(3, 4), 80, F(7, 10)), F(7, 10)),
       ((F(5, 4), 120, F(1, 10)), F(-3, 4))]

def build():
    g = group()
    g.d['old_observations'] = [reading(g.d, st(s), OLD_MODEL, "sunda", o, 50) for s, o in OLD]
    return g

M_C1 = {'cands': {'R2': F(13, 10000)}}
M_C2 = {'cands': {'R4': F(29, 10000)}}
M_C3 = {'expr': [("bq*lh**2/hax**2", F(8, 10000))]}

def worlds():
    g = build()
    out = []
    # C1: one anomalous reading, three registered suspects; R3 (exact) excluded by BOUND
    new1 = [reading(g.d, st((F(1,2), F(7,2), F(9,4))), M_C1, "yomp", F(-1,4), 80)]
    poss1 = [pos(st((F(1,2), 12, 2)), "yomp"), pos(st((F(1,4), 5, F(5,2))), "yomp"), pos(st((1, 3, F(6,5))), "yomp"),
             pos(st((F(3,2), 4, 3)), "sunda")]
    out.append(("C1", g.world("C1", new1, poss1), M_C1, "FORK with three branches (R1, R2, R4); scope-sensitive"))
    # C2: KNOWN(R4), switch nebulium (on for jor > 3/2); R1 fits the shape but is just out of its old bound
    new2 = [reading(g.d, st((2, 2, F(7,4))), M_C2, "yomp", F(1,5), 80), reading(g.d, st((F(1,2), 4, F(8,3))), M_C2, "yomp", F(-1,2), 80)]
    poss2 = [pos(st((1, 3, 2)), "yomp"), pos(st((F(1,2), 9, F(5,4))), "sunda"), pos(st((F(5,2), 1, 3)), "yomp")]
    out.append(("C2", g.world("C2", new2, poss2), M_C2, "KNOWN, nebulium type (switch on jor)"))
    # C3: NEW; R2 would fit if uncovered (SCOPE); NO_SCOPE says KNOWN(R2)
    new3 = [reading(g.d, st((F(1,4), 100, F(1,2))), M_C3, "yomp", F(1,3), 80), reading(g.d, st((F(1,3), 85, F(6,5))), M_C3, "yomp", F(-1,4), 80),
            reading(g.d, st((F(1,5), 30, F(1,4))), M_C3, "sunda", F(1,5), 80)]
    poss3 = [pos(st((F(1,4), 6, F(1,2))), "yomp"), pos(st((F(2,3), 70, 2)), "sunda")]
    out.append(("C3", g.world("C3", new3, poss3), M_C3, "NEW, scope-sensitive (the covered R2 would fit uncovered)"))
    return out
