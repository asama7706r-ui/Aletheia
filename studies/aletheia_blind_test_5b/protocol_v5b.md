# Aletheia blind test 5b - pre-registered protocol v5b (SEALED 2026-10-31)

Status: SEALED at 2026-10-31T10:03:06Z, with the code, after the project owner reviewed the Notion page «مسودة التجربة 5ب: ما يحتاج مراجعتك» and approved sealing on 2026-10-31, on the condition that the regression run on the worlds of test 5 finish without errors (it did; that page, section 4). Written by the procedure author (Claude) on 2026-10-28. The SHA-256 of every sealed file is in `SEALED_HASHES.txt`.
**What 5b is.** Blind test 5 (sealed 2026-10-23) FAILED. Its audit found that the rules were applied correctly and that the failure was in the search for witnesses and refutations. The workshop page («ورشة الأمثلة», section 10) then widened the search (option C) and measured it on the worlds of test 5, which are spent for that purpose. Test 5b tests **the same claim, with the same seed, language, workshop, composition, bounds, time limit and criteria, on new worlds from new generator runs**, with the widened procedure and the corrections listed in Section 16. The project owner chose to prepare it on 2026-10-28 (workshop page, 10.9).
Sources:
- everything protocol v5 names (the test-5 draft and its decisions 1-17, the seed page, language v0.5, the Q10 page, the workshop page);
- test 5's protocol addendum 1 (2026-10-23), whose clarifications are written into Sections 2.7, 4.3, 4.4a, 4.6 and 11 here;
- test 5's audit (`audit.md`, its correction 1) and its lessons;
- the workshop page, sections 10.4 to 10.13 (option C, its three measurements, and the two small changes of 10.13).
Section 15 lists the choices made while writing this protocol; Section 16 lists every change from protocol v5.

## 0. Roles, order and rules
- **Procedure author** (Claude): writes this protocol, the procedure (`procedure/procedure_v5b.py` with the files it imports: `procedure_v5.py`, `proc_c.py`, `proc_c2.py`, `proc_c3.py`, `shape_search.py`, `shape_search_na.py`, `shape_driver.py`, `solver_worker.py`), `scorer/ref_v5b.py`, `scorer/certs_v5.py`, `scorer/baselines_v5b.py`, `scorer/score_v5b.py`, `scorer/validate_v5b.py`, `run/run_batches_5b.py` and the tools. Develops them ONLY on the dev set (Section 12). Seals them before any test world exists.
- **Sealed inputs:**
  - `seed/seed_registry.json`, the tower (v0.5 registry), with `seed/seed_notes.md` (what each id means; the procedure never reads it) and `seed/check_seed.py`;
  - `lang/SPEC_v0.5.md` and `lang/reader_v0.py`.
- **Two world generators, two batches of 30 worlds each** (decisions 12, 12a, 12b):
  - **Batch A:** a separate Claude session, at its highest reasoning effort, with code execution.
  - **Batch B:** Gemini 4 Argon (decision 12), running locally on the project owner's machine with Python and file access (2026-10-22). The project owner starts it. Because it can reach the disk, it works in its own generator folder holding only the package, and it never opens any other folder. The exact model name is written in the batch's `progress.txt`.
  - These are new runs of the two generators: neither has seen the worlds of test 5, and neither reads them.
  - Each generator reads ONLY this protocol and the files in `seed/`, `lang/` and `tools/`. It RUNS `scorer/validate_v5b.py` (with the modules it imports and `scorer/dev_fingerprints_5b.json`) but never reads the code in `scorer/`, so that its `key/verify_key.py` and its certificates stay independent of the reference (Section 13, item 10). It never reads the procedure, the dev folder, the results, earlier tests, any Notion page, or any memory files.
  - Each writes `worlds/W-01.json` ... `worlds/W-30.json` and `key/key.json` in its batch folder (`batch_A/`, `batch_B/`).
  - Each first writes its own verification code `key/verify_key.py` from this protocol alone, and its output `key/verify_output.txt`. Then it runs `python scorer/validate_v5b.py .` inside its package folder (which is its batch folder) and repairs its files until the validator prints `VALID`.
  - Each reports the SHA-256 of every sealed file it received, computed by code, so that the run is known to use the sealed files.
- **The procedure author must not read any world or key before the SHA-256 of that batch's `results/outputs_X.json` is published.** Running the frozen procedure on the worlds is allowed. Nothing is debugged, repaired or changed after sealing.
- **Order:**
  1. Seal.
  2. Generate, verify, validate (each batch).
  3. Publish the hashes of the worlds and keys.
  4. Run `python -I run/run_batches_5b.py A B`. It runs `procedure/procedure_v5b.py run batch_X/worlds results/outputs_X.json results/parts_X` for each batch in turn (the procedure reads the worlds folder only, never the key), on AC power only, with the machine kept awake (Section 2.1).
  5. Publish the outputs hash.
  6. Open the key. Run `python scorer/score_v5b.py batch_X results/outputs_X.json results/report_X.json`.
  7. Publish the reports verbatim, then a separate audit.
- **Notes to the project owner** (addendum 1, A5.5): a generator that writes `key/generator_notes.md` describes the problem without quoting the role of a planned batch world. A role quoted in a note is not used in the batch, nor any renaming of it.
- **Independence:** the scorer and the validator never import the procedure. They recompute the truth with their own code (`scorer/ref_v5b.py`) and check every certificate by exact arithmetic (`scorer/certs_v5.py`). The procedure imports `scorer/certs_v5.py` only to check its own certificates before writing them; it never imports the reference, the baselines, the scorer or the validator. The reference searches by linear algebra on truncated ideals; the procedure by rewriting systems, templates, refutation of small groups of rules, and a shape-first witness search (different methods, by the same author).
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
- **The same claim as test 5,** word for word. What changed is how the procedure searches (Section 2.9) and the corrections of Section 16. Test 5's FAIL stands; 5b neither repairs nor replaces it.
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
- **The procedure's time:** at most 3600 seconds of wall-clock time per world, run on the project owner's machine with no other heavy process running. At the limit the procedure writes what it has: candidates it could not decide stay as `no_witness` branches, which is wrong where a proof decides. (On the worlds of test 5, the procedure of 5b took at most 2817 seconds for one world, A W-28; workshop page, 10.12.)
- **The power and the sleep of the machine** (lesson of the workshop's measurements): the run harness `run/run_batches_5b.py` starts nothing on battery, keeps the machine and the screen awake, and logs the power source every 30 seconds. Each world is saved as soon as it is solved. A world that runs more than 60 seconds on battery is stopped and starts again from nothing on AC power, so that every counted world ran its whole time on AC power and awake. The power log is published with the outputs.
- P1, the parts degree of the draft, is not used: the only parts are the type-restricted copies (Section 2.3; choice 1 in Section 15 of protocol v5).

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
- **"Canonical sentences"** (addendum 1, A4) means what the checker compares: each sentence becomes its operator plus the unordered pair of its two sides; each side is written in the reader's canonical form after nested sums are flattened and their summands sorted; products keep their order, and signs and constants are kept. The role is mirror-invariant under σ when the set of these keys equals the set for the reversed role renamed by σ.
- Without such a translation, two tied branches stay two branches: a wrong merge hides a difference silently, while a wrong branch is declared (13.5, condition 1).
- **Trap T6** (Section 6) needs a world where this happens. Development found one (2026-10-22): over `k02`, the role `(e1*xx)*xx + (xx*xx)*e1 != e1*(xx*xx) + xx*(xx*e1)` has the mirror twins {q5, q5[nno], q6} and {q5, q5[onn], q6}, both without a witness. So T6 stays in the composition.

### 2.8 Known kinds (Q10 13.3; trap 15; decision 15)
- **The check:** read the role in the kind `k` (k01 or k02). There, the product is commutative and associative, so every chain and every bracketing of it has one value. The role becomes a system of polynomial equations and inequations with rational coefficients. For `k02`, `e1` is a variable with `e1*e1 + 1 = 0`.
- **A solution** is a list of values: real algebraic numbers for `k01`, and pairs (real part, imaginary part) of real algebraic numbers for `k02` (Section 4.5). The translation sends each generator to its value. It keeps every operation of the kind, because the values live in the kind itself.
- **No solution:** for `k02` this is decided by a Gröbner basis equal to {1} (Hilbert's Nullstellensatz, with one extra variable per inequation, the Rabinowitsch trick). For `k01` the procedure must also decide whether a complex solution has a real one; Section 3 (V14) keeps such worlds decidable.

### 2.9 What the procedure searches (informative; it is scored only through its outputs)
The procedure of test 5 (`procedure_v5.py`, unchanged), with the changes of option C installed by the other files of `procedure/` (workshop page, 10.6 to 10.13):
- **Witnesses:**
  - the template, as in test 5: the quotient of the free algebra by the role and the kept equational units, by rewriting on products up to length P2; when it closes within dimension P3, the conditions (q12, q13, q14) are checked on it, with quotients for "or" (decision 5; trap 14); q12 and q13 are certified by a norm (Section 4.3);
  - the witness tricks of test 5 (guessed commutations and anticommutations, zero-divisor quotients);
  - then, for the branches still undecided, a **shape-first search**: a shape fixes which products are basis elements; the other products are unknown combinations of smaller basis elements, solved exactly. Associative shapes (matrices) up to dimension 5, then non-associative shapes (trees) up to dimension 4, smallest dimension first, at most 600 seconds per branch; a pass modulo a prime orders the shapes without dropping any; each exact solve runs at most 20 seconds, and an unsolved shape makes its dimension "partly searched". The associative half is skipped for a branch when a conflict the procedure has proven is made only of rules the branch keeps and rules of the q5 family: every associative table satisfies q5 and all its copies (10.13). Each `no_witness` branch records how far this search got.
- **Refutations:**
  - rewriting in the truncated free algebra, with case nodes on zero divisors, inverses and positivity (Section 4.4), up to depth S, as in test 5, plus: q6[on] relators in associative ambients; copy instances whose argument is a product of two names written in the role; splits on the factors of a name's minimal polynomial; inverse nodes on each name;
  - **conflicts first:** the procedure keeps the sets of kept rules it has proven contradictory (with their certificates), and examines only the smallest drop sets that break every known conflict (the minimal hitting sets; Reiter 1987), smallest first. For each, it first tries to refute small groups of the rules the candidate keeps (at most 3 rules, at most 20 seconds each, after seeking an example of the group), then the whole candidate. A new refutation is shrunk to the rules its certificate needs and becomes a conflict. The first phase stops at 2700 seconds, leaving the rest of the hour to the shape search.
  - every conflict goes into the output's `refutations` field (Section 4.7).
- **The known kinds:** Gröbner bases and real root isolation, as in test 5.
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
  - **V11:** the world does not reproduce a dev world, up to renaming the generators. The validator holds SHA-256 fingerprints of the canonical roles of the dev set (Section 12), which now holds the 60 worlds of test 5 and the two roles quoted in its batch A generator's notes.
  - **V12:** every trap the key declares holds (Section 6).
  - **V13, the W8 lesson:** every trap condition is computed from the whole truth. "Not found by X" means not by X, and not by any part or combination of X.
  - **V14:** a world with origin `k01` whose roles have a complex solution but whose key gives no real one must have finitely many complex solutions (a zero-dimensional ideal). Then "no real solution" is checked by isolating every root.
  - **V15:** no two worlds of a batch have the same canonical role up to renaming the generators and changing the nonzero numbers (test 5 audit, lesson 1: in its batch B, five errors fell in two families of roles that differed only in their numbers). Here every nonzero number is replaced by 1 before comparing; signs, written as negations, and zeros are kept.

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
    - **The matrix C** of NORM and INV acts on coordinate columns in the basis b0, ..., b(n−1): C(x)_i = Σ_j C[i][j]·x_j (addendum 1, A5.2).
    - **A witness with `"q12": NORM` and `"q13": null` keeps q13 too:** the checker uses the q12 certificate for q13. Writing a certificate in `"q13"` as well is also accepted; it is then checked as INV (A5.3).
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

### 4.4a A refutation in JSON, and the numbering of relators (test 5's addendum 1, A1 to A3)
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
- **Where refutations go:** in the key, `{"drop": [...], "proof": REFUTATION}` (Section 5); in an output's `"refutations"` list (4.7), items of the same form. A branch's `"proofs"` maps a unit u to a REFUTATION of the candidate D \ {u}.
- **The numbering of relators** (Section 4.4, item 1):
  - only a product of three or more factors written without brackets is a chain. A sum never adds a relator, whatever its length: addition is fixed in W;
  - for each role sentence in file order, equations and inequations alike, the checker reads the left side, then the right side. Inside a side, the factors of a product are read before the product, so inner chains come first. For each chain it appends "first bracketing minus bracketing k", for k = 2, 3, ... in the order of Section 4.4. Then, for an equation, it appends left side minus right side;
  - the first bracketing splits after the first factor at every level: a*(b*(c*d)). It is also the value the chain takes in "left side minus right side" and in an inequation;
  - example (origin `k01`, role `["x*y*z = x", "x*x*x != 0"]`, candidate `["q5", "q6"]`): relator 0 = x*(y*z) − (x*y)*z; relator 1 = x*(y*z) − x; relator 2 = x*(x*x) − (x*x)*x (the chain of the inequation); inequation 0 = x*(x*x). When q5 is kept, relators 0 and 2 are 0 in the ambient and keep their numbers;
  - then `e1*e1 + 1` for origin `k02`, and then the relators added by case nodes on the path. Each child of a case node extends its parent's list on its own, so both children of a split use the same next number.
- **Four refutations the sealed checker accepts** (they show the format only; worlds are not to be modelled on them, Section 11):
  - **E1, `positive`:** origin `k01`, role `["x*x = -1"]`, candidate `[]`. Relator 0 is x*x + 1, a square plus a positive number.
    `{"theta": null, "tree": {"node": "positive", "t": [[["1", "x"]]], "c": "1", "terms": [["1", {"ctx": 0}, []]]}}`
  - **E2, `split` with a fraction coefficient:** origin `k01`, role `["x*x = 2", "x*y + y*x = 0", "y != 0"]`, candidate `["q14"]` (q6 and q12 kept). With q6, relator 1 is 2·x*y, so x*y = (1/2)·relator 1. Child 1 adds x (relator 2): relator 0 − relator 2·x = −2. Child 2 adds y (relator 2), which is inequation 0.
    `{"theta": null, "tree": {"node": "split", "by": "q12", "a": [["1", "x"]], "b": [["1", "y"]], "proof_ab": [["1/2", {"ctx": 1}, []]], "children": [{"node": "close", "target": {"const": "-2"}, "terms": [["1", {"ctx": 0}, []], ["-1", {"ctx": 2}, [["R", [["1", "x"]]]]]]}, {"node": "close", "target": {"ineq": 0}, "terms": [["1", {"ctx": 2}, []]]}]}}`
  - **E3, `inverse`:** origin `k01`, role `["t*t = 0", "t != 0"]`, candidate `["q12", "q14"]` (q5 and q13 kept). Child 1 adds t. Child 2 adds t*tv − 1 and tv*t − 1 (relators 1 and 2), and t = (t*t)*tv − t*(t*tv − 1).
    `{"theta": null, "tree": {"node": "inverse", "a": [["1", "t"]], "v": "tv", "children": [{"node": "close", "target": {"ineq": 0}, "terms": [["1", {"ctx": 1}, []]]}, {"node": "close", "target": {"ineq": 0}, "terms": [["1", {"ctx": 0}, [["R", [["1", "tv"]]]]], ["-1", {"ctx": 1}, [["L", [["1", "t"]]]]]]}]}}`
  - **E4, θ:** origin `k01`, role `["x*x = 2", "x*y = 0", "y != 0"]`, candidate `[]`, θ = √2. Split by q12 on (x − θ, x + θ), whose product is relator 0. Then y = (θ/2)·x*y ∓ (θ/2)·(x ∓ θ)*y in each child.
    `{"theta": {"poly": ["-2", "0", "1"], "lo": "1", "hi": "2"}, "tree": {"node": "split", "by": "q12", "a": [["1", "x"], [["0", "-1"], "1"]], "b": [["1", "x"], [["0", "1"], "1"]], "proof_ab": [["1", {"ctx": 0}, []]], "children": [{"node": "close", "target": {"ineq": 0}, "terms": [[["0", "1/2"], {"ctx": 1}, []], [["0", "-1/2"], {"ctx": 2}, [["R", [["1", "y"]]]]]]}, {"node": "close", "target": {"ineq": 0}, "terms": [[["0", "-1/2"], {"ctx": 1}, []], [["0", "1/2"], {"ctx": 2}, [["R", [["1", "y"]]]]]]}]}}`

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
- **Output:** `{"kind": "values" | "inequation", "detail": [...]}`. The checker recomputes the closure and checks only `"kind"`; `"detail"` is for the reader and is not checked (addendum 1, A5.1).

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
 "refutations": [{"drop": [...], "proof": REFUTATION}, ...],   every conflict the procedure proved (2.9), each for the
                                                              candidate that keeps exactly its rules
 "bounds": {"P2": ..., "P3": ..., "S": ..., "list": "1"}}
```
- The procedure also writes informative fields that nothing scores: `"phase1"` (times and counts of the first phase), `"conflicts"` and `"tested"` (the conflicts and the candidates examined), and in each `no_witness` branch `"searched"` (how far the shape search got, or why it was skipped) and, for a witnessed one, `"witness_source"`.
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
- **Undecided candidates** (addendum 1, A5.4): give a witness or a refutation for every candidate you can decide. A candidate with neither stays undecided; when it is minimal it is a `no_witness` branch of the truth, and the key must list it so (V9). This is how NO_WITNESS worlds and `no_witness` branches arise. The validator prints at most the first 12 undecided candidates of a world, in sorted order: settle those that can be settled and run it again to see the rest.
- A refutation in the key is offered by the reference to every candidate, not only to the one it is written for (Section 8.1). So one certificate for the candidate that keeps exactly a contradictory set of rules covers every candidate that keeps that set.
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
- **Traps.** The trap table of the draft (section 6), with decisions 8, 14 and 15 applied. Each trap appears in at least 2 worlds of each batch, T6 included (development found it, Section 2.7). The validator computes every condition from the truth and the baselines.

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

- **The variant worlds of T9, T10 and T13** (test 5 audit, lesson 3): the truth of the changed world uses the same witnesses and known-kind certificates, and the same refutations carried over by their relators, never by their numbers. A relator or inequation is matched by its element in the free algebra; a refutation that cites one the variant does not have is not carried over, and relators added by case nodes keep their place after the role's own. So re-bracketing a chain, removing the frame or changing the origin never changes the truth by renumbering alone.
- **Baseline sensitivity:** for each baseline of Section 7, at least 8 worlds per batch where its decision differs from the truth. Whichever baseline turns out best, the McNemar test then has enough discordant worlds (decision 13).
- **Diversity:** vary the number of generators, the relations (squares, anticommutation, nilpotents, idempotents, mixed brackets), the origin and the numbers. Famous algebras appear only under neutral names and with changed relations; the dev cases (Section 12) are excluded by V11, and families that differ only in their numbers by V15.

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
    - by the mirror symmetry of Section 2.7, a candidate and its mirror share their status when the role is mirror-invariant;
    - copy instances (Section 2.3) whose arguments are names, and, in non-associative ambients, one argument that is a product of two names written in the role; a kept q6[on] gives instances in associative ambients too (test 5 audit, correction 1).
  - These limits are fixed numbers, never time, so the truth is the same on every machine.
- **Every certificate for every candidate** (workshop page, 10.9, fix 2): a valid refutation in the pool, from the key or from the output, is offered through the checker to every candidate the reference examines, not only to the candidate it is written for and the candidates that keep more. A candidate it refutes is REFUTED. (In test 5 the reference used a refutation only for its own candidate and those keeping more; so a proof of a small contradictory set of rules, written once, did not reach the other candidates that keep the same set.)
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
- **reported only,** each printed by the scorer with its count and its worlds (test 5 audit, lesson 2): branches the output adds where a valid proof decides; unmerged mirror twins; `no_witness` branches of the output that the truth witnesses; NO_WITNESS verdicts where the truth has a witnessed branch; changes of the truth by the procedure's certificates (8.1).

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
  It would be the first PASS of the Q10 decisions: test 5 tested them and failed on the search (its audit).
- **FAIL** returns those rules, or their implementation, to design. **VOID** means a rerun.
- **What a PASS does not undo:** the procedure of 5b was developed on the worlds of test 5 after its FAIL. A PASS here shows that this procedure works on new worlds; it does not change test 5's result.
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
- These 22 worlds are test 5's dev set (`dev/batch_dev/`), unchanged.
- **The 60 worlds of test 5,** with their generators' keys (`dev/batch_t5A/`, `dev/batch_t5B/`). The procedure author read them while auditing test 5 and while developing option C, so they are spent for testing (test 5 audit, lesson 4) and belong to the dev set. Test 5's batch A world W-12 and batch B world W-24 have the same role up to renaming.
- **The two roles quoted in test 5's batch A generator notes** (addendum 1, A5.5).
- **Dev checks of 5b** (in `dev/`; their outputs are kept beside them):
  - the procedure on the 22 dev worlds, scored by the 5b scorer against the dev key;
  - the 5b reference against test 5's on the 82 dev worlds: which truths change, and why;
  - deliberate corruption of outputs, certificates, worlds and keys, including the new parts (reuse of certificates, V15 by numbers, the variant worlds); every kind of wrong output and every validity rule must be caught (lesson of test 2);
  - every copy unit, kept, produces relators in every ambient, and dropping it makes a certificate that cites it fail (test 5 audit, correction 1);
  - the procedure on the 60 worlds of test 5, through the run harness's rules, as a check for crashes before sealing (not a measurement; `dev/run_check_t5.py`).
- **The mirror pair (T6)** was found during test 5's development (Section 2.7).
- **The validator's fingerprints** (V11) cover every dev world, in `scorer/dev_fingerprints_5b.json`.
- **What the dev scores show, and what they do not:** the dev key of the 22 worlds was written from test 5's procedure's outputs, and the procedure of 5b was developed on the 60 worlds of test 5. So dev scores test the chain (checkers, reference, validator, scorer). They are not evidence that the procedure is right: that comes only from the new generators' worlds and keys.

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
    - **They share some search ideas:** both try linear forms with coefficients in {-1, 0, 1}, both search over Q(sqrt c), and both now use copy instances with a product of two role names as an argument. sqrt(c) was added to both on 2026-10-22, after a dev comparison showed both missing the same refutation (x*x = 2: the split (x − √2)(x + √2) = 0).
    - So a blind spot they share, for example cube roots, makes the truth UNDECIDED where a proof exists. Only a generator's certificate catches it; the validator lists the undecided candidates of every world so that a generator can supply one. In test 5 this safeguard caught a shared code error that the protocol had not declared (the audit's correction 1); that error is fixed in both programs here.
11. **The comparison with baselines is partly definitional:** each baseline is a known wrong rule applied to the true classification.
12. **The worlds are formal and few:** 30 per batch.
13. **The procedure's limit is time, not a count of steps** (Section 3). A world near the limit can give a different output on a slower or busier machine. The procedure runs once, on one machine, and the published outputs hash is the record; the reference's limits are counts, so the truth does not depend on the machine.
14. **The procedure's search still has narrow parts,** chosen by a human. Any of them can miss a witness or a refutation that exists:
    - the witness tricks guess only commutation and anticommutation; their zero-divisor quotients use coefficients ±1;
    - refutations split on at most 8 pairs of linear forms over the first 4 names with coefficients in {-1, 0, 1}, plus the factors of minimal polynomials; depth S;
    - the shape search solves each shape for at most 20 seconds, tries only rational points (free unknowns set to 0, ±1, ±2), goes to dimension 5 (associative) and 4 (non-associative) only, treats a generator outside a non-associative shape as a scalar, and imposes the quadratic form of Section 4.3 when q12 or q13 is kept;
    - on the worlds of test 5, its weakest point was a dimension-4 example whose equations the solver did not finish (workshop page, 10.9: test 5's batch B, W-28 to W-30).
15. **"Searched up to dimension n" is a record, not a proof.** A `no_witness` branch says how far the shape search got; nothing proves that no example exists beyond it, or inside it where a shape was left unsolved (workshop page, 10.13).
16. **The procedure was developed on spent worlds.** Option C and the changes of Section 16 were chosen after reading the worlds of test 5, and measured on them. Only new worlds can show whether they hold in general: that is this test.

## 14. Hashes (SHA-256)
- **Published on the Notion page when sealed:**
  - this protocol;
  - `seed/seed_registry.json`, `seed/seed_notes.md`, `seed/check_seed.py`, `seed/make_seed.py` (the same files as test 5's, the same SHA-256);
  - `lang/SPEC_v0.5.md`, `lang/reader_v0.py` (the same as test 5's);
  - `procedure/procedure_v5b.py`, `procedure/procedure_v5.py` (the same as test 5's), `procedure/proc_c.py`, `procedure/proc_c2.py`, `procedure/proc_c3.py`, `procedure/shape_search.py`, `procedure/shape_search_na.py`, `procedure/shape_driver.py`, `procedure/solver_worker.py`;
  - `scorer/ref_v5b.py`, `scorer/certs_v5.py` (the same as test 5's), `scorer/baselines_v5b.py`, `scorer/score_v5b.py`, `scorer/validate_v5b.py`, `scorer/dev_fingerprints_5b.json`;
  - `run/run_batches_5b.py`, `tools/hash_files.py`, `tools/make_packages_5b.py`;
  - `GENERATOR_START_5b.md`, `GENERATOR_START_5b_en.md`.
- **For each batch:**
  - the combined hash of the 30 worlds, and `key/key.json`, published before the procedure runs (lesson of test 4);
  - `results/outputs_X.json`, published by the procedure author before the key is opened, with `results/power_log.txt` and `results/run_times.txt`.

## 15. Choices made while writing this protocol (for review)
Test 5's choices 1 to 14 (protocol v5, Section 15) stand, except where a choice below or Section 16 changes them. The choices below are the procedure author's to make (implementation of a test whose judge is our own rules; the project owner's rule of 2026-10-21), unless marked.
1. [the project owner's decision, 2026-10-28] **5b tests test 5's claim with option C** and the two small changes of the workshop page, 10.13, and without the two larger proposals of 10.13 (proofs that no example exists, and learning why a proof never completes).
2. **Everything that defines the test stays as in test 5:** the seed (the same SHA-256), the language, the workshop W, the units and marks, the composition and traps, the bounds P2, P3 and S, the hour per world, the seven baselines, the criteria C1 to C7 and the outcome rule. So 5b differs from test 5 only in the procedure, in the corrections of the scorer side that the audit asked for, and in the worlds.
3. **The same two generators** (a separate Claude session for A; Gemini 4 Argon, locally, for B), in new runs.
4. **V11 stays "up to renaming" only,** while V15 becomes "up to renaming and the nonzero numbers". V11 keeps out worlds the procedure author has read; a new world with the structure of a spent one but other numbers is still a new world for the procedure, and forbidding it would push the generators to unnatural roles. V15 keeps a batch from holding families whose errors come together.
5. **The reference is corrected, not widened:** the q6[on] code error and the undeclared limit on copy arguments (the audit's correction 1) are fixed, and the certificates are reused (fix 2). Its search limits stay test 5's.
6. **Every pool certificate is offered to every candidate the reference examines.** To keep this affordable, a certificate is offered only where the candidate keeps every unit it cites, and a rejection is remembered: a certificate rejected while a set of units is kept is rejected while fewer are kept.
7. **The run harness restarts a world that ran more than 60 seconds on battery,** and logs the power source (the lesson of the workshop's measurements, 10.8 and 10.12).

## 16. Changes from protocol v5
- **Procedure:** option C (Section 2.9): rounds 1 and 2 of the workshop's study (10.6 to 10.9), the conflicts-first loop (10.10 to 10.12), and the two changes of 10.13: the associative shape search skipped where a proven conflict excludes it, and the time limit held inside the scan for zero-divisor pairs. `procedure_v5.py` itself is unchanged.
- **Output:** the `refutations` field holds every conflict the procedure proved, in the form `{"drop", "proof"}` (4.7; 10.9, fix 1), and the informative fields of 4.7.
- **Reference (8.1):** q6[on] instances in associative ambients; copy instances with a product of two role names as an argument; every pool certificate offered to every candidate (10.9, fix 2).
- **Validator:** V11 also covers the 60 worlds of test 5 and the two roles of its batch A notes; V15 compares roles up to the nonzero numbers too; the variant worlds of T9, T10 and T13 carry the certificates over by relators, not numbers; T6 is required (it already was, by `T6_ENABLED`).
- **Scorer:** prints every "reported only" count of 8.3.
- **Text:** test 5's addendum 1 is written into Sections 0, 2.7, 4.3, 4.4a, 4.6 and 5; the run harness and the power rule into Sections 0 and 2.1; new limitations 14 to 16.
