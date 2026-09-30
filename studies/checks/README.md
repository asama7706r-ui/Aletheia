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
| `q9c_*.py` | Checks for the "identity card" design question: how symmetries act on a newly added quantity. |

Run them from this folder, e.g. `python posthoc_audit.py`. They need Python 3 and sympy.
