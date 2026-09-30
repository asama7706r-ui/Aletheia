# Blind test 2: decide or fork (Part A) and grades of zero (Part B)

- **Sealed:** 2026-09-30T04:46:48Z.
- **Outcome:** Part A **PASS**, Part B **PASS**, 0 exclusions.
- **Protocol:** [`procedure/protocol_v2.md`](procedure/protocol_v2.md), sealed. A copy is in this folder.

## Questions
- **Part A, 30 worlds.** Given laws and observations of nonzero quantities:
  - answer DETERMINED when the givens determine the algebraic level;
  - otherwise answer FORK, listing every viable branch and, for each non-last branch, a decisive set of observations with checkable certificates;
  - answer CONTRADICTION when nothing fits;
  - answer UNDERDETERMINED when a free parameter changes the answer.
- **Part B, 18 worlds.** Given a law with a candidate term, declared constants, symmetries and exact observations with an observer's resolution, classify the term as one of: TYPE_IMPOSSIBLE, SYMMETRY_ZERO, INCIDENTAL, ACTIVE (with its exact interval), BOUNDED (with its exact bound), UNCONSTRAINED, CONFLICT.
  - The classification must avoid "false death": calling a merely undetected term exactly zero.

## Method
- Same design as blind test 1: sealed procedure and scorer, a separate generator session, key hash published first, outputs hash published before the key was opened, and the report published verbatim.
- The scorer does **not** import the procedure. It checks every key claim by elementary means:
  - witness matrices;
  - certificate expansion;
  - its own Groebner bases and rational solutions.
- The generator's own verification checked 2496 items with 0 failures.

## Results (`results/report.json`)
| Part A (30) | correct | forks correct (10) | over-fork |
|---|---|---|---|
| **procedure** | **30/30** | **10/10** (valid decisive sets and certificates) | **0** |
| V1D: role rule, cannot fork | 20 | 0 | 0 |
| OCC: first viable level, cannot fork | 17 | 0 | 0 |
| FORKALL: fork whenever possible | 8 | 2 | 11 |

| Part B (18) | correct | false death | conflicts detected |
|---|---|---|---|
| **procedure** | **18/18** | **0** | **3/3** |
| THRESH: undetected = zero | 5 | 4/4 | 2/3 |
| MENTION: mentioned = active | 6 | 0 | 0/3 |
| NOSYM: no symmetry reasoning | 12 | 0 | 2/3 |

## Post-hoc audit
- **Scorer mutation test** (after the fact): 14/14 deliberate key corruptions were caught, and all originals were accepted. Lesson: mutation-test the scorer before sealing. This was done for LLM comparison 1.
- **Extra material from the generator:** `key/aux_proofs.json` holds extra proofs. It is outside the key hash, and the scorer never reads it.
- **Limits:**
  - "correct" is defined by our own rules, so the test shows the rules are computable, not that they are the best policy;
  - no worlds with 4 generators;
  - the generator is from the same model family;
  - the 95% confidence interval lower bounds are about 88% (30/30) and 81% (18/18).
- **Exposure:** these 48 worlds were later given to four LLMs ([LLM comparison 1](../aletheia_llm_compare_1/REPORT.md)), so they are no longer hidden.

## Reproduce
From this folder, with Python 3 and sympy:
```
python procedure/procedure_v2.py run worlds results/outputs_rerun.json
python procedure/score_v2.py worlds key/key.json results/outputs_rerun.json results/report_rerun.json
```
Both files reproduce the published ones bit for bit:
- outputs: `7cb8c05a…`
- report: `4d073404…`
