"""The common driver of the shape-first searches: hard time limits and the coarse "modulo a prime" pass.

For one dimension, every shape gives a system of equations. The coarse pass solves each system modulo a large
prime (fast). Shapes whose system has solutions modulo p go first to the exact solver; the others follow. No shape
is dropped: the coarse pass only orders the work, so the search stays complete. Each exact solve runs in a worker
process with a hard time limit; a shape whose solve times out is "unresolved", and the dimension is then reported
as searched only partly. Every candidate point is checked by the caller (the sealed checker decides)."""
import itertools
import multiprocessing as mp
import os
import sys
import time

import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solver_worker  # noqa: E402

PRIME = 1000003
MODP_TIMEOUT, EXACT_TIMEOUT = 5, 20


class Solver:
    def __init__(self):
        self.proc = self.conn = None

    def _start(self):
        ctx = mp.get_context("spawn")
        a, b = ctx.Pipe()
        self.proc = ctx.Process(target=solver_worker.work, args=(b,), daemon=True)
        self.proc.start()
        self.conn = a

    def call(self, task, timeout):
        if self.proc is None or not self.proc.is_alive():
            self._start()
        self.conn.send(task)
        if self.conn.poll(timeout):
            return self.conn.recv()
        self.proc.kill()
        self.proc.join()
        self.proc = None
        return ("timeout", None)


SOLVER = Solver()


def rational_points(sol, unk, tries, max_points):
    """Rational points of one solution family: free unknowns set to small integers."""
    vals = {k: sp.sympify(eval(v, sp.__dict__)) for k, v in sol.items()}  # noqa: S307 (srepr from our own worker)
    free = [x for x in unk if str(x) not in vals]
    count = 0
    for choice in itertools.product(tries, repeat=len(free)):
        count += 1
        if count > max_points:
            return
        sub = dict(zip(free, choice))
        full = {}
        ok = True
        for x in unk:
            v = vals.get(str(x))
            v = sp.nsimplify(v.subs(sub)) if v is not None else sp.Integer(sub.get(x, 0))
            if not v.is_Rational:
                ok = False
                break
            full[x] = v
        if ok:
            yield full


def drive(items, deadline, finish, tries=(0, 1, -1, 2, -2), max_points=200):
    """items: [(label, eqs, unknowns)] for one dimension. finish(label, point) -> witness or None.
    Returns (witness or None, {"resolved": k, "unresolved": u, "no_solution": z})."""
    stats = {"resolved": 0, "unresolved": 0, "no_solution": 0}
    prepared = []
    for label, eqs, unk in items:
        eqs = [e for e in (sp.expand(x) for x in eqs) if e != 0]
        prepared.append((label, eqs, unk))
    order = []
    for label, eqs, unk in prepared:
        if time.time() > deadline:
            break
        if not eqs:
            order.append((0, label, eqs, unk))
            continue
        r = SOLVER.call(("modp", [str(e) for e in eqs], [str(x) for x in unk], PRIME),
                        min(MODP_TIMEOUT, max(1, deadline - time.time())))
        rank = 0 if r == ("ok", "some") else (2 if r == ("ok", "one") else 1)
        order.append((rank, label, eqs, unk))
    order.sort(key=lambda x: x[0])
    for _rank, label, eqs, unk in order:
        if time.time() > deadline:
            stats["unresolved"] += 1
            continue
        if not eqs:
            sols = [{}]
        else:
            r = SOLVER.call(("exact", [str(e) for e in eqs], [str(x) for x in unk]),
                            min(EXACT_TIMEOUT, max(1, deadline - time.time())))
            if r[0] != "ok":
                stats["unresolved"] += 1
                continue
            if r[1] == "none":
                stats["no_solution"] += 1
                stats["resolved"] += 1
                continue
            sols = r[1]
        stats["resolved"] += 1
        for sol in sols:
            for pt in rational_points(sol, unk, tries, max_points):
                if time.time() > deadline:
                    stats["unresolved"] += 1          # this shape's points were not all tried
                    return None, stats
                w = finish(label, pt)
                if w is not None:
                    return w, stats
    return None, stats
