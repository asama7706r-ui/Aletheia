# LLM comparison 2 - pre-registered protocol

Status: SEALED. The project owner reviewed the draft and approved it without changes on 2026-10-03. The SHA-256 hashes of this protocol, the two sheets, the prompts and the tools are in `SEALED_HASHES.txt` and are published on the Notion page of LLM comparison 2 before the first model run (a file cannot contain its own hash). Environment used: Python 3.12.10.

## 0. Questions
LLM comparison 1 showed that frontier LLMs execute the blind-test-2 rules as well as the frozen procedure when the rules are given to them. It left open how they behave when the rules are NOT given. This study asks that question on the 27 Part A worlds of blind test 3 (the nebulium check), on which the frozen procedure was correct with proofs on 27/27.
- **Q1 (primary), condition N, the question only.** The models receive the meaning of the world fields, the facts that hold in every world, and the question with its four possible answers defined in plain words. They do not receive the method: the order of the checks, the exclusion reasons, or the auxiliary systems. Do they reach the procedure's answers?
- **Q2, condition M, the question plus the method.** The same worlds, with the method of protocol_v3 sections 2.6-2.8 restated in prose. Does the method change their answers on the same worlds?
- **The failures we look for:**
  - **false familiarity:** KNOWN or FORK on a NEW world, i.e. claiming that registered candidates suffice when the givens exclude them;
  - **scope errors:** wrong answers on the 15 scope-sensitive worlds, where ignoring the coverage factors changes the answer, especially answers equal to the NO_SCOPE baseline's;
  - **false novelty:** NEW on a KNOWN or FORK world;
  - **planet-X:** KNOWN or FORK on a NO_DEFICIT world, i.e. "explaining" a residual within precision.
- This is a snapshot. It is not evidence about real discovery. The coverage factors are written in the worlds, so neither condition tests whether a coverage condition can be found (blind test 3 did not test that either).

## 1. Materials
- The 27 Part A worlds of blind test 3 (`aletheia_blind_test_3/worlds/W-01.json` ... `W-27.json`). They were never published before this study.
- The reference, used unmodified, refused by `tools/score_llm2.py` if a SHA-256 differs:
  - `aletheia_blind_test_3/key/key.json`, SHA-256 daee204d4432e3774dcf512dae5311b08ee70cc2b8bef53816133503d92d1b34, published before the test-3 run;
  - `aletheia_blind_test_3/results/report.json`, SHA-256 dd7034634bb5ce700e1ce6a9e73d465df5fa7ed3cc5ab46a5ff5c41c8755f822: the sealed scorer's report, which gives the NO_SCOPE answer per world and the list of 15 scope-sensitive worlds;
  - `aletheia_blind_test_3/results/outputs.json`, SHA-256 393e65dacff9119600305e53b5faa339d744ecadabbe0626a2c7ee330cf15a9b: used only by the pre-seal reference check (section 9).
- New, sealed here:
  - `instructions/sheet_N.md` and `instructions/sheet_M.md`. Sections 1-3 (world fields, facts, question) are identical in the two sheets. Sheet M adds section 4 (the method) and asks for exclusion reasons. Both sheets were written from protocol_v3 alone, before the content of any world was read in this study.
  - `prompts/N1.txt` ... `prompts/N4.txt`, `prompts/M1.txt` ... `prompts/M4.txt` and `prompts/batch_plan.json`: 8 paste-ready batches, made by `tools/make_prompts.py`. Batch = sheet + worlds. Batches 1-3 hold 7 worlds each and batch 4 holds 6, in id order, identical in N and M.
  - A world is shown with its protocol fields only. `possible_observations` is dropped, because the verdict does not use it; `experiment` is dropped, because it is always "A". Nothing else is changed.
  - `tools/parse_answers.py`, `tools/score_llm2.py`, `tools/mutation_test.py`.
- **Part B of blind test 3 is not used.** Which files to reopen is a convention of our rules, so without the rules there is no fair correct answer; and LLM comparison 1 already showed that given rules of this kind are executed. The 18 Part B items stay unpublished.
- **Exposure.** Sending the worlds to hosted models exposes them. After this study the 27 Part A worlds are "burned" for any later test of language models. They remain usable as regression tests for a rebuilt kernel.

## 2. Models
As in amendment 1 of LLM comparison 1:
- Four scored models:
  - Anthropic: the claude.ai app;
  - Google: the Gemini app or Google AI Studio, whichever offers the stronger model;
  - DeepSeek: its official chat;
  - Qwen: its official chat.
- For each, use the most capable model offered to the runner in that interface on the first run day, in its normal chat mode.
  - A reasoning or "thinking" option is allowed and recorded.
  - Agent, deep-research and multi-step research modes are not allowed.
- **Code execution is ALLOWED** where the interface offers it, and recorded. This differs from LLM comparison 1: the question here is whether the models apply the right checks, not whether they can do exact fraction arithmetic without a calculator. If an interface offers no code execution, the model runs without it.
- Web search is off. Memory and personalization are off (a temporary or incognito chat where offered).
- OpenAI is not scored: its flagship needs a subscription the runner does not have. The free ChatGPT model may be run as SUPPLEMENTARY data, labelled non-flagship, outside the overall result.
- Recorded in runs/<slug>/meta.json: the interface, the model name as shown, the reasoning option, memory and web status, code execution (off / available but unused / used in which batches), whether the model is scored, and the dates.

## 3. Run procedure (runner: the project owner)
1. For every model, run all four N batches before any M batch.
2. For every batch, open a NEW conversation.
3. Paste the batch prompt file verbatim. Send nothing else: no hints, corrections or follow-ups.
4. Copy the COMPLETE reply into runs/<slug>/<batch>.txt without editing.
5. One rerun of a batch is allowed ONLY for a platform error: no reply, an error message, or a reply cut off before its final json block. Record the rerun in meta.json.
   - A wrong or badly formatted answer is never rerun.
   - A second platform failure counts as MISSING.
6. Finish all runs within 7 days of the first.
7. The runner does not open the test-3 key. The scorer author (Claude) does not run the models.

**Order:**
1. Seal.
2. Run all models.
3. Freeze the raw runs: publish the SHA-256 of a list of the hashes of every run file, before parsing.
4. Parse.
5. Score.
6. Publish the summary verbatim.
7. Audit.

## 4. Scoring
- **Correct:** the same verdict as the key, and the same relation (KNOWN) or the same branch set (FORK). This is the correctness of the test-3 baselines (protocol_v3 section 7.2). Proofs, intervals, quarantine notes and decisive sets are not asked for.
- **Counts per model and condition:**
  - correct (of 27);
  - scope-sensitive correct (of 15), and how many of the 15 answers equal the NO_SCOPE baseline's answer;
  - false familiarity (of 9 NEW worlds);
  - false novelty (of 15 KNOWN and FORK worlds);
  - fork correct (of 6);
  - over-fork (FORK on the 9 KNOWN worlds);
  - planet-X (KNOWN or FORK on the 3 NO_DEFICIT worlds);
  - missed deficit (NO_DEFICIT on the 24 worlds with a deficit);
  - MISSING and INVALID answers.
- **Method effect (Q2), per model:** b = worlds correct in M and wrong in N; c = the reverse; two-sided exact McNemar p. Reported, not a criterion: 27 paired worlds give little power, and the verdicts of section 6 carry the conclusion.
- **Model vs procedure:** one-sided exact McNemar p on the 27 worlds (the procedure was correct on all). Reported.
- **Exploratory, condition M only:** for each exclusion reason, recall and precision of the (candidate, reason) pairs that the model lists, against the key's reason sets. Not in any verdict.

## 5. Parsing rules (tools/parse_answers.py)
- **R1:** Use the last fenced json block. Otherwise use the last fenced block of any kind. Otherwise use the last '[' ... ']' list of objects with ids. Otherwise every world of the batch is MISSING.
- **R2:** The only repair allowed is removing trailing commas.
- **R3:** A dict holding one list is unwrapped; a single answer dict is wrapped.
- **R4:** Only the batch's own ids count, compared after stripping spaces and upper-casing. If an id repeats, the last occurrence counts.
- **R5:** The verdict is read from "verdict", or from "label" if "verdict" is absent. It is upper-cased, with spaces and hyphens turned into underscores, and must be NO_DEFICIT, KNOWN, NEW or FORK; otherwise the answer is INVALID. Candidate ids are stripped and upper-cased.
- **R6:** KNOWN needs "relation": one candidate id (a list holding exactly one id is accepted). FORK needs "branches": a list of candidate ids; duplicates are removed and the list is sorted. A missing or malformed field makes the answer INVALID.
- **R7 (condition M, exploratory):** "excluded" maps candidate ids to lists of reason names. Names other than the five are dropped and counted.
- **MISSING and INVALID count as wrong.** A model with 6 or more MISSING or INVALID answers in a condition is format-flagged in that condition.

## 6. Verdicts (pre-registered)
- **Per model and condition:**
  - **NO_GAP:** correct >= 24/27, false familiarity <= 1/9, and scope-sensitive correct >= 13/15.
  - **GAP:** correct <= 21/27, or false familiarity >= 3/9, or scope-sensitive correct <= 11/15.
  - **MIXED:** otherwise.
  - For calibration: NO_SCOPE scores 12/27, false familiarity 3/9 and scope-sensitive 0/15, so a model that ignores coverage is GAP on three counts.
- **Overall, per condition, over the scored models:**
  - EDGE_NOT_SUPPORTED if any scored model is NO_GAP;
  - GAP_SUPPORTED if every scored model is GAP;
  - MIXED otherwise.
- **Interpretation code:**
  - **I1:** N is EDGE_NOT_SUPPORTED.
  - **I2:** N is GAP_SUPPORTED and M is EDGE_NOT_SUPPORTED.
  - **I3:** N and M are both GAP_SUPPORTED.
  - **I4:** any other combination.

## 7. Interpretation (pre-registered)
- **I1:** at least one frontier model, given only the question, reaches the procedure's answers on these worlds. The nebulium check, as posed here with the coverage factors written in the worlds, needs neither our method nor the kernel. The kernel has no edge on this task.
- **I2:** without the method every scored model shows a gap, and with it at least one does not. The value lies in the written method, which can be given to any model. This is a real result about the method, but it is not evidence that the kernel's code is needed.
- **I3:** every scored model shows a gap with and without the method. This supports a present gap for this kind of task (exact feasibility with coverage factors), and nothing more. It is not evidence of real discovery, and the gap may close as models improve.
- **I4:** reported as is. No claim is made.
- No outcome is evidence that the kernel can infer coverage conditions or make real discoveries.

## 8. The author's prediction (written before sealing; not part of any verdict)
- Per scored model: N between 23 and 27 of 27; M between 25 and 27 of 27; |M - N| <= 3 worlds.
- Overall N: EDGE_NOT_SUPPORTED, so interpretation I1.
- If a gap appears, it is most likely in: BOUND exclusions (a candidate fits the new readings, but the old readings exclude its strength); planet-X traps; dimmer worlds that need exact factors at each state; and worlds with a visible relation.
- Reasons, summarized:
  - in LLM comparison 1, four models were correct on 48/48 worlds when given the rules;
  - the coverage factor is written in each world, so the hard part of the real nebulium story (knowing that a coverage condition exists) is given away;
  - to be scorable, the question must define the answers exactly, and the definitions already imply most of the method;
  - code execution removes arithmetic errors.
- The hypothesis of LLM comparison 1 expected a gap and was refuted; the author is from the same model family as one tested model and may misjudge in either direction.

## 9. Pre-seal checks done
- **Reference check:** `python tools/score_llm2.py --reference-check` scores the frozen test-3 outputs of the procedure and its three baselines directly, without the parser. It reproduces the sealed test-3 numbers: procedure 27/27, NO_SCOPE 12/27, ALWAYS_NEW 12/27, DIMS_ONLY 5/27. The procedure's reasons give recall and precision 1 for all five reasons.
- **Mutation test:** `python tools/mutation_test.py`, 46 checks, 0 failures:
  - 13 harmless variants (case, spacing, "label", trailing commas, other blocks, unfenced list, wrapped dict, repeated id, and others) change nothing;
  - 9 single corruptions change exactly the expected counts;
  - missing answers and a missing batch file, NO_SCOPE answers on the scope-sensitive worlds, the McNemar value, and the reason analysis;
  - 10 verdict-boundary cases;
  - overall labels, interpretation codes, and the exclusion of unscored models;
  - the hash guard refuses a tampered key.
- The world fields shown were checked for answer hints: names are neutral (validity rule W1 of test 3), and the coverage summaries only describe the factors.

## 10. Known limitations (declared before the runs)
- **The question carries much of the method.** To be scorable, sheet N must define the four answers exactly. Those definitions imply the checks (coverage at each state, the old readings, the coefficient form, the symmetries). Condition N therefore tests whether models derive the method from exact definitions, not whether they would ask the right question unprompted.
- The coverage factors are given in the worlds; inferring them is not tested.
- "Correct" is defined by our rules. The study measures agreement with them, not whether they are the best policy.
- Generator, sheet author, scorer author and one tested model are all from the Claude family.
- Code execution differs across interfaces; it is recorded, not equalized.
- Models run once per batch; results vary across runs and over time. Batches of 6-7 worlds share one context.
- 27 worlds: the paired comparison of N and M has little statistical power.
- Official apps may add hidden system prompts or tools that differ between vendors. No OpenAI flagship is tested.
