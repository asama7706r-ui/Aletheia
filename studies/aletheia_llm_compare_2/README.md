# LLM comparison 2

**Question:** on the 27 Part A worlds of blind test 3 (the nebulium check), do frontier LLMs reach the frozen procedure's answers when given only the question, without the method? And does the method change their answers?

**Result (2026-10-03):** pre-registered interpretation **I1**. With the question only, Claude answered all 27 worlds correctly; with the method, Qwen also answered all 27. **Erratum:** an earlier recorded decision excluded the generator's family (Claude) from this comparison, and the protocol omitted it. With it applied, the question-only condition is MIXED (no claim). See [REPORT.md](REPORT.md), section 9.

## Files
| Path | What it is | Sealed |
|---|---|---|
| `protocol_llm2.md` | Pre-registered protocol | yes |
| `instructions/sheet_N.md` | Task sheet N: the question only | yes |
| `instructions/sheet_M.md` | Task sheet M: the question plus the method (sections 1-3 identical to sheet N) | yes |
| `prompts/N1-N4.txt`, `M1-M4.txt`, `batch_plan.json` | Paste-ready batches (sheet + 7 or 6 worlds) | yes |
| `tools/make_prompts.py` | Builds the prompt files from `../aletheia_blind_test_3/worlds` | yes |
| `tools/parse_answers.py` | Extracts answers from raw replies (pre-registered rules R1-R7) | yes |
| `tools/score_llm2.py` | Scores against the test-3 key and sealed report, both hash-checked | yes |
| `tools/mutation_test.py` | Pre-seal mutation test of parser and scorer (46 checks) | yes |
| `SEALED_HASHES.txt` | Hashes of all sealed files | its own hash was published |
| `runs/<model>/` | Raw replies exactly as recorded, `meta.json` and `parsed.json` | frozen by `RUNS_FROZEN.txt` before parsing |
| `results/summary.txt`, `report_llm2.json` | Scorer output, published verbatim | |
| `results/audit.md` | Post-hoc audit, including the declared deviations | |
| `RUN_GUIDE_ar.md` | The Arabic run guide used by the runner | |

Some replies are partly in Arabic, because of the account's language setting. They are kept verbatim.

## Reproduce
From this folder, with Python 3 and sympy:
```
python tools/mutation_test.py
python tools/parse_answers.py runs/claude
python tools/parse_answers.py runs/gemini
python tools/parse_answers.py runs/deepseek
python tools/parse_answers.py runs/qwen
python tools/parse_answers.py runs/kimi
python tools/score_llm2.py runs/claude runs/gemini runs/deepseek runs/qwen runs/kimi
python tools/score_llm2.py --reference-check
sha256sum -c SEALED_HASHES.txt
sha256sum -c RUNS_FROZEN.txt
```
- `mutation_test.py` should report 0 failures.
- The `results/summary.txt` that `score_llm2.py` writes should have SHA-256 `ba1c34b7ad40bd89391c26cb60e7459946e811586f11007bb1d220d2522d40dd`.
- `--reference-check` reproduces the blind-test-3 numbers: procedure 27, NO_SCOPE 12, ALWAYS_NEW 12, DIMS_ONLY 5.
- Every file should pass both hash checks (`sha256sum -c` skips the header lines with a warning).

`score_llm2.py` needs the sibling folder `../aletheia_blind_test_3`. It refuses to run if the hash of the test-3 key, report or outputs differs.

## How the models were run
- Each batch went into a new conversation in the model's official interface, with memory off and web search off. Code execution was allowed and recorded.
- The four N batches of a model were run before its M batches.
- The prompt file was pasted verbatim, with no other message, and the complete reply was copied into `runs/<model>/<batch>.txt`.
- DeepSeek stopped working after M1. Kimi K3 was run on M2 and M3 as supplementary data, outside every verdict. Several Gemini replies were cut off by the app. See `results/audit.md`, section 3.
