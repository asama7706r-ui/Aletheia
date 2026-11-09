# Brief: coding the history of some hypercomplex number systems

## What this is
We are building a small, carefully sourced dataset about how some number systems ("hypercomplex numbers") were introduced:
- what their authors wanted before they arrived at the final system;
- what they actually defined;
- what properties the result has;
- what happened to it afterwards.

You are the coder. Your job is to report what the provided sources say, with exact quotations. Reconstruct nothing the sources do not support.

## The files you received
- `00_BRIEF.md` (this file), `01_CASES.md` (the 12 cases, and which source files belong to each), `02_PROPERTIES.md` (the properties to report).
- `sources/`: the evidence.
  - `W00` to `W08` are English Wikipedia articles in raw wikitext, at fixed revisions.
  - `S01` to `S05` are texts of historical papers. They were made by optical character recognition (OCR) of old scans and contain OCR errors.
  - `S06` is a scanned book (PDF page images, no text layer).

## Step 0: confirm the files
Using code, compute the SHA-256 of every file you received, and write them to `received_files_sha256.txt`, one line per file: `<sha256>  <file name>`. Do not edit any received file.

## Step 1: transcribe Clifford's two papers (S06)
`S06_Clifford_Mathematical_Papers_1882.pdf` is W. K. Clifford's *Mathematical Papers* (1882), a scanned book. The Wikipedia article W04 cites two places in it: the 1873 paper "Preliminary sketch of biquaternions", and a later paper or note on biquaternions. W04 links them at archive.org page positions n283 and n493, so look near PDF pages 284 and 494, and find them by their titles.
- Transcribe both papers in full into `clifford_transcription.txt`, as faithfully as you can.
- Mark the start of every PDF page with a line `=== PDF page N ===`.
- Do not correct the author's wording or notation. Write mathematical symbols in plain text, for example `w^2 = 1`.
- If you cannot find a paper, say so in `notes` and do not transcribe anything else in its place.

## Step 2: code each of the 12 cases
For each case in `01_CASES.md`, read every source file listed for it, and fill one record as in the schema below. All 12 records go into one JSON file, `cases_coded.json` (a list of 12 objects).

**Rules for evidence. These matter most.**
1. **Every historical statement needs at least one quotation** from the provided files. A quotation is copied character for character from the file, including OCR errors, odd spacing and broken words. Keep each quotation short, at most 60 words. Give the file name and a locator: a page header, a printed page number, a PDF page, or a section heading.
   - For Clifford, quote from your own `clifford_transcription.txt`, and give its PDF page.
2. **The provided files are the only evidence.** Do not search the web and do not use other documents as evidence. You may use your own background knowledge to know where to look. If you know something relevant that is not in the files, write it in `notes`, marked "NOT IN FILES".
3. **Separate three things** that are easy to mix up:
   - (a) what the author wanted or required BEFORE arriving at the final definition (the problem, the goal, the conditions they hoped to keep);
   - (b) choices the author made on the way (for example choosing a sign, adding a unit, accepting the loss of some property);
   - (c) the final published definition.
   If the sources do not separate them, say so.
4. **Exclusion.** Set `"include": false` when the files contain no source stating what an identifiable author wanted before the construction (item a), or when no author and time can be identified. Explain why in `exclusion_reason`, and still fill the other fields as far as the files allow.
5. **Properties.** For each property in `02_PROPERTIES.md`, write `holds`, `fails` or `unclear`.
   - Say whether you computed it from the multiplication rules (`computed`, and you may and should use code) or took it from a source (`stated`, with a quotation).
   - When a property fails, give one concrete counterexample from the multiplication rules.
6. **Families.** A case that is a family (for example "multicomplex numbers, 2^n dimensions for n >= 3") is coded at its first member beyond the cases already listed (here n = 3), unless the sources treat the family only as a whole.

## The schema of one record
```json
{
  "case_id": "C1",
  "system": "name as in 01_CASES.md",
  "include": true,
  "exclusion_reason": "",
  "author_and_time": {"author": "", "year": "", "quotes": []},
  "wanted_before_construction": {"summary": "", "requirements": [], "quotes": []},
  "choices_during_construction": {"summary": "", "quotes": []},
  "coefficients": "real | complex | other (say which)",
  "published_definition": {
    "basis": [],
    "multiplication_rules": [],
    "assumptions_stated_by_author": "",
    "quotes": []
  },
  "properties": {
    "P1": {"value": "holds | fails | unclear", "how": "computed | stated", "reason": "", "quotes": []}
  },
  "what_happened_next": {"summary": "", "quotes": []},
  "notes": ""
}
```
- Each quotation is an object: `{"file": "S02_Cockle_1849a.txt", "locator": "p. 41", "text": "exact characters"}`.
- `properties` has the keys P1 to P14.
- Write multiplication rules as plain equations, for example `i*j = k`, `j*i = -k`, `i*i = -1`.

## What to hand back
Three files: `received_files_sha256.txt`, `clifford_transcription.txt` and `cases_coded.json`. Also give a short report in plain text: anything you could not do, and any doubt about a source.
