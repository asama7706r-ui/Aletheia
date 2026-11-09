#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Spot checks of seed_registry.json: every rule holds on a concrete model of its floor.

What it checks (exact fractions throughout, standard library only):
  1. the v0.5 reader accepts the seed, and prints its SHA-256;
  2. f01 (list v1): every sentence of every rule holds for every assignment of its
     variables from a pool of rationals, with the usual order. The rationals are an
     ordered field, like the reals, so a sentence of list v1 that fails here is
     miswritten. This is run twice, with 0^-1 = 0 and with 0^-1 = 5: q13 leaves the
     inverse of 0 free (Q10, D1), so both must pass;
  3. f02 (the complex list): the same on complex numbers with rational parts, and
     the relation of k02 holds for e1 = (0, 1);
  4. f03 (the frame): t1 holds on 2 x 2 rational matrices (actions on a plane,
     composed by the matrix product);
  5. negative controls: deliberately miswritten sentences must FAIL on the same
     models, so the checks above can see a writing error. Among them, a*b = b*a
     fails on the frame model: commutativity is not a frame theorem (trap 10).
A rule written by `keeps` (q2) says nothing about a kind taken by itself: inside its
own kind the old elements are all the elements. It is reported, not evaluated.
These are spot checks over finite pools, not proofs. The truth of list v1 for the
reals is textbook; this script guards the WRITING of the seed, as check_cards.py
did for the test-4 registry.
Usage: python check_seed.py   (exit 0 = all checks passed)
"""
import itertools
import json
import os
import sys
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lang"))
import reader_v0 as R  # noqa: E402


# ----------------------------------------------------------------- models

class Reals:
    """Rationals with the usual order; 0^-1 is a chosen value (the list leaves it free)."""
    ordered = True

    def __init__(self, inv0):
        self.inv0 = F(inv0)
        self.name = f"rationals, 0^-1 = {inv0}"

    def num(self, n):
        return F(n)

    def frac(self, n, d):
        return F(n, d)

    def add(self, x, y):
        return x + y

    def mul(self, x, y):
        return x * y

    def neg(self, x):
        return -x

    def inv(self, x):
        return 1 / x if x != 0 else self.inv0

    def gt(self, x, y):
        return x > y


class Complex:
    """Pairs (re, im) of rationals; no order."""
    ordered = False

    def __init__(self, inv0):
        self.inv0 = (F(inv0[0]), F(inv0[1]))
        self.name = f"complex numbers with rational parts, 0^-1 = {inv0}"

    def num(self, n):
        return (F(n), F(0))

    def frac(self, n, d):
        return (F(n, d), F(0))

    def add(self, x, y):
        return (x[0] + y[0], x[1] + y[1])

    def mul(self, x, y):
        return (x[0] * y[0] - x[1] * y[1], x[0] * y[1] + x[1] * y[0])

    def neg(self, x):
        return (-x[0], -x[1])

    def inv(self, x):
        n = x[0] * x[0] + x[1] * x[1]
        return (x[0] / n, -x[1] / n) if n != 0 else self.inv0

    def gt(self, x, y):
        raise ValueError("the complex model has no order")


class Matrices:
    """2 x 2 rational matrices: actions on a plane, composed by the product."""
    ordered = False
    name = "2 x 2 rational matrices"

    def num(self, n):
        return ((F(n), F(0)), (F(0), F(n)))

    def frac(self, n, d):
        return self.num(F(n, d))

    def add(self, x, y):
        return tuple(tuple(x[i][j] + y[i][j] for j in range(2)) for i in range(2))

    def mul(self, x, y):
        return tuple(tuple(sum(x[i][k] * y[k][j] for k in range(2)) for j in range(2)) for i in range(2))

    def neg(self, x):
        return tuple(tuple(-e for e in row) for row in x)

    def inv(self, x):
        raise ValueError("t1 uses no inverse")

    def gt(self, x, y):
        raise ValueError("the matrix model has no order")


REAL_POOL = [F(0), F(1), F(-1), F(2), F(1, 2), F(-3, 4), F(5, 3), F(-7)]
CPLX_POOL = [(F(a), F(b)) for a, b in
             [(0, 0), (1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (F(1, 2), -2), (-3, F(1, 3))]]


def m(a, b, c, d):
    return ((F(a), F(b)), (F(c), F(d)))


MAT_POOL = [m(1, 0, 0, 1), m(0, 1, 0, 0), m(0, 0, 1, 0), m(1, 2, 3, 4), m(0, -1, 1, 0),
            m(2, 0, 0, F(1, 2)), m(1, 1, 0, 1), m(-3, F(1, 2), 5, 0)]


# ----------------------------------------------------------------- evaluation

def values(node, env, M):
    """The set of values of a term. A chain (3 or more factors or terms with no brackets)
    gives the values of all its bracketings; one value means they all agree."""
    t = node[0]
    if t == "num":
        return {M.num(node[1])}
    if t == "frac":
        return {M.frac(node[1], node[2])}
    if t == "name":
        return {env[node[1]]}
    if t == "neg":
        return {M.neg(x) for x in values(node[1], env, M)}
    if t == "inv":
        return {M.inv(x) for x in values(node[1], env, M)}
    if t in ("sum", "prod"):
        op = M.add if t == "sum" else M.mul
        items = [values(x, env, M) for x in node[1]]
        memo = {}

        def span(i, j):
            if j - i == 1:
                return items[i]
            if (i, j) not in memo:
                memo[(i, j)] = {op(x, y) for k in range(i + 1, j) for x in span(i, k) for y in span(k, j)}
            return memo[(i, j)]
        return span(0, len(items))
    raise ValueError(node)


def atom_holds(node, env, M):
    _, op, lhs, rhs = node
    left, right = values(lhs, env, M), values(rhs, env, M)
    if len(left) != 1 or len(right) != 1:     # a chain whose bracketings disagree
        return False
    (x,), (y,) = left, right
    if op == "=":
        return x == y
    if op == "!=":
        return x != y
    return M.gt(x, y)


def sentence_holds(ast, env, M):
    _, prem, concl = ast
    return not all(atom_holds(a, env, M) for a in prem) or any(atom_holds(a, env, M) for a in concl)


def counterexample(sentence, names, pool, M, fixed=None):
    """The first assignment from the pool that breaks the sentence, or None."""
    ast = R.parse_sentence(sentence)[0]
    free = sorted(names)
    for combo in itertools.product(pool, repeat=len(free)):
        env = dict(zip(free, combo))
        env.update(fixed or {})
        if not sentence_holds(ast, env, M):
            return env
    return None


# ----------------------------------------------------------------- checks

def main():
    failures = 0
    path = os.path.join(HERE, "seed_registry.json")
    with open(path, encoding="utf-8") as fh:
        seed = json.load(fh)
    ctx, info = R.check_registry(seed, "seed_registry.json")
    if ctx.errors:
        for e in ctx.errors:
            print("FAIL ", e)
        return 1
    print(f"ok    the v0.5 reader accepts the seed; sha256 {R.sha256_of(info['canon'])}")

    floors = {f["id"]: f for f in seed["floors"]}
    plan = [("f01", Reals(0), REAL_POOL), ("f01", Reals(5), REAL_POOL),
            ("f02", Complex((0, 0)), CPLX_POOL), ("f02", Complex((3, 4)), CPLX_POOL),
            ("f03", Matrices(), MAT_POOL)]
    for fid, M, pool in plan:
        n_sent = n_cases = 0
        for r in floors[fid]["rules"]:
            if r["keeps"]:
                continue
            for s in r["sentences"]:
                names = set(r["vars"])
                bad = counterexample(s, names, pool, M)
                n_sent += 1
                n_cases += len(pool) ** len(names)
                if bad is not None:
                    failures += 1
                    print(f"FAIL  {fid} {r['id']}: {s!r} breaks at {bad} on {M.name}")
        keeps = [r["id"] for r in floors[fid]["rules"] if r["keeps"]]
        print(f"ok    {fid} on {M.name}: {n_sent} sentences hold in {n_cases} assignments"
              + (f" ({', '.join(keeps)} written by keeps: not evaluated on the kind itself)" if keeps else ""))

    # the relation of k02 holds for e1 = (0, 1), and fails for a wrong choice
    k02 = next(k for k in seed["kinds"] if k["id"] == "k02")
    C = Complex((0, 0))
    good = all(sentence_holds(R.parse_sentence(s)[0], {"e1": (F(0), F(1))}, C) for s in k02["relations"])
    wrong = all(sentence_holds(R.parse_sentence(s)[0], {"e1": (F(1), F(0))}, C) for s in k02["relations"])
    if good and not wrong:
        print("ok    k02: e1*e1 = -1 holds for e1 = (0, 1), and fails for e1 = (1, 0)")
    else:
        failures += 1
        print("FAIL  k02 relation")

    # negative controls: miswritten sentences must break somewhere on the same models
    controls = [
        ("f01", Reals(0), REAL_POOL, "(a + b) + c = a + (b + (-c))"),
        ("f01", Reals(0), REAL_POOL, "a*(b + c) = a*b + b*c"),
        ("f01", Reals(0), REAL_POOL, "(a + b)*c = a*c + b"),
        ("f01", Reals(0), REAL_POOL, "a + (-a) = 1"),
        ("f01", Reals(0), REAL_POOL, "a + 1 = a"),
        ("f01", Reals(0), REAL_POOL, "a*b = 0 -> a = 0"),
        ("f01", Reals(0), REAL_POOL, "a*a^-1 = 1"),
        ("f01", Reals(0), REAL_POOL, "a != 0 -> a*a^-1 = 0"),
        ("f01", Reals(0), REAL_POOL, "a > b -> b > a"),
        ("f01", Reals(0), REAL_POOL, "a > b -> a*c > b*c"),
        ("f01", Reals(0), REAL_POOL, "a > 0 | 0 > a"),
        ("f01", Reals(0), REAL_POOL, "a > 0 & b > 0 -> 0 > a*b"),
        ("f02", Complex((0, 0)), CPLX_POOL, "a*a = a -> a = 1"),
        ("f02", Complex((0, 0)), CPLX_POOL, "a*b = b*a + 1"),
        # not "a*a != 1 + 1": it is false on the complex numbers, but no number in a
        # rational pool squares to 2, so a pool cannot catch it (a limit of spot checks)
        ("f02", Complex((0, 0)), CPLX_POOL, "a*a != -1"),
        ("f03", Matrices(), MAT_POOL, "a*b = b*a"),
        ("f03", Matrices(), MAT_POOL, "(a*b)*c = a*(c*b)"),
    ]
    caught = 0
    for fid, M, pool, s in controls:
        names = R.parse_sentence(s)[1]
        if counterexample(s, names, pool, M) is not None:
            caught += 1
        else:
            failures += 1
            print(f"FAIL  negative control not caught on {fid}: {s!r}")
    print(f"ok    {caught} of {len(controls)} miswritten sentences break on the models"
          if caught == len(controls) else f"FAIL  {caught} of {len(controls)} negative controls caught")

    print("\nall checks passed" if failures == 0 else f"\n{failures} FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
