# Addendum 1 to RESULTS.md (2026-10-22): a correction after the project owner's refutation attempt

RESULTS.md (SHA-256 9581a29f…331a) is unchanged. This addendum corrects one claim in it.

**The project owner's question:** what shows our method is right, if all it does when stuck is to say that branching is right? Is that not like saying "both answers are correct" to avoid admitting that one does not know?

**The correction.** RESULTS.md section 4 item 2 says that in C2 "history went OURS' way". That overstates the result. Under the registered scoring (PREREG section 4), a branching prediction AGREEs whenever history built any one of its branches, so in C2 OURS could not have scored a disagreement. The accurate reading is:
- history contradicted COUNT, FIRST and ORDER (each predicted only the quaternion branch);
- history did not contradict OURS;
- but OURS did not predict which branch Segre would choose.
The registered scoring rewards branching. MAXCON reached 4/4 largely by branching.

**What still holds** (all of it is the content of OURS' branch in C2, and none of it is a choice):
- each branch has an explicit witness (the quaternions; the tricomplex numbers);
- every other drop set is refuted or undecided;
- the decider is stated: whether the new units commute with i, or whether zero divisors are forbidden;
- Segre's stated reason for his choice was keeping the laws of ordinary arithmetic, which is that decider.
  - Not from the registered sources, background knowledge only: Hamilton chose the opposite branch to keep "the law of the moduli", which excludes zero divisors.

**Evidence that branching is not a default, from earlier blind tests and not from this one:**
- In test 2 the procedure decided in 20 worlds and branched in 10, all correctly.
- In test 4 the always-branch baseline (FORK_ALL) scored 18/39 against the procedure's 39/39.

**A post-hoc, NOT registered illustration.** Credit 1/k when history matches one of k branches:
- OURS 3.5/4;
- COUNT 3/4;
- FIRST 3/4;
- ASSOC 2.5/4 (C3 gives no answer);
- MAXCON 2.5/4;
- ORDER 0/4.
The edge of OURS over COUNT is half a case. This scoring was chosen after seeing the results, so it is evidence of nothing; it only shows the size of the difference.

**For later tests:** register a scoring that penalises branching before the run, and look for cases where OURS gives a single answer that history could contradict.
