# Blind test 5b audit: correction 1 (2026-11-04)

`audit.md` stays as it is, with its published hash. This file corrects one sentence of it. The result does not change:
test 5b FAILED, and the injection check is still 17 of 17.

## What was wrong

Section 4.1 says: "in every one of the 12 worlds the factor comes from a polynomial written in the role itself". I
wrote that after reading the roles, without computing it, and it is too strong. Checked world by world:

- **The polynomial is written in the role (8 worlds):** A W-01, A W-21, B W-15, B W-21, B W-22, B W-25, B W-26, B W-27.
  A W-21 (`vo*vo = e1`) still needs sqrt(2) to factor it.
- **The word is written, and the relation is derived by the rules (3 worlds):** A W-04, A W-20 (the word is in an
  inequation, and its polynomial follows by associativity), A W-17 (the factors are written, and the zero product
  follows by associativity).
- **Neither is written (1 world):** A W-07. The word da·ke·lu·mi appears nowhere in the role; the generator chose it
  (its notes call it the "omega*omega = 441 argument").

## What holds instead (`diag_direction_5b.py`, computed)

On a copy of the 5b procedure, for the branch the output added in each of the 12 worlds:

- **12 of 12:** the procedure's own rewriter for that candidate already reduces the key's a·b to 0.
- **12 of 12:** given a and b, its own search closes both cases.
- **10 of 12:** a small proposer that reads only the world and the rewriter (not the key) derives a pair that closes
  both cases, and the sealed checker accepts the whole refutation. It proposes at most 8 pairs, the first one works
  each time, and each world takes under a second. It misses exactly A W-07 and A W-21.

So the better statement is: **the missing step was inside what the procedure already knew in all 12; a simple
derivation from the role's words finds it in 10.** Lesson 9.1 of `audit.md` should read the same way: take split
factors from what the procedure's own system knows, starting from the role's words.

## Limits of this diagnostic

- It is not pre-registered, and it runs on spent worlds.
- I wrote the proposer after reading these 12 worlds, so it may fit them. It shows nothing about new worlds.
- It checks one branch per world. It does not show that the whole decision would become correct, and it measures no
  regression on other worlds.
- It covers refutations only. The six missing witnesses are not touched.

## Also added (`narrowing_5b.py`, computed)

In the sealed run, over the 38 worlds with a phase-1 record, the procedure tested 195 of 29,312 candidates as whole
candidates; conflicts ruled out the rest. It also tried 1,269 groups of rules.
