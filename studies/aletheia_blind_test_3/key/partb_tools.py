"""Helpers to design Part B items against the assembled worlds (generator's script)."""
import sys, os, json, pickle
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from verify_key import *
from build_worlds import Q

ROOT = os.path.dirname(HERE)

def load():
    raws = []
    for i in range(1, 28):
        with open(os.path.join(ROOT, 'worlds', f"W-{i:02d}.json"), encoding='utf-8') as fh:
            raws.append(json.load(fh))
    worlds = {d['id']: World(d) for d in raws}
    summaries = {wid: world_summary(W) for wid, W in worlds.items()}
    return raws, worlds, summaries

CATS = ['obs_flip', 'obs_inside', 'obs_fork', 'rel_new_known', 'rel_known_fork', 'rel_unchanged', 'rel_none',
        'root_vanish', 'root_revive', 'root_unchanged', 'root_none']

def evaluate(raws, worlds, summaries, item):
    reop, finals, errs = item_reference(raws, worlds, summaries, item)
    cats = []
    if not errs:
        cats = [c for c in CATS if item_category_ok(item, c, reop, finals, summaries, worlds)]
    return reop, finals, errs, cats

def show(raws, worlds, summaries, item):
    reop, finals, errs, cats = evaluate(raws, worlds, summaries, item)
    if errs:
        print("  ERRORS:", errs[:4])
    else:
        print("  reopened", reop, "cats", cats, "finals", {w: f"{answer_str(summaries[w]['answer'])}->{answer_str(a)}" for w, a in finals.items()})
    return reop, finals, errs, cats

import itertools as _it

GROUPS = {
    # observable: (unit expression with the observable's dims, dimensionless ratios, existing object names)
    'vexa': ("kz*vu*dov*pim**2", ["sel/kq", "dov*pim/vu", "pim*dov/vu"], "wiss"),
    'tumb': ("kv", ["ral/kw", "tep/kx"], "lurn"),
    'plin': ("bq", ["hax/lh", "mev/tz", "jor"], "gix"),
    'ostr': ("cj*cl**2", ["xel/cl", "yor/cl", "zun"], "nim"),
    'kimb': ("ke", ["bw/(ke*aq)", "cs/kf", "aq/kt"], "vimo"),
    'dral': ("gm*ga/ux", ["ux**2/(ga*wq**2)", "vy/gm"], "tolu"),
    'wesk': ("nu1", ["ofa/(nu1*ipo)", "ruk/nq"], "garu"),
    'yuth': ("pw*kro/dun", ["kro**3/(pw*kro)", "dun/zh"], "vonu"),
    'brel': ("fum*sio", ["sio/tq", "fum/xr"], "wamo"),
}

def templates(observable, max_terms=200, seed=0):
    import random
    unit, ratios, obj = GROUPS[observable]
    rng = random.Random(seed)
    out = []
    exps = [-2, -1, 1, 2]
    for n in (1, 2):
        for combo in _it.combinations(ratios, n):
            for es in _it.product(exps, repeat=n):
                term = unit + "".join(f"*({r})**{e}" if e > 0 else f"/({r})**{-e}" for r, e in zip(combo, es))
                out.append(term)
    rng.shuffle(out)
    return out[:max_terms]
