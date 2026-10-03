from build_worlds import *

def group():
    return Group(
        "tumb",
        {"tumb": dims(Q=1, T=-1), "ral": dims(L=1), "tep": dims(K=1)},
        {"kv": {"value": "11/6", "dims": dims(Q=1, T=-1)}, "kw": {"value": "5/2", "dims": dims(L=1)},
         "kx": {"value": "300", "dims": dims(K=1)}},
        {"orvi": "1/50", "kelto": "3/40"},
        "tumb = kv*ral/(ral + kw)",
        {"id": "V1", "object": "nod", "term": "kv*ral/kw"},
        [cand(1, "lurn", "kv*ral**2/kw**2"),
         cand(2, "pexa", "kv*(tep/kx)**2", cov=switch("tep/kx", "<", F(2, 3))),
         cand(3, "sibo", "kv*tep/kx", cov=dimmer("ral/kw", "r**2/(1+r**2)", "hidden at small ral, back at large ral")),
         cand(4, "dwim", "kv*kw/ral")],
        [])

def st(t):
    return {"ral": t[0], "tep": t[1]}

OLD_MODEL = {"mu": F(403, 1000), "cands": {"R3": F(17, 200)}}
OLD = [((F(1, 2), 420), F(3, 5)), ((F(3, 4), 150), F(-1, 2)), ((F(1, 4), 260), F(1, 3)), ((1, 510), F(-4, 5))]

def build():
    g = group()
    g.d['old_observations'] = [reading(g.d, st(s), OLD_MODEL, "orvi", o, 500) for s, o in OLD]
    return g

M_B1 = {'mu': F(403, 1000), 'cands': {'R3': F(17, 200)}}
M_B2 = {'mu': F(41, 100), 'cands': {'R1': F(3, 500)}}
M_B3 = {'mu': F(41, 100), 'expr': [("kv*ral*tep/(kw*kx)", F(-1, 40))]}

def worlds():
    g = build()
    out = []
    # B1: KNOWN(R3), dimmer nebulium (back at large ral); fits only for mu below the midpoint of M_old
    new1 = [fixed(g.d, st((F(25,2), 170)), F(529,100), "orvi", M_B1), fixed(g.d, st((5, 450)), F(577,200), "kelto", M_B1)]
    poss1 = [pos(st((F(17,2), 610)), "kelto"), pos(st((F(3,2), 140)), "orvi"), pos(st((20, 260)), "kelto"), pos(st((24, 640)), "kelto")]
    out.append(("B1", g.world("B1", new1, poss1), M_B1, "KNOWN, nebulium type (dimmer); visible relation matters"))
    # B2: FORK(R1, R2); R2 is off in the new domain but acts through an old reading by shifting mu
    new2 = [fixed(g.d, st((F(31,2), 450)), F(1333,200), "orvi", M_B2), fixed(g.d, st((17, 230)), F(1453,200), "kelto", M_B2)]
    poss2 = [pos(st((F(9,2), 610)), "kelto"), pos(st((F(31,2), 120)), "orvi"), pos(st((22, 350)), "orvi"), pos(st((F(5,2), 175)), "kelto")]
    out.append(("B2", g.world("B2", new2, poss2), M_B2, "FORK(R1, R2); R2 is switched off in the new domain and acts only through an old reading (shifting mu); visible relation matters; scope-sensitive"))
    # B3: NEW; R2 and R3 excluded by BOUND alone
    new3 = [fixed(g.d, st((F(19,2), 160)), F(423,100), "orvi", M_B3), fixed(g.d, st((7, 160)), F(167,50), "kelto", M_B3),
            fixed(g.d, st((F(21,2), 450)), F(867,200), "orvi", M_B3)]
    poss3 = [pos(st((F(9,2), 610)), "kelto"), pos(st((F(31,2), 120)), "orvi"), pos(st((22, 350)), "orvi")]
    out.append(("B3", g.world("B3", new3, poss3), M_B3, "NEW; BOUND is the sole reason for R2 and R3"))
    return out
