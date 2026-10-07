# Start message for the generator session (blind test 4), English translation

This is an English translation of [`GENERATOR_START.md`](GENERATOR_START.md). The Arabic text is the one that will be used, and it is authoritative where the two differ.
**Status:** fixed at sealing (2026-10-07).

**Before starting** (instructions to the project owner):
- Open a new Claude session whose working folder is this folder: `D:\work_app\aletheia_research\aletheia_blind_test_4`. That way the project memory is not loaded into it.
- Choose the highest reasoning level, and allow code execution.
- Do not pass any world, or any validator output, to the build session before the outputs hash is published.

**The message, pasted verbatim:**

```
You will generate the worlds of blind test 4 in the Aletheia project. You are the "world generator" of the protocol.

1. Read ONLY: the file protocol_v4.md in this folder, the files in the folders registry and lang, and the Notion page "Blind test 4: the registry and the identity card". Read nothing else.
2. Forbidden to open: the folders procedure, dev and results; any folder of earlier tests or comparisons; the folder language_v0; any other Notion page; and the Claude memory folder. Never read the code in the scorer folder: you only run the validator.
3. Write worlds/W-01.json to W-30.json and key/key.json, as specified in the protocol, in the description language v0.4 and against the sealed registry. Use code and exact fractions.
4. Verify by yourself first: write key/verify_key.py from the protocol alone, run it, and save its output in key/verify_output.txt. Then run:
   python scorer/validate_v4.py worlds key/key.json
   and repair your files until it prints VALID. The validator may take minutes.
5. Update progress.txt after every stage.
6. On bias: you are from the same model family that wrote the procedure, so you may unintentionally make worlds that are easy for it. Follow section 11 of the protocol: unfamiliar forms, numbers and dimensions; a varying deciding transformation; old observations close to the edge of their precision; and genuinely tempting baselines. Do not add constraints that make the test easier than the protocol requires.
7. Use the registry as it is. If you doubt that a card is physically right, write it in key/generator_notes.md and continue with the card as written.
8. If you find an ambiguity in the protocol, or a requirement cannot be met, write it in key/generator_notes.md and stop. Do not resolve it yourself.
9. At the end, run: python tools/hash_files.py key/key.json
   and publish the hash in the steps table of the Notion page, at step 3. Do not publish the worlds anywhere else.
```
