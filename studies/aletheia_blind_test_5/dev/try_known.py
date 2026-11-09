import sys, time
sys.path.insert(0, 'procedure'); sys.path.insert(0, 'scorer')
import procedure_v5 as PR
cases = [(['ga*ga = 1', 'gb != 0'], 'k01'), (['ga*ga = 2', 'gb != 0'], 'k01'), (['xa*ya = 1'], 'k01'),
         (['ga*e1 = e1*ga', 'gb*e1 = -(e1*gb)'], 'k02'), (['xa != 0'], 'k02'), (['xa*xa = -1', 'ya != xa'], 'k01')]
for role, o_ in cases:
    gens = sorted({t for s_ in role for t in ['ga', 'gb', 'xa', 'ya'] if t in s_})
    w = {'builds': [{'id': 'b', 'origin': o_, 'generators': gens, 'role': role, 'frames': [], 'src': 'seed'}]}
    t = time.time()
    o = PR.solve_world(w, budget=60)
    print(role, o['verdict'], o['known'] and (o['known']['kind'], o['known']['values']), round(time.time() - t, 1))
for role, o_ in [(['ga*ga = 1', 'gb != e1'], 'k02'), (['ga*ga = -1', 'gb*gb = 4', 'gb != 2'], 'k01'), (['xa*ya = 3', 'xa != 1', 'ya != 1'], 'k01')]:
    gens = sorted({t for s_ in role for t in ['ga', 'gb', 'xa', 'ya'] if t in s_})
    w = {'builds': [{'id': 'b', 'origin': o_, 'generators': gens, 'role': role, 'frames': [], 'src': 'seed'}]}
    t = time.time()
    o = PR.solve_world(w, budget=60)
    print(role, o['verdict'], o['known'] and (o['known']['kind'], o['known']['values']), round(time.time() - t, 1))
