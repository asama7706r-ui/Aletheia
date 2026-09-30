# Remaining E1 designs, keyed by private slot name. Each returns (world, key, extra) without id.
from wcheck import *
from wideal import regular_rep
from wsocle import socle_dim

sf = lambda M: [[fstr(x) for x in r] for r in M]


def reg(world, fam, D=6):
    grades = [g["grade"] for g in world["generators"]]
    rels = relations(world, None) if not world.get("parameters") else None
    return rels, grades


def regular_witness(world, fam, pvals=None, D=6):
    grades = [g["grade"] for g in world["generators"]]
    rels = relations(world, pvals) + family_relations(grades, fam)
    mats, normal = regular_rep(len(grades), rels, D)
    return mats, normal


def d_SUB_3():
    world = {"experiment": "E1",
      "generators": [{"name": "a", "grade": 0}, {"name": "b", "grade": 0}, {"name": "c", "grade": 0}],
      "laws": ["a*a = 1", "b**2 = 1", "a*b = c", "b*c = a", "c*a = b",
               "(a + b + c)**2 = 3 + 2*(a + b + c)"]}
    key = {"label": "SUBSUMED", "true_values": {"a": "1", "b": "-1", "c": "-1"},
      "observed_nonzero": ["a", "b", "c", "a + b + c"],
      "category": "subsumed: quaternion-looking cyclic relations a*b = c, b*c = a, c*a = b with involutions (Klein four-group)",
      "notes": "The relations present the Klein four-group (b*a*b = a gives a*b = b*a), whose group algebra is commutative; its four characters (1,1,1), (1,-1,-1), (-1,1,-1), (-1,-1,1) are rational solutions with all generators and a + b + c nonzero. Intended values a = 1, b = -1, c = -1."}
    return world, key, {}


def d_SUB_P():
    world = {"experiment": "E1",
      "generators": [{"name": "x", "grade": 0}],
      "variables": ["t"], "parameters": ["k"],
      "laws": ["x**2 - k*x = 4 - 2*k", "x**3 + x = 10",
               "(t + x)*(t + k - x) = t**2 + k*t + 2*k - 4"]}
    key = {"label": "SUBSUMED", "true_values": {"x": "2"}, "true_parameter_values": {"k": "3"},
      "observed_nonzero": ["x", "x**2"],
      "category": "subsumed with a parameter that does not change the decision",
      "notes": "Law 1 is (x - 2)*(x + 2 - k) = 0 and law 2 is (x - 2)*(x^2 + 2x + 5) = 0; since k^2 - 2k + 5 > 0 the gcd is always x - 2, so for every rational k the laws force x = 2 exactly (law 3 restates law 1 as a factorization in t). Decision SUBSUMED with x = 2 for all k, including the grid {-3,...,3,1/2}; true k = 3."}
    return world, key, {}


def d_NKc_2():
    world = {"experiment": "E1",
      "generators": [{"name": "h", "grade": 0}],
      "variables": ["t"],
      "laws": ["(t + h)**3 = t**3 + 3*t**2*h + 3*t*h**2",
               "(1 + h + h**2/2)**2 = 1 + 2*h + 2*h**2",
               "(1 - h)*(1 + h + h**2) = 1"]}
    Hm = [["0", "0", "0"], ["1", "0", "0"], ["0", "1", "0"]]
    key = {"label": "NEW_KIND", "true_family": "comm", "true_dim": 3, "witness": {"h": Hm},
      "observed_nonzero": ["h", "h**2"], "complete_presentation": True,
      "category": "new kind (comm, outside the familiar list): truncated polynomial algebra Q[h]/(h^3), second-order infinitesimal",
      "notes": "Law 1 (second-order Taylor expansion of a cube) gives h^3 = 0 while keeping the h and h^2 terms; law 2 is exp(h)^2 = exp(2h) to second order; law 3 inverts 1 - h by a truncated geometric series. The only rational value h = 0 kills h and h^2. Witness = nilpotent Jordan block (local algebra with one-dimensional socle, so minimal). Laws present T completely (dim 3)."}
    return world, key, {"roles": ["h", "h**2"]}


def d_NKg_2():
    world = {"experiment": "E1",
      "generators": [{"name": "w", "grade": 0}, {"name": "u", "grade": 1}, {"name": "v", "grade": 1}],
      "variables": ["s", "t"],
      "laws": ["w*w = 2",
               "(s*u + t*v)**2 = 0",
               "(w + s*u)*(w + t*v) = (w + t*v)*(w + s*u) + 2*s*t*u*v",
               "(w + u*v)**2 = 2 + 2*w*u*v"]}
    mats, normal = regular_witness(world, "graded")
    assert len(normal) == 8
    key = {"label": "NEW_KIND", "true_family": "graded", "true_dim": 8,
      "witness": {"w": sf(mats[0]), "u": sf(mats[1]), "v": sf(mats[2])},
      "observed_nonzero": ["u*v - v*u", "u*v", "w*u*v", "u", "v", "w"], "complete_presentation": True,
      "category": "new kind (graded, outside the familiar list): mixed-grade superalgebra Q(sqrt 2) tensor Grassmann(u, v)",
      "notes": "Even w with w^2 = 2, odd u, v. Law 3 is a supercommutator law: w commutes with u, v and u*v - v*u = 2*u*v. In comm it gives u*v = 0, so the fermion bilinear and law 4 collapse silently. No rational w with w^2 = 2. Witness = regular representation (Q(sqrt2)-local algebra with simple socle, so no smaller faithful representation). Laws present T completely (dim 8)."}
    return world, key, {"roles": ["u*v", "w*u*v", "u", "v", "w"]}


def d_NKg_3():
    world = {"experiment": "E1",
      "generators": [{"name": n, "grade": 1} for n in ["a1", "a2", "a3", "a4"]],
      "variables": ["s", "t", "u", "v"],
      "laws": ["(s*a1 + t*a2 + u*a3 + v*a4)**2 = 0",
               "(a1*a3 + a2*a4)**2 = -2*a1*a2*a3*a4",
               "(s*a1*a2 + t*a3*a4)**2 = 2*s*t*a1*a2*a3*a4",
               "a3*a4*a1*a2 = a1*a2*a3*a4"]}
    mats, normal = regular_witness(world, "graded")
    assert len(normal) == 16 and socle_dim(mats) == 1
    key = {"label": "NEW_KIND", "true_family": "graded", "true_dim": 16,
      "witness": {n: sf(M) for n, M in zip(["a1", "a2", "a3", "a4"], mats)},
      "observed_nonzero": ["a1*a2 - a2*a1", "a1*a2*a3*a4", "a1*a2", "a3*a4", "a1*a3", "a1", "a2", "a3", "a4"],
      "complete_presentation": True,
      "category": "new kind (graded, outside the familiar list): 4-generator exterior algebra with Pfaffian laws",
      "notes": "T = exterior algebra on a1..a4 (dim 16). Laws 2-3: the square of a 2-form is twice its Pfaffian times the volume a1*a2*a3*a4. In comm, law 1 gives a_i*a_j = 0, so the volume and all Pfaffian laws collapse to 0 = 0 (silent). Rational values force all generators to 0. Witness = regular representation (one-dimensional socle, minimal)."}
    return world, key, {"roles": ["a1*a2*a3*a4", "a1*a2", "a3*a4", "a1*a3", "a1", "a2", "a3", "a4"]}


def d_NKg_5():
    world = {"experiment": "E1",
      "generators": [{"name": "x", "grade": 0}, {"name": "y", "grade": 0}, {"name": "f", "grade": 1}, {"name": "g", "grade": 1}],
      "variables": ["s", "t"],
      "laws": ["x*x = 0", "y**2 = 0",
               "(s*f + t*g)**2 = 0",
               "(x + s*f)*(y + t*g) - (y + t*g)*(x + s*f) = 2*s*t*f*g",
               "(x + s*g)*(y + t*f) - (y + t*f)*(x + s*g) = 2*s*t*g*f",
               "(x + f)*(y + g) + (y + g)*(x + f) = 2*x*y + 2*x*g + 2*y*f"]}
    mats, normal = regular_witness(world, "graded")
    assert len(normal) == 16 and socle_dim(mats) == 1
    key = {"label": "NEW_KIND", "true_family": "graded", "true_dim": 16,
      "witness": {n: sf(M) for n, M in zip(["x", "y", "f", "g"], mats)},
      "observed_nonzero": ["f*g - g*f", "f*g", "x*y*f*g", "x", "y", "f", "g", "x*y"],
      "complete_presentation": True,
      "category": "new kind (graded, outside the familiar list): superspace with two even nilpotent and two odd coordinates, super-area laws",
      "notes": "T = Q[x,y]/(x^2,y^2) tensor Grassmann(f,g) (dim 16). Laws 4-5: the commutator of two super-displacements is twice the fermionic area f*g (and they give all even/odd commutations). In comm this forces f*g = 0 (silent collapse of the super-area, and of x*y*f*g). Rational values force all generators to 0. Witness = regular representation (one-dimensional socle, minimal)."}
    return world, key, {"roles": ["f*g", "x*y*f*g", "x", "y", "f", "g", "x*y"]}


def d_NKa_3():
    world = {"experiment": "E1",
      "generators": [{"name": n, "grade": 1} for n in ["a1", "a2", "b1", "b2"]],
      "variables": ["s", "t", "u", "v"],
      "laws": ["(s*a1 + t*a2)**2 = 0",
               "(s*b1 + t*b2)**2 = 0",
               "(s*a1 + t*a2)*(u*b1 + v*b2) + (u*b1 + v*b2)*(s*a1 + t*a2) = s*u + t*v",
               "(b1*a1)**2 = b1*a1",
               "a2*b2*a2 = a2",
               "a1*b1*a2*b2 = (1 - b1*a1)*(1 - b2*a2)"]}
    sm = mat([[0, 1], [0, 0]]); sp_ = mat([[0, 0], [1, 0]]); sz = mat([[1, 0], [0, -1]]); I2 = mid(2)
    def kron(A, B):
        return [[A[i // 2][j // 2] * B[i % 2][j % 2] for j in range(4)] for i in range(4)]
    wit = {"a1": sf(kron(sm, I2)), "a2": sf(kron(sz, sm)), "b1": sf(kron(sp_, I2)), "b2": sf(kron(sz, sp_))}
    key = {"label": "NEW_KIND", "true_family": "assoc", "true_dim": 16, "witness": wit,
      "observed_nonzero": ["a1*b1 - b1*a1", "a1*b1 + b1*a1", "a1", "b1", "a2", "b2", "b1*a1", "b2*a2"],
      "complete_presentation": True,
      "category": "new kind (assoc, outside the familiar list): two fermionic modes with canonical anticommutation relations (Clifford algebra on 4 odd generators = M4(Q))",
      "notes": "T = M4(Q) via the Jordan-Wigner representation (4x4 is minimal for M4(Q)). All generators are odd, but the anticommutator of a_i and b_i is 1, not 0: the graded family forces 1 = 0, and comm also forces 1 = 0 (a1*(2*a1*b1) = a1 gives a1 = 0). Law 4: number operators are projectors; law 6: the vacuum projector factorizes. Laws present T completely (dim 16)."}
    return world, key, {"roles": ["a1", "b1", "a2", "b2", "b1*a1", "b2*a2"]}


def d_NKa_4():
    world = {"experiment": "E1",
      "generators": [{"name": "p", "grade": 0}, {"name": "f", "grade": 1}, {"name": "g", "grade": 1}],
      "variables": ["s", "t"],
      "laws": ["p*p = 1", "p*f = -f*p", "p*g + g*p = 0",
               "(s*f + t*g)**2 = 0",
               "(1 + p)*f = f*(1 - p)",
               "(1 + p)*f*g = f*g*(1 + p)"]}
    # regular representation of the presented algebra (the 4-dim Grassmann module is NOT faithful:
    # f*g*(1 - p) acts as zero there)
    mats, normal = regular_witness(world, "assoc")
    assert len(normal) == 8 and algebra_dim(mats) == 8
    Pm, Lf, Lg = mats
    key = {"label": "NEW_KIND", "true_family": "assoc", "true_dim": 8,
      "witness": {"p": sf(Pm), "f": sf(Lf), "g": sf(Lg)},
      "observed_nonzero": ["p*f - f*p", "f", "g", "f*g", "1 + p", "1 - p"], "complete_presentation": True,
      "category": "new kind (assoc, outside the familiar list): Grassmann pair with a fermion-parity operator (smash product Grassmann(f,g) # Z2)",
      "notes": "p is even but anticommutes with the odd f, g (p = (-1)^F). In the graded family p must commute with f, so p*f = 0 and f = 0 (p invertible): silent collapse of the fermions; comm collapses the same way; rational values force f = g = 0. Witness = regular representation (8x8): the algebra has two indecomposable projectives A(1+p)/2 and A(1-p)/2, each local with a simple socle (f*g*(1+p) and f*g*(1-p)) of opposite parity, so a faithful module must contain both and needs dimension 8 (the 4-dim Grassmann module with parity is not faithful). Laws present T completely (dim 8)."}
    return world, key, {"roles": ["f", "g", "f*g", "1 + p", "1 - p"]}


def quat_regular(a, b):
    a, b = F(a), F(b)
    Lx = [[0, a, 0, 0], [1, 0, 0, 0], [0, 0, 0, a], [0, 0, 1, 0]]
    Ly = [[0, 0, b, 0], [0, 0, 0, -b], [1, 0, 0, 0], [0, -1, 0, 0]]
    return [[F(v) for v in r] for r in Lx], [[F(v) for v in r] for r in Ly]


def d_NKa_P():
    world = {"experiment": "E1",
      "generators": [{"name": "x", "grade": 0}, {"name": "y", "grade": 0}],
      "variables": ["s", "t"], "parameters": ["m"],
      "laws": ["(s*x + t*y)**2 = (m**2 + 2)*s**2 - 3*t**2",
               "(x*y)**2 = 3*m**2 + 6",
               "x*y*x = -(m**2 + 2)*y"]}
    Lx, Ly = quat_regular(2, -3)
    ev = {}
    for c in PARAM_GRID:
        X, Y = quat_regular(c * c + 2, -3)
        ev[fstr(c)] = {"witness": {"x": sf(X), "y": sf(Y)}, "dim": 4}
    key = {"label": "NEW_KIND", "true_family": "assoc", "true_dim": 4,
      "witness": {"x": sf(Lx), "y": sf(Ly)}, "true_parameter_values": {"m": "0"},
      "observed_nonzero": ["x*y - y*x", "x", "y", "x*y"], "complete_presentation": True,
      "category": "new kind (assoc; quaternion-type, familiar family) with a parameter that does not change the decision: generalized quaternion algebra (m^2 + 2, -3)",
      "notes": "For every rational m, x and y are invertible (x^2 = m^2 + 2 > 0, y^2 = -3) and anticommute, so comm (= graded, grades 0) forces x*y = 0 and then 1 = 0: the decision is NEW_KIND assoc for all m. True m = 0: T = (2, -3)_Q, a division algebra (2X^2 - 3Y^2 = Z^2 has no nontrivial rational solution, by descent mod 3), not isomorphic to Hamilton's quaternions (it splits at infinity) nor to M2(Q); witness = regular 4x4 representation (minimal for a 4-dimensional division algebra). Laws present T completely (dim 4)."}
    return world, key, {"roles": ["x", "y", "x*y"], "param_evidence": ev}


def d_CON_3():
    world = {"experiment": "E1",
      "generators": [{"name": "x", "grade": 0}],
      "laws": ["(x**2 - 2)*(x - 1) = 0", "x**3 + x**2 = 2*x + 2", "x**4 = 1"]}
    key = {"label": "CONTRADICTION",
      "category": "contradiction: three spectral conditions on one observable, pairwise consistent but jointly empty",
      "notes": "Law 2 is (x^2 - 2)*(x + 1) = 0. Subtracting law 1 from law 2 gives 2*(x^2 - 2) = 0, so x^2 = 2 and x^4 = 4; law 3 then gives 4 = 1, i.e. 3 = 0, so 1 = 0. Every pair of laws is consistent: {1,2}: x = sqrt 2 (Q(sqrt 2)); {1,3}: x = 1; {2,3}: x = -1."}
    extra = {"loo_models": {0: {"x": [["-1"]]}, 1: {"x": [["1"]]}, 2: {"x": [["0", "2"], ["1", "0"]]}}}
    return world, key, extra


def d_UND_4():
    world = {"experiment": "E1",
      "generators": [{"name": "f", "grade": 1}, {"name": "g", "grade": 1}],
      "variables": ["s", "t"], "parameters": ["c"],
      "laws": ["f*f = 0", "g**2 = 0",
               "(1 + t*g)*(1 + s*f) = 1 + s*f + t*g + (2*c**2 - 1)*s*t*f*g",
               "(f + g)**2 = 2*c**2*f*g"]}
    und = {}
    for c in PARAM_GRID:
        q = 2 * c * c - 1
        fam = "graded" if q == -1 else ("comm" if q == 1 else "assoc")
        mats, normal = regular_witness(world, fam, {"c": fstr(c)})
        obs = {"graded": ["f*g - g*f", "f", "g", "f*g"], "comm": ["f", "g", "f*g"],
               "assoc": ["f*g - g*f", "f*g + g*f", "f", "g", "f*g"]}[fam]
        und[fstr(c)] = {"decision": "NEW_KIND:" + fam, "witness": {"f": sf(mats[0]), "g": sf(mats[1])},
                        "dim": len(normal), "observed": obs}
    key = {"label": "UNDERDETERMINED",
      "category": "underdetermined: two odd nilpotent modes with exchange phase q = 2c^2 - 1 (g*f = q*f*g); the family depends on c",
      "notes": "Law 3 gives g*f = q*f*g with q = 2c^2 - 1 (never 0 on the grid). c = 0: q = -1, Grassmann algebra, NEW_KIND graded (comm kills f*g). c = 1 or -1: q = 1, Q[f,g]/(f^2, g^2), NEW_KIND comm (graded kills f*g; rational values kill f, g). c in {-3,-2,2,3,1/2}: q in {17, 7, -1/2}, quantum-plane quotient, NEW_KIND assoc (comm and graded both kill f*g). All cases have dim 4."}
    return world, key, {"roles": ["f", "g", "f*g"], "und": und}


DESIGNS = {"SUB-3": d_SUB_3, "SUB-P": d_SUB_P, "NKc-2": d_NKc_2, "NKg-2": d_NKg_2, "NKg-3": d_NKg_3,
           "NKg-5": d_NKg_5, "NKa-3": d_NKa_3, "NKa-4": d_NKa_4, "NKa-P": d_NKa_P, "CON-3": d_CON_3,
           "UND-4": d_UND_4}
