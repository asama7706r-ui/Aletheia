"""Post-hoc audit of blind test 1 (exploratory, NOT part of the sealed evidence).
Imports the frozen procedure read-only. Question: what signal made the procedure reject the
stricter family in each NEW_KIND world, and was that signal stated in the laws?"""
import json, os, sys
from fractions import Fraction
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "aletheia_blind_test_1")
sys.path.insert(0, os.path.join(ROOT, "procedure"))
import procedure_v1 as P

key = {k["id"]: k for k in json.load(open(os.path.join(ROOT, "key", "key.json"), encoding="utf-8"))}
RANK = {"comm": 0, "graded": 1, "assoc": 2}


def content_with_strings(world, ctx):
    out, seen = [], set()
    for law in world["laws"]:
        lhs_s, rhs_s = law.split("=")
        for side in (ctx.parse(lhs_s), ctx.parse(rhs_s)):
            stack = [side]
            while stack:
                x = stack.pop()
                if P.has_gen(x, ctx):
                    p = P.to_poly(x, ctx)
                    k = frozenset(p.items())
                    if p and k not in seen:
                        seen.add(k)
                        out.append((str(x), p))
                stack.extend(x.args)
    return out


def proportional(p, q):
    if set(p) != set(q):
        return False
    ratios = {p[m] / q[m] for m in p}
    return len(ratios) == 1


rows = []
for i in range(1, 29):
    wid = "E1-%02d" % i
    k = key[wid]
    if k["label"] != "NEW_KIND":
        continue
    world = json.load(open(os.path.join(ROOT, "worlds", wid + ".json"), encoding="utf-8"))
    pv = {p: Fraction(v) for p, v in k.get("true_parameter_values", {}).items()}
    ctx, relations, _c, n, D = P._prepare(world, pv or None)
    content = content_with_strings(world, ctx)
    A = P.TruncMold(n, relations, D)
    live = [(s, p) for s, p in content if P.alive(A, p)]
    observed = [(e, P.to_poly(ctx.parse(e), ctx)) for e in k.get("observed_nonzero", [])]
    literal = [e for e, q in observed if any(proportional(q, p) for _s, p in content)]
    print("=" * 90)
    print(wid, "truth:", k["true_family"], "| observed stated literally in laws: %d/%d %s"
          % (len(literal), len(observed), literal))
    decisive_stated = None
    for fam in ("comm", "graded"):
        if RANK[fam] >= RANK[k["true_family"]]:
            break
        if fam == "graded" and not any(ctx.grades):
            continue
        M = P.build_mold(fam, ctx, relations, D)
        if M.trivial():
            print("   %-6s: loud collapse (1 = 0)" % fam)
            continue
        dying = [s for s, p in live if not P.alive(M, p)]
        dying_obs = [e for e, q in observed if not P.alive(M, q)]
        stated = [e for e in dying_obs if e in literal]
        print("   %-6s: silent; law subterms that die: %d -> %s" % (fam, len(dying), dying[:6]))
        print("           observed quantities that die: %s ; of them stated in the laws: %s" % (dying_obs, stated))
        if decisive_stated is None:
            decisive_stated = bool(stated)
    sols = P.rational_solutions(relations, n)
    print("   rational solutions of the laws: %d" % len(sols))
    rows.append((wid, k["true_family"], len(literal), len(observed), decisive_stated))

print()
print("SUMMARY")
for r in rows:
    print("  %s %-6s observed stated %d/%d ; the first silent family is exposed by a STATED observed quantity: %s" % r)
