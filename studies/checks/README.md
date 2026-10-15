# Exploratory checks (not evidence)

These are small scratch scripts written during design discussions. They check hand calculations, test counterexamples, and run post-hoc audits.

- They are **not** pre-registered and **not** sealed.
- Their results are **not** evidence for any claim. Treat them as a lab notebook.

| Script | What it checks |
|---|---|
| `shadow_mold_check.py` | Hand examples for "Yoneda shadow = representing object (mold)": Bombelli, a piezoelectric tensor, 2-D Dirac, and Grassmann. |
| `grassmann_check.py`, `fertility_check.py` | Early calculator checks on exterior algebras and u^2 = c. |
| `info_conservation_check.py` | Scratch checks for the information-conservation discussion. |
| `role_physics_check.py` | Examples for "a role is the law's content that must not be lost". |
| `posthoc_audit.py` | Post-hoc audit of blind test 1: which signal rejected the stricter family in each NEW_KIND world? It imports the frozen procedure read-only. |
| `q9c_e2_10_time_reversal_check.py` | World E2-10: time reversal exposes the damping filler only if the damping coefficient is held fixed. |
| `q9c_touch_shortcut_counterexample.py` | A vertical spring: the gravity term touches neither position nor acceleration, yet it breaks the up/down mirror. So "re-check only what the filler touches" is unsafe. |
| `q9c_new_quantity_action_check.py` | Three ways a symmetry can act on a newly added quantity, tried on E2-10 and E2-11: hold it fixed, derive it from the law under test, or act by its kind. |
| `q9c_unit_only_transformations_check.py` | On all 16 E2 worlds, unit changes and a "units-only time reversal" never detect a change of law, so they belong to the dimensions item. Also: a magnetic field is constant in time but flips under time reversal. |
| `q9c_f4_sos_certificate_check.py` | An exact algebraic certificate that the Motzkin polynomial is nonnegative, as an example of turning "is it bounded below?" into a checkable identity. |
| `q10_b1_dirac_relaxations.py` | The two relaxations of the Dirac demand: a 5-dim commutative, non-associative algebra, and the Dirac matrices (associative, non-commutative). Both have zero divisors. |
| `q10_a1_order_split_check.py` | Counting "order" as one rule or as three parts changes what minimal change picks between a two-element world and the quaternions, and makes the quaternions appear as three tied branches. |
| `q10_a1_linked_rules_check.py` | "No zero divisors" and "cancellation" agree in every ring checked, and come apart once additive negatives are dropped. |
| `q10_b2_branch_relations_check.py` | Two relaxations can be one structure read in a mirror (reversed multiplication), or one inside the other: the 5-dim Dirac branch is the Dirac matrices under the symmetric product (ab + ba)/2. |
| `q10_b2_third_branch_search.py` | Brute-force search over 3-element structures for a third branch of the demand z*0 + 0*z != 0: an element that swallows everything. |
| `q10_assumption_promotion_check.py` | When does an assumption become proven? Tiny worlds over Z/7 with ATMS-style labels and the "zero test", plus the coincidence rule applied to 6*pi^5. |
| `q10_forms_split_check.py` | Two writings of one law split when commutativity is dropped: (x+y)^2 with 2xy versus xy + yx on matrices and quaternions, and (p - ix)(p + ix) = p^2 + x^2 + 1 for operators. |

Run them from this folder, e.g. `python posthoc_audit.py`. Most need Python 3 and sympy; the `q10_*` scripts use the standard library only.
