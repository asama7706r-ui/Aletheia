# Blind test 5b: the new-kind ladder with a wider search

- **Status:** DONE.
  - Sealed 2026-10-31T10:03:06Z, after a clean regression run on the worlds of test 5. The hashes are in `SEALED_HASHES.txt` (SHA-256 `4c2fe881...`) and on the Notion page.
  - Two batches of 30 new worlds, from new runs of the two generators: a separate Claude session (batch A) and Gemini 4 Argon, run locally (batch B). Neither saw the worlds of test 5.
  - Key hashes `499aefe6...` (A) and `5f5721b2...` (B). Outputs hashes `6ebf3227...` (A) and `f7b0b9f4...` (B), published before the keys were opened. Report hashes `24a7d206...` (A) and `2e0c8da4...` (B).
- **Outcome: FAIL.** Both batches FAIL. In both, C2, C3 and C4 fail, and C1 and C5-C7 hold; 0 exclusions.
  - Batch A: decision accuracy 0.67 (20/30) against the best baseline's 0.70 (COARSE); McNemar p = 0.73. Verdicts 0.77, drop sets 0.47, marks 0.47.
  - Batch B: decision accuracy 0.77 (23/30) against 0.73 (COARSE); p = 0.50. Verdicts 0.90, drop sets 0.63, marks 0.63.
  - Pooled: 43/60 for the procedure and 43/60 for COARSE (`audit/pooled_5b.py`).
  - In both batches: no false witness, no silent collapse, no silent choice.
- **Audit:** `audit/audit.md`, with `audit/audit_correction_1.md` (2026-11-04). Post-hoc and not pre-registered; neither changes the result.
  - All 22 FREEDOM, IMPOSSIBLE and KNOWN_SUFFICES worlds are correct. The 17 wrong worlds all need a new kind: 12 miss a refutation and 6 miss a witness (B W-22 misses both).
  - Given the key's certificates, a copy of the procedure gives the truth in 17 of 17 (`audit/diag_inject_5b.py`); with test 5, 33 of 33 wrong worlds over the two tests. So again the search, not the rules, lost.
  - Time did not bind: the longest world took 1412 s of its 3600 s.
  - The correction: in all 12 missed refutations, the missing proof step was inside what the procedure already knew. A small proposer that reads only the world finds it in 10 of the 12; it was written after reading these worlds, so it shows nothing about new ones.
  - Later diagnostics on these spent worlds, not pre-registered: `audit/diag_moves_all.py`, `audit/slices_map.py` and `audit/cayley_dickson_check.py`, each with its output.
- **Exposure:** the procedure's author read the worlds after the outputs hashes, for the audit and later studies, so they are spent as test material. They are public from this publication on. Neither generator's model family is scored in any later comparison on them.
- **Protocol:** [`protocol_v5b.md`](protocol_v5b.md). Section 16 lists every change from protocol v5.
- **Decisions:** the project's (Arabic) review page for test 5b, and the workshop page, sections 10.4-10.13 (option C and its measurements).

## The claim
The same claim as [blind test 5](../aletheia_blind_test_5/README.md), with the same seed, language, workshop, composition, bounds, time limit and criteria, on new worlds from new generator runs. Test 5's audit found that the rules were applied correctly and the search was too narrow. So 5b tests a widened search ("option C"):
- refutation by small groups of kept rules first;
- learning minimal conflicting sets of rules, and searching only the candidates they leave (minimal hitting sets);
- a shape-first witness search, associative and non-associative, in the time the first phase leaves;
- the corrections listed in the protocol's Section 16, among them the code error that test 5's audit correction found.

## Layout
- `seed/`, `lang/`: the same sealed tower and description language v0.5 as test 5, byte for byte.
- `procedure/procedure_v5b.py`: the procedure. It runs test 5's `procedure_v5.py` (unchanged) with the changes in `proc_c.py`, `proc_c2.py` and `proc_c3.py`, and the witness search in `shape_search.py`, `shape_search_na.py`, `shape_driver.py` and `solver_worker.py`. All of these are sealed.
- `scorer/`: the reference (`ref_v5b.py`; it never imports the procedure), the certificate checker (`certs_v5.py`, unchanged from test 5), the baselines (`baselines_v5b.py`), the scorer (`score_v5b.py`), the world validator (`validate_v5b.py`) and the dev fingerprints.
- `tools/`: `hash_files.py` and `make_packages_5b.py` (the generator packages, made at sealing).
- `run/run_batches_5b.py`: the harness that ran the procedure once on both batches. It runs on AC power only, keeps the machine awake, logs the power source, and restarts a world from nothing after 60 s on battery.
- `batch_A/`, `batch_B/`: the 30 worlds and the key of each batch. The worlds were copied from the generators' packages before the run, the keys after the outputs hash was published.
- `results/`: the outputs, the per-world parts (`parts_X/`), the reports, the scorer's printed text (`score_X.txt`), the run logs, the run and scorer times, and the power log.
- `audit/`: the audit, its correction, and the diagnostic scripts with their outputs.
- `dev/`: the dev set and development checks, excluded from the test:
  - `batch_dev/`: test 5's 22 dev worlds. `key_test5.json` is test 5's dev key; `key.json` corrects two of its entries for 5b (its `README.md` says why).
  - `batch_t5A/`, `batch_t5B/`: the 60 worlds of test 5 with their keys, spent and used as dev worlds.
  - `check_dev_5b.py`, `check_validate_5b.py`, `mutation_test_5b.py`, `run_check_t5.py`, with their outputs in `check_dev/` and `check_t5/`. `check_t5/` also keeps the records of an earlier attempt, set aside on 2026-10-28 (`*.standby-20261028`).
  - `make_seal_5b.py`: the sealing script, run once.
- `GENERATOR_START_5b.md` is the (Arabic) start message given to the generators; `GENERATOR_START_5b_en.md` is its English translation.
- Not included: the generators' own working files (their builders, key verifiers, notes, logs and final messages), which stayed in their packages outside the lab.

## Reproduce the test
From this folder, with Python 3.12 and sympy 1.14 (the versions of the run):
```
python -I scorer/validate_v5b.py batch_A
python -I scorer/score_v5b.py batch_A results/outputs_A.json results/report_A_rerun.json
python -I procedure/procedure_v5b.py run batch_A/worlds results/outputs_A_rerun.json results/parts_A_rerun
```
and the same for `batch_B`.
- **The validator** printed VALID for each batch in the generators' runs (audit, section 1).
- **The scorer** has no time limit and no randomness, so on the published outputs it is expected to reproduce `results/report_X.json` byte for byte. It took 1136 s (A) and 318 s (B). It was not rerun for this publication.
- **The procedure** is not reproducible byte for byte. It stops on wall-clock limits (3600 s per world, 2700 s for its first phase, 20 s per group of rules), so its output depends on the machine and its load. The run took about 73 minutes (A, with one restart after the machine ran on battery) and 68 minutes (B). Compare a rerun's decisions with the published outputs, not its hash.
- Give the rerun a new parts folder, as above: the procedure resumes from any parts it finds. `run/run_batches_5b.py` refuses to overwrite `results/outputs_X.json`.

## Rerun the development checks
```
python -I dev/check_validate_5b.py
python -I dev/mutation_test_5b.py
```
`dev/check_dev_5b.py` compares with the outputs of the workshop's third measurement, which live in the lab's workshop folder and are not published, so it does not run here. `dev/run_check_t5.py` reruns the procedure on the 60 worlds of test 5, which took about an hour before sealing.
