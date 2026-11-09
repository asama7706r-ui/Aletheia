"""Workshop search study, stage 1b: non-associative witnesses, shape first.

The basis is a set of bracketed words (trees) closed under subterms: the shape. A product of two basis words is
fixed when it is itself a basis word, and unknown otherwise (a combination of smaller basis words). The role,
the kept equational units (q6 as symmetry of the table; for k02, E*E = -1 and the kept copies with the old
variable set to E) and, when q12 or q13 is kept, the quadratic-algebra form that the sealed procedure's
certificate method needs (b_i*b_i in span(1, b_i); b_i*b_j + b_j*b_i in span(1, b_i, b_j)) become equations in
the unknowns, solved exactly. Every witness found is checked by the sealed checker.
Limits: rational solutions only; the certificate method of the sealed procedure (quadratic algebras) only."""
import itertools
import time
from fractions import Fraction as Fr

import sympy as sp

import shape_search as SS
from shape_search import P, CHK


def tkey(t):
    return (deg(t), repr(t))


def deg(t):
    return 0 if t == () else (1 if isinstance(t, str) else deg(t[0]) + deg(t[1]))


def tree_shapes(alphabet, n):
    out = []

    def grow(S, last):
        if len(S) == n:
            out.append(sorted(S, key=tkey))
            return
        cands = {g for g in alphabet if g not in S}
        cands |= {(a, b) for a in S for b in S if a != () and b != () and (a, b) not in S}
        for w in sorted(cands, key=tkey):
            if tkey(w) > last:
                grow(S | {w}, tkey(w))
    grow({()}, tkey(()))
    return out


def search(world, drop, nmax=5, deadline=None, tries=(0, 1, -1, 2, -2), max_points=400):
    b = world["builds"][0]
    origin, frames = b["origin"], list(b["frames"])
    gens = sorted(b["generators"])
    info = CHK.world_info(world)
    U = [u for u in P.UNITS[origin] if not ("f03" in frames and u in P.Q5F)]
    kept = set(U) - set(drop)
    if "q14" in kept:
        return None, {"skipped": "q14 kept"}
    alphabet = (["e1"] if origin == "k02" else []) + gens
    atoms = P.read_role(b)
    import shape_driver as D
    deadline = deadline or (time.time() + 3600)
    rep = {"bound": 1, "partial": None, "shapes": 0, "unresolved": 0}
    for n in range(2, nmax + 1):
        if time.time() > deadline:
            rep["stopped"] = "time"
            return None, rep
        items, ctx = [], []
        for S in tree_shapes(alphabet, n):
            idx = {w: i for i, w in enumerate(S)}
            unk = []
            T = {}
            for i, s in enumerate(S[1:], 1):
                for j, t in enumerate(S[1:], 1):
                    w = (s, t)
                    v = [0] * n
                    if w in idx:
                        v[idx[w]] = 1
                    else:
                        for k, u in enumerate(S):
                            if tkey(u) < tkey(w):
                                x = sp.Symbol(f"t_{i}_{j}_{k}")
                                unk.append(x)
                                v[k] = x
                    T[(i, j)] = v
            gval = {}
            for g in alphabet:
                if g in idx:
                    gval[g] = [1 if k == idx[g] else 0 for k in range(n)]
                else:
                    x = sp.Symbol(f"g_{g}")
                    unk.append(x)
                    gval[g] = [x] + [0] * (n - 1)
            def mul(a, c, T=T, n=n):
                out = [0] * n
                for i in range(n):
                    if a[i] == 0:
                        continue
                    for j in range(n):
                        if c[j] == 0:
                            continue
                        if i == 0:
                            out[j] += a[i] * c[j]
                        elif j == 0:
                            out[i] += a[i] * c[j]
                        else:
                            for k in range(n):
                                out[k] += a[i] * c[j] * T[(i, j)][k]
                return [sp.expand(x) for x in out]

            def term(ast, agree):
                t = ast[0]
                if t in ("num", "frac"):
                    c = sp.Integer(ast[1]) if t == "num" else sp.Rational(ast[1], ast[2])
                    return [c] + [0] * (n - 1)
                if t == "name":
                    return list(gval[ast[1]])
                if t == "neg":
                    return [-x for x in term(ast[1], agree)]
                if t == "sum":
                    out = [0] * n
                    for x in ast[1]:
                        out = [a + c for a, c in zip(out, term(x, agree))]
                    return out
                vals = [term(x, agree) for x in ast[1]]
                if len(vals) == 2:
                    return mul(vals[0], vals[1])
                brs = P.bracketings(vals, mul)
                for x in brs[1:]:
                    agree.append([a - c for a, c in zip(brs[0], x)])
                return brs[0]
            eqs, ineqs = [], []
            for op, l, r in atoms:
                ag = []
                d = [a - c for a, c in zip(term(l, ag), term(r, ag))]
                for x in ag:
                    eqs += x
                (eqs if op == "=" else ineqs).extend([d] if op != "=" else d)
            E = gval.get("e1")
            if origin == "k02":
                eqs += [a + (1 if k == 0 else 0) for k, a in enumerate(mul(E, E))]
            basis = [[1 if k == i else 0 for k in range(n)] for i in range(n)]
            if "q6" in kept:
                for i in range(1, n):
                    for j in range(i + 1, n):
                        eqs += [a - c for a, c in zip(T[(i, j)], T[(j, i)])]
            if origin == "k02":
                m = mul
                for u in sorted(kept & set(P.COPIES)):
                    for x, y, z in itertools.product(basis, repeat=3):
                        lhs, rhs = {
                            "q5[onn]": (m(m(E, y), z), m(E, m(y, z))), "q5[non]": (m(m(x, E), z), m(x, m(E, z))),
                            "q5[nno]": (m(m(x, y), E), m(x, m(y, E))), "q5[oon]": (m(m(E, E), z), m(E, m(E, z))),
                            "q5[ono]": (m(m(E, y), E), m(E, m(y, E))), "q5[noo]": (m(m(x, E), E), m(x, m(E, E))),
                            "q6[on]": (m(E, y), m(y, E))}[u]
                        eqs += [a - c for a, c in zip(lhs, rhs)]
            if "q5" in kept:
                for x, y, z in itertools.product(basis[1:], repeat=3):
                    eqs += [a - c for a, c in zip(mul(mul(x, y), z), mul(x, mul(y, z)))]
            if "q12" in kept or "q13" in kept:
                for i in range(1, n):
                    eqs += [T[(i, i)][k] for k in range(1, n) if k != i]
                    for j in range(i + 1, n):
                        s = [a + c for a, c in zip(T[(i, j)], T[(j, i)])]
                        eqs += [s[k] for k in range(1, n) if k not in (i, j)]
            items.append((len(ctx), eqs, unk))
            ctx.append((S, T, gval, ineqs))
        rep["shapes"] += len(items)

        def finish(i, full, n=n):
            S, T, gval, ineqs = ctx[i]
            if any(all(sp.sympify(a).subs(full) == 0 for a in q) for q in ineqs):
                return None
            w = make_witness(T, gval, full, n, info, drop, origin, gens, kept)
            if w is not None:
                rep["shape"] = [repr(s) for s in S]
            return w
        w, st = D.drive(items, deadline, finish, tries=tries, max_points=max_points)
        rep["unresolved"] += st["unresolved"]
        if w is not None:
            rep["found_at"] = n
            return w, rep
        if st["unresolved"] and rep["partial"] is None:
            rep["partial"] = n
        if rep["partial"] is None:
            rep["bound"] = n
    return None, rep


def make_witness(T, gval, full, n, info, drop, origin, gens, kept):
    def fr(x):
        x = sp.Rational(sp.sympify(x).subs(full))
        return Fr(int(x.p), int(x.q))
    table = {}
    for (i, j), v in T.items():
        for k in range(n):
            c = fr(v[k])
            if c:
                table[(i, j, k)] = c
    gv = {g: [fr(x) for x in gval[g]] for g in gval}
    tpl = {"n": n, "table": table, "gens": gv}
    w = {"dim": n, "table": [[i, j, k, P.fs(c)] for (i, j, k), c in sorted(table.items())], "theta": None,
         "gens": {g: [P.fs(x) for x in gv[g]] for g in gens}, "q12": None, "q13": None}
    if origin == "k02":
        w["E"] = [P.fs(x) for x in gv["e1"]]
    if n > 1 and ("q12" in kept or "q13" in kept):
        cert = P.quadratic_norm(tpl)
        if cert is None:
            return None
        w["q12" if "q12" in kept else "q13"] = cert
    ok, _ = CHK.safe(CHK.check_witness, w, info, sorted(drop))
    return w if ok else None
