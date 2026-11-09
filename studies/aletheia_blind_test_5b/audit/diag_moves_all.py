"""Diagnostic after test 5b (not a test; spent worlds; the sealed results stand). Asked after the owner's question of
2026-11-05: Stockfish narrows a huge search. Does the same shape work on our refutations?
Stockfish needs a list of legal moves in each position, then searches deeper step by step. Here:
- moves(): the "legal moves" of a state, computed from that state's own rewriter, never from a key or a fixed list:
  zero products among the names and the role's words, then factored one-word relations of those words, then of the
  rewriter's other normal words (up to length P2 when associative, 2 otherwise), and exact roots over Q(sqrt c);
- refute(): the same three node kinds as the sealed search (close, positive, split/inverse), with depth 0, 1, 2, ...
  S in turn (iterative deepening), budget 30 s per candidate. The sealed checker must accept the proof.
The set: every refutation in the keys of test 5 and test 5b, each read as a question: "refute this candidate".
The comparison: did the sealed procedure, in its full hour per world, reach a proof the checker accepts for it?
(5b: results/outputs_X.json; test 5's worlds: dev/check_t5/outputs_X.json, the same sealed code.)

Reading rule, written before the first run. Only the key proofs with a case node at the root count, on test 5's
worlds (the builder was not written on them, though I read those worlds weeks ago):
- 80% or more found: deriving moves from the state is not just fitted to the 12 worlds of 5b;
- under 50%: it is fitted to them;
- between: mixed, and the misses say what is missing.
Usage (from aletheia_blind_test_5b/): python -I audit/diag_moves_all.py"""
import itertools
import json
import os
import sys
import time
from fractions import Fraction as Fr

import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import diag_direction_5b as D  # noqa: E402
import diag_build_5b as B  # noqa: E402

P, C = D.P, D.C
ROOT = D.ROOT
T5 = os.path.join(os.path.dirname(ROOT), "aletheia_blind_test_5")
BUDGET = 30
sys.stdout.reconfigure(encoding="utf-8")


def safely(fn, *args):
    try:
        return fn(*args) or []
    except Exception:  # a diagnostic: a move source that cannot handle a state gives no moves there
        return []


def roots_of(W, alg, rw, v):
    """(re, im) of each exact root of v's degree-2 relation, as (a, b, c) triples, or []."""
    expr = B.degree2_relation(W, alg, rw, v)
    t = sp.Symbol("t")
    if expr is None or sp.degree(expr, t) != 2:
        return []
    rs = list(sp.roots(sp.Poly(expr, t, extension=True), t))
    if len(rs) != 2:
        return []
    parts = [(B.surd_of(sp.re(r)), B.surd_of(sp.im(r))) for r in rs]
    return [] if any(x is None for p in parts for x in p) else parts


def root_pairs(W, alg, rw, v):
    if W.th_c is None:
        return []
    parts = roots_of(W, alg, rw, v)
    if not parts or {x[2] for p in parts for x in p if x[2] is not None} != {W.th_c}:
        return []
    A = alg.W
    els = []
    for re_, im_ in parts:
        e_ = dict(v)
        if re_[0] or re_[1]:
            e_ = alg.add(e_, {A.unit: P.Surd(-re_[0], -re_[1], W.th_c)})
        if im_[0] or im_[1]:
            e_ = alg.add(e_, {A.gen("e1"): P.Surd(-im_[0], -im_[1], W.th_c)})
        els.append(e_)
    a, b = els
    return [(a, b)] if not rw.nf(alg.mul(a, b)) else []


def moves(W, alg, rw):
    key = id(rw)
    if key in W.move_cache:
        return W.move_cache[key][1]
    A = alg.W
    L = D.word_list(W, alg)
    out = []

    def add(ps):
        for p in ps:
            if p not in out:
                out.append(p)
    for x, y in itertools.product(L, repeat=2):
        if rw.nf(x) and rw.nf(y) and not rw.nf(alg.mul(x, y)):
            add([(x, y)])
    for v in L:
        add(safely(D.poly_pairs, W, alg, rw, v))
        add(safely(root_pairs, W, alg, rw, v))
    for word in safely(B.normal_words, W, alg, rw, P.P2 if A.assoc else 2):
        if time.time() > W.t_end:
            break
        v = {word: Fr(1)}
        if v not in L:
            add(safely(D.poly_pairs, W, alg, rw, v))
            add(safely(root_pairs, W, alg, rw, v))
    W.move_cache[key] = (rw, out)                 # rw is kept, so its id stays its own
    return out


def build(W, kept, extra, names, depth, maxd):
    if time.time() > W.t_end:
        return None
    alg, rw, _rels, ineqs = W.rewriter(kept, extra, names)
    A = alg.W
    m = rw.member({A.unit: Fr(1)})
    if m is not None:
        return {"node": "close", "target": {"const": "1"}, "terms": P.terms_json(m, A)}
    for k, t_ in enumerate(ineqs):
        m = rw.member(t_)
        if m is not None:
            return {"node": "close", "target": {"ineq": k}, "terms": P.terms_json(m, A)}
    if "q14" in kept:
        for t_ in D.word_list(W, alg):
            tt = alg.mul(t_, t_)
            r = rw.nf(tt)
            if set(r) <= {A.unit} and r.get(A.unit, 0) < 0:
                c = -r[A.unit]
                m = rw.member(alg.add(tt, {A.unit: c}))
                if m is not None:
                    return {"node": "positive", "t": [P.el_json(t_, A)], "c": P.cj(c), "terms": P.terms_json(m, A)}
    if depth >= maxd:
        return None
    splitter = "q12" if "q12" in kept else ("q14" if "q14" in kept else None)
    if splitter is None and "q13" not in kept:
        return None
    pairs = moves(W, alg, rw)
    if splitter is None:
        for g in sorted(names):
            gv = {A.gen(g): Fr(1)}
            if rw.nf(gv) and all(gv != a for a, _b in pairs):
                pairs = pairs + [(gv, None)]
    for a, b in pairs:
        if time.time() > W.t_end:
            return None
        k0 = build(W, kept, extra + [a], names, depth + 1, maxd)
        if k0 is None:
            continue
        if splitter:
            k1 = build(W, kept, extra + [b], names, depth + 1, maxd)
            if k1 is None:
                continue
            return {"node": "split", "by": splitter, "a": P.el_json(a, A), "b": P.el_json(b, A),
                    "proof_ab": P.terms_json(rw.member(alg.mul(a, b)), A), "children": [k0, k1]}
        v = next(f"w{i}" for i in range(1, 99) if f"w{i}" not in names)
        vv = {A.gen(v): Fr(1)}
        av = alg.add(alg.mul(a, vv), {A.unit: Fr(1)}, -1)
        va = alg.add(alg.mul(vv, a), {A.unit: Fr(1)}, -1)
        k1 = build(W, kept, extra + [av, va], names | {v}, depth + 1, maxd)
        if k1 is not None:
            return {"node": "inverse", "a": P.el_json(a, A), "v": v, "children": [k0, k1]}
    return None


def theta_of(c):
    return None if c is None else {"poly": [P.fs(-c), "0", "1"], "lo": "0", "hi": P.fs(c + 1)}


def refute(W, kept, d, winfo):
    """A proof the sealed checker accepts, or None; also the number of moves at the root."""
    alg, rw, _r, _i = W.rewriter(kept)
    n_root = len(moves(W, alg, rw))
    fields = [None]
    for word in safely(B.normal_words, W, alg, rw, P.P2 if alg.W.assoc else 2):
        for p in safely(roots_of, W, alg, rw, {word: Fr(1)}):
            for x in p:
                if x[2] is not None and x[2] not in fields:
                    fields.append(x[2])
    for c in fields:
        W.th_c = c
        for maxd in range(0, P.S + 1):
            tree = build(W, kept, [], W.names, 0, maxd)
            if tree is not None:
                cert = {"theta": theta_of(c), "tree": tree}
                if C.safe(C.check_refutation, cert, winfo, sorted(d))[0]:
                    return cert, n_root
            if time.time() > W.t_end:
                return None, n_root
    return None, n_root


def study(label, root, out_dir):
    rows = []
    for batch in "AB":
        key = json.load(open(os.path.join(root, f"batch_{batch}", "key", "key.json"), encoding="utf-8"))
        outs = json.load(open(os.path.join(out_dir, f"outputs_{batch}.json"), encoding="utf-8"))
        for e in key:
            wid = e["id"]
            path = os.path.join(root, f"batch_{batch}", "worlds", f"{wid}.json")
            winfo = C.world_info(C.R.load(path))
            world = json.load(open(path, encoding="utf-8"))
            mine = (outs.get(wid) or {}).get("procedure", {}).get("refutations") or []
            for r in e.get("refutations") or []:
                d = r["drop"]
                sealed = any(C.safe(C.check_refutation, m["proof"], winfo, sorted(d))[0] for m in mine)
                W = P.World(world, time.time() + BUDGET)
                W.th_c = None
                W.move_cache = {}
                t0 = time.time()
                try:
                    cert, n_root = refute(W, set(W.U) - set(d), d, winfo)
                except Exception as ex:
                    cert, n_root = None, f"ERROR {type(ex).__name__}: {ex}"
                row = {"set": label, "batch": batch, "world": wid, "drop": d, "root": r["proof"]["tree"]["node"],
                       "sealed": sealed, "built": cert is not None, "moves": n_root,
                       "seconds": round(time.time() - t0, 1)}
                rows.append(row)
                print(json.dumps(row), flush=True)
    return rows


def summary(rows):
    for label in sorted({r["set"] for r in rows}):
        for kind, roots in (("case node at the root", ("split", "inverse")), ("no case node", ("close", "positive"))):
            rs = [r for r in rows if r["set"] == label and r["root"] in roots]
            ms = [r["moves"] for r in rs if isinstance(r["moves"], int)]
            print(f"{label}, {kind}: {len(rs)} proofs; sealed procedure reached {sum(r['sealed'] for r in rs)}; "
                  f"builder reached {sum(r['built'] for r in rs)}; "
                  f"builder only {sum(r['built'] and not r['sealed'] for r in rs)}; "
                  f"sealed only {sum(r['sealed'] and not r['built'] for r in rs)}; neither "
                  f"{sum(not r['sealed'] and not r['built'] for r in rs)}; moves at the root: "
                  f"max {max(ms) if ms else None}, mean {sum(ms) / len(ms) if ms else 0:.1f}; "
                  f"mean seconds {sum(r['seconds'] for r in rs) / len(rs) if rs else 0:.1f}", flush=True)


if __name__ == "__main__":
    rows = study("test 5", T5, os.path.join(ROOT, "dev", "check_t5"))
    rows += study("test 5b", ROOT, os.path.join(ROOT, "results"))
    summary(rows)
