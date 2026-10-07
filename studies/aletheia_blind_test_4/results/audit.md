# Blind test 4 - audit (2026-10-07)

Written by the procedure author (Claude) after the report was published, as the protocol requires (section 0, order step 7). It checks the run, not the design; the pre-registered interpretation (protocol section 9) is not changed here.

## 1. Order of the run (all checked)
1. Sealed at 2026-10-07T05:22:45Z: 13 files in `SEALED_HASHES.txt` (its own SHA-256 is `a7bcbe146d9ad398c3c42687e18b92c503ccfa96e856aa5c949b875397338dad`).
2. The generator, a separate Claude session, wrote 30 worlds and the key, ran its own `key/verify_key.py` (VERIFY: OK), and then ran the sealed validator.
   - Run 1: rejected, only for the order of the `kept` list (see 3.1).
   - Run 2: VALID (30 worlds).
3. The generator published the key hash `33e7ce8ba4194d27898374da3b38bd6c6c11731bb41f5e54ecba342ebf7a3ecf` on the Notion test page.
4. Before running the procedure, I checked:
   - all 13 sealed hashes: OK;
   - the key's hash: equal to the published one.
   I opened neither the worlds nor the key.
5. The procedure ran from 06:08:38Z to 06:08:45Z (7 s) with no error. The outputs hash `b1141207d391c4cfd5fec8737d5f8ad5a6d8c4ebbd46ad3186180fcae3eae618` was published before the key was opened.
6. The scorer gave PASS. The report hash is `1d6fc968511ff7320a1abc420fa3348f91f9c4c629712efd06bf0e1a5a9a8e5c`, and the printed report was published verbatim.
7. After the report, the validator was rerun: VALID (30 worlds), 4.5 s.

## 2. Result
- The procedure is correct on 39 of 39 fillers. Correctness covers the whole card: the verdict and its reason, every transformation's status with its proofs, F1 with its inferred dimensions, F3 with its point or Farkas certificate, and the decisive observations of every branch.
- No world was excluded.
- No silent substitution and no false alarm.
- Branches: 7 of 7 CONDITIONAL fillers are correct.
- INVALID: 4 of 4 detected (3 single-filler worlds, plus one filler in W-03).
- Silent choice: none. Every pair of kept fillers in the 5 several-filler worlds got a valid decisive state.
- **Baselines** (fillers correct, out of 39):

| baseline | correct |
|---|---|
| DIMS (best) | 30 |
| DERIVE | 29 |
| FIX | 21 |
| FORK_ALL | 18 |

- **McNemar against DIMS:** b = 9, c = 0, p = 1/512.
- All of DIMS's errors are fillers decided, or branched, by a meaning-reading transformation. This is the "false sufficiency" the baseline stands for.

## 3. Findings
### 3.1 The validator requires `kept` sorted by filler id (a protocol omission, harmless)
- The protocol does not say in which order `kept` is listed. The validator compares the key's `kept` with its sorted reference, so the generator's first key (file order) was rejected in W-03 and W-28.
- The generator then sorted the lists. The worlds were not changed.
- The scorer's own check of the procedure's `kept` (silent choice) is order-free, so the score does not depend on order.
- **For the next test:** state the order, or compare as sets.

### 3.2 The worlds were not bound by a published hash before the run (the generator's note 5)
- Only `key/key.json` was hashed on Notion. The generator recorded each world's SHA-256 in `key/world_hashes.txt`, and all 30 match the worlds that were run (checked after the key was opened).
- I never wrote to `worlds/`.
- **For the next test:** publish a combined hash of the worlds together with the key hash.

### 3.3 T8 counts the quarter turn too (as written)
- The generator's trap computation, like the validator's, counts `rot_z` acting by its matrix on a vector in the law as T8. This follows the protocol's wording ("a matrix that is not a multiple of the identity").
- The draft's intent, matrix actions read from meaning cards, is covered separately by the required sub-cases:
  - m23 under `rev_t`: W-05 and W-08;
  - an axial vector under `refl_x`: W-13 and W-24.

### 3.4 What the generator read and ran
- The generator states that it read only the allowed sources (`key/generator_notes.md`, section 3.4). It computed SHA-256 over `scorer/validate_v4.py` and `tools/hash_files.py` without displaying them.
- Its scripts import only the sealed reader (`lang/reader_v0.py`) and its own `verify_key.py`. I checked this by reading their import lines.
- It reported no doubtful registry card.

### 3.5 Three independent implementations agree
- The procedure, the scorer's reference and the generator's own `verify_key.py` were written separately; the last one from the protocol alone, in another session.
- They agree on every verdict. They also agree on the number of fillers each baseline gets wrong: FIX 18, DERIVE 10, DIMS 9, FORK_ALL 21.
- This is evidence that the protocol's rules are computed as written. It is not evidence that the rules or the registry are physically right.

### 3.6 Composition (from the validator and the generator's check)
- **Single-filler worlds:** 7 SAME, 8 ANOTHER (W-20 and W-30 decided by F3 alone), 3 INVALID, 7 CONDITIONAL.
- **Several-filler worlds:** W-03, W-09, W-15, W-28 and W-29. Three of them have an ANOTHER_LAW or INVALID filler.
- **Traps:** each appears in at least 2 worlds.
  - T7: through registry cards (m09, m10) and through new quantities of meaning `"?"`, including an unknown kind (W-02).
  - Each type of transformation decides at least 2 worlds: kind-reading W-02, W-27, W-29; cast-reading W-06, W-07, W-15.
- **Old observations:** at 80-97% of their precision (generator's note).

### 3.7 Zero-effect report (reported, not scored)
- Labels: absent 102, zero for any value 7, below precision 4, not applicable (F3 fails) 8.
- They agree with the reference on 39 of 39 fillers.
- This is the first data for the ledger test, where a zero effect separates a witness from a non-witness.

## 4. Limits (unchanged from protocol section 13)
- **The generator and the procedure author are the same model family.** The generator was told to counter this (protocol section 11) and reports having done so: unfamiliar forms, varying deciding transformations, tempting baselines, and old observations near the edge of precision.
- **"Correct" is defined by our rules and by the sealed registry.** The cards were checked against 15 laws of known symmetry; nothing in this test checks them further.
- **Not tested here:** the catalog's blind spot ("what the registry does not know") and accidental symmetries (Q9 page, 9.15). F4 and F5 are not tested either.
- **The worlds are formal and few.** PASS is evidence that the identity card can be filled automatically with proofs. It is not evidence of real discovery, nor of superiority over language models.
