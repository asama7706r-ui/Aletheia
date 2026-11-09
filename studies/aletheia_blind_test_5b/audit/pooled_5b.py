# Pooled numbers over both batches (protocol 8.4: "the pooled numbers are published too").
# The sealed scorer prints per-batch numbers only; this reads its two reports.
import json
from math import comb

W = []
for b in "AB":
    r = json.load(open(f"results/report_{b}.json"))
    W += list(r["worlds"].values())
n = len(W)
branchy = [w for w in W if w["truth"][0] in ("NEW_KIND", "BRANCHES", "NO_WITNESS")]
print(f"worlds {n}")
print(f"verdict accuracy {sum(w['verdict_ok'] for w in W)}/{n}")
print(f"drop-set accuracy {sum(w['drop_ok'] for w in branchy)}/{len(branchy)}")
print(f"marks accuracy {sum(w['marks_ok'] for w in branchy)}/{len(branchy)}")
d = sum(w["decision_ok"] for w in W)
print(f"decision accuracy {d}/{n}")
for k in W[0]["baselines"]:
    a = sum(w["baselines"][k] for w in W)
    b = sum(w["decision_ok"] and not w["baselines"][k] for w in W)
    c = sum((not w["decision_ok"]) and w["baselines"][k] for w in W)
    p = sum(comb(b + c, i) for i in range(b, b + c + 1)) / 2 ** (b + c) if b + c else 1.0
    print(f"baseline {k}: decision {a}/{n}, b={b}, c={c}, one-sided McNemar p={p:.4f}")
