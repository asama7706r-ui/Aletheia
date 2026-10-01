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

Run them from this folder, e.g. `python posthoc_audit.py`. They need Python 3 and sympy.
