"""Design helpers for the generator (not part of the verification)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_key import *

def margin(X):
    """min over x of max_i (a_i.x - b_i): <=0 feasible (negative = slack), >0 = violation"""
    if not X.unknowns:
        return max(-r[1] for r in X.rows)
    us = X.unknowns + ['__t']
    A = [[r[0].get(u, F(0)) for u in X.unknowns] + [F(-1)] for r in X.rows]
    b = [r[1] for r in X.rows]
    st, val, x = lp(A, b, [F(0)] * len(X.unknowns) + [F(-1)])
    return -val

def report(W, extra=True):
    ctx = Ctx(W)
    s = world_summary(W)
    an = s['an']
    print(f"== {W.id} {W.y}: {answer_str(s['answer'])}  NO_SCOPE={answer_str(s['no_scope'])} "
          f"mid_mu={answer_str(s['mid_mu']) if s['mid_mu'] else '-'} errs={world_errors(W)}")
    print(f"   Z margin {float(margin(ctx.Z())):.5g}")
    for R in W.ledger:
        i = an['info'][R['id']]
        mA = margin(ctx.A(R)); mC = margin(ctx.C(R)); mS = margin(ctx.S(R))
        print(f"   {R['id']}: TYPE={i['TYPE']} SYM={i['SYM']} A={float(mA):.4g} C={float(mC):.4g} S={float(mS):.4g} "
              f"reasons={an['reasons'].get(R['id'], 'SUFF')}")
    if 'intervals' in an:
        for k, iv in an['intervals'].items():
            print(f"   {k}: " + ", ".join(f"{u}=[{float(a):.5g},{float(b):.5g}]" for u, (a, b) in iv.items()))
            print(f"      ranges: " + " ".join(f"[{float(a):.5g},{float(b):.5g}]" for a, b in an['ranges'][k]))
    if an['verdict'] == 'FORK':
        print("   sep:", an['separating'])
    if an['verdict'] == 'NEW':
        print("   joint feasible:", an['joint_feasible'])
    return s

import random

def search(g, wid, model, slots, possible, pred, n=200, seed=0, verbose=False, grid=200):
    """slots: list of (state_sampler(rng) -> state dict, observer, offset choices)"""
    from build_worlds import reading
    rng = random.Random(seed)
    found = []
    for it in range(n):
        new = []
        for sampler, ob, offs in slots:
            new.append(reading(g.d, sampler(rng), model, ob, rng.choice(offs), grid))
        d = g.world(wid, new, possible)
        try:
            W = World(d)
            if world_errors(W):
                continue
            s = world_summary(W)
        except Exception as e:
            if verbose: print('err', e)
            continue
        ok = pred(W, s)
        if ok:
            found.append((ok, new))
            if verbose: print(it, ok, [o['state'] for o in new])
    return found

def with_cand(d, c):
    d = copy.deepcopy(d)
    d['ledger'].append(copy.deepcopy(c))
    return d
import copy
