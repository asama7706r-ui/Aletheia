# Do frontier LLMs execute an explicit "decide-or-fork" and "grades-of-zero" protocol? A pre-registered comparison

**Study:** LLM comparison 1 of the Aletheia project.
**Pre-registered:** 2026-09-30T18:16:07Z, amended before any run at 18:50Z.
**Runs:** 2026-09-30/10-01.
**Result:** the hypothesis is **refuted**.

## Summary
- **Background.** In [blind test 2](../aletheia_blind_test_2/README.md), a frozen symbolic procedure solved two exact tasks on 48 unseen formal "worlds":
  - **decide-or-fork:** 30/30. It commits to one algebraic structure only when the givens determine it, and otherwise lists the correct alternatives with checkable deciding observations.
  - **grades of zero:** 18/18. It classifies an undetected term as exactly zero only when a reason forces it, never "false death".
- **Our hypothesis.** Large language models (LLMs) would fail these tasks, over-deciding or killing undetected terms, even when given the exact rules. That failure would have been a concrete edge for a symbolic kernel.
- **Test.** We gave the same 48 worlds and the same rules, as a plain-text task sheet, to four frontier models from different vendors.
- **Result.** DeepSeek, Gemini and Qwen each scored 30/30 and 18/18, with zero over-claims and zero false deaths. Claude did the same after a declared correction of one corrupted transcript. The official, uncorrected score is lower, for a recording reason explained in the audit.
- **Pre-registered conclusion.** The kernel's edge cannot rest on "LLMs over-decide or kill undetected terms".

## 1. Question and pre-registered hypothesis
Given the exact rules of blind test 2 in prose, do current frontier LLMs execute them as well as the frozen procedure?

The verdict rules were fixed before any run (protocol section 6):
- **NO_GAP:** Part A >= 27/30, over-claim <= 1, Part B >= 16/18, and false death = 0.
- **GAP:** Part A <= 24/30, or over-claim >= 3, or Part B <= 13/18, or false death >= 2.
- **MIXED:** otherwise.

Overall result:
- If any model is NO_GAP, the result is "rule-execution edge not supported".
- If all models are GAP, the result is "present gap supported".

## 2. Materials
- **Worlds and key:** the 48 blind-test-2 worlds (30 Part A, 18 Part B) and their key. Every key claim carries a machine-checkable witness or certificate, verified by the sealed test-2 scorer with 0 exclusions. The worlds were never published before this study.
- **Task sheets** (`instructions/`): restate the definitions of the test-2 protocol, sections 2 and 7.
  - The mention examples were checked against the sealed code.
  - No composition counts or answers were given.
- **Batches:** 8 batches of 6 worlds, in id order. Each batch is the sheet followed by its worlds.

## 3. Models (amendment 1)
LMArena's direct-choice lists lagged a generation behind, and its Battle mode cannot guarantee that one model answers all batches. So each vendor's official interface was used, with the strongest model available to the runner.

| Model (as shown) | Interface | Reasoning option | Notes |
|---|---|---|---|
| Claude Opus 5.5 | claude.ai | "extra" (a "max" level existed but was not used) | code tool available, not used |
| DeepSeek-V4.1-Flash | chat.deepseek.com | deep reasoning | a "Flash" variant |
| Gemini-3.8-high | gemini.google.com | thinking | web search not disabled; replies partly in Arabic |
| Qwen3.8-Max | chat.qwen.ai | thinking | web search not disabled; ran code in A1, A2, A4, A5 |

OpenAI's flagship needs a subscription the runner does not have, so it was not tested. This limitation was declared before any run.

## 4. Scoring
- The **sealed test-2 scorer** (`score_v2.py`, SHA-256 `4453d00c…`) is used unmodified. The wrapper refuses to run if its hash differs.
- **Primary, Part A:** the sealed correctness, except that a FORK counts when its branch sequence matches. Decisive sets are not required, because the graded ones need machine certificates that a chat model cannot fairly be asked to produce.
- **Strict, Part A:** the full sealed correctness. It is reported, but not used for the verdict. For chat answers it tops out at 27/30.
- **Part B:** the sealed correctness: the class must match; BOUNDED needs the exact bound; ACTIVE needs the exact interval when one is given.
- **Integrity:**
  - The parser and wrapper were mutation-tested before sealing (26 text-level corruptions and variants, 9 verdict boundaries, and the hash guard).
  - The raw replies were frozen by hash (`RUNS_FROZEN.txt`, `34343eae…`) and the hash was published before scoring.

## 5. Results (verbatim scorer output, `results/summary.txt`, SHA-256 `598c0390…`)
```
entrant | A_primary_correct | A_strict_correct | A_fork_primary_correct | A_over_claim | A_over_fork | A_contradictions_accepted | B_correct | B_false_death | B_conflicts_detected | missing_or_invalid | verdict
ref:procedure | 30 | 30 | 10 | 0 | 0 | 0 | 18 | 0 | 3 | 0 | -
ref:V1D | 20 | 20 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 18 | -
ref:OCC | 17 | 17 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 18 | -
ref:FORKALL | 9 | 8 | 3 | 0 | 11 | 0 | 0 | 0 | 0 | 18 | -
ref:THRESH | 0 | 0 | 0 | 0 | 0 | 0 | 5 | 4 | 2 | 30 | -
ref:MENTION | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 30 | -
ref:NOSYM | 0 | 0 | 0 | 0 | 0 | 0 | 12 | 0 | 2 | 30 | -
claude | 24 | 21 | 7 | 0 | 0 | 0 | 18 | 0 | 3 | 6 | GAP
deepseek | 30 | 27 | 10 | 0 | 0 | 0 | 18 | 0 | 3 | 0 | NO_GAP
gemini | 30 | 27 | 10 | 0 | 0 | 0 | 18 | 0 | 3 | 0 | NO_GAP
qwen | 30 | 27 | 10 | 0 | 0 | 0 | 18 | 0 | 3 | 0 | NO_GAP
overall: RULE_EXECUTION_EDGE_NOT_SUPPORTED
```
- The `ref:` rows are the frozen procedure and the six baselines of blind test 2, for comparison.
- In the test-2 design, V1D and OCC cannot fork, and THRESH calls anything undetected zero.

## 6. Audit (post hoc, `results/audit.md`)
1. **One corrupted transcript.**
   - `runs/claude/A4.txt` was recorded with every double quote, slash and asterisk stripped: "1/2" became "12", and `i*j - j*i` became `ij - ji`. The other 31 files are intact.
   - As pre-registered, the batch counts as MISSING, which produces Claude's official GAP.
   - A declared sensitivity analysis restores only the quotes in its final answer block and drops the decisive sets. With that, Claude scores 30/30 (strict 24) and 18/18, verdict NO_GAP.
   - The overall result is the same either way.
2. **Full agreement.** All four models give the same label, level, branches, bound and interval on 48/48 worlds, and all of them are correct.
   - Three models give identical decisive sets on 8 of 10 forks.
   - This explains why two models produced textually identical answer blocks in two batches: correct answers in the sheet's format are nearly canonical.
3. **Deviations, recorded:**
   - Web search was not disabled for Gemini and Qwen. The worlds and key were never online, so no effect is plausible.
   - Qwen ran code.
   - DeepSeek was a "Flash" variant.
   - Gemini's full replies for A1-A3 were not kept; only the final answer blocks were.
4. **Clarity of the rules.** Four model families executed the prose rules perfectly, without any clarifying dialogue. So the sheet is not ambiguous. This removes one declared limitation.

## 7. Interpretation (as pre-registered)
- **What the result shows:** given the exact rules, current frontier LLMs decide-or-fork and grade zeros on these worlds exactly as well as the frozen procedure. The procedure's advantage in this study therefore cannot be accuracy of rule execution.
- **Remaining candidates** for any advantage of a symbolic kernel, none of them tested here:
  - determinism and reproducibility;
  - speed and cost (the procedure plus the scorer take about 30 seconds on a laptop CPU for all 48 worlds, against about two minutes of "thinking" per batch of 6);
  - machine-checkable certificates;
  - the rules themselves, as a specification.
- **Not tested here** (these are new questions for new pre-registered studies with new hidden worlds, and are not used to rescue the hypothesis):
  - whether LLMs apply this discipline when they are **not** given the rules;
  - larger or harder worlds;
  - the kernel's discovery layer: constructing new kinds from deficits.

## 8. Limitations
- "Correct" is defined by our own rules. The study measures rule execution, not whether the rules are the best policy.
- The worlds were generated by a Claude-family model, and one tested model is from that family.
- One run per batch, through consumer interfaces with vendor-specific hidden settings. Results vary across runs and over time.
- Four models only, and no OpenAI flagship.
- The worlds are small, formal and exact. Nothing here concerns noisy data or real discovery.
- The 48 worlds are now exposed ("burned") and cannot serve as hidden tests again.

## 9. Authorship
- The study was directed and all model runs were performed by the project owner (Asama).
- The protocol, task sheets, parser, wrapper, mutation test, scoring and this report were written by Claude (Anthropic) under that direction.
- The worlds and key come from a separate Claude session (blind test 2).
