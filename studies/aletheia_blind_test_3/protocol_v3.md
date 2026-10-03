# Aletheia blind test 3 - pre-registered protocol v3

Status: SEALED. The SHA-256 hashes of this protocol and of the sealed code are published on the Notion page of blind test 3 and in `SEALED_HASHES.txt`. Environment used for development: Python 3.12.10, sympy 1.14.0. The decisions behind this protocol are in section 12 of the Notion page "مسودة مواصفة التجربة 3", which supersedes sections 0-11 of that page where they differ.

## 0. Roles, order and rules
- **Procedure author** (Claude, build session):
  - writes this protocol, `procedure/procedure_v3.py`, `scorer/ref_v3.py`, `scorer/score_v3.py`, `scorer/validate_v3.py` and `tools/hash_files.py`;
  - develops them ONLY on the dev set (Section 13);
  - seals them by publishing their SHA-256 hashes on the Notion page of blind test 3 before any test world exists.
- **World generator:** a separate Claude session, at its highest reasoning effort, with code execution. It is from the same model family as the procedure author; this is a declared limitation (Section 14), and Section 12 tells the generator how to counter it.
  - It reads ONLY this protocol and the Notion page of blind test 3.
  - It must NOT open `procedure/`, `dev/` or `results/`, anything in the folders of blind tests 1 and 2 or of LLM comparison 1, any other Notion page, or the Claude memory directory.
  - It writes `worlds/W-01.json` ... `worlds/W-27.json` (Part A), `data/D-01.json` ... `data/D-18.json` (Part B) and `key/key.json`.
  - It writes its own verification code `key/verify_key.py` and its output `key/verify_output.txt` BEFORE using the validator, and without reading the code in `scorer/`.
  - Then it runs `python scorer/validate_v3.py worlds data key/key.json` (running it is allowed) and repairs its files until the validator prints `VALID`.
  - It keeps `progress.txt` updated, so that progress is visible.
  - It computes SHA-256 of `key/key.json` with `python tools/hash_files.py key/key.json`. The hash is published on the Notion page, by the generator or by the project owner, before the procedure runs.
- The procedure author must not read `worlds/`, `data/` or `key/` before the SHA-256 of `results/outputs.json` is published. Running the frozen procedure on `worlds/` and `data/` is allowed. Nothing is debugged, repaired or changed after sealing.
- **Order:**
  1. Seal.
  2. Generate, verify and validate.
  3. Publish the key hash.
  4. Run the frozen procedure: `python procedure/procedure_v3.py run worlds data results/outputs.json`.
  5. Publish the outputs hash.
  6. Open the key and run the frozen scorer: `python scorer/score_v3.py worlds data key/key.json results/outputs.json results/report.json`.
  7. Publish the report verbatim, then a separate post-hoc audit.
- The scorer and the validator do not import the procedure. They recompute the reference answer with their own code and check every proof by elementary exact arithmetic.
- The worlds are not published, in the repository or elsewhere, until the project owner decides whether they will be shown to language models without the rules.

## 1. Claims under test
- **Part A (primary): the nebulium check.** Before inventing a new kind to fill a deficit, the kernel looks for a registered lurking relation of a known object whose coverage allows it to return where the deficit is. On unseen worlds the procedure must:
  - answer NO_DEFICIT when the new readings are within the observers' precision of the established explanation;
  - answer KNOWN, with the relation, its exact coefficient range and a quarantine note of what would overturn it, when exactly one registered relation suffices;
  - answer NEW when no registered relation suffices, with a true, checkable reason for excluding each one;
  - answer FORK, with a decisive set of possible observations, when two or three registered relations suffice and the possible observations can separate them.
  - Every answer carries machine-checkable proofs.
- **Part B (secondary): reopening.** The Part A verdicts are the kernel's file cabinet. When one new datum arrives (a reading, a new relation of a known object, or a corrected shared root), the procedure must reopen exactly the files that depend on it, recompute them correctly, and change no other file.
- **Not tested** (declared):
  - inferring return conditions or coverage factors (they are given);
  - relations that are not registered at all;
  - explanations that combine two or more registered relations;
  - more than one visible relation of uncertain strength in a world;
  - symmetry breaking, or symmetries valid only in part of a world;
  - incidental zeros (worlds have no parameters);
  - exponential and other non-rational fades;
  - uncertainty of inputs other than the observers' precision, and confirmation by an independent source;
  - locating which root is wrong when readings conflict;
  - "another law" answers, and "a new object of a known kind";
  - filling the law identity card; real data; real discovery; speed.

## 2. Part A world model
### 2.1 Quantities, constants, observers
- Each world has one **observable** (a quantity name). Worlds that use the same observable name describe the same phenomenon. They must share identical quantities, constants used, base law, visible relation, ledger, symmetries, observers and old observations, and may differ only in their new and possible observations.
- **Quantities:** name -> dimensions (map of rational exponents; `{}` is dimensionless). The **state quantities** are all quantities except the observable.
- **Constants:** name -> exact nonzero rational value and dimensions. A constant name denotes one shared root: it has the same value and dimensions in every world where it appears.
- **Observers:** name -> precision, an exact rational >= 0. An observer name denotes one instrument: it has the same precision in every world where it appears.

### 2.2 Base law and the visible relation
- **Base law:** `y = f`, where f is a rational expression in the state quantities and constants, with dim(f) = dim(y).
- **Visible relation** (optional, at most one per world): a term `h_V` with an unknown strength `mu`, contributing `mu*h_V(s)` at state s.
  - Its coefficient must have dimension dim(y) - dim(h_V), reachable by a product of rational powers of the declared constants (as for candidates, Section 2.8).
  - It has no coverage factor.
  - `M_old` is the set of `mu` that satisfy all old observations with every candidate at zero. Validity: `M_old` is nonempty, bounded, and does not contain 0 (the relation is really visible, and its strength is uncertain).
- The **established explanation** at state s is `E(s) = f(s) + mu*h_V(s)` (just `f(s)` without a visible relation).

### 2.3 Candidates (the ledger) and coverage factors
- Each **candidate** R has an id, an object name, a term `h_R` (a rational expression in state quantities and constants), a coefficient that is `"unknown"` or exact, and an optional coverage.
- R contributes `lam_R * h_R(s) * phi_R(s)`, where `phi_R` is its coverage factor (`phi_R = 1` without coverage).
- **Coefficient form:** `lam_R` is a dimensionless number times a product of rational powers of the declared constants. Its required dimension is dim(y) - dim(h_R).
- **Coverage** = a dimensionless **ratio** `rho_R(s)` (an expression in state quantities and constants) and a **factor**, one of:
  - **dimmer:** `phi_R(s) = g(rho_R(s))`, where g is a rational expression in the single variable `r`. Validity: 0 <= phi_R <= 1 at every listed state (old, new and possible observations).
  - **switch:** `phi_R(s) = 1` if `rho_R(s) < t` (for `"on": "<"`) or `rho_R(s) > t` (for `"on": ">"`), else 0, with t a positive rational. Validity: no listed state has `rho_R(s) = t`.
- A coverage may carry a `"summary"` (free text, such as "returns when the ratio is below 1"). It is a description only and is never used in any computation. The numbers decide.
- With every candidate at zero, the old observations hold (validity). So every candidate can be set to zero while another one is examined. The explanation of a deficit is ONE candidate.

### 2.4 Symmetries
- A symmetry is `{"name": ..., "map": {q: "c*q2", ...}}`: the observable, if listed, is sent to a nonzero rational multiple of itself, and each listed state quantity to a nonzero rational multiple of a state quantity; unlisted quantities are unchanged.
- Validity: it maps the established law `y = f + mu*h_V` to itself for every `mu`, and leaves every candidate's coverage ratio unchanged identically.
- A candidate R is **forbidden** by a symmetry if the map sends `y = f + mu*h_V + lam*h_R` to itself only when `lam = 0`. A declared symmetry holds everywhere in the world.

### 2.5 Observations
- `old_observations` (the old domain) and `new_observations` (the new domain): each is `{"state": {every state quantity: rational}, "value": rational, "observer": name}`. With d = the observer's precision, the true value of y at that state lies in [value - d, value + d].
- `possible_observations`: each is `{"state": ..., "observer": name}`. They are states where an observation could be made, with that observer's precision. They are used for quarantine notes, decisive sets and Part B readings.

### 2.6 Constraint systems
- An observation k at state s_k with reading v_k and precision d_k gives the two linear inequalities
  `v_k - d_k <= E(s_k) + (included contributions at s_k) <= v_k + d_k`
  in the unknowns: `mu` (if there is a visible relation) and `lam_R` (if R is included and its coefficient is unknown). Known parts move to the right-hand side.
- The systems for a candidate R:
  - **Z (step 0):** all old and new observations; no candidate.
  - **A_R (actual):** all old and new observations; R included with its actual factor; `lam_R` fixed if exact.
  - **C_R (uncovered):** as A_R, but `phi_R` is replaced by 1 at every new-observation state; old states keep the actual factor. Without coverage, C_R = A_R.
  - **S_R (shape):** the new observations with R included and `phi_R` replaced by 1 at the new states; the old observations WITHOUT R (they constrain `mu` only); `lam_R` free even when an exact value is given.
- A system is **feasible** if some values of its unknowns satisfy all its inequalities. A system without unknowns is feasible if every inequality holds.

### 2.7 Verdicts
1. **NO_DEFICIT** if Z is feasible (step 0). A residual within precision is never "explained" by a candidate.
2. Otherwise, R is **sufficient** if it is not TYPE-impossible, not SYMMETRY-forbidden, and A_R is feasible.
   - No sufficient candidate: **NEW**.
   - Exactly one: **KNOWN(R)**. A new kind fitted to the deficit could also fit; by conservatism the known relation is chosen, and the quarantine note records what would overturn it.
   - Two or three: **FORK** with those branches. Validity requires every pair of branches to be decisively separable (Section 2.9). A world with more than three sufficient candidates is invalid.

### 2.8 Exclusion reasons
For every candidate that is not sufficient, ALL applicable reasons are listed:
- **TYPE:** no product of rational powers of the declared constants has the dimension dim(y) - dim(h_R). This is the test-2 "constants" check; coverage factors are dimensionless.
- **SYMMETRY:** R is forbidden by a declared symmetry (Section 2.4).
- **SCOPE:** R has coverage, A_R is infeasible, and C_R is feasible. "It would suffice if it were uncovered in the new domain."
- **SHAPE:** S_R is infeasible. "Even uncovered, no strength of R fits the new observations."
- **BOUND:** S_R is feasible and C_R is infeasible. "Some strength would fit, but what is known about the strength (its exact value, or the old observations) excludes every such strength, even uncovered."
- When A_R is infeasible, at least one of SCOPE, SHAPE and BOUND applies. BOUND excludes both SCOPE and SHAPE; SCOPE and SHAPE can co-occur only through a visible relation. TYPE and SYMMETRY can co-occur with anything, including a candidate whose A_R is feasible.
- A verdict's proof needs at least one listed reason for every non-sufficient candidate, and every listed reason must be true. Whether the list is complete is measured separately as "analysis accuracy" (Section 7.3).

### 2.9 Predicted ranges, quarantine notes, decisive sets
- For a feasible system X and a state s, the **predicted range** `P_X(s)` is the exact interval [min, max] of the predicted value of y at s over the feasible set of X. The predicted value uses the established explanation and the included contributions with their ACTUAL factors at s.
- **Quarantine note** of KNOWN(R): `P_{A_R}(s)` at every possible observation, in order. A reading v with precision d at s overturns the explanation if [v - d, v + d] does not meet `P_{A_R}(s)`.
- **Base note** of NO_DEFICIT: `P_Z(s)` at every possible observation.
- **FORK:** the ranges `P_{A_R}(s)` for every branch R at every possible observation, and a **decisive set**: a list of possible-observation indices such that every pair of branches R, R' has an s in the list with gap(`P_R(s)`, `P_R'(s)`) > 2*d(s), where gap(I, J) = max(lo_J - hi_I, lo_I - hi_J). Then any reading at s is inconsistent with at least one of the two branches, whichever is true.
- **Decisively separable pair:** some possible observation satisfies that gap condition.

## 3. Part A world format, budgets and validity
```
{"id": "W-00", "experiment": "A",
 "observable": "yy",
 "quantities": {"yy": {"M": 1, "T": -2}, "aa": {"L": -3}, "bb": {}},
 "constants": {"kc": {"value": "250", "dims": {"L": -3}},
               "ku": {"value": "3", "dims": {"M": 1, "T": -2}}},
 "observers": {"lab1": "1/100", "far1": "1/20"},
 "base_law": "yy = ku*bb",
 "visible": null,
 "ledger": [
   {"id": "R1", "object": "ob1", "term": "ku*bb", "coefficient": "unknown",
    "coverage": {"ratio": "aa/kc", "factor": {"type": "dimmer", "expr": "1/(1+r)"},
                 "summary": "fades when aa exceeds kc"}},
   {"id": "R2", "object": "ob2", "term": "ku*bb**2", "coefficient": {"exact": "1/2"},
    "coverage": {"ratio": "aa/kc", "factor": {"type": "switch", "on": "<", "threshold": "1"}}},
   {"id": "R3", "object": "ob2", "term": "ku*bb**3", "coefficient": "unknown", "coverage": null}],
 "symmetries": [],
 "old_observations": [{"state": {"aa": "250000", "bb": "1"}, "value": "3", "observer": "lab1"}],
 "new_observations": [{"state": {"aa": "5/2", "bb": "1"}, "value": "8", "observer": "far1"}],
 "possible_observations": [{"state": {"aa": "250000", "bb": "2"}, "observer": "lab1"},
                           {"state": {"aa": "5/2", "bb": "2"}, "observer": "far1"}]}
```
- A visible relation is written `"visible": {"id": "V1", "object": "ob0", "term": "<expression>"}`.
- **Budgets:**
  - the observable plus 1 to 4 state quantities; 0 to 4 constants; 1 to 3 observers;
  - 2 to 5 candidates; at most 1 visible relation; 0 to 2 symmetries;
  - 1 to 6 old observations, 1 to 4 new observations, 2 to 6 possible observations.
- **Expressions:** only +, -, *, / and integer powers from -3 to 3. Rational numbers are written exactly (`1/2`, never `0.5`). Every given rational has a numerator and denominator of absolute value at most 10^9.
- **Names:** 2 to 6 characters, lowercase ASCII letters and digits, starting with a letter. They must be neutral: no physical meaning, no hint of the answer. Reserved and forbidden: `re im ln pi oo li lam mu nan zoo sin cos tan cot sec csc exp log abs max min sqrt sign floor root beta gamma zeta erf`. All names in one world are distinct (an object may own several candidates). Candidate ids are `R1`, `R2`, ...; the visible relation id is `V1`.
- **Validity** (a world that fails any rule is invalid and is excluded from scoring):
  - W1: format, budgets and names; every name used in an expression is declared; ids are unique.
  - W2: every expression evaluates to an exact rational at every listed state (no division by zero). dim(f) = dim(y); every ratio is dimensionless; dimmer values lie in [0, 1]; no listed state sits on a switch threshold.
  - W3: the visible relation, if any, is not TYPE-impossible, and `M_old` is nonempty, bounded and excludes 0.
  - W4: the old observations hold with every candidate at zero for some `mu`. Readings at identical states have overlapping intervals.
  - W5: symmetries obey Section 2.4.
  - W6: at least 2 candidates, at least one of which is not TYPE-impossible and is not in the answer (not the KNOWN relation, not a branch): a distractor with the right dimensions.
  - W7: at most 3 sufficient candidates. For FORK, every pair is decisively separable. The feasible set of A_R for every sufficient R, and of Z for NO_DEFICIT, is bounded.
  - W8: in a NEW world no combination of candidates explains the observations: the joint system with every candidate that is neither TYPE-impossible nor SYMMETRY-forbidden (actual factors; exact coefficients fixed; unknown ones free) and `mu` is infeasible.
  - W9: shared names are consistent across worlds (Section 2.1).
  - W10: the world does not reproduce a dev world or the format example (Section 13).

## 4. Part A outputs and proofs
`results/outputs.json` is `{"A": {world_id: {method: output}}, "B": {item_id: {method: output}}}`. The procedure's output for a world is:
```
{"verdict": "NO_DEFICIT | KNOWN | NEW | FORK",
 "relation": "R2",                       (KNOWN)
 "branches": ["R1", "R3"],               (FORK, sorted)
 "step0": {"deficit": true, "certificate": <farkas Z>} | {"deficit": false, "certificate": <point Z>},
 "explanations": {"R2": {"point": <point A_R2>,
                         "intervals": {"lam": [lo, hi] | null, "mu": [lo, hi] | null},
                         "ranges": [[lo, hi], ...]}},   (KNOWN: the relation; FORK: every branch;
                                                         NO_DEFICIT: key "BASE" with system Z)
 "decisive": [0, 2],                     (FORK)
 "excluded": {"R1": {"reasons": ["SCOPE"],
                     "certificates": {"SCOPE": {"A": <farkas>, "C": <point>}}}},
 "depends_on": {"observable": "yy", "examined": ["R1", "R2", "R3"],
                "constants": ["kc", "ku"], "observers": ["far1", "lab1"]}}
```
- **The inequalities** of a system, in the form used by every certificate: for observation k of the domain `old` or `new` (k counts from 0 in that list; a reading appended in Part B gets the next index), let `K` be the known part of the predicted value at its state (f, the fixed visible part, and every contribution with a fixed coefficient) and `a` the coefficients of the unknowns. Then `"upper"` is `a.x <= v + d - K` and `"lower"` is `-a.x <= -(v - d - K)`.
- **point:** values of the system's unknowns, e.g. `{"mu": "3/2", "lam": "5"}` (only the unknowns present). The scorer checks every inequality of the system exactly.
- **farkas:** a list of `{"obs": "old" | "new", "k": index, "side": "upper" | "lower", "y": positive rational}`. The scorer combines the referenced inequalities of the named system with these multipliers and requires the coefficient of every unknown to be 0 and the right-hand side to be negative. For a system without unknowns this is a single violated inequality.
- The numbers in outputs and certificates are exact rationals of any size; the 10^9 budget of Section 3 applies to world data only.
- **Certificates per reason:** SCOPE: `{"A": farkas(A_R), "C": point(C_R)}`. SHAPE: `{"S": farkas(S_R)}`. BOUND: `{"S": point(S_R), "C": farkas(C_R)}`. TYPE and SYMMETRY need no certificate: the scorer recomputes them.
- **intervals:** the exact range of each unknown over the feasible set; `null` when the unknown is absent. **ranges:** `P(s)` at every possible observation, in order.
- **Baselines:** `{"verdict": ..., "relation": ..., "branches": ...}` only.
- All numbers are exact rational strings.

## 5. Part A key format
`key/key.json` is `{"A": [...], "B": [...]}`. A Part A entry:
```
{"id": "W-01", "verdict": "KNOWN", "relation": "R2", "branches": null,
 "reasons": {"R1": ["SCOPE"], "R3": ["BOUND"]},
 "hidden_truth": {"terms": [{"candidate": "R2", "coefficient": "..."}, {"expr": "...", "coefficient": "..."}],
                  "visible_coefficient": "..."},
 "category": "free text", "notes": "free text"}
```
- `verdict`, and `relation` (KNOWN) or `branches` (FORK), are required. They must equal the scorer's reference answer; otherwise the world is excluded.
- `reasons` is optional; if given, each list must equal the reference set, otherwise the world is excluded.
- `hidden_truth` is optional and informational: the model the generator used to make the readings. A term is a ledger candidate (with its own coverage factor) or an unregistered expression in state quantities and constants. The scorer reports whether every reading lies within precision of it; this is never scored.

## 6. Part A composition (27 worlds)
All counts are computed by the validator and the scorer from the reference answers.
- KNOWN 9, NEW 9, FORK 6, NO_DEFICIT 3.
- **Scope-sensitive** worlds (the NO_SCOPE baseline's answer differs from the reference): at least 8 in all, including:
  - at least 5 KNOWN worlds of the **nebulium type** (the answer relation has coverage and the world is scope-sensitive), of which at least 3 have a dimmer and at least 2 a switch;
  - at least 2 NEW worlds;
  - at least 1 FORK world.
- **Sole reasons:** each of TYPE, SYMMETRY, SCOPE, SHAPE and BOUND is the only reason for at least one candidate in some NEW world.
- **Visible relation that matters:** at least 3 worlds whose reference answer changes when `mu` is fixed at the midpoint of `M_old`.
- At least 1 FORK with three branches.
- At least 1 NO_DEFICIT world with a **planet-X trap**: a candidate that is neither TYPE-impossible nor SYMMETRY-forbidden and whose A_R is feasible, so it could "explain" the sub-precision residual.
- **Support for Part B:** the observables, constants and observers must be shared enough to allow the Part B composition (Section 10.1). In particular, some observable must be shared by at least three worlds, one of them NO_DEFICIT.
- **Diversity:** vary dimensions, term forms (monomials, sums, ratios), coverage ratios built from different quantities, and the position of the answer in the ledger. Worlds that share an observable must have different new observations.

## 7. Part A baselines, correctness, metrics, criteria
### 7.1 Baselines (all share step 0)
- **ALWAYS_NEW:** every deficit -> NEW.
- **DIMS_ONLY:** deficit -> KNOWN(the first candidate in ledger order that is not TYPE-impossible); NEW if there is none. It never forks.
- **NO_SCOPE:** the procedure with every coverage factor set to 1 everywhere, old and new. It can fork.

### 7.2 Correctness
- **The procedure** is correct on a world when the verdict equals the reference, every proof checks, and:
  - NO_DEFICIT: a valid point of Z, and the base note equals the reference.
  - KNOWN: the same relation; the step-0 certificate is valid; the point of A_R is valid; the intervals and the quarantine note equal the reference exactly; every other candidate has at least one listed reason, and every listed reason is true with valid certificates.
  - NEW: the step-0 certificate is valid; every candidate has at least one listed reason, every listed reason true and certified.
  - FORK: the same branch set; the step-0 certificate is valid; every branch's point, intervals and ranges are valid and exact; the decisive set is valid; every non-branch candidate has valid reasons.
- **Baselines** are correct when the verdict and the relation or branch set equal the reference. They produce no proofs.

### 7.3 Metrics
- accuracy;
- **false novelty:** NEW answers on KNOWN and FORK worlds, over the number of those worlds (15);
- **false familiarity:** KNOWN or FORK answers on NEW worlds, over the number of NEW worlds (9). This is an objective error: claiming that registered relations suffice when the givens exclude them. False novelty is an error relative to conservatism. The two are reported separately;
- **fork accuracy:** FORK worlds answered correctly (Section 7.2), over 6;
- over-fork: FORK answers on KNOWN worlds (reported);
- quarantine notes valid among the procedure's KNOWN answers (part of correctness; also reported);
- **analysis accuracy** (diagnostic, no threshold): for each reason type, the share of applicable (candidate, reason) pairs that the procedure listed, and the share of listed pairs that are true, with the list of every miss. It shows whether a shortfall lies in information or in reasoning.

### 7.4 Criteria (fractions of the valid worlds in each class)
- A1: accuracy >= 0.70.
- A2: false novelty <= 0.15.
- A3: false familiarity <= 0.15.
- A4: fork accuracy >= 0.70.
- A5: accuracy minus the best baseline's accuracy >= 0.15, AND one-sided exact McNemar p < 0.05 against that baseline.
  - b = worlds where the procedure is correct and the baseline is not; c = the reverse; p = P(X >= b) for X ~ Binomial(b + c, 1/2).
  - The best baseline has the highest accuracy; ties go to the one giving the larger p.
- Without the composition guarantee of Section 6, A5 could fail by construction. The comparison is partly definitional: NO_SCOPE fails scope-sensitive worlds by definition, and ALWAYS_NEW and DIMS_ONLY cannot fork.

### 7.5 Outcome
- VOID if more than 20% of the 27 worlds are excluded (6 or more).
- PASS if A1-A5 all hold.
- FAIL otherwise.

## 8. Part B: reopening
### 8.1 The cabinet
- The cabinet is the 27 Part A worlds with one verdict file each: the procedure's own Part A output for the procedure, and the reference answer for the reference.
- Each Part B item is applied ALONE to the cabinet as it is after Part A. Items do not accumulate.

### 8.2 Items
- **observation:** a new reading for one world: a state equal to one of that world's possible-observation states, its observer, and a value.
- **relation:** a new candidate for an observable. Its object must already appear in some world's ledger; its id must be new in that observable's ledger. The observable may be one that no world uses (then it carries its dimensions).
- **root:** a corrected value of one shared constant, or a corrected precision of one observer. The constant or observer must appear in at least one world.

### 8.3 Reopening rules
- **R1, observation:** only the file of that world can be reopened.
  - A NEW file is never reopened by a reading: a reading adds a constraint, and a constraint cannot make an excluded candidate sufficient.
  - A KNOWN or NO_DEFICIT file is reopened if the reading interval misses its recorded range at that state (quarantine note or base note).
  - A FORK file is reopened if the reading interval misses the range of at least one branch at that state.
  - For R1, reopening happens exactly when the verdict changes.
- **R2, relation:** reopen every file of a world with that observable whose verdict is not NO_DEFICIT. Step 0 examined no candidate in a NO_DEFICIT file, so a new candidate cannot change it.
- **R3, root:** reopen every file that used the root.
  - A constant is used if it appears in the base law or the visible relation, or, for a verdict other than NO_DEFICIT, in any candidate's term or coverage ratio.
  - An observer is used if any old or new observation of the world comes from it, or, for a FORK verdict, any possible observation (decisive sets depend on precision).
- **Recomputation:** a reopened file is recomputed with the datum applied: the reading is appended to the world's new observations; the candidate is appended to the ledger of every world with that observable; the root's value is replaced in every world. Files that are not reopened keep their verdicts.
- Under R2 and R3 a file can be reopened and keep its verdict. Reopening is not the same as changing.

## 9. Part B formats
```
{"id": "D-01", "experiment": "B", "type": "observation",
 "world": "W-05", "state": {"aa": "5/2", "bb": "2"}, "observer": "far1", "value": "17/2"}

{"id": "D-02", "experiment": "B", "type": "relation", "observable": "yy",
 "relation": {"id": "R4", "object": "ob2", "term": "ku*bb", "coefficient": "unknown", "coverage": null}}
 (for an observable no world uses, add "observable_dims": {...})

{"id": "D-03", "experiment": "B", "type": "root", "constant": "kc", "new_value": "300"}
{"id": "D-04", "experiment": "B", "type": "root", "observer": "lab1", "new_precision": "1/10"}
```
- **Procedure output** per item: `{"reopened": [sorted world ids], "verdicts": {world_id: <full Part A output>}}`, with verdicts only for the reopened files.
- **Baselines:** REOPEN_NONE `{"reopened": []}`; REOPEN_ALL `{"reopened": <all 27>, "verdicts": {...}}`, recomputed with the procedure's own rules (scored on verdict and relation or branches only).
- **Key entry:** `{"id": "D-01", "type": "<category, Section 10.1>", "reopened": [...], "final": {world_id: {"verdict": ..., "relation": ..., "branches": ...}}}`, with the final verdicts of the reopened files. They must equal the reference; otherwise the item is excluded.

## 10. Part B composition, validity, correctness, criteria
### 10.1 Composition (18 items)
Each item declares its category; the validator checks it against the reference outcome.
- **observation (6):**
  - `obs_flip` (2): the reading misses the note of a KNOWN or NO_DEFICIT file (at least 1 KNOWN);
  - `obs_inside` (2): nothing is reopened, because the reading meets the recorded range or the file is NEW (at least 1 on a KNOWN file);
  - `obs_fork` (2): the reading excludes at least one branch of a FORK file.
- **relation (8):**
  - `rel_new_known` (2): a NEW file becomes KNOWN with the new candidate;
  - `rel_known_fork` (2): a KNOWN file becomes a FORK that includes the new candidate;
  - `rel_unchanged` (2): files are reopened and no verdict changes;
  - `rel_none` (2): nothing is reopened.
- **root (4):**
  - `root_vanish` (1): a deficit vanishes, so some file becomes NO_DEFICIT;
  - `root_revive` (1): an excluded candidate becomes sufficient in some file;
  - `root_unchanged` (1): files are reopened and no verdict changes;
  - `root_none` (1): the root appears in some world but no file used it.
- Also required:
  - at least 2 relation items whose reference list has 2 or more files;
  - at least 1 relation item whose observable has a NO_DEFICIT file (which must not be reopened);
  - at least 1 root item whose reference list has 2 or more files.

### 10.2 Validity of an item
- Its format and category are valid.
- An observation is at a listed possible state with that observation's observer, and does not conflict with an existing reading at the same state.
- A relation obeys W1 and W2.
- A root exists in some world, and a new precision is >= 0.
- After the datum is applied, every world the datum changes still satisfies W1-W9.
- No file outside the reference list changes its verdict (the rules R1-R3 are sound for the item).
- The key's list and final verdicts equal the reference.
- An item that fails any of these is excluded.

### 10.3 Correctness, metrics and criteria
- **List exact:** the procedure's reopened set equals the reference set.
- **Verdicts correct:** every file in the reference list has the reference final verdict. For a file the procedure reopened, its new verdict is proof-checked as in Section 7.2. For a file it did not reopen, its stale Part A verdict is compared.
- **Silent change:** a file outside the reference list whose verdict the procedure changed, or a verdict reported for a file outside the procedure's own list.
- **Metrics:** list exactness; micro precision and recall of reopened files; verdict correctness. Baselines are reported too. Items whose failure traces to a wrong Part A verdict of a touched file are reported separately.
- **Criteria** (fractions of valid items):
  - B1: list exact >= 8/9.
  - B2: verdicts correct >= 8/9.
  - B3: zero silent changes.
- **Outcome:** VOID if 4 or more of the 18 items are excluded; PASS if B1-B3 all hold; FAIL otherwise.

## 11. Pre-registered interpretation
- **Part A PASS** is evidence that on unseen formal worlds the nebulium-check rule can be computed correctly with machine-checkable proofs:
  - decide KNOWN when a registered relation's coverage factor and old-observation bounds allow it;
  - decide NEW when every registered relation is excluded for a true, stated reason;
  - fork with decisive observations when two or three relations suffice;
  - refuse to explain residuals within precision.
  - Coverage reasoning changes the answers where it should (against NO_SCOPE).
- **Part A FAIL** returns the rule or its implementation to design. **VOID** means a rerun with new worlds.
- **Part B PASS** is evidence that the record of each verdict states exactly which ledger, state and roots it depends on, and that reopening exactly those files and recomputing them gives the right verdicts. It is a protection claim (the independence test of condition 2 in question 2 measures roots), not an efficiency claim.
- **Analysis accuracy** is diagnostic only.
- **Not evidence of:**
  - conservatism being the best policy;
  - superiority over language models (they were shown to apply given rules equally well in LLM comparison 1);
  - inferring coverage or return conditions;
  - real data or real discovery.

## 12. Generator brief
- **Bias.** You are from the same model family as the author of the procedure, so shared habits could make the worlds accidentally easy for it. Counter this deliberately:
  - prefer unfamiliar term forms, dimensions and numbers;
  - do not model worlds on the examples in this protocol;
  - vary the position of the answer in the ledger and the order of observations;
  - place readings near decision boundaries (never on them);
  - make distractors genuinely tempting, with the right dimensions and a plausible size.
- **Never** read the procedure, the dev set or anything listed in Section 0.
- **Method:**
  - Use code and exact fractions.
  - Write `key/verify_key.py` from this protocol alone and run it first.
  - Then run the sealed validator, and repair until it prints VALID.
  - Keep `progress.txt` updated.
- **Do not** add constraints that make the test easier than this protocol requires. If a requirement cannot be met, or the protocol is ambiguous, stop and write the problem in `key/generator_notes.md` for the project owner. Do not resolve it silently.
- **Names** are neutral and must not reveal any answer.

## 13. Dev set (used during development; excluded from the test)
The format example of Section 3, and these worlds and items:
- **Part A:**
  - nebulium toys: a line covered by density at the old states and back at low density, once with a dimmer and once with a switch;
  - a helium toy (the only plausible candidate is excluded by BOUND);
  - a coronium toy (coverage by a temperature ratio);
  - a two-branch fork toy;
  - a step-0 toy, and a planet-X trap toy;
  - a visible-relation toy (the answer depends on `mu`);
  - one toy each with TYPE, SYMMETRY, SHAPE and SCOPE as the sole reason;
  - a planet-X world (NEW until a constant is corrected).
- **Part B:**
  - a Bowen toy (a new relation turns NEW into KNOWN);
  - a fall toy (a reading overturns a KNOWN file), and a reading inside a quarantine note;
  - a fork-decision toy;
  - a toy where a new relation turns KNOWN into FORK;
  - a planet-X toy (a corrected constant makes a deficit vanish);
  - a precision toy (a corrected observer revives candidates);
  - a toy where a NO_DEFICIT file sharing the observable is not reopened;
  - a relation for an unused observable, and a root that no file used.
- The validator rejects a world whose base law and candidate terms reproduce a dev world (it holds only their SHA-256 fingerprints).
- **Regression check (not evidence):** the BOUNDED, ACTIVE, UNCONSTRAINED and CONFLICT worlds of blind test 2, Part B, converted to this format, must give the same coefficient intervals.

## 14. Known limitations (declared before the test)
- The generator and the procedure author are models of the same family.
- The scorer and the procedure are independent code by the same author.
- "Correct" is defined by our rules: the test shows that the rules are computable with proofs, not that they are the best policy. Conservatism is a design choice.
- Only registered relations can be found, and coverage factors are given, not inferred.
- Explanations are single relations.
- At most one visible relation of uncertain strength per world.
- Symmetries hold everywhere.
- No incidental zeros; no exponential fades.
- Step 0 covers observer precision only.
- Conflicting readings and the search for a wrong root are not tested.
- The comparison with baselines is partly definitional (Section 7.4). DIMS_ONLY depends on a ledger order chosen by the generator; its ceiling is 12 of 27.
- Part B errors can propagate from Part A verdicts; they are reported separately.
- The worlds are formal and few: the 95% lower confidence bound for 27/27 is about 87%, and for 18/18 about 81%.

## 15. Hashes (SHA-256)
- `procedure/procedure_v3.py`, `scorer/ref_v3.py`, `scorer/score_v3.py`, `scorer/validate_v3.py`, `tools/hash_files.py` and this protocol are published on the Notion page when sealed (a file cannot contain its own hash).
- `key/key.json`: published before the procedure runs.
- `results/outputs.json`: published by the procedure author before the key is opened.
