"""Dev check of test 5b: the 5b procedure on the 60 worlds of test 5 (dev/batch_t5A, dev/batch_t5B), through the
run harness's rules (run/run_batches_5b.py: AC power only, machine and screen kept awake, power logged, a world
restarted after 60 s on battery), with its outputs in dev/check_t5/. A regression check before sealing, not a
measurement: no criterion is attached. Usage (from aletheia_blind_test_5b/): python -I dev/run_check_t5.py"""
import ctypes
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "run"))
import run_batches_5b as RB  # noqa: E402

RB.OUT = os.path.join(HERE, "check_t5")

if __name__ == "__main__":
    os.makedirs(RB.OUT, exist_ok=True)
    ctypes.windll.kernel32.SetThreadExecutionState(RB.ES_CONTINUOUS | RB.ES_SYSTEM_REQUIRED | RB.ES_DISPLAY_REQUIRED)
    RB.note(f"dev check session started {RB.now()}")
    for b in ("A", "B"):
        outp = os.path.join(RB.OUT, f"outputs_{b}.json")
        if os.path.exists(outp):
            RB.note(f"{b}: {outp} exists; not run again")
            continue
        cmd = [sys.executable, "-I", os.path.join(ROOT, "procedure", "procedure_v5b.py"), "run",
               os.path.join(HERE, f"batch_t5{b}", "worlds"), outp, os.path.join(RB.OUT, f"parts_{b}")]
        rc, secs = RB.run_on_ac(f"{b} run", cmd, os.path.join(RB.OUT, f"run_{b}.log"))
        RB.note(f"{b}: exit {rc}, last start {secs:.0f} s, ended {RB.now()}")
        if rc != 0:
            sys.exit(rc)
    RB.note(f"dev check session ended {RB.now()}")
