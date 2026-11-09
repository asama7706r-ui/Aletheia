# The ladder theory against history: pre-registration

Registered 2026-10-21, BEFORE any case is coded and before any prediction is computed. Once its SHA-256 is posted on the Notion page «مسودة: اختبار نظرية السلّم بالتاريخ», this file is never edited. A later change goes in a dated addendum file, and its reason is written there.

Decisions of the project owner (2026-10-21, that page, section 9): (1) the claim below; (2) the scope is number systems (hypercomplex systems over the reals) only, for now; (3) hypothesis H1 is registered now.

## 1. What is tested
**The theory (OURS)**, the ladder rules as decided on the Q10 page and in the test-5 draft:
- the old rules are list v1 (Q10 11.8) for an origin in the reals, and the complex list (list v1 without the order bundle q14) for an origin in the complex numbers;
- a relaxation drops a set of whole rules; q1 and q2 are protected and never dropped;
- the preferred relaxations are the containment-minimal drop sets that leave the demand consistent with the kept rules and with a witness model (a concrete algebra satisfying the demand and every kept rule);
- several containment-minimal sets mean BRANCHES, and no silent choice;
- KNOWN_SUFFICES when an old kind already satisfies the demand; IMPOSSIBLE when every relaxation that keeps q1 and q2 fails.
At this stage the theory is compared at the level of whole rules q1-q14. Generated parts are not scored.

**Rivals** (the test-5 baselines), each applied to the same demand:
- COUNT: the drop sets of fewest rules; ties branch.
- MAXCON: the maximal consistent subsets of the whole list, with q1 and q2 treated like the others (nothing protected).
- ORDER: drop rules in the textbook order (order bundle q14, then commutativity q6, then associativity q5, then the rest by id) until the demand is consistent.
- ASSOC: like OURS, but q5 (associativity) is never dropped; if no relaxation exists, no answer.
- FIRST: the first consistent relaxation in a fixed enumeration (by size, then by rule ids), with no branching.

**Question:** which rule agrees with history more often, and where does each disagree?

## 2. The case pool (fixed now)
**Source of the pool:** the English Wikipedia article "Hypercomplex number", revision 1378320581 (2026-10-03T23:51:19Z). Its wikitext is saved as `sources/wikipedia/hypercomplex_number_wikitext.txt` (SHA-256 a8bf5c7378f3d0d1a506ed6d1b7658022b2185e89534f0a6903e585d0a9e4dc9).

**Rules:**
- R1. A case is a specific algebra named in that revision. Isomorphic names are one case. General classes and constructions are not cases (Clifford algebras in general, composition algebras, the Cayley-Dickson construction, "hyperquaternion algebras" as a family).
- R2. Excluded: every system used in designing the ladder rules, or isomorphic to one, because testing a rule on the data it was made from is no test. The evidence is listed in the table.
- R3. Excluded: a system whose demand cannot be written in description language v0.5.
- R4. Excluded at coding: a system for which the coder finds no source stating what its author wanted BEFORE the construction (a motivating demand distinct from the full definition), or no identifiable author and time. The coder decides this, with quotations.

| # | system (as named in the article) | iso class | status | reason |
|---|---|---|---|---|
| 1 | real numbers | R | origin | not a case |
| 2 | complex numbers | C | excluded R2 | Q10 page throughout; test-1 dev cases |
| 3 | split-complex numbers (= Cl1,0) | R x R | excluded R2 | test-1 dev case "split-complex with light lines" (aletheia_blind_test_1/protocol_v1.md, line 125) |
| 4 | dual numbers | R[e]/(e^2) | excluded R2 | test-1 dev cases; test-5 trap 11 |
| 5 | quaternions (= Cl0,2) | H | excluded R2 | Q10 page throughout |
| 6 | coquaternions = split-quaternions (= Cl1,1, Cl2,0) | M2(R) | excluded R2 | test-1 dev case "Dirac 1+1" (dev/dev-dirac11.json); Cl(1,1) and Cl(2,0) in the test-1 familiar list (protocol_v1.md, line 71) |
| 7 | biquaternions = Pauli algebra (= Cl3,0) | M2(C) | excluded R2 | quaternions over the complex numbers: Q10 B3, test-5 trap 13 |
| 8 | octonions | O | excluded R2 | Q10 page (9.4, 11.6 2b) |
| 9 | spacetime algebra (Cl1,3) | M2(H) | excluded R2 | the Dirac case, Q10 page throughout |
| 10 | Dirac algebra | H x H x C | excluded R2 | the Dirac case |
| 11 | sedenions | S | excluded R2 | checks/q10_assoc_parts_check.py (Cayley-Dickson to 16 dimensions) |
| 12 | tessarines = bicomplex numbers | C x C | POOL | |
| 13 | multicomplex numbers (2^n dimensions, n >= 3) | family | POOL, one case | n = 2 is case 12 |
| 14 | hyperbolic quaternions | (non-associative) | POOL | not counted for H1 (section 4) |
| 15 | split-biquaternions (= Cl0,3) | H x H | POOL | |
| 16 | split-octonions | split O | POOL | |
| 17 | complex octonions | C x O | POOL | |
| 18 | H x H (= Cl3,1) | M4(R) | POOL | flagged: physically close to the Dirac case (another signature), but not isomorphic to a used system |
| 19 | quaternionic matrix (H x H x H) | M4(H) | POOL | |
| 20 | trigintaduonions | 32-dim Cayley-Dickson | POOL | |
| 21 | sexagintaquatronions | 64-dim | POOL | |
| 22 | centumduodetrigintanions | 128-dim | POOL | |
| 23 | ducentiquinquagintasexions | 256-dim | POOL | |

Pool before coding: 12 cases (12 to 23). Many are expected to fall under R4, which is decided by the coder, not by me.

## 3. How a case is coded
- **Coder:** Gemini (via the agy command line), an independent model family that has not seen our rules, pages or predictions.
- **What the coder gets:**
  - for each pool system, its English Wikipedia article (revision recorded) and the freely available primary sources cited there (whole documents, not excerpts);
  - a template, and a plain list of standard properties to report (q1-q14 as plain field axioms, named; no relaxation rule, no ranking, no prediction).
- **What the coder writes for each case:**
  1. the author and the time;
  2. the motivating demand: what the author wanted before the construction, with verbatim quotations and their places in the sources;
  3. the origin (reals or complex numbers);
  4. the full definition as published;
  5. which of the listed properties the built system has;
  6. what history did next (used, ignored, replaced, and by what), with quotations;
  7. the R4 verdict (keep or exclude, and why).
- **My checks, before any prediction:**
  - every quotation must occur verbatim in the source file (a script);
  - every property is checked by computation on the published multiplication table;
  - the motivating demand is translated into v0.5, and the translation is reviewed against the quotations. If it cannot be written, the case falls under R3.
  - I correct only proven errors (a quotation not found, a property computed wrong), and I list every correction.

## 4. Scoring (per case, per rule)
- **AGREE:** the drop set of the system history built equals one of the rule's predicted drop sets.
- **OVER:** history dropped more than every predicted set. Either history relaxed more than needed, or the motivating demand was coded too thin.
- **UNDER:** history kept a rule the prediction drops. This is impossible if the demand and the list are right, so it is investigated as a coding or list error and reported.
- **OUT:** the rule gives no answer (no relaxation, a collapse, or no branch matches), or history's choice rested on reasons outside the list (a norm, physics), as stated in the quotations.
- When OURS branches, whether history (anyone, at any later time) built the other branches is recorded too.
- Reported as counts per rule, plus every disagreement in full. With this few cases no significance test is claimed.

## 5. Hypothesis H1 (Claude's, registered now)
**Claim:** in most cases, once the demand is fixed the relaxation is forced, and history's real choice was in revising the demand itself, which the ladder theory does not cover.

**Test, over the counted cases except hyperbolic quaternions:** H1 holds if, in at least half of them, both of these are true:
- (i) OURS gives a single minimal drop set for the motivating demand;
- (ii) the published definition contains defining relations that are not consequences of the motivating demand under the kept rules, or the author or a successor later replaced the system by changing its defining relations.

**Why hyperbolic quaternions are excluded:** H1 was formed on 2026-10-21 from reading that Macfarlane's relations force non-associativity and that he returned to complexified quaternions in 1900 to regain associativity (Wikipedia, "Hyperbolic quaternion"). A case that inspired a hypothesis cannot test it.

## 6. Order of work
1. Post this file's SHA-256.
2. Fetch the sources (section 3) and record their hashes.
3. Run the coder; check the quotations and properties; translate into v0.5.
4. Compute the predictions of OURS and the five rivals; post their SHA-256.
5. Compare, and report as is.
All of this happens before the test-5 procedure is written.

## 7. Limits stated now
- Few cases: this is a qualitative probe. A disagreement is informative; an agreement is weak evidence.
- Hindsight: Claude knows this history in outline. Hence the independent coder, the verbatim-quotation rule, and predictions registered before comparison.
- History is not truth: mathematicians chose for reasons outside algebra. Such reasons are tagged OUT, not counted against a rule.
- The pool is limited by one encyclopedia article; systems it does not name are not tested.
- A request header in the first download of the pool article carried the project owner's email address (Claude's mistake, 2026-10-21). It has no effect on the data, and later downloads send no personal data.
