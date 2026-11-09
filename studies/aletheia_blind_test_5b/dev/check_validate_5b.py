"""Dev check of test 5b (protocol_v5b.md, Section 12): the 5b validator on the 82 dev worlds (test 5's 22 dev worlds
and its 60 test worlds, with their keys), with the dev fingerprints set aside so that V11 does not exclude them.
Every one of these keys was VALID under test 5's validator, so each error printed here is a change made by 5b:
- V9: the 5b reference's truth differs from the key, that is, from test 5's truth (Section 16, the reference);
- V12: a trap the key declares no longer holds (for example T9 once the certificates follow their relators);
- the batch lines: the composition and V15, now up to the nonzero numbers.
Usage (from aletheia_blind_test_5b/): python -I dev/check_validate_5b.py [batch_dev|batch_t5A|batch_t5B ...]"""
import io
import os
import sys
import time
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scorer"))
import validate_v5b as V  # noqa: E402

V.DEV_FP = os.path.join(HERE, "no_dev_fingerprints.json")
sys.stdout.reconfigure(encoding="utf-8")

if __name__ == "__main__":
    for b in sys.argv[1:] or ["batch_t5A", "batch_t5B", "batch_dev"]:
        t0 = time.time()
        buf = io.StringIO()
        with redirect_stdout(buf):
            ok, results = V.validate_batch(os.path.join(HERE, b), quick=(b == "batch_dev"))
        text = buf.getvalue()
        with open(os.path.join(HERE, "check_dev", f"validate_{b}.txt"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        lines = [ln for ln in text.splitlines() if ln.startswith(("BAD", "      V", "BATCH"))]
        print(f"== {b}: {len(results)} worlds, {time.time() - t0:.0f} s")
        print("\n".join(lines) if lines else "   no world error")
