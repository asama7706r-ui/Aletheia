from build_worlds import *

# N1: a NO_DEFICIT phenomenon on its own; constant zh appears only in its candidates
def group_n1():
    return Group(
        "yuth",
        {"yuth": dims(L=3, M=-1), "kro": dims(L=1), "dun": dims(M=1)},
        {"pw": {"value": "5/9", "dims": dims(L=2)}, "zh": {"value": "41", "dims": dims(M=1)}},
        {"tavo": "1/25", "brav": "1/20"},
        "yuth = kro*pw/dun",
        None,
        [cand(1, "vonu", "kro**3/zh"),
         cand(2, "ekra", "pw*kro*zh/dun**2", cov=switch("dun/zh", "<", F(1, 3)))],
        [])

def st1(t):
    return {"kro": t[0], "dun": t[1]}

# N2: NO_DEFICIT only for a visible strength away from the midpoint of M_old
def group_n2():
    return Group(
        "brel",
        {"brel": dims(K=1, T=1), "sio": dims(T=1), "fum": dims(K=1)},
        {"xr": {"value": "13/3", "dims": dims(K=1)}, "tq": {"value": "8", "dims": dims(T=1)}},
        {"orvi": "1/50", "gavi": "1/12"},
        "brel = fum*sio*(1 + sio/tq)",
        {"id": "V1", "object": "lito", "term": "xr*sio**2/tq"},
        [cand(1, "wamo", "xr*tq*(fum/xr)**3"),
         cand(2, "ulse", "fum*tq**2/sio", cov=dimmer("fum/xr", "1/(1 + r)")),
         cand(3, "dezo", "xr*sio*fum/(fum + xr)")],
        [])

def st2(t):
    return {"sio": t[0], "fum": t[1]}

M_N1 = {'cands': {'R1': F(1, 300)}}
M_N2 = {'mu': F(1, 5)}

OLD1 = [((2, 3), F(1, 3)), ((F(3, 2), 7), F(-1, 2)), ((3, 5), F(3, 5))]
OLD2 = [((F(1, 2), 3), F(1, 3)), ((1, F(3, 2)), F(-1, 2)), ((F(3, 4), 6), F(3, 5)), ((F(3, 2), 2), F(-2, 3))]
M_N1 = {'cands': {'R1': F(1, 100)}}
M_N2 = {'mu': F(1, 5)}
M_N2_NEW = {'mu': F(1043, 5850)}

def build_n1():
    g = group_n1()
    g.d['old_observations'] = [reading(g.d, st1(s), {}, "tavo", o, 400) for s, o in OLD1]
    return g

def build_n2():
    g = group_n2()
    g.d['old_observations'] = [reading(g.d, st2(s), M_N2, "orvi", o, 600) for s, o in OLD2]
    return g

def worlds():
    out = []
    g = build_n1()
    new1 = [reading(g.d, st1((4, 9)), M_N1, "tavo", F(1,5), 400), reading(g.d, st1((5, 11)), M_N1, "brav", F(-1,10), 400)]
    poss1 = [pos(st1((8, 6)), "brav"), pos(st1((2, 12)), "tavo"), pos(st1((6, 20)), "tavo")]
    out.append(("N1", g.world("N1", new1, poss1), M_N1, "NO_DEFICIT; sub-precision residual shaped like R1"))
    g = build_n2()
    new2 = [reading(g.d, st2((6, 2)), M_N2_NEW, "gavi", F(-1,4), 600), reading(g.d, st2((9, 5)), M_N2_NEW, "orvi", F(1,3), 600)]
    poss2 = [pos(st2((12, 3)), "gavi"), pos(st2((F(5,2), 9)), "orvi"), pos(st2((4, F(1,2))), "gavi")]
    out.append(("N2", g.world("N2", new2, poss2), M_N2_NEW, "NO_DEFICIT only for mu in the lower part of M_old; visible relation matters"))
    return out
