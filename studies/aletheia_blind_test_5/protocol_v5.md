# Aletheia blind test 5 - pre-registered protocol v5 (SEALED 2026-10-23)

Status: SEALED on 2026-10-23, with the seed and the code, after the project owner reviewed it (the Notion page «مسودة بروتوكول التجربة 5: ما يحتاج مراجعتك») and approved sealing. Written by the procedure author (Claude) on 2026-10-22; the last changes before sealing (2026-10-23) are the time limit and the text fixes listed on that page, section 4أ. The exact sealing time and the SHA-256 of every sealed file are in `SEALED_HASHES.txt`.
Sources:
- the Notion page «مسودة مواصفة التجربة 5: سلّم الصنف الجديد», decisions 1-17 in its section 12 (all approved, 2026-10-21 and 2026-10-22);
- its child page «مسودة بذرة التجربة 5» (the seed, approved 2026-10-22);
- the description language v0.5 (`lang/SPEC_v0.5.md`, `lang/reader_v0.py`);
- the Q10 page («السؤال 10»): list v1 (11.8), the decisions of 11.6, the four marks (7.7), the zero test (7.8, proposal 1), the merge step (13.5);
- the discussion page «ورشة الأمثلة» (2026-10-22), for the limits of the witness space.
Section 15 lists the choices made while writing this protocol. The project owner approved choices 1 and 2 (the two limits) on 2026-10-22; they are decisions 16 and 17 of the draft.

## 0. Roles, order and rules
- **Procedure author** (Claude): writes this protocol, `procedure/procedure_v5.py`, `scorer/ref_v5.py`, `scorer/certs_v5.py`, `scorer/baselines_v5.py`, `scorer/score_v5.py`, `scorer/validate_v5.py` and `tools/hash_files.py`. Develops them ONLY on the dev set (Section 12). Seals them before any test world exists.
- **Sealed inputs:**
  - `seed/seed_registry.json`, the tower (v0.5 registry), with `seed/seed_notes.md` (what each id means; the procedure never reads it) and `seed/check_seed.py`;
  - `lang/SPEC_v0.5.md` and `lang/reader_v0.py`.
- **Two world generators, two batches of 30 worlds each** (decisions 12, 12a, 12b):
  - **Batch A:** a separate Claude session, at its highest reasoning effort, with code execution.
  - **Batch B:** Gemini 4 Argon (decision 12), running locally on the project owner's machine with Python and file access (2026-10-22). The project owner starts it. Because it can reach the disk, it works in its own generator folder holding only the package, and it never opens any other folder. The exact model name is written in the batch's `progress.txt`.
  - Each generator reads ONLY this protocol and the files in `seed/`, `lang/` and `tools/`. It RUNS `scorer/validate_v5.py` (with the modules it imports and `scorer/dev_fingerprints.json`) but never reads the code in `scorer/`, so that its `key/verify_key.py` and its certificates stay independent of the reference (Section 13, item 10). It never reads the procedure, the dev folder, the results, earlier tests, any Notion page, or any memory files.
  - Each writes `worlds/W-01.json` ... `worlds/W-30.json` and `key/key.json` in its batch folder (`batch_A/`, `batch_B/`).
  - Each first writes its own verification code `key/verify_key.py` from this protocol alone, and its output `key/verify_output.txt`. Then it runs `python scorer/validate_v5.py .` inside its package folder (which is its batch folder) and repairs its files until the validator prints `VALID`.
  - Each reports the SHA-256 of every sealed file it received, computed by code, so that the run is known to use the sealed files.
- **The procedure author must not read any world or key before the SHA-256 of that batch's `results/outputs_X.json` is published.** Running the frozen procedure on the worlds is allowed. Nothing is debugged, repaired or changed after sealing.
- **Order:**
  1. Seal.
  2. Generate, verify, validate (each batch).
  3. Publish the hashes of the worlds and keys.
  4. Run `python procedure/procedure_v5.py run batch_X/worlds results/outputs_X.json` (the procedure reads the worlds folder only, never the key).
  5. Publish the outputs hash.
  6. Open the key. Run `python scorer/score_v5.py batch_X results/outputs_X.json results/report_X.json`.
  7. Publish the reports verbatim, then a separate audit.
- **Independence:** the scorer and the validator never import the procedure. They recompute the truth with their own code (`scorer/ref_v5.py`) and check every certificate by exact arithmetic (`scorer/certs_v5.py`). The procedure imports `scorer/certs_v5.py` only to check its own certificates before writing them; it never imports the reference, the baselines, the scorer or the validator. The reference searches by linear algebra on truncated ideals; the procedure by rewriting systems and templates (different methods, by the same author).
- The worlds stay unpublished until the project owner decides whether they will ever be shown to language models. Neither generator's model family is scored in any later comparison on these worlds.
- **Environment:** Python 3.12 with sympy 1.14 (Gröbner bases in the known-kind check, Section 2.8). Every number is an exact fraction; no floating point decides anything.

## 1. Claim under test
- **One claim** (decision 1; the seven items are one machine):
  - when a build asks for a kind that the old kind cannot hold, the procedure builds the new kind by the smallest relaxation, by containment, of the sealed list of old rules;
  - it gives every judged unit its mark, with a proof for every forced fall;
  - it never relaxes the two protected rules;
  - it builds a witness by itself for every branch it accepts, or says plainly that none was built;
  - when relaxations tie, it branches and states what decides between them, and it merges a false tie only with a checked translation;
  - it finds when a known kind suffices, and when a requested value is free;
  - it does all this without silent collapse and without silent choice.
- **Relative to the workshop** (decision 14). Every statement in this test, a witness, a refutation, a mark or a verdict, is relative to the witness space W of Section 2.2. W keeps seven rules of list v1 fixed. So "one branch" here means "one branch inside W". Outside W the theory as written can admit more branches, even for i² = −1 over the reals (the workshop page, section 7). This test does not see them.
- **Not new by itself:** minimal relaxation alone is known (literature review, 5.2). What is tested is the seven items together (decision 11).
- **Not tested** (declared):
  - mark 2, "needed for the proof of the role": roles are given directly, with no free variables, so no rule is used to derive them (Section 13);
  - generated identities other than the type-restricted copies of the list rules (Section 2.3);
  - the transfer of meaning by new operations, and "an independent consequence" (decision 2);
  - inferring an unwritten role; physical observations; real discovery; speed; language models;
  - trap 6 as written in the draft (z·0 + 0·z ≠ 0) and trap 7 (renaming operations), postponed by decisions 14 and 15;
  - merges other than the mirror (13.5, cases 2 and 3);
  - kinds outside W, among them every kind that breaks addition, distributivity, the identities or the negatives.

## 2. What the procedure computes
### 2.1 Inputs
- **The sealed seed:**
  - floors `f01` (list v1, q1-q14), `f02` (the complex list, q1-q13), `f03` (a frame floor: theorem `t1`, associativity);
  - kinds `k01` (the reals) and `k02` (the complex numbers, generator `e1` with `e1*e1 = -1`).
- **A world:** a v0.5 world file with exactly one build (`origin`, `generators`, `role`, `frames`), accepted by `lang/reader_v0.py` with the sealed seed, and obeying Section 3.
- **The bounds** (proposed after development; fixed at sealing and written here and in `seed/seed_notes.md`):
  - **P2 = 4**, the longest product in a role, and the base length of the searches (decision 4);
  - **P3 = 16**, the largest dimension of a witness table (decision 4); Dirac's algebra, the largest dev case, has dimension 16;
  - **S = 4**, the deepest nesting of case nodes in a refutation (Section 4.4).
- **The procedure's time:** at most 3600 seconds of wall-clock time per world, run on the project owner's machine with no other heavy process running. At the limit the procedure writes what it has: candidates it could not decide stay as `no_witness` branches, which is wrong where a proof decides. (The heaviest random dev request took 1145 seconds alone, and more than 1800 seconds while four runs shared the machine; Section 13, item 13.)
- P1, the parts degree of the draft, is not used: the only parts are the type-restricted copies (Section 2.3; choice 1 in Section 15).

### 2.2 The workshop W
- **A witness** for a build is a finite-dimensional unital algebra over the real numbers, given by:
  - a dimension n (1 ≤ n ≤ P3);
  - a basis b0 = 1, b1, ..., b(n-1);
  - structure constants: exact fractions c[i][j][k] with b_i*b_j = Σ_k c[i][j][k] b_k, where b0 is a two-sided unit;
  - a product extended bilinearly.
- **The old kind inside it:** the old real r is r·b0. For origin `k02`, the witness also gives an element E with exact rational coordinates and E*E = −b0, and the old complex number x + y·e1 is x·b0 + y·E.
- **The generators** get coordinates in F^n, where F = Q(θ) for one real algebraic number θ, or F = Q (Section 4.1).
- **Seven rules always hold in W** (choice 3): q3, q4, q9 and q11, because the elements form a vector space; q7 and q8, because the product is bilinear; and q10, because b0 is a unit. A relaxation that would need to break one of them is outside the test.
- **q1 and q2 also hold in W by construction:** b0 ≠ 0. The old kind sits inside as itself: the reals are the multiples of b0, with their own arithmetic and order; for `k02`, E*E = −b0, so span{b0, E} is a copy of the complex numbers.
  - The inverse is a total operation (Q10, D1). On old elements it gives the old values; on new elements it is constrained only when q13 is kept (Section 4.3).

### 2.3 Judged units and fixed rules
- **Fixed, never judged:**
  - **PROTECTED:** q1, q2 (Q10 11.6, question 4);
  - **WORKSHOP:** q3, q4, q7, q8, q9, q10, q11 (Section 2.2). For origin `k01`, also every type-restricted copy: the old reals are scalars, so a copy with an old variable holds in every witness;
  - **FRAME:** when `frames` is `["f03"]`, the theorem t1 holds. So q5 and all its copies are proven from the frame (mark 1; Q10 7.8, proposal 1, condition (b); the proof of t1 is declared by the seed, `seed_notes.md`, gap 3).
- **Judged units U** (the units a candidate may drop):
  - **origin `k01`:** q5, q6, q12, q13, q14;
  - **origin `k02`:** q5, q6, q12, q13, and seven type-restricted copies (Q10 11.6, 2b; language v0.5, change 3). A copy is named by the rule and the types of its variables, in the order they are written:
    - from `(a*b)*c = a*(b*c)`: `q5[onn]`, `q5[non]`, `q5[nno]`, `q5[oon]`, `q5[ono]`, `q5[noo]`;
    - from `a*b = b*a`: `q6[on]`.
    The copy with every variable old is protected by q2; with every variable new it is the rule itself. Because the old kind is spanned by 1 and E, and the rules are linear in each variable, a copy holds exactly when it holds with each old variable set to E.
  - With the frame, q5 and its copies leave U.
- **Not judged:**
  - copies of q12, q13 and q14: conditions and bundles are not split into parts (Q10 11.6, 2a);
  - other identities of the old kind (alternativity, flexibility, Jordan, Moufang and the like): Section 13, limit 3.

### 2.4 Candidates and their status
- **A candidate** is a set D ⊆ U: the units it drops. Its demand is the role, every unit of U not in D, and every fixed rule.
- **Each candidate has one status**, computed from certificates (Section 4):
  - **WITNESSED:** a valid witness satisfies the role and every unit of U \ D;
  - **REFUTED:** a valid refutation exists for some candidate D' ⊇ D (it then refutes D too, since D keeps more);
  - **UNDECIDED:** neither.
- **Monotone:** a witness of D also witnesses every larger candidate, and a refutation of D also refutes every smaller one. If one candidate is both WITNESSED and REFUTED, a certificate checker or the seed is wrong; the scorer stops and the event is reported.
- **Minimal candidates:** the candidates that are not REFUTED, while every proper subset of them is REFUTED (the containment rule, Q10 11.6, question 5). Counting units only orders the procedure's search; it never decides.

### 2.5 The verdict
The procedure decides in this order:
1. **FREEDOM:** the role contains `0^-1`. Section 3 guarantees that such a role holds in the origin kind for every value of `0^-1`, so no kind needs building; but the requested value is one the list leaves free (Q10, D1). Output the slot `0^-1` and its fate. The fate is always `undecided` here: a mathematical world has no anchor, and a value chosen to make things work is forbidden (blueprint 5.5).
2. **IMPOSSIBLE:** the role contradicts the protected rules by congruence closure (Section 4.6).
3. **KNOWN_SUFFICES:** the role has a solution in a tower kind that contains the origin. For `k01` these are `k01` and `k02`; for `k02` only `k02`. Report the smallest such kind (`k01` before `k02`) with the values of the generators (Section 2.8).
4. **Otherwise**, from the minimal candidates after the merge step (Section 2.7), each one a branch:
   - **NEW_KIND:** exactly one branch, and it is WITNESSED;
   - **BRANCHES:** two or more branches, at least one WITNESSED; with the decider for each pair: the units kept by one branch and dropped by the other;
   - **NO_WITNESS:** every branch is UNDECIDED. This is a deficit, not "impossible": no proof forbids the branch, and none was built within the bounds.
- The role is never empty, and Section 3 (V8) guarantees a witness of the largest candidate, U itself, outside FREEDOM, IMPOSSIBLE and KNOWN_SUFFICES. So the list of branches is never empty.

### 2.6 Marks (Q10 7.7 and 7.8)
For every branch D, every rule of the origin's list and every copy gets one mark:
- **PROTECTED:** q1, q2.
- **WORKSHOP:** the rules fixed by W (Section 2.3).
- **FRAME** (mark 1): proven from the frame.
- **FORCED** (mark 3): a unit u in D. Its proof is a valid refutation of D \ {u}: keeping u with the other units the branch keeps contradicts the role. Such a refutation exists because D is minimal.
- **ASSUMED** (mark 4): a unit of U that D keeps. No proof forbids it, no proof forces it; it is kept by minimal change and marked as an assumption.
- **Mark 2** ("needed for the proof of the role") cannot occur in this test (Section 1).
- **No other mark exists:** a rule used without a mark is an error (the rigor condition of 7.7).

### 2.7 The merge step (Q10 13.5, case 1)
Two branches D1 ≠ D2 are one law written twice, and are merged, exactly when all three hold:
1. the origin is `k02`;
2. D2 is the mirror of D1. The mirror swaps `q5[onn]` with `q5[nno]`, and `q5[oon]` with `q5[noo]`, and keeps every other unit;
3. the role is mirror-invariant: some permutation σ of the build's generators maps the reversed role onto the role, as sets of canonical sentences. To reverse a sentence, reverse every product (u*v becomes v*u, at every level) and keep the sums, signs and constants.
- Then the opposite algebra of a witness of D1 (the same table, product read in reverse), with generator g given the value of σ⁻¹(g), is a witness of D2.
- The merged output is one branch, D1, with `"mirror": {"twin": D2, "perm": σ}`. The checker verifies 2 and 3.
- Without such a translation, two tied branches stay two branches: a wrong merge hides a difference silently, while a wrong branch is declared (13.5, condition 1).
- **Trap T6** (Section 6) needs a world where this happens. Development found one (2026-10-22): over `k02`, the role `(e1*xx)*xx + (xx*xx)*e1 != e1*(xx*xx) + xx*(xx*e1)` has the mirror twins {q5, q5[nno], q6} and {q5, q5[onn], q6}, both without a witness. So T6 stays in the composition.

### 2.8 Known kinds (Q10 13.3; trap 15; decision 15)
- **The check:** read the role in the kind `k` (k01 or k02). There, the product is commutative and associative, so every chain and every bracketing of it has one value. The role becomes a system of polynomial equations and inequations with rational coefficients. For `k02`, `e1` is a variable with `e1*e1 + 1 = 0`.
- **A solution** is a list of values: real algebraic numbers for `k01`, and pairs (real part, imaginary part) of real algebraic numbers for `k02` (Section 4.5). The translation sends each generator to its value. It keeps every operation of the kind, because the values live in the kind itself.
- **No solution:** for `k02` this is decided by a Gröbner basis equal to {1} (Hilbert's Nullstellensatz, with one extra variable per inequation, the Rabinowitsch trick). For `k01` the procedure must also decide whether a complex solution has a real one; Section 3 (V14) keeps such worlds decidable.

### 2.9 What the procedure searches (informative; it is scored only through its outputs)
- **Witnesses:**
  - it computes the template, that is, the quotient of the free algebra by the role and the kept equational units, by linear algebra on products up to length P2;
  - when the template closes within dimension P3, it checks the conditions (q12, q13, q14) on it, and branches on "or" by passing to quotients (decision 5; trap 14);
  - it certifies q12 and q13 by a norm (Section 4.3).
- **Refutations:** linear algebra in the same truncated free algebra, with case nodes on zero divisors, inverses and positivity (Section 4.4), up to depth S.
- **The known kinds:** Gröbner bases and real root isolation.
- The procedure may find more certificates than the reference does, or fewer. The truth is the union of every valid certificate (Section 8.1).

## 3. World format, budgets and validity
- **Format:** a v0.5 world file naming the registry `t5_tower` and the SHA-256 of the sealed seed's canonical form. File names `W-01.json` ... `W-30.json`; the `id` inside is `w01` ... `w30`. The lists `bodies`, `quantities`, `relations`, `laws`, `observers`, `observations` and `fillers` are `[]`. The build's `src` is `"seed"`.
- **Budgets:**

| item | limit |
|---|---|
| builds | exactly 1 |
| generators | 1 to 4 |
| role sentences | 1 to 12 |
| factors in one product or chain | at most P2 |
| numbers | numerator and denominator at most 100 in absolute value |
| `^-1` | only as `0^-1`, and only in FREEDOM worlds |
| `frames` | `[]` or `["f03"]` |
| names | 2 to 6 lowercase ASCII letters and digits, starting with a letter, neutral, distinct from every seed id (`f01` ... `t1`, `q1` ... `q14`, `e1`) |

- **Validity.** A world that fails any rule is invalid and excluded from scoring.
  - **V1:** the reader accepts the world with the sealed seed.
  - **V2:** the budgets above hold.
  - **V3, FREEDOM worlds:** the role contains `0^-1`, and every role sentence has the form `g = t`. Here g is a generator defined by exactly one such sentence, and t is a term over fractions, `e1` (origin `k02`), `0^-1` and generators defined earlier in the list (no cycles). Such a role holds in the origin kind for every value of `0^-1`.
  - **V4, IMPOSSIBLE worlds:** congruence closure (Section 4.6) finds a contradiction, and `0^-1` does not occur.
  - **V5:** in every other world, `0^-1` does not occur.
  - **V6, KNOWN_SUFFICES worlds:** the key gives a valid solution in the smallest tower kind (Section 2.8).
  - **V7:** in every world that is not FREEDOM, IMPOSSIBLE or KNOWN_SUFFICES, the role has no solution in any tower kind containing the origin: a Gröbner basis equal to {1} over `k02`.
  - **V8:** in every world that is not FREEDOM, IMPOSSIBLE or KNOWN_SUFFICES, the key gives a valid witness for the largest candidate, D = U. This keeps the world inside W: the role must be satisfiable in W when every judged unit is dropped.
  - **V9:** the key agrees with the reference truth computed from the key's certificates and the reference's own search (Section 8.1): the same verdict, the same branches (after the merge step) with the same statuses, the same smallest known kind, the same slot.
  - **V10:** every certificate respects the size limits of Section 4 and the bounds P2, P3 and S.
  - **V11:** the world does not reproduce a dev world. The validator holds SHA-256 fingerprints of the canonical roles of the dev set (Section 12).
  - **V12:** every trap the key declares holds (Section 6).
  - **V13, the W8 lesson:** every trap condition is computed from the whole truth. "Not found by X" means not by X, and not by any part or combination of X.
  - **V14:** a world with origin `k01` whose roles have a complex solution but whose key gives no real one must have finitely many complex solutions (a zero-dimensional ideal). Then "no real solution" is checked by isolating every root.
  - **V15:** no two worlds of a batch have the same canonical role up to renaming the generators.

## 4. Outputs and certificates
### 4.1 Numbers
- **A fraction** is a string `"p/q"` or `"p"` in lowest terms.
- **θ** is `{"poly": [a0, a1, ..., ad], "lo": "l", "hi": "u"}`. The ai are fractions, d ≥ 2, ad ≠ 0. Sturm's count shows exactly one real root of the polynomial in (l, u], and that root is θ.
- **An element of F = Q(θ)** is a list of d fractions, the coefficients of 1, θ, ..., θ^(d−1). Without θ, it is a single fraction.
- **Equalities** in F are checked exactly, by reduction modulo the polynomial.
- **"Not zero"** is checked by exact interval arithmetic: θ's interval is bisected at most 60 times, until the interval value of the element excludes 0. Otherwise the inequation is not certified.

### 4.2 Elements of the free algebra (in proofs)
- **A word** is written in JSON: `"1"` (the unit), a name (a build generator, `e1` for origin `k02`, or a fresh name introduced by an inverse node), or a pair `[left, right]`, the product of two words. For example `[["x", "y"], "x"]` is (x*y)*x.
- **An element** is a list of `[coefficient, word]` pairs, with coefficients in F.
- **The ambient algebra** of a refutation node is the free unital algebra over F, taken modulo the kept global laws among q5 and q6:
  - neither kept: bracketed words;
  - q6 kept: bracketed words whose two factors are put in a fixed order at every level;
  - q5 kept: words without brackets;
  - both kept: commutative monomials.
  The checker computes canonical forms in that algebra. Every other kept law enters only as an explicit instance.

### 4.3 Witness certificate
```
{"dim": n, "table": [[i, j, k, "c"], ...],          nonzero structure constants only; b0 is the unit and is not listed
 "E": ["x0", ..., "x(n-1)"],                        origin k02 only
 "theta": θ | null,
 "gens": {g: [F-element, ...n coordinates], ...},
 "q12": NORM | null, "q13": NORM | INV | null}
```
- **The checker verifies:**
  - for `k02`, E*E = −b0;
  - every role sentence: equations exactly; inequations by Section 4.1; chains by computing every bracketing;
  - every kept equational unit, on the basis: q5 and q6 as identities, and the copies with each old variable set to E;
  - each kept condition, with its certificate:
    - **NORM** = `{"N": symmetric n×n rational matrix, "C": n×n rational matrix}`. N is positive definite (all leading principal minors > 0); N(x*y) = N(x)N(y) as a polynomial identity; x*C(x) = C(x)*x = N(x)·b0 as polynomial identities. Then q12 holds (N(x)N(y) = 0 forces x = 0 or y = 0), and so does q13, with x^-1 = C(x)/N(x).
    - **INV** = the same without multiplicativity: q13 holds, q12 is not claimed.
    - Both also check that the old elements keep their inverses (q2): C(b0) = b0; and for `k02`, C(E) = −E, N(E) = 1, and N has no cross term between b0 and E.
    - **q14 kept** is certified only when n = 1, by the order of the reals; in larger dimensions a witness never claims q14.
- **The witness's units:** the kept units are the units the certificate shows to hold. Its claimed candidate is the set of the other units. A witness may claim a larger candidate than the units it actually fails.
- **Size limits:** n ≤ P3; at most 4096 table entries; at most 64 numbers in one coordinate.

### 4.4 Refutation certificate (a proof tree, W-relative)
A refutation of candidate D shows that no witness keeps the role and every unit of U \ D. It is a tree of nodes. Each node has a context:
- **the relators, numbered from 0 in this order:**
  1. for each role sentence, in the order of the world file: first, for each chain met while reading the sentence (left side, then right side, inner chains first), the differences between its first bracketing and each other one; then, for an equation, left side minus right side. A difference that is 0 in the ambient keeps its number;
  2. for `k02`, `e1*e1 + 1`;
  3. the relators added by case nodes on the path from the root, in order;
- **the inequations, numbered from 0:** the role inequations, each as left side minus right side, in the order of the world file.
- The bracketings of a chain are enumerated recursively: split after the first factor, then after the second, and so on, with the bracketings of each side in the same order.

The node types:
- **`close`**: `{"target": T, "terms": [[coef, relator, path], ...]}`.
  - T is a nonzero constant (it contradicts q1 or q2), or one of the context's inequations.
  - A relator is `{"ctx": i}`, the context relator number i, or an instance of a kept unit, for example `{"unit": "q5[onn]", "args": {"b": element, "c": element}}`. `args` gives an element for each new variable of the rule as list v1 writes it (`(a*b)*c = a*(b*c)` for q5 and its copies, `a*b = b*a` for q6 and q6[on]); every old variable is E. Instances of q5 and q6 themselves are allowed when they are kept.
  - A path is a list of steps `["L", element]` or `["R", element]`, each one multiplying the current element by the given element on the left or on the right. In W, a relator equal to 0 stays 0 under such multiplications (bilinearity).
  - The checker expands Σ coef·path(relator) in the ambient algebra and requires it to equal T.
- **`split`**: `{"by": "q12" | "q14", "a": element, "b": element, "proof_ab": close-like terms showing a*b in the ideal, "children": [node, node]}`. The first child adds the relator a, the second adds b.
  - With q14 this rests on lemma O: in a W algebra with the order bundle, a*b = 0 with a, b ≠ 0 is impossible, because ±a > 0 and ±b > 0 give ±(a*b) > 0 by bilinearity.
  - The unit used must be kept.
- **`inverse`**: `{"a": element, "children": [node, node]}`, with q13 kept.
  - The first child adds the relator a.
  - The second introduces a fresh name v and adds the relators a*v − 1 and v*a − 1.
- **`positive`**: `{"t": [element, ...], "c": F-element, "terms": ...}`, with q14 kept.
  - The terms show that Σ t_i*t_i + c lies in the ideal, and c > 0 is certified by intervals.
  - It rests on lemma S: in a W algebra with the order bundle every square is ≥ 0, because (−t)*(−t) = t*t; so a sum of squares plus a positive old number is never 0.
  - It closes the node.
- **Validity:** every node's units are kept by the candidate, every leaf closes, the depth of case nodes is at most S, and the certificate has at most 20000 terms in all.
- **Soundness:** every step holds in every W algebra that satisfies the candidate, so a valid tree refutes the candidate in W. The proofs of lemmas O and S above are part of this protocol.

### 4.5 Known-kind certificate
`{"kind": "k01" | "k02", "theta": θ | null, "values": {g: F-element (k01) | [F-element, F-element] (k02, real and imaginary parts)}}`. The checker evaluates the role in the kind: equations exactly, inequations by intervals.
- For `k02`, `e1` is the imaginary unit.
- For the smallest kind: a `k01`-origin world reported at `k02` also needs "no real solution". The checker decides it by V14: it computes all complex solutions and checks that none is real.

### 4.6 IMPOSSIBLE
- **Congruence closure** over the ground terms of the role:
  - names and products of names are uninterpreted;
  - a term built only from fractions and `e1` is evaluated in the origin kind;
  - when the arguments of a term all have known old values, the term gets the computed old value.
- **A contradiction** is either one class holding two different old values, or both sides of a role inequation in one class.
  - These steps use only equality and the protected old arithmetic, so they hold in every candidate, inside W or not.
- **Output:** `{"kind": "values" | "inequation", "detail": [...]}`. The checker recomputes the closure.

### 4.7 The output file
`results/outputs_X.json` is `{world_id: {method: OUTPUT}}`. For the procedure:
```
{"verdict": "NEW_KIND" | "BRANCHES" | "KNOWN_SUFFICES" | "NO_WITNESS" | "FREEDOM" | "IMPOSSIBLE",
 "freedom": {"slot": "0^-1", "fate": "undecided"} | null,
 "impossible": IMPOSSIBLE | null,
 "known": KNOWN | null,
 "branches": [{"drop": [unit ids, sorted],
               "status": "witnessed" | "no_witness",
               "witness": WITNESS | null,
               "marks": {rule or copy id: "PROTECTED" | "WORKSHOP" | "FRAME" | "FORCED" | "ASSUMED"},
               "proofs": {unit id: REFUTATION, ...},         one for each FORCED unit
               "mirror": {"twin": [unit ids], "perm": {g: g', ...}} | null}],
 "deciders": [{"pair": [i, j], "only_kept_by_i": [...], "only_kept_by_j": [...]}],
 "refutations": [REFUTATION, ...],                           optional: any other refutations the procedure found
 "bounds": {"P2": ..., "P3": ..., "S": ..., "list": "1"}}
```
Baselines output only `{"verdict": ..., "branches": [{"drop": [...], "status": ...}], "known": {"kind": ...} | null}`.

## 5. Key format
`key/key.json` is a list of entries:
```
{"id": "W-01", "verdict": ...,
 "branches": [{"drop": [...], "status": "witnessed" | "no_witness", "witness": WITNESS | null,
               "mirror": {...} | null}] | null,
 "known": KNOWN | null, "freedom": {"slot": "0^-1"} | null, "impossible": IMPOSSIBLE | null,
 "top_witness": WITNESS | null,                    V8
 "refutations": [{"drop": [...], "proof": REFUTATION}, ...],    optional
 "traps": ["T3", ...], "notes": "free text"}
```
- Every witnessed branch carries its witness. Refutations are optional: the validator's reference searches for its own, and a generator adds one where the reference does not find it (the validator names the candidates it could not decide).
- Marks are not in the key: the reference computes them from the branches, the origin and the frames.

## 6. Composition (each batch: 30 worlds)
- **Verdicts** (decision 13):

| verdict | worlds |
|---|---|
| NEW_KIND | 9 |
| BRANCHES | 6 |
| KNOWN_SUFFICES | 5, at least 2 with origin `k01` at `k02` (T7) and at least 2 at `k01` with an irrational value (T15) |
| NO_WITNESS | 4 |
| FREEDOM | 3 |
| IMPOSSIBLE | 3 |

- **Origins:** at least 10 worlds of each origin. **Frames:** at least 3 worlds with `f03`.
- **Traps.** The trap table of the draft (section 6), with decisions 8, 14 and 15 applied. Each trap appears in at least 2 worlds of each batch; T6 only if development finds it (Section 2.7). The validator computes every condition from the truth and the baselines.

| trap | condition |
|---|---|
| T1, the bits world | MAXCON's output has a branch that drops q2 and not q1 (a characteristic-2 table) |
| T2, the trivial world | MAXCON's output has the branch {q1, q2} (the zero ring: the role has no inequation) |
| T3, a split rule | the truth has two branches of different sizes, and COUNT's decision differs from it |
| T4, false strictness | origin `k02`; a branch drops q6 and keeps `q6[on]`; COARSE's decision differs from the truth |
| T5, excess freedom | origin `k01`; q14 is in a branch; SPLIT_ORDER reports more branches than the truth |
| T6, the mirror pair | a merge by Section 2.7 occurs in the truth (conditional, see 2.7) |
| T7, a known kind under new names | KNOWN_SUFFICES at `k02` for origin `k01` |
| T8, a non-associative rival | the truth has a branch containing q5 and a branch not containing it; ASSOC's decision differs |
| T9, the request form | the role has a chain without brackets, and the truth changes when that chain is replaced by its left-bracketed form |
| T10, the frame | `frames` is `["f03"]`, and the truth changes when the frame is removed |
| T11, a forced fall | q12 is FORCED in every branch (for example a nilpotent: θ*θ = 0 with θ ≠ 0) |
| T12, the free slot | FREEDOM |
| T13, another origin | origin `k02`, the role does not use `e1`, and the truth changes when the origin is `k01` |
| T14, a witness in a quotient | a witnessed branch keeps q12, and its witness is a proper quotient of the template of its kept equations: the template closes within P3 with a larger dimension than the witness's generated subalgebra |
| T15, it exists already | KNOWN_SUFFICES at `k01` with a value of degree at least 2 over the rationals |

- **Baseline sensitivity:** for each baseline of Section 7, at least 8 worlds per batch where its decision differs from the truth. Whichever baseline turns out best, the McNemar test then has enough discordant worlds (decision 13).
- **Diversity:** vary the number of generators, the relations (squares, anticommutation, nilpotents, idempotents, mixed brackets), the origin and the numbers. Famous algebras appear only under neutral names and with changed relations; the dev cases (Section 12) are excluded by V11.

## 7. Baselines
Each baseline is a known wrong rule (draft, section 7). All of them read the truth's classification of candidates (Section 8.1), so they differ from the truth only by their rule, never by a weaker search. They share the truth's FREEDOM, IMPOSSIBLE and KNOWN_SUFFICES verdicts, except where stated.
1. **COUNT:** the branches are the non-refuted candidates of fewest units. It falls in T3.
2. **MAXCON** (Martinez and others, 2017; decision 10): q1 and q2 become judged units, and the branches are the minimal candidates of this larger lattice. It adds:
   - the zero ring, the candidate {q1, q2}, when the role has no inequation;
   - the characteristic-2 candidate {q2} ∪ F2. F2 is the set of units that fail in the template of the role with every unit kept, computed over the field of two elements, when that template closes within P3 and the role's inequations hold in it (q14 always fails in characteristic 2).
   - It falls in T1 and T2. On IMPOSSIBLE and KNOWN_SUFFICES worlds whose role has no inequation, it reports the zero-ring branch too.
3. **ORDER,** a fixed textbook order: it drops, cumulatively, q14, q6, q5, q12, q13 (for `k02`, without q14), each rule with its copies. It answers the first prefix that is WITNESSED, as a single branch.
4. **ASSOC** ("assume associativity", the families of test 1): q5 and its copies are never dropped. The branches are the minimal candidates among those that keep them. With none, it answers "no answer". It falls in T8.
5. **FIRST** ("the first found"): the first WITNESSED candidate, by number of units and then in the order q5, q6, q12, q13, q14, `q5[onn]`, `q5[non]`, `q5[nno]`, `q5[oon]`, `q5[ono]`, `q5[noo]`, `q6[on]`. It reports it as NEW_KIND, choosing silently. On FREEDOM worlds it fills `0^-1` with 0 and answers KNOWN_SUFFICES.
6. **COARSE** (the coarse list, no parts): only the rules are units, and each copy follows its rule. The candidates are the ones that drop whole rules with all their copies. It falls in T4.
7. **SPLIT_ORDER** (the order's parts without the bundle; 2a): q14 is replaced by three separate units, totality, sums and products. In W each one alone can be dropped while the other two hold:
   - the cone of positive reals keeps sums and products;
   - an order by coordinates, with b0 first, keeps totality and sums;
   - an order with only the positive reals above 0 keeps totality and products.
   So every branch D of the truth that contains q14 becomes three branches. It falls in T5.

## 8. Truth, correctness, metrics, criteria
### 8.1 The truth of a world
- **Sources:** the scorer's reference computes the truth from:
  - the world;
  - every certificate in the key;
  - every certificate in the procedure's output;
  - the reference's own bounded search for refutations:
    - words up to length P2 in non-associative ambients and P2 + 1 in associative ones (4 after an inverse node adds a fresh name);
    - at each node, at most 8 zero-divisor pairs and at most 4 inverse nodes, from the linear forms with coefficients in {-1, 0, 1};
    - at most 60 nodes per candidate, depth S, at most 1500 rows and 40000 products per truncated ideal;
    - first over Q; then, when the role makes the square of a generator equal to a positive rational c that is not a square, over Q(sqrt c), where the linear forms also use ±sqrt(c) (for example the split (x − √2)(x + √2) = 0 when x*x = 2);
    - by the mirror symmetry of Section 2.7, a candidate and its mirror share their status when the role is mirror-invariant.
  - These limits are fixed numbers, never time, so the truth is the same on every machine.
- **Rule:** valid certificates are the judge (history test, section 11.6, item 1). A branch is real when it has a witness, or when no proof refutes it; a fork is real when no proof decides it. So the procedure is never penalized for a valid certificate. And a branch where some valid proof decides is an error, whoever found the proof.
- **Recorded events:**
  - If the procedure's certificates change a key's verdict, the world stays and is scored against the changed truth, and the change is listed in the report.
  - If any witness and any refutation contradict each other, the run stops (Section 2.4).
- The validator's truth (V9) uses the key and the reference only.

### 8.2 Correctness of an output on a world
- **Verdict correct:** equal to the truth's verdict.
- **Decision correct:** the verdict is correct, and:
  - for NEW_KIND, BRANCHES and NO_WITNESS, the set of branches after the merge step equals the truth's, with equal statuses (and, for merged branches, a valid mirror translation);
  - for KNOWN_SUFFICES, the same smallest kind;
  - for FREEDOM, the slot `0^-1` with fate `undecided`.
- **Marks correct:** the decision is correct, every mark equals the truth's (Section 2.6), every FORCED unit has a valid refutation of D \ {u}, and every witness is valid.
- A baseline's decision is correct by the same definition, without certificates.

### 8.3 Metrics (per batch, over valid worlds)
- **verdict accuracy;**
- **drop-set accuracy:** decision correct, over the worlds whose truth is NEW_KIND, BRANCHES or NO_WITNESS;
- **marks accuracy:** marks correct, over the same worlds;
- **decision accuracy:** decision correct, over all worlds (this is the measure compared with the baselines);
- **false witness:** worlds with at least one witness or known-kind certificate in the output that the checker rejects;
- **silent collapse:** worlds where an output witness or known-kind certificate fails q1, q2 or a role sentence. Every such world also counts as a false witness;
- **silent choice:** worlds whose truth has two or more branches after the merge, and whose output reports a proper subset of them;
- **reported only:** branches the output adds where a valid proof decides; unmerged mirror twins; NO_WITNESS answers where the truth has a witness; changes of the truth by the procedure's certificates (8.1).

### 8.4 Criteria (each batch alone, decision 12b; the pooled numbers are published too)
- **C1:** verdict accuracy ≥ 0.70.
- **C2:** drop-set accuracy ≥ 0.70.
- **C3:** marks accuracy ≥ 0.70.
- **C4:** both of:
  - decision accuracy minus the best baseline's decision accuracy ≥ 0.15;
  - one-sided exact McNemar p < 0.05 against that baseline. Here b = worlds where the procedure is correct and the baseline is not, c = the reverse, and p = P(X ≥ b) with X ~ Binomial(b + c, 1/2). A tie in baseline accuracy goes to the larger p.
- **C5:** silent collapse in 0 worlds.
- **C6:** silent choice in at most 1 world.
- **C7:** false witness in 0 worlds.
- **Outcome of a batch:** VOID if 7 or more of its 30 worlds are excluded; PASS if C1-C7 all hold; FAIL otherwise.
- **The test passes** when both batches pass. If one batch is VOID, it is rerun with new worlds from the same generator.

## 9. Pre-registered interpretation
- **PASS** is evidence that, on unseen formal worlds and inside the workshop W, the rules for building a new kind can be computed:
  - the smallest relaxation by containment, with protection, marks and proofs;
  - witnesses built by the procedure itself, and an honest NO_WITNESS where none is built;
  - branching with deciders, and merging only by a checked translation;
  - known kinds and free slots found;
  - all without silent collapse or silent choice.
  This is the first test of the Q10 decisions, which until now were all untested.
- **FAIL** returns those rules, or their implementation, to design. **VOID** means a rerun.
- **Not evidence of:**
  - uniqueness outside W (the workshop page, section 7);
  - real discovery, or superiority over language models;
  - the novelty of minimal relaxation itself;
  - mark 2, the generated identities beyond the copies, the transfer of meaning, or any kind outside W.

## 10. Hidden information
- The seed, its notes, the language and this protocol are public to the generators. Worlds hold requests, never verdicts.
- The procedure never reads `seed/seed_notes.md`.
- The key's certificates are never shown to the procedure. The procedure's certificates enter the truth only after the outputs hash is published.

## 11. Generator brief
- **Bias.**
  - Batch A comes from the same model family as the procedure's author. Batch B removes that limit for its 30 worlds.
  - Both generators: prefer unfamiliar relations and numbers; do not model worlds on the examples in this protocol, the draft or the language files; make every baseline genuinely tempting.
- **What a world is:** a request (a role) over an origin. You design it from an algebra you know, under neutral names, and you give in the key the witnesses of its branches and of its largest candidate. You may add refutations; the validator tells you which candidates its reference could not decide.
- **Method:**
  1. Use code and exact fractions.
  2. Write `key/verify_key.py` from this protocol alone, and run it first.
  3. Run the sealed validator, and repair until it prints `VALID`.
  4. Keep `progress.txt` updated, with the model name and the SHA-256 of every file you received.
- **Do not** add constraints that make the test easier than this protocol requires. If a requirement cannot be met, or the protocol is ambiguous, stop and write the problem in `key/generator_notes.md` for the project owner. Do not resolve it silently.

## 12. Dev set (used during development; excluded from the test)
- **Famous cases** (decision 6), under their own relations:
  - the complex numbers, quaternions over each origin, octonions (by their Fano relations);
  - Grassmann numbers, split-complex numbers, tessarines, Segre's tricomplex numbers, Macfarlane's hyperbolic quaternions, Clifford's biquaternions;
  - Dirac's gamma matrices with and without the frame, the quaternion request with `(i*j)*k` only and with `i*j*k`;
  - 1/0 with list 1, √2 and the cube root of 2;
  - a nilpotent θ with θ*θ = 0.
- **One toy world per trap,** and one per verdict.
- **Dev checks:**
  - `dev/fuzz_compare.py`: random small roles; procedure against the independent reference;
  - `dev/mutation_test.py`: deliberate corruption of outputs, certificates, worlds and keys; every kind of wrong output and every validity rule must be caught (lesson of test 2);
  - `dev/make_dev.py`: writes the dev worlds, the dev key (from the procedure's outputs), and the fingerprints for V11.
- **The mirror pair (T6)** was found during development (Section 2.7).
- **The validator's fingerprints** (V11) cover every dev world, in `scorer/dev_fingerprints.json`.
- **What the dev scores show, and what they do not:** the dev key is written from the procedure's own outputs (`dev/make_dev.py`). So a dev score of 22 of 22 tests the chain (checkers, reference, validator, scorer), and shows that the reference found no proof the procedure missed. It is not evidence that the procedure is right: that comes only from the generators' worlds and keys.

## 13. Known limitations (declared before the test)
1. **Relative to W.** Seven rules are fixed by the workshop, and every verdict holds inside W only. Outside W even i² = −1 over the reals has a second branch, without distributivity, that no proof refutes and no table builds (the workshop page, section 7). Kinds that break addition, distributivity, the identities or the negatives (the extended reals, wheels, near-rings) are outside this test (decision 14).
2. **"Correct" is defined by our rules,** by the sealed list and by the certificates. A rule absent from the list is neither checked nor counted (the header of list v1).
3. **The parts are only the type-restricted copies** of q5 and q6 over `k02`. Other identities of the old kind (alternativity, flexibility, Jordan, Moufang) are neither generated nor judged nor marked. For `k01` every copy is fixed by W.
4. **Mark 2 is not tested,** because roles carry no free variables and are not derived from a law.
5. **Certification of conditions is narrow:**
   - q12 is certified only by a multiplicative positive-definite norm (composition algebras), and q13 by a conjugation (Cayley-Dickson-like algebras). A division algebra without such a norm cannot serve as a witness.
   - q14 is certified only in dimension 1.
   - So some branches are NO_WITNESS by the limits of certification, not by mathematics; the truth's statuses are relative to these certificate forms.
6. **NO_WITNESS does not mean impossible,** and UNDECIDED depends on the search bounds and on the certificates found by anyone.
7. **The frame theorem t1 is declared by the seed,** not proved by the kernel (trap 10; language v0.5, *Not in v0.5*).
8. **FREEDOM's fate is always `undecided`:** the worlds are mathematical and carry no anchor. FREEDOM roles are definitions only (V3).
9. **The merge step is tested only for the mirror** (Section 2.7).
10. **One author, two programs:** the procedure and the reference are independent code by the same author. Batch A's generator is from the same model family; batch B's is not.
    - **They share some search ideas:** both try linear forms with coefficients in {-1, 0, 1}, and both search over Q(sqrt c). sqrt(c) was added to both on 2026-10-22, after a dev comparison showed both missing the same refutation (x*x = 2: the split (x − √2)(x + √2) = 0).
    - So a blind spot they share, for example cube roots, makes the truth UNDECIDED where a proof exists. Only a generator's certificate catches it; the validator lists the undecided candidates of every world so that a generator can supply one.
11. **The comparison with baselines is partly definitional:** each baseline is a known wrong rule applied to the true classification.
12. **The worlds are formal and few:** 30 per batch.
13. **The procedure's limit is time, not a count of steps** (Section 3). A world near the limit can give a different output on a slower or busier machine. The procedure runs once, on one machine, and the published outputs hash is the record; the reference's limits are counts, so the truth does not depend on the machine.

## 14. Hashes (SHA-256)
- **Published on the Notion page when sealed:**
  - this protocol;
  - `seed/seed_registry.json`, `seed/seed_notes.md`, `seed/check_seed.py`, `seed/make_seed.py`;
  - `lang/SPEC_v0.5.md`, `lang/reader_v0.py`;
  - `procedure/procedure_v5.py`;
  - `scorer/ref_v5.py`, `scorer/certs_v5.py`, `scorer/baselines_v5.py`, `scorer/score_v5.py`, `scorer/validate_v5.py`, `scorer/dev_fingerprints.json`;
  - `tools/hash_files.py`, `tools/make_packages.py`;
  - `GENERATOR_START.md`, `GENERATOR_START_en.md`.
- **For each batch:**
  - the combined hash of the 30 worlds, and `key/key.json`, published before the procedure runs (lesson of test 4);
  - `results/outputs_X.json`, published by the procedure author before the key is opened.

## 15. Choices made while writing this protocol (for review)
Marked [changes a decision] when a choice departs from an approved decision of the draft. The others fill in details the draft left open, and are the procedure author's to make (implementation of a test whose judge is our own rules).
1. [changes a decision; APPROVED 2026-10-22, decision 16] **The parts are only the type-restricted copies** (2.3; limit 3). Q10 11.6, 2b, says the generator takes every equation of the old kind up to a degree P1, and that the verdict is judged by containment over the surviving equations.
   - Judging over every generated identity would need proofs that no witness keeps more of them, over a large family of identity sets, and we have no checkable form for such proofs.
   - The copies keep what the traps need: false strictness (T4) and the mirror pair (T6).
2. [declares a limit of an approved claim; APPROVED 2026-10-22, decision 17] **Mark 2 cannot occur** (2.6; limit 4).
3. **The workshop W and its seven fixed rules,** with the marks WORKSHOP and PROTECTED, and the declared relativity (decision 14).
4. **Certificates are the judge, and the truth is their union** (8.1). This applies the project owner's insight on branch scoring (history test, 11.6): a fork is real when no proof decides it and each branch is witnessed or undecided. So branching where a proof decides is an error, and choosing where none decides is the forbidden silent choice.
5. **The certificate forms** (Section 4): the norm and conjugation for q12 and q13; q14 only in dimension 1; refutation trees with four node types and lemmas O and S; ambient algebras by the kept global laws; Q(θ) numbers with Sturm and interval checks.
6. **FREEDOM worlds are definitions only, with fate `undecided`** (V3).
7. **IMPOSSIBLE only by congruence closure** (4.6). A contradiction that needs one of the seven W rules would not be a true impossibility (limit 1), so such worlds are excluded by V8.
8. **Known kinds:** the smallest tower kind; Gröbner bases decide "no solution"; V14 keeps "no real solution" decidable.
9. **Seven baselines, read on the true classification** (Section 7). SPLIT_ORDER is new: the draft named "parts without the bundle" as the victim of trap 5 but listed no such baseline; and the coarse list does not fall in trap 5 (correction in the draft, 2026-10-22).
10. **The traps after decisions 8, 14 and 15:**
    - T7 is a known kind under new names;
    - T14 needs examples the tower does not satisfy;
    - T6 is conditional on development;
    - T11's victim is any rule that keeps everything; it is a computed condition, not a baseline.
11. **Batch B:** Gemini 4 Argon, running locally with Python (the project owner, 2026-10-22). It runs the sealed Python validator directly, so the TypeScript copy proposed in the draft (12a, note of 2026-10-22) is not needed.
12. **Budgets** (Section 3), and the forms of chains and inequations in roles.
13. **Bounds** P2 = 4, P3 = 16, S = 4, the size limits, and the reference's search bounds (8.1).
14. **The procedure's witness search guesses relations** when the template of a request does not close: e1 commuting or anticommuting with each new generator (origin `k02`), and pairs of new generators doing so. A guess only steers the search: every witness found is checked like any other, and a guess that leads nowhere costs nothing but time.
