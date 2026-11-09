import sys, time, json
sys.path.insert(0, 'procedure'); sys.path.insert(0, 'scorer')
import procedure_v5 as PR, ref_v5 as RF, certs_v5 as C, score_v5 as SC, validate_v5 as V
role = ['ga*ga = 2', 'gb*gb = 0', 'gc*gc = -2', 'ga*gb = -(gb*ga)', 'ga*gc = -(gc*ga)', 'gb*gc = -(gc*gb)', 'ga != 0', 'gb != e1', 'gc*e1 = e1*gc']
w = {'builds': [{'id': 'b', 'origin': 'k02', 'generators': ['ga', 'gb', 'gc'], 'role': role, 'frames': [], 'src': 'seed'}]}
t = time.time()
o = PR.solve_world(w, budget=900)
t1 = time.time()
pool, problems = SC.output_pool(o, C.world_info(w))
tr = RF.truth(w, pool)
print('procedure', V.summary_safe(o), round(t1 - t, 1), 's')
print('truth    ', V.summary_safe(tr), round(time.time() - t1, 1), 's')
print('agree', V.decision_equal(o, tr))
