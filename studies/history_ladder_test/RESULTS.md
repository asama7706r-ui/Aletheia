# The ladder theory against history: results (2026-10-22)

The comparison of the registered predictions with history. Written after posting the hash of `predictions/PREDICTIONS_SHA256.txt` (260af655…) on the Notion page (section 10.4). Nothing in the predictions was changed after that.

## 1. What history built (Claude's computation, `tools/check_witnesses.py`, exact)
All four systems are finite-dimensional unital real algebras containing their origin, so q1-q4 and q7-q11 hold in each.

| case | system as published | q5 assoc. | q6 comm. | q12 no zero div. | q13 inverses | q14 order | history's drop set |
|---|---|---|---|---|---|---|---|
| C1 | Cockle's tessarines (1848) | holds | holds | fails: (1+j)(1-j) = 0 | fails: 1+j | (origin C, not scored) | {q12, q13} |
| C2 | Segre's tricomplex numbers (1892) | holds | holds | fails: (h-i)(h+i) = 0 | fails: h-i | (origin C) | {q12, q13} |
| C3 | Macfarlane's hyperbolic quaternions (1891) | fails: (ii)j != i(ij) | fails: ij != ji | fails: (1+i)(1-i) = 0 | fails: 1+i | fails (lemma O) | {q5, q6, q12, q13, q14} |
| C4 | Clifford's biquaternions, w^2 = 1, w central (1873) | holds | fails: ij != ji | fails: (1+w)(1-w) = 0 | fails: 1+w | fails: i^2 = -1 | {q6, q12, q13, q14} |

## 2. The comparison (PREREG section 4)
| rule | C1 | C2 | C3 | C4 | AGREE |
|---|---|---|---|---|---|
| OURS | AGREE | AGREE (one of two branches) | AGREE | AGREE | 4 / 4 |
| COUNT | AGREE | UNDER (predicts {q6}: history kept commutativity) | AGREE | AGREE | 3 / 4 |
| FIRST | AGREE | UNDER (as COUNT) | AGREE | AGREE | 3 / 4 |
| ASSOC | AGREE | AGREE (one of two branches) | OUT (no answer) | AGREE | 3 / 4 |
| MAXCON | AGREE | AGREE (one of two branches) | AGREE, plus a branch where 1 + 1 = 0 | AGREE, plus a branch where 1 + 1 = 0 | 4 / 4 |
| ORDER | UNDER (drops everything) | UNDER (predicts {q6}) | UNDER (drops everything) | UNDER (drops everything) | 0 / 4 |

**The branches of OURS (C2):**
- {q6} is the non-commutative branch, which keeps division: the quaternions, which contain C. That branch had been built before Segre: Hamilton's quaternions, communicated "beginning in 1844" (W01).
- {q12, q13} is the commutative branch, with zero divisors.
- History built both branches, and Segre chose the commutative one knowing the other. W01: "Segre read [[W. R. Hamilton]]'s ''Lectures on Quaternions'' (1853)". His stated reason was to keep the laws of ordinary arithmetic (C2, coded quotations). That reason is exactly what T1 kept out of the demand.

**A correction to the PREREG wording.** Section 4 says UNDER "is impossible if the demand and the list are right". That holds only for drops that are forced. The UNDER results above are choices of an unforced drop (COUNT, FIRST and ORDER drop commutativity in C2; ORDER drops the additive laws everywhere). They are disagreements of those rules, not coding errors.

## 3. Hypothesis H1 (counted cases C1, C2, C4; C3 excluded)
| case | (i) OURS gives a single drop set | (ii) extra relations, or later replacement | both |
|---|---|---|---|
| C1 | yes | no: Cockle's ij = ji follows from the kept q6, k = ij is a name, and Segre's bicomplex numbers are the same algebra in another basis | no |
| C2 | no (two branches) | — | no |
| C4 | yes | yes: "w commutes with i, j, k" does not follow from the demand once q6 has fallen; Clifford chose it | yes |

H1 holds in 1 of 3 counted cases. It needed at least half. **H1 is not supported.**
- C3 (not counted, because it inspired H1) does fit H1's picture: Macfarlane replaced his relations in 1900 to regain associativity.

## 4. What this shows, and what it does not
1. **Most cases are forced.** In C1, C3 and C4, the demand forces a single drop set. Any rule that computes forced drops agrees there: OURS, COUNT, FIRST, and ASSOC except in C3. These three cases show that our list and our computation describe the historical systems correctly. They do not show that our preference rule is better than another.
2. **One case discriminates: C2.**
   - Containment (OURS) answers "two branches", and history built both, with Segre choosing knowingly between them.
   - Fewest-rules (COUNT), first-found (FIRST) and the textbook order (ORDER) each predict only the quaternion branch, against Segre's actual construction.
   - This is a single case, but it is the one place where the theories differ, and there history went OURS' way.
3. **Protection matters.** MAXCON matches history too, but in C3 and C4 it adds a branch in which old arithmetic collapses (1 + 1 = 0). This is the test-5 trap 1 ("the bits world") appearing in real history cases. Our protected rule q2 is what removes it.
4. **ORDER fails everywhere** partly because of its registered definition: it drops the additive laws before reaching the zero-divisor rule. This is a weakness of that baseline as written, not a finding about history.
5. **H1 is not supported:** in the counted cases, the authors mostly did not revise the demand. In C2 the real choice was between branches that our theory itself produces.

## 5. Limits
- Four cases: a qualitative probe; no significance is claimed.
- The witness space W cannot show disagreements on additive, distributive or unit laws (PREDICTIONS section 1).
- Undecided sets (non-associative, keeping inverses) were neither witnessed nor refuted, and are not counted for any rule.
- C4's origin is outside the tower (T2: the quaternion relations are given). C4's quotations rest on the coder's transcription of Clifford's scan, which Claude did not check against the images.
- The coder used its own numbering of the properties. This has no effect: the properties above are Claude's computation.
- Hindsight: Claude knew this history in outline. The case pool came from a fixed rule, the coding was done by an independent model with verbatim quotations, and the predictions were registered before this comparison.
