# Blind test 3: the nebulium check (Part A) and reopening (Part B)

- **Status:** DONE.
  - Sealed 2026-10-02T18:34:50Z. The hashes are in `SEALED_HASHES.txt` and on the Notion page.
  - Key hash `daee204d...`. Outputs hash `393e65da...` (published before the key was opened). Report hash `dd703463...`.
- **Outcome:** Part A **PASS** (27/27 with proofs; best baseline 12/27; McNemar p = 1/32768). Part B **PASS** (18/18 exact lists and verdicts; 0 silent changes). 0 exclusions.
- **Audit:** `results/audit.md`.
- **Exposure:** the 27 Part A worlds were shown to language models in LLM comparison 2 (2026-10-03), after this test was complete. The 18 Part B items were not shown. Both were published with this study afterwards.
- **Protocol:** [`protocol_v3.md`](protocol_v3.md).
- **Decisions:** section 12 of the project's (Arabic) draft-specification notes for test 3.

## Layout
- `procedure/procedure_v3.py`: the procedure. It uses exact Fourier-Motzkin elimination with Farkas multipliers.
- `scorer/ref_v3.py`: the independent reference. It uses ast parsing and an exact simplex, and never imports the procedure.
- `scorer/score_v3.py`: the scorer.
- `scorer/validate_v3.py`: the world validator, sealed with the scorer and run by the generator.
- `tools/hash_files.py`: prints SHA-256 hashes, never file contents.
- `dev/`: the dev set and development checks, excluded from the test:
  - `make_dev.py`: writes `dev/worlds`, `dev/data` and `dev/key.json`. It holds 11 hand-designed worlds and 10 items, with the reasoning in comments.
  - `score_dev.py`: the frozen scorer with W10 off, because the dev worlds are the dev set itself.
  - `fuzz_compare.py`: Part A differential test on random worlds (procedure against reference).
  - `fuzz_partb.py`: Part B differential test on random cabinets and items.
  - `regression_t2.py`: coefficient intervals on the blind-test-2 Part B worlds.
  - `mutation_test.py`: deliberate corruptions of keys, worlds and outputs.
  - `results/`: logs of the runs.

## Development checks run before sealing (consistency checks, not evidence)
- **Dev set:** the procedure is correct with all proofs on 11/11 worlds and 10/10 items (Part A PASS, Part B PASS on the dev set).
- **Differential tests:**
  - Part A: 7574 random worlds, 0 disagreements (verdicts, reason sets, intervals, ranges, proof checks);
  - Part B: 1402 random items, 0 disagreements (reopened lists, recomputed verdicts), and no rule gap.
- **Regression:** blind test 2, Part B: 18/18 identical coefficient intervals.
- **Scorer mutation test:** 40/40 corruptions caught; the originals are accepted.

## Reproduce the test
From this folder, with Python 3 and sympy:
```
python procedure/procedure_v3.py run worlds data results/outputs_rerun.json
python scorer/score_v3.py worlds data key/key.json results/outputs_rerun.json results/report_rerun.json
python scorer/validate_v3.py worlds data key/key.json
```
- `outputs_rerun.json` should have SHA-256 `393e65dacff9119600305e53b5faa339d744ecadabbe0626a2c7ee330cf15a9b`, and `report_rerun.json` should have `dd7034634bb5ce700e1ce6a9e73d465df5fa7ed3cc5ab46a5ff5c41c8755f822`. The rerun names keep the published files intact.
- The validator should print VALID.
- `key/` also holds the generator's own code, its independent verifier (`verify_key.py`) and its notes, including the W8 ambiguity it reported (`generator_notes.md`).
- `GENERATOR_START.md` is the (Arabic) start message given to the generator session.

## Rerun the development checks
```
python dev/make_dev.py
python procedure/procedure_v3.py run dev/worlds dev/data dev/results/dev_outputs.json
python dev/score_dev.py dev/worlds dev/data dev/key.json dev/results/dev_outputs.json dev/results/dev_report.json
python dev/mutation_test.py
python dev/fuzz_compare.py 2000 31
python dev/fuzz_partb.py 800 21
python dev/regression_t2.py <path to studies/aletheia_blind_test_2>
```
