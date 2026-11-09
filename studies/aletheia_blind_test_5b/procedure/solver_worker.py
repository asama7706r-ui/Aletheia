"""A worker process for exact solving, so that a hard time limit can kill a sympy call that does not stop.
Tasks (lists of equation strings and unknown names):
  ("modp", eqs, names, p): the reduced Groebner basis modulo the prime p (grevlex): "one" if it is [1], else "some".
  ("exact", eqs, names):   over the rationals: "none" if the Groebner basis is [1], else the solutions of sympy's
                           solve on the lex basis, as {name: srepr(value)} (values may contain free unknowns)."""


def work(conn):
    import sympy as sp
    while True:
        task = conn.recv()
        if task is None:
            return
        kind = task[0]
        try:
            syms = [sp.Symbol(n) for n in task[2]]
            loc = {n: s for n, s in zip(task[2], syms)}
            eqs = [sp.sympify(e, locals=loc) for e in task[1]]
            if kind == "modp":
                eqs = [sp.fraction(sp.together(e))[0] for e in eqs]
                G = sp.groebner(eqs, *syms, order="grevlex", modulus=task[3])
                conn.send(("ok", "one" if list(G.exprs) == [1] else "some"))
            else:
                G = sp.groebner(eqs, *syms, order="lex")
                if list(G.exprs) == [1]:
                    conn.send(("ok", "none"))
                    continue
                sols = sp.solve(list(G.exprs), syms, dict=True)
                conn.send(("ok", [{str(k): sp.srepr(v) for k, v in s.items()} for s in sols]))
        except Exception as e:  # noqa: BLE001  (reported to the caller)
            conn.send(("error", f"{type(e).__name__}: {e}"))
