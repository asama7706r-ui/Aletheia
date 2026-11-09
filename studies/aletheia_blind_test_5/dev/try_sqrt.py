import sys, time
sys.path.insert(0, 'procedure'); sys.path.insert(0, 'scorer')
import procedure_v5 as PR
for role in [['ga*ga = 2', 'gb*gb = 2', 'ga*gb = -(gb*ga)'], ['ga*ga = 2', 'gb*gb = -1', 'ga*gb = -(gb*ga)']]:
    w = {'builds': [{'id': 'b', 'origin': 'k01', 'generators': ['ga', 'gb'], 'role': role, 'frames': [], 'src': 'seed'}]}
    t = time.time()
    o = PR.solve_world(w, budget=300)
    print(role, o['verdict'], [(b['drop'], b['status'], sorted(b['proofs'])) for b in o['branches']], round(time.time() - t, 1), flush=True)
