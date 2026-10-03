"""Assemble worlds/, data/ and key/key.json from the group definitions (generator's script)."""
import sys, os, json, random, copy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_worlds import *
import g_a, g_b, g_c, g_d, g_e, g_f, g_g, g_n

ROOT = os.path.dirname(HERE)

def all_worlds():
    out = []
    for mod in (g_a, g_b, g_c, g_d, g_e, g_f, g_g, g_n):
        out += mod.worlds()
    return out

def assign_ids(ws, seed=20261002):
    names = [w[0] for w in ws]
    rng = random.Random(seed)
    perm = list(range(1, len(names) + 1))
    rng.shuffle(perm)
    return {n: f"W-{p:02d}" for n, p in zip(names, perm)}

def world_dicts():
    ws = all_worlds()
    ids = assign_ids(ws)
    out = {}
    for name, d, model, note in ws:
        d = copy.deepcopy(d)
        d['id'] = ids[name]
        # key order as in the protocol
        dd = {k: d[k] for k in ["id", "experiment", "observable", "quantities", "constants", "observers", "base_law",
                                "visible", "ledger", "symmetries", "old_observations", "new_observations",
                                "possible_observations"]}
        out[ids[name]] = (name, dd, model, note)
    return out, ids

if __name__ == "__main__" and len(sys.argv) == 1:
    out, ids = world_dicts()
    for wid, (name, d, model, note) in sorted(out.items()):
        print(wid, name)

def write_worlds(out):
    os.makedirs(os.path.join(ROOT, 'worlds'), exist_ok=True)
    for wid, (name, d, model, note) in out.items():
        with open(os.path.join(ROOT, 'worlds', f"{wid}.json"), 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(d, fh, indent=1, ensure_ascii=False)
            fh.write('\n')

OLD_MODELS = {"vexa": g_a.OLD_MODEL, "tumb": g_b.OLD_MODEL, "plin": g_c.OLD_MODEL, "ostr": g_d.OLD_MODEL,
              "kimb": g_e.OLD_MODEL, "dral": g_f.OLD_MODEL, "wesk": g_g.OLD_MODEL, "yuth": {}, "brel": {"mu": F(1, 5)}}

def hidden_consistent(W, model):
    for ob in W.old + W.new:
        s = ob['state']
        val = W.fval(s)
        if W.vis is not None and model.get('mu') is not None:
            val += F(model['mu']) * W.hv(s)
        for rid, lam in model.get('cands', {}).items():
            R = W.cand(rid)
            val += F(lam) * W.h(R, s) * W.phi(R, s)
        for ex, c in model.get('expr', []):
            val += F(c) * ev(parse(ex), W.env(s))
        if abs(val - ob['value']) > W.prec(ob):
            return False
    return True

def key_A(out):
    entries = []
    for wid, (name, d, model, note) in sorted(out.items()):
        W = World(d)
        s = world_summary(W)
        v, r, b = s['answer']
        e = {"id": wid, "verdict": v, "relation": r, "branches": list(b) if b else None}
        if v != 'NO_DEFICIT':
            e["reasons"] = {rid: rs for rid, rs in s['an']['reasons'].items()}
        ht = hidden(model)
        if hidden_consistent(W, model):
            e["hidden_truth"] = ht
        else:
            note = note + (". hidden_truth omitted: the old readings come from the group's shared old model "
                           f"{json.dumps(hidden(OLD_MODELS[d['observable']]))}, the new readings from {json.dumps(ht)}")
        cat = [f"group {name[0]} ({d['observable']})"]
        if s['scope_sensitive']:
            cat.append("scope-sensitive")
        if s['nebulium']:
            cat.append(f"nebulium type ({s['nebulium']})")
        if s['mu_matters']:
            cat.append("visible relation matters")
        if s['planet_x']:
            cat.append("planet-X trap")
        e["category"] = "; ".join(cat)
        e["notes"] = note + f". NO_SCOPE answer: {answer_str(s['no_scope'])}" + \
            (f"; answer with mu at the midpoint of M_old: {answer_str(s['mid_mu'])}" if s['mid_mu'] else "")
        entries.append(e)
    return entries

def main():
    import part_b
    out, ids = world_dicts()
    write_worlds(out)
    keyA = key_A(out)
    raws_by_id = {wid: d for wid, (n, d, m, note) in out.items()}
    summaries = {wid: world_summary(World(d)) for wid, d in raws_by_id.items()}
    its = part_b.assign(part_b.items(ids, raws_by_id, summaries))
    os.makedirs(os.path.join(ROOT, 'data'), exist_ok=True)
    raws = [raws_by_id[f"W-{i:02d}"] for i in range(1, 28)]
    keyB = []
    bnotes = []
    for iid, cat, it, note in its:
        with open(os.path.join(ROOT, 'data', f"{iid}.json"), 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(it, fh, indent=1, ensure_ascii=False)
            fh.write('\n')
        reop, finals, errs = item_reference(raws, {w: World(d) for w, d in raws_by_id.items()}, summaries, it)
        if errs:
            print("ITEM ERRORS", iid, errs)
        keyB.append({"id": iid, "type": cat, "reopened": reop,
                     "final": {w: {"verdict": a[0], "relation": a[1], "branches": list(a[2]) if a[2] else None}
                               for w, a in finals.items()}})
        bnotes.append(f"- {iid} [{cat}]: {note}")
    key = {"A": keyA, "B": keyB}
    os.makedirs(os.path.join(ROOT, 'key'), exist_ok=True)
    with open(os.path.join(ROOT, 'key', 'key.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(key, fh, indent=1, ensure_ascii=False)
        fh.write('\n')
    with open(os.path.join(ROOT, 'key', 'part_b_notes.md'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write("# Part B items: generator's notes (not part of key.json)\n\n" + "\n".join(bnotes) + "\n")
    print("written:", len(out), "worlds,", len(its), "items")

if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'write':
    main()
