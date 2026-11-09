# Blind test 5b: separate audit

Written by the procedure author after the outputs hash was published (2026-10-31T18:08Z) and the keys were opened.
It is not pre-registered and does not change the result: **test 5b FAILED** (both batches FAIL; C2, C3 and C4 fail
in both; C1 and C5 to C7 hold). Scripts and their outputs are in this folder; their hashes are at the end.

Marks: (computed) means a script in this folder computed it; (read) means read from code, logs or keys;
(argued) means my own reasoning, not computed and not from a published source.

## 1. Is the truth sound?

- No world was excluded; the sealed validator printed VALID for both batches (generators' logs). (read)
- Each generator wrote its own checker from the protocol alone, and it agrees with its key: A "KEY VERIFIED",
  B "ALL 30 WORLDS AND KEY PASSED ALL PROTOCOL CHECKS". So a third and a fourth implementation of the rules agree with the truth. (read)
- The procedure's certificates changed the truth in no world (scorer: `truth_changed_by_output` empty). (computed)
- So the 17 errors are real, by the test's own definition of truth.

## 2. The 17 wrong worlds

- All 22 worlds whose truth is FREEDOM, IMPOSSIBLE or KNOWN_SUFFICES are correct (11 per batch). Every error is in a
  world that needs a new kind: A 9 of 19 correct, B 12 of 19. (computed)
- Two kinds of error, as in test 5 (scorer's reported_only lists):
  - **R, missing refutation (12 worlds):** the output keeps a smaller drop set that a valid proof in the key refutes.
    A W-01, W-04, W-07, W-17, W-20, W-21; B W-15, W-21, W-22, W-25, W-26, W-27.
  - **W, missing witness (6 worlds):** the output says `no_witness` on a branch the key witnesses.
    A W-02, W-12, W-19, W-22; B W-19, W-22.
  - B W-22 has both, so 12 + 6 = 18 errors in 17 worlds.

## 3. Rules or search? (`diag_inject_5b.py`)

- **Check:** the same as test 5's audit (7.3), on the 5b procedure. A copy of the procedure starts with the key's
  witnesses and refutations in its memory, as if it had found them: witnesses in `witness_of`, refutations in
  `proof_of` and, through `proc_c3.add_conflict`, in the conflict list that drives its hitting-set loop. Everything
  else is its own code: search, minimality, statuses, merge, marks and proofs. The sealed files are not changed.
- **Result: 17 of 17.** In every wrong world it gives the truth's decision, every mark equals the truth's, every
  FORCED unit has a valid proof, and every witness is valid (the longest world took 376 s of a 900 s budget). (computed)
- **What this shows:** the procedure applies the rules correctly to the evidence it has; it lost on evidence it did
  not find. Together with test 5 (16 of 16), that is 33 of 33 wrong worlds over two tests.
- **What it does not show:** that the rules are right. The truth is computed from the same certificates by the
  reference, written by the same author, so this shows agreement of two programs on the same evidence (limit 2:
  "correct" is defined by our rules). Section 1's independent checkers are the stronger evidence for the truth.

## 4. Where the search falls short

### 4.1 Refutations (`refutation_shapes_5b.py`)

Every missing refutation is one case node (depth 1): a split by q12 or q14 on a pair of factors, or an inverse by
q13. (computed) And in every one of the 12 worlds the factor comes from a polynomial written in the role itself:
(read: the roles and the key's trees)

| group | worlds | the role says | the split the key uses |
| --- | --- | --- | --- |
| a name's polynomial, factored over Q(e1) (origin k02) | A W-01, B W-21, B W-22, B W-25 | e.g. `sol*sol = -9/4`; `u1*u1 - 2*u1 + 10 = 0`; `v1*v1 + 9 = 0` | (sol − 3/2·e1)(sol + 3/2·e1); (u1 − 1 − 3·e1)(u1 − 1 + 3·e1); (v1 − 3·e1)(v1 + 3·e1) |
| the same over Q(√2, e1) | A W-21 | `vo*vo = e1` | (vo − (√2/2)(1 + e1))(vo + (√2/2)(1 + e1)) |
| a name's polynomial over Q, in a non-associative branch | B W-15, B W-26, B W-27 | `(u1*u1)*u1 + 2*u1 = 0`; `m1*m1 - 3*m1 = 0`; `u1*u1 = 9/4` | (u1·u1 + 2)·u1 with a positive node; m1·(m1 − 3); (u1 − 3/2)(u1 + 3/2) |
| a word (a product of names) | A W-04, W-07, W-17, W-20 | `ny*ox = 3/7`; four anticommuting squares (ω = da·ke·lu·mi, ω·ω = 441); `bo*(ce*fu) + (bo*ce)*fu = 0`; `hu*ip = e1` | (7/3·ox·ny)(7/3·ox·ny − 1); (ω − 21)(ω + 21); (bo·ce)·fu; (ip·hu)(ip·hu − e1) |

Why the procedure missed them (read: `procedure_v5.small_forms`, `proc_c.minpoly_pairs`, `proc_c.search`):
- Its split pairs are linear forms over the first 4 names with coefficients in {−1, 0, 1} (and ±sqrt(c) as a
  constant), plus the factors of a name's minimal polynomial.
- Those minimal polynomials are factored over Q only, so x² + 9/4 and x² − 2x + 10 do not split. The linear forms
  reach e1 at most with coefficient ±1, while these factors need 3/2·e1, 3·e1 or 1 ± 3·e1.
- They are computed in associative ambients only, so a branch that drops q5 gets none, even for `m1*m1 - 3*m1 = 0`,
  whose factorization m1·(m1 − 3) needs no associativity.
- Words are never factors: only names.
These are the narrow parts declared in limit 14 ("refutations split on at most 8 pairs of linear forms over the
first 4 names with coefficients in {-1, 0, 1}, plus the factors of minimal polynomials"). The reference has the same
limits (limit 10), so the generators' certificates supplied every one of them, as the safeguard intended.

### 4.2 Witnesses (`witness_shapes_5b.py`, and the output's `searched` records)

| worlds | the key's witness | the procedure's record |
| --- | --- | --- |
| A W-02, A W-22, B W-19 | dimension 8, not associative (octonion-like, with q12 and q13 certificates) | non-associative search complete to dimension 4 (A W-22: complete to 3, partial at 4) |
| A W-12, A W-19 | dimension 4, not associative, coefficients −4/9; −3, −4, −1/2 | non-associative search "complete to dimension 4" |
| B W-22 | dimension 4, associative (quaternion-like, ±9) | associative search complete to dimension 2, partial from 3 |

(computed and read) In five of the six, change A skipped the associative half because a proven conflict excludes
every associative table; the key's witnesses there are indeed not associative. In B W-22 the associative search ran
and stopped partway through dimension 3. The misses are again declared narrow parts (limit
14: non-associative shapes go to dimension 4 only, and free unknowns are tried at 0, ±1, ±2 only). A W-12 and A W-19
show limit 15 at work: the record "complete to dimension 4" stands next to a dimension-4 example. It means "every
shape tried with its guesses", not "no example exists".

### 4.3 Time did not bind

No world came near the hour (longest: A W-28, 1412 s; B W-22, 960 s), and phase 1 stayed under its 2700 s limit in
all 60 worlds. (computed) One world (A W-28) restarted after more than 60 s on battery, as the harness is written to
do, and was then correct.

### 4.4 Why the new worlds found these holes

The generator brief (protocol section 11) asks for unusual relations and numbers. The search guesses small numbers
(±1, ±2) and names only. So the brief points straight at the narrow parts of limit 14. In the workshop (10.12) and in
the regression run, option C was right on the worlds of test 5, which it was developed on; on new worlds it is not
(limit 16). The measured improvement did not generalize.

## 5. Generator A's remark on q14 (`q14_check_5b.py`)

- **The claim** (A's progress.txt and final message): over k01, every algebra in W that keeps q14 is R itself, so a
  candidate keeping q14 has no model when the role has no real solution, but no certificate form can say so.
- **Argument** (argued, not computed; uses only what W fixes: a finite-dimensional real unital algebra with
  bilinear multiplication, no associativity or commutativity):
  1. q14 orders R·1 in the usual way (1 = 1·1 > 0, and r·1 = (√r·1)² > 0 for r > 0), so multiplying by a positive
     real keeps signs, and every x ≠ 0 has x·x > 0 (x·x = (−x)·(−x)).
  2. If 0 < z < ε·1 for every real ε > 0, then (ε·1 − z)·z > 0 gives z·z < ε·z: z·z is infinitesimal against z.
     Repeating gives z, z·z, (z·z)·(z·z), ... in ever smaller Archimedean classes. A totally ordered real vector
     space of dimension n has at most n classes, so no positive infinitesimal exists.
  3. Likewise, if z > r·1 for every r, then (z − r·1)·z > 0 gives z·z > r·z, and the squares climb through ever
     larger classes: impossible. So every x is within every ε·1 of t·1, t = sup{r : r·1 < x}, and x = t·1.
  So the algebra is R, of dimension 1. This agrees with limit 5 ("q14 is certified only in dimension 1") and shows
  that limit loses no witness; what it loses is refutations.
- **Where it matters:** two truth branches keep q14 over k01, both `no_witness`, both in worlds whose role has no
  real solution (computed): A W-04 and A W-17, branch {q5, q6}. By the argument they have no model, but no proof form
  of section 4 refutes them, so they stay branches of the truth. The procedure output the same branch in both.
- **Effect on the result:** none. Both worlds are wrong for another reason (section 4.1), and the truth is defined
  by certificates (8.1). It is a sharper instance of limit 5: some branches are NO_WITNESS by the limits of
  certification, not by mathematics.

## 6. Other notes

1. **Pooled numbers** (`pooled_5b.py`): decision 43/60 for the procedure and 43/60 for COARSE (b = 8, c = 8,
   p = 0.60). Over both batches the procedure does not beat the best baseline at all. (computed)
2. **Generator A** ran out of its usage limit once and resumed (its log says so). It wrote scratch copies of draft
   worlds to temp folders outside its batch folder and deleted them at the end. That is outside the letter of its
   rule 2; no project folder is named, and blindness is not affected. (read)
3. **Generator B** numbered its worlds by verdict (W-01 to W-03 FREEDOM, W-04 to W-06 IMPOSSIBLE, ..., W-27 to W-30
   NO_WITNESS). The procedure does not read ids, so no effect; a future brief should ask for a shuffled order. Its
   log also says it "verified mathematically" that its remaining undecided candidates have neither witnesses nor
   refutations: an overclaim, on which the truth does not rely. (read)
4. **No shared code error** like test 5's correction 1 showed up: the injection check is 17 of 17, and the four
   implementations of the truth agree. (computed and read)

## 7. What the failure says, and what it does not

- **Pre-registered (section 9):** FAIL returns the rules, or their implementation, to design.
- **What the audit points to:** the implementation, and in it the search for evidence, as in test 5. The rules gave
  the truth whenever the evidence was there (17 of 17 here, 16 of 16 in test 5).
- **Not shown:** that the rules are right (they define "correct", limit 2); that a wider search would pass (only a
  new sealed test on new worlds can show that); anything outside W.

## 8. Real strengths

- No false witness, no silent collapse, no silent choice in 60 new worlds (and in test 5's 60).
- All 22 FREEDOM, IMPOSSIBLE and KNOWN_SUFFICES worlds correct; C1 holds in both batches (0.77 and 0.90).
- Where it found no evidence, it said `no_witness` with a record of how far it searched, instead of guessing.
- With the evidence, its decisions, marks and proofs match the truth in every wrong world.

## 9. Lessons (proposals, not decided)

1. **Take split factors from the role, not from a list of small guesses:** factor the role's own polynomials of a
   name over Q, over Q(e1) in k02 and over Q(√c); use the words written in the role as factors; and allow a name's
   own powers as written (`x*x`) in non-associative branches. Every refutation missing here has that shape.
2. **Witness shapes:** Cayley-Dickson doubling up to dimension 8, and parameters taken from the role's constants
   instead of 0, ±1, ±2.
3. **Certificate forms:** a form for "this candidate keeps q14 over k01 and the role has no real solution" would
   close the gap of section 5 (a theory question: limit 5).
4. **Generator brief:** ask for a shuffled order of worlds.
5. **Any of these must be sealed and tested on new worlds from new generator runs.** The worlds of 5b are now spent
   for that purpose, as test 5's were.
