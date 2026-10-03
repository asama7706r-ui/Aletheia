# LLM comparison 2: post-hoc audit (exploratory, not evidence)

Written after the summary. Nothing here changes the pre-registered outcome.

## 1. Outcome (from `results/summary.txt`, sha256 ba1c34b7...)
- **Overall N (question only): EDGE_NOT_SUPPORTED. Overall M (with method): EDGE_NOT_SUPPORTED. Interpretation I1.**

| model | N | M |
|---|---|---|
| Claude Opus 5.5 (extra) | 27/27, NO_GAP | 27/27, NO_GAP |
| Qwen3.8-Max (thinking, code) | 25/27, MIXED (false familiarity 2) | 27/27, NO_GAP |
| DeepSeek-4.1 (deep reasoning) | 24/27, MIXED (scope-sensitive 12/15) | 6/27, GAP (20 missing, format-flagged) |
| Gemini-3.8 (thinking) | 23/27, MIXED | 6/27, GAP (20 missing, format-flagged) |
| Kimi K3 (supplementary, M2-M3 only) | - | 14/14 answered |

- Exploratory reasons in M: every reason that any model listed was true (precision 1 for all models and all five reasons). Claude and Qwen listed every applicable reason (recall 1).

## 2. Integrity
- Sealed 2026-10-03T03:51:24Z (`SEALED_HASHES.txt` f9e8234a...), before any run.
- Raw runs frozen 2026-10-03T06:46:22Z (`RUNS_FROZEN.txt` e0a090c5...). The hash was published before any parsing.
- The scorer read the test-3 key and report unmodified (hash guards passed).

## 3. Deviations from the run procedure
- **DeepSeek stopped working after M1.** M2-M4 count as MISSING, as the rules require.
  - The runner then ran **Kimi K3** on M2 and M3 and first saved those replies in `runs/deepseek`.
  - At the runner's request they were moved, unchanged (same SHA-256), to `runs/kimi` before the freeze. They are scored as supplementary data, outside every verdict.
  - Kimi's settings were not recorded.
- **Gemini M2 and M3:** each reply is an app message ("I can't help, I'm only a language model") followed by a JSON list cut off mid-entry. The runner retried more than once, which is more than the one rerun allowed. No complete reply resulted, so the extra tries changed nothing. The files hold the last attempts.
- **Gemini M4:** the reply is complete, but its final block is a dict keyed by world id with "status" and "candidate" fields, not the required list. Parsing rules R1-R3 do not accept that shape, so the batch counts as MISSING, as pre-registered.
- **Metadata:**
  - every meta.json gives the date 2026-03-10, but the file times show the runs were on 2026-10-03;
  - code execution was "unable to check" for Claude and Gemini, "used on M2" for DeepSeek (where M2 is missing), and "all batches" for Qwen.
- **The runner's remark:** in the runner's view, Claude was the only flagship-tier model among those tested; the others were the newest of their families, not the strongest. This is recorded as context and was not verified.

## 4. Sensitivity checks (exploratory)
- **Without Claude:**
  - overall N becomes MIXED: no other model is NO_GAP in N, and none is GAP. The interpretation would then be I4;
  - overall M stays EDGE_NOT_SUPPORTED, because Qwen is NO_GAP with the method.
  - So the I1 verdict in N rests on Claude alone. Claude is from the same family as the world generator and the sheet author (a declared limitation, section 10 of the protocol). A family advantage cannot be excluded.
- **Gemini in M on the answers it did give:**
  - counted are the complete entries before each cut, plus M4 read with "status" as the verdict and "candidate" as the relation;
  - result: 17 of 20 correct (M1 6/7, M2 4/4, M3 3/3, M4 4/6). One M4 entry uses the label "DEFICIT", which is invalid;
  - Gemini's M verdict stays GAP, and the overall result does not change.

## 5. Where the errors fell (all 11 wrong answers of the scored models)
- **TYPE (4):** the model accepted a candidate whose coefficient cannot have the right dimensions with the declared constants.
  - In N: W-07 (Gemini, Qwen) and W-16 (Qwen).
  - In M: W-07 (DeepSeek), even though sheet M states the TYPE check explicitly.
  - In N the constraint is a stated fact of the world (section 2 of the sheet), not a check, so the model had to derive the check itself.
- **A visible relation of uncertain strength (4):**
  - W-06, a planet-X trap: Gemini "explained" a residual within precision with R3;
  - W-13, a switch nebulium world: Gemini answered NEW instead of KNOWN R2;
  - W-26, a scope-sensitive fork: Gemini and DeepSeek both kept R1 and missed the branch R2.
- **Coverage worlds without a visible relation (2), both DeepSeek in N:**
  - W-12 (dimmer): it added R4, which the old readings exclude (BOUND);
  - W-21 (switch): it answered NEW instead of KNOWN R3.
- **A calculation error (1):** W-03, Gemini in M, accepted R2, which no strength fits (SHAPE).
- **The method's effect:** Qwen's only two errors in N (both TYPE) disappeared in M, where TYPE is an explicit step. Claude did not change. Gemini and DeepSeek cannot be compared, because their M batches are missing. With 2 changed worlds, this is a hint, not evidence (p = 1/2).

## 6. The author's pre-registered prediction, checked
- N between 23 and 27 for each scored model: **held** (23, 24, 25, 27).
- M between 25 and 27: **held** for the two models with complete M runs (27, 27). It cannot be checked for the other two.
- |M - N| <= 3: **held** where it can be checked (0, 2).
- Overall N = I1: **held**.
- Predicted error sites:
  - BOUND: held (W-12);
  - planet-X: held (W-06);
  - dimmers: held (W-12);
  - visible relations: held (4 errors).
- **Missed:** TYPE was the joint-largest error class (4) and was not predicted.

## 7. Interpretation (as pre-registered, I1)
- The one model that answered all 27 worlds correctly, Claude, did so without the method. Interpretation I1 therefore applies: on these worlds, with the coverage factors written in, the nebulium check is within reach of frontier models, and the kernel has no edge on this task.
- The other models came close (23-25 of 27). Their errors cluster where an answer depends on a consequence the model must derive itself (the coefficient form gives the TYPE check), or on two uncertainties at once (a visible relation of unknown strength together with a candidate).
- With the method, Qwen also answered all 27. This agrees with LLM comparison 1: given rules are executed.
- **What remains open, as before:**
  - **Candidate edges without evidence:**
    - determinism;
    - cost and speed: the frozen procedure re-ran all 27 worlds and 18 items, with proofs, in about 15 seconds, while the models took minutes per batch. This is an observation that was not pre-registered;
    - machine-checkable proofs.
  - **Untested by anything so far:** inferring a coverage condition that is not written down. That is the hard part of the real nebulium story.
- **Not evidence of:** real discovery, or any ranking of the vendors (one run each, some batches lost).

## 8. Exposure
The 27 Part A worlds have now been sent to hosted models and are burned for any later test of language models. They remain usable as regression tests for a rebuilt kernel. The 18 Part B items of test 3 were not shown and remain unpublished.
