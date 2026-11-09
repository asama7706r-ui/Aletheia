# Blind test 5, audit correction 1 (2026-10-24)

`audit.md` (SHA-256 1bbb8e63…, published 2026-10-23) is left unchanged. This file corrects its section 5.2, and the matching sentences on the Notion test page (7.4) and the workshop page (10.3, item 3). The checks are in `aletheia_research/workshop_search_study/`.

## What was wrong
Section 5.2 said that 11 of the 12 candidates the procedure kept, but the truth refutes, are missed by both programs because of "the shared blind spot that limit 10 declared". I wrote this without checking what each missing proof needs. Checked now (`diag_q6on.py`, and the key's proofs), the 12 candidates have four causes:

| cause | candidates | in which program |
|---|---|---|
| **A code error.** A kept q6[on] (e1 commutes with the new names) gives no relator when the ambient is associative. `procedure_v5.World.copy_instances` returns nothing for associative ambients, and `ref_v5.Searcher` sets `copies = []` there. Associativity implies the q5 copies, but not q6[on]. | 5: A W-06, A W-18, B W-28, W-29, W-30 | both |
| **An undeclared limit.** Copy instances take single names as arguments only. The key's proofs use products of two names written in the role: xa·e1, xu·yo, xa·yb. | 5: A W-09 (2), A W-28 (2), A W-29 (1) | both |
| **The declared limit (linear forms).** The key splits on fa·fa and fa − 1, a factor of degree 2. An inverse node on fa, which is a linear form, would also refute it, but both programs try inverse nodes only on members of zero-divisor pairs. | 1: A W-10 | both |
| **Time.** The sealed procedure refutes this candidate in isolation at once, but in the run the world hit the 3600 s limit first. | 1: A W-28 {q5, q6[on]} | procedure only |

- **The code error:** with it fixed, the sealed procedure's own search refutes all five of its candidates at once.

## What stands
- **Section 4 stands.** Given the key's certificates, the procedure's own code gives the truth in 16 of 16 worlds. The errors are missing evidence, not wrong rules.
- **The truth is not affected.** With the q6[on] error fixed in a copy of the reference, the truth of all 60 worlds is unchanged (`diag_truth_q6on.py`: A 0 of 30, B 0 of 30). The keys' certificates already covered these candidates. The published scores stand.
- **The weight changes.** Limit 10 foresaw blind spots of shared search ideas. Here most of the missed refutations come from a code error and an undeclared limit, both shared because both programs have one author. Only the generators' certificates caught them, as limit 10 intended for blind spots, so the safeguard worked. But it worked against an error the protocol did not declare.

## Lesson for a next test (proposal, not decided)
Before sealing, check that every kept unit can produce a relator in every ambient. For example, mutation tests that drop each copy unit in turn and expect some refutation to fail.
