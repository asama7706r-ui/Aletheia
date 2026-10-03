from build_worlds import *

def group():
    return Group(
        "wesk",
        {"wesk": dims(L=1, T=-1), "ofa": dims(L=1), "ipo": dims(T=1), "ruk": dims(Q=1)},
        {"nu1": {"value": "21/8", "dims": dims(L=1, T=-1)}, "nq": {"value": "7/2", "dims": dims(Q=1)}},
        {"hesk": "1/30", "gavi": "1/12", "pondo": "1/24"},
        "wesk = ofa/ipo + nu1",
        {"id": "V1", "object": "seb", "term": "nu1*ruk/nq"},
        [cand(1, "garu", "ofa**2/(ipo*(ofa + nu1*ipo))"),
         cand(2, "tibe", "nu1*(ruk/nq)**3", cov=switch("ruk/nq", ">", 2)),
         cand(3, "mawo", "nu1*nq/ruk", cov=dimmer("ofa/(nu1*ipo)", "r**2/(1 + r**2)")),
         cand(4, "pelo", "ofa*ruk/(ipo*nq)", coef=F(-3, 5))],
        [])

def st(t):
    return {"ofa": t[0], "ipo": t[1], "ruk": t[2]}

OLD_MODEL = {'mu': F(-7, 9)}
OLD = [((F(1, 2), 4, F(3, 2)), F(1, 3)), ((F(1, 4), 2, 5), F(-1, 2)), ((1, 6, F(5, 2)), F(1, 2)), ((F(3, 4), 5, 6), F(-3, 5))]

def build():
    g = group()
    g.d['old_observations'] = [reading(g.d, st(s), OLD_MODEL, "hesk", o, 900) for s, o in OLD]
    return g

M_G1 = {'mu': F(-785, 1000), 'cands': {'R2': F(-1, 100)}}
M_G2 = {'mu': F(-78, 100), 'cands': {'R3': F(1, 5)}}
M_G3 = {'mu': F(-72, 100)}
M_G4 = {'mu': F(-78, 100), 'expr': [("nu1*nq/ruk", F(3, 2))]}

def worlds():
    g = build()
    out = []
    new1 = [fixed(g.d, st((F(1,2), F(15,2), F(17,2))), F(-1219,450), "hesk", M_G1), fixed(g.d, st((F(11,4), F(15,2), F(29,2))), F(-6611,900), "gavi", M_G1)]
    poss1 = [pos(st((2, 1, 9)), "hesk"), pos(st((F(1,2), 3, 4)), "gavi"), pos(st((3, F(1,2), 2)), "hesk")]
    out.append(("G1", g.world("G1", new1, poss1), M_G1, "KNOWN, nebulium type (switch on ruk/nq); visible relation matters"))
    new2 = [fixed(g.d, st((F(21,2), F(5,4), 2)), F(1921,180), "hesk", M_G2), fixed(g.d, st((F(15,2), 2, F(5,2))), F(244,45), "gavi", M_G2)]
    poss2 = [pos(st((1, 4, 3)), "hesk"), pos(st((12, F(1,2), 5)), "gavi"), pos(st((F(5,2), 2, 1)), "hesk")]
    out.append(("G2", g.world("G2", new2, poss2), M_G2, "KNOWN, dimmer relation returns at large ofa/(nu1*ipo)"))
    new3 = [fixed(g.d, st((F(7,2), F(1,2), 1)), F(6529,720), "pondo", M_G3), fixed(g.d, st((3, F(5,4), F(5,2))), F(439,120), "pondo", M_G3),
            fixed(g.d, st((F(27,4), F(13,4), 1)), F(331,80), "pondo", M_G3)]
    poss3 = [pos(st((2, 1, 9)), "hesk"), pos(st((F(1,2), 3, 4)), "gavi")]
    out.append(("G3", g.world("G3", new3, poss3), M_G3, "NEW, scope-sensitive; the readings need a visible strength outside M_old; all from observer pondo"))
    new4 = [fixed(g.d, st((F(9,2), F(3,4), F(7,2))), F(2366,225), "hesk", M_G4), fixed(g.d, st((F(3,4), 3, 4)), F(301,75), "gavi", M_G4),
            fixed(g.d, st((F(1,4), F(1,2), F(3,2))), F(1031,90), "hesk", M_G4)]
    poss4 = [pos(st((2, 1, 9)), "hesk"), pos(st((F(1,2), 3, 4)), "gavi")]
    out.append(("G4", g.world("G4", new4, poss4), M_G4, "NEW; R3 would fit if uncovered (SCOPE alone)"))
    return out
