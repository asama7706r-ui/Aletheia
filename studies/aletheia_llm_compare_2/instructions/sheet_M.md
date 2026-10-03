TASK SHEET M - is something new needed? (with the method)

You will receive several small "worlds" in JSON. Each world describes one measured quantity, the established law for it, a list of registered candidate effects (the "ledger"), and readings. For each world, answer the question in section 3 by following the method in section 4 literally. Treat every world independently and use exact rational arithmetic. Think as long as you need. At the very END of your reply, give exactly one fenced code block marked json containing a JSON list with one object per world (format in section 6).

1. WHAT A WORLD SAYS
- "observable": the name of the measured quantity, called y below.
- "quantities": every quantity with its dimensions, a map from base dimensions to rational exponents ({} means dimensionless). Every quantity other than the observable is a "state quantity". A state gives a value to every state quantity.
- "constants": named constants, each with an exact value and dimensions.
- "observers": instruments, each with a precision d >= 0. A reading v by an observer means that the true value of y at that state lies in the closed interval [v - d, v + d].
- "base_law": "y = f", where f is an expression in the state quantities and constants.
- "visible": null, or a relation already seen in the old readings. It contributes mu*h_V at a state, where h_V is its "term" and mu is an unknown number, the same at every state.
- "ledger": the registered candidates. A candidate R has a "term" h_R, a "coefficient" ("unknown", or {"exact": value}) and a "coverage" (or null). If R is present, it contributes lam_R * h_R * phi_R at a state, where:
  - lam_R is its coefficient: the given exact value, or an unknown number, the same at every state;
  - phi_R is its coverage factor at that state, computed from the coverage ratio rho = the "ratio" expression evaluated at that state:
    - "dimmer": phi_R = g(rho), where g is the given "expr" in the variable r;
    - "switch": phi_R = 1 if rho < threshold (for "on": "<") or rho > threshold (for "on": ">"); otherwise phi_R = 0;
    - coverage null: phi_R = 1 at every state.
  - A coverage "summary", if present, is only a description. The numbers decide.
- "symmetries": each has a "map" that sends the observable and some state quantities to rational multiples of quantities ({"q": "c*q2"} means q -> c*q2). Unlisted quantities are unchanged.
- "old_observations" and "new_observations": readings {"state", "value", "observer"}. The old readings were explained by the established law. The new readings were made later, often in other conditions.
- Expressions use Python syntax: * is multiplication, ** is a power.

2. FACTS THAT HOLD IN EVERY WORLD
- The true law of y is the established law plus AT MOST ONE ledger candidate: y = f + mu*h_V + (the contribution of one candidate, or nothing). The term mu*h_V exists only if there is a visible relation. Combinations of two or more candidates are not considered.
- Every coefficient (mu, and every lam) is a pure number times a product of rational powers of the world's declared constants, and every contribution has the dimensions of y.
- Every declared symmetry is an exact symmetry of the true law: applying its map to the equation of the true law gives the same equation back.
- Every reading is truthful within its observer's precision. The coverage factors and the exact coefficients are correct as given.

3. THE QUESTION
The new readings may not fit the established law. Decide which ONE of these holds:
- NO_DEFICIT: the established law alone (with some value of mu, if there is a visible relation) fits every old and new reading within precision. In that case the answer is NO_DEFICIT, whatever the candidates could also do.
- KNOWN: there is a deficit, and exactly one ledger candidate can be the missing part, that is: with that candidate present, the true law can fit every old and new reading within precision while respecting section 2. Give that candidate's id.
- FORK: there is a deficit, and two or three ledger candidates can each, alone, be the missing part. Give their ids.
- NEW: there is a deficit, and no ledger candidate can be the missing part. Something that is not in the ledger is needed.

4. THE METHOD (follow it literally)
4.1 Inequalities. An observation at state s with reading v and precision d gives the two linear inequalities
    v - d <= E(s) + (the included contributions at s) <= v + d,
where E(s) = f(s) + mu*h_V(s) (just f(s) without a visible relation). The unknowns are mu (if there is a visible relation) and lam_R (if R is included and its coefficient is "unknown"). A system is FEASIBLE if some values of its unknowns satisfy all its inequalities. A system without unknowns is feasible if every inequality holds.

4.2 The systems for a candidate R:
- Z (step 0): all old and new observations; no candidate.
- A_R (actual): all old and new observations; R included with its actual coverage factor; lam_R fixed if it is exact.
- C_R (uncovered): as A_R, but phi_R is replaced by 1 at every new-observation state; old states keep the actual factor. Without coverage, C_R = A_R.
- S_R (shape): the new observations with R included and phi_R replaced by 1; the old observations WITHOUT R (they constrain mu only); lam_R free even when an exact value is given.

4.3 Steps.
1. Step 0: if Z is feasible, the answer is NO_DEFICIT. Stop. A residual within precision is never "explained" by a candidate.
2. Otherwise, for each candidate R, determine:
   - TYPE-impossible: no product of rational powers of the declared constants has the dimension dim(y) - dim(h_R). Coverage factors are dimensionless.
   - SYMMETRY-forbidden: some declared symmetry maps the equation y = f + mu*h_V + lam*h_R to itself only when lam = 0.
   - whether A_R is feasible.
   R is SUFFICIENT if it is not TYPE-impossible, not SYMMETRY-forbidden, and A_R is feasible.
3. No sufficient candidate: NEW. Exactly one: KNOWN with that candidate. Two or three: FORK with those candidates.

4.4 Exclusion reasons. For every candidate that is not sufficient (when there is a deficit), list ALL the reasons that apply:
- TYPE: R is TYPE-impossible.
- SYMMETRY: R is SYMMETRY-forbidden.
- SCOPE: R has a coverage, A_R is infeasible, and C_R is feasible. ("It would suffice if it were uncovered in the new domain.")
- SHAPE: S_R is infeasible. ("Even uncovered, no strength of R fits the new observations.")
- BOUND: S_R is feasible and C_R is infeasible. ("Some strength would fit, but what is known about the strength, its exact value or the old observations, excludes every such strength, even uncovered.")
- When A_R is infeasible, at least one of SCOPE, SHAPE and BOUND applies. TYPE and SYMMETRY can occur together with anything, including a candidate whose A_R is feasible.

5. CONVENTIONS
- Write rationals exactly, e.g. "1/2". Never use decimals.
- Use the candidate ids of the world (R1, R2, ...).
- Reason names must be exactly: TYPE, SYMMETRY, SCOPE, SHAPE, BOUND.

6. OUTPUT FORMAT
At the end of your reply, give ONE fenced json block with a JSON list, one object per world, for example:
```json
[
 {"id": "W-90", "verdict": "NO_DEFICIT"},
 {"id": "W-91", "verdict": "KNOWN", "relation": "R2", "excluded": {"R1": ["SCOPE"], "R3": ["SHAPE", "TYPE"]}},
 {"id": "W-92", "verdict": "FORK", "branches": ["R1", "R3"], "excluded": {"R2": ["BOUND"]}},
 {"id": "W-93", "verdict": "NEW", "excluded": {"R1": ["SYMMETRY"], "R2": ["SHAPE"]}}
]
```
- "excluded" lists every candidate that is not sufficient, with all its reasons. Omit it for NO_DEFICIT.
- The ids above are only a format example. Use the ids of the worlds you receive.
