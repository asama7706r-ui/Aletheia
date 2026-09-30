from wcheck import *
world = {"id": "E1-03", "experiment": "E1",
  "generators": [{"name": "a", "grade": 0}, {"name": "b", "grade": 0}],
  "variables": ["x", "y"],
  "parameters": ["c"],
  "laws": ["(a*x + c*b*y)**2 - c*(b*x + a*y)**2 = x**2 - c*y**2",
           "a*b = 2",
           "b*a = a*b",
           "(a**2 + c*b**2)**2 = 1 + 16*c"]}
def nk_witness(c):
    c = F(c)
    # companion matrix of b^4 + (1/c) b^2 - 4/c ; a = (c b^3 + b)/2
    Bm = [[F(0)]*4 for _ in range(4)]
    for i in range(1, 4): Bm[i][i-1] = F(1)
    Bm[0][3] = F(4)/c; Bm[2][3] = -F(1)/c
    B3 = mmul(mmul(Bm, Bm), Bm)
    A = madd([[c*x for x in r] for r in B3], Bm)
    A = [[x/2 for x in r] for r in A]
    s = lambda M: [[fstr(x) for x in r] for r in M]
    return {"a": s(A), "b": s(Bm)}
und = {}
for c in PARAM_GRID:
    if c == 0: und[fstr(c)] = {"decision": "SUBSUMED", "point": {"a": "1", "b": "2"}}
    elif c == 3: und[fstr(c)] = {"decision": "SUBSUMED", "point": {"a": "2", "b": "1"}}
    else: und[fstr(c)] = {"decision": "NEW_KIND:comm", "witness": nk_witness(c), "dim": 4, "observed": ["a", "b"]}
key = {"id": "E1-03", "label": "UNDERDETERMINED",
  "category": "underdetermined: unit of norm 1 in the plane with metric x^2 - c*y^2, with fixed product a*b = 2",
  "notes": "Laws reduce to a*b = b*a = 2 and a^2 - c*b^2 = 1, i.e. c*b^4 + b^2 - 4 = 0. c = 0: SUBSUMED (a=1,b=2 or a=-1,b=-2). c = 3: SUBSUMED (a=2,b=1 or a=-2,b=-1). c in {-3,-2,-1,1,2,1/2}: no rational solution, NEW_KIND comm (commutative algebra Q[b]/(c*b^4 + b^2 - 4), dim 4, a = (c*b^3 + b)/2)."}
errs, info = check_E1(world, key, {"roles": ["a", "b"], "und": und})
print("E1-03 checks:", "PASS" if not errs else "FAIL")
if errs: print(errs)
else:
    save_world_and_key(world, key); print(update_progress("E1-03 saved; next E1-04"))
