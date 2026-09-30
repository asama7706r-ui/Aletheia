# Blind test 1: mold + role (E1) and the law identity card (E2)

- **Sealed:** 2026-09-29T11:52:25Z.
- **Outcome:** E1 **PASS**, E2 **PASS**, 0 exclusions.
- **Protocol:** [`procedure/protocol_v1.md`](procedure/protocol_v1.md), sealed. A copy is in this folder.

## Questions
- **E1, primary.** Given only a world's laws, decide one of:
  - SUBSUMED: the unknowns are known rational values;
  - NEW_KIND: a new kind is needed, together with its family (comm < graded < assoc);
  - CONTRADICTION;
  - UNDERDETERMINED.

  The decision must avoid "silent collapse", i.e. choosing a family too restrictive for the hidden truth.
- **E2, secondary.** Given a law, its identity card (dimensions, validated data points, symmetries, state) and a proposed filled law, decide one of: SAME_LAW_NEW_STATE, ANOTHER_LAW, INVALID.

## Method
1. `procedure/procedure_v1.py` and `procedure/score_v1.py` were written on a dev set only (`dev/`) and sealed by publishing their SHA-256.
2. A separate session then generated 44 unseen worlds and the key: 28 E1 and 16 E2 worlds in `worlds/`, plus `key/`. It also wrote independent verification code (`key/verify_key.py`, with 0 failures).
3. The key hash was published, the frozen procedure was run, and the outputs hash was published before the key was opened.
4. The frozen scorer was run, and its report was published verbatim.

## Results (`results/report.json`)
| E1 (28 worlds) | correct | silent collapse (14 NEW_KIND truths) |
|---|---|---|
| **procedure** | **28/28** | **0/14** |
| B1: always impose old rules | 13 | 11/14 |
| B2: never impose rules | 15 | 0 (but over-loose on 100% of comm/graded truths) |
| B3: relax only on loud collapse | 16 | 11/14 |

- One-sided exact McNemar against B3: b = 12, c = 0, p = 0.00024.
- Dimensions agreed in 14/14 worlds.

| E2 (16 worlds) | balanced accuracy |
|---|---|
| **procedure** | **0.905** |
| C1: accept any filler | 0.333 |
| C2: flag any change | 0.333 |
| C3: dimensions only | 0.667 |

- Detectable ANOTHER_LAW: 5/5.
- False alarms: 0/6.
- INVALID detected: 3/3.
- Misses: only the 2 worlds that were undetectable by design.

## Post-hoc audit (exploratory, not evidence)
1. **No leakage.** The generator's code imports nothing from `procedure/`.
2. **Roles were stated.** In every silent-collapse trap, the quantity that the stricter family kills is written in the laws. The result shows that "a stated role is read and preserved", not that an unstated role can be inferred.
3. **Over-loose traps were not tested.** These are laws that mention a quantity that is zero in the truth. Blind test 2 was designed to cover them.
4. **E2 blind spot.** Symmetries missing from the card are invisible to the procedure.
5. **Uncertainty.** The 95% confidence interval lower bound for 28/28 is about 88%.

## Notes
- `protocol_v1.md` and some generator scripts in `key/work/` mention the temporary folders where the study originally ran. They are kept unchanged: they are part of the sealed record, and no run needs them.
- `worlds/` and `key/` are published. These worlds can no longer serve as a hidden test.

## Reproduce
From this folder, with Python 3 and sympy:
```
python procedure/procedure_v1.py run worlds results/outputs_rerun.json
python procedure/score_v1.py worlds key/key.json results/outputs_rerun.json results/report_rerun.json
```
Both files reproduce the published ones bit for bit:
- outputs: `4a95f22d…`
- report: `0f29aa47…`
