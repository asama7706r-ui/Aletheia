# Aletheia description language v0.4: specification (draft, not sealed)

This file is the complete grammar. `reader_v0.py` is its executable form; if they disagree, the reader is wrong and must be fixed.
Earlier versions: `SPEC_v0.1.md`, `SPEC_v0.2.md` and `SPEC_v0.3.md`; their readers, tests and examples are kept unchanged in `versions/`.

## Changes from v0.3 (2026-10-06)
Decision 10 on the test-4 draft (gap G8), with the project owner's framing of the old observations (test-4 draft, section 4.3): the filler describes the new thing, and its effect is computed at the old observations, never tuned there.
- **`value`** in every new quantity: `"var"` (a variable) or `"?"` (an unknown constant, fixed once from the deficit). Before v0.4 a filler could not say which, and a reader had to assume.
- **`old_value`** replaces `absent_value`, because the field is the new quantity's value at the old observations (those with `epoch <= accepted_at` of the law), zero or not:
	- a fraction (a list of n fractions for an n-component kind), e.g. `"0"` when the thing was absent;
	- `"same"`: the thing was present all along with its present constant value (needs `value: "?"`);
	- `"?"`: unknown; those old observations then cannot test this filler.
	- With kind `"?"`, the only number allowed is `"0"` (the zero of whatever kind it is).

## Changes from v0.2 (in v0.3, 2026-10-06)
Decisions of the project owner on the questions raised by coverage check 2 (`coverage/RESULTS_run2.md`):
- **Decision 10:** `calibrated_against` stays. It is a fact about the history of instruments, used by the ledger to count independent witnesses; it never enters a law.
- **Decision 11 (new rule):** when a new quantity's `meaning` is known, its `under` must equal that meaning card's actions, exactly as written in the card (a `"?"`, a fraction, a matrix or a `{"derived": ...}`). A chosen meaning already fixes the actions, so the filler must say so openly; to leave an action open, set the meaning to `"?"`. In run 2 Gemini chose a card that silently decided a freedom while writing `"?"` for it; the v0.3 reader rejects that file and accepts all the others.
- **Decision 12:** definitions over the components of a multi-component meaning (candidate G6) are deferred to the test-4 spec. Until then such a meaning is built by a world relation.

## Changes from v0.1 (in v0.2, 2026-10-06)
Coverage check 1 (`coverage/RESULTS_run1.md`) found three gaps that test 4 needs. The project owner approved each one:
- **G1, a filler may add bodies.** `new_bodies` in every filler. Each new body must own at least one new quantity of that filler, and each new quantity must appear in the filler's `eq`. Whether a new body is *necessary* and *proven* is a kernel verdict (blueprint 1.1, 3.8, 5.2), never written in a world.
- **G2, old vs new observations, and fair judgement between them.** Every observation carries `epoch` (its arrival order). Every law carries `accepted_at` (the epoch at which it was accepted). Every observer carries `calibrated_against` (the observers it was calibrated against), so the kernel can tell independent witnesses from ones that share a root (blueprint 3.8, 4.1, 4.2). Why an observation is trusted is a kernel verdict (blueprint 3.2, 3.12), never written in a world.
- **G5, matrix actions on meanings.** A meaning-reading action may be an n×n matrix on an n-component quantity, in meaning cards and in new quantities. Example: time reversal conjugates a complex field, `[["1","0"],["0","-1"]]` on its two components.
- Not added (kept for the ladder test): G3, a statement to build an unknown kind; G4, generator grades and free variables in kind relations (a free variable is a hidden "for all", which v0 excludes).

## Principles
1. **Facts, not verdicts.** Every statement is a fact with a source (`src`). No field ever states a conclusion such as "same law", "valid filler", "necessary body", "trusted observation" or "deficit". Observations are written; the kernel finds deficits.
2. **No defaults.** Every field must be written. An unknown value is written as `"?"`, and only where this grammar allows it.
3. **Neutral names.** A name carries no meaning; meaning lives only in meaning cards.
4. **Exact numbers.** Every physical number is a string holding an exact fraction in lowest terms: `"7/4"`, `"-3"`, `"0"`. Not `"0.5"`, not `"2/4"`, not `"1e-9"` (write `"1/1000000000"`). Counts and orders (`shape`, dimension exponents, `epoch`, `accepted_at`) are plain JSON integers.
5. **Closed grammar.** Anything not listed here is not part of v0.4. Do not invent fields. If a fact cannot be written, it is reported as a missing piece.

## Two files
- **Registry** (sealed before any world exists) holds TYPES: dimensions, floors, kinds, transformations, instruments, meaning cards, definitions, body types.
- **World** holds INSTANCES: bodies, quantities, relations, laws, observers, observations, fillers. A world names its registry by `registry` (id) and `registry_sha256` (SHA-256 of the registry's canonical form, printed by `reader_v0.py canon`; write 64 zeros if you cannot compute it).

## Registry
```
{"v0": "0.4", "file": "registry", "id": NAME, "catalog": "1",
 "dimensions": ["L", "M", "T", ...],                     base dimensions, capitalized
 "floors": [{"id", "depends_on": [floor ids], "src": "seed"}],          no cycles
 "kinds": [{"id", "floor", "over": "fractions", "shape": [positive ints],   [] = one number, [2] = 2-vector, [3,3] = rank-2 tensor
            "generators": [names], "relations": [equations over the generators],
            "under": {T: ACTION, ...}, "src": "seed"}],
 "transformations": [{"id", "reads": "kind" | "meaning" | "cast", "src": "seed"}],
 "instruments": [{"id", "unit": DIMS, "src": "seed"}],
 "meanings": [{"id", "kind", "anchor": {"instrument": id} | {"seed": "human"} | {"derived": definition id},
               "conditions": [relations over meaning ids using >= > !=],
               "under": {T: ACTION | {"derived": definition id}, ...}, "src": "seed"}],
 "definitions": [{"id", "eq": equation over meaning ids, "src": "seed"}],
 "body_types": [{"id", "src": "seed"}]}
```
- **ACTION** = a fraction (multiplies every component), an n×n matrix of fractions acting on the n components (only when n ≥ 2, n = size of the kind's shape), or `"?"`.
- A kind's `under` lists exactly the transformations with `reads: "kind"`.
- A meaning's `under` lists exactly the transformations with `reads: "meaning"`. Besides an ACTION it may be `{"derived": definition id}` (computed from that definition, which must mention this meaning).
- Transformations with `reads: "cast"` appear in no action table. Their action is computed from the bodies: two bodies of the same body type exchange all their quantities of equal meaning.
- DIMS = `{"L": 1, "T": -1}`: declared dimension names, nonzero integer exponents; `{}` = dimensionless.

## World
```
{"v0": "0.4", "file": "world", "id": NAME, "registry": registry id, "registry_sha256": 64 hex,
 "bodies": [{"id", "type": body type id, "src"}],                    the cast; "world" is reserved
 "quantities": [{"id", "meaning", "owner": body id | "world", "dims": DIMS,
                 "components": [] | [n names],                       n = size of the meaning's kind
                 "value": "var" | fraction | [n fractions] | "?", "src"}],
 "relations": [{"id", "eq", "src"}],                                 defining links between quantities
 "laws": [{"id", "eq", "accepted_at": integer >= 0, "src"}],
 "observers": [{"id", "instrument", "precision": fraction > 0,
                "calibrated_against": [observer ids] | "?", "src"}],
 "observations": [{"id", "observer", "of": single-number name, "state": {name: fraction}, "value": fraction,
                   "epoch": integer >= 0, "src": the observer id}],
 "fillers": [{"id", "of": law id, "eq": the law after the filler,
              "new_bodies": [{"id", "type": body type id}],
              "new": [{"id", "kind": id | "?", "meaning": id | "?",
                       "owner": body id | new body id of this filler | "world" | "?",
                       "dims": DIMS | "?", "components": [] | [n names] | "?" (must be "?" iff kind is "?"),
                       "under": {each meaning-reading T: ACTION},     a matrix only when the kind is known and n >= 2;
                                                                    if the meaning is known: exactly its card's action
                       "value": "var" | "?",                         a variable, or an unknown constant
                       "old_value": fraction | [n fractions] | "same" | "?",   its value at the old observations
                       "route": instrument id | "?"}],
              "src"}]}
```
- `src` in a world is `"seed"` or an existing id; for an observation it must be its observer.
- `value: "var"` = a variable; a fraction = a constant; `"?"` = an unknown constant.
- An observation's `of` names a single-number quantity or a component; the `state` lists the other names fixed during the reading.
- **Epochs.** `epoch` orders arrivals: equal epochs arrived together. An observation is *old* for a law when its `epoch <= accepted_at` of that law (it was available when the law was accepted), *new* otherwise. This is a fact computed from two numbers, not a verdict about the observation.
- **Calibration.** `calibrated_against: []` = calibrated against no observer of this world; `"?"` = unknown. No observer is calibrated against itself, and the calibration links have no cycle.
- **Fillers.** Several fillers for one law are allowed (alternative repairs). Each filler's new bodies and new quantities are local to it: two fillers may use the same new id. Each new body must own at least one new quantity of its filler, and each new quantity must appear in the filler's `eq` (by its id, or by a component name). A new quantity with a known meaning writes exactly its card's actions in `under`. Its `old_value` is its value at the old observations: `"same"` only with `value: "?"`, and only `"0"`, `"same"` or `"?"` when its kind is `"?"`.

## Expressions (the letters)
| letter | example | note |
|---|---|---|
| integer | `7` | fractions are written with `/`: `7/4` |
| name | `xel` | lowercase letters, digits, `_`; starts with a letter |
| `+ -` (binary and unary) | `a - b`, `-a` | |
| `* /` | `a*b`, `a/b` | |
| integer power | `a^2`, `a^-1`, `a^(-1)` | no fractional or symbolic exponents |
| derivative | `D(x, t)` | two names |
| parentheses | `(a + b)*c` | |
| `=` | laws, relations, definitions, kind relations | exactly one |
| `>= > !=` | meaning conditions only | exactly one; no `<`, `<=` |

Not letters in v0.4: functions (exp, sin, sqrt), decimals, fractional powers, exists/for-all, free text.

**Which names an expression may use:**
- world laws and relations: single-number quantity ids and component names (never the id of a multi-component quantity);
- a filler's `eq`: the same plus its own new quantities (and their components);
- definitions and meaning conditions: meaning ids;
- kind relations: that kind's generators.

## Uniqueness
All ids in a file are unique, components included. World ids must not reuse registry ids. A filler's local ids (new bodies, new quantities, their components) must not reuse any world or registry id.
