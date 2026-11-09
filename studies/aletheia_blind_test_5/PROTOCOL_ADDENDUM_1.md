# Aletheia blind test 5 - protocol addendum 1: clarifications (2026-10-23)

Status: written after the seal of 2026-10-23T09:45:35Z and before any test world exists, in answer to the notes of the batch A generator (`key/generator_notes.md`). It is sealed by its SHA-256, published on the Notion test page before generation resumes.

**It changes no sealed file and no rule.** Every point below states what the sealed checker (`scorer/certs_v5.py`, `scorer/validate_v5.py`) already does, where `protocol_v5.md` left it unwritten. Where this addendum and the sealed code differ, the sealed code decides. Both generators read this addendum as part of the protocol.

## A1. A refutation in JSON (Section 4.4)
```
REFUTATION = {"theta": θ | null, "tree": NODE}          θ as in 4.1; it fixes F for every coefficient in the tree
NODE = {"node": "close",    "target": {"const": F-element} | {"ineq": k}, "terms": TERMS}
     | {"node": "positive", "t": [element, ...], "c": F-element, "terms": TERMS}
     | {"node": "split",    "by": "q12" | "q14", "a": element, "b": element, "proof_ab": TERMS, "children": [NODE, NODE]}
     | {"node": "inverse",  "a": element, "v": name, "children": [NODE, NODE]}
TERMS = [[coef, relator, path], ...]                     coef: an F-element
relator = {"ctx": i} | {"unit": u, "args": {variable: element, ...}}
path = [["L" | "R", element], ...]
element = [[coef, word], ...]        word = "1" | name | [word, word]
F-element = a fraction string, or (with θ) a list of d fraction strings, the coefficients of 1, θ, ..., θ^(d-1)
```
- **The node type** is the field `"node"`.
- **`close`:** `{"const": c}` is a constant c certified nonzero (Section 4.1); `{"ineq": k}` is the context's inequation number k. The terms must sum exactly to the target.
- **`proof_ab`** has the form of `terms`, and its sum must equal a*b exactly in the ambient algebra.
- **`inverse`:** `"v"` is the fresh name: a valid name that is not a generator, not `e1`, and not an earlier `v` on the path. Only the second child may use it.
- **Coefficients** are any elements of F. They are not limited to {-1, 0, 1}; that limit belongs to the reference's search only (Section 8.1).
- **Where refutations go:** in the key, `{"drop": [...], "proof": REFUTATION}` (Section 5). The optional `"refutations"` list of an output (4.7) has items of the same form `{"drop", "proof"}`. A branch's `"proofs"` maps a unit u to a REFUTATION of the candidate D \ {u}.

## A2. The numbering of relators (Section 4.4, item 1)
- **Chains:** only a product of three or more factors written without brackets is a chain. A sum never adds a relator, whatever its length: addition is fixed in W.
- **Order:** for each role sentence in file order, equations and inequations alike, the checker reads the left side, then the right side. Inside a side, the factors of a product are read before the product, so inner chains come first. For each chain it appends "first bracketing minus bracketing k", for k = 2, 3, ... in the order of Section 4.4. Then, for an equation, it appends left side minus right side.
- **The first bracketing** splits after the first factor at every level: a*(b*(c*d)). It is also the value the chain takes in "left side minus right side" and in an inequation.
- **Example** (origin `k01`, role `["x*y*z = x", "x*x*x != 0"]`, candidate `["q5", "q6"]`):
  - relator 0 = x*(y*z) − (x*y)*z;
  - relator 1 = x*(y*z) − x;
  - relator 2 = x*(x*x) − (x*x)*x (the chain of the inequation);
  - inequation 0 = x*(x*x).
  When q5 is kept, relators 0 and 2 are 0 in the ambient and keep their numbers.
- **Then** `e1*e1 + 1` for origin `k02`, and then the relators added by case nodes on the path. Each child of a case node extends its parent's list on its own, so both children of a split use the same next number.

## A3. Four refutations the sealed checker accepts
Checked by `dev/addendum1_examples.py` (exit 0), which also checks that broken copies are rejected. They show the format only; worlds are not to be modelled on them (Section 11).
- **E1, `positive`:** origin `k01`, role `["x*x = -1"]`, candidate `[]`. Relator 0 is x*x − (−1) = x*x + 1, a square plus a positive number.
```
{"theta": null, "tree": {"node": "positive", "t": [[["1", "x"]]], "c": "1", "terms": [["1", {"ctx": 0}, []]]}}
```
- **E2, `split` with a fraction coefficient:** origin `k01`, role `["x*x = 2", "x*y + y*x = 0", "y != 0"]`, candidate `["q14"]` (q6 and q12 kept). With q6, relator 1 is 2·x*y, so x*y = (1/2)·relator 1. Child 1 adds x (relator 2): relator 0 − relator 2·x = −2. Child 2 adds y (relator 2), which is inequation 0.
```
{"theta": null, "tree": {"node": "split", "by": "q12", "a": [["1", "x"]], "b": [["1", "y"]], "proof_ab": [["1/2", {"ctx": 1}, []]], "children": [{"node": "close", "target": {"const": "-2"}, "terms": [["1", {"ctx": 0}, []], ["-1", {"ctx": 2}, [["R", [["1", "x"]]]]]]}, {"node": "close", "target": {"ineq": 0}, "terms": [["1", {"ctx": 2}, []]]}]}}
```
- **E3, `inverse`:** origin `k01`, role `["t*t = 0", "t != 0"]`, candidate `["q12", "q14"]` (q5 and q13 kept). Child 1 adds t. Child 2 adds t*tv − 1 and tv*t − 1 (relators 1 and 2), and t = (t*t)*tv − t*(t*tv − 1).
```
{"theta": null, "tree": {"node": "inverse", "a": [["1", "t"]], "v": "tv", "children": [{"node": "close", "target": {"ineq": 0}, "terms": [["1", {"ctx": 1}, []]]}, {"node": "close", "target": {"ineq": 0}, "terms": [["1", {"ctx": 0}, [["R", [["1", "tv"]]]]], ["-1", {"ctx": 1}, [["L", [["1", "t"]]]]]]}]}}
```
- **E4, θ:** origin `k01`, role `["x*x = 2", "x*y = 0", "y != 0"]`, candidate `[]`, θ = √2. Split by q12 on (x − θ, x + θ), whose product is relator 0. Then y = (θ/2)·x*y ∓ (θ/2)·(x ∓ θ)*y in each child.
```
{"theta": {"poly": ["-2", "0", "1"], "lo": "1", "hi": "2"}, "tree": {"node": "split", "by": "q12", "a": [["1", "x"], [["0", "-1"], "1"]], "b": [["1", "x"], [["0", "1"], "1"]], "proof_ab": [["1", {"ctx": 0}, []]], "children": [{"node": "close", "target": {"ineq": 0}, "terms": [[["0", "1/2"], {"ctx": 1}, []], [["0", "-1/2"], {"ctx": 2}, [["R", [["1", "y"]]]]]]}, {"node": "close", "target": {"ineq": 0}, "terms": [[["0", "-1/2"], {"ctx": 1}, []], [["0", "1/2"], {"ctx": 2}, [["R", [["1", "y"]]]]]]}]}}
```

## A4. Mirror invariance (Section 2.7, item 3)
"Canonical sentences" means what the checker compares:
- each sentence becomes its operator plus the **unordered pair** of its two sides;
- each side is written in the reader's canonical form after **nested sums are flattened and their summands sorted**;
- products keep their order, and signs and constants are kept.

The role is mirror-invariant under σ when the set of these keys equals the set for the reversed role renamed by σ. Under this reading the example of Section 2.7 is mirror-invariant. A role whose sentence set maps onto itself literally also satisfies it.

## A5. Smaller points
1. **IMPOSSIBLE (4.6):** the checker recomputes the closure and checks only `"kind"`. `"detail"` is for the reader and is not checked.
2. **The matrix C of NORM and INV (4.3)** acts on coordinate columns in the basis b0, ..., b(n−1): C(x)_i = Σ_j C[i][j]·x_j.
3. **A witness with `"q12": NORM` and `"q13": null` keeps q13 too:** the checker uses the q12 certificate for q13 (4.3: x^-1 = C(x)/N(x)). Writing a certificate in `"q13"` as well is also accepted; it is then checked as INV.
4. **Undecided candidates (Section 8.1; brief, item 4):** give a witness or a refutation for every candidate you can decide. A candidate with neither stays undecided; when it is minimal it is a `no_witness` branch of the truth, and the key must list it so (V9). This is how NO_WITNESS worlds and `no_witness` branches arise. The validator prints at most the first 12 undecided candidates of a world, in sorted order: settle those that can be settled and run it again to see the rest.
5. **Notes to the project owner** describe a problem without quoting the role of a planned batch world. A role quoted in a note is not used in the batch, nor any renaming of it. This applies to the two probe roles quoted in batch A's notes of 2026-10-23.
6. **The reasoning effort of batch A (Section 0)** is set by the project owner in the app. The generator does not need to verify it.
