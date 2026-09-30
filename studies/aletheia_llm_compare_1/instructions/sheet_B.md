TASK SHEET B - classify a candidate term (exact arithmetic)

You will receive several small "worlds" in JSON. For each world, classify the candidate term under the rules below. The rules are exact: follow them literally, in the given order, with exact rational arithmetic. Treat every world independently. Think as long as you need. At the very END of your reply, give exactly one fenced code block marked json containing a JSON list with one object per world (format in section 4).

1. WORLD FORMAT
- "quantities": each quantity with its dimensions, a map of rational exponents over base dimensions such as M, L, T. {} means dimensionless. "y" is the output quantity.
- "constants": named constants with exact values and dimensions.
- "parameters": dimensionless parameters with their given values.
- "law": the base law "y = f(...)".
- "term": {"expr": E, "unknown": u}. The candidate term E is linear in the unknown u: E = u * h, where h may contain quantities, constants and parameters. The full law is y = f + u*h.
- "coefficient_form":
  - "free": u may be any number;
  - "constants": u must be a dimensionless number times a product of rational powers of the declared constants.
- "symmetries": maps that send each listed quantity to a rational multiple of a quantity. Unlisted quantities are unchanged. Each map is a symmetry of the BASE law.
- "observations": each gives the inputs (every quantity except y), the measured output (y) and the observer's resolution d. d = 0 means exact.

2. CLASSIFICATION REASONS, checked in this order
- (1) TYPE_IMPOSSIBLE: coefficient_form is "constants", and no product of rational powers of the declared constants has dimension dim(y) - dim(h). If dim(y) - dim(h) is dimensionless, a pure number works, so this reason does not apply.
- (2) SYMMETRY_ZERO: some declared symmetry maps the FULL law (base plus term) to itself only if u = 0. That is, after applying the map to every quantity, the transformed full law is equivalent to the original only when u = 0.
- (3) INCIDENTAL: h is identically 0 at the given parameter values, but not identically 0 as a function of the parameters.
- Feasible set S:
  - Each observation with h != 0 (h evaluated at that observation) gives the exact interval u*h in [r - d, r + d], where r = output - f(inputs) and d is its resolution.
  - S is the intersection of the resulting intervals for u.
  - If no observation has h != 0, S is unconstrained (all of the real line).

3. FINAL LABEL
- CONFLICT, if some observation with h = 0 misses the base law by more than its resolution (|output - f(inputs)| > d), or if S is empty.
- Otherwise, if one of reasons (1)-(3) applies:
  - CONFLICT if 0 is not in S (the term is detected although it is forbidden);
  - else the FIRST reason that applies.
- Otherwise, UNCONSTRAINED if no observation has h != 0.
- Otherwise, ACTIVE if 0 is not in S. Report the exact interval S = [lo, hi].
- Otherwise, BOUNDED. Report the exact bound B = max |s| over s in S.

4. OUTPUT FORMAT
At the end of your reply, give ONE fenced json block with a JSON list, one object per world, for example:
```json
[
 {"id": "B-90", "label": "BOUNDED", "bound": "1/8"},
 {"id": "B-91", "label": "ACTIVE", "interval": ["3/100", "7/100"]},
 {"id": "B-92", "label": "SYMMETRY_ZERO"}
]
```
- Labels must be exactly one of: TYPE_IMPOSSIBLE, SYMMETRY_ZERO, INCIDENTAL, CONFLICT, UNCONSTRAINED, ACTIVE, BOUNDED.
- Give "bound" for BOUNDED and "interval" for ACTIVE, as exact rational strings such as "7/1500". Never use decimals.
- The ids above are only a format example. Use the ids of the worlds you receive.
