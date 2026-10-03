"""Print the SHA-256 of each file given on the command line (it never prints file contents).

Usage:  python hash_files.py <file> [<file> ...]
"""
import hashlib
import sys


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 16), b""):
            h.update(block)
    return h.hexdigest()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for p in sys.argv[1:]:
        print(sha256(p), p)
