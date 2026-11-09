"""SHA-256 of files, and the combined hash of a batch's worlds (protocol_v5.md, Section 14).
Usage: python tools/hash_files.py FILE ...        one line per file
       python tools/hash_files.py --worlds DIR    each world's hash, then the combined hash of the 30 worlds:
                                                  the SHA-256 of the lines "name sha256" joined by newlines,
                                                  in name order"""
import hashlib
import os
import sys


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv):
    if len(argv) >= 2 and argv[0] == "--worlds":
        d = argv[1]
        names = sorted(f for f in os.listdir(d) if f.endswith(".json"))
        lines = [f"{n} {sha(os.path.join(d, n))}" for n in names]
        for ln in lines:
            print(ln)
        combined = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
        print(f"combined {combined}  ({len(names)} worlds)")
        return 0
    if not argv:
        print(__doc__)
        return 2
    for p in argv:
        print(f"{sha(p)}  {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
