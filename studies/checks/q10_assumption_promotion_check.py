"""Q10 / 7.7 marks check (2026-10-14): when does an assumption become proven?

The user's test: hypothesis H1 comes from law L1 and unexpectedly connects to
law L2. Is that a gap-free proof, or support only? And hypothesis H2 comes
from L2 and is related to H1: what does that prove?

Method: tiny worlds. Every quantity takes a value in Z/7 (a field, so the
algebra is ordinary). A law, an observation or a hypothesis is a condition
on a world. "G proves F" means: every world that satisfies G satisfies F.
This is exactly checkable by enumeration.

For each fact F the script computes its ATMS-style label: the smallest sets
S of hypotheses such that (laws + observations + S) proves F. The ledger's
"zero test" (blueprint 1.11 item 1, 3.9 rule 4) asks whether the empty set
is in the label, i.e. whether F follows with every hypothesis removed.

Part E checks the coincidence rule of the information-checker page,
section 5: a numerical match counts as evidence only if its precision bits
exceed the description bits of the formula plus the log of the number of
formulas tried. Test case: 6*pi^5 against the proton/electron mass ratio.
(A first version of this script forgot the "tries" term; fixed 2026-10-14.)

Standard library only.
"""
from itertools import product
from math import pi, e, log2, sqrt
import random

P = 7


def worlds(names):
    for vals in product(range(P), repeat=len(names)):
        yield dict(zip(names, vals))


def proves(names, premises, fact):
    return all(fact(w) for w in worlds(names) if all(c(w) for c in premises))


def consistent(names, premises):
    return any(all(c(w) for c in premises) for w in worlds(names))


def count(names, premises):
    return sum(1 for w in worlds(names) if all(c(w) for c in premises))


def label(names, roots, hyps, fact):
    """Smallest hypothesis sets S (by inclusion) with roots + S proving fact."""
    found = []
    keys = list(hyps)
    for k in range(len(keys) + 1):
        for i in range(1 << len(keys)):
            S = [keys[j] for j in range(len(keys)) if i >> j & 1]
            if len(S) != k or any(set(f) <= set(S) for f in found):
                continue
            prem = roots + [hyps[h] for h in S]
            if consistent(names, prem) and proves(names, prem, fact):
                found.append(tuple(S))
    return found


def show(name, lab):
    txt = " or ".join("{" + ",".join(s) + "}" for s in lab) or "none"
    zero = "PASSES (proven)" if () in lab else "fails (rests on hypotheses)"
    print(f"    label({name}) = {txt:28s} zero test {zero}")


# ---------- Part A: H1 predicts something in L2's domain (one-way link) ----
print("Part A: H1 (from L1) predicts an observation in L2's domain")
V = ["p", "q", "r", "s", "t"]
L1 = lambda w: w["q"] == (w["p"] + w["r"]) % P          # output = input + hidden r
H1 = lambda w: w["r"] == 0                               # assumption: no hidden term
L2 = lambda w: w["s"] == ((w["q"] - w["p"]) * w["t"]) % P  # other domain, factor t
O = lambda w: w["s"] == 0                                # observed in L2's domain
assert proves(V, [L1, H1, L2], O)                        # H1 predicts O: "connection"
show("H1", label(V, [L1, L2, O], {"H1": H1}, H1))
bad = count(V, [L1, L2, O, lambda w: w["r"] != 0])
print(f"    worlds where L1, L2 and O all hold but H1 is false: {bad}")
n0, n1 = count(V, [L1, L2]), count(V, [L1, L2, O])
h0, h1 = count(V, [L1, L2, H1]), count(V, [L1, L2, O, H1])
print(f"    share of worlds with H1 true: before O {h0}/{n0}, after O {h1}/{n1}"
      "  (illustration only; blueprint 3.11: shares never decide)")
assert bad > 0

# ---------- Part B: the link can be reversed (L2 with O leads back to H1) ---
print("Part B: same, but L2's factor is a known nonzero number (3)")
L2b = lambda w: w["s"] == ((w["q"] - w["p"]) * 3) % P
show("H1", label(V, [L1, L2b, O], {"H1": H1}, H1))
assert proves(V, [L1, L2b, O], H1)

# ---------- Part C: H2 comes from L2 and is tied to H1 --------------------
print("Part C: H2 (from L2) and H1 (from L1) are tied by the laws")
V = ["p", "q", "r", "s", "u"]
L2c = lambda w: w["s"] == (w["q"] - w["p"] + w["u"]) % P  # L2 with its own hidden u
H2 = lambda w: w["u"] == 0
R = [L1, L2c, O]
hyps = {"H1": H1, "H2": H2}
show("H1", label(V, R, hyps, H1))
show("H2", label(V, R, hyps, H2))
iff = lambda w: H1(w) == H2(w)
show("H1<->H2", label(V, R, hyps, iff))
both_false = count(V, R + [lambda w: not H1(w), lambda w: not H2(w)])
print(f"    worlds where the laws and O hold and BOTH hypotheses are false: {both_false}")
assert proves(V, R, iff) and not proves(V, R, H1) and both_false > 0
# the exit from the circle: a second, independent observation
O2 = lambda w: (w["r"] + 2 * w["u"]) % P == 0           # another instrument
show("H1 with O2", label(V, R + [O2], hyps, H1))
assert proves(V, R + [O2], H1)

# ---------- Part D: H2' conflicts with H1 ---------------------------------
print("Part D: H2' (from L2) says u = 1")
H2x = lambda w: w["u"] == 1
notboth = lambda w: not (H1(w) and H2x(w))
show("not(H1 and H2')", label(V, R, {"H1": H1, "H2'": H2x}, notboth))
assert proves(V, R, notboth)

# ---------- Part E: an "unexpected" numerical match by chance -------------
print("Part E: coincidence rule (information-checker page, section 5)")
ratio = 1836.15267343      # proton/electron mass ratio (CODATA 2018)
guess = 6 * pi ** 5
rel = abs(ratio - guess) / ratio
forms = [(k, a, b, c) for k in range(1, 11) for a in range(-6, 7)
         for b in range(-6, 7) for c in range(-4, 5)]
vals = sorted(k * pi ** a * e ** b * sqrt(2) ** c for k, a, b, c in forms)
prec_bits, desc_bits = -log2(rel), log2(len(forms))
tries_bits = log2(len(forms))      # if the whole family was searched
print(f"    6*pi^5 = {guess:.6f}, ratio = {ratio}, relative gap {rel:.2e}")
print(f"    precision bits {prec_bits:.1f}; description bits {desc_bits:.1f}"
      f" ({len(forms)} formulas k*pi^a*e^b*sqrt2^c)")
print(f"    rule: precision > description + log2(tries) -> {prec_bits:.1f} >"
      f" {desc_bits + tries_bits:.1f}? {prec_bits > desc_bits + tries_bits}"
      f"  (without counting tries: {prec_bits > desc_bits})")
rng = random.Random(14)


def best(target):
    import bisect
    i = bisect.bisect_left(vals, target)
    cand = [vals[j] for j in (i - 1, i) if 0 <= j < len(vals)]
    return min(abs(v - target) / target for v in cand)


targets = [10 ** rng.uniform(0, 4) for _ in range(500)]
hits = sum(best(x) <= rel for x in targets)
print(f"    random targets in [1, 10000] matched at least as well: {hits}/500")
assert prec_bits < desc_bits + tries_bits and hits > 0
