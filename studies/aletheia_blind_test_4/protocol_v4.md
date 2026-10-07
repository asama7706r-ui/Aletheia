# Aletheia blind test 4 - pre-registered protocol v4 (SEALED)

Status: SEALED on 2026-10-07 by the procedure author (Claude), after the project owner reviewed and approved every item (Notion review page «مسودة بروتوكول التجربة 4: ما يحتاج مراجعتك», sections 1-5). The SHA-256 hashes of this protocol, of the registry and of the sealed code are in `SEALED_HASHES.txt` and on the Notion page «التجربة العمياء 4: السجل وبطاقة الهوية». Environment: Python 3.12.10, sympy 1.14.0.
Sources: the Notion page "مسودة مواصفة التجربة 4: السجل وبطاقة الهوية" (decisions in its section 12), its child page "مسودة سجل التجربة 4" (decisions R1-R6), and the description language v0.4 (`lang/SPEC_v0.4.md`). Section 15 lists the choices made while writing this protocol; the project owner approved all of them.

## 0. Roles, order and rules
- **Procedure author** (Claude): writes this protocol, `procedure/procedure_v4.py`, `scorer/ref_v4.py`, `scorer/score_v4.py`, `scorer/validate_v4.py` and `tools/hash_files.py`, develops them ONLY on the dev set (Section 12), and seals them before any test world exists.
- **Sealed inputs:**
  - `registry/registry.json`: the registry, in language v0.4;
  - `registry/registry_notes.md`: what each id means; the procedure never reads it;
  - `registry/check_cards.py`: the check of the cards against laws of known symmetry;
  - `lang/SPEC_v0.4.md` and `lang/reader_v0.py`: the language and its strict reader.
- **Before sealing,** the scorer and the validator are tested by deliberate corruption: for every kind of wrong output and every validity rule, a corrupted copy must be caught (lesson of test 2).
- **World generator:** a separate Claude session, at its highest reasoning effort, with code execution. It belongs to the same model family as the procedure author. This is a declared limitation (Section 13), and Section 11 tells the generator how to counter it.
  - It reads ONLY this protocol, the files in `registry/` and `lang/`, and the Notion page of blind test 4.
  - It must NOT open `procedure/`, `dev/` or `results/`, the folders of earlier tests and comparisons, the folder `language_v0/`, any other Notion page, or the Claude memory directory. It never reads the code in `scorer/`; it only runs the validator.
  - It writes `worlds/W-01.json` ... `worlds/W-30.json` and `key/key.json`.
  - It writes its own verification code `key/verify_key.py` and its output `key/verify_output.txt` BEFORE using the validator, from this protocol alone.
  - Then it runs `python scorer/validate_v4.py worlds key/key.json` and repairs its files until the validator prints `VALID`.
  - If it believes a registry card is physically wrong, it reports this in `key/generator_notes.md` and does not change the registry.
  - It keeps `progress.txt` updated, and computes SHA-256 of `key/key.json` with `python tools/hash_files.py key/key.json`.
- The procedure author must not read `worlds/` or `key/` before the SHA-256 of `results/outputs.json` is published. Running the frozen procedure on `worlds/` is allowed. Nothing is debugged, repaired or changed after sealing.
- **Order:**
  1. Seal.
  2. Generate, verify, validate.
  3. Publish the key hash.
  4. Run `python procedure/procedure_v4.py run worlds results/outputs.json`.
  5. Publish the outputs hash.
  6. Open the key and run `python scorer/score_v4.py worlds key/key.json results/outputs.json results/report.json`.
  7. Publish the report verbatim, then a separate audit.
- The scorer and the validator do not import the procedure. They recompute every reference answer with their own code (`scorer/ref_v4.py`) and check every proof by exact arithmetic.
- The worlds stay unpublished until the project owner decides whether they will ever be shown to language models (a later, separate question). The generator's model family is never scored in any comparison on these worlds.

## 1. Claim under test
- **One claim:** on unseen worlds written in the description language against a registry sealed before them, the procedure fills the identity card of every filler by itself, with machine-checkable proofs, and labels the filler correctly. The card has three items:
  - **F1, dimensions:** the filled law is dimensionally consistent, and the unknown dimensions of a new quantity are inferred as a prediction.
  - **F2, symmetry:** for every transformation of the catalog, whether the law is unchanged before and after the filler. Each quantity's action comes from the registry (its kind, its meaning card) or from the bodies, and never from the law under test.
  - **F3, old observations:** the filled law, with the new quantities as the filler describes them, still reproduces the observations on which the law was accepted.
- **The label** is SAME_LAW_NEW_STATE, ANOTHER_LAW, INVALID, or CONDITIONAL. A CONDITIONAL label comes with branches on unknown actions and a decisive observation.
- **And without:** silent substitution; frequent false alarms; and, in worlds with several fillers, a silent choice among fillers that keep the law's identity.
- **Not tested** (declared):
  - F4 (conditions) and F5 (state and scope);
  - step 0 and the nebulium check (test 3); every world here has a real deficit;
  - building a new kind or a new transformation;
  - affine transformations (Galilean boosts, translations), and the similarity scaling (blueprint 7.3, item 6);
  - fillers that edit several laws, or a new thing whose effect changes from one old observation to another, like Neptune moving in its orbit (it needs a law of its own; gap G7);
  - two fillers that are one law written twice (apparent multiplicity, question 4);
  - unknown old values (`"?"`), unknown owners, unknown actions of multi-component quantities, and products of transformations as separate items of the card (but see V13);
  - language-model comparisons, real data, real discovery, speed.

## 2. What the procedure computes
### 2.1 Inputs
- **The sealed registry:** kinds, five transformations (catalog version 1), instruments, meaning cards, definitions, body types.
  - `rev_t` (time reversal), `refl_x` (reflection x -> -x) and `conj_c` (charge conjugation) read the meaning.
  - `rot_z` (a quarter turn about z) reads the kind.
  - `exch` (exchange of two bodies of the same type) reads the cast.
- **A world:** a v0.4 world file accepted by `lang/reader_v0.py` with the sealed registry, and obeying Section 3.
- **In a world:** one **law** `y = f` (`y` a single name), its fillers `y = f_k`, the bodies, quantities, observers and observations.

### 2.2 Actions
For a transformation T and a name in the law or a filler, the action is read from the registry and the world, never from the law under test (blueprint 5.5):
- **T reads the meaning:** the meaning card's entry for T. It is one of:
  - a fraction, which multiplies every component;
  - an n x n matrix on the n components;
  - `"?"`, unknown;
  - `{"derived": d}`, computed from the definition d: a product or quotient multiplies or divides the actions, an integer power raises the action to that power, `D(a, b)` gives action(a) / action(b), and numbers act as 1.
  - A new quantity uses its own `under[T]`. When its meaning is known, this equals the card (the v0.3 rule). When its meaning is `"?"`, it may be `"?"`.
- **T reads the kind:** the kind's entry for T. A new quantity of kind `"?"` is written as one name, so it counts as one number with an unknown action.
- **T reads the cast:** one transformation `exch(b1, b2)` for each pair of distinct world bodies of the same body type. It swaps every quantity owned by b1 with the quantity of the same meaning owned by b2, component by component. Validity V7 guarantees this partner exists, for world and new quantities alike. Quantities owned by other bodies, by new bodies or by `"world"` are unchanged.
- **Unknown actions are signs.** Applied twice, `rev_t`, `refl_x` and `conj_c` give the identity, and so does `rot_z` applied four times. The action of a single number is then a rational a with a^2 = 1 or a^4 = 1, so a = +1 or a = -1. Each unknown is therefore a sign s, named `q:T` (the quantity id and the transformation). This follows from the transformations; it is not a choice that saves the card.
- **Image of a name:** a single-number name q with action a goes to a*q. The components (c_1, ..., c_n) of a quantity with matrix M go to M (c_1, ..., c_n).

### 2.3 Invariance of one equation
- For one assignment of the unknown signs, an equation `y = f` is **unchanged** under T if T maps its solutions to solutions. Concretely: replace every name by its image, then replace y by f. The difference image(y) - image(f) must then be identically zero, as a rational function of the remaining names.
- Otherwise the equation is **changed**. A **witness point** proves it: values of the remaining names at which that difference is defined and not zero. Names that appear only in the image, such as the y component that `rot_z` makes of an x component, are free.
- When y keeps its name (image(y) = c*y), this is the criterion of `registry/check_cards.py`: the same equation up to a nonzero constant factor. This form also covers a name that turns into another name, under `rot_z` or `exch`.

### 2.4 F2: the symmetry item
- **The catalog of a world:** `rev_t`, `refl_x`, `conj_c`, `rot_z`, and `exch(b1, b2)` for every pair of world bodies of the same type. A filler's new bodies have no "before", so they enter no exchange (they belong to F5, not tested).
- **For a filler and a transformation T,** let U be the unknown signs of the names that appear in the law or in the filled law under T. For every assignment of U:
  - `old`: whether the law is unchanged;
  - `new`: whether the filled law is unchanged;
  - **changed:** whether `old` differs from `new`. Both directions count: a lost and a gained symmetry are both changes.
- **The status of T:**
  - `no_change` if changed is false for every assignment;
  - `changed` if changed is true for every assignment;
  - otherwise `conditional`. The **keeping assignments** are those where changed is false.
- An unknown **matters** for T if flipping its sign alone changes the value of changed for some assignment.
- The procedure never picks an assignment (blueprint 5.5).

### 2.5 F1: the dimensions item
- **Dimensions of a name:**
  - a world quantity: its `dims`;
  - a new quantity: its `dims` if given; otherwise its meaning's dimensions (the anchor instrument's unit, or the dimensions derived through the definitions); if there are none, an unknown vector of rational exponents.
- **Rules:** a product adds dimensions, a quotient subtracts them, an integer power multiplies them, and numbers are dimensionless. Every sum or difference requires equal dimensions of its operands, and the two sides of the equation must have equal dimensions. These are linear equations in the unknown exponents.
- **F1 status:** `consistent` if they have a solution, else `inconsistent`. A new quantity whose written `dims` differ from its meaning's dimensions makes the filler inconsistent.
- **Inferred dimensions:** for each new quantity whose dimensions were unknown, the unique solution, or `undetermined`.

### 2.6 F3: the old-observations item
- **Old and new:** an observation is old if its `epoch` is at most the law's `accepted_at`, and new otherwise. All observations in a world are of the law's left side y.
- **What the new quantities are at each observation** (the filler describes the new thing; its effect is computed at the old observations, never tuned there):
  - at an old observation, a new quantity takes its `old_value`; with `old_value: "same"`, it takes its own unknown constant value;
  - at a new observation, a constant (`value: "?"`) takes its unknown constant value, the same at every observation;
  - at a new observation, a variable (`value: "var"`) takes a separate free value, named `q@k` (k is the index of the observation in the new list).
- **The unknowns** x are these values, one per component. Validity V5 makes every filled law affine in them.
- **The inequalities** use the form of test 3. For observation k of the `old` or `new` list (k counts from 0, in file order), let v be its value, d its observer's precision, K the known part of f_k at its state, and a the coefficients of the unknowns. Then:
  - `"upper"` is `a.x <= v + d - K`;
  - `"lower"` is `-a.x <= -(v - d - K)`.
- **F3 status:** `holds` if the system of all old and new inequalities is feasible, `fails` otherwise.
  - Every filler fits the new observations alone (validity V8). So a failure means the description of the new thing, applied at the old observations together with what the deficit requires, contradicts them.
  - The project owner's three outcomes (test-4 draft, 4.3) all fall under this one computation. If the effect at the old observations is zero (absent, covered, or orthogonal to the law), or stays and the law holds, F3 holds. If it stays and breaks the law, F3 fails. The reason for a zero effect is not scored in this test.
- The law itself satisfies all old observations (validity V8).
- **The zero-effect report** (reported, never scored; approved 2026-10-06). For each filler and each old observation, the effect there is E = f_k - f at its state, with the new quantities taking their old-observation values. Each old observation gets one label:
  - `absent`: f_k with every fraction `old_value` substituted is identically f, whatever the state and the `"same"` constants;
  - `zero_for_any_value`: not absent, but E is zero at that state for every value of the unknowns;
  - `below_precision`: F3 holds, and |E| is at most the observer's precision at every point of the F3 feasible set;
  - `visible`: F3 holds, and none of the above applies;
  - `n/a`: neither of the first two applies, and F3 fails.
  These labels prepare the ledger test (a witness or not) and the scope test (where the effect will appear). The project owner's "orthogonal to the law" needs the scope of an observation, which v0.4 cannot write.

### 2.7 The verdict (blueprint 5.7, with INVALID first)
1. **INVALID** if F1 is inconsistent.
2. Otherwise **ANOTHER_LAW** if F3 fails or some transformation has status `changed`.
3. Otherwise **CONDITIONAL** if some transformation has status `conditional`. The filler keeps the law's identity exactly when every conditional transformation is at one of its keeping assignments. Different transformations have different unknowns, so these conditions are independent.
4. Otherwise **SAME_LAW_NEW_STATE**.

**The reason** lists the items that give the verdict:
- INVALID: F1.
- ANOTHER_LAW: F3 if it fails, and every transformation with status `changed`.
- CONDITIONAL: every transformation with status `conditional`.
- SAME_LAW_NEW_STATE: nothing.

### 2.8 Decisive observations (blueprint 5.6, item 4)
- **A CONDITIONAL filler:** for each conditional transformation T, the decisive observation measures each unknown that matters for T with its instrument:
  - for a new quantity, its `route`;
  - for a world quantity, the instrument that anchors its meaning;
  - `"?"` when there is none. The branch then waits for an instrument (requirement 10).
  - **Why it decides:** measure the quantity at a state where its reading r is not zero, then again at the image of that state under T. The reading becomes s*r. So the branch s = +1 predicts r and the branch s = -1 predicts -r, and they differ because r is not zero. The keeping assignments say which readings keep the law's identity.
- **Several fillers:** a decisive state for every pair of fillers labelled SAME_LAW_NEW_STATE.
  - It is a state (a value for every variable name of the two filled laws other than y and their new quantities; constants keep their values) and an observer of y in this world.
  - The two fillers' predicted intervals of y at that state must be separated by more than twice that observer's precision. Then any reading of that observer is consistent with at most one of them.
  - **The predicted interval** of a filler at a state is the exact range of f_k over the feasible set of its constants, given all the world's observations (Section 2.6).
- **Kept fillers:** in a world with several fillers, the list of every filler labelled SAME_LAW_NEW_STATE. They are all branches; none is chosen.

## 3. World format, budgets and validity
- **Format:** a v0.4 world file (`lang/SPEC_v0.4.md`) naming the registry `test4_registry` and the SHA-256 of the sealed registry's canonical form. The file names are `W-01.json` ... `W-30.json`; the `id` inside is `w01` ... `w30`, by the language's name rule.
- **Budgets per world:**

| item | count |
|---|---|
| bodies | 0 to 4, at most 2 of any one body type |
| world quantities | 2 to 9 |
| laws | exactly 1 |
| relations | none (`"relations": []`) |
| observers | 1 to 3 |
| old observations | 1 to 6 |
| new observations | 1 to 4 |
| fillers | 1 (single-filler worlds), or 2 to 3 (several-filler worlds) |
| new quantities per filler | 0 to 3 |
| new bodies per filler | 0 to 2 |

- **Expressions:** the v0.4 letters with integer powers from -3 to 3, and no `D()`. Every number in a world has a numerator and a denominator of absolute value at most 10^9.
- **Names:** 2 to 6 characters, lowercase ASCII letters and digits, starting with a letter, and neutral: no physical meaning, no hint of the answer. All names in a world are distinct, components included, and distinct from every registry id.
- **Validity.** A world that fails any rule is invalid and is excluded from scoring.
  - **V1:** the reader accepts the world with the sealed registry.
  - **V2, the law:**
    - exactly one law, with `accepted_at`;
    - its left side is a single name y: a single-number world quantity, or a component of one;
    - y appears neither on the right side of the law nor on the right side of any filler;
    - no `D()` in the law or in any filler. An observation's state can fix only names, so a rate of change enters a law as a quantity of its own, with a derived meaning such as velocity or acceleration;
    - every filler's `of` is this law, and its `eq` has the same left side y.
  - **V3, new quantities:**
    - every new quantity has a known owner;
    - its `old_value` is a fraction (a list for a multi-component kind) or `"same"`, never `"?"`.
  - **V4, unknown actions:**
    - only on single-number quantities, which includes the kind `"?"`;
    - at most 2 unknown signs per filler, over all transformations. The registry's `"?"` cards on names in the law or the filled law count.
  - **V5, the filled law is affine in its new quantities:**
    - no product of two new quantities or components;
    - no new quantity in a denominator;
    - no power of a new quantity other than 1;
    - every new quantity still appears after expansion.
  - **V6, world quantities:**
    - each `value` is `"var"` or a fraction (a list), never `"?"`;
    - each `dims` equals the meaning's dimensions where the meaning has them;
    - the law is dimensionally consistent.
  - **V7, bodies:**
    - a body owns at most one quantity of each meaning, counting the filler's new quantities;
    - two world bodies of the same type own quantities of exactly the same meanings;
    - a new quantity owned by one of two same-type bodies has a known meaning, and the other body owns a quantity of the same meaning (a world quantity, or a new quantity of the same filler);
    - a new body's type is a type that no world body has.
  - **V8, observations:**
    - every observation is of y;
    - every state gives a value to every variable name of the law and of all fillers other than y and the new quantities, and to no constant;
    - no division by zero at any state;
    - the law satisfies every old observation within its observer's precision;
    - at least one new observation differs from the law's prediction by more than its precision (a real deficit);
    - every filler alone satisfies all new observations for some values of its new quantities.
  - **V9, dimensions:** in every filler that is not INVALID, every new quantity's dimensions are determined (by its meaning, its `dims`, or inference), and every inferred exponent is an integer.
  - **V10, several-filler worlds:**
    - no filler is CONDITIONAL;
    - at least 2 fillers are SAME_LAW_NEW_STATE;
    - the new quantities of those fillers are constants (`value: "?"`), and their feasible sets (Section 2.6) are bounded;
    - every pair of them has a decisive state (Section 2.8).
  - **V11:** the world does not reproduce a dev world (Section 12). The validator holds SHA-256 fingerprints of the dev laws and filled laws.
  - **V12:** the key entry agrees with the reference answer (Section 5).
  - **V13, products of transformations (the W8 lesson of test 3):** the reference answer does not change when the products of catalog transformations are checked as well.
    - Run Sections 2.4 and 2.7 over every element of the group that the world's catalog generates (at most 128 elements under these budgets). Every SAME_LAW_NEW_STATE filler must keep its verdict, and every CONDITIONAL filler the same set of assignments that keep its identity. (An INVALID or ANOTHER_LAW verdict cannot be changed by adding products; a world counted as "decided by F3 alone" in Section 6 must also show no change under every product.)
    - This can matter only when the law itself is changed by some transformation of the catalog. Example: a law that time reversal and charge conjugation each break, but their product keeps, and a filler that breaks that product too.

## 4. Outputs and proofs
`results/outputs.json` is `{world_id: {method: output}}`. The procedure's output for a world:
```
{"fillers": {
   "f1": {"verdict": "SAME_LAW_NEW_STATE | ANOTHER_LAW | INVALID | CONDITIONAL",
          "reason": [{"item": "F1"}, {"item": "F3"}, {"item": "F2", "transformation": "rev_t"}, ...],
          "F1": {"consistent": true, "inferred_dims": {"qn": {"M": 1} | "undetermined"}},
          "F2": {"rev_t": {"status": "no_change | changed | conditional",
                           "unknowns": ["qn:rev_t"],
                           "assignments": [{"signs": {"qn:rev_t": -1},
                                            "old": "unchanged" | {"point": {...}},
                                            "new": "unchanged" | {"point": {...}}}, ...],
                           "keeping": [{"qn:rev_t": -1}],        (conditional only)
                           "matters": ["qn:rev_t"]},             (conditional only)
                 "exch(b1,b2)": {...}, ...},
          "F3": {"holds": true, "point": {"qn": "3/2", "qv@0": "-1"}} | {"holds": false, "farkas": [...]},
          "zero_report": ["absent", "below_precision", ...],     (one label per old observation, in order)
          "decisive": [{"transformation": "rev_t",
                        "measure": [{"unknown": "qn:rev_t", "instrument": "i06" | "?"}]}]},   (conditional only)
   ...},
 "world": {"kept": ["f1", "f2"],
           "decisive": [{"pair": ["f1", "f2"], "state": {...}, "observer": "ob1",
                         "intervals": {"f1": ["lo", "hi"], "f2": ["lo", "hi"]}}]},   (several-filler worlds)
 "catalog": "1"}
```
- **Proofs for one assignment** (Section 2.3):
  - `"unchanged"`: the scorer checks the identity by exact expansion (the draft's "the two expressions match").
  - `{"point": {name: value, ...}}`: changed. The scorer evaluates the difference at the point exactly and requires it to be defined and not zero (the draft's "witness point").
  - A conditional transformation's assignments thus show the draft's "one value that keeps and one that does not".
- **F1** needs no certificate: the scorer recomputes it, as test 3 did for TYPE.
- **F3:**
  - `point` gives a value to every unknown and must satisfy every inequality;
  - `farkas` is a list of `{"obs": "old" | "new", "k": index, "side": "upper" | "lower", "y": positive rational}`. Combined with these multipliers, the inequalities must give 0 for the coefficient of every unknown and a negative right-hand side. For a system without unknowns, this is a single violated inequality.
- Every number is an exact rational string, of any size.
- **Baselines** output only `{"fillers": {fid: {"verdict": ...}}, "world": {"kept": [...]}}`.

## 5. Key format
`key/key.json` is a list of entries:
```
{"id": "W-01",
 "fillers": {"f1": {"verdict": "ANOTHER_LAW", "F2": {"rev_t": "changed", ...}}},
 "kept": ["f1", "f2"] | null,
 "decisive": [{"pair": ["f1", "f2"], "state": {...}, "observer": "ob1"}] | null,
 "traps": ["T2"], "notes": "free text"}
```
- Each filler's `verdict` is required and must equal the scorer's reference; otherwise the world is excluded.
- The per-transformation statuses under `F2` are optional. If given, each must equal the reference.
- `kept` is required for several-filler worlds and must equal the reference.
- `decisive` is required for several-filler worlds: `[{"pair": [fid, fid], "state": {...}, "observer": id}]`, one entry for every pair of kept fillers. The validator checks each one exactly, as in 8.2; this is how V10 is checked. The procedure never sees it, and it finds its own states.
- `traps` declares the traps the world is meant to exercise (Section 6). The validator checks every declared trap against its condition.

## 6. Composition (30 worlds)
- **25 single-filler worlds:**

| reference verdict | worlds |
|---|---|
| SAME_LAW_NEW_STATE | 7 |
| ANOTHER_LAW | 8, at least 2 of them decided by F3 alone (F1 consistent, every transformation `no_change`) |
| INVALID | 3 |
| CONDITIONAL | 7 |

- **5 several-filler worlds,** each with 2 or 3 fillers, at least 2 of them SAME_LAW_NEW_STATE. In at least 2 of these worlds, a third filler is ANOTHER_LAW or INVALID.
- **Traps.** These are the trap table of the test-4 draft (section 6), with trap 1 moved from mass doubling to charge conjugation (registry decision R1). The validator computes each condition. Each trap appears in at least 2 worlds.

| trap | condition, computed from the reference and the baselines |
|---|---|
| T1, a new quantity must transform with the rest | a SAME_LAW_NEW_STATE filler with a new quantity of meaning m04 (a third charge), which FIX labels ANOTHER_LAW because of `conj_c` |
| T2, a filler that a free choice would rescue | an ANOTHER_LAW filler decided by a meaning-reading transformation, which DERIVE and DIMS both label SAME_LAW_NEW_STATE; at least one with a new quantity of meaning m06 (damping) under `rev_t` |
| T3, an external field whose source moves | a SAME_LAW_NEW_STATE filler with a new quantity of meaning m18, which FIX labels ANOTHER_LAW because of `rev_t` |
| T4, a moving observer | a SAME_LAW_NEW_STATE filler with a new quantity of meaning m22, which FIX labels ANOTHER_LAW because of `refl_x` |
| T5, a gained symmetry | a transformation with status `changed` where, for every assignment, the law is changed and the filled law unchanged |
| T6, identical bodies | a filler whose only `changed` transformations are exchanges |
| T7, an unknown action | a CONDITIONAL filler; at least 2 through a `"?"` card of the registry (m09 or m10), and at least 2 through a new quantity whose meaning is `"?"` |
| T8, a matrix action | a filler whose reason contains a transformation acting on a quantity of its law by a matrix that is not a multiple of the identity; at least one with m23 under `rev_t`, and one with an axial vector (m18, m19 or m20) under `refl_x` |
| T9, several fillers | the 5 several-filler worlds |

- **Each type of transformation decides at least 2 worlds:** kind-reading (`rot_z`), meaning-reading, and cast-reading (`exch`). A type decides a filler when the filler's reason contains a transformation of that type.
- **Baseline sensitivity:** for each baseline of Section 7, at least 8 fillers where its verdict differs from the reference. Whichever baseline turns out best, the McNemar test of C7 then has enough discordant fillers.
- **The W8 lesson:** every condition above is computed from the reference card as a whole. "Not detected by X" always means "not by X, nor by any part or combination of X" (V13 for transformations).
- **Diversity:** vary meanings, transformations, dimensions, law forms (monomials, sums, ratios) and the position of fillers. No two worlds share the same law and filled laws.

## 7. Baselines
Each baseline is a known wrong rule (test-4 draft, section 7). All baselines use the procedure's F1, F3 and verdict rule, and change only where F2 gets its actions. None of them produces a decisive observation.
- **FIX** ("keep the new quantity fixed"):
  - every new quantity is left unchanged by every transformation: action 1 under meaning- and kind-reading transformations, and never exchanged;
  - every unknown sign of the registry is +1.
- **DERIVE** ("derive the action from the law") is the circular rule that blueprint 5.5 forbids. Under each transformation, whatever can be chosen is chosen to keep the card:
  - free choices: the new quantities' meaning-reading actions (+1 or -1 for a single number, a diagonal matrix of +1 and -1 for an n-component quantity, whatever their cards say) and every unknown sign;
  - the status is `no_change` if some choice makes changed false, else `changed`.
- **DIMS** ("the action from the dimensions") is the false sufficiency of question 9, 9.5: a change of units that every dimensionally consistent filler passes.
  - Under each meaning-reading transformation, every quantity (world or new) acts by (-1)^e times the identity. For `rev_t`, e is the exponent of T in its dimensions; for `refl_x`, of L; for `conj_c`, of Q.
  - A new quantity with unknown dimensions uses its inferred dimensions, or e = 0 if undetermined.
  - Other actions are as in the procedure.
- **FORK_ALL** ("always branch"), like FORKALL in test 2, measures over-branching.
  - Every new quantity's meaning-reading action is unknown, whatever its card says: an unknown sign for a single number, a diagonal matrix of unknown signs for an n-component quantity.
  - Other actions are as in the procedure.
- In several-filler worlds, a baseline's kept list is its SAME_LAW_NEW_STATE fillers.
- The procedure of test 1 with hand-written cards is not a baseline: it needs the generator to write the cards, which is the leak this test removes.

## 8. Correctness, metrics, criteria
### 8.1 Correctness of the procedure on a filler
The procedure is correct on a filler when all of these hold:
- the verdict and the reason equal the reference;
- **F1:** the status and every inferred dimension equal the reference;
- **F2:** for every transformation of the catalog:
  - the status equals the reference;
  - every proof checks;
  - for a conditional transformation, the keeping assignments and the unknowns that matter equal the reference;
- **F3:** the status equals the reference, and the point or the Farkas certificate checks;
- **CONDITIONAL:** every conditional transformation has a decisive observation listing exactly its unknowns that matter, each with its correct instrument.

A baseline is correct on a filler when its verdict equals the reference.

### 8.2 Correctness on a several-filler world
- The kept list equals the reference.
- Every pair of kept fillers has a valid decisive state: the intervals are recomputed exactly, and the gap is above twice the observer's precision.

### 8.3 Metrics
- **accuracy:** fillers correct (8.1), over all valid fillers;
- **silent substitution:** fillers whose reference is ANOTHER_LAW, answered SAME_LAW_NEW_STATE or CONDITIONAL (the forbidden outcome, blueprint 5.2);
- **false alarms:** fillers whose reference is SAME_LAW_NEW_STATE, answered ANOTHER_LAW, over those fillers;
- **branch accuracy:** CONDITIONAL fillers answered correctly (8.1), over the CONDITIONAL fillers;
- **silent choice:** several-filler worlds that fail 8.2 because a reference kept filler is missing or a pair of kept fillers lacks a valid decisive state;
- **INVALID detection:** INVALID fillers answered INVALID, over the INVALID fillers;
- **over-branching** (reported only): CONDITIONAL answers on fillers whose reference is decided.
- **zero-effect report** (reported only): the count of each label, and the share of labels equal to the reference.

### 8.4 Criteria
- **C1:** accuracy >= 0.70.
- **C2:** silent substitution in at most 1 filler.
- **C3:** false alarms <= 0.15.
- **C4:** branch accuracy >= 0.70.
- **C5:** silent choice in at most 1 world.
- **C6:** INVALID detection >= 2/3.
- **C7:** both of:
  - accuracy minus the best baseline's accuracy >= 0.15;
  - one-sided exact McNemar p < 0.05 against that baseline. Here b = fillers where the procedure is correct and the baseline is not, c = the reverse, and p = P(X >= b) with X ~ Binomial(b + c, 1/2). A tie in baseline accuracy goes to the larger p.
- **Outcome:** VOID if 7 or more of the 30 worlds are excluded (more than 20%); PASS if C1-C7 all hold; FAIL otherwise.

## 9. Pre-registered interpretation
- **PASS** is evidence that, on unseen formal worlds, the identity card can be filled automatically from a sealed registry and computed with machine-checkable proofs:
  - actions come from kinds, meaning cards and bodies;
  - where an action is unknown, the procedure branches instead of guessing;
  - there is no silent substitution, and no silent choice among identity-preserving fillers.
  - It closes the blind spot of test 1 as the draft defines it (section 2): changes in transformations nobody wrote down, decided by what the registry knows about the new quantity.
- **FAIL** returns the card's candidates (blueprint 5.3-5.7), or their implementation, to design. **VOID** means a rerun with new worlds.
- **Not evidence of:** real discovery; superiority over language models; the correctness of the registry's physics (checked separately by `registry/check_cards.py`); F4 or F5.

## 10. Hidden information
- The registry, its notes and the language are public to the generator. The answers are not in any world: worlds hold facts (laws, observations, fillers), never verdicts.
- The procedure never reads `registry/registry_notes.md`.

## 11. Generator brief
- **Bias.** You are from the same model family as the author of the procedure, so shared habits could make the worlds accidentally easy for it. Counter this deliberately:
  - prefer unfamiliar law forms, dimensions and numbers;
  - do not model worlds on the examples in this protocol or in the language files;
  - vary which transformation decides;
  - place old observations close to the edge of their precision, never on it;
  - make FIX, DERIVE, DIMS and FORK_ALL genuinely tempting.
- **Physics.** Use the registry as it is. If you believe a card is physically wrong, write it in `key/generator_notes.md` and keep using the card as written.
- **Method:**
  1. Use code and exact fractions.
  2. Write `key/verify_key.py` from this protocol alone, and run it first.
  3. Run the sealed validator, and repair until it prints VALID.
  4. Keep `progress.txt` updated.
- **Do not** add constraints that make the test easier than this protocol requires. If a requirement cannot be met, or the protocol is ambiguous, stop and write the problem in `key/generator_notes.md` for the project owner. Do not resolve it silently.

## 12. Dev set (used during development; excluded from the test)
- `dev/make_dev.py` writes 24 dev worlds and their key:
  - **D-01 to D-16:** toy worlds that cover every trap T1-T9, the zero-effect labels, an unknown kind, an INVALID filler, a filler decided by F3 alone, and a several-filler world.
  - **E2 worlds of blind test 1** (published), rewritten against this registry:
    - E-01, E-05 (written as a kinetic energy), E-07 (written as F = (m + m2) a), E-11 (written as an energy), E-13 and E-14;
    - E2-10 and E2-15 are D-02 and D-06;
    - not expressible: E2-02, E2-04 and E2-08 (square roots), E2-03 (a Galilean boost), E2-09 (F5), E2-12 and E2-16 (a new quantity in a denominator, V5).
  - **Coverage-check cases of the language:** C2 is C-02 (a new body), C3 is C-03, and C8 is D-09. C11 has no law.
    - C1 is rejected by V13 and kept in `dev/rejected/` as a case the validator must reject: under the half turn (`rot_z` applied twice) its law is unchanged and the filled law is not.
- **Dev checks:**
  - `dev/fuzz_compare.py`: random worlds, procedure against the independent reference;
  - `dev/mutation_test.py`: deliberate corruption of outputs, worlds and keys;
  - `dev/make_dev_hashes.py`: the fingerprints for V11.
- The validator rejects a world whose law and filled laws reproduce a dev world. It holds only their SHA-256 fingerprints.

## 13. Known limitations (declared before the test)
- The generator and the procedure author are models of the same family. The scorer and the procedure are independent code by the same author.
- **"Correct" is defined by our rules and by the sealed registry.** If a card is physically wrong, the test cannot see it.
  - The cards were checked against 15 laws of known symmetry.
  - Only the overall sign of the complex field is unguarded, and it is a phase convention.
  - A wrong card shows up only when another fact contradicts it.
- **The blind spot moved, it did not vanish:** from "what the generator did not write" to "what the registry does not know". It is now declared once for all laws.
- One law per world. Unknown actions only as signs of single numbers. F4 and F5 are not tested, and neither are affine transformations, things whose effect changes between old observations, or apparent multiplicity.
- **`rot_z` can decide only through a law on a scalar or on a z component.** A quarter turn makes a law on an x or y component into a law on another component, so it is changed before and after the filler alike (registry decision R2). The half turn, a product of two quarter turns, can still change such a law; V13 then rejects the world, as it does the coverage case C1.
- **Every symmetry the law has counts in the card, whether it is supported or accidental** (a property of a simple formula only). Breaking an accidental symmetry is labelled like any other change (neutral review of the 9c candidates, gap 5, left as a theoretical risk).
- **There is no label "a generalization with a limit of agreement"** (such as relativistic energy returning to Newton's as c grows). Such fillers get one of the four labels (neutral review, part B 2.4, item 3).
- The comparison with baselines is partly definitional, since each baseline is a known wrong rule.
- The worlds are formal and few.

## 14. Hashes (SHA-256)
- **Published on the Notion page when sealed:**
  - this protocol;
  - `registry/registry.json`, `registry/registry_notes.md`, `registry/check_cards.py`;
  - `lang/SPEC_v0.4.md`, `lang/reader_v0.py`;
  - `procedure/procedure_v4.py`;
  - `scorer/ref_v4.py`, `scorer/score_v4.py`, `scorer/validate_v4.py`;
  - `tools/hash_files.py`.
- `key/key.json`: published before the procedure runs.
- `results/outputs.json`: published by the procedure author before the key is opened.

## 15. Choices made while writing this protocol (approved 2026-10-06 and 2026-10-07)
Marked [changes a decision] when the choice departs from an approved decision of the draft; the others fill in details the draft left open.
**Review (2026-10-06):** the project owner approved every item below (items without a comment by tacit approval). Item 3: V13 stays in the validator, and checking products inside the procedure is deferred to a later test. Item 4: the alternative is recorded as an open question on the status page. Item 7: the owner approved an unscored report of the computable reason for a zero effect (2.6, the zero-effect report). While writing the code, the key also gained the decisive states of several-filler worlds, so that V10 can be checked (Section 5).
1. [changes a decision; APPROVED 2026-10-06] **Laws without `D()`** (V2). Decision 4 allowed `D(x, t)` on the left side. In v0.4, an observation can only read a name and a state can only fix names, so a `D()` in a law could not be checked against any observation. A rate of change enters as a quantity of its own, with a derived meaning (m13, m14); its actions are still computed from the definitions.
2. [changes a decision; APPROVED 2026-10-06] **One law per world, and no relations.** The draft's sketch allowed "one law or more" and defining relations. The card belongs to one law, and without `D()` in laws, relations would only restate the cards. Component relations would also be changed by `rot_z`.
3. **The W8 lesson** applied to transformations: V13 (products of transformations), and the sentence on combinations in Section 6.
4. **Identical bodies:** a new quantity given to one of two same-type bodies needs a partner of the same meaning on the other (V7). The alternative, counting it as breaking the exchange, is left for later.
5. **Unknown actions are signs** (2.2), at most 2 per filler, only on single numbers; a new quantity of unknown kind counts as one number (V4).
6. **F2 compares on the world's catalog before the filler.** New bodies enter no exchange and have new body types (2.4, V7).
7. **F3 is the joint feasibility** of the old and the new observations, with the values the filler describes. A constant present all along (`"same"`) must fit both. No `"?"` old values in test worlds. The reason for a zero effect is not scored (2.6, V3).
8. **Several-filler worlds:** no CONDITIONAL filler; the kept fillers have constants only; the procedure chooses the decisive state. Silent choice also counts a missing decisive state (2.8, V10, 8.3).
9. **The form of the proofs** (Section 4). Invariance is written as "solutions go to solutions" (2.3), which equals the registry check's criterion when y keeps its name. The decisive observation of a branch gives the unknowns that matter with their instruments, and the readings r and -r (2.8).
10. **Correctness requires the whole card,** every transformation's status included, not only the verdict (8.1). The scoring unit is the filler (about 35 to 40 fillers); silent choice is counted per world.
11. **The exact definitions of the four baselines** (Section 7). DIMS is extended from time reversal (the draft) to the mirror (by the L exponent) and to charge conjugation (by the Q exponent). DERIVE and FORK_ALL use diagonal sign matrices for vectors.
12. **The computed trap conditions** (Section 6). T1 uses a third charge under `conj_c` (decision R1). T7 needs at least 2 of each source of the unknown, and T8 needs m23 under `rev_t` and an axial vector under `refl_x`.
13. **Budgets** (Section 3): at most 4 bodies with at most 2 of a type, observation counts, numbers up to 10^9, and names of 2 to 6 characters.
