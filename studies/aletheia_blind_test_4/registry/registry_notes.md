# Test 4 registry (SEALED 2026-10-07): what each id means, and why each action is what it is

`registry.json` is built by `make_registry.py` (v0.4 language). Ids are neutral so that names carry no meaning.
This file is for the world generator and for human review. The kernel's procedure never reads it.
Status: reviewed by the project owner (2026-10-06): decisions R1-R6 taken (Notion page «مسودة سجل التجربة 4», section 5). Sealed together with the registry, the protocol and the code, by SHA-256, on 2026-10-07, before any world exists.

## Transformations (catalog version 1)
| id | what it does | reads |
|---|---|---|
| rev_t | time reversal: run the film backwards | meaning |
| refl_x | reflection of one axis, x -> -x (a mirror) | meaning |
| conj_c | charge conjugation: swap every charge for its opposite | meaning |
| rot_z | a quarter turn about the z axis | kind |
| exch | exchange of two bodies of the same body type | cast (the bodies) |

Kind actions under rot_z: scalar `1`; vec3 `[[0,-1,0],[1,0,0],[0,0,1]]` (polar and axial vectors turn alike under a proper rotation); cplx `1` (the two parts of a complex field are not directions in space).

Notation for the meaning actions below: `+1` unchanged, `-1` flips; POLAR = `diag(-1,1,1)` (an ordinary vector: only its x part flips in the mirror x -> -x); AXIAL = `diag(1,-1,-1)` (an axial vector, det(R) R: its y and z parts flip); CONJ = `diag(1,-1)` (complex conjugation on (real, imaginary)).

## Meanings
| id | meaning | kind | anchor | rev_t | refl_x | conj_c |
|---|---|---|---|---|---|---|
| m01 | time | scalar | i01 clock | -1 | +1 | +1 |
| m02 | mass (> 0) | scalar | i03 balance | +1 | +1 | +1 |
| m03 | energy | scalar | i04 calorimeter | +1 | +1 | +1 |
| m04 | electric charge | scalar | i05 electrometer | +1 | +1 | -1 |
| m05 | spring stiffness (> 0) | scalar | seed | +1 | +1 | +1 |
| m06 | damping coefficient, a material constant (> 0) | scalar | seed | +1 | +1 | +1 |
| m07 | coupling constant (like Coulomb's k or G) | scalar | seed | +1 | +1 | +1 |
| m08 | charge density | scalar | seed | +1 | +1 | -1 |
| m09 | coupling of an interaction whose mirror behaviour was never tested | scalar | seed | +1 | ? | +1 |
| m10 | field whose behaviour under time reversal was never tested | scalar | seed | ? | +1 | +1 |
| m11 | distance between two bodies (> 0) | scalar | i02 ruler | +1 | +1 | +1 |
| m12 | position | vec3 | i02 ruler | +1 | POLAR | +1 |
| m13 | velocity, d01: m13 = D(m12, m01) | vec3 | derived | (-1) | (POLAR) | (+1) |
| m14 | acceleration, d02: m14 = D(m13, m01) | vec3 | derived | (+1) | (POLAR) | (+1) |
| m15 | momentum, d03: m15 = m02*m13 | vec3 | derived | (-1) | (POLAR) | (+1) |
| m16 | force | vec3 | i06 dynamometer | +1 | POLAR | +1 |
| m17 | electric field | vec3 | i07 field probe | +1 | POLAR | -1 |
| m18 | magnetic field | vec3 | i08 magnetometer | -1 | AXIAL | -1 |
| m19 | angular momentum | vec3 | seed | -1 | AXIAL | +1 |
| m20 | torque | vec3 | seed | +1 | AXIAL | +1 |
| m21 | free-fall field (acceleration of gravity) | vec3 | seed | +1 | POLAR | +1 |
| m22 | velocity of a moving observer | vec3 | seed | -1 | POLAR | +1 |
| m23 | charged scalar field (two real parts) | cplx | seed | CONJ | +1 | CONJ |

Values in parentheses are computed by the kernel from the definitions; `check_cards.py` prints them.
Instruments: i01 clock (T), i02 ruler (L), i03 balance (M), i04 calorimeter (M L^2 T^-2), i05 electrometer (Q), i06 dynamometer (M L T^-2), i07 electric field probe (M L T^-2 Q^-1), i08 magnetometer (M T^-1 Q^-1). Body types ty01-ty08 carry no meaning.

## Why these actions
1. **Checked against laws with known symmetries** (`check_cards.py`, run 2026-10-06): 15 laws, among them Newton's second law, the Lorentz force, the isotropic and the damped spring, free fall, Coulomb energy, the energy seen by a moving observer, L = r x p, torque, F = qE and the Klein-Gordon charge density. From the cards alone, each law comes out unchanged or changed exactly as physics says: 15/15. Classical mechanics and electromagnetism are invariant under time reversal, a reflection, charge conjugation and rotations; damping breaks time reversal.
	- The check catches wrong cards: 10 deliberate card errors were all caught, including coverage check 2's Klein-Gordon error (complex field left unchanged by time reversal).
	- A sign flip of every card was tried one at a time: only the overall sign of m23 goes unnoticed. That sign is a phase convention (the density is built from products of the field's parts), and m23's mirror action (+1, a scalar rather than a pseudoscalar field) is a modelling choice that no law in the check can test.
2. **Standard tables** (from memory, not opened in this session): Jackson, *Classical Electrodynamics*, 3rd ed., section 6.10, Table 6.1 (behaviour of r, p, L, F, torque, E, B, charge density, current density and energy under parity and time reversal); charge conjugation flips charges and so the fields and densities they produce (e.g. Griffiths, *Introduction to Elementary Particles*, ch. 4); time reversal takes a wave function to its complex conjugate (Sakurai, *Modern Quantum Mechanics*, section 4.4).
3. **The damping coefficient (m06)** is a material constant and does not flip under time reversal, so damping breaks the symmetry (Notion Q9 page 9.5; neutral review 3.4; test 1 key note on E2-10).
4. **The two `?` cards (m09, m10)** are deliberate: a symmetry never tested in a domain is unknown there, which is how the theta-tau puzzle was solved (Lee and Yang, 1956). They serve trap 7 of the test-4 draft.

## Design choices (proposals for review)
- No "double all masses" transformation in this draft. My first reason (the inertial force m a doubles while the gravitational force G m1 m2 / r^2 quadruples) holds only for the naive form, masses alone. Corrected after the project owner's comment (2026-10-06): if time and charge are rescaled with the masses so that the constants of the domain stay fixed (masses x4, times x1/2, charges x4, lengths x1), every action is fixed by the quantity's dimensions, and all the Newtonian and Coulomb laws of `check_cards.py` stay the same, gravity between two bodies included. Laws with another fixed scale change, as they should: E = m c^2 (a fixed speed). This "similarity scaling" is a valid, testable transformation whose actions follow from dimensions plus the list of fixed constants. Decision (2026-10-06): it stays out of test 4 and is recorded for a later test (blueprint 7.3, item 6); charge conjugation is the third meaning-reading transformation.
- Every directional quantity is a 3-vector, never an "x component" scalar: a component written as a scalar would wrongly stay unchanged under rotations.
- No meaning built from vector components (gap G6): energies are anchored by an instrument, and formulas such as a kinetic energy from velocity components live in world relations.
- Conditions (F4) are few and are not scored in test 4.
