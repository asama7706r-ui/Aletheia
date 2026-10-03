# Start message for the generator session (blind test 3), English translation

This is an English translation of [`GENERATOR_START.md`](GENERATOR_START.md). Claude translated it after the study. The Arabic original is the text that was actually used, and it is authoritative where the two differ.

**Before starting** (instructions to the project owner):
- Open a new Claude session whose working folder is this folder: `D:\work_app\aletheia_research\aletheia_blind_test_3`. That way the project memory is not loaded into it.
- Choose the highest reasoning level, and allow code execution.
- Do not pass any world, or any validator output, to the build session before the outputs hash is published.

**The message, pasted verbatim:**

```
You will generate the worlds of blind test 3 in the Aletheia project. You are the "world generator" of the protocol.

1. Read ONLY the file protocol_v3.md in this folder and the Notion page "Blind test 3: the nebulium check and reopening". Read nothing else.
2. Forbidden to open: the folders procedure, dev and results; any folder of earlier tests (aletheia_blind_test_1, aletheia_blind_test_2 and aletheia_llm_compare_1); any other Notion page; and the Claude memory folder. Never read the code in the scorer folder: you only run the validator.
3. Write worlds/W-01.json to W-27.json, data/D-01.json to D-18.json, and key/key.json, as specified in the protocol. Use code and exact fractions.
4. Verify by yourself first: write key/verify_key.py from the protocol alone, run it, and save its output in key/verify_output.txt. Then run:
   python scorer/validate_v3.py worlds data key/key.json
   and repair your files until it prints VALID.
5. Update progress.txt after every stage.
6. On bias: you are from the same model family that wrote the procedure, so you may unintentionally make worlds that are easy for it. Follow section 12 of the protocol: unfamiliar forms and numbers, genuinely tempting distractors, readings close to the decision boundaries, and a varying position of the answer in the ledger. Do not add constraints that make the test easier than the protocol requires.
7. If you find an ambiguity in the protocol, or a requirement cannot be met, write it in key/generator_notes.md and stop. Do not resolve it yourself.
8. At the end, run: python tools/hash_files.py key/key.json
   and publish the hash in the steps table of the Notion page, at step 3. Do not publish the worlds anywhere else.
```

**Translator's notes:**
- The Notion page named in item 1 is the project's Arabic notes page for this test. At generation time it held:
  - a summary of the test;
  - the steps table with the sealed hashes;
  - the review notes on the protocol;
  - this start message.

  It held no worlds and no answers.
- The generator followed item 7 once: it stopped and reported the W8 wording ambiguity in `key/generator_notes.md`. See `results/audit.md`, section 3.
