# Start messages for the two generators (blind test 5), English translation

This is an English translation of [`GENERATOR_START.md`](GENERATOR_START.md). The Arabic text is the one that will be used, and it is authoritative where the two differ.
**Status:** sealed with the protocol on 2026-10-23 (the hashes are in `SEALED_HASHES.txt`).

**Before starting** (instructions to the project owner):
- The two generator packages are made at sealing with `python tools/make_packages.py D:\work_app\t5_gen`. Each generator gets a folder outside the lab, holding only the protocol, the seed, the language, the world validator and the hash tool: nothing of the procedure.
- **Batch A (Claude):** open a new Claude session whose working folder is `D:\work_app\t5_gen\batch_A`, so that the project memory is not loaded. Choose the highest reasoning level, and allow code execution.
- **Batch B (Gemini 4 Argon, local):** run it with working folder `D:\work_app\t5_gen\batch_B`, with Python.
- Do not pass any world, key, or validator output to the Claude session that wrote the procedure before that batch's outputs hash is published.

## Message A, pasted verbatim into the Claude session

```
You will generate the worlds of blind test 5 in the Aletheia project, batch A. You are the "world generator" of the protocol.

1. Read ONLY what is in this folder: protocol_v5.md and the folders seed, lang and tools. Never read the code in the folder scorer: you only run the validator.
2. Forbidden to open any folder outside this one, in particular D:\work_app\aletheia_research, D:\work_app\MyOwnAi and D:\work_app\t5_gen\batch_B, the Claude memory folder, and any Notion page.
3. Write worlds/W-01.json to W-30.json and key/key.json as the protocol specifies (Sections 3, 4, 5, 6 and 11), in the description language v0.5 against the sealed seed. Use code and exact fractions.
4. Verify by yourself first: write key/verify_key.py from the protocol alone, run it, and save its output in key/verify_output.txt. Then run:
   python scorer/validate_v5.py .
   and repair your files until it prints VALID. The validator may take minutes. For every world it names the candidates its reference could not decide: give each one a witness or a refutation certificate in the protocol's format, or change the world.
5. Update progress.txt after every stage. Write in it the exact model name, and the SHA-256 of every file you received, computed with python tools/hash_files.py.
6. On bias: you are from the same model family that wrote the procedure, so you may unintentionally make worlds that are easy for it. Follow Section 11 of the protocol: unfamiliar relations and numbers; do not build on the examples of the protocol or the language files; make every baseline genuinely tempting. Do not add constraints that make the test easier than the protocol requires.
7. If you find an ambiguity in the protocol, or a requirement cannot be met, write it in key/generator_notes.md and stop. Do not resolve it yourself.
8. At the end run:
   python tools/hash_files.py --worlds worlds
   python tools/hash_files.py key/key.json
   and write both hashes in progress.txt. The project owner publishes them. Do not publish the worlds anywhere.
```

## Message B, pasted verbatim into Gemini 4 Argon

```
You will generate the worlds of blind test 5 in the Aletheia project, batch B. You are the "world generator" of the protocol.

1. You run on the project owner's machine and can reach the disk. So work in this folder only: D:\work_app\t5_gen\batch_B. Read only what is in it: protocol_v5.md and the folders seed, lang and tools. Never read the code in the folder scorer: you only run the validator.
2. Forbidden to open any folder outside this one, in particular D:\work_app\aletheia_research, D:\work_app\MyOwnAi and D:\work_app\t5_gen\batch_A.
3. Write worlds/W-01.json to W-30.json and key/key.json as the protocol specifies (Sections 3, 4, 5, 6 and 11), in the description language v0.5 against the sealed seed. Use Python code and exact fractions.
4. Verify by yourself first: write key/verify_key.py from the protocol alone, run it, and save its output in key/verify_output.txt. Then run:
   python scorer/validate_v5.py .
   and repair your files until it prints VALID. The validator may take minutes. For every world it names the candidates its reference could not decide: give each one a witness or a refutation certificate in the protocol's format, or change the world.
5. Update progress.txt after every stage. Write in it the exact model name, and the SHA-256 of every file you received, computed with python tools/hash_files.py.
6. Follow Section 11 of the protocol: unfamiliar relations and numbers; do not build on the examples of the protocol or the language files; make every baseline genuinely tempting. Do not add constraints that make the test easier than the protocol requires.
7. If you find an ambiguity in the protocol, or a requirement cannot be met, write it in key/generator_notes.md and stop. Do not resolve it yourself.
8. At the end run:
   python tools/hash_files.py --worlds worlds
   python tools/hash_files.py key/key.json
   and write both hashes in progress.txt. The project owner publishes them. Do not publish the worlds anywhere.
```
