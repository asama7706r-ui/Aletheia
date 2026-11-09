"""Run the sealed procedure of blind test 5b on the test batches, one after the other, alone on the machine
(protocol_v5b.md, Section 0, order step 4, and Section 13, item 13).
- AC power only. Nothing starts on battery. A world that runs more than BLIP seconds on battery is stopped and
  starts again from nothing on AC power (each world is saved as soon as it is solved, so the others are kept).
- The machine and the screen are kept awake while this process runs (a display request, as a video player makes).
- The power source is logged every PLOG seconds in results/power_log.txt; the times in results/run_times.txt.
Usage (from aletheia_blind_test_5b/): python -I run/run_batches_5b.py A B
Writes results/outputs_X.json (by the procedure), results/run_X.log and results/parts_X/. Refuses to overwrite an
existing outputs file."""
import ctypes
import datetime
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results")
POLL, BLIP, PLOG = 10, 60, 30  # seconds: power check; battery time tolerated before a stop; power log interval
ES_CONTINUOUS, ES_SYSTEM_REQUIRED, ES_DISPLAY_REQUIRED = 0x80000000, 0x00000001, 0x00000002
LAST_LOG = [0.0]


class PowerStatus(ctypes.Structure):
    _fields_ = [("ACLineStatus", ctypes.c_ubyte), ("BatteryFlag", ctypes.c_ubyte), ("BatteryLifePercent", ctypes.c_ubyte),
                ("SystemStatusFlag", ctypes.c_ubyte), ("BatteryLifeTime", ctypes.c_ulong),
                ("BatteryFullLifeTime", ctypes.c_ulong)]


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def note(line):
    with open(os.path.join(OUT, "run_times.txt"), "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(line, flush=True)


def on_battery():
    s = PowerStatus()
    ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(s))
    if time.time() - LAST_LOG[0] >= PLOG:
        LAST_LOG[0] = time.time()
        with open(os.path.join(OUT, "power_log.txt"), "a", encoding="utf-8") as fh:
            fh.write(f"{now()} {({0: 'battery', 1: 'AC'}).get(s.ACLineStatus, 'unknown')} {s.BatteryLifePercent}%\n")
    return s.ACLineStatus == 0


def wait_for_ac(what):
    if on_battery():
        note(f"{what}: on battery at {now()}; waiting for AC power")
        while on_battery():
            time.sleep(POLL)
        note(f"{what}: AC power back at {now()}")


def run_on_ac(what, cmd, log_path):
    """Runs cmd on AC power until it ends; returns its exit code and the seconds of its last start."""
    while True:
        wait_for_ac(what)
        t0 = time.time()
        with open(log_path, "a", encoding="utf-8") as log:
            proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, cwd=ROOT)
            since = None
            while proc.poll() is None:
                time.sleep(POLL)
                if not on_battery():
                    if since is not None:
                        note(f"{what}: on battery for {time.time() - since:.0f} s, tolerated (ended {now()})")
                    since = None
                elif since is None:
                    since = time.time()
                elif time.time() - since > BLIP:
                    subprocess.call(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    proc.wait()
                    note(f"{what}: stopped at {now()}, more than {BLIP} s on battery; the world in progress starts "
                         "again on AC power")
                    break
            else:
                if since is not None:
                    note(f"{what}: on battery for {time.time() - since:.0f} s at its end, tolerated")
                return proc.returncode, time.time() - t0


def main(batches):
    if not batches:
        print(__doc__)
        return 2
    os.makedirs(OUT, exist_ok=True)
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)
    note(f"session started {now()} (Python {sys.version.split()[0]})")
    for b in batches:
        outp = os.path.join(OUT, f"outputs_{b}.json")
        if os.path.exists(outp):
            note(f"{b}: {outp} exists; not run again")
            continue
        cmd = [sys.executable, "-I", os.path.join(ROOT, "procedure", "procedure_v5b.py"), "run",
               os.path.join(ROOT, f"batch_{b}", "worlds"), outp, os.path.join(OUT, f"parts_{b}")]
        rc, secs = run_on_ac(f"{b} run", cmd, os.path.join(OUT, f"run_{b}.log"))
        note(f"{b}: exit {rc}, last start {secs:.0f} s, ended {now()}")
        if rc != 0:
            return rc
    note(f"session ended {now()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
