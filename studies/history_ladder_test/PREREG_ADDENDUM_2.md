# Addendum 2 to PREREG.md (2026-10-22): rules for translating the coded demands into v0.5

Written after reading the coder's return (CODING_CHECK.md) and BEFORE any prediction is computed. PREREG section 3 says that the motivating demand "is translated into v0.5, and the translation is reviewed against the quotations". The coded cases showed that this needs four rules, fixed here so that the translation is mechanical and not chosen case by case.

- **T1. Old laws are not part of the demand.** When an author's requirement restates a law of the old list, it is NOT written into the role, because the old list itself carries it. Examples: Cockle's "laws of combination" of ordinary algebra (S03 p. 408); Segre's preservation of the formal laws of ordinary arithmetic. Writing such a law into the role would hand the theory its answer. Whether the author's wish to keep it was honoured is compared afterwards, as part of history.
- **T2. A starting system outside the tower.** When the author started from a system that is not in the tower (only reals and complex numbers are; for example Clifford started from quaternions):
  - the role is written over the nearest tower kind below it, the reals or the complex numbers;
  - the starting system's defining relations are added to the role as given facts.
  The case is then labelled "origin outside the tower", and the label is reported with its result.
- **T3. Independence.** v0.5 cannot write "no linear relation" between units. The role writes the distinctness the author states or implies between named elements, as `!=` (for example `j != 1`, `j != -1`, `h != i`, `h != -i`). The gap is reported with the case.
- **T4. Stages.** The demand is the earliest stage the coder documents as "wanted before construction":
  - for C3, Macfarlane's 1891 requirement; his 1900 associative revision is "what happened next";
  - for C4, Clifford's elliptic case omega^2 = 1, which is the system of this case (split-biquaternions); the parabolic case omega^2 = 0 (dual quaternions) is recorded but is not this case.
- **And the coder's own property values are not used** (CODING_CHECK item 5). Claude computes every property from the published multiplication rules in `cases_coded.json`.
