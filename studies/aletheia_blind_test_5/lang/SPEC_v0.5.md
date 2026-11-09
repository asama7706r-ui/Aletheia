# Aletheia description language v0.5: specification (draft, not sealed)

This file is the complete grammar. `reader_v0.py` is its executable form; if they disagree, the reader is wrong and must be fixed.
Earlier versions: `SPEC_v0.1.md` to `SPEC_v0.4.md`; their readers, tests and examples are kept unchanged in `versions/`.

## Changes from v0.4 (2026-10-21)
Decision 3 on the test-5 draft («مسودة مواصفة التجربة 5», section 12): exactly five additions, and nothing else.
1. **G4, sentences in floor descriptions.** A floor may carry a versioned list of rules (`rules_version`, `rules`). A rule is written as *sentences*: free variables (an implicit "for all" at the front of each sentence, never written), "if ... then" (`->`), "or" (`|`) and the order symbol `>`. List v1 of the Q10 page (11.8) is written this way.
2. **G3, a statement to build a kind.** A world may hold `builds`: "build a kind that contains this old kind and satisfies this role". The role names new generators; existence comes from naming them, and later from a witness built by the kernel, never from a sentence.
3. **Type restriction, old or new.** Every free variable of a floor rule is declared `"old"` (it ranges over the old kind inside a candidate new kind) or `"new"` (it ranges over the whole candidate, old elements included). List v1 declares all its variables `"new"`. Type-restricted copies, such as `a*b = b*a` with `a: "old"` and `b: "new"`, are the parts the kernel generates (Q10, 11.6, 2b); test files will write them in the same form. Worlds have no free variables: free variables belong to floor descriptions only (Q10, 11.6, question 3).
4. **`!=` in roles and in kind relations** (in v0.4 only meaning conditions had it).
5. **A floor of real numbers.** A kind may be `"over": "reals"`. Every number written in a file is still an exact fraction; a real number that is not a fraction (like the square root of 2) is never written, only asked for.

Three encoding choices were needed to write list v1 with these five additions. They are not new powers, but they are choices: Claude proposed them and the project owner approved them (2026-10-21):
- **Sentences are clauses:** `A & B -> C | D`. `&` joins conditions before `->` only, and `|` joins outcomes after it only, with no nesting. Every clause is a sentence with "for all" at the front and no "there exists"; and every such sentence can be written as a list of clauses (its conjunctive normal form: a negated atom moves before `->`, `a != b` is the negation of `a = b`, and an empty outcome is written `0 != 0`). So clauses add no power beyond G4. Transitivity (`a > b & b > c -> a > c`) cannot be written without `&` before `->`.
- **Rule ق2 is written by `keeps`,** the list of the old kind's letters that keep their values among old elements. ق2 says the old kind sits unchanged inside the new one. That is a statement about two kinds, not a sentence inside one, so it cannot be written with sentences.
- **Brackets are kept.** In sentences, `u*v*w` with no brackets means that every bracketing has that value (Hamilton's `ijk`), while `(u*v)*w` names one bracketing. Q10, D1, the lesson on how a request is written: the result follows the written form.

## Principles
1. **Facts, not verdicts.** Every statement is a fact with a source (`src`). No field ever states a conclusion such as "same law", "valid filler", "necessary body", "trusted observation", "deficit", "new kind needed" or "known kind suffices". Observations and requests are written; the kernel finds deficits and builds kinds.
2. **No defaults.** Every field must be written. An unknown value is written as `"?"`, and only where this grammar allows it.
3. **Neutral names.** A name carries no meaning; meaning lives only in meaning cards. A rule's id is a label, not a claim.
4. **Exact numbers.** Every number is an exact fraction in lowest terms: a string `"7/4"`, `"-3"`, `"0"` in data fields, and `7/4` inside expressions and sentences. Not `0.5`, not `2/4`, not `1e-9`. Counts and orders (`shape`, dimension exponents, `epoch`, `accepted_at`) are plain JSON integers.
5. **Closed grammar.** Anything not listed here is not part of v0.5. Do not invent fields. If a fact cannot be written, it is reported as a missing piece.

## Two files
- **Registry** (sealed before any world exists) holds TYPES: dimensions, floors (with their rule lists), kinds, transformations, instruments, meaning cards, definitions, body types.
- **World** holds INSTANCES: bodies, quantities, relations, laws, observers, observations, fillers, and builds. A world names its registry by `registry` (id) and `registry_sha256` (SHA-256 of the registry's canonical form, printed by `reader_v0.py canon`).

## Registry
```
{"v0": "0.5", "file": "registry", "id": NAME, "catalog": "1",
 "dimensions": ["L", "M", "T", ...],                     base dimensions, capitalized
 "floors": [{"id", "depends_on": [floor ids],                            no cycles
             "rules_version": "1" | "0",                 "0" exactly when rules is []
             "rules": [RULE, ...], "src": "seed"}],
 "kinds": [{"id", "floor", "over": "fractions" | "reals", "shape": [positive ints],
            "generators": [names], "relations": [SENTENCES over the generators, with = or != only],
            "under": {T: ACTION, ...}, "src": "seed"}],
 "transformations": [{"id", "reads": "kind" | "meaning" | "cast", "src": "seed"}],
 "instruments": [{"id", "unit": DIMS, "src": "seed"}],
 "meanings": [{"id", "kind", "anchor": {"instrument": id} | {"seed": "human"} | {"derived": definition id},
               "conditions": [relations over meaning ids using >= > !=],
               "under": {T: ACTION | {"derived": definition id}, ...}, "src": "seed"}],
 "definitions": [{"id", "eq": equation over meaning ids, "src": "seed"}],
 "body_types": [{"id", "src": "seed"}]}

RULE = {"id", "protected": true | false,
        "vars": {name: "old" | "new"},                   its free variables ({} if none)
        "sentences": [SENTENCE, ...],                    the rule holds when all its sentences hold
        "keeps": [LETTER, ...],                          only for a rule like ق2; see below
        "src": "seed"}
```
- **Floor rules** are checked on a candidate kind that contains the floor's kind (a new kind built from it, or the floor's kind itself). Each name in a rule's sentences is a free variable declared in `vars`, and each declared variable appears in a sentence. A variable may not be a generator of a kind on the same floor.
- **`vars`**: `"new"` ranges over the whole candidate; `"old"` ranges over the floor's kind inside it. So `a*b = b*a` with `a: "old"`, `b: "new"` says the old elements commute with everything, which is weaker than the same sentence with both `"new"` (the whole candidate is commutative; test-5 draft, trap 4). When the candidate is the floor's kind itself, the two types coincide.
- A rule has **exactly one** of `sentences` and `keeps` non-empty; the other is `[]`. A rule written by `keeps` has `vars: {}`.
- `protected: true` = this rule is never relaxed (Q10, 11.6, question 4). It is a fact about the sealed list, decided by the human seed, not a verdict of the kernel.
- **`keeps`** lists letters from `0 1 + - * ^-1 >`, without repeats. It means: the floor's old kind sits inside any new kind built from it; distinct old elements stay distinct; and each listed letter, applied to old elements, gives the same old element as before (`>` compares old elements only). `>` may be kept only if a sentence of the same floor uses `>`.
- **Rule ids** are local to their floor: unique inside it, and different from every registry statement id. Two floors may reuse a rule id (the complex list reuses the numbers of list v1).
- A **frame floor** (Q10, 7.5) is a floor whose rules are theorems about every kind that belongs to the frame, such as "composition of actions is associative". In v0.5 it is written like any floor, usually with no kind on it. Its proof cannot be written in v0.5 (see *Not in v0.5*).
- ACTION, DIMS, `under` tables and meanings are as in v0.4: an ACTION is a fraction, an n×n matrix of fractions (n ≥ 2), or `"?"`; DIMS is `{"L": 1, "T": -1}`; a kind's `under` lists exactly the kind-reading transformations; a meaning's `under` lists exactly the meaning-reading ones (it may also be `{"derived": definition id}`); cast-reading transformations appear in no action table.

## World
```
{"v0": "0.5", "file": "world", "id": NAME, "registry": registry id, "registry_sha256": 64 hex,
 "bodies", "quantities", "relations", "laws", "observers", "observations", "fillers":   exactly as in v0.4
 "builds": [{"id",
             "origin": kind id,                          the old kind the new one must contain (Q10, B3)
             "generators": [names],                      the new elements, named ([] is allowed)
             "role": [SENTENCES with = or != only],      what the new elements must satisfy (not empty)
             "frames": [floor ids],                      frames the law's text puts the new elements in ([] if none)
             "src"}]}
```
- The v0.4 parts of a world are unchanged: see `SPEC_v0.4.md`, section *World*, for bodies, quantities, relations, laws, observers, observations, epochs, calibration and fillers. A world about kinds only writes those lists as `[]`.
- **What a build says:** "a kind is wanted that contains the old kind `origin` and has elements `generators` satisfying every `role` sentence". It never says which old rules fall, whether a known kind suffices, or whether the request is possible. Those are kernel verdicts.
- **The origin** must be a kind whose floor has rules (`rules_version` is not `"0"`): those rules are the old rules the kernel judges.
- **Names in a role:** the build's generators and the origin kind's own generators (old named elements, such as `i` of the complex kind). A role has no free variables. Each generator must appear in at least one role sentence.
- **`frames`**: floors with rules, other than the origin's floor. The membership is a fact read from the law's text, with its source in `src` (Q10, 7.8, proposal 1).
- Generators are local to their build: two builds may reuse them. They must not reuse a world id, a registry id or an origin generator, and a build names each one once.

## Expressions in v0.4 places (the field letters)
Unchanged from v0.4. World laws, relations and filler equations, registry definitions and meaning conditions use: integers, fractions written `7/4`, lowercase names, `+ - * /`, integer powers (`a^2`, `a^-1`, `a^(-1)`), `D(x, t)`, parentheses, and exactly one of `=` (laws, relations, definitions) or `>= > !=` (meaning conditions). Not letters there: functions, decimals, fractional powers, `<`, `<=`, and the sentence letters `& | ->`.

## Sentences (the algebra letters, new in v0.5)
Used in floor rules, kind relations and build roles.

```
SENTENCE  =  [ATOM & ATOM & ... ->] ATOM | ATOM | ...
ATOM      =  TERM REL TERM                   one relation sign per atom
REL       =  =  |  !=  |  >                  > in floor rules only
```
| letter | example | meaning |
|---|---|---|
| integer, fraction | `2`, `1/2` | an old number; a fraction is two integers in lowest terms, denominator above 1 (`-3` is the negative of `3`, see `-`) |
| name | `a`, `u` | a free variable, a generator, or an origin generator (by place) |
| `+`, `-` | `a + b`, `a - b`, `-a` | `a - b` means `a + (-b)`; `-` is the named negative of ق11 |
| `*` | `a*b` | the kind's product, in this order |
| `^2` | `a^2` | means `a*a`, one factor |
| `^-1` | `a^-1` | the named inverse of ق13; a total operation, so `0^-1` names a value (Q10, D1) |
| `( )` | `(a*b)*c` | grouping is kept, never re-associated |
| `->` | `a != 0 -> a*a^-1 = 1` | if ... then (floor rules only) |
| `&` | `a > b & b > c -> a > c` | and, before `->` only (floor rules only) |
| `\|` | `a*b = 0 -> a = 0 \| b = 0` | or, after `->` or alone (floor rules only) |

- **Chains.** A product of three or more factors with no brackets, `u*v*w`, means that every bracketing of it has the same value; the same for sums. A bracketed product, `(u*v)*w`, is that bracketing only. So `u*v*w = -1` asks for more than `(u*v)*w = -1`. An atom with a chain holds only when every bracketing of each chain gives one value, and that value satisfies the relation: `u*v*w != 0` says that the bracketings agree and their value is not 0.
- **Minus.** A leading minus covers the whole product after it: `-a*b` is `-(a*b)`. Write `(-a)*b` for the other. A minus right after another sign needs brackets: `a*(-b)` and `a + (-b)`, never `a*-b` or `a + -b`. With distributivity these readings agree; without it they may not, so the written form decides.
- **Not letters in sentences:** `/` between names (write `a*b^-1`), other powers (write `x*x*x` or a bracketed product instead of `x^3`), `>=`, `<`, `<=` (write `a > b | a = b`, or swap the sides), `D(x, t)`, functions, decimals, "there exists", and nested connectives (no brackets around atoms, one `->` per sentence).
- **Which names a sentence may use:** a floor rule, only its declared variables; a kind relation, only that kind's generators; a role, only the build's generators and the origin's generators.
- **Canonical form.** The reader writes each sentence in one canonical spelling: spacing normalized, `a^2` written `a*a`, `a - b` written `a + (-b)` (so the named negative stays visible), the atoms before `->` and after it sorted, and the sentences of a rule, a kind and a role sorted, and so are the generators of a kind and of a build. Brackets that group are kept; renaming variables is not normalized.

## Uniqueness
All statement ids in a file are unique, components included. World ids must not reuse registry ids. A filler's local ids must not reuse any world or registry id. Rule ids are local to their floor and must not reuse a registry id. A rule's variables are local to it. A build's generators are local to it and must not reuse a world or registry id.

## Not in v0.5
- **"There exists"** in any sentence. Existence comes from naming a generator, and from the witness model the kernel builds (Q10, 11.5; test-5 draft, decision 4).
- **Partial operations.** `^-1` is total: `0^-1` has a value that the rules may leave free (Q10, D1).
- **Probabilities** in any field.
- **The proof of a frame theorem.** Writing "composition of actions is associative" with its proof needs a second sort (the state) and an operation that applies an action to a state. v0.5 has neither, so a frame theorem is declared by the human seed, as a declared gap. Decision of the project owner (2026-10-21): trap 10 of test 5 stays, and its protocol states that the frame theorem there is declared by the seed, not proved by the kernel.
- **The completeness of the reals,** and its shadow in sentences ("every positive number has a square root", "every polynomial of odd degree has a root"): declared gaps of list v1 (Q10, 11.8).
- Transformation actions on the generators of built kinds; a statement that a new kind acts on a state (other than through `frames`); decimals and functions everywhere; free text; verdict fields.
