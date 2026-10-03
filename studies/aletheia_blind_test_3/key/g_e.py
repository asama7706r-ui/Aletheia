from build_worlds import *

def group():
    return Group(
        "kimb",
        {"kimb": dims(N=1, T=-1), "aq": dims(T=1), "bw": dims(N=1), "cs": dims(K=1)},
        {"ke": {"value": "17/5", "dims": dims(N=1, T=-1)}, "kf": {"value": "250", "dims": dims(K=1)},
         "kt": {"value": "3/2", "dims": dims(T=1)}},
        {"pirro": "1/16", "tavo": "1/25"},
        "kimb = ke*bw/(bw + ke*aq)",
        None,
        [cand(1, "lask", "ke*(aq/kt)**2", cov=switch("aq/kt", "<", F(1, 3))),
         cand(2, "zuro", "ke*bw**2/(bw + ke*aq)**2"),
         cand(3, "hosp", "ke*cs/kf", cov=switch("cs/kf", ">", F(3, 2))),
         cand(4, "vimo", "bw/aq")],
        [])

def st(t):
    return {"aq": t[0], "bw": t[1], "cs": t[2]}

OLD_MODEL = {}
OLD = [((F(1, 4), 2, 120), F(1, 2)), ((F(2, 5), 7, 300), F(-1, 3)), ((F(1, 5), 11, 210), F(3, 5)),
       ((F(3, 4), 5, 340), F(-3, 4)), ((F(3, 10), 3, 60), F(1, 4))]

def build():
    g = group()
    g.d['old_observations'] = [reading(g.d, st(s), OLD_MODEL, "pirro", o, 400) for s, o in OLD]
    return g

M_E1 = {'cands': {'R3': F(1, 25)}}
M_E2 = {'cands': {'R4': F(3, 2000)}}
M_E3 = {'expr': [("ke*(aq/kt)**2", F(-1, 10))]}
M_E4 = {'cands': {'R3': F(1, 25)}}

def worlds():
    g = build()
    out = []
    new1 = [reading(g.d, st((F(4,5), 6, 520)), M_E1, "pirro", F(1,3), 400), reading(g.d, st((F(13,10), 9, 440)), M_E1, "tavo", F(-1,2), 400),
            reading(g.d, st((F(3,5), 4, 610)), M_E1, "pirro", F(-1,4), 400)]
    poss1 = [pos(st((1, 8, 300)), "pirro"), pos(st((F(1,4), 3, 700)), "tavo"), pos(st((2, 10, 380)), "pirro")]
    out.append(("E1", g.world("E1", new1, poss1), M_E1, "KNOWN, nebulium type (switch on cs/kf)"))
    new2 = [reading(g.d, st((F(1,40), 9, 150)), M_E2, "pirro", F(1,4), 400), reading(g.d, st((F(1,25), 14, 90)), M_E2, "tavo", F(-1,3), 400)]
    poss2 = [pos(st((F(1,50), 5, 200)), "pirro"), pos(st((F(1,10), 12, 330)), "tavo"), pos(st((F(1,30), 2, 100)), "pirro")]
    out.append(("E2", g.world("E2", new2, poss2), M_E2, "KNOWN, uncovered relation that was below precision in the old domain"))
    new3 = [reading(g.d, st((F(6,5), 4, 200)), M_E3, "pirro", F(1,4), 400), reading(g.d, st((2, 7, 150)), M_E3, "tavo", F(-1,3), 400)]
    poss3 = [pos(st((F(1,5), 5, 200)), "pirro"), pos(st((F(5,2), 6, 100)), "tavo")]
    out.append(("E3", g.world("E3", new3, poss3), M_E3, "NEW, scope-sensitive (R1 switched off in the new domain)"))
    new4 = [reading(g.d, st((F(1,20), 8, 500)), M_E4, "pirro", F(-1,3), 400), reading(g.d, st((F(1,16), 7, 430)), M_E4, "tavo", F(1,5), 400)]
    poss4 = [pos(st((1, 8, 500)), "pirro"), pos(st((F(1,20), 8, 200)), "tavo"), pos(st((F(1,10), 3, 650)), "pirro")]
    out.append(("E4", g.world("E4", new4, poss4), M_E4, "FORK(R3, R4); R4 at the edge of its old bound; scope-sensitive"))
    return out
