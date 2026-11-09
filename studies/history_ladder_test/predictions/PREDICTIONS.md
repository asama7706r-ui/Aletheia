# Predictions of the six rules for the four coded demands (registered BEFORE the comparison)

Written 2026-10-22, after PREREG.md, PREREG_ADDENDUM_1, CODING_CHECK and PREREG_ADDENDUM_2, and before any comparison with history. This file states only what each rule predicts. It never says what history did.

## 0. Inputs
- **The demands** (v0.5 worlds read against the test-5 seed tower, translated by rules T1-T4): `roles/C1_tessarines.json`, `roles/C2_multicomplex.json`, `roles/C3_hyperbolic_quaternions.json`, `roles/C4_split_biquaternions.json`. They were written by `tools/make_roles.py`, and all pass the v0.5 reader.
  - **C1** (origin: complex numbers, e1 = i): `j*j = 1`; j differs from 1, -1, e1 and -e1.
  - **C2** (origin: complex numbers): `h*h = -1`, `l*l = -1`; h, l, 1 and e1 pairwise differ, also up to sign.
  - **C3** (origin: reals): `i*i = j*j = k*k = 1`, `i*j = k = -(j*i)`, `j*k = i = -(k*j)`, `k*i = j = -(i*k)`; 1, i, j and k pairwise differ, also up to sign.
  - **C4** (origin: reals; origin outside the tower, T2): Hamilton's quaternion rules for i, j, k, plus `w*w = 1`; 1, i, j, k and w pairwise differ, also up to sign.
- **The old rules:** list v1 (q1-q14) for origin reals; the complex list (q1-q13) for origin complex. q1 and q2 are protected, except for MAXCON.

## 1. The witness space (declared now)
- **W**: finite-dimensional unital algebras over the reals that contain the old kind as a subalgebra, given by a multiplication table on a basis and extended bilinearly. This follows the method of test-5 decision 4 (a candidate table, checked directly).
- **In W,** q3, q4, q7, q8, q9, q10 and q11 hold by construction, and an old real r acts on any element as scalar multiplication. So those seven rules never enter a minimal drop set, and a relaxation that would need to break them is outside W and not predicted.
- **Limit, stated before the comparison:** W cannot show a disagreement with history on additive, distributive or unit laws. The rules that can discriminate are q5 (associativity), q6 (commutativity), q12 (no zero divisors), q13 (inverses) and q14 (order).
- **A drop set is "witnessed"** when an explicit algebra in W satisfies the demand and every kept rule (`tools/check_witnesses.py`, exact arithmetic). It is "refuted" when a proof (section 2) derives a contradiction from the demand and the kept rules. It is "undecided" when neither holds. Undecided sets are reported and never counted as predictions.
- **For MAXCON,** which may drop q1 and q2: **W'** = W plus unital finite-dimensional algebras over any field, plus the zero ring. The zero ring is excluded in all four cases, because every demand contains a `!=` between two named elements.

## 2. Lemmas (proofs inside W)
- **Z.** If u*u = 1 and u differs from 1 and -1, then (1 + u)*(1 - u) = 1 - u + u - u*u = 0 with both factors nonzero, so q12 fails.
- **I.** If a*b = 0 with a and b nonzero, and q5 and q13 hold, then b = (a^-1*a)*b = a^-1*(a*b) = a^-1*0 = 0, a contradiction. So q5 or q13 must fall.
- **O.** q14 forbids zero divisors and forbids x*x = -1:
  - by trichotomy and q14's sum rule, a nonzero a has a > 0 or -a > 0, so plus or minus a*b is a product of two positives, hence positive, hence nonzero;
  - 1 > 0 (otherwise -1 > 0 and 1 = (-1)*(-1) > 0); and x*x = (+-x)*(+-x) > 0, so x*x = -1 would give 0 > 1.
- **K.** If x*y = z and y*x = -z, with z*z = +1 or -1, then q6 fails: q6 would give z = -z, so z = (1/2)*(z + z) = 0 and z*z = 0, contradicting q1 or q2.
- **A3** (C3 only). (i*j)*j = k*j = -i and i*(j*j) = i*1 = i. So q5 would give i = -i, hence i = 0 and 1 = i*i = 0. q5 fails.

## 3. The facts per case
- **C1.**
  - Z with u = j: q12 always falls.
  - By I, q5 or q13 falls too.
  - Witnessed: {q12, q13}, by the tessarines (commutative and associative).
  - Undecided: {q5, q12}, a non-associative algebra in which every nonzero element has an inverse; no witness is known and no proof refutes it.
  - q6 alone cannot help: Z holds without q6.
  - Minimal witnessed sets: **{q12, q13}** only.
- **C2.**
  - If q6 holds, then (h - i)*(h + i) = h*i - i*h = 0 with both factors nonzero, so q12 falls, and by I q5 or q13 falls too.
  - Witnessed: {q12, q13}, by the tricomplex numbers.
  - Witnessed: {q6}, by the quaternions, with e1 = i, h = j, l = (3i + 4j)/5. H is a division ring.
  - Undecided: {q5, q12}.
  - Every proper subset of either witnessed set is refuted.
  - Minimal witnessed sets: **{q6}** and **{q12, q13}**. These are incomparable by containment.
- **C3.**
  - K (i*j = k, j*i = -k): q6 falls. A3: q5 falls. Z with u = i: q12 falls. O: q14 falls.
  - Witnessed: {q5, q6, q12, q13, q14}, by Macfarlane's 4-dimensional table (1 + i has no right inverse).
  - Undecided: {q5, q6, q12, q14}, which keeps inverses. Hence the minimality of the witnessed set in the q13 direction is undecided.
  - Minimal witnessed set: **{q5, q6, q12, q13, q14}**, with the undecided subset noted.
- **C4.**
  - K (i*j = k, j*i = -k): q6 falls. O (i*i = -1): q14 falls. Z with u = w: q12 falls. I: q5 or q13 falls.
  - Witnessed: {q6, q12, q13, q14}, by H (+) H (w central).
  - Undecided: {q5, q6, q12, q14}.
  - Every proper subset of {q6, q12, q13, q14} is refuted.
  - Minimal witnessed set: **{q6, q12, q13, q14}**.
- **The extra MAXCON branches, through dropping q2:**
  - **C3:** the same rules over GF(2) form a commutative, associative algebra (A3 and K need 1/2, which does not exist in characteristic 2). It fails q12, q13 and q14 (by Z read mod 2, and because characteristic 2 cannot be ordered).
    - In characteristic other than 2, A3 still applies. So **{q2, q12, q13, q14}** is minimal in W'.
  - **C4:** likewise, H (+) H read over GF(2) gives **{q2, q12, q13, q14}**.
  - **C1, C2:** dropping q2 gains nothing. Z, and the C2 product (h - i)*(h + i), hold over every field, so every set containing q2 contains a smaller witnessed set.

## 4. The predictions (drop sets; "|" separates branches)
| rule | C1 (origin C) | C2 (origin C) | C3 (origin R) | C4 (origin R) |
|---|---|---|---|---|
| OURS | {q12, q13} | BRANCHES {q6} \| {q12, q13} | {q5, q6, q12, q13, q14} | {q6, q12, q13, q14} |
| COUNT | {q12, q13} | {q6} | {q5, q6, q12, q13, q14} | {q6, q12, q13, q14} |
| MAXCON | {q12, q13} | {q6} \| {q12, q13} | {q5, q6, q12, q13, q14} \| {q2, q12, q13, q14} | {q6, q12, q13, q14} \| {q2, q12, q13, q14} |
| ORDER | all of q3-q13 | {q6} | all of q3-q14 | all of q3-q14 |
| ASSOC | {q12, q13} | {q6} \| {q12, q13} | no answer (q5 is forced to fall) | {q6, q12, q13, q14} |
| FIRST | {q12, q13} | {q6} | {q5, q6, q12, q13, q14} | {q6, q12, q13, q14} |

**How the rival entries follow:**
- **ORDER** drops q14, q6, q5, then q3, q4, q7, q8, q9, q10, q11, q12, q13, and stops at the first prefix with a witness in W.
  - In C1, C3 and C4, no prefix before q13 has one: before q12 the demand forces zero divisors; at q12, the prefix keeps q13 with q5 dropped, which is the undecided case.
  - In C2, the prefix {q6} is witnessed by H.
- **FIRST** takes the first witnessed set by size, then by rule ids. Undecided sets are skipped.
- **COUNT** takes the witnessed sets of fewest rules.
- **Undecided sets are never counted** as a rule's prediction, for any rule. They are listed in section 3 so that no reader takes the predictions as complete.

## 5. Verdict forms of OURS
- C1: NEW_KIND {q12, q13}.
- C2: BRANCHES {q6} | {q12, q13}. The decider is whether the new units commute with i, or whether there are no zero divisors.
- C3: NEW_KIND {q5, q6, q12, q13, q14}.
- C4: NEW_KIND {q6, q12, q13, q14}.

KNOWN_SUFFICES does not apply in any case. The origin kind cannot meet any demand: in C, x*x = 1 only for x = 1 or -1, and x*x = -1 only for x = i or -i; R contains no anticommuting units.
