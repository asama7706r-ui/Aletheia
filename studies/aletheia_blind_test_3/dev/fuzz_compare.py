"""Differential test (development only): random small worlds, procedure vs independent reference.

For every random world that the reference can load, it compares the verdict, the sufficient set, every
reason set, every explanation interval and range, and checks the procedure's full output with the
scorer's proof checker. Random worlds are throwaway sanity checks, not test worlds.

Usage:  python fuzz_compare.py [n_worlds] [seed]
"""
import os
import random
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "procedure"))
sys.path.insert(0, os.path.join(HERE, "..", "scorer"))
import procedure_v3 as P  # noqa: E402
import ref_v3 as R  # noqa: E402


def rq(rng, lo=-6, hi=6, dens=(1, 2, 3, 4, 5, 10)):
    return Fraction(rng.randint(lo, hi), rng.choice(dens))


def s(v):
    return R.s(v)


def rand_term(rng, qs, consts):
    parts = []
    for q in qs:
        k = rng.choice([0, 0, 1, 1, 2, 3])
        if k:
            parts.append("%s**%d" % (q, k) if k > 1 else q)
    if consts and rng.random() < 0.5:
        parts.append(rng.choice(consts))
    body = "*".join(parts) if parts else "1"
    if rng.random() < 0.25 and qs:
        body = "(%s + %s)" % (body, rng.choice(qs))
    if rng.random() < 0.15 and qs:
        body = "%s/(1 + %s**2)" % (body, rng.choice(qs))
    return body


def rand_world(rng, i):
    nq = rng.choice([1, 2, 2, 3])
    qs = ["qa", "qb", "qc"][:nq]
    consts = {}
    for c in ["ka", "kb"][:rng.choice([0, 1, 2])]:
        consts[c] = {"value": s(Fraction(rng.randint(1, 9), rng.choice([1, 2, 5]))), "dims": {}}
    cn = list(consts)
    observers = {"oa": s(Fraction(rng.randint(0, 5), rng.choice([10, 20, 50]))),
                 "ob": s(Fraction(rng.randint(1, 10), rng.choice([10, 20])))}
    base = rand_term(rng, qs, cn)
    vis = None
    if rng.random() < 0.3:
        vis = {"id": "V1", "object": "oz", "term": rand_term(rng, qs, cn)}
    ledger = []
    for j in range(rng.choice([2, 3, 4])):
        cov = None
        r = rng.random()
        if r < 0.25:
            cov = {"ratio": rng.choice(qs) + ("**2" if rng.random() < 0.3 else ""),
                   "factor": {"type": "dimmer", "expr": rng.choice(["1/(1+r)", "r/(1+r)", "1/(1+r**2)"])}}
        elif r < 0.45:
            cov = {"ratio": rng.choice(qs) + "**2",
                   "factor": {"type": "switch", "on": rng.choice(["<", ">"]), "threshold": s(Fraction(rng.randint(1, 9), 2))}}
        co = "unknown" if rng.random() < 0.8 else {"exact": s(rq(rng))}
        ledger.append({"id": "R%d" % (j + 1), "object": "o%d" % j, "term": rand_term(rng, qs, cn),
                       "coefficient": co, "coverage": cov})
    syms = []
    if rng.random() < 0.25:
        q = rng.choice(qs)
        syms.append({"name": "m", "map": {q: "-" + q}})

    def state():
        return {q: s(rq(rng, -5, 5, (1, 2, 4))) for q in qs}
    # readings: base + random hidden contributions + noise, evaluated with the reference evaluator
    w = {"id": "F-%d" % i, "experiment": "A", "observable": "yy",
         "quantities": dict({"yy": {}}, **{q: {} for q in qs}), "constants": consts, "observers": observers,
         "base_law": "yy = " + base, "visible": vis, "ledger": ledger, "symmetries": syms,
         "old_observations": [], "new_observations": [], "possible_observations": []}
    names = set(qs) | set(cn)
    fb = R.Expr(base, names)
    hidden = [(R.Expr(rand_term(rng, qs, cn), names), rq(rng, -3, 3)) for _ in range(rng.choice([0, 1, 2]))]
    if rng.random() < 0.6:
        pick = rng.choice(ledger)
        hidden = [(R.Expr(pick["term"], names), rq(rng, -3, 3), pick)]
    vis_e = R.Expr(vis["term"], names) if vis else None
    mu = rq(rng, 1, 4)
    cvals = {c: Fraction(consts[c]["value"]) for c in cn}

    def reading(st, dom):
        env = dict(cvals)
        env.update({q: Fraction(v) for q, v in st.items()})
        y = fb.ev(env) + (mu * vis_e.ev(env) if vis_e else 0)
        if dom == "new" or (hidden and len(hidden[0]) == 3 and rng.random() < 0.3):
            for h in hidden:
                e, c = h[0], h[1]
                fac = Fraction(1)
                if len(h) == 3 and h[2]["coverage"] is not None:
                    cov = h[2]["coverage"]
                    rho = R.Expr(cov["ratio"], names).ev(env)
                    if cov["factor"]["type"] == "dimmer":
                        fac = R.Expr(cov["factor"]["expr"], {"r"}).ev({"r": rho})
                    else:
                        t = Fraction(cov["factor"]["threshold"])
                        fac = Fraction(1) if ((rho < t) if cov["factor"]["on"] == "<" else (rho > t)) else Fraction(0)
                y += c * e.ev(env) * fac
        y += Fraction(rng.randint(-3, 3), rng.choice([20, 50, 100]))
        return s(y)
    try:
        for _ in range(rng.choice([1, 2, 3, 4])):
            st = state()
            w["old_observations"].append({"state": st, "value": reading(st, "old"), "observer": rng.choice(["oa", "ob"])})
        for _ in range(rng.choice([1, 2, 3])):
            st = state()
            w["new_observations"].append({"state": st, "value": reading(st, "new"), "observer": rng.choice(["oa", "ob"])})
        for _ in range(rng.choice([2, 3])):
            w["possible_observations"].append({"state": state(), "observer": rng.choice(["oa", "ob"])})
    except R.Invalid:
        return None
    return w


def compare(w):
    try:
        rw = R.RWorld(w)
        a = R.analyse(rw)
    except R.Invalid:
        return "skip", None
    try:
        out = P.analyse(P.World(w))
    except P.WorldError as ex:
        return "mismatch", "procedure error %s (reference loaded)" % ex
    probs = []
    if R.norm_answer(out) != R.answer_of(a):
        probs.append("answer %s vs %s" % (R.norm_answer(out), R.answer_of(a)))
    else:
        ok, pp, listed = R.check_world_output(rw, a, out)
        nonsep = a["verdict"] == "FORK" and any(not ks for ks in R.separable_pairs(rw, a).values())
        if nonsep:
            pp = [x for x in pp if not x.startswith("invalid decisive set") and not x.startswith("decisive set does not")]
            if out.get("decisive") is not None:
                pp.append("decisive set given although a pair is not separable")
        if pp:
            probs.append("proof check: %s" % pp)
        for rid, rs in a["reasons"].items():
            if listed.get(rid, set()) != rs:
                probs.append("reasons %s: %s vs %s" % (rid, listed.get(rid), rs))
    return ("ok" if not probs else "mismatch"), probs


def main(n=2000, seed=7):
    rng = random.Random(seed)
    stats = {"ok": 0, "skip": 0, "mismatch": 0, "unbuilt": 0}
    verdicts = {}
    for i in range(n):
        w = rand_world(rng, i)
        if w is None:
            stats["unbuilt"] += 1
            continue
        st, info = compare(w)
        stats[st] += 1
        if st == "ok":
            v = P.analyse(P.World(w), proofs=False)["verdict"]
            verdicts[v] = verdicts.get(v, 0) + 1
        if st == "mismatch":
            print("MISMATCH", w["id"], info)
            if stats["mismatch"] > 10:
                break
    print(stats, verdicts)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2000, int(sys.argv[2]) if len(sys.argv) > 2 else 7)
