# Blind test 4: the registry and the identity card

- **Status:** DONE.
  - Sealed 2026-10-07T05:22:45Z. The hashes are in `SEALED_HASHES.txt` and on the Notion page.
  - Key hash `33e7ce8b...`. Outputs hash `b1141207...` (published before the key was opened). Report hash `1d6fc968...`.
- **Outcome: PASS.**
  - 39/39 fillers correct with full identity cards and proofs.
  - Best baseline: DIMS, 30/39; McNemar p = 1/512.
  - 7/7 branches correct; no silent substitution, false alarm or silent choice; 0 exclusions.
- **Audit:** `results/audit.md`.
- **Exposure:** the worlds have not been shown to any language model. The generator's family (Claude) is never scored in any comparison on them.
- **Protocol:** [`protocol_v4.md`](protocol_v4.md).
- **Decisions:** the project's (Arabic) draft-specification notes for test 4 (section 12), the registry review (R1-R6), and the protocol review.

## The claim
On unseen worlds written in the description language v0.4 against a registry sealed before them, the procedure fills each filler's identity card by itself and labels the filler. The card has three items:
- **F1, dimensions:** consistency, with the new quantities' dimensions inferred.
- **F2, symmetry:** five transformations (time reversal, a mirror, charge conjugation, a quarter turn, the exchange of identical bodies). The actions come from the registry's kinds and meaning cards and from the bodies, never from the law under test.
- **F3, old observations:** the new thing as the filler describes it, computed at the observations the law was accepted on, never tuned there.

The label is SAME_LAW_NEW_STATE, ANOTHER_LAW, INVALID, or CONDITIONAL. A CONDITIONAL label comes with branches on unknown actions and a decisive observation.

## Layout
- `registry/`: the sealed registry and its inputs.
  - `registry.json` is the registry. `registry_notes.md` gives the meaning of each neutral id; the procedure never reads it.
  - `check_cards.py` checks the cards against 15 laws of known symmetry: 15/15.
  - `make_registry.py` builds the registry.
- `lang/`: the description language v0.4 (`SPEC_v0.4.md`) and its strict reader (`reader_v0.py`).
- `procedure/procedure_v4.py`: the procedure. It uses sympy for exact algebra, and an exact dictionary simplex (Chvátal, Bland's rule) for the observation systems, with Farkas certificates from the dual.
- `scorer/ref_v4.py`: the independent reference. It uses its own code, a different exact simplex and exact Gaussian elimination, and never imports the procedure. It checks validity rules V1-V13; V13 checks every product of the catalog's transformations.
- `scorer/score_v4.py`: the scorer.
- `scorer/validate_v4.py`: the world validator, sealed with the scorer and run by the generator.
- `tools/hash_files.py`: prints SHA-256 hashes, never file contents.
- `worlds/`, `key/`, `results/`: the test material.
  - `key/` holds the generator's builder, its independent verifier `verify_key.py` and its notes.
  - `results/` holds the outputs, the report, the run logs and the audit.
- `dev/`: the dev set and development checks, excluded from the test:
  - `make_dev.py` writes 24 dev worlds (toys for every trap, rewritten E2 worlds of blind test 1, and coverage-check cases), and `dev/rejected/` (a case the validator must reject).
  - `fuzz_compare.py`: random worlds, procedure against the reference.
  - `mutation_test.py`: deliberate corruption of outputs, worlds and keys.
  - `make_dev_hashes.py`: the dev fingerprints for V11.
  - `results/`: logs of the runs.

## Development checks run before sealing (consistency checks, not evidence)
- **Dev set:** the procedure is correct with all proofs on 26/26 fillers of the 24 dev worlds.
- **Mutation test:** 1119 corruptions caught, 0 missed; the originals are accepted.
- **Differential test:** 792 random fillers in the final runs, 0 disagreements on the card, the baselines or the zero report.
  - In several-filler worlds, a decisive state was found for every pair that has one.
  - The pairs without one were the same law written twice.

## Reproduce the test
From this folder, with Python 3.12 and sympy 1.14:
```
python procedure/procedure_v4.py run worlds results/outputs_rerun.json
python scorer/score_v4.py worlds key/key.json results/outputs_rerun.json results/report_rerun.json
python scorer/validate_v4.py worlds key/key.json
```
- `outputs_rerun.json` should have SHA-256 `b1141207d391c4cfd5fec8737d5f8ad5a6d8c4ebbd46ad3186180fcae3eae618`, and `report_rerun.json` should have `1d6fc968511ff7320a1abc420fa3348f91f9c4c629712efd06bf0e1a5a9a8e5c`. Both were checked byte for byte; the rerun names keep the published files intact.
- The validator should print VALID (30 worlds).
- `GENERATOR_START.md` is the (Arabic) start message given to the generator session; `GENERATOR_START_en.md` is its English translation.

## Rerun the development checks
```
python dev/make_dev.py
python procedure/procedure_v4.py run dev/worlds dev/results/dev_outputs.json
cd scorer && python score_v4.py ../dev/worlds ../dev/key.json ../dev/results/dev_outputs.json ../dev/results/dev_report.json --dev && cd ..
python dev/mutation_test.py
python dev/fuzz_compare.py 300 1
```
