"""Make the two generator packages of blind test 5b (protocol_v5b.md, Section 0), run at sealing.

Each package is a separate folder OUTSIDE the lab, holding only what a generator may read or run:
the protocol, the seed, the language, the validator with the modules it imports, and the hash tool.
The procedure, the dev set and the scorer's report code are not in it. The script writes
package_manifest.txt (SHA-256 of every file) in each package, to compare with the hashes the
generator reports. Usage: python tools/make_packages_5b.py OUT_ROOT   (for example D:\\work_app\\t5b_gen)"""
import hashlib
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FILES = [
    "protocol_v5b.md",
    "seed/seed_registry.json", "seed/seed_notes.md", "seed/check_seed.py", "seed/make_seed.py",
    "lang/SPEC_v0.5.md", "lang/reader_v0.py",
    "scorer/certs_v5.py", "scorer/ref_v5b.py", "scorer/baselines_v5b.py", "scorer/validate_v5b.py",
    "scorer/dev_fingerprints_5b.json",
    "tools/hash_files.py",
]


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main(out_root):
    for batch in ("batch_A", "batch_B"):
        dest = os.path.join(out_root, batch)
        if os.path.exists(dest):
            raise SystemExit(f"{dest} exists already: a package is made once, at sealing")
        lines = []
        for rel in FILES:
            src = os.path.join(ROOT, rel)
            dst = os.path.join(dest, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            if sha(src) != sha(dst):
                raise SystemExit(f"copy mismatch: {rel}")
            lines.append(f"{sha(dst)}  {rel}")
        os.makedirs(os.path.join(dest, "worlds"))
        os.makedirs(os.path.join(dest, "key"))
        with open(os.path.join(dest, "package_manifest.txt"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines) + "\n")
        with open(os.path.join(dest, "progress.txt"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(f"blind test 5b, {batch}: progress of the world generator\nmodel: (write the exact model name)\n")
        print(f"wrote {dest} ({len(FILES)} files)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1])
