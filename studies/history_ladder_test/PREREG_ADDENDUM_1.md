# Addendum 1 to PREREG.md (2026-10-22, written before any case is coded)

PREREG.md (SHA-256 64cb957b049f208b238bc77012d9e955a0b67d71e0193d98c65268b452947cc7) is unchanged. This addendum records two changes to its section 3, made before coding, and their reasons.

1. **The coder.** It is Gemini 4 Argon in Google AI Studio, run by the project owner, instead of Gemini through the agy command line.
   - Reason: the agy command line on this machine has no access to Argon, and the project owner prefers the newest model of the independent family.
   - Independence is unchanged. Argon gets only the coder package: a neutral brief, the case list, a list of plain properties, and the sources. It gets no rule, ranking, prediction or project page.
   - The project owner carries the files both ways. Argon reports the SHA-256 of every file it received, and these are compared with `coder_package_expected_sha256.txt`.
2. **Clifford's papers.** The scanned book (S06) has no text layer, and this machine has no OCR tool and cannot render its JBIG2 page images.
   - So the coder first transcribes Clifford's two biquaternion papers into `clifford_transcription.txt` and quotes from that.
   - For this case (C4), Claude checks the quotations against the coder's transcription, not against the scan. The faithfulness of the transcription itself is NOT checked by Claude, and is stated as a limit.

**The package:** `coder_package/` and `history_coder_package.zip` (SHA-256 222bce5f0f3d1a542d830b7d3bee2098acdcbb71b0798480e46c03a37c137249), with:
- `00_BRIEF.md`: 8485e1934ae4a72a4d434f6f95095fe736a48c87331dbced8af4efd1cef61ddc
- `01_CASES.md`: 013ed9f94750988ced0da6e3c14872d8dfa09c17f307e757d7e2abcc29c0153e
- `02_PROPERTIES.md`: bf8879421ed2a065d36179ecdab3a63edeef1e996dc48b38f7258d15e9e693eb
- the 15 sources, whose hashes are listed in `coder_package_expected_sha256.txt`.
