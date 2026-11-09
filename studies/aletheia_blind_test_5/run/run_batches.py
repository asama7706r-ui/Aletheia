"""Run the sealed procedure on the test batches, one after the other, alone on the machine
(protocol_v5.md, Section 0, order step 4; Section 13, item 13: it runs once).
Keeps Windows from idle-sleeping while it runs (SetThreadExecutionState, released when this process ends),
because the procedure's limit is wall-clock time per world.
Usage (from aletheia_blind_test_5/): python -I run/run_batches.py A B
Writes results/outputs_X.json (by the procedure), results/run_X.log (its printed lines) and
appends to results/run_times.txt. Refuses to overwrite an existing outputs file."""
import ctypes
import datetime
import os
import subprocess
import sys

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def note(line):
    with open("results/run_times.txt", "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def main(batches):
    if not batches:
        print(__doc__)
        return 2
    for b in batches:
        if os.path.exists(f"results/outputs_{b}.json"):
            print(f"results/outputs_{b}.json exists: the procedure runs once; nothing was run")
            return 1
    if os.name == "nt":
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
    import sympy
    note(f"python {sys.version.split()[0]}, sympy {sympy.__version__}, TIME_PER_WORLD from procedure/procedure_v5.py")
    worst = 0
    for b in batches:
        start = now()
        t0 = datetime.datetime.now()
        with open(f"results/run_{b}.log", "w", encoding="utf-8") as log:
            rc = subprocess.call([sys.executable, "-I", "procedure/procedure_v5.py", "run",
                                  f"batch_{b}/worlds", f"results/outputs_{b}.json"],
                                 stdout=log, stderr=subprocess.STDOUT)
        secs = (datetime.datetime.now() - t0).total_seconds()
        note(f"batch_{b}: start {start}, end {now()}, {secs:.0f} s, exit {rc}")
        worst = max(worst, rc)
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
