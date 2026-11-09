"""Audit diagnostic for test 5b (not pre-registered; the sealed result stands): rules or evidence?
The same check as test 5's audit/diag_inject.py, on the 5b procedure (procedure_v5b.py and the files it imports;
the sealed files are not changed). For each world the procedure got wrong, a copy of the procedure starts with the
key's witnesses and refutations in its memory, as if it had found them itself:
- every witness goes into witness_of, under the units it fails;
- every refutation goes into proof_of and, through proc_c3.add_conflict, into the list of conflicts that drives the
  hitting-set loop (so it is shrunk and split into parts exactly as the procedure's own conflicts are).
Everything else is the procedure's own code: its search, its minimality, statuses, merge, marks and proofs.
If it then gives the truth's decision with correct marks, its rules were applied correctly and only the certificates
were missing. Compared with the truth as the sealed scorer printed it (results/report_X.json).
Usage (from aletheia_blind_test_5b/): python -I audit/diag_inject_5b.py [BUDGET_SECONDS]"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "procedure"))
sys.path.insert(0, os.path.join(ROOT, "scorer"))
import procedure_v5b as PB  # noqa: E402
import proc_c3 as C3  # noqa: E402
import certs_v5 as C  # noqa: E402
import ref_v5b as RF  # noqa: E402
import validate_v5b as V  # noqa: E402

P = PB.P
sys.stdout.reconfigure(encoding="utf-8")
ENTRY = {}
ORIG_INIT = P.World.__init__


def init(self, world, t_end):
    ORIG_INIT(self, world, t_end)
    e = ENTRY["e"]
    ws = [b["witness"] for b in e.get("branches") or [] if b.get("witness")]
    ws += [e["top_witness"]] if e.get("top_witness") else []
    for w in ws:
        self.witness_of[frozenset(C.witness_fail_units(w, self.info))] = w
    for r in e.get("refutations") or []:
        drop = frozenset(r["drop"])
        self.proof_of[drop] = r["proof"]
        C3.add_conflict(self, frozenset(self.U) - drop, r["proof"], "key")


P.World.__init__ = init


def check(batch, wid, row, budget):
    path = os.path.join(ROOT, f"batch_{batch}", "worlds", f"{wid}.json")
    world = json.load(open(path, encoding="utf-8"))
    key = json.load(open(os.path.join(ROOT, f"batch_{batch}", "key", "key.json"), encoding="utf-8"))
    ENTRY["e"] = {e["id"]: e for e in key}[wid]
    t0 = time.time()
    out = PB.solve_world(world, budget=budget)
    secs = time.time() - t0
    got = json.loads(json.dumps(V.summary_safe(out)))
    same = got == row["truth"]
    info = C.world_info(C.R.load(path))
    marks_ok = forced_ok = wit_ok = True
    for b in out.get("branches") or []:
        if b["marks"] != RF.marks_of(info, b["drop"]):
            marks_ok = False
        for u in b["drop"]:
            p = (b.get("proofs") or {}).get(u)
            if p is None or not C.safe(C.check_refutation, p, info, [x for x in b["drop"] if x != u])[0]:
                forced_ok = False
        if b["status"] == "witnessed" and not C.safe(C.check_witness, b["witness"], info, b["drop"])[0]:
            wit_ok = False
    print(f"{batch} {wid}: decision {'= truth' if same else '!= truth ' + json.dumps(got)}; "
          f"marks {'ok' if marks_ok else 'DIFFER'}; forced proofs {'all valid' if forced_ok else 'MISSING'}; "
          f"witnesses {'valid' if wit_ok else 'INVALID'}; {secs:.1f} s", flush=True)


if __name__ == "__main__":
    budget = int(sys.argv[1]) if len(sys.argv) > 1 else 900
    for batch in "AB":
        rep = json.load(open(os.path.join(ROOT, "results", f"report_{batch}.json"), encoding="utf-8"))["worlds"]
        for wid in sorted(rep):
            if not rep[wid]["decision_ok"]:
                check(batch, wid, rep[wid], budget)
