# LLM comparison 1

**Question:** given the exact rules of blind test 2 in plain text, do current frontier LLMs execute them as well as the frozen procedure did?

**Result (2026-10-01):** the hypothesis that they would not is **refuted**. See [REPORT.md](REPORT.md).

## Files
| Path | What it is | Sealed |
|---|---|---|
| `protocol_llm1.md` | Pre-registered protocol | yes |
| `amendment_1.md` | Change of model access, written before any run | hash published before any run |
| `instructions/sheet_A.md`, `sheet_B.md` | Task sheets given to the models | yes |
| `prompts/A1-A5.txt`, `B1-B3.txt`, `batch_plan.json` | Paste-ready batches (sheet + 6 worlds) | yes |
| `tools/parse_answers.py` | Extracts answers from raw replies (pre-registered rules R1-R7) | yes |
| `tools/score_llm.py` | Scores with the sealed test-2 scorer, unmodified and hash-checked | yes |
| `tools/mutation_test.py` | Pre-seal mutation test of parser and wrapper | yes |
| `tools/make_prompts.py` | Builds the prompt files | yes |
| `SEALED_HASHES.txt` | Hashes of all sealed files | its own hash was published |
| `runs/<model>/` | Raw replies exactly as recorded, `meta.json` and `parsed.json` | frozen by `RUNS_FROZEN.txt` before scoring |
| `results/summary.txt`, `report_llm.json` | Scorer output, published verbatim | |
| `results/audit.md` | Post-hoc audit | |
| `results/sensitivity_claude_A4/` | Declared sensitivity analysis for one corrupted transcript | |
| `results/pre_seal_reference_*` | Dry run before sealing that reproduced the blind-test-2 numbers | |

The Gemini replies are partly in Arabic, because of the account's language setting. They are kept verbatim.

## Reproduce
From this folder, with Python 3 and sympy:
```
python tools/mutation_test.py
python tools/parse_answers.py runs/claude
python tools/parse_answers.py runs/deepseek
python tools/parse_answers.py runs/gemini
python tools/parse_answers.py runs/qwen
python tools/score_llm.py runs/claude runs/deepseek runs/gemini runs/qwen
sha256sum -c SEALED_HASHES.txt
sha256sum -c RUNS_FROZEN.txt
```
- `mutation_test.py` should exit 0.
- The `results/summary.txt` that `score_llm.py` writes should have SHA-256 `598c0390b1304349eedfeae654d58d5af1c2ff132d667254c5a45516987ae944`.
- Every file should pass both hash checks.

`score_llm.py` needs the sibling folder `../aletheia_blind_test_2`. It refuses to run if the hash of the sealed scorer there differs.

## How the models were run
- Each batch went into a new conversation in the model's official interface, with memory and personalization off where the interface allowed.
- The prompt file was pasted verbatim, with no other message.
- The complete reply was copied into `runs/<model>/<batch>.txt`.
- One rerun was allowed only for platform errors. None was needed.
