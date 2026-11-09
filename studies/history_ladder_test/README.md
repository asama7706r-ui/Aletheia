# The ladder theory against history

- **Status:** DONE.
  - Pre-registered 2026-10-21, before any case was coded: [`PREREG.md`](PREREG.md) (SHA-256 `64cb957b...`), with two addenda written before any prediction was computed.
  - Predictions registered 2026-10-22: the hash of `predictions/PREDICTIONS_SHA256.txt` (`260af655...`) was posted before the comparison with history.
  - Results 2026-10-22: [`RESULTS.md`](RESULTS.md) (`9581a29f...`), and [`RESULTS_ADDENDUM_1.md`](RESULTS_ADDENDUM_1.md), a correction made the same day after the project owner tried to refute the result.
- **Outcome:** a qualitative probe on four historical cases; no significance is claimed.
  - Agreement with the drop set history built: OURS 4/4, MAXCON 4/4, COUNT 3/4, FIRST 3/4, ASSOC 3/4, ORDER 0/4.
  - Three cases (C1, C3, C4) are forced: every rule that computes forced drops agrees there.
  - Only C2 (Segre's tricomplex numbers) discriminates. OURS branches, and history built both branches. The addendum corrects the reading: under the registered scoring a branching prediction agrees whenever history built any one of its branches, so in C2 OURS could not have scored a disagreement. History did not contradict OURS, but OURS did not predict Segre's choice.
  - MAXCON reaches 4/4 largely by branching, and in C3 and C4 it adds a branch where 1 + 1 = 0. The protected rule q2 is what removes that branch in OURS.
  - Hypothesis H1 ("history's real choice was in revising the demand") holds in 1 of 3 counted cases: **not supported**.
- **Coder:** Gemini 4 Argon in Google AI Studio, run by the project owner (`PREREG_ADDENDUM_1.md`). It got only the coder package: a neutral brief, the case list, a list of plain properties and the sources, and no rule, ranking or prediction. All 18 file hashes it reported equal ours, and 316 of its 316 quotations occur verbatim in the files they name (`CODING_CHECK.md`).

## The question
Which rule for relaxing the old laws agrees with history more often, on hypercomplex number systems? OURS is the ladder theory: drop a containment-minimal set of whole rules (q1-q14), never the protected q1 and q2, and branch when several minimal sets exist. Its rivals are the baselines of blind test 5: COUNT, MAXCON, ORDER, ASSOC and FIRST.
- **The case pool** is fixed by a rule: the systems named in one revision of the English Wikipedia article "Hypercomplex number", minus those used in designing the rules (PREREG, section 2).
- **The coder** decided which cases have an author's demand stated before the construction. Four did: C1 Cockle's tessarines (1848), C2 Segre's tricomplex numbers (1892), C3 Macfarlane's hyperbolic quaternions (1891), and C4 Clifford's split-biquaternions (1873). Eight were excluded.
- **The demands** were translated into description language v0.5 by the fixed rules of `PREREG_ADDENDUM_2.md`, and the predictions were computed and registered before the comparison.

## Layout
- `PREREG.md`, `PREREG_ADDENDUM_1.md` (the coder, and Clifford's scanned book), `PREREG_ADDENDUM_2.md` (the translation rules T1-T4).
- `sources/`: what was fetched, and how (`MANIFEST.md`).
  - `wikipedia/`: the articles as raw wikitext at recorded revisions, with the API answers.
  - `primary/`: the texts of the primary sources, from the OCR of old scans, with their errors kept. Macfarlane's article is also there as a PDF, and Segre's text comes with the GDZ page files it was joined from.
- `coder_package/`: what the coder received (all but `S06`, below): the brief (`00_BRIEF.md`), the cases (`01_CASES.md`), the properties (`02_PROPERTIES.md`) and the sources. `coder_package_expected_sha256.txt` lists the sources' hashes.
- `coder_returned/`: the coder's files, unchanged: `cases_coded.json`, `clifford_transcription.txt`, `coder_report.txt` and `received_files_sha256.txt`.
- `CODING_CHECK.md`: the check of the coder's return, made before any prediction.
- `predictions/`: `PREDICTIONS.md`, the four demands as v0.5 worlds (`roles/`), the output of the witness check, and `PREDICTIONS_SHA256.txt`.
- `RESULTS.md`, `RESULTS_ADDENDUM_1.md`.
- `tools/`: `fetch_wiki.py` (the Wikipedia fetch; the request carries no personal data), `gdz_to_text.py`, `check_quotes.py`, `make_roles.py`, `algebras.py` and `check_witnesses.py` (exact arithmetic).

## Files not included
Five large files are not in this repository. Each is listed with its SHA-256, so a copy fetched from its source can be checked. `sources/MANIFEST.md` says where each came from.

| file | size | SHA-256 |
|---|---|---|
| `history_coder_package.zip` (the coder package as sent; its 18 files are byte for byte those of `coder_package/` plus `S06` below) | 22.8 MB | `222bce5f0f3d1a542d830b7d3bee2098acdcbb71b0798480e46c03a37c137249` |
| `coder_package/sources/S06_Clifford_Mathematical_Papers_1882.pdf` (W. K. Clifford, *Mathematical Papers*, 1882, scanned; archive.org item `mathematicalpap00smitgoog`) | 23.2 MB | `239d7feebbb66d7651e4662874d73cf273e2d9fc60d0f9678cfc1f1265f0e583` |
| `sources/primary/clifford_mathematical_papers/mathematicalpap00smitgoog.pdf` (the same file) | 23.2 MB | `239d7feebbb66d7651e4662874d73cf273e2d9fc60d0f9678cfc1f1265f0e583` |
| `sources/primary/cockle_phil_mag_vol33_1848/londonedinburghp33lond.pdf` (Philosophical Magazine, vol. 33, 1848, scanned; Biodiversity Heritage Library) | 32.7 MB | `347dc47b5e72a92ed13e2ebc560c6568d8eb74b259da288d54d89b398eea15da` |
| `sources/primary/cockle_phil_mag_vol34_1849/londonedinburghp34lond.pdf` (Philosophical Magazine, vol. 34, 1849, scanned; Biodiversity Heritage Library) | 31.6 MB | `0fdf9e7ed5dda3f90f0bdf2814187950a894614aabc2531fdb34889cdb3a7687` |

The texts made from the two Cockle volumes are included. Clifford's book has no text layer: the coder transcribed the two papers it needed (`coder_returned/clifford_transcription.txt`), and Claude did not check that transcription against the scan (a stated limit).

## Third-party material
- `sources/wikipedia/` and `coder_package/sources/W00`-`W08` are English Wikipedia text by Wikipedia contributors, at the revisions listed in `sources/MANIFEST.md`. They are under CC BY-SA 4.0, not under this repository's licenses.
- Macfarlane's article (`sources/primary/macfarlane_1902_hyperbolic_quaternions/`) comes from Zenodo record 2154076, released under CC0.
- The other primary texts are OCR of public-domain papers by Cockle (1848-1849) and Segre (1892), from the scans named in `sources/MANIFEST.md`.

## Rerun the checks
From this folder, with Python 3 (the tools read the v0.5 reader and the seed from the sibling folder `../aletheia_blind_test_5/`):
```
python -I tools/check_witnesses.py
python -I tools/check_quotes.py
```
- `check_witnesses.py` should exit 0 and print exactly `predictions/check_witnesses_output.txt`.
- `check_quotes.py` should print `quotations: 316; found verbatim: 316; not found: 0`.
- Both were rerun for this publication, with these results. Each takes under a second.
- `tools/make_roles.py` rewrites the registered files in `predictions/roles/`; if you run it, compare them with `predictions/PREDICTIONS_SHA256.txt`.
