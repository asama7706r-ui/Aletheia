"""Dev run of fuzz case 55 (seed 20261023, 2026-10-23): the procedure timed out at 1800 s and kept two
candidates the reference refutes. Usage: python -I dev/try_case55.py BUDGET OUT.json
Writes the procedure's full output, so the reference can be run on its certificates afterwards."""
import json, sys, time
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, 'procedure'); sys.path.insert(0, 'scorer')
import procedure_v5 as PR, validate_v5 as V
role = ['ga*ga = 2', 'gb*gb = -2', 'gc*gc = -1', 'ga*gb = -(gb*ga)', 'gb*gc = -(gc*gb)', 'gb != 0']
w = {'builds': [{'id': 'b', 'origin': 'k02', 'generators': ['ga', 'gb', 'gc'], 'role': role, 'frames': [], 'src': 'seed'}]}
t = time.time()
o = PR.solve_world(w, budget=int(sys.argv[1]))
print('procedure', V.summary_safe(o), round(time.time() - t, 1), 's', flush=True)
print('recorded truth: BRANCHES {q12,q13,q6} witnessed, {q12,q5} no_witness')
json.dump({"world": w, "output": o}, open(sys.argv[2], "w", encoding="utf-8"), indent=1)
