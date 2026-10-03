"""Part B items (generator's script). World references use group-local names, mapped to W-ids."""
import sys, os, json, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from verify_key import *
from build_worlds import Q, truth_value, rnd
import g_a, g_c

def items(ids, raws_by_id, summaries):
    W = {wid: World(d) for wid, d in raws_by_id.items()}
    out = []
    def obs_item(cat, name, pidx, value, note):
        wid = ids[name]
        p = W[wid].poss[pidx]
        it = {"experiment": "B", "type": "observation", "world": wid,
              "state": {k: Q(v) for k, v in p['state'].items()}, "observer": p['observer'], "value": Q(value)}
        out.append((cat, it, note))
    # --- observation items
    w = W[ids['A1']]; p = w.poss[1]
    t = truth_value(raws_by_id[ids['A1']], p['state'], g_a.M_R1)
    obs_item('obs_flip', 'A1', 1, rnd(t + F(3, 10) * w.prec(p), 400),
             "NO_DEFICIT file: a reading where the planet-X candidate R1 is back (low sel) misses the base note; becomes KNOWN(R1)")
    w = W[ids['E1']]; P = summaries[ids['E1']]['an']['ranges']['R3'][0][0]; d = w.prec(w.poss[0])
    obs_item('obs_flip', 'E1', 0, P + d + F(1, 20),
             "KNOWN(R3) file: reading where the switch keeps R3 off lies just beyond the quarantine note; becomes NEW")
    w = W[ids['F1']]; P = summaries[ids['F1']]['an']['ranges']['R1'][0][0]; d = w.prec(w.poss[0])
    obs_item('obs_inside', 'F1', 0, P + F(9, 10) * d,
             "KNOWN(R1, exact) file: the reading meets the point note at 0.9 of the precision; nothing reopened")
    w = W[ids['C3']]; p = w.poss[0]
    t = truth_value(raws_by_id[ids['C3']], p['state'], g_c.M_C3)
    obs_item('obs_inside', 'C3', 0, rnd(t + F(1, 5) * w.prec(p), 80),
             "NEW file: a reading that agrees with the uncovered R2 shape; a NEW file is never reopened by a reading")
    obs_item('obs_fork', 'C1', 3, F(7504, 10),
             "FORK(R1,R2,R4): the reading excludes R4 only; becomes FORK(R1,R2)")
    w = W[ids['A4']]; p = w.poss[1]
    t = truth_value(raws_by_id[ids['A4']], p['state'], g_a.M_R1)
    obs_item('obs_fork', 'A4', 1, rnd(t - F(1, 5) * w.prec(p), 400),
             "FORK(R1,R4): the reading at high sel excludes R4; becomes KNOWN(R1)")
    # --- relation items
    def rel_item(cat, obs, rid, obj, term, note, cov=None, coef="unknown"):
        it = {"experiment": "B", "type": "relation", "observable": obs,
              "relation": {"id": rid, "object": obj, "term": term, "coefficient": coef, "coverage": cov}}
        out.append((cat, it, note))
    rel_item('rel_new_known', "tumb", "R5", "pexa", "kv*ral**2*tep/(kw**2*kx)",
             "the NEW file of tumb becomes KNOWN(R5); the KNOWN and FORK files are reopened and keep their verdicts")
    rel_item('rel_new_known', "plin", "R5", "fosk", "bq*lh**2/hax**2",
             "an uncovered relation with R2's term: the scope-sensitive NEW file becomes KNOWN(R5); the three-branch fork keeps its branches")
    rel_item('rel_known_fork', "kimb", "R5", "zuro", "bw**2/(ke*aq**2)",
             "KNOWN(R4) file of kimb becomes FORK(R4,R5); three other files reopened unchanged")
    rel_item('rel_known_fork', "tumb", "R5", "lurn", "kv*ral*tep**3/(kw*kx**3)",
             "KNOWN(R3) file of tumb (visible relation) becomes FORK(R3,R5)")
    rel_item('rel_unchanged', "vexa", "R5", "pemsy", "kz*dov**3*pim**3/vu",
             "switch-covered like R4; reopens the three non-NO_DEFICIT files of vexa, no verdict changes; the NO_DEFICIT file is not reopened",
             cov={"ratio": "dov*pim/vu", "factor": {"type": "switch", "on": ">", "threshold": "3"}})
    rel_item('rel_unchanged', "ostr", "R5", "terk", "cj*xel*yor*zun**2",
             "a relation forbidden by the reflection flp; reopens all three ostr files, no verdict changes")
    rel_item('rel_none', "yuth", "R3", "ekra", "pw**2/(kro*dun)",
             "the only yuth file is NO_DEFICIT: nothing is reopened")
    rel_item('rel_none', "brel", "R4", "wamo", "xr*sio**3/tq**2",
             "the only brel file is NO_DEFICIT (visible relation): nothing is reopened")
    # --- root items
    out.append(('root_none', {"experiment": "B", "type": "root", "constant": "zh", "new_value": "44"},
                "zh appears only in the candidates of a NO_DEFICIT file: no file used it"))
    out.append(('root_revive', {"experiment": "B", "type": "root", "constant": "vu", "new_value": "13/6"},
                "vu sits in R4's switch ratio: the corrected value turns R4 on in the NEW file of vexa, which becomes KNOWN(R4)"))
    out.append(('root_unchanged', {"experiment": "B", "type": "root", "observer": "tavo", "new_precision": "21/500"},
                "tavo is used in eight files (incl. a NO_DEFICIT file): all reopened, no verdict changes"))
    out.append(('root_vanish', {"experiment": "B", "type": "root", "observer": "pondo", "new_precision": "1/10"},
                "pondo made every new reading of one wesk file; with the corrected precision its deficit vanishes"))
    return out

def assign(out, seed=7):
    rng = random.Random(seed)
    order = list(range(len(out)))
    rng.shuffle(order)
    res = []
    for k, i in enumerate(order):
        cat, it, note = out[i]
        it = dict(it)
        iid = f"D-{k + 1:02d}"
        it = {"id": iid, **it}
        res.append((iid, cat, it, note))
    res.sort()
    return res
