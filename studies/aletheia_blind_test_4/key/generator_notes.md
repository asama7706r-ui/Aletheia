# Blind test 4: generator notes (2026-10-07)

Written by the world generator (a separate Claude session). This file stays in `key/`, closed until the key is opened.

## 1. Blocking problems
None. I found no ambiguity in the protocol that I had to resolve myself, and no requirement I could not meet.
The sealed validator printed `VALID (30 worlds)` on its second run.

## 2. Registry cards
I used every card exactly as written. None of them looks physically wrong to me. Remarks only:
- m20 (torque) is +1 under `rev_t` and axial under `refl_x`. That is consistent with torque = dL/dt, with L odd and t odd.
- m23's `refl_x` = +1 (a scalar, not a pseudoscalar, field) is a modelling choice, as the registry notes already say. No world depends on it.
- m22 and m19 to m21 are seed-anchored, so their dimensions are free in a world. Where a new quantity of such a meaning has dims `"?"`, its dims are inferred. In W-05, for example, the new observer velocity comes out dimensionless (a velocity divided by a fixed speed).

## 3. Observations for the project owner (not blocking)
1. **Order of `kept`.** The protocol does not say in which order the kept fillers are listed. The validator's first run rejected my key because I had listed them in file order, while its reference lists them sorted by id. I now write them sorted. The content is unchanged.
   - In two worlds the sorted order differs from file order: W-03 and W-28.
   - If the scorer compares the procedure's `kept` list in order, a procedure that writes file order would fail 8.2 there for a formatting reason only.
   - I did not reorder the fillers to avoid this, because that would tailor the worlds to the procedure. I have not read the scorer, so I do not know how it compares.
2. **T8.** My trap computation also counts a quarter turn (`rot_z`) acting by its matrix on a vector in the law. On that basis I declared T8 in W-02, W-27 and W-29, and the validator accepted it. The required sub-cases are each present in both the law and the filled law: m23 under `rev_t` in W-05 and W-08, and an axial vector under `refl_x` in W-13 and W-24.
3. **Order of my checks.**
   - I wrote `key/verify_key.py` and ran it (VERIFY: OK) before the first validator run.
   - After that run, I changed only one thing in it: the `kept` comparison now ignores order (point 1). I then reran it and saved the output to `key/verify_output.txt`.
   - The validator's raw output is in `key/validator_run1.txt` (rejected: `kept` order only) and `key/validator_run2.txt` (VALID).
4. **What I opened.**
   - I read only the allowed sources.
   - I also displayed `SEALED_HASHES.txt` in the root, whose content is the same as section 3 of the Notion page.
   - I computed SHA-256 over the bytes of `scorer/validate_v4.py` and `tools/hash_files.py` to compare them with the sealed list, without displaying their code. All hashes matched.
   - I never opened `procedure/`, `dev/`, `results/`, `language_v0/`, any other Notion page, or the memory directory.
5. **The world files are not bound by the published hash.** Only `key/key.json` is hashed on Notion. The SHA-256 of each world file is in `key/world_hashes.txt`. If you want the worlds bound before the procedure runs, a combined hash of `worlds/` could also be published.

## 4. What is in `key/`
- `key.json`: the key. Verdicts are the design intent. F2 statuses are given for every non-INVALID filler, `kept` and `decisive` for the several-filler worlds, and `traps` lists every trap whose condition holds. `notes` holds the readable design label (S, A, I, C, M) and a one-line description.
- `make_worlds.py`: the builder. It writes each world with readable labels, computes observation values exactly, then renames every id to a random neutral name. `name_map.json` keeps the mapping.
- `verify_key.py` and `verify_output.txt`: my own check, written from the protocol alone.
- `world_hashes.txt`, `validator_run1.txt`, `validator_run2.txt`, and this file.

## 5. Countering the shared-family bias (Section 11)
- **Old observations.** They sit at 80-97% of the observer's precision, never on its edge. Several worlds interleave old and new observations in file order. `accepted_at` varies from 1 to 4.
- **Which transformation decides varies.**
  - Kind-reading (`rot_z`) decides W-02, W-27 and W-29, including a "d-wave" unknown kind: uq*(hx^2 - hy^2) is odd under a quarter turn, so it keeps the law only with sign -1.
  - Cast-reading (`exch`) decides W-06, W-07 and W-15.
  - The meaning-reading transformations decide the rest.
- **Unusual unknowns.** Keeping assignments of -1 as well as +1. Two conditional transformations in one filler (W-08, W-10). A law that is itself conditional on a registry `"?"` card, where only the new unknown matters (W-23). An unknown sign that does not matter at all, because the law is already changed by the same transformation (W-01: SAME).
- **The baselines are genuinely tempting.**
  - FIX fails on 18 fillers. They include a filler whose pair of new quantities is exchanged symmetrically (W-15) and one exchanged asymmetrically (W-07).
  - DERIVE fails on 10 fillers, including a damping coefficient under `rev_t` (W-25), a torque used as a polar vector (W-13), and a gained symmetry (W-05).
  - DIMS fails on 9 fillers and FORK_ALL on 21.
- **F3 traps.**
  - W-30: a constant present all along whose required value breaks the old observations at small displacement.
  - W-20: a variable whose stated old value is too large.
  - Effects below precision (W-11) and zero for any value (W-19) on SAME fillers.
- **INVALID fillers that look right.**
  - W-12: written dims that make the filled law consistent but contradict the meaning (a "velocity" with acceleration dims; the filler would also be ANOTHER_LAW if it were not INVALID).
  - W-18: one coupling in two terms with incompatible dims.
  - W-16: written dims Q T.
  - W-03: a distance used as a mass.
- **Several-filler worlds.**
  - W-15: an ANOTHER_LAW filler whose fitted values look symmetric (ca1 near 0, ca2 near cz), although its form breaks the exchange.
  - W-28: three kept fillers, so three decisive pairs.
