# Do frontier LLMs reach the "nebulium check" answers without being taught the method? A pre-registered comparison

**Study:** LLM comparison 2 of the Aletheia project.
**Pre-registered:** 2026-10-03T03:51:24Z.
**Runs:** 2026-10-03. Raw replies frozen at 06:46:22Z, before any parsing.
**Result:** pre-registered interpretation **I1**: no kernel edge on these worlds. **See the erratum (section 9):** by a decision recorded before this study, the generator's family (Claude) should not have been scored. Without it, the question-only condition is MIXED (no claim).

## Summary
- **Background.**
  - In [blind test 3](../aletheia_blind_test_3/README.md), a frozen symbolic procedure solved 27 unseen formal worlds with proofs (27/27).
  - In each world, new readings may not fit an established law. The procedure decides among four answers:
    - no deficit;
    - a known registered relation explains the readings;
    - something new is needed;
    - a fork between two or three relations.
  - Each relation carries a "coverage factor" that says where it acts. The question is whether an effect that looks new is in fact a known one acting where it was hidden before, as in the historical nebulium lines.
- **What was still open.** [LLM comparison 1](../aletheia_llm_compare_1/REPORT.md) showed that frontier LLMs execute such rules perfectly when given them. It left open what they do without the rules.
- **Design.** Each model answered all 27 worlds twice, in separate new conversations:
  - **N:** the question only. The meaning of the world fields, the facts that hold in every world, and the four answers defined in plain words.
  - **M:** the question plus the method: the order of checks, the auxiliary systems and the five exclusion reasons.
- **Result.**
  - In N, Claude scored 27/27. Qwen scored 25, DeepSeek 24 and Gemini 23, each MIXED by one threshold.
  - In M, Claude and Qwen both scored 27/27. DeepSeek and Gemini lost most of their M batches to platform failures.
- **Pre-registered conclusion (I1).** At least one frontier model reached the procedure's answers without the method, so the kernel has no edge on these worlds.
- **Main caveat, and erratum.** The I1 verdict in N rests on Claude alone, which is from the same model family as the world generator. A decision recorded before this study said the generator's family should not be used for this comparison; the protocol omitted it (section 9). With it applied, N is MIXED: the question without the method stays open, while with the method a model from outside the generator's family (Qwen) matches the procedure.

## 1. Questions and pre-registered verdict rules
- **Q1 (primary, condition N).** Given only the question, do frontier LLMs reach the procedure's answers?
- **Q2 (condition M).** Does the method change their answers on the same worlds?

**Verdict rules (protocol section 6), per model and condition:**
- **NO_GAP:** correct >= 24/27, false familiarity <= 1/9, and scope-sensitive correct >= 13/15.
- **GAP:** correct <= 21/27, or false familiarity >= 3/9, or scope-sensitive correct <= 11/15.
- **MIXED:** otherwise.
- For calibration, a baseline that ignores coverage scores 12/27, false familiarity 3/9 and scope-sensitive 0/15.

**Overall, per condition:** EDGE_NOT_SUPPORTED if any scored model is NO_GAP; GAP_SUPPORTED if all are GAP; MIXED otherwise.

**Interpretation codes:**
- **I1:** N is EDGE_NOT_SUPPORTED.
- **I2:** N is GAP_SUPPORTED and M is EDGE_NOT_SUPPORTED.
- **I3:** both are GAP_SUPPORTED.
- **I4:** any other combination.

## 2. Materials
- The 27 Part A worlds of blind test 3, never published before this study. They were shown with their protocol fields only.
- The test-3 key and sealed report, used unmodified and hash-checked.
- Sheets N and M share sections 1-3 word for word. Both were written from the test-3 protocol alone, before any world was read for this study.
- **Part B of blind test 3 was not shown.** Which files to reopen is a convention of our rules, so without them there is no fair "correct" answer.

## 3. Models
- **Scored:** Claude Opus 5.5 (claude.ai, "extra" reasoning), Gemini 3.8 (Gemini app, thinking), DeepSeek 4.1 (official chat, deep reasoning) and Qwen3.8-Max (official chat, thinking).
- **Supplementary:** Kimi K3, on M2 and M3 only.
- Memory and web search were off. Code execution was allowed and recorded: Qwen used it in every batch; for Claude and Gemini it could not be verified.

## 4. Scoring
- An answer is **correct** when the verdict matches the key, together with the same relation (KNOWN) or the same branch set (FORK). No proofs are asked for.
- MISSING and INVALID answers count as wrong.
- Exclusion reasons in M are an exploratory measure only.

## 5. Results (verbatim scorer output, `results/summary.txt`, SHA-256 `ba1c34b7…`)
| model | N | M |
|---|---|---|
| Claude | 27/27, NO_GAP | 27/27, NO_GAP |
| Qwen | 25/27, MIXED (false familiarity 2/9) | 27/27, NO_GAP |
| DeepSeek | 24/27, MIXED (scope-sensitive 12/15) | 6/27, GAP (20 missing) |
| Gemini | 23/27, MIXED | 6/27, GAP (20 missing) |
| Kimi K3 (supplementary) | - | 14/14 answered |

**Overall N: EDGE_NOT_SUPPORTED. Overall M: EDGE_NOT_SUPPORTED. Interpretation: I1.**

In M, every exclusion reason that any model listed was true. Claude and Qwen listed every applicable reason.

## 6. Audit (post hoc, `results/audit.md`)
- **The verdict in N rests on one model.** Without Claude, N is MIXED (I4). In M, the verdict stands without Claude, because Qwen scored 27/27.
- **Where the errors fell.** The scored models made 11 errors:
  - **TYPE (4):** the model accepted a candidate whose coefficient cannot have the right dimensions with the declared constants. In N this constraint is stated as a fact of the world, so the check itself had to be derived;
  - **a visible relation of uncertain strength (4):** including one planet-X trap, where a residual within precision was "explained";
  - **coverage (2):** both in nebulium worlds;
  - **arithmetic (1).**
- **The method's effect.** Qwen's two N errors were both TYPE errors, and both disappeared in M, where TYPE is an explicit step. This is a hint, not evidence.
- **The author's prediction, registered before the seal.** The predicted ranges held: N between 23 and 27, M between 25 and 27 where complete, |M - N| <= 3, and I1. Four predicted error sites held. TYPE errors were not predicted.
- **Deviations:**
  - DeepSeek stopped working after M1.
  - Gemini's M2 and M3 replies were cut off after an app refusal message, and were retried more than the one allowed time without result.
  - Gemini's M4 reply was complete but in a non-accepted format, so it counts as MISSING. Exploratory: on the answers Gemini did give in M, it scored 17/20.

## 7. Interpretation (as pre-registered)
- **I1.** On these worlds, with the coverage factors written into each world, the nebulium check is within reach of a frontier model that is not taught the method. The kernel has no edge on this task.
- The other models came close, and their errors cluster where a consequence must be derived (TYPE) or two uncertainties combine.
- **Still without evidence:** the remaining candidate edges, namely determinism, cost and speed, and machine-checkable proofs.
- **Not tested by anything so far:** inferring a coverage condition that is not written down.

## 8. Limitations
- The question had to define the answers exactly to be scorable, and those definitions carry much of the method.
- The coverage factors are given in the worlds.
- The generator, the sheet author, the scorer author and one tested model are all from the Claude family.
- Each batch was run once. Two models lost most of condition M to platform failures. No OpenAI flagship was tested.
- 27 worlds give little statistical power for the paired comparison.
- The 27 worlds are now burned for later LLM tests.

## 9. Erratum (2026-10-03, after publication)
- The draft specification of blind test 3 (section 12.2, item 18, approved by the project owner) recorded that the generator's model family is not suitable for a later comparison of models without the rules on these worlds. The generator then became Claude, so this applies to Claude. This study's protocol omitted the decision and scored Claude. The omission was the protocol author's (Claude's).
- The pre-registered label stays I1; it is not changed after the results.
- **With the earlier decision applied:** overall N is MIXED (interpretation I4: no claim), and overall M remains EDGE_NOT_SUPPORTED (Qwen 27/27).
- **The more defensible summary:**
  - with the method, a frontier model from outside the generator's family matches the procedure;
  - without the method, the question is open. Models from outside that family scored 23-25 of 27, close but below the NO_GAP thresholds.
- Details are in `results/audit.md`, section 9.

## 10. Authorship
The study was designed and run under the direction of the project lead, Asama, who performed all model runs. The protocol, sheets, tools and this report were written by Claude (Anthropic).
