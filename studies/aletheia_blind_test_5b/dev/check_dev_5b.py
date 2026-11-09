"""Dev check of test 5b (protocol_v5b.md, Section 12): the 5b procedure's outputs on the 22 dev worlds
(dev/check_dev/outputs_dev.json, written by `procedure/procedure_v5b.py run`) against the outputs of the workshop's
third measurement (round 3, the same procedure without the two changes of 10.13), then scored by the 5b scorer
against the dev key. Usage (from aletheia_blind_test_5b/): python -I dev/check_dev_5b.py"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scorer"))
import score_v5b as SC  # noqa: E402
import validate_v5b as V  # noqa: E402

V.DEV_FP = os.path.join(HERE, "no_dev_fingerprints.json")   # dev worlds are not excluded as dev worlds (V11) here

STUDY = os.path.join(os.path.dirname(ROOT), "workshop_search_study", "results_c3")
sys.stdout.reconfigure(encoding="utf-8")


def seconds(log):
    out = {}
    for line in open(log, encoding="utf-8"):
        m = re.match(r"(W-\d+)\.json: \w+ \(([\d.]+)s\)", line)
        if m:
            out[m[1]] = float(m[2])
    return out


if __name__ == "__main__":
    new = json.load(open(os.path.join(HERE, "check_dev", "outputs_dev.json"), encoding="utf-8"))
    old = json.load(open(os.path.join(STUDY, "outputs_dev.json"), encoding="utf-8"))
    t_new, t_old = seconds(os.path.join(HERE, "check_dev", "run.log")), seconds(os.path.join(STUDY, "run_dev.log"))
    same = 0
    for wid in sorted(new):
        a, b = new[wid]["procedure"], old[wid]["procedure"]
        ka = (a["verdict"], [x["drop"] for x in a.get("branches") or []], [x["status"] for x in a.get("branches") or []])
        kb = (b["verdict"], [x["drop"] for x in b.get("branches") or []], [x["status"] for x in b.get("branches") or []])
        same += ka == kb
        skipped = [x.get("searched", {}).get("stopped") for x in a.get("branches") or []
                   if "conflict" in str((x.get("searched") or {}).get("stopped"))]
        print(f"{wid}: {a['verdict']:15s} {'same' if ka == kb else 'DIFFERENT ' + str(kb)}; "
              f"{t_new.get(wid, 0):6.1f} s (round 3: {t_old.get(wid, 0):6.1f} s)"
              + (f"; associative search skipped: {skipped}" if skipped else ""))
    print(f"same verdict, branches and statuses as round 3: {same} of {len(new)}; "
          f"time {sum(t_new.values()):.0f} s (round 3: {sum(t_old.values()):.0f} s)")
    rep = SC.score(os.path.join(HERE, "batch_dev"), os.path.join(HERE, "check_dev", "outputs_dev.json"),
                   os.path.join(HERE, "check_dev", "report_dev.json"))
    print(json.dumps(rep["metrics"]["reported_only"], indent=1))
