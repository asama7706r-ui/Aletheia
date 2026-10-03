"""Generator's construction script for the blind-test-3 worlds (kept with the key).

Every reading is produced from an explicit hidden truth plus a chosen offset
inside the observer's precision band, then rounded to a grid and re-checked.
"""
import sys, os, json, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_key import *
from fractions import Fraction as F

def Q(x):
    return fs(F(x))

def dims(**kw):
    return {k: v for k, v in kw.items()}

def obs(state, value, observer):
    return {"state": {k: Q(v) for k, v in state.items()}, "value": Q(value), "observer": observer}

def pos(state, observer):
    return {"state": {k: Q(v) for k, v in state.items()}, "observer": observer}

def cand(i, obj, term, coef="unknown", cov=None):
    c = {"id": f"R{i}", "object": obj, "term": term,
         "coefficient": coef if coef == "unknown" else {"exact": Q(coef)}, "coverage": cov}
    return c

def dimmer(ratio, expr, summary=None):
    c = {"ratio": ratio, "factor": {"type": "dimmer", "expr": expr}}
    if summary:
        c["summary"] = summary
    return c

def switch(ratio, on, thr, summary=None):
    c = {"ratio": ratio, "factor": {"type": "switch", "on": on, "threshold": Q(thr)}}
    if summary:
        c["summary"] = summary
    return c

def rnd(x, grid):
    """round exact x to the nearest multiple of 1/grid"""
    x = F(x)
    return F(round(x * grid), grid)

class Group:
    """shared part of the worlds of one observable"""
    def __init__(self, observable, quantities, constants, observers, base_law, visible, ledger, symmetries):
        self.d = {"observable": observable, "quantities": quantities, "constants": constants,
                  "observers": observers, "base_law": base_law, "visible": visible, "ledger": ledger,
                  "symmetries": symmetries, "old_observations": []}

    def world(self, wid, new, possible):
        d = {"id": wid, "experiment": "A"}
        d.update(copy.deepcopy(self.d))
        d["new_observations"] = new
        d["possible_observations"] = possible
        return d

    def proto(self):
        """a World object for evaluation with a dummy new/possible list"""
        d = self.world("W-XX", [], [])
        return d

def truth_value(d, state, model):
    """model: {'mu': x, 'cands': {Rid: lam}, 'expr': [(expr, coef)]}"""
    W = World(_complete(d, state))
    s = {k: F(v) for k, v in state.items()}
    val = W.fval(s)
    if W.vis is not None and model.get('mu') is not None:
        val += F(model['mu']) * W.hv(s)
    for rid, lam in model.get('cands', {}).items():
        R = W.cand(rid)
        val += F(lam) * W.h(R, s) * W.phi(R, s)
    for ex, c in model.get('expr', []):
        val += F(c) * ev(parse(ex), W.env(s))
    return val

def _complete(d, state):
    d = copy.deepcopy(d)
    obsname = next(iter(d['observers']))
    st = {k: Q(v) for k, v in state.items()}
    d.setdefault('id', 'W-XX')
    d['experiment'] = 'A'
    if not d.get('old_observations'):
        d['old_observations'] = [{"state": st, "value": "0", "observer": obsname}]
    d['new_observations'] = [{"state": st, "value": "0", "observer": obsname}]
    d['possible_observations'] = [{"state": st, "observer": obsname}] * 2
    return d

def reading(d, state, model, observer, offset, grid):
    """truth + offset*precision, rounded to 1/grid; checked to stay within precision of truth"""
    t = truth_value(d, state, model)
    prec = rat(d['observers'][observer])
    v = rnd(t + F(offset) * prec, grid)
    assert abs(v - t) <= prec, (state, float(t), float(v), float(prec))
    return obs(state, v, observer)

def hidden(model):
    terms = [{"candidate": r, "coefficient": Q(l)} for r, l in model.get('cands', {}).items()]
    terms += [{"expr": e, "coefficient": Q(c)} for e, c in model.get('expr', [])]
    h = {"terms": terms}
    if model.get('mu') is not None:
        h["visible_coefficient"] = Q(model['mu'])
    return h

def fixed(d, state, value, observer, model):
    """an explicit reading, checked to lie within precision of the hidden truth"""
    t = truth_value(d, state, model)
    prec = rat(d['observers'][observer])
    v = F(value)
    assert abs(v - t) <= prec, (state, float(t), float(v), float(prec))
    return obs(state, v, observer)
