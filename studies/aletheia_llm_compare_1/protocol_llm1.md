# LLM comparison 1 - pre-registered protocol

## 0. Question
Given the exact rules in plain text, do current frontier LLMs execute the two blind-test-2 tasks as well as the frozen procedure did? The tasks are:
- Part A, decide or fork: 30 worlds.
- Part B, grades of zero: 18 worlds.

The specific failures we look for:
- **over-claim:** DETERMINED on a FORK world;
- **false death:** calling an undetected term exactly zero.

This is a snapshot. It is not evidence about real discovery.

## 1. Materials
- The 48 blind-test-2 worlds, the key, and the frozen procedure's outputs (30/30 and 18/18).
- The SEALED test-2 scorer `score_v2.py` (SHA-256 4453d00c556e1b0e0ef3f02d982e8fad48c4ce5ea46f65f0405a9e8589cdecad).
  - It is used unmodified.
  - `tools/score_llm.py` refuses to run if the hash differs.
- New, sealed here (hashes in SEALED_HASHES.txt, published on Notion before the first model run):
  - `instructions/sheet_A.md` and `instructions/sheet_B.md`: the task sheets. They restate the definitions of protocol_v2 sections 2 and 7.
  - `prompts/*.txt` and `prompts/batch_plan.json`: 8 paste-ready batches of 6 worlds, in id order. Batch = sheet + worlds.
  - `tools/parse_answers.py`, `tools/score_llm.py` and `tools/mutation_test.py`.
- The worlds were never published. Sending them to hosted models exposes them, so after this study they are "burned": any later test needs new hidden worlds.

## 2. Models
- One model per family: Google, OpenAI, Anthropic, and one of DeepSeek or Qwen, whichever ranks higher.
- For each family, the highest-ranked text model of that family in the LMArena model selector on the day of the first run, used via Direct Chat or Side by Side.
  - If that model is unavailable, take the next model of the same family.
  - Never use anonymous Battle mode for scored runs.
- Tools and web search are not added.
- The exact displayed name, the family, the mode, and the date and time are recorded in runs/<slug>/meta.json.
- Optional and exploratory, not part of the verdict: a repeat run of one model to gauge run-to-run variation.

## 3. Run procedure (runner: the project owner)
1. For every model and every batch, open a NEW conversation.
2. Paste the batch prompt file verbatim. Send nothing else: no hints, corrections or follow-ups.
3. Copy the COMPLETE reply into runs/<slug>/<batch>.txt without editing.
4. One rerun of a batch is allowed ONLY for a platform error: no reply, an error message, or a reply cut off before its final json block. Record the rerun in meta.json.
   - A wrong or badly formatted answer is never rerun.
   - A second platform failure counts as MISSING.
5. Finish all runs within 7 days of the first.
6. The runner never sees the key. The scorer author (Claude) does not run the models.

**Order:**
1. Seal.
2. Run all models.
3. Parse.
4. Score.
5. Publish the summary verbatim.
6. Audit.

## 4. Scoring
- **Primary, Part A:** sealed correctness, except that a FORK counts when the branch level sequence matches, without decisive sets.
  - Reason: decisive sets at graded branches need machine certificates that a chat model cannot fairly be asked for.
- **Strict, Part A:** the sealed `correct_A` in full. It is reported, but it is not in the verdict.
  - Even perfect chat answers reach at most 27/30 here, because A-08, A-12 and A-27 need graded certificates.
- **Part B:** the sealed `correct_B`:
  - the class must match;
  - BOUNDED needs the exact bound;
  - ACTIVE needs the exact interval when one is given.
- **Counts per model:**
  - A primary / strict correct;
  - fork primary correct (of 10);
  - over-claim (of 10);
  - over-fork (of 13);
  - contradictions accepted (of 4);
  - B correct (of 18);
  - B balanced accuracy;
  - false death (of 4: 3 BOUNDED and 1 UNCONSTRAINED);
  - conflicts detected (of 3);
  - MISSING or INVALID answers.
- **McNemar:** one-sided exact test, model vs procedure on the primary Part A. Reported, not a criterion.

## 5. Parsing rules (tools/parse_answers.py)
- **R1:** Use the last fenced json block. Otherwise use the last fenced block of any kind. Otherwise use the last '[' ... ']' list of objects with ids. Otherwise the batch is MISSING.
- **R2:** The only repair allowed is removing trailing commas.
- **R3:** A dict holding one list is unwrapped; a single answer dict is wrapped.
- **R4:** Only the batch's own ids count. If an id repeats, the last occurrence counts.
- **R5:** Labels are upper-cased, with spaces and hyphens turned into underscores. Level names are case-insensitive, and "commutative" and "associative" are accepted. Branches may be strings or {"level": ...}.
- **R6:** A flat decisive list for a two-branch fork is wrapped. "values" is ignored.
- **R7:** Bound and interval must be exact rationals, written as fractions, integers or finite decimals. Anything else is INVALID.
- **MISSING and INVALID count as wrong.** Format failures are also counted and reported. A model with 10 or more is format-flagged.

## 6. Verdict per model (pre-registered)
- **NO_GAP:** A primary >= 27/30, over-claim <= 1, B >= 16/18, and false death = 0.
- **GAP:** A primary <= 24/30, or over-claim >= 3, or B <= 13/18, or false death >= 2.
- **MIXED:** otherwise.
- **Overall:**
  - RULE_EXECUTION_EDGE_NOT_SUPPORTED if any model is NO_GAP;
  - PRESENT_GAP_SUPPORTED if every model is GAP;
  - otherwise MIXED.

## 7. Interpretation (pre-registered)
- **NO_GAP for a model:** that model executes our rules on these worlds about as well as the procedure. The kernel's claimed edge then cannot rest on "LLMs over-decide or kill undetected terms". It must rest on other properties (determinism, certificates, auditability), and those need their own evidence.
- **GAP for every model:** today's frontier models, even when given the exact rules, do not reliably decide-or-fork or grade zeros on these worlds. This supports a present gap for this kind of task, and nothing more. It is not evidence that the kernel can make real discoveries, and the gap may close as models improve.
- **MIXED:** reported as is. No claim is made.

## 8. Known limitations (declared before the runs)
- "Correct" is defined by our own rules. The study measures rule execution, not whether the rules are the best policy.
- The rules are given in prose, so a failure may be a misreading of the prose rather than of the mathematics.
- Models run without tools, in Arena's settings, once per batch. Results vary across runs and over time.
- The worlds were generated by a Claude-family model, and one tested model is from that family.
- Batches of 6 share one context. Answers within a batch are not independent.
- The scorer author is Claude. The key's validity was checked by the sealed scorer, which found 0 exclusions in test 2.
- Worlds are small and formal. Nothing here concerns real data or real discovery.

## 9. Pre-seal checks done
- The wrapper reproduces the sealed test-2 numbers for the procedure and all six baselines:
  - procedure: 30 (A) and 18 (B);
  - V1D 20, OCC 17, FORKALL 8 (strict);
  - THRESH 5, MENTION 6, NOSYM 12.
- tools/mutation_test.py:
  - 26 text-level corruptions and harmless variants, each changing the scores exactly as expected, or not at all;
  - 9 verdict-boundary cases;
  - the hash guard, which refused a tampered copy of the scorer.
- The mention examples in sheet A were checked against the sealed code's mention extraction.
