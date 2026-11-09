"""Seal blind test 5b (protocol_v5b.md, Sections 0 and 14), run once, with the project owner's approval.
It writes the sealing time into the status lines of the protocol and of the two start messages, then writes
SEALED_HASHES.txt (LF line endings) with the SHA-256 of every sealed file. It refuses to run twice.
Usage (from aletheia_blind_test_5b/): python -I dev/make_seal_5b.py"""
import datetime
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEED_SHA = "6d668c608861f5cea0467e750c65743ac45f62f48c6a80a8587aea51c60b70e5"
FILES = [
    "protocol_v5b.md",
    "seed/seed_registry.json", "seed/seed_notes.md", "seed/check_seed.py", "seed/make_seed.py",
    "lang/SPEC_v0.5.md", "lang/reader_v0.py",
    "procedure/procedure_v5b.py", "procedure/procedure_v5.py", "procedure/proc_c.py", "procedure/proc_c2.py",
    "procedure/proc_c3.py", "procedure/shape_search.py", "procedure/shape_search_na.py", "procedure/shape_driver.py",
    "procedure/solver_worker.py",
    "scorer/ref_v5b.py", "scorer/certs_v5.py", "scorer/baselines_v5b.py", "scorer/score_v5b.py",
    "scorer/validate_v5b.py", "scorer/dev_fingerprints_5b.json",
    "run/run_batches_5b.py", "tools/hash_files.py", "tools/make_packages_5b.py",
    "GENERATOR_START_5b.md", "GENERATOR_START_5b_en.md",
]


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def replace_once(rel, old, new):
    p = os.path.join(ROOT, rel)
    t = open(p, encoding="utf-8").read()
    if t.count(old) != 1:
        raise SystemExit(f"{rel}: the status line to replace was not found exactly once")
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(t.replace(old, new))


if __name__ == "__main__":
    out = os.path.join(ROOT, "SEALED_HASHES.txt")
    if os.path.exists(out):
        raise SystemExit("SEALED_HASHES.txt exists: the test is sealed already")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    replace_once("protocol_v5b.md", "# Aletheia blind test 5b - pre-registered protocol v5b (DRAFT, not sealed)",
                 f"# Aletheia blind test 5b - pre-registered protocol v5b (SEALED {stamp[:10]})")
    replace_once("protocol_v5b.md",
                 "Status: DRAFT, written by the procedure author (Claude) on 2026-10-28, for the project owner's review "
                 "before sealing. The exact sealing time and the SHA-256 of every sealed file will be in "
                 "`SEALED_HASHES.txt`.",
                 f"Status: SEALED at {stamp}, with the code, after the project owner reviewed the Notion page "
                 "«مسودة التجربة 5ب: ما يحتاج مراجعتك» and approved sealing on 2026-10-31, on the condition that the "
                 "regression run on the worlds of test 5 finish without errors (it did; that page, section 4). Written "
                 "by the procedure author (Claude) on 2026-10-28. The SHA-256 of every sealed file is in "
                 "`SEALED_HASHES.txt`.")
    replace_once("GENERATOR_START_5b.md",
                 "**الحالة:** مسودة، تُختم مع البروتوكول، والبصمات ستكون في `SEALED_HASHES.txt`.",
                 f"**الحالة:** مختومة مع البروتوكول ({stamp})، والبصمات في `SEALED_HASHES.txt`.")
    replace_once("GENERATOR_START_5b_en.md",
                 "**Status:** DRAFT, to be sealed with the protocol (the hashes will be in `SEALED_HASHES.txt`).",
                 f"**Status:** sealed with the protocol ({stamp}; the hashes are in `SEALED_HASHES.txt`).")
    lines = [f"Aletheia blind test 5b - sealed files (SHA-256). Sealed at {stamp} by the procedure author (Claude), "
             "with the project owner's approval.",
             f"Environment: Python {sys.version.split()[0]}, sympy {__import__('sympy').__version__}. Seed canonical "
             f"SHA-256 (the value worlds name in registry_sha256): {SEED_SHA}"]
    lines += [f"{sha(os.path.join(ROOT, rel))}  {rel}" for rel in FILES]
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"SEALED_HASHES.txt: {sha(out)}")
