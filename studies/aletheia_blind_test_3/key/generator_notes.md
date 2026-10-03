# Generator notes: blind test 3

Status: **resolved.** The first run of the sealed validator printed `INVALID (2 problems)` (see `key/validator_output_run1.txt`); the second problem followed from the first. I stopped and reported Issue 1. The project owner chose **option 1**. I applied it:
- `key/verify_key.py` now checks W8 under both readings (L and C).
- W-16's three new readings were replaced. It is still NEW: R3 TYPE as the sole reason, R1 BOUND, R2 and R4 SHAPE close to the boundary. No combination of R2 and R4, with or without R1 at 1/8, fits.
- Own check: `KEY CONSISTENT` (`key/verify_output.txt`). Sealed validator: `VALID` (`key/validator_output.txt`).

## Issue 1 (blocking): how rule W8 treats a candidate with an exact coefficient

**Protocol text (Section 3, W8):**
> W8: in a NEW world no combination of candidates explains the observations: the joint system with every candidate that is neither TYPE-impossible nor SYMMETRY-forbidden (actual factors; exact coefficients fixed; unknown ones free) and `mu` is infeasible.

There are two ways to read this.

- **Reading L (literal: one joint system).** Every eligible candidate is in the joint system. An exact coefficient stays fixed at its registered value, so that candidate cannot be switched off. My `key/verify_key.py` implements this reading.
- **Reading C ("no combination").** No *subset* of eligible candidates explains the observations. An exact-coefficient candidate may therefore be absent, i.e. its contribution is 0 instead of its registered value. The sealed validator's verdict on W-16 matches this reading. Its verdicts on W-03 and W-18 also match it, and they rule out a third reading in which exact coefficients are freed.

**Where they differ:** only W-16, which is a NEW world in the `dral` group.
- Its eligible candidates are R1 (exact coefficient 1/8), R2 (unknown) and R4 (unknown, dimmer). R3 is TYPE-impossible.
- Joint system {R1 fixed at 1/8, R2, R4}: **infeasible**. W8 holds under reading L.
- Joint system {R2, R4} without R1: **feasible**. W8 fails under reading C. The validator reports `PROBLEM W-16: W8: a combination of candidates explains the observations`.
- Joint system with R1 freed: feasible.

I checked all 9 NEW worlds, and every world that a Part B item turns into (or keeps as) NEW, under the three variants: R1-type candidates fixed, any subset, and freed. **Only W-16 depends on the reading.** W-03 and W-18 are infeasible under readings L and C (they become feasible only if exact coefficients are freed), and the validator accepts them. No Part B item is affected.

**Effect if left unresolved:** W-16 is invalid under the sealed validator, so it would be excluded from scoring (1 of 27; VOID needs 6 or more). The brief requires `VALID`, so the files cannot be handed over as they are.

**Options for the project owner (I have not applied either):**
1. **Redesign W-16 so that W8 holds under both readings.** No combination of R2 and R4, with or without R1 at 1/8, may explain the readings. The minimal change is to new readings or states of W-16, keeping its role: NEW, R3 TYPE as the sole reason, R1 excluded by BOUND. The only Part B item on `dral` is D-02, an observation on W-11, which a change to W-16 does not touch. Then rerun `key/verify_key.py` (after making its W8 check apply both readings) and the sealed validator, recompute the key and publish its hash.
2. **The owner decides that reading L is the intended one.** The sealed validator then disagrees with the protocol on this point. That is a matter for the post-hoc audit, and W-16 would be excluded by the sealed code anyway.

Option 1 does not make the test easier. It only removes the dependence of one world's validity on this reading. I still did not apply it, because instruction 7 forbids deciding this myself.

## Interpretation points where my code and the validator agree (for the record, not blocking)
- **W7 in NO_DEFICIT worlds:** "sufficient" is defined only after step 0 finds a deficit (Section 2.7), so W7's limit of three does not apply to NO_DEFICIT worlds. After item D-16, the NO_DEFICIT world of `brel` has four eligible candidates whose A_R is feasible, and the validator accepts it.
- **Symmetry "maps the law to itself":** read as the same law with the same `mu` and `lam` (`h_R(Tq) = c_y * h_R(q)` identically). The validator agrees on the SYMMETRY-only candidate in W-01.
- **TYPE with rational powers:** a candidate needing L^-1 T is reachable as ga^(-1/2) (`dral` R2). The validator agrees.
- **`hidden_truth`:** omitted (it is optional) for W-05, W-17 and W-18. Their old readings come from the group's shared old model and their new readings from a different model, so no single model covers every reading. Both models are written in each entry's `notes`.
- **Key Part B entries** contain only the fields of Section 9. The generator's notes on the items are in `key/part_b_notes.md`.

## Files
- `key/verify_key.py`, `key/verify_output.txt`: own verification (prints `KEY CONSISTENT` under reading L).
- `key/validator_output_run1.txt`: output of `python scorer/validate_v3.py worlds data key/key.json`.
- `key/build_all.py`, `key/g_*.py`, `key/part_b.py`, `key/build_worlds.py`, `key/design_tools.py`, `key/partb_tools.py`: generator scripts (rebuild with `python key/build_all.py write`).
