# Blind test 3: post-hoc audit (exploratory, not evidence)

Written after the report. Nothing here changes the pre-registered outcome.

## 1. Outcome (from `results/report.json`, sha256 dd703463...)
- **Part A: PASS.** The procedure was correct with every proof on 27/27 worlds:
  - accuracy 1, false novelty 0, false familiarity 0, fork accuracy 6/6, quarantine notes valid 1;
  - baselines: ALWAYS_NEW 12/27, NO_SCOPE 12/27, DIMS_ONLY 5/27;
  - best baseline ALWAYS_NEW (tied with NO_SCOPE); McNemar b = 15, c = 0, p = 1/32768;
  - analysis accuracy: recall 1 and precision 1 for all five reasons (TYPE 7, SYMMETRY 6, SCOPE 9, SHAPE 47, BOUND 14 applicable pairs).
- **Part B: PASS.** Exact reopened lists 18/18, correct verdicts 18/18, 0 silent changes. REOPEN_NONE: exact lists 5/18, verdicts 8/18. REOPEN_ALL: exact lists 0/18, verdicts 18/18, micro precision 35/486.
- 0 worlds and 0 items excluded.
- Composition exceeded the minimums: 15 scope-sensitive worlds (8 required).
  - nebulium type: 4 dimmer, 3 switch;
  - scope-sensitive: 3 NEW, 5 FORK;
  - the visible relation mattered in 4 worlds;
  - 1 three-branch fork; 3 planet-X traps.

## 2. Integrity
- All seven seal hashes were re-verified before the run.
- Key hash `daee204d...`: published by the generator at 19:49:53Z, before the run, and confirmed by the build session without reading the key.
- Outputs hash `393e65da...`: published at 19:55Z, before the key was opened.
- **Reproducibility:** a second run gave byte-identical outputs (`393e65da...`) and an identical report (`dd703463...`).
- **No leakage:**
  - the generator's code (`key/*.py`) imports nothing from `procedure/` or `scorer/`, and makes no subprocess calls;
  - the generator wrote its own exact engine (`key/verify_key.py`, 56 KB, two-phase simplex), which reports `KEY CONSISTENT`.
- `progress.txt` shows visible progress at every stage.

## 3. A real protocol ambiguity, found by the generator (W8)
- **The text:** W8 says "the joint system with every candidate ... (actual factors; exact coefficients fixed; unknown ones free) ... is infeasible".
  - Literally (reading L), an exact-coefficient candidate is always present at its value.
  - The sealed validator implements "no combination" as any subset (reading C), so such a candidate may be absent.
  - The two differed only on one generated world, W-16.
- **What the generator did:** it stopped, as instruction 7 requires, and reported the problem in `key/generator_notes.md`. It resolved nothing itself.
- **What the owner chose:** option 1. W-16's new readings were redesigned so that W8 holds under both readings. Its role was kept (NEW, R3 TYPE as the sole reason, R1 BOUND, R2/R4 SHAPE). This happened before the key hash existed.
- **This audit's check:** all 9 NEW worlds satisfy W8 under both readings, so no validity verdict depends on the wording.
- **Lesson:** the protocol wording was mine and should have said "no subset". W8 is a validity condition; it never enters the procedure's answers.

## 4. Other interpretation points the generator recorded (it and the validator agree)
- W7's limit of three applies only after step 0 finds a deficit.
- The symmetry check is per candidate term.
- TYPE allows rational powers (e.g. ga^(-1/2)).
- `hidden_truth` was omitted for 3 worlds whose old and new readings come from different models. It holds within precision for the other 24.

## 5. Limits, as declared before the test
- The generator and the procedure author are the same model family. The generator was told the bias risk and used near-boundary readings, but shared habits cannot be excluded.
- "Correct" is defined by our rules: the test shows that they are computable with proofs, not that they are the best policy. Conservatism is a design choice.
- The comparison with baselines is partly definitional: NO_SCOPE fails scope-sensitive worlds by construction, and ALWAYS_NEW and DIMS_ONLY cannot fork.
- Coverage factors and return conditions were given, not inferred. Only registered relations can be found. Explanations are single relations.
- The worlds are formal. The 95% lower confidence bound is about 87% for 27/27 and about 81% for 18/18.
- Part B dependency tracking covers ledger, state and root; no Part A error propagated (none occurred).
- Nothing here is evidence of superiority over language models (LLM comparison 1), or of real discovery.

## 6. Exposure
The worlds have been seen only by the generator session and this build session. They stay unpublished until the project owner decides whether they will be shown to language models without the rules.
