# LLM comparison 1 - post-hoc audit (written after scoring)

## Official result (pre-registered rules, as recorded)
- results/summary.txt (sha256 598c0390…) and report_llm.json (sha256 fea3da7f…).
- Raw runs were frozen before scoring: RUNS_FROZEN.txt, sha256 34343eae….
- Scores:

  | model | Part A primary | strict | Part B | verdict |
  |---|---|---|---|---|
  | DeepSeek-V4.1-Flash (deep reasoning) | 30/30 | 27/27 max | 18/18 | NO_GAP |
  | Gemini-3.8-high (thinking) | 30/30 | 27/27 max | 18/18 | NO_GAP |
  | Qwen3.8-Max (thinking) | 30/30 | 27/27 max | 18/18 | NO_GAP |
  | Claude Opus 5.5 (extra reasoning) | 24/30 (A4 MISSING) | 21 | 18/18 | GAP |

- For all four models: over-claim 0, over-fork 0, contradictions accepted 0, false death 0, conflicts detected 3/3.
- Overall: **RULE_EXECUTION_EDGE_NOT_SUPPORTED**.

## Findings
1. **Claude A4 was recorded corrupted.** runs/claude/A4.txt has 0 double quotes, 0 slashes and no asterisks. Examples: "1/2" became "12" and "i*j - j*i" became "ij - ji". Every other file (31 of 32) has them.
   - This is a recording (copy) error, not model behaviour.
   - As pre-registered, the batch counts as MISSING, so Claude's official verdict (GAP) is an artifact.
   - Declared sensitivity analysis (results/sensitivity_claude_A4/): quotes were restored in the final block, labels, levels and branches were kept as written, and the decisive sets were dropped. Claude then scores A 30/30, strict 24, B 18/18, verdict NO_GAP. The overall result is unchanged either way.
2. **Agreement.** All four models give the same label, level, branches, bound and interval on 48/48 worlds, and all of these are correct.
   - DeepSeek, Gemini and Qwen give identical decisive sets on 8/10 forks.
   - This explains why Gemini's A2 and A3 matched Qwen's text: correct answers in the sheet's format are near-canonical. No copy error is indicated.
3. **Deviations from the amendment:**
   - Web search was not turned off for Gemini and Qwen. The worlds and key were never online, so no effect is plausible.
   - Qwen ran code in A1, A2, A4 and A5, as recorded.
   - Claude used "extra" rather than "max" reasoning.
   - DeepSeek's recorded model is a "Flash" variant. It still scored perfectly.
   - Gemini's full replies for A1-A3 were lost; only the final JSON was kept. The runner notes the originals were in Arabic.
4. **Sheet clarity.** Four model families, with no clarifying dialogue, reached 100% on the rules as written. So the prose rules are unambiguous enough to be executed. This answers the "maybe the sheet is unclear" limitation.

## Interpretation (as pre-registered, section 7)
- Current frontier LLMs, given the exact rules, execute decide-or-fork and grade zeros on these 48 worlds as well as the frozen procedure.
- The kernel's claimed edge therefore cannot rest on "LLMs over-decide or kill undetected terms". Any edge must rest on other properties, such as determinism, speed and cost, and machine-checkable certificates. Each of these needs its own evidence.
- NOT tested here, and not to be used to rescue the hypothesis:
  - whether models apply this discipline WITHOUT being given the rules;
  - larger or harder worlds.
  These are new questions for new pre-registered tests with new hidden worlds.
- The 48 worlds are now burned.
