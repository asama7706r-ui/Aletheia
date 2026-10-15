# Is there a third branch for the demand z*0 + 0*z != 0: keep L, R, C (and
# associativity, units, 1 != 0) but drop additive negatives?
from itertools import product
def monoids(n, e):
    out = []
    for t in product(range(n), repeat=n*n):
        op = lambda a, b: t[a*n+b]
        if any(op(e, a) != a for a in range(n)): continue
        if any(op(a, b) != op(b, a) for a in range(n) for b in range(n)): continue
        if any(op(op(a, b), c) != op(a, op(b, c)) for a in range(n) for b in range(n) for c in range(n)): continue
        out.append(t)
    return out
for n in (2, 3):
    adds = monoids(n, 0); muls = monoids(n, 1)
    found = []
    for ta in adds:
        add = lambda a, b: ta[a*n+b]
        has_neg = all(any(add(a, b) == 0 for b in range(n)) for a in range(n))
        for tm in muls:
            mul = lambda a, b: tm[a*n+b]
            if any(mul(a, add(b, c)) != add(mul(a, b), mul(a, c)) for a in range(n) for b in range(n) for c in range(n)):
                continue
            zs = [z for z in range(n) if add(mul(z, 0), mul(0, z)) != 0]
            if zs:
                found.append((ta, tm, zs, has_neg))
    print(n, len(adds), len(muls), "solutions:", len(found), "with negatives:", sum(f[3] for f in found))
    if found:
        ta, tm, zs, hn = found[0]
        print("  example add", ta, "mul", tm, "z", zs)
