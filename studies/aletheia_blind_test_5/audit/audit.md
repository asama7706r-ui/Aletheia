# Blind test 5: the audit (2026-10-23)

Written by the procedure author (Claude) after the outputs hashes were published and the keys opened (protocol_v5.md, Section 0, order step 7). It is not pre-registered and changes no result. **The pre-registered result stands: both batches FAIL, so the test fails.** Every number below is a diagnostic. The scripts and their outputs are in this folder.

## 1. The record
- **Seal:** 2026-10-23T09:45:35Z (`SEALED_HASHES.txt`, c7723066…). `PROTOCOL_ADDENDUM_1.md` (clarifications only) was sealed at 10:55:00Z (56ff3c17…), before any test world existed.
- **Generators:**
  - Batch A: claude-opus-5-5, in a separate Claude Code session.
  - Batch B: "Gemini 4 Argon (High)", run locally.
  - Both logged the sealed validator's `VALID`. After generation, the 13 sealed files in each package still had their sealed hashes.
- **Worlds and keys:** their hashes were recomputed, found equal to each `progress.txt`, and published before the run:

  | batch | worlds | key |
  |---|---|---|
  | A | 61d0ea68… | f3e8abde… |
  | B | 1ac7666e… | eea7894b… |

- **Run:**
  - Harness: `run/run_batches.py` (40dc9f01…), with Python 3.12.10 and sympy 1.14.0. Exit 0 for both batches.
  - Batch A: 13:23:24Z to 14:29:48Z, 3984 s. One world, A W-28, hit the 3600 s limit.
  - Batch B: 29 s.
- **Outputs and keys:** the outputs hashes were published before any key was opened (A f29f45a0…, B af55c1ec…). The keys were then copied into the lab, and their hashes were equal to the published ones.
- **Scorer:**
  - Batch A took 830 s and batch B 127 s.
  - Reports: bb19233d… (A) and d61c630a… (B).
  - The printed text was posted verbatim on the test page, section 6, and diffed equal to `results/score_X.txt`.
- **What the procedure author saw before the outputs hash:**
  - From `progress.txt`, by a search command: the hash, model, `VALID` and stage lines. One line of B says that its key adds refutations for two candidates in W-28 to W-30.
  - Batch A's generator notes, including their last update: two general notes, quoting no role.
  - No world, no key and no validator output. The procedure was sealed before all of it.

## 2. Is the truth sound?
- No world was excluded, and every key certificate passed the sealed checker (V8, V9).
- Each generator wrote its own `key/verify_key.py` from the protocol alone. Each passes 30 of 30 on its key (`key/verify_output.txt` in each package). So a third implementation of the rules agrees with the keys.
- The procedure's certificates changed no truth: it found no witness or refutation that the key and the reference lacked.
- **Conclusion:** within the test's own definitions (limit 2), the 16 wrong decisions are real.

## 3. The 16 wrong worlds (`audit_out.txt`, part 2)
**Missing witness:** same drop sets as the truth, but a witnessed branch is reported `no_witness`.

| world | truth | what the procedure missed | why (section 5) |
|---|---|---|---|
| A W-04 (T14) | BRANCHES | the witness of {q14, q6}, a quotient of the 8-dimensional template | needs the zero divisor zi − 2·xa·yo + 1 (coefficient 2) |
| A W-19 | NEW_KIND | a 3-dim witness | the template does not close; the witness needs ha·ha = ha and the other free products 0 |
| A W-21 | BRANCHES | the 6-dim witness of {q12, q13, q6} | the same pattern over k02 |
| A W-22 | NEW_KIND | a 4-dim non-associative witness | the products the role leaves free (zu·ve, wo·zu, zu·wo) must be chosen; the key sets them to 0 |
| A W-24 | BRANCHES | two 3-dim witnesses | xe·xe and yi·yi are free; the key's witnesses use idempotents, and squares equal to −1 |
| B W-18 (T14) | NEW_KIND | the quaternion witness of {q14, q6} | needs the quotient u2·u2 + 5 = 0 (constant 5) |
| B W-19 (T14) | NEW_KIND | the same | needs the quotient u2·u2 + 7 = 0 |

**Missing refutation:** the output keeps a candidate that the truth refutes.

| world | truth | candidates kept | refuted by |
|---|---|---|---|
| A W-06 (T14) | BRANCHES | 1, and also the witness of {q6, q6[on]} | the key only |
| A W-09 (T6) | NO_WITNESS | 2 (a mirror pair) | the key only |
| A W-10 | NEW_KIND | the empty candidate {} | the key only: the split fa·fa·(fa − 1) = 0 has a factor of degree 2 |
| A W-18 | NEW_KIND | 1 | the key only |
| A W-28 (T6) | NO_WITNESS | 3 | the key only for 2; the reference's search for {q5, q6[on]}. This world hit the time limit |
| A W-29 | BRANCHES | 1 | the key only |
| B W-28, W-29, W-30 | BRANCHES | {q6} | the key only (its refutations of {q6, q12} and {q6, q13}) |

So 7 worlds miss only witnesses and 9 miss refutations. A W-06 misses both.

## 4. Rules or evidence? (`diag_inject.py`)
`diag_inject.py` runs a copy of the procedure; the sealed file is not changed.
- **The change:** its memory of found certificates starts with the key's witnesses and refutations, as if it had found them itself.
- **What stays the procedure's own:** its search, minimality, statuses, mirror merge, marks and proofs.
- **The comparison:** with the truth the sealed scorer printed. Marks are checked against the reference's marks, every FORCED unit must carry a proof the sealed checker accepts, and every witness must pass.

**Result: 16 of 16** (`diag_inject_out.txt`). In every wrong world, the procedure's own code, given the key's certificates, returns:
- the truth's decision;
- marks equal to the reference's;
- a valid proof for every FORCED unit;
- valid witnesses.

A W-28 used the whole 900 s budget of this diagnostic and still gave the truth.

So in all 60 worlds the procedure applied the rules correctly to the evidence it had:
- in 44 worlds it found enough evidence;
- in the other 16, what it lacked is exactly what the key supplied.

The errors are missing evidence, not wrong rules. "Correctly" here means in agreement with the reference (the same author) and with the generators' own verifiers (independent code).

## 5. Where the search falls short (`procedure/procedure_v5.py`)
### 5.1 Witnesses
1. **Quotients only by zero divisors with coefficients ±1.**
   - `zero_divisor_elements` tries b_i, 1 + b_i, 1 − b_i and b_i ± b_j only.
   - `diag_quotients.py` also tries c + b_i and c + b_i + d·b_j, with small rational c and d.
   - With that wider list, the procedure's own code builds the 4-dim witnesses of B W-18, B W-19, A W-04 and A W-06, in 13 to 236 s. The sealed checker accepts all four (`diag_quotients_out.txt`).
2. **Few guesses when the template does not close.** When the role leaves products free, `guesses` adds only "x and y commute" or "x and y anticommute". The witnesses of A W-19, W-21, W-22 and W-24 need other choices: x·x = x, x·x = 0, x·x = −1, and "the other products are 0". This was not run, only read from the code and the keys.

### 5.2 Refutations
- `search` and `small_forms` split only on linear forms with coefficients in {−1, 0, 1}, at most 8 pairs per node.
- The reference has the same limits (Section 8.1). So 11 of the 12 candidates are missed by both programs: the shared blind spot that limit 10 declared.
- The generators' certificates caught every one, as limit 10 foresaw. Batch A's generator named two such patterns in its notes: factors of degree 2, and coefficients outside {−1, 0, 1}.
- The twelfth candidate, A W-28 {q5, q6[on]}, is refuted by the reference's own search. The procedure ran out of time on that world.

## 6. Other findings
1. **Missing counts in the scorer.** The sealed scorer does not print three "reported only" counts of Section 8.3. Computed here:

   | count | A | B |
   |---|---|---|
   | branches the output adds where a valid proof decides | 9, in 6 worlds | 3, in 3 worlds |
   | unmerged mirror twins | 0 | 0 |
   | NO_WITNESS answers where the truth has a witness | 6 | 5 |

2. **By verdict:**
   - FREEDOM, IMPOSSIBLE and KNOWN_SUFFICES: all correct, 11 of 11 in each batch.
   - All errors are in the verdicts with branches: A 11 of 19 wrong, B 5 of 19 wrong.
3. **By trap** (`audit_out.txt`, part 5):
   - T14 (a witness in a quotient): A 1 of 3, B 0 of 2.
   - T6 (the mirror pair): A 0 of 2, B 2 of 2.
   - T3 (a split rule): A 2 of 8, B 3 of 6.
   - T11 (a forced fall): A 6 of 11, B 7 of 7.
4. **Families in batch B.** Grouping roles up to renaming the generators and changing the numbers gives 26 families for 30 worlds:
   - the families with more than one world are (W-12, W-13), (W-18, W-19) and (W-28, W-29, W-30);
   - all five B errors are in the last two;
   - batch A has 30 distinct roles;
   - V15 compares roles up to renaming only, so the same structure with other numbers passes it.
5. **The T9 note of batch A's generator.** With `f03` and an unbracketed chain, the T9 condition can hold only because re-bracketing renumbers the relators, so the key's proofs drop.
   - Batch A avoided it.
   - Batch B's two T9 worlds (W-16, W-17) have no frame and no key refutation, so they are unaffected.
6. **The comparison is asymmetric (limit 11).** The baselines read the true classification. Every certificate the procedure misses counts against it and never against a baseline. So C4 compared the procedure's rules with its own search against wrong rules with complete evidence.
7. **Time.** One world (A W-28) hit the limit, and the others took at most 210 s.
8. **A check of mine that was wrong.** My first rules check in `audit_v5.py` assembled a truth from the output's own certificates, with the search off. It was invalid: an output carries only the proofs of its FORCED units, not every refutation the procedure found. I removed it before this write-up; `diag_inject.py` replaces it.

## 7. What the FAIL says, and what it does not
- **Pre-registered (Section 9):** a FAIL returns the rules, or their implementation, to design.
- **The audit points to the implementation, namely the search for witnesses and refutations, and not to the rules:**
  - section 4;
  - no false witness, no silent collapse and no silent choice in 60 worlds;
  - the marks are right in every world whose decision is right.
- **Not shown:**
  - that the rules are right: correctness is defined by them (limit 2);
  - that a wider search would pass: the diagnostics ran on worlds already seen, so only a new sealed test with new worlds can show it;
  - anything outside W.
- **Real strengths:**
  - the safety criteria C5 to C7 held in both batches;
  - the procedure said "no witness" plainly instead of guessing;
  - FREEDOM, IMPOSSIBLE and KNOWN_SUFFICES were right in all 22 worlds;
  - batch B passed C1 to C3.

## 8. Lessons for a next test (proposals, not decisions)
1. V15 should compare roles up to renaming and numbers.
2. The scorer should print every count of Section 8.3.
3. T9 should not depend on relator numbering.
4. Any widened search must be sealed and tested on new worlds from new generator runs. The worlds of test 5 are spent for that purpose, because the procedure author has read them.
